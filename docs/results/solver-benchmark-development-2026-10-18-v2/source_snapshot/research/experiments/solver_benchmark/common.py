"""Shared domains, reference scoring, validation and evidence serialization."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from seat_solver.production.policy import TIERS, mapped_weights, policy, validate_request
from seat_solver.production.production import initial_rows
from seat_solver.production.production_scoring import candidate_cost, eligible, options, packing_pairs
from seat_solver.production.production_validator import validate_placements

ROOT = Path(__file__).resolve().parents[3]
KEYS = ("contribution_seat", "activeness", "category_zone")
SEARCH_SEED = 20261012
ORDER_SEED = 20261018
INPUT_SEED = 20261021
HEAVY_SEED = 20261022
PILOT_SEED = 20261020
CONFIGS = {
    "current": KEYS,
    "reversed": tuple(reversed(KEYS)),
    "two": (KEYS[0], KEYS[2]),
    "disabled": (),
}
METHODS = ("cp_sat", "scip", "greedy")
PROTOCOL = "solver-selection-v1-2026-10-18"


def preferences(name):
    active = CONFIGS[name]
    return [{"key": k, "enabled": True} for k in active] + [
        {"key": k, "enabled": False} for k in KEYS if k not in active
    ]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save(path, value):
    """Atomic replace within an exclusive, caller-created evidence directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read(path):
    return json.loads(Path(path).read_text())


def compact_weights(request):
    weights = mapped_weights(request["preferences"], request["preference_profile_version"])
    divisor = math.gcd(*weights.values()) or 1
    return {k: weights[k] // divisor for k in KEYS}


def reference_components(request, cfg, participant, seats):
    """Decimal recomputation independent of candidate_cost's integer arithmetic."""
    peers = [p for p in eligible(request) if p["contribution_tier"] == participant["contribution_tier"]]
    def rounded(n, d):
        return int((Decimal(n) / Decimal(max(1, d))).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    amounts = [p["contribution_amount_rm"] for p in peers]
    activities = [p["events_joined_last_2_years"] for p in peers]
    contribution = 1 + rounded(99 * (participant["contribution_amount_rm"] - min(amounts)),
                               max(amounts) - min(amounts))
    activity = rounded(100 * (participant["events_joined_last_2_years"] - min(activities)),
                       max(activities) - min(activities))
    disadvantage = 2 * sum(s["priority_rank"] - 1 for s in seats) // len(seats)
    matrix = cfg["category_zone_costs"]
    zone = 2 * sum(matrix[participant["participant_category"]][s["zone"]] for s in seats) // len(seats)
    maximum = 200 * (request["layout"]["seats_per_row"] - 1)
    return dict(zip(KEYS, (rounded(100 * contribution * disadvantage, maximum),
                          rounded(100 * activity * disadvantage, maximum),
                          rounded(100 * zone, 2 * max(v for row in matrix.values() for v in row.values())))))


@dataclass(frozen=True)
class Bundle:
    ids: tuple[str, ...]
    row: int
    best: int
    worst: int
    mask: int
    cost: int
    components: dict


@dataclass
class Problem:
    request: dict
    cfg: dict
    people: dict
    bundles: dict
    targets: dict
    packing: list
    weights: dict


def prepare(request):
    validate_request(request)
    if request["generation_mode"] != "INITIAL" or request.get("attendance"):
        raise ValueError("Benchmark accepts fresh INITIAL requests without attendance overrides")
    cfg = policy()
    weights = compact_weights(request)
    people = {p["participant_id"]: p for p in eligible(request)}
    layout = request["layout"]
    bits = {s["seat_id"]: 1 << i for i, s in enumerate(layout["seats"])}
    allowed = initial_rows(request)
    bundles = {}
    for pid, person in people.items():
        candidates = sorted((o for o in options(request, person) if o[0]["row_number"] in allowed[pid]),
                            key=lambda o: tuple(s["seat_id"] for s in o))
        bundles[pid] = []
        for option in candidates:
            # Pure Decimal calculation avoids reopening/validating the policy file
            # for every option. Preflight checks EVERY vector against production.
            components = reference_components(request, cfg, person, option)
            orders = [(s["row_number"] - 1) * layout["seats_per_row"] + s["priority_rank"] for s in option]
            bundles[pid].append(Bundle(tuple(s["seat_id"] for s in option), option[0]["row_number"],
                                       min(orders), max(orders), sum(bits[s["seat_id"]] for s in option),
                                       sum(weights[k] * components[k] for k in KEYS), components))
    remaining = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in people.values())
    targets = {}
    for row in range(1, layout["row_count"] + 1):
        capacity = sum(not s["is_blocked"] and s["row_number"] == row for s in layout["seats"])
        targets[row] = min(remaining, capacity)
        remaining -= targets[row]
    if remaining:
        # Keep an impossible demand explicit for all adapters/correctness tests.
        targets[0] = remaining
    return Problem(request, cfg, people, bundles, targets, packing_pairs(layout), weights)


def verify_option_scores(problem):
    seats = {s["seat_id"]: s for s in problem.request["layout"]["seats"]}
    checked = 0
    for pid, bundles in problem.bundles.items():
        for bundle in bundles:
            maintained = candidate_cost(problem.request, problem.cfg, problem.people[pid],
                                        [seats[s] for s in bundle.ids])["normalized"]
            if maintained != bundle.components:
                raise ValueError(f"Compiled score differs from maintained scorer: {pid}, {bundle.ids}")
            checked += 1
    return checked


def compatible(p, a, q, b):
    if a.mask & b.mask:
        return False
    pt, qt = TIERS.index(p["contribution_tier"]), TIERS.index(q["contribution_tier"])
    if pt < qt:
        return a.worst < b.best
    if pt > qt:
        return b.worst < a.best
    return (p["contribution_amount_rm"] - q["contribution_amount_rm"]) * (a.row - b.row) <= 0


def score_and_audit(problem, placements):
    audit = validate_placements(problem.request, placements)
    if not audit["passed"]:
        return audit, None
    lookup = {s["seat_id"]: s for s in problem.request["layout"]["seats"]}
    totals = dict.fromkeys(KEYS, 0)
    for assignment in placements:
        p = problem.people[assignment["participant_id"]]
        seats = [lookup[s] for s in assignment["seat_ids"]]
        independent = reference_components(problem.request, problem.cfg, p, seats)
        maintained = candidate_cost(problem.request, problem.cfg, p, seats)["normalized"]
        if independent != maintained:
            raise ValueError("Independent reference scorer disagrees with production scorer")
        for key in KEYS:
            totals[key] += independent[key]
    n = len(problem.people)
    cost = sum(problem.weights[k] * totals[k] for k in KEYS)
    return audit, {"objective": cost, "cost_per_registration": cost / n if n else None,
                   "components": totals, "component_means": {k: v / n if n else None for k, v in totals.items()}}


def execute(request, method, seconds, seed=SEARCH_SEED, checkpoint=None):
    from .adapters import build_adapter
    started = time.perf_counter()
    problem = prepare(request)
    prepared = time.perf_counter()
    search = build_adapter(problem, method, seconds, seed)
    built = time.perf_counter()
    result = search()
    searched = time.perf_counter()
    chosen = result.pop("chosen", None)
    placements = None if chosen is None else [
        {"participant_id": pid, "seat_ids": list(problem.bundles[pid][j].ids)}
        for pid, j in sorted(chosen.items())
    ]
    record = {"method": method, "budget_seconds": seconds, "search_seed": seed,
              "worker_count": 1, "canonicalize": False, "request_sha256": digest(request),
              "weights": problem.weights, "registrations": len(problem.people),
              "physical_seats": sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in problem.people.values()),
              "execution_status": "completed", "valid": False, "placements": placements,
              "objective": None, "components": None, "component_means": None,
              "absolute_gap": None, "relative_gap": None, "validation": None,
              "first_incumbent_seconds": None,
              "first_incumbent_unavailable_reason": "No comparable incumbent callback in SCIP MPSolver wrapper",
              **result}
    if placements is not None and checkpoint:
        checkpoint({**record, "execution_status": "validation_pending"})
    if placements is not None:
        audit, scores = score_and_audit(problem, placements)
        record["validation"] = audit
        record["valid"] = audit["passed"]
        if scores:
            record.update(scores)
            reported = result.get("reported_objective")
            if reported is not None and abs(reported - scores["objective"]) > 1e-5:
                raise ValueError("Adapter objective differs from independent rescoring")
            bound = result.get("best_bound")
            if bound is not None:
                if bound > scores["objective"] + 1e-5:
                    raise ValueError("Solver lower bound exceeds validated incumbent")
                record["absolute_gap"] = max(0, scores["objective"] - bound)
                record["relative_gap"] = record["absolute_gap"] / max(1, abs(scores["objective"]))
    ended = time.perf_counter()
    search_call = result.get("search_call_seconds", searched - built)
    record["timing"] = {"preprocessing_seconds": prepared - started,
                         "model_build_seconds": built - prepared,
                         "search_seconds": search_call,
                         "extraction_seconds": max(0, searched - built - search_call),
                         "validation_scoring_seconds": ended - searched,
                         "allocation_total_seconds": ended - started}
    record["valid_plan_return_seconds"] = ended - started if record["valid"] else None
    return record
