"""Ten-run deterministic benchmark of the full solve pipeline.

Each run executes the complete ``solve_seat_allocation`` pipeline on freshly
loaded inputs; timings use ``time.perf_counter`` around the whole run, and
per-run CP-SAT statistics come from each run's actual solver response. No
metric is estimated or reused between runs.
"""

from __future__ import annotations

import argparse
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from seat_solver.models import (
    SCHEMA_VERSION,
    load_floor_plan,
    load_participants,
    load_previous_allocation,
    load_solver_config,
    write_json,
)
from seat_solver.solver import solve_seat_allocation


def _rss_bytes() -> int | None:
    try:
        import psutil
    except ImportError:  # pragma: no cover
        return None
    memory = psutil.Process().memory_info()
    return int(getattr(memory, "peak_wset", memory.rss))


def _p95(values: list[float]) -> float:
    """95th percentile via linear interpolation between closest ranks."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = 0.95 * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    fraction = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def run_benchmark(
    participants_path: Path,
    floor_plan_path: Path,
    config_path: Path,
    previous_allocation_path: Path | None,
    runs: int,
) -> dict[str, Any]:
    per_run: list[dict[str, Any]] = []
    for run_index in range(1, runs + 1):
        started = time.perf_counter()
        participants = load_participants(participants_path)
        floor_plan = load_floor_plan(floor_plan_path)
        config = load_solver_config(config_path)
        previous = (
            load_previous_allocation(previous_allocation_path)
            if previous_allocation_path is not None
            else None
        )
        result = solve_seat_allocation(participants, floor_plan, config, previous)
        elapsed = time.perf_counter() - started

        if result["status"] == "success":
            stats = result["solver"]
            per_run.append(
                {
                    "run_index": run_index,
                    "status": stats["status"],
                    "success": True,
                    "total_wall_time_seconds": round(elapsed, 6),
                    "solver_wall_time_seconds": stats["wall_time_seconds"],
                    "solver_user_time_seconds": stats["user_time_seconds"],
                    "objective_value": stats["objective_value"],
                    "best_objective_bound": stats["best_objective_bound"],
                    "optimality_gap": stats["optimality_gap"],
                    "num_conflicts": stats["num_conflicts"],
                    "num_branches": stats["num_branches"],
                    "num_boolean_variables": stats["num_boolean_variables"],
                    "num_integer_variables": stats["num_integer_variables"],
                    "num_constraints": stats["num_constraints"],
                    "eligible_single_assignment_count": stats[
                        "eligible_single_assignment_count"
                    ],
                    "eligible_emperor_pair_count": stats["eligible_emperor_pair_count"],
                    "peak_memory_rss_bytes": stats["peak_memory_rss_bytes"],
                }
            )
        else:
            per_run.append(
                {
                    "run_index": run_index,
                    "status": result["error"].get("solver_status") or "ERROR",
                    "success": False,
                    "total_wall_time_seconds": round(elapsed, 6),
                    "error_code": result["error"]["code"],
                    "error_message": result["error"]["message"],
                }
            )

    successes = [run for run in per_run if run["success"]]
    times = [run["total_wall_time_seconds"] for run in successes]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case_study": "PJ Kwan Inn Teng",
        "runs": runs,
        "successful_optimal_runs": len(successes),
        "failed_runs": runs - len(successes),
        "wall_time_seconds": (
            {
                "min": round(min(times), 6),
                "max": round(max(times), 6),
                "mean": round(statistics.fmean(times), 6),
                "median": round(statistics.median(times), 6),
                "p95": round(_p95(times), 6),
            }
            if times
            else None
        ),
        "objective_values": [run["objective_value"] for run in successes],
        "best_objective_bounds": [run["best_objective_bound"] for run in successes],
        "num_conflicts": [run["num_conflicts"] for run in successes],
        "num_branches": [run["num_branches"] for run in successes],
        "peak_memory_rss_bytes": _rss_bytes(),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "per_run": per_run,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--participants", type=Path, default=Path("data/mock_participants.json")
    )
    parser.add_argument("--floor-plan", type=Path, default=Path("data/floor_plan.json"))
    parser.add_argument(
        "--config", type=Path, default=Path("config/solver_config.json")
    )
    parser.add_argument("--previous-allocation", type=Path, default=None)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--output", type=Path, default=Path("output/performance_report.json")
    )
    args = parser.parse_args(argv)

    report = run_benchmark(
        args.participants,
        args.floor_plan,
        args.config,
        args.previous_allocation,
        args.runs,
    )
    write_json(args.output, report)
    if report["failed_runs"]:
        print(
            f"benchmark FAILED: {report['failed_runs']}/{report['runs']} runs "
            f"unsuccessful -> {args.output}",
            file=sys.stderr,
        )
        return 1
    times = report["wall_time_seconds"]
    print(
        f"benchmark OK: {report['successful_optimal_runs']}/{report['runs']} optimal, "
        f"mean={times['mean']:.3f}s p95={times['p95']:.3f}s -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
