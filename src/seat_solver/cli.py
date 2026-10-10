"""Production command-line interface: ``solve`` and ``validate`` subcommands.

Expected input problems and solver failures are written as structured JSON
error documents (exit code 1) instead of raising uncaught exceptions. The
historical v1 ``legacy-solve`` command lives with the relocated prototype in
research/baselines/legacy_cp_sat/cli.py.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from seat_solver.jsonio import read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_solve(args: argparse.Namespace) -> int:
    from seat_solver.production.production import error, solve

    try:
        result = solve(read_json(args.request))
    except (OSError, ValueError) as exc:
        result = error("INVALID_INPUT", str(exc))
    write_json(args.output, result)
    print(result.get("solver", {}).get("status", result.get("error", {}).get("code")))
    return 0 if result["status"] == "success" else 1


def run_validate(args: argparse.Namespace) -> int:
    from seat_solver.production.production_validator import audit_result

    try:
        result = read_json(args.result)
    except (OSError, ValueError) as exc:
        report = {
            "schema_version": "2.0.0",
            "generated_at": _now_iso(),
            "result_file": str(args.result),
            "passed": False,
            "findings": [],
            "error": f"could not load result file: {exc}",
        }
        write_json(args.output, report)
        print(f"error: {report['error']}", file=sys.stderr)
        return 1
    if result.get("schema_version") != "2.0.0":
        report = {
            "schema_version": "2.0.0",
            "generated_at": _now_iso(),
            "result_file": str(args.result),
            "passed": False,
            "findings": [],
            "error": (
                "only schema_version 2.0.0 production results are supported here; "
                "validate historical v1 results with the legacy baseline CLI in "
                "research/baselines/legacy_cp_sat"
            ),
        }
        write_json(args.output, report)
        print(f"error: {report['error']}", file=sys.stderr)
        return 1
    report = audit_result(result)
    write_json(args.output, report)
    print("validation " + ("PASSED" if report["passed"] else "FAILED"))
    return 0 if report["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seat_solver.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser(
        "solve", help="solve a versioned production request (never publish)"
    )
    solve_parser.add_argument("--request", type=Path, required=True)
    solve_parser.add_argument("--output", type=Path, required=True)
    solve_parser.set_defaults(handler=run_solve)

    validate_parser = subparsers.add_parser(
        "validate", help="independently validate a production result file"
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
