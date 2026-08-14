"""Precomputed integer soft-constraint cost matrices.

Every cost is a non-negative integer computed before model construction so
the CP-SAT objective stays purely integer (HC12). The four components map to
the soft constraints SC1 (priority-seat mismatch), SC2 (category-zone
mismatch), SC3 (movement after regeneration), and SC4 (activeness mismatch).

Normalization: the raw component scales are very different (movement can
reach several hundred on the 16x16 hall while priority mismatch tops out at
15), so with ``normalize_penalties`` enabled every raw component cost is
rescaled to the integer range 0..NORMALIZATION_SCALE by its theoretical
maximum before the weights are applied. The weights then act on comparable
quantities and keep their configured meaning.
"""

from __future__ import annotations

from dataclasses import dataclass

from seat_solver.models import (
    FloorPlan,
    Participant,
    PreviousAllocation,
    Seat,
    SolverConfig,
)
from seat_solver.preprocessing import EmperorUnit, SeatPair, SingleUnit

NORMALIZATION_SCALE = 100

COMPONENT_NAMES = ("priority_seat", "category_zone", "movement", "activeness")


@dataclass(frozen=True)
class PenaltyScaler:
    """Rescales raw component costs to 0..scale integers (round half up).

    ``normalized = round(scale * raw / max_raw)`` computed as
    ``(2 * scale * raw + max_raw) // (2 * max_raw)`` to stay integer-only.
    With ``normalize`` disabled the raw value passes through unchanged.
    """

    normalize: bool
    maxima: dict[str, int]
    scale: int = NORMALIZATION_SCALE

    def normalized(self, component: str, raw: int) -> int:
        if not self.normalize:
            return raw
        max_raw = max(1, self.maxima[component])
        return (2 * self.scale * raw + max_raw) // (2 * max_raw)


@dataclass(frozen=True)
class CostBreakdown:
    """Unweighted integer penalty components for one candidate assignment."""

    priority_seat: int
    category_zone: int
    movement: int
    activeness: int

    def raw_components(self) -> dict[str, int]:
        return {
            "priority_seat": self.priority_seat,
            "category_zone": self.category_zone,
            "movement": self.movement,
            "activeness": self.activeness,
        }

    def normalized_components(self, scaler: PenaltyScaler) -> dict[str, int]:
        return {
            component: scaler.normalized(component, raw)
            for component, raw in self.raw_components().items()
        }

    def weighted_components(
        self, config: SolverConfig, scaler: PenaltyScaler
    ) -> dict[str, int]:
        normalized = self.normalized_components(scaler)
        weights = {
            "priority_seat": config.priority_seat_weight,
            "category_zone": config.category_zone_weight,
            "movement": config.movement_weight,
            "activeness": config.activeness_weight,
        }
        return {
            component: weights[component] * normalized[component]
            for component in COMPONENT_NAMES
        }

    def weighted_total(self, config: SolverConfig, scaler: PenaltyScaler) -> int:
        return sum(self.weighted_components(config, scaler).values())


def desired_priority_rank(participant: Participant, config: SolverConfig) -> int:
    """SC1 target rank: when several rules apply, the highest priority
    (numerically lowest rank) wins."""
    ranks = [config.default_rank]
    if participant.requires_accessible_seat:
        ranks.append(config.accessible_rank)
    if participant.is_monk:
        ranks.append(config.monk_rank)
    if participant.is_elderly:
        ranks.append(config.elderly_rank)
    return min(ranks)


def activity_target_rank(
    activity: int, min_activity: int, max_activity: int, max_rank: int = 16
) -> int:
    """SC4 target rank in 1..max_rank using integer round-half-up arithmetic.

    Implements 1 + round((max_rank - 1) * (max - a) / max(1, max - min))
    without floats: round(n / d) with round-half-up equals (2n + d) // (2d)
    for n, d >= 0. ``max_rank`` is the floor plan's worst seat rank (16 for
    the 16-seat PJKIT rows).
    """
    span = max(1, max_activity - min_activity)
    numerator = (max_rank - 1) * (max_activity - activity)
    return 1 + (2 * numerator + span) // (2 * span)


def movement_cost_single(
    participant_prev_seat: Seat | None, seat: Seat, config: SolverConfig
) -> int:
    """SC3 for singles: zero when keeping the previous seat or when no
    previous seat exists; otherwise a fixed penalty plus integer row and
    column distances."""
    if participant_prev_seat is None:
        return 0
    if participant_prev_seat.seat_id == seat.seat_id:
        return 0
    return (
        config.fixed_move_penalty
        + config.row_distance_weight
        * abs(participant_prev_seat.row_number - seat.row_number)
        + config.column_distance_weight
        * abs(participant_prev_seat.physical_position - seat.physical_position)
    )


def movement_cost_pair(
    prev_pair_seats: tuple[Seat, Seat] | None, pair: SeatPair, config: SolverConfig
) -> int:
    """SC3 for Emperor units: zero for the identical previous pair, moderate
    for another pair in the same row, larger when the row changes."""
    if prev_pair_seats is None:
        return 0
    prev_ids = {s.seat_id for s in prev_pair_seats}
    if prev_ids == set(pair.seat_ids):
        return 0
    prev_row = prev_pair_seats[0].row_number
    prev_first_position = min(s.physical_position for s in prev_pair_seats)
    return (
        config.fixed_move_penalty
        + config.row_distance_weight * abs(prev_row - pair.row_number)
        + config.column_distance_weight * abs(prev_first_position - pair.first_position)
    )


def compute_component_maxima(
    floor_plan: FloorPlan, config: SolverConfig
) -> dict[str, int]:
    """Theoretical maximum raw cost per soft-constraint component.

    Used as the normalization denominators, so every component maps onto the
    same 0..NORMALIZATION_SCALE range regardless of its natural unit:

    - priority_seat / activeness: the largest possible rank difference given
      the configured desired ranks and the floor plan's priority ranks.
    - category_zone: twice the largest matrix entry (an Emperor pair sums the
      zone costs of its two seats).
    - movement: the fixed penalty plus the largest possible row and column
      distances on the floor plan.
    """
    max_rank = max(seat.priority_rank for seat in floor_plan.seats)
    desired_ranks = [
        config.accessible_rank,
        config.monk_rank,
        config.elderly_rank,
        config.default_rank,
    ]
    priority_max = max(
        max_rank - min(desired_ranks),
        max(desired_ranks) - min(config.emperor_pair_priorities.values(), default=1),
    )
    zone_max = 2 * max(
        cost for costs in config.category_zone_costs.values() for cost in costs.values()
    )
    movement_max = (
        config.fixed_move_penalty
        + config.row_distance_weight * (floor_plan.row_count - 1)
        + config.column_distance_weight * (floor_plan.seats_per_row - 1)
    )
    return {
        "priority_seat": max(1, priority_max),
        "category_zone": max(1, zone_max),
        "movement": max(1, movement_max),
        "activeness": max(1, max_rank - 1),
    }


class CostCalculator:
    """Computes and caches all unweighted cost components for eligible
    assignments. The activity rank normalisation uses the min and max event
    counts over the full participant list."""

    def __init__(
        self,
        participants: list[Participant],
        floor_plan: FloorPlan,
        config: SolverConfig,
        previous_allocation: PreviousAllocation | None,
    ) -> None:
        self._config = config
        self._floor_plan = floor_plan
        self._previous = previous_allocation
        activities = [p.events_joined_last_2_years for p in participants]
        self._min_activity = min(activities) if activities else 0
        self._max_activity = max(activities) if activities else 0
        self._max_rank = max(seat.priority_rank for seat in floor_plan.seats)
        self.component_maxima = compute_component_maxima(floor_plan, config)
        self.scaler = PenaltyScaler(
            normalize=config.normalize_penalties, maxima=self.component_maxima
        )

    def _previous_seats(self, participant: Participant) -> tuple[Seat, ...]:
        """Movement costs are driven solely by the previous-allocation input;
        with no previous allocation every movement cost is exactly zero."""
        if self._previous is None:
            return ()
        seat_ids = self._previous.seats_for(participant.participant_id)
        return tuple(
            self._floor_plan.seat_by_id(seat_id)
            for seat_id in seat_ids
            if self._floor_plan.has_seat(seat_id)
        )

    def activity_rank(self, participant: Participant) -> int:
        return activity_target_rank(
            participant.events_joined_last_2_years,
            self._min_activity,
            self._max_activity,
            self._max_rank,
        )

    def single_cost(self, unit: SingleUnit, seat: Seat) -> CostBreakdown:
        participant = unit.participant
        prev_seats = self._previous_seats(participant)
        prev_seat = prev_seats[0] if len(prev_seats) == 1 else None
        zone_costs = self._config.category_zone_costs[participant.participant_category]
        return CostBreakdown(
            priority_seat=abs(
                desired_priority_rank(participant, self._config) - seat.priority_rank
            ),
            category_zone=zone_costs[seat.zone],
            movement=movement_cost_single(prev_seat, seat, self._config),
            activeness=abs(self.activity_rank(participant) - seat.priority_rank),
        )

    def pair_cost(self, unit: EmperorUnit, pair: SeatPair) -> CostBreakdown:
        participant = unit.participant
        prev_seats = self._previous_seats(participant)
        prev_pair = (prev_seats[0], prev_seats[1]) if len(prev_seats) == 2 else None
        zone_costs = self._config.category_zone_costs[participant.participant_category]
        return CostBreakdown(
            priority_seat=abs(
                desired_priority_rank(participant, self._config) - pair.pair_priority
            ),
            category_zone=zone_costs[pair.seats[0].zone]
            + zone_costs[pair.seats[1].zone],
            movement=movement_cost_pair(prev_pair, pair, self._config),
            activeness=abs(self.activity_rank(participant) - pair.pair_priority),
        )
