"""Frontend-friendly JSON result construction.

Builds plain-JSON dictionaries (no OR-Tools objects, sets, tuples, or enums)
for both successful and error outcomes so the output stays renderable by the
Buddy seat-map frontend in every case.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from seat_solver.cost_calculator import (
    COMPONENT_NAMES,
    CostBreakdown,
    PenaltyScaler,
)
from seat_solver.models import (
    CASE_STUDY_NAME,
    FloorPlan,
    Participant,
    Seat,
    SCHEMA_VERSION,
    SolverConfig,
)
from seat_solver.preprocessing import SeatPair, TierBands


@dataclass(frozen=True)
class ExtractedAssignment:
    """One solved allocation unit extracted from the CP-SAT solution."""

    participant: Participant
    allocation_type: str  # "SINGLE" or "EMPEROR_PAIR"
    seats: tuple[Seat, ...]
    pair: SeatPair | None
    cost: CostBreakdown
    tie_break: int
    effective_previous_seat_ids: tuple[str, ...]

    @property
    def seat_ids(self) -> tuple[str, ...]:
        return tuple(seat.seat_id for seat in self.seats)

    @property
    def moved(self) -> bool | None:
        if not self.effective_previous_seat_ids:
            return None
        return set(self.effective_previous_seat_ids) != set(self.seat_ids)


def _display_names(assignment: ExtractedAssignment) -> dict[str, str]:
    """Per-seat display names.

    An Emperor with a named adjacent guest shows the primary name on the
    better-ranked seat and the guest on the other seat; with a null guest name
    both seats display the primary participant's name.
    """
    participant = assignment.participant
    if assignment.allocation_type == "SINGLE":
        return {assignment.seats[0].seat_id: participant.full_name}
    ordered = sorted(assignment.seats, key=lambda seat: seat.priority_rank)
    names = {ordered[0].seat_id: participant.full_name}
    if participant.adjacent_person_name is None:
        names[ordered[1].seat_id] = participant.full_name
    else:
        names[ordered[1].seat_id] = participant.adjacent_person_name
    return names


def input_summary(
    participants: list[Participant], floor_plan: FloorPlan
) -> dict[str, int]:
    emperor = sum(1 for p in participants if p.contribution_tier == "EMPEROR")
    bodhi = sum(1 for p in participants if p.contribution_tier == "BODHI")
    merit = sum(1 for p in participants if p.contribution_tier == "MERIT")
    required = 2 * emperor + bodhi + merit
    blocked = sum(1 for seat in floor_plan.seats if seat.is_blocked)
    available = floor_plan.total_seats - blocked
    return {
        "primary_participant_count": len(participants),
        "emperor_count": emperor,
        "bodhi_count": bodhi,
        "merit_count": merit,
        "required_seat_count": required,
        "total_seat_count": floor_plan.total_seats,
        "blocked_seat_count": blocked,
        "available_seat_count": available,
        "empty_seat_count": available - required,
    }


def build_success_result(
    run_id: str,
    generated_at: str,
    participants: list[Participant],
    floor_plan: FloorPlan,
    config: SolverConfig,
    scaler: PenaltyScaler,
    assignments: list[ExtractedAssignment],
    solver_stats: dict[str, Any],
    bands: TierBands,
    hard_constraint_validation: dict[str, Any],
) -> dict[str, Any]:
    seat_to_assignment: dict[str, ExtractedAssignment] = {}
    seat_display: dict[str, str] = {}
    for assignment in assignments:
        seat_display.update(_display_names(assignment))
        for seat_id in assignment.seat_ids:
            seat_to_assignment[seat_id] = assignment

    unweighted_totals = dict.fromkeys(COMPONENT_NAMES, 0)
    normalized_totals = dict.fromkeys(COMPONENT_NAMES, 0)
    weighted_totals = dict.fromkeys(COMPONENT_NAMES, 0)
    tie_break_total = 0
    assignment_payloads: list[dict[str, Any]] = []
    for assignment in sorted(assignments, key=lambda a: a.participant.participant_id):
        cost = assignment.cost
        raw = cost.raw_components()
        normalized = cost.normalized_components(scaler)
        weighted = cost.weighted_components(config, scaler)
        for key in COMPONENT_NAMES:
            unweighted_totals[key] += raw[key]
            normalized_totals[key] += normalized[key]
            weighted_totals[key] += weighted[key]
        tie_break_total += assignment.tie_break

        participant = assignment.participant
        assignment_payloads.append(
            {
                "participant_id": participant.participant_id,
                "full_name": participant.full_name,
                "contribution_tier": participant.contribution_tier,
                "contribution_amount_rm": participant.contribution_amount_rm,
                "participant_category": participant.participant_category,
                "is_monk": participant.is_monk,
                "is_elderly": participant.is_elderly,
                "requires_accessible_seat": participant.requires_accessible_seat,
                "events_joined_last_2_years": participant.events_joined_last_2_years,
                "allocation_type": assignment.allocation_type,
                "seat_ids": list(assignment.seat_ids),
                "seats": [
                    {
                        "seat_id": seat.seat_id,
                        "row_number": seat.row_number,
                        "physical_position": seat.physical_position,
                        "priority_rank": seat.priority_rank,
                        "zone": seat.zone,
                        "display_name": seat_display[seat.seat_id],
                    }
                    for seat in sorted(
                        assignment.seats, key=lambda s: s.physical_position
                    )
                ],
                "pair_priority": (
                    assignment.pair.pair_priority if assignment.pair else None
                ),
                "previous_seat_ids": list(assignment.effective_previous_seat_ids),
                "moved": assignment.moved,
                "penalty": {
                    "unweighted": raw,
                    "normalized": normalized,
                    "weighted": {
                        **weighted,
                        "total": cost.weighted_total(config, scaler),
                    },
                },
            }
        )

    rows_payload: list[dict[str, Any]] = []
    empty_seat_ids: list[str] = []
    for row_number in range(1, floor_plan.row_count + 1):
        row_seats = floor_plan.seats_in_row(row_number)
        seats_payload = []
        for seat in row_seats:
            if seat.is_blocked:
                occupancy = "BLOCKED"
            elif seat.seat_id in seat_to_assignment:
                occupancy = "OCCUPIED"
            else:
                occupancy = "EMPTY"
                empty_seat_ids.append(seat.seat_id)
            occupant = seat_to_assignment.get(seat.seat_id)
            seats_payload.append(
                {
                    "seat_id": seat.seat_id,
                    "physical_position": seat.physical_position,
                    "priority_rank": seat.priority_rank,
                    "side": seat.side,
                    "zone": seat.zone,
                    "is_accessible": seat.is_accessible,
                    "is_blocked": seat.is_blocked,
                    "occupancy_status": occupancy,
                    "participant_id": (
                        occupant.participant.participant_id if occupant else None
                    ),
                    "display_name": seat_display.get(seat.seat_id),
                }
            )
        rows_payload.append(
            {
                "row_number": row_number,
                "tier_band": bands.tier_of_row(row_number),
                "seats": seats_payload,
            }
        )

    weighted_summary = {
        **weighted_totals,
        "tie_break": tie_break_total,
        "total": sum(weighted_totals.values()) + tie_break_total,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": generated_at,
        "case_study": CASE_STUDY_NAME,
        "status": "success",
        "input_summary": input_summary(participants, floor_plan),
        "weights": config.weights_dict(),
        "constraint_config": {
            "enforce_front_fill": config.enforce_front_fill,
            "enforce_middle_fill": config.enforce_middle_fill,
            "normalize_penalties": config.normalize_penalties,
            "normalization_scale": scaler.scale,
            "component_maxima": dict(scaler.maxima),
        },
        "solver": solver_stats,
        "penalty_summary": {
            "unweighted": unweighted_totals,
            "normalized": normalized_totals,
            "weighted": weighted_summary,
        },
        "tier_bands": {tier: list(rows) for tier, rows in bands.rows.items()},
        "floor_plan": {
            "row_count": floor_plan.row_count,
            "seats_per_row": floor_plan.seats_per_row,
            "total_seats": floor_plan.total_seats,
            "aisle_after_position": floor_plan.aisle_after_position,
            "rows": rows_payload,
        },
        "assignments": assignment_payloads,
        "empty_seat_ids": empty_seat_ids,
        "unassigned_participants": [],
        "hard_constraint_validation": hard_constraint_validation,
    }


def build_error_result(
    run_id: str,
    generated_at: str,
    code: str,
    message: str,
    solver_status: str | None = None,
    details: dict[str, Any] | None = None,
    wall_time_seconds: float | None = None,
    objective_value: int | None = None,
    best_objective_bound: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": generated_at,
        "case_study": CASE_STUDY_NAME,
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "solver_status": solver_status,
            "details": details or {},
        },
        "solver": {
            "wall_time_seconds": wall_time_seconds,
            "objective_value": objective_value,
            "best_objective_bound": best_objective_bound,
        },
    }
