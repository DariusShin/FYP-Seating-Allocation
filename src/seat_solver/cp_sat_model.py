"""CP-SAT model construction.

Builds a pure-integer assignment model:

- ``x[p, s]`` Boolean assignment variables for single-seat participants,
  created only for eligible seats (HC1, HC3, HC4, HC8, HC9). Eligibility is
  restricted to the participant tier's demand-derived band rows, which
  enforces band ordering (EMPEROR before BODHI before MERIT) and
  tier-exclusive rows by construction.
- ``y[e, k]`` Boolean pair-assignment variables for Emperor allocation units,
  created only for eligible valid pairs inside the Emperor band
  (HC2, HC6, HC7).
- Linear row expressions plus auxiliary boundary variables encode the
  contribution-ordering constraint HC5.
- The objective minimizes ``MAIN_OBJECTIVE_SCALE * MainPenalty + TieBreak``
  where the tie-break term is strictly dominated by any main-penalty change.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from seat_solver.cost_calculator import CostBreakdown, CostCalculator, PenaltyScaler
from seat_solver.models import FloorPlan, SolverConfig, TIER_NAMES
from seat_solver.preprocessing import (
    EmperorUnit,
    SeatPair,
    SingleUnit,
    TierBands,
    compute_row_fill_targets,
)


@dataclass
class ModelBundle:
    """The built model plus every lookup needed for extraction and auditing."""

    model: cp_model.CpModel
    single_vars: dict[tuple[str, str], cp_model.IntVar]
    pair_vars: dict[tuple[str, int], cp_model.IntVar]
    single_costs: dict[tuple[str, str], CostBreakdown]
    pair_costs: dict[tuple[str, int], CostBreakdown]
    tie_break_terms: dict[tuple[str, str] | tuple[str, int], int] = field(
        default_factory=dict
    )
    eligible_single_assignment_count: int = 0
    eligible_emperor_pair_count: int = 0
    max_tie_break_total: int = 0


def build_model(
    singles: list[SingleUnit],
    emperors: list[EmperorUnit],
    valid_pairs: list[SeatPair],
    floor_plan: FloorPlan,
    config: SolverConfig,
    cost_calculator: CostCalculator,
    bands: TierBands,
) -> ModelBundle:
    model = cp_model.CpModel()
    seat_order = {seat.seat_id: index for index, seat in enumerate(floor_plan.seats)}

    single_vars: dict[tuple[str, str], cp_model.IntVar] = {}
    pair_vars: dict[tuple[str, int], cp_model.IntVar] = {}
    single_costs: dict[tuple[str, str], CostBreakdown] = {}
    pair_costs: dict[tuple[str, int], CostBreakdown] = {}
    seat_occupants: dict[str, list[cp_model.IntVar]] = {
        seat.seat_id: [] for seat in floor_plan.seats
    }

    # HC1: every single-seat participant gets exactly one eligible seat.
    for unit in singles:
        pid = unit.participant.participant_id
        vars_for_unit = []
        for seat in unit.eligible_seats:
            var = model.NewBoolVar(f"x[{pid},{seat.seat_id}]")
            single_vars[(pid, seat.seat_id)] = var
            single_costs[(pid, seat.seat_id)] = cost_calculator.single_cost(unit, seat)
            seat_occupants[seat.seat_id].append(var)
            vars_for_unit.append(var)
        model.AddExactlyOne(vars_for_unit)

    # HC2 + HC6 + HC7: every Emperor unit gets exactly one valid adjacent pair.
    for unit in emperors:
        pid = unit.participant.participant_id
        vars_for_unit = []
        for pair in unit.eligible_pairs:
            var = model.NewBoolVar(f"y[{pid},{pair.pair_index}]")
            pair_vars[(pid, pair.pair_index)] = var
            pair_costs[(pid, pair.pair_index)] = cost_calculator.pair_cost(unit, pair)
            for seat in pair.seats:
                seat_occupants[seat.seat_id].append(var)
            vars_for_unit.append(var)
        model.AddExactlyOne(vars_for_unit)

    # HC3: at most one occupant per physical seat.
    for occupant_vars in seat_occupants.values():
        if len(occupant_vars) > 1:
            model.AddAtMostOne(occupant_vars)

    _add_contribution_ordering(
        model,
        singles,
        emperors,
        valid_pairs,
        single_vars,
        pair_vars,
        floor_plan,
        config,
    )

    if config.enforce_front_fill:
        _add_front_fill(
            model,
            singles,
            emperors,
            valid_pairs,
            single_vars,
            pair_vars,
            floor_plan,
            bands,
        )

    if config.enforce_middle_fill:
        _add_middle_fill(model, floor_plan, seat_occupants)

    bundle = ModelBundle(
        model=model,
        single_vars=single_vars,
        pair_vars=pair_vars,
        single_costs=single_costs,
        pair_costs=pair_costs,
        eligible_single_assignment_count=len(single_vars),
        eligible_emperor_pair_count=len(pair_vars),
    )
    _add_objective(
        bundle,
        singles,
        emperors,
        valid_pairs,
        seat_order,
        config,
        cost_calculator.scaler,
    )
    return bundle


def _row_expression(
    unit_key: str,
    seats_or_pairs: list[tuple[cp_model.IntVar, int]],
) -> cp_model.LinearExpr:
    """Linear expression for the assigned zero-based row: because exactly one
    assignment variable of the unit is 1, the weighted sum equals its row."""
    return sum(var * row_index for var, row_index in seats_or_pairs)


def _add_contribution_ordering(
    model: cp_model.CpModel,
    singles: list[SingleUnit],
    emperors: list[EmperorUnit],
    valid_pairs: list[SeatPair],
    single_vars: dict[tuple[str, str], cp_model.IntVar],
    pair_vars: dict[tuple[str, int], cp_model.IntVar],
    floor_plan: FloorPlan,
    config: SolverConfig,
) -> None:
    """HC5: inside each tier, strictly higher contribution implies an equal or
    earlier row.

    Encoding: sort the tier's distinct contribution values descending into
    levels; between consecutive levels g and g+1 introduce an integer boundary
    variable b with row(i) <= b for every unit i in level g and b <= row(j)
    for every unit j in level g+1. Transitivity over the chain of boundaries
    yields row(i) <= row(j) for every strictly-greater contribution pair,
    while units with equal contribution stay mutually unordered.
    """
    units_by_tier: dict[str, list[tuple[int, cp_model.LinearExpr]]] = {
        tier: [] for tier in TIER_NAMES
    }
    for unit in singles:
        pid = unit.participant.participant_id
        expr = _row_expression(
            pid,
            [
                (single_vars[(pid, seat.seat_id)], seat.row_index)
                for seat in unit.eligible_seats
            ],
        )
        units_by_tier[unit.participant.contribution_tier].append(
            (unit.participant.contribution_amount_rm, expr)
        )
    for unit in emperors:
        pid = unit.participant.participant_id
        expr = _row_expression(
            pid,
            [
                (pair_vars[(pid, pair.pair_index)], pair.row_index)
                for pair in unit.eligible_pairs
            ],
        )
        units_by_tier["EMPEROR"].append((unit.participant.contribution_amount_rm, expr))

    max_row_index = floor_plan.row_count - 1
    for tier, units in units_by_tier.items():
        if len(units) < 2:
            continue
        levels: dict[int, list[cp_model.LinearExpr]] = {}
        for contribution, expr in units:
            levels.setdefault(contribution, []).append(expr)
        ordered_contributions = sorted(levels.keys(), reverse=True)
        for higher, lower in zip(ordered_contributions, ordered_contributions[1:]):
            boundary = model.NewIntVar(
                0, max_row_index, f"row_boundary[{tier},{higher}>{lower}]"
            )
            for expr in levels[higher]:
                model.Add(expr <= boundary)
            for expr in levels[lower]:
                model.Add(boundary <= expr)


def _add_front_fill(
    model: cp_model.CpModel,
    singles: list[SingleUnit],
    emperors: list[EmperorUnit],
    valid_pairs: list[SeatPair],
    single_vars: dict[tuple[str, str], cp_model.IntVar],
    pair_vars: dict[tuple[str, int], cp_model.IntVar],
    floor_plan: FloorPlan,
    bands: TierBands,
) -> None:
    """HC13: rows fill front to back inside each tier band.

    Every seat of row r outranks every seat of row r+1 within a band, so a
    later row may only hold occupants once every earlier band row is full.
    Because the tier demand is fixed before solving, each band row's occupancy
    is fully determined by the band derivation; the constraint is the exact
    equality ``sum of assignment variables on row r == target(r)`` per band
    row (pair variables for the Emperor band, seat variables otherwise).
    """
    participants = [unit.participant for unit in singles] + [
        unit.participant for unit in emperors
    ]
    targets = compute_row_fill_targets(participants, floor_plan, valid_pairs, bands)

    emperor_row_vars: dict[int, list[cp_model.IntVar]] = {}
    for unit in emperors:
        pid = unit.participant.participant_id
        for pair in unit.eligible_pairs:
            emperor_row_vars.setdefault(pair.row_number, []).append(
                pair_vars[(pid, pair.pair_index)]
            )
    for row_number, target in targets["EMPEROR"].items():
        model.Add(sum(emperor_row_vars.get(row_number, [])) == target)

    single_row_vars: dict[tuple[str, int], list[cp_model.IntVar]] = {}
    for unit in singles:
        pid = unit.participant.participant_id
        tier = unit.participant.contribution_tier
        for seat in unit.eligible_seats:
            single_row_vars.setdefault((tier, seat.row_number), []).append(
                single_vars[(pid, seat.seat_id)]
            )
    for tier in ("BODHI", "MERIT"):
        for row_number, target in targets[tier].items():
            model.Add(sum(single_row_vars.get((tier, row_number), [])) == target)


def _add_middle_fill(
    model: cp_model.CpModel,
    floor_plan: FloorPlan,
    seat_occupants: dict[str, list[cp_model.IntVar]],
) -> None:
    """HC14: every row fills outward from the centre aisle on both sides.

    For each row side, order the non-blocked seats by physical distance from
    the aisle and require occ(outer) <= occ(inner) for each consecutive pair,
    where occ(s) is the sum of the seat's assignment variables (0 or 1 by
    HC3). Transitivity makes each side's occupied seats one contiguous block
    that starts at the aisle, ruling out gaps such as
    ``[X][ ][X]`` between the aisle and the outermost occupied seat.
    Uses ``physical_position``, never ``priority_rank``.
    """
    aisle = floor_plan.aisle_after_position
    for row_number in range(1, floor_plan.row_count + 1):
        row_seats = [
            seat for seat in floor_plan.seats_in_row(row_number) if not seat.is_blocked
        ]
        left_outward = sorted(
            (seat for seat in row_seats if seat.physical_position <= aisle),
            key=lambda seat: seat.physical_position,
            reverse=True,
        )
        right_outward = sorted(
            (seat for seat in row_seats if seat.physical_position > aisle),
            key=lambda seat: seat.physical_position,
        )
        for side in (left_outward, right_outward):
            for inner, outer in zip(side, side[1:]):
                model.Add(
                    sum(seat_occupants[outer.seat_id])
                    <= sum(seat_occupants[inner.seat_id])
                )


def _add_objective(
    bundle: ModelBundle,
    singles: list[SingleUnit],
    emperors: list[EmperorUnit],
    valid_pairs: list[SeatPair],
    seat_order: dict[str, int],
    config: SolverConfig,
    scaler: PenaltyScaler,
) -> None:
    """Objective: MAIN_OBJECTIVE_SCALE * weighted main penalty + tie-break.

    With ``normalize_penalties`` enabled the weighted penalty of a candidate
    is ``sum(weight_c * normalized_c)`` where each component is rescaled to
    0..100 by its theoretical maximum, so the four weights compare like for
    like (see ``cost_calculator.PenaltyScaler``).

    The tie-break term for a candidate is ``unit_rank * option_index`` where
    ``unit_rank`` is the unit's 1-based position in participant-id order and
    ``option_index`` is the deterministic global seat index (singles) or pair
    index (Emperor units). Weighting by the unit rank breaks the swap symmetry
    between equal-cost participants (swapping units p, q between options a, b
    changes the sum by (rank_p - rank_q) * (index_a - index_b) != 0), so the
    optimum is a single canonical layout. Dominance: the maximum achievable
    tie-break total is recorded in ``max_tie_break_total`` and must stay
    strictly below ``main_objective_scale`` so a one-unit main-penalty
    difference always outweighs the whole tie-break term.
    """
    scale = config.main_objective_scale
    terms = []
    max_tie_break = 0

    unit_rank = {
        pid: rank + 1
        for rank, pid in enumerate(
            sorted(
                [unit.participant.participant_id for unit in singles]
                + [unit.participant.participant_id for unit in emperors]
            )
        )
    }

    for unit in singles:
        pid = unit.participant.participant_id
        unit_max = 0
        for seat in unit.eligible_seats:
            key = (pid, seat.seat_id)
            var = bundle.single_vars[key]
            weighted = bundle.single_costs[key].weighted_total(config, scaler)
            tie_break = unit_rank[pid] * seat_order[seat.seat_id]
            bundle.tie_break_terms[key] = tie_break
            terms.append(var * (scale * weighted + tie_break))
            unit_max = max(unit_max, tie_break)
        max_tie_break += unit_max

    for unit in emperors:
        pid = unit.participant.participant_id
        unit_max = 0
        for pair in unit.eligible_pairs:
            key = (pid, pair.pair_index)
            var = bundle.pair_vars[key]
            weighted = bundle.pair_costs[key].weighted_total(config, scaler)
            tie_break = unit_rank[pid] * pair.pair_index
            bundle.tie_break_terms[key] = tie_break
            terms.append(var * (scale * weighted + tie_break))
            unit_max = max(unit_max, tie_break)
        max_tie_break += unit_max

    bundle.max_tie_break_total = max_tie_break
    if max_tie_break >= scale:
        raise ValueError(
            f"main_objective_scale ({scale}) must exceed the maximum possible "
            f"tie-break total ({max_tie_break}); increase the scale in the config"
        )
    bundle.model.Minimize(sum(terms))
