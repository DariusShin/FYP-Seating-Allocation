"""Solve orchestration: validate, preprocess, model, solve, extract, audit.

``solve_seat_allocation`` is the single reusable entry point. It always
returns a JSON-serializable dictionary — a success document only when CP-SAT
proves OPTIMAL and the extracted solution passes independent validation and
schema validation; otherwise a structured error document.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from ortools.sat.python import cp_model

from seat_solver.cost_calculator import CostCalculator
from seat_solver.cp_sat_model import ModelBundle, build_model
from seat_solver.models import (
    FloorPlan,
    Participant,
    PreviousAllocation,
    SolverConfig,
)
from seat_solver.preprocessing import (
    EmperorUnit,
    SingleUnit,
    StructuredError,
    TierBands,
    build_allocation_units,
    build_valid_pairs,
    check_capacity,
    check_total_capacity,
    compute_allowed_rows,
    compute_tier_bands,
    validate_inputs,
)
from seat_solver.result_formatter import (
    ExtractedAssignment,
    build_error_result,
    build_success_result,
)
from seat_solver.validator import (
    compute_hard_constraint_validation,
    validate_against_schema,
)

ENGINE_NAME = "Google OR-Tools CP-SAT"

_STATUS_NAMES = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_run_id() -> str:
    return f"RUN-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"


def _peak_rss_bytes() -> int | None:
    """Approximate peak process memory; None when psutil is unavailable."""
    try:
        import psutil
    except ImportError:  # pragma: no cover - psutil is an optional dependency
        return None
    memory = psutil.Process().memory_info()
    return int(getattr(memory, "peak_wset", memory.rss))


def _variable_counts(model: cp_model.CpModel) -> tuple[int, int]:
    booleans = 0
    integers = 0
    for variable in model.Proto().variables:
        domain = list(variable.domain)
        if domain == [0, 1]:
            booleans += 1
        else:
            integers += 1
    return booleans, integers


def solve_seat_allocation(
    participants: list[Participant],
    floor_plan: FloorPlan,
    config: SolverConfig,
    previous_allocation: PreviousAllocation | None = None,
) -> dict[str, Any]:
    """Run the full pipeline and return a frontend-friendly result dictionary.

    Success is reported only for a proven ``OPTIMAL`` CP-SAT status; every
    other outcome (invalid input, capacity violations, FEASIBLE-only,
    INFEASIBLE, MODEL_INVALID, UNKNOWN, failed post-validation) yields a
    structured error document with a machine-readable code.
    """
    run_id = _new_run_id()
    generated_at = _now_iso()
    started = time.perf_counter()

    def error(
        code: str,
        message: str,
        solver_status: str | None = None,
        details: dict[str, Any] | None = None,
        objective_value: int | None = None,
        best_objective_bound: int | None = None,
    ) -> dict[str, Any]:
        return build_error_result(
            run_id=run_id,
            generated_at=generated_at,
            code=code,
            message=message,
            solver_status=solver_status,
            details=details,
            wall_time_seconds=round(time.perf_counter() - started, 6),
            objective_value=objective_value,
            best_objective_bound=best_objective_bound,
        )

    validation_error = validate_inputs(
        participants, floor_plan, config, previous_allocation
    )
    if validation_error is not None:
        return error(
            validation_error.code,
            validation_error.message,
            None,
            validation_error.details,
        )

    try:
        valid_pairs = build_valid_pairs(floor_plan, config)
    except ValueError as exc:
        return error("INVALID_INPUT", str(exc))

    total_error = check_total_capacity(participants, floor_plan)
    if total_error is not None:
        return error(total_error.code, total_error.message, None, total_error.details)

    bands_or_error = compute_tier_bands(participants, floor_plan, valid_pairs)
    if isinstance(bands_or_error, StructuredError):
        return error(
            bands_or_error.code,
            bands_or_error.message,
            None,
            bands_or_error.details,
        )
    bands: TierBands = bands_or_error

    capacity_error = check_capacity(
        participants, floor_plan, config, valid_pairs, bands
    )
    if capacity_error is not None:
        return error(
            capacity_error.code, capacity_error.message, None, capacity_error.details
        )

    allowed_rows = (
        compute_allowed_rows(participants, bands) if config.enforce_front_fill else None
    )
    singles, emperors = build_allocation_units(
        participants, floor_plan, valid_pairs, bands, allowed_rows
    )
    for unit in singles:
        if not unit.eligible_seats:
            return error(
                "TIER_CAPACITY_EXCEEDED",
                f"participant {unit.participant.participant_id} has no eligible seat",
                details={"participant_id": unit.participant.participant_id},
            )
    for emperor_unit in emperors:
        if not emperor_unit.eligible_pairs:
            return error(
                "TIER_CAPACITY_EXCEEDED",
                f"participant {emperor_unit.participant.participant_id} has no "
                "eligible Emperor pair",
                details={"participant_id": emperor_unit.participant.participant_id},
            )

    cost_calculator = CostCalculator(
        participants, floor_plan, config, previous_allocation
    )
    try:
        bundle = build_model(
            singles, emperors, valid_pairs, floor_plan, config, cost_calculator, bands
        )
    except ValueError as exc:
        return error("MODEL_INVALID", str(exc))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(config.max_time_seconds)
    solver.parameters.num_search_workers = config.num_search_workers
    solver.parameters.random_seed = config.random_seed
    solver.parameters.log_search_progress = config.log_search_progress
    status = solver.Solve(bundle.model)
    status_name = _STATUS_NAMES.get(status, f"STATUS_{status}")

    if status_name in ("FEASIBLE", "INFEASIBLE", "MODEL_INVALID", "UNKNOWN"):
        objective = (
            int(round(solver.ObjectiveValue())) if status_name == "FEASIBLE" else None
        )
        bound = (
            int(round(solver.BestObjectiveBound()))
            if status_name == "FEASIBLE"
            else None
        )
        code, message = {
            "FEASIBLE": (
                "OPTIMAL_NOT_PROVEN",
                "CP-SAT returned FEASIBLE, but only a proven OPTIMAL result is "
                "accepted"
                + (" (require_optimal is enabled)" if config.require_optimal else ""),
            ),
            "INFEASIBLE": (
                "INFEASIBLE",
                "no assignment satisfies all hard constraints",
            ),
            "MODEL_INVALID": ("MODEL_INVALID", "the CP-SAT model is invalid"),
            "UNKNOWN": (
                "SOLVER_UNKNOWN",
                "CP-SAT could not decide the model within its limits",
            ),
        }[status_name]
        return error(
            code,
            message,
            status_name,
            {"require_optimal": config.require_optimal},
            objective,
            bound,
        )

    if status_name != "OPTIMAL":  # pragma: no cover - defensive
        return error(
            "SOLVER_UNKNOWN", f"unexpected solver status {status_name}", status_name
        )

    assignments = _extract_assignments(
        solver, bundle, singles, emperors, previous_allocation
    )

    objective_value = int(round(solver.ObjectiveValue()))
    best_bound = int(round(solver.BestObjectiveBound()))
    main_penalty = sum(
        assignment.cost.weighted_total(config, cost_calculator.scaler)
        for assignment in assignments
    )
    tie_break_penalty = sum(assignment.tie_break for assignment in assignments)
    reconstructed = config.main_objective_scale * main_penalty + tie_break_penalty
    if reconstructed != objective_value:
        return error(
            "OUTPUT_VALIDATION_FAILED",
            "reconstructed objective does not match the solver objective",
            status_name,
            {"reconstructed": reconstructed, "solver_objective": objective_value},
            objective_value,
            best_bound,
        )

    booleans, integers = _variable_counts(bundle.model)
    solver_stats = {
        "engine": ENGINE_NAME,
        "status": status_name,
        "objective_value": objective_value,
        "main_penalty": main_penalty,
        "tie_break_penalty": tie_break_penalty,
        "main_objective_scale": config.main_objective_scale,
        "best_objective_bound": best_bound,
        "optimality_gap": objective_value - best_bound,
        "wall_time_seconds": solver.WallTime(),
        "user_time_seconds": solver.UserTime(),
        "num_conflicts": solver.NumConflicts(),
        "num_branches": solver.NumBranches(),
        "num_boolean_variables": booleans,
        "num_integer_variables": integers,
        "num_constraints": len(bundle.model.Proto().constraints),
        "eligible_single_assignment_count": bundle.eligible_single_assignment_count,
        "eligible_emperor_pair_count": bundle.eligible_emperor_pair_count,
        "peak_memory_rss_bytes": _peak_rss_bytes(),
        "response_stats": solver.ResponseStats(),
    }

    result = build_success_result(
        run_id=run_id,
        generated_at=generated_at,
        participants=participants,
        floor_plan=floor_plan,
        config=config,
        scaler=cost_calculator.scaler,
        assignments=assignments,
        solver_stats=solver_stats,
        bands=bands,
        hard_constraint_validation={
            "all_constraints_satisfied": True,
            "duplicate_seat_count": 0,
            "unassigned_count": 0,
            "tier_band_violation_count": 0,
            "contribution_order_violation_count": 0,
            "emperor_adjacency_violation_count": 0,
            "aisle_crossing_violation_count": 0,
            "accessibility_violation_count": 0,
            "blocked_seat_violation_count": 0,
            "front_fill_violation_count": 0,
        },
    )
    # Recount the hard-constraint block independently from the serialized
    # result itself, then reject the run if anything is violated.
    counters = compute_hard_constraint_validation(result)
    result["hard_constraint_validation"] = counters
    if not counters["all_constraints_satisfied"]:
        return error(
            "OUTPUT_VALIDATION_FAILED",
            "extracted solution violates hard constraints",
            status_name,
            counters,
            objective_value,
            best_bound,
        )

    schema_errors = validate_against_schema(result, "solver_result.schema.json")
    if schema_errors:
        return error(
            "OUTPUT_VALIDATION_FAILED",
            "result document failed JSON Schema validation",
            status_name,
            {"schema_errors": schema_errors},
            objective_value,
            best_bound,
        )
    return result


def _extract_assignments(
    solver: cp_model.CpSolver,
    bundle: ModelBundle,
    singles: list[SingleUnit],
    emperors: list[EmperorUnit],
    previous_allocation: PreviousAllocation | None,
) -> list[ExtractedAssignment]:
    def previous_for(participant_id: str) -> tuple[str, ...]:
        if previous_allocation is None:
            return ()
        return previous_allocation.seats_for(participant_id)

    assignments: list[ExtractedAssignment] = []
    for unit in singles:
        pid = unit.participant.participant_id
        chosen = [
            seat
            for seat in unit.eligible_seats
            if solver.Value(bundle.single_vars[(pid, seat.seat_id)]) == 1
        ]
        if len(chosen) != 1:  # pragma: no cover - HC1 guarantees exactly one
            raise RuntimeError(f"participant {pid} has {len(chosen)} seats")
        key = (pid, chosen[0].seat_id)
        assignments.append(
            ExtractedAssignment(
                participant=unit.participant,
                allocation_type="SINGLE",
                seats=(chosen[0],),
                pair=None,
                cost=bundle.single_costs[key],
                tie_break=bundle.tie_break_terms[key],
                effective_previous_seat_ids=previous_for(pid),
            )
        )
    for unit in emperors:
        pid = unit.participant.participant_id
        chosen_pairs = [
            pair
            for pair in unit.eligible_pairs
            if solver.Value(bundle.pair_vars[(pid, pair.pair_index)]) == 1
        ]
        if len(chosen_pairs) != 1:  # pragma: no cover - HC2 guarantees exactly one
            raise RuntimeError(f"emperor {pid} has {len(chosen_pairs)} pairs")
        pair = chosen_pairs[0]
        key = (pid, pair.pair_index)
        assignments.append(
            ExtractedAssignment(
                participant=unit.participant,
                allocation_type="EMPEROR_PAIR",
                seats=pair.seats,
                pair=pair,
                cost=bundle.pair_costs[key],
                tie_break=bundle.tie_break_terms[key],
                effective_previous_seat_ids=previous_for(pid),
            )
        )
    return assignments
