"""Reproducible evaluation runner: core, profiles, randomized, saturation.

No AWS latency is claimed: deployment measurements must be collected on AWS separately.
"""

import argparse
import itertools
import json
import platform
import random
import resource
import statistics
import time

import ortools

from seat_solver.prototype.models import write_json
from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.production_validator import audit_result


def profile_space():
    keys = ["contribution_seat", "activeness", "category_zone"]
    for k in range(4):
        for active in itertools.permutations(keys, k):
            yield [{"key": x, "enabled": True} for x in active] + [
                {"key": x, "enabled": False} for x in keys if x not in active
            ]


def core_scenarios():
    specs = [
        (0, 1, 0),
        (0, 2, 0),
        (1, 0, 0),
        (1, 1, 1),
        (35, 30, 20),
        (40, 35, 25),
        (45, 30, 20),
        (50, 30, 20),
        (56, 24, 16),
        (70, 40, 30),
        (80, 40, 40),
        (100, 20, 20),
        (3, 9, 4),
        (4, 8, 8),
        (20, 20, 20),
        (20, 20, 20),
        (0, 0, 0),
        (121, 0, 0),
        (0, 1, 0),
        (0, 2, 0),
    ]
    for i, counts in enumerate(specs, 1):
        r = generate(*counts, seed=20260918 + i)
        if i in (14, 19):
            r["participants"][0]["requires_accessible_seat"] = True
        if i == 20:
            r["participants"][0]["requires_accessible_seat"] = "false"
        yield (
            f"DS-{i:02d}",
            r,
            None,
        )


def evaluate(suite="core", runs=100, budget=5):
    scenarios = []
    if suite == "core":
        scenarios = list(core_scenarios())
    elif suite == "profiles":
        for i, profile in enumerate(profile_space()):
            r = generate(12, 8, 8)
            r["preferences"] = profile
            scenarios.append((f"PROFILE-{i:02}", r, None))
    elif suite == "random":
        for i in range(runs):
            rng = random.Random(i)
            e = rng.randrange(25, 55)
            m = rng.randrange(15, 45)
            b = 100 - e - m
            scenarios.append(
                (
                    f"RANDOM-{i:03}",
                    generate(e, m, b, seed=i, accessible=rng.randrange(0, 8)),
                    None,
                )
            )
    elif suite == "saturation":
        for e in (0, 20, 40, 60, 80, 100):
            for demand in (120, 180, 220, 240):
                if 2 * e > demand:
                    continue
                singles = demand - 2 * e
                scenarios.append(
                    (
                        f"SAT-{e}-{demand}",
                        generate(e, singles // 2, singles - singles // 2),
                        None,
                    )
                )
    results = []
    for name, request, _ in scenarios:
        request["solver"].update(max_time_seconds=budget, canonicalize=False)
        started = time.perf_counter()
        out = solve(request)
        elapsed = time.perf_counter() - started
        row = {
            "scenario": name,
            "seed": request["solver"]["random_seed"],
            "layout_version_id": request["layout_version_id"],
            "registration_units": len(request["participants"]),
            "required_physical_seats": sum(
                2 if p["contribution_tier"] == "EMPEROR" else 1
                for p in request["participants"]
                if p["registration_status"] == "CONFIRMED"
            ),
            "input_sha256": __import__("hashlib")
            .sha256(json.dumps(request, sort_keys=True).encode())
            .hexdigest(),
            "end_to_end_seconds": elapsed,
            "status": out.get("solver", {}).get(
                "status", out.get("error", {}).get("code")
            ),
        }
        if out["status"] == "success":
            row.update(
                validation=audit_result(out),
                normalized_penalties=out["quality"]["normalized"],
                proof=out["solver"]["proof"],
                phase_timing=out["solver"]["timing"],
            )
        else:
            row["error"] = out["error"]
        results.append(row)
    times = sorted(r["end_to_end_seconds"] for r in results)
    q = statistics.quantiles(times, n=4) if len(times) > 1 else [times[0]] * 3
    statuses = {
        s: sum(r["status"] == s for r in results)
        for s in sorted({r["status"] for r in results})
    }
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "suite": suite,
        "environment": {
            "python": platform.python_version(),
            "ortools": ortools.__version__,
            "platform": platform.platform(),
            "solve_budget_seconds": budget,
        },
        "summary": {
            "runs": len(results),
            "min": min(times),
            "max": max(times),
            "median": statistics.median(times),
            "iqr": q[2] - q[0],
            "p95": times[min(len(times) - 1, int(0.95 * (len(times) - 1)))],
            "status_counts": statuses,
            "status_rates": {k: v / len(results) for k, v in statuses.items()},
            "process_peak_rss_bytes": peak
            if platform.system() == "Darwin"
            else peak * 1024,
        },
        "runs": results,
        "deployment_measurements": "Not collected; requires deployed Lambda cold/warm invocations.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--suite", choices=["core", "profiles", "random", "saturation"], default="core"
    )
    p.add_argument("--runs", type=int, default=100)
    p.add_argument("--budget", type=float, default=5)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    if a.runs < 1 or not 0 < a.budget <= 300:
        p.error("positive runs and budget <= 300 required")
    report = evaluate(a.suite, a.runs, a.budget)
    write_json(a.output, report)
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
