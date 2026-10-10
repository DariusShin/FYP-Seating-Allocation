"""Synthetic sensitivity study; reuses production hard constraints, changes only costs.

Run from the repository: .venv/bin/python research/experiments/preference_sensitivity.py
No production policy, registration store, or workspace is modified.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from seat_solver.production.policy import MINIMUMS, policy, validate_request
from seat_solver.production.production import build
from research.fixtures.synthetic_participants import generate
from seat_solver.production.production_scoring import candidate_cost, eligible
from seat_solver.production.production_validator import validate_placements

KEYS = ("contribution_seat", "activeness", "category_zone")
WEIGHTS = {
    "current": (4, 3, 2),  # exactly equivalent to 40/30/20
    "equal": (1, 1, 1),
    "rank_sum": (3, 2, 1),
    "rank_reciprocal": (6, 3, 2),
    "roc": (11, 5, 2),
    "flatter": (36, 30, 24),
    "steeper": (44, 30, 16),
    "contribution_only": (1, 0, 0),
    "activity_only": (0, 1, 0),
    "category_only": (0, 0, 1),
}
SIZES = {"small": (8, 8, 8), "typical": (56, 24, 16), "full": (80, 40, 32)}


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def rounded(n, d):
    # Decimal implementation independently checks production integer rounding.
    return int((Decimal(n) / Decimal(max(1, d))).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def independent_cost(req, cfg, p, seats):
    peers = [q for q in eligible(req) if q["contribution_tier"] == p["contribution_tier"]]
    c = [q["contribution_amount_rm"] for q in peers]
    a = [q["events_joined_last_2_years"] for q in peers]
    importance_c = 1 + rounded(99 * (p["contribution_amount_rm"] - min(c)), max(c) - min(c))
    importance_a = rounded(100 * (p["events_joined_last_2_years"] - min(a)), max(a) - min(a))
    disadvantage = 2 * sum(s["priority_rank"] - 1 for s in seats) // len(seats)
    table = cfg["category_zone_costs"]
    zone = 2 * sum(table[p["participant_category"]][s["zone"]] for s in seats) // len(seats)
    bound = 200 * (req["layout"]["seats_per_row"] - 1)
    return (
        rounded(100 * importance_c * disadvantage, bound),
        rounded(100 * importance_a * disadvantage, bound),
        rounded(100 * zone, 2 * max(v for row in table.values() for v in row.values())),
    )


def matrices(cfg):
    result = {"base": copy.deepcopy(cfg)}
    for name in ("squared", "ordinal", "zero", "scaled_double"):
        result[name] = copy.deepcopy(cfg)
        for category, row in cfg["category_zone_costs"].items():
            ranks = {value: i for i, value in enumerate(sorted(set(row.values())))}
            result[name]["category_zone_costs"][category] = {
                zone: {"squared": value**2, "ordinal": ranks[value], "zero": 0,
                       "scaled_double": 2 * value}[name]
                for zone, value in row.items()
            }
    return result


def fixture(size, pattern, seed):
    req = generate(*SIZES[size], seed=seed, accessible=0)
    req.pop("attendance", None)
    req["preferences"] = [{"key": key, "enabled": True} for key in KEYS]
    for p in req["participants"]:
        p["full_name"] = "Synthetic " + p["participant_id"]
        if pattern == "conflict":
            extra = p["contribution_amount_rm"] - MINIMUMS[p["contribution_tier"]]
            p["events_joined_last_2_years"] = 20 - extra // 50
        elif pattern == "tied":
            p["contribution_amount_rm"] = MINIMUMS[p["contribution_tier"]]
    return validate_request(req)


def run_instance(req, name, out, limit):
    cfgs = matrices(policy())
    start = time.perf_counter()
    model, variables, options, _, _ = build(req, cfgs["base"])
    build_time = time.perf_counter() - start
    coefficients = {key: {} for key in cfgs}
    checked = 0
    for p in eligible(req):
        pid = p["participant_id"]
        for key, cfg in cfgs.items():
            coefficients[key][pid] = []
            for option in options[pid]:
                independent = independent_cost(req, cfg, p, option)
                production = candidate_cost(req, cfg, p, option)["normalized"]
                assert independent == tuple(production[k] for k in KEYS)
                coefficients[key][pid].append(independent)
                checked += 1
        assert coefficients["base"][pid] == coefficients["scaled_double"][pid]
    # Every option, not merely selected options: common positive scaling leaves costs unchanged.
    profiles = [("base", w) for w in WEIGHTS]
    profiles += [(m, w) for m in ("squared", "ordinal") for w in ("current", "equal", "roc")]
    profiles += [("zero", "current")]
    results = []
    for matrix, weight in profiles:
        vector = WEIGHTS[weight]
        expr = sum(v * sum(a * b for a, b in zip(vector, c))
                   for pid, vs in variables.items()
                   for v, c in zip(vs, coefficients[matrix][pid]))
        model.Minimize(expr)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = limit
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 20261011
        status = solver.Solve(model)
        row = {"instance": name, "matrix": matrix, "weight": weight, "weights": vector,
               "registrations": len(req["participants"]), "status": solver.StatusName(status),
               "solve_seconds": solver.WallTime(), "model_build_seconds_shared": build_time,
               "best_bound": solver.BestObjectiveBound(), "branches": solver.NumBranches(),
               "conflicts": solver.NumConflicts()}
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            chosen = {pid: next(j for j, v in enumerate(vs) if solver.Value(v))
                      for pid, vs in variables.items()}
            placements = [{"participant_id": pid,
                           "seat_ids": [s["seat_id"] for s in options[pid][j]]}
                          for pid, j in chosen.items()]
            audit = validate_placements(req, placements)
            assert audit["passed"], audit
            row["validation"] = audit
            row["placements"] = placements
            row["components_by_matrix"] = {
                m: [sum(costs[pid][j][k] for pid, j in chosen.items()) for k in range(3)]
                for m, costs in coefficients.items() if m != "scaled_double"}
            row["objective"] = sum(w * c for w, c in zip(vector, row["components_by_matrix"][matrix]))
            assert abs(row["objective"] - solver.ObjectiveValue()) < 1e-5
            row["relative_gap"] = max(0, row["objective"] - row["best_bound"]) / max(1, abs(row["objective"]))
        results.append(row)
    save(out / "runs" / (name + ".json"), {"runs": results, "checked_option_vectors": checked})
    print(name, dict(Counter(r["status"] for r in results)), flush=True)
    return results, checked


def summarize(rows):
    comparisons = []
    for name in sorted({r["instance"] for r in rows}):
        subset = [r for r in rows if r["instance"] == name]
        base = next(r for r in subset if r["matrix"] == "base" and r["weight"] == "current")
        if "objective" not in base:
            continue
        for r in subset:
            if "objective" not in r:
                continue
            base_under_alternative = sum(w * c for w, c in zip(r["weights"], base["components_by_matrix"][r["matrix"]]))
            comparisons.append({"instance": name, "matrix": r["matrix"], "weight": r["weight"],
                "alternative_proven_optimal": r["status"] == "OPTIMAL",
                "baseline_objective_under_alternative": base_under_alternative,
                "alternative_objective": r["objective"],
                "baseline_suboptimal_proven": base_under_alternative > r["objective"],
                "baseline_also_optimal_proven": r["status"] == "OPTIMAL" and base_under_alternative == r["objective"],
                "common_scale_components": r["components_by_matrix"]["base"]})
    return {"statuses": dict(Counter(r["status"] for r in rows)),
            "valid_returned_solutions": sum(r.get("validation", {}).get("passed", False) for r in rows),
            "comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/preference-sensitivity-2026-10-11")
    parser.add_argument("--seconds", type=float, default=1.5)
    parser.add_argument("--sizes", nargs="+", choices=list(SIZES), default=list(SIZES))
    parser.add_argument("--patterns", nargs="+", choices=["mixed", "conflict", "tied"], default=["mixed", "conflict", "tied"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[20261011, 20261012])
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    if args.out.exists():
        parser.error("Output directory already exists; choose a new --out to preserve previous evidence")
    start = time.perf_counter()
    source_paths = [Path(__file__).relative_to(ROOT),
                    Path("services/seating/config/production_policy.json"),
                    Path("services/seating/src/seat_solver/jsonio.py")]
    source_paths += list(Path("services/seating/src/seat_solver/production").glob("*.py"))
    hashes = {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_paths}
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "ortools": ortools.__version__, "platform": platform.platform(), "machine": platform.machine(),
        "solver_workers": 1, "solver_seed": 20261011, "time_limit_seconds_per_solve": args.seconds,
        "data_seeds": args.seeds, "sizes": {s: SIZES[s] for s in args.sizes}, "patterns": args.patterns,
        "weights": WEIGHTS, "policy": policy(), "source_sha256": hashes,
        "purpose": "Sensitivity diagnostics; no empirical PJKIT preference labels; all participants synthetic",
        "scope": "Initial generation only; production hard constraints; no canonical tie breaking; no accessibility requests"}
    save(args.out / "manifest.json", manifest)
    rows, checked = [], 0
    for size in args.sizes:
        for pattern in args.patterns:
            for seed in args.seeds:
                name = f"{size}-{pattern}-{seed}"
                req = fixture(size, pattern, seed)
                save(args.out / "inputs" / (name + ".json"), req)
                result, count = run_instance(req, name, args.out, args.seconds)
                rows.extend(result)
                checked += count
    summary = summarize(rows)
    summary.update({"total_runs": len(rows), "checked_option_vectors": checked,
                    "elapsed_seconds": time.perf_counter() - start,
                    "scaling_invariance_checks": "passed for every generated option"})
    save(args.out / "summary.json", summary)
    print({k: v for k, v in summary.items() if k != "comparisons"})


if __name__ == "__main__":
    main()
