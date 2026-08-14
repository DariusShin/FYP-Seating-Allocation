"""Command-line interface: ``solve`` and ``validate`` subcommands.

Expected input problems and solver failures are written as structured JSON
error documents (exit code 1) instead of raising uncaught exceptions.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from seat_solver.models import (
    InputDataError,
    load_floor_plan,
    load_participants,
    load_previous_allocation,
    load_solver_config,
    read_json,
    write_json,
)
from seat_solver.result_formatter import build_error_result
from seat_solver.solver import solve_seat_allocation
from seat_solver.validator import validate_result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_error(path: Path, exc: Exception) -> dict:
    return build_error_result(
        run_id="RUN-INPUT-ERROR",
        generated_at=_now_iso(),
        code="INVALID_INPUT",
        message=f"could not load {path}: {exc}",
        details={"file": str(path)},
    )


def run_solve(args: argparse.Namespace) -> int:
    try:
        participants = load_participants(args.participants)
        floor_plan = load_floor_plan(args.floor_plan)
        config = load_solver_config(args.config)
        previous = (
            load_previous_allocation(args.previous_allocation)
            if args.previous_allocation is not None
            else None
        )
    except (OSError, ValueError, KeyError, InputDataError) as exc:
        failed_path = args.participants
        result = _load_error(Path(failed_path), exc)
        write_json(args.output, result)
        print(f"error: {result['error']['message']}", file=sys.stderr)
        return 1

    result = solve_seat_allocation(participants, floor_plan, config, previous)
    write_json(args.output, result)
    if result["status"] == "success":
        stats = result["solver"]
        print(
            f"status=OPTIMAL objective={stats['objective_value']} "
            f"main_penalty={stats['main_penalty']} "
            f"wall_time={stats['wall_time_seconds']:.3f}s -> {args.output}"
        )
        return 0
    print(
        f"error: {result['error']['code']}: {result['error']['message']} "
        f"-> {args.output}",
        file=sys.stderr,
    )
    return 1


def run_validate(args: argparse.Namespace) -> int:
    try:
        result = read_json(args.result)
    except (OSError, ValueError) as exc:
        report = {
            "schema_version": "1.0.0",
            "generated_at": _now_iso(),
            "result_file": str(args.result),
            "overall_passed": False,
            "summary": {"total_checks": 0, "passed_checks": 0, "failed_checks": 0},
            "checks": [],
            "error": f"could not load result file: {exc}",
        }
        write_json(args.output, report)
        print(f"error: {report['error']}", file=sys.stderr)
        return 1

    report = validate_result(result, _now_iso(), result_file=str(args.result))
    write_json(args.output, report)
    summary = report["summary"]
    print(
        f"validation {'PASSED' if report['overall_passed'] else 'FAILED'}: "
        f"{summary['passed_checks']}/{summary['total_checks']} checks passed "
        f"-> {args.output}"
    )
    return 0 if report["overall_passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seat_solver.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="run the CP-SAT solver")
    solve_parser.add_argument("--participants", type=Path, required=True)
    solve_parser.add_argument("--floor-plan", type=Path, required=True)
    solve_parser.add_argument("--config", type=Path, required=True)
    solve_parser.add_argument("--previous-allocation", type=Path, default=None)
    solve_parser.add_argument(
        "--output", type=Path, default=Path("output/seat_allocation_result.json")
    )
    solve_parser.set_defaults(handler=run_solve)

    validate_parser = subparsers.add_parser(
        "validate", help="independently validate a result file"
    )
    validate_parser.add_argument("--result", type=Path, required=True)
    validate_parser.add_argument(
        "--output", type=Path, default=Path("output/validation_report.json")
    )
    validate_parser.set_defaults(handler=run_validate)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
