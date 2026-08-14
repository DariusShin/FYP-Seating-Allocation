"""Input validation, capacity checks, tier-band derivation, and
allocation-unit construction.

Everything here runs before CP-SAT model construction so that impossible
inputs are rejected with structured errors instead of solver failures, and so
that decision variables are only created for eligible combinations (HC4, HC8,
HC9 are enforced structurally).

Tier bands: PJKIT tiers occupy contiguous blocks of rows ordered
EMPEROR -> BODHI -> MERIT from the front of the hall, with boundaries
determined by each event's tier demand rather than by fixed venue zones, and
with every row belonging to at most one tier (tier-exclusive rows). Because
demand is known before solving and rows fill front to back, the band of every
tier is fully determined here (``compute_tier_bands``) and eligibility can be
restricted to band rows, which enforces band ordering and row exclusivity by
construction.
"""

from __future__ import annotations

from dataclasses import dataclass

from seat_solver.models import (
    CATEGORY_NAMES,
    FloorPlan,
    Participant,
    PreviousAllocation,
    Seat,
    SolverConfig,
    TIER_NAMES,
)


@dataclass(frozen=True)
class SeatPair:
    """One valid adjacent Emperor seat pair (never spanning the aisle)."""

    pair_index: int
    row_number: int
    row_index: int
    first_position: int
    second_position: int
    pair_priority: int
    seats: tuple[Seat, Seat]

    @property
    def seat_ids(self) -> tuple[str, str]:
        return (self.seats[0].seat_id, self.seats[1].seat_id)

    @property
    def is_accessible(self) -> bool:
        return any(seat.is_accessible for seat in self.seats)


@dataclass(frozen=True)
class TierBands:
    """The demand-derived contiguous row bands, ordered E -> B -> M.

    ``rows[tier]`` is the tuple of row numbers the tier occupies. Unused rows
    behind the Merit band belong to no tier. ``unit_targets[tier]`` maps each
    band row to the exact number of allocation units (pairs for EMPEROR,
    seats otherwise) placed on it under front-to-back filling.
    """

    rows: dict[str, tuple[int, ...]]
    unit_targets: dict[str, dict[int, int]]

    def tier_of_row(self, row_number: int) -> str | None:
        for tier, rows in self.rows.items():
            if row_number in rows:
                return tier
        return None


@dataclass(frozen=True)
class SingleUnit:
    """A one-seat allocation unit (Bodhi or Merit participant)."""

    participant: Participant
    eligible_seats: tuple[Seat, ...]


@dataclass(frozen=True)
class EmperorUnit:
    """A two-seat Emperor allocation unit assigned to exactly one valid pair."""

    participant: Participant
    eligible_pairs: tuple[SeatPair, ...]


@dataclass(frozen=True)
class StructuredError:
    code: str
    message: str
    details: dict


def validate_inputs(
    participants: list[Participant],
    floor_plan: FloorPlan,
    config: SolverConfig,
    previous_allocation: PreviousAllocation | None = None,
) -> StructuredError | None:
    """Structural validation of the input documents (error code INVALID_INPUT)."""
    problems: list[str] = []

    seen_ids: set[str] = set()
    for p in participants:
        if p.participant_id in seen_ids:
            problems.append(f"duplicate participant_id {p.participant_id}")
        seen_ids.add(p.participant_id)
        if p.contribution_tier not in TIER_NAMES:
            problems.append(f"{p.participant_id}: unknown tier {p.contribution_tier!r}")
            continue
        if p.participant_category not in CATEGORY_NAMES:
            problems.append(
                f"{p.participant_id}: unknown category {p.participant_category!r}"
            )
        if not config.tiers[p.contribution_tier].contains(p.contribution_amount_rm):
            problems.append(
                f"{p.participant_id}: contribution RM{p.contribution_amount_rm} "
                f"is outside tier {p.contribution_tier}"
            )
        if p.contribution_amount_rm < 0:
            problems.append(f"{p.participant_id}: negative contribution")
        if p.events_joined_last_2_years < 0:
            problems.append(f"{p.participant_id}: negative event count")
        expected_prev = 2 if p.contribution_tier == "EMPEROR" else 1
        if p.previous_seat_ids and len(p.previous_seat_ids) != expected_prev:
            problems.append(
                f"{p.participant_id}: previous_seat_ids must contain "
                f"{expected_prev} seats when present"
            )

    seat_ids: set[str] = set()
    for seat in floor_plan.seats:
        if seat.seat_id in seat_ids:
            problems.append(f"duplicate seat_id {seat.seat_id}")
        seat_ids.add(seat.seat_id)
    if floor_plan.total_seats != floor_plan.row_count * floor_plan.seats_per_row:
        problems.append(
            "floor plan seat count does not equal row_count * seats_per_row"
        )

    if previous_allocation is not None:
        used: set[str] = set()
        for pid, seats in previous_allocation.allocations.items():
            for seat_id in seats:
                if seat_id in used:
                    problems.append(
                        f"previous allocation reuses physical seat {seat_id}"
                    )
                used.add(seat_id)
                if not floor_plan.has_seat(seat_id):
                    problems.append(
                        f"previous allocation of {pid} references unknown seat "
                        f"{seat_id}"
                    )

    if problems:
        return StructuredError(
            code="INVALID_INPUT",
            message="input validation failed",
            details={"problems": problems},
        )
    return None


def build_valid_pairs(floor_plan: FloorPlan, config: SolverConfig) -> list[SeatPair]:
    """Enumerate the valid Emperor pairs K over every row of the hall.

    Pairs are the configured physical-position pairs. The centre aisle sits
    between positions ``aisle_after_position`` and ``aisle_after_position +
    1``; no configured pair may span it, and pairs containing a blocked seat
    are excluded (HC7, HC9). Tier-band eligibility is applied later, once the
    bands are derived from demand.
    """
    pairs: list[SeatPair] = []
    aisle = floor_plan.aisle_after_position
    for row_number in range(1, floor_plan.row_count + 1):
        row_seats = {
            s.physical_position: s for s in floor_plan.seats_in_row(row_number)
        }
        for (first, second), priority in sorted(config.emperor_pair_priorities.items()):
            if first <= aisle < second:
                raise ValueError(
                    f"configured pair {first}-{second} crosses the centre aisle"
                )
            seat_a, seat_b = row_seats.get(first), row_seats.get(second)
            if seat_a is None or seat_b is None:
                continue
            if seat_a.is_blocked or seat_b.is_blocked:
                continue
            pairs.append(
                SeatPair(
                    pair_index=len(pairs),
                    row_number=row_number,
                    row_index=row_number - 1,
                    first_position=first,
                    second_position=second,
                    pair_priority=priority,
                    seats=(seat_a, seat_b),
                )
            )
    return pairs


def check_total_capacity(
    participants: list[Participant], floor_plan: FloorPlan
) -> StructuredError | None:
    """HC11 (first stage): total seat demand against non-blocked capacity.

    Runs before the band derivation so an over-capacity event is reported as
    ``CAPACITY_EXCEEDED`` rather than as a band-packing failure.
    """
    required_seats = sum(
        2 if p.contribution_tier == "EMPEROR" else 1 for p in participants
    )
    available = sum(1 for s in floor_plan.seats if not s.is_blocked)
    if required_seats > available:
        return StructuredError(
            code="CAPACITY_EXCEEDED",
            message=(
                f"required seats ({required_seats}) exceed available seats "
                f"({available})"
            ),
            details={"required_seats": required_seats, "available_seats": available},
        )
    return None


def compute_tier_bands(
    participants: list[Participant],
    floor_plan: FloorPlan,
    valid_pairs: list[SeatPair],
) -> TierBands | StructuredError:
    """Derive the demand-driven tier bands by front-to-back packing (HC4).

    Rows are consumed in order 1..N by the tiers in precedence order
    EMPEROR -> BODHI -> MERIT. The Emperor tier consumes rows by valid-pair
    capacity, the single-seat tiers by non-blocked seat capacity. A tier's
    last row may be only partially used, but it still belongs exclusively to
    that tier (tier-exclusive rows): the next tier starts on the following
    row. Rows behind the Merit band remain unassigned. Returns a structured
    ``TIER_CAPACITY_EXCEEDED`` error when the hall runs out of rows.
    """
    counts = {tier: 0 for tier in TIER_NAMES}
    for p in participants:
        counts[p.contribution_tier] += 1

    pair_capacity: dict[int, int] = {}
    for pair in valid_pairs:
        pair_capacity[pair.row_number] = pair_capacity.get(pair.row_number, 0) + 1
    seat_capacity: dict[int, int] = {}
    for seat in floor_plan.seats:
        if not seat.is_blocked:
            seat_capacity[seat.row_number] = seat_capacity.get(seat.row_number, 0) + 1

    rows: dict[str, tuple[int, ...]] = {}
    unit_targets: dict[str, dict[int, int]] = {}
    next_row = 1
    for tier in TIER_NAMES:
        capacity = pair_capacity if tier == "EMPEROR" else seat_capacity
        remaining = counts[tier]
        band_rows: list[int] = []
        targets: dict[int, int] = {}
        while remaining > 0:
            if next_row > floor_plan.row_count:
                return StructuredError(
                    code="TIER_CAPACITY_EXCEEDED",
                    message=(
                        f"tier bands do not fit: {tier} still needs {remaining} "
                        f"unit(s) beyond row {floor_plan.row_count}"
                    ),
                    details={
                        "tier": tier,
                        "unplaced_units": remaining,
                        "row_count": floor_plan.row_count,
                        "tier_demand": counts,
                    },
                )
            take = min(remaining, capacity.get(next_row, 0))
            if take > 0:
                band_rows.append(next_row)
                targets[next_row] = take
                remaining -= take
            next_row += 1
        rows[tier] = tuple(band_rows)
        unit_targets[tier] = targets
    return TierBands(rows=rows, unit_targets=unit_targets)


def check_capacity(
    participants: list[Participant],
    floor_plan: FloorPlan,
    config: SolverConfig,
    valid_pairs: list[SeatPair],
    bands: TierBands,
) -> StructuredError | None:
    """HC11: total, per-band, and accessibility capacity validation.

    Runs after ``compute_tier_bands`` (which already guarantees the bands fit
    the hall) and additionally verifies total seat demand and that each
    tier's accessible demand can be met inside its own band.
    """
    counts = {tier: 0 for tier in TIER_NAMES}
    accessible_demand = {tier: 0 for tier in TIER_NAMES}
    for p in participants:
        counts[p.contribution_tier] += 1
        if p.requires_accessible_seat:
            accessible_demand[p.contribution_tier] += 1

    required_seats = 2 * counts["EMPEROR"] + counts["BODHI"] + counts["MERIT"]
    available = sum(1 for s in floor_plan.seats if not s.is_blocked)
    if required_seats > available:
        return StructuredError(
            code="CAPACITY_EXCEEDED",
            message=(
                f"required seats ({required_seats}) exceed available seats "
                f"({available})"
            ),
            details={"required_seats": required_seats, "available_seats": available},
        )

    tier_problems: list[str] = []
    emperor_rows = set(bands.rows["EMPEROR"])
    band_pairs = [pair for pair in valid_pairs if pair.row_number in emperor_rows]
    if counts["EMPEROR"] > len(band_pairs):
        tier_problems.append(
            f"EMPEROR demand {counts['EMPEROR']} exceeds band pair capacity "
            f"{len(band_pairs)}"
        )
    accessible_pairs = sum(1 for pair in band_pairs if pair.is_accessible)
    if accessible_demand["EMPEROR"] > accessible_pairs:
        tier_problems.append(
            f"EMPEROR accessible demand {accessible_demand['EMPEROR']} exceeds "
            f"accessible pair capacity {accessible_pairs} inside the Emperor band"
        )

    for tier in ("BODHI", "MERIT"):
        band_rows = set(bands.rows[tier])
        band_seats = [
            s
            for s in floor_plan.seats
            if s.row_number in band_rows and not s.is_blocked
        ]
        if counts[tier] > len(band_seats):
            tier_problems.append(
                f"{tier} demand {counts[tier]} exceeds band capacity {len(band_seats)}"
            )
        accessible_supply = sum(1 for s in band_seats if s.is_accessible)
        if accessible_demand[tier] > accessible_supply:
            tier_problems.append(
                f"{tier} accessible demand {accessible_demand[tier]} exceeds "
                f"accessible capacity {accessible_supply} inside the {tier} band"
            )

    if tier_problems:
        return StructuredError(
            code="TIER_CAPACITY_EXCEEDED",
            message="tier band capacity exceeded",
            details={"problems": tier_problems},
        )
    return None


def compute_row_fill_targets(
    participants: list[Participant],
    floor_plan: FloorPlan,
    valid_pairs: list[SeatPair],
    bands: TierBands,
) -> dict[str, dict[int, int]]:
    """HC13 (front-fill): exact per-row occupancy targets for each tier band.

    Inside a tier band every row outranks the row behind it (even the best
    seat of row r+1 is lower priority than the worst seat of row r), so rows
    must fill front to back. Because tier demand is known before solving, the
    occupancy of every band row is fully determined by the band derivation;
    the targets are exactly ``bands.unit_targets``.

    Returns ``{tier: {row_number: required_unit_count}}``.
    """
    return {tier: dict(bands.unit_targets[tier]) for tier in TIER_NAMES}


def compute_allowed_rows(
    participants: list[Participant], bands: TierBands
) -> dict[str, set[int]]:
    """Per-participant allowed rows implied by front-fill and ordering (HC5,
    HC13).

    With front-fill enforced, every band row's unit count is fixed
    (``bands.unit_targets``), and within-tier contribution ordering packs the
    tier's contribution levels front to back: sorting a tier's units by
    contribution descending, the units of one contribution level occupy a
    contiguous block of packing positions, and a unit may only sit on a row
    whose position interval intersects its level's block. This is a pure
    domain reduction — it removes only combinations that the hard constraints
    already exclude — but it shrinks the CP-SAT model dramatically for
    demand-heavy tiers.
    """
    allowed: dict[str, set[int]] = {}
    for tier in TIER_NAMES:
        members = [p for p in participants if p.contribution_tier == tier]
        if not members:
            continue
        levels: dict[int, list[Participant]] = {}
        for p in members:
            levels.setdefault(p.contribution_amount_rm, []).append(p)
        targets = bands.unit_targets[tier]
        rows_sorted = sorted(targets)
        higher = 0
        for contribution in sorted(levels, reverse=True):
            group = levels[contribution]
            first_position = higher + 1
            last_position = higher + len(group)
            rows_ok: set[int] = set()
            cumulative_before = 0
            for row_number in rows_sorted:
                cumulative_after = cumulative_before + targets[row_number]
                if (
                    cumulative_before < last_position
                    and cumulative_after >= first_position
                ):
                    rows_ok.add(row_number)
                cumulative_before = cumulative_after
            for p in group:
                allowed[p.participant_id] = rows_ok
            higher = last_position
    return allowed


def build_allocation_units(
    participants: list[Participant],
    floor_plan: FloorPlan,
    valid_pairs: list[SeatPair],
    bands: TierBands,
    allowed_rows: dict[str, set[int]] | None = None,
) -> tuple[list[SingleUnit], list[EmperorUnit]]:
    """Convert participant records into allocation units with eligible options.

    Eligibility encodes HC4 (demand-derived tier band, hence band ordering
    and tier-exclusive rows), HC8 (accessibility), and HC9 (blocked seats)
    by never creating an ineligible combination. When ``allowed_rows`` is
    provided (front-fill enforced), eligibility is further reduced to the
    rows implied by contribution-level packing (``compute_allowed_rows``).
    """
    singles: list[SingleUnit] = []
    emperors: list[EmperorUnit] = []
    emperor_rows = set(bands.rows["EMPEROR"])

    def rows_for(p: Participant, band: set[int]) -> set[int]:
        if allowed_rows is None:
            return band
        return band & allowed_rows.get(p.participant_id, band)

    for p in participants:
        if p.contribution_tier == "EMPEROR":
            usable_rows = rows_for(p, emperor_rows)
            eligible_pairs = tuple(
                pair
                for pair in valid_pairs
                if pair.row_number in usable_rows
                and (not p.requires_accessible_seat or pair.is_accessible)
            )
            emperors.append(EmperorUnit(participant=p, eligible_pairs=eligible_pairs))
        else:
            usable_rows = rows_for(p, set(bands.rows[p.contribution_tier]))
            eligible_seats = tuple(
                seat
                for seat in floor_plan.seats
                if seat.row_number in usable_rows
                and not seat.is_blocked
                and (not p.requires_accessible_seat or seat.is_accessible)
            )
            singles.append(SingleUnit(participant=p, eligible_seats=eligible_seats))
    return singles, emperors
