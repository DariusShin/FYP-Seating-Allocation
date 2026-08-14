"""Deterministic synthetic participant generator.

Generates exactly 122 primary participant records (86 Emperor, 12 Bodhi,
24 Merit) plus a consistent previous-allocation file. All randomness is
driven by a single seeded ``random.Random`` instance, so identical seeds
produce byte-identical output.

The mix mirrors the real PJKIT registrations, where Emperor pair units are
the large majority: 86 pairs (172 seats) plus 36 single seats demand 208 of
the hall's 232 assignable seats. Roughly half of the Emperor participants
provide an adjacent guest name; the rest leave it null so both pair seats
display the primary participant's name.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import replace
from pathlib import Path

from seat_solver.floor_plan_generator import generate_floor_plan
from seat_solver.models import (
    CATEGORY_IMPORTANCE,
    SCHEMA_VERSION,
    FloorPlan,
    Participant,
    write_json,
)
from seat_solver.preprocessing import SeatPair, compute_tier_bands

DEFAULT_SEED = 20260707
DEFAULT_COUNT = 122

EMPEROR_COUNT = 86
BODHI_COUNT = 12
MERIT_COUNT = 24

EMPEROR_CONTRIBUTION_CHOICES = [2000, 2200, 2600, 3000, 3800, 5000, 6800, 8888]
BODHI_CONTRIBUTION_CHOICES = [1000, 1200, 1300, 1500, 1600, 1800, 1900]
MERIT_CONTRIBUTION_CHOICES = [500, 550, 600, 650, 700, 750, 800, 850, 900, 950]

MONK_COUNT = 4
ELDERLY_COUNT = 30
ACCESSIBLE_COUNT = 8
PREVIOUS_ALLOCATION_RATIO = 0.7

SURNAMES = [
    "Tan",
    "Lim",
    "Lee",
    "Wong",
    "Ng",
    "Chan",
    "Cheah",
    "Goh",
    "Ong",
    "Teoh",
    "Yap",
    "Khoo",
    "Chong",
    "Loh",
    "Foo",
    "Sim",
    "Chin",
    "Lau",
    "Ho",
    "Gan",
]
GIVEN_NAMES = [
    "Wei Ming",
    "Mei Ling",
    "Kok Seng",
    "Siew Lan",
    "Chee Keong",
    "Li Hua",
    "Ah Kow",
    "Bee Choo",
    "Hock Seng",
    "Swee Lin",
    "Kah Wai",
    "Yoke Fong",
    "Boon Huat",
    "Poh Choo",
    "Teck Meng",
    "Sook Yee",
    "Chun Hong",
    "Lai Fun",
    "Keat Seng",
    "Guat Eng",
    "Meng Chye",
    "Siok Ching",
    "Yew Weng",
    "Pei San",
]
MONK_NAMES = [
    "Venerable Jing Hai",
    "Venerable Hui Neng",
    "Venerable Bao Sheng",
    "Venerable De Cheng",
    "Venerable Fa Xian",
    "Venerable Guang Ming",
    "Venerable Ru Shan",
    "Venerable Wu Jing",
    "Venerable Zhi Yuan",
    "Venerable Chan Kong",
]


def _unique_names(rng: random.Random, count: int) -> list[str]:
    """Deterministically build unique synthetic Malaysian-style names."""
    names: list[str] = []
    seen: set[str] = set()
    while len(names) < count:
        candidate = f"{rng.choice(SURNAMES)} {rng.choice(GIVEN_NAMES)}"
        if candidate in seen:
            continue
        seen.add(candidate)
        names.append(candidate)
    return names


def generate_participants(
    count: int = DEFAULT_COUNT, seed: int = DEFAULT_SEED
) -> list[Participant]:
    """Generate the deterministic 122-record dataset.

    The tier split is fixed at 86 Emperor, 12 Bodhi, and 24 Merit so the seat
    demand is exactly 86*2 + 12 + 24 = 208 of the 232 assignable seats.
    """
    if count != DEFAULT_COUNT:
        raise ValueError(
            "the prototype dataset is fixed at exactly 122 primary participants"
        )
    rng = random.Random(seed)

    tiers = (
        ["EMPEROR"] * EMPEROR_COUNT + ["BODHI"] * BODHI_COUNT + ["MERIT"] * MERIT_COUNT
    )
    contributions = (
        [rng.choice(EMPEROR_CONTRIBUTION_CHOICES) for _ in range(EMPEROR_COUNT)]
        + [rng.choice(BODHI_CONTRIBUTION_CHOICES) for _ in range(BODHI_COUNT)]
        + [rng.choice(MERIT_CONTRIBUTION_CHOICES) for _ in range(MERIT_COUNT)]
    )

    # One pool covers primary names plus guest names for half the Emperors.
    guest_count = (EMPEROR_COUNT + 1) // 2
    name_pool = _unique_names(rng, count + guest_count)
    lay_names = name_pool[:count]
    guest_names = name_pool[count:]

    # Monks live among the Bodhi and Merit tiers in this synthetic dataset.
    monk_candidates = list(range(EMPEROR_COUNT, count))
    monk_indices = set(rng.sample(monk_candidates, MONK_COUNT))

    elderly_pool = [i for i in range(count)]
    elderly_indices = set(rng.sample(elderly_pool, ELDERLY_COUNT))

    accessible_pool = (
        rng.sample(range(0, EMPEROR_COUNT), 2)
        + rng.sample(range(EMPEROR_COUNT, EMPEROR_COUNT + BODHI_COUNT), 2)
        + rng.sample(range(EMPEROR_COUNT + BODHI_COUNT, count), 4)
    )
    accessible_indices = set(accessible_pool)
    assert len(accessible_indices) == ACCESSIBLE_COUNT

    events = [rng.randint(0, 22) for _ in range(count)]
    # Guarantee the required activity spread: at least one 0 and one >= 20.
    events[rng.randrange(count)] = 0
    events[rng.randrange(count)] = max(20, max(events))

    participants: list[Participant] = []
    monk_name_iter = iter(MONK_NAMES)
    guest_iter = iter(guest_names)
    for index in range(count):
        tier = tiers[index]
        is_monk = index in monk_indices
        if is_monk:
            category = "MONASTIC"
            full_name = next(monk_name_iter)
        else:
            category = rng.choices(
                ["COMMITTEE", "VOLUNTEER", "GENERAL_DEVOTEE"],
                weights=[15, 25, 60],
                k=1,
            )[0]
            full_name = lay_names[index]

        is_elderly = index in elderly_indices
        age = rng.randint(60, 85) if is_elderly else rng.randint(25, 59)

        adjacent_person_name: str | None = None
        if tier == "EMPEROR" and index % 2 == 0:
            # Even-indexed Emperors bring a named adjacent guest; the others
            # leave it null so both seats display the primary name — mirroring
            # the merged-cell vs two-name pairs of the real PJKIT layouts.
            adjacent_person_name = next(guest_iter)

        participants.append(
            Participant(
                participant_id=f"P{index + 1:03d}",
                full_name=full_name,
                is_synthetic=True,
                contribution_amount_rm=contributions[index],
                contribution_tier=tier,
                age=age,
                is_elderly=is_elderly,
                is_monk=is_monk,
                requires_accessible_seat=index in accessible_indices,
                participant_category=category,
                category_importance=CATEGORY_IMPORTANCE[category],
                events_joined_last_2_years=events[index],
                adjacent_person_name=adjacent_person_name,
                previous_seat_ids=(),
            )
        )
    return participants


def _pairs_for_previous(floor_plan: FloorPlan) -> list[SeatPair]:
    """Odd-even non-blocked pairs ordered centre-out (best seat rank first).

    The pair desirability order falls out of the seat priority pattern: the
    pair holding the better-ranked seat is the better pair, which reproduces
    the centre-out, east-first pair priorities without needing the config.
    """
    pairs: list[SeatPair] = []
    for row_number in range(1, floor_plan.row_count + 1):
        row_seats = {
            s.physical_position: s for s in floor_plan.seats_in_row(row_number)
        }
        for first in range(1, floor_plan.seats_per_row, 2):
            seat_a, seat_b = row_seats.get(first), row_seats.get(first + 1)
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
                    second_position=first + 1,
                    pair_priority=min(seat_a.priority_rank, seat_b.priority_rank),
                    seats=(seat_a, seat_b),
                )
            )
    return pairs


def build_previous_allocation(
    participants: list[Participant],
    floor_plan: FloorPlan,
    rng: random.Random,
    keep_ratio: float = PREVIOUS_ALLOCATION_RATIO,
) -> dict[str, tuple[str, ...]]:
    """Build a hard-constraint-consistent previous allocation, then keep a
    deterministic ~70% subset of participants with previous seats.

    The demand-derived tier bands are computed exactly as the engine computes
    them; seats are then filled in contribution order (descending) inside
    each band, row by row and by priority rank within a row, so the previous
    layout also satisfies band ordering, tier-exclusive rows, and the
    contribution-ordering hard constraint. A same-row repair pass then swaps
    accessible-requiring participants onto accessible seats (or accessible
    pairs), which keeps contribution ordering intact because ordering only
    depends on the row. No physical seat is used twice.
    """
    valid_pairs = _pairs_for_previous(floor_plan)
    bands = compute_tier_bands(participants, floor_plan, valid_pairs)
    if not hasattr(bands, "rows"):  # pragma: no cover - default data always fits
        raise ValueError("default scenario does not fit the floor plan")

    allocation: dict[str, tuple[str, ...]] = {}

    emperors = [p for p in participants if p.contribution_tier == "EMPEROR"]
    emperors.sort(key=lambda p: (-p.contribution_amount_rm, p.participant_id))
    emperor_rows = list(bands.rows["EMPEROR"])
    pair_slots = [
        pair
        for row in emperor_rows
        for pair in sorted(
            (p for p in valid_pairs if p.row_number == row),
            key=lambda p: p.pair_priority,
        )
    ]
    emperor_holder: dict[int, Participant] = {}
    for participant, pair in zip(emperors, pair_slots):
        emperor_holder[pair.pair_index] = participant
    pair_by_index = {pair.pair_index: pair for pair in pair_slots}

    for index in sorted(emperor_holder):
        participant = emperor_holder[index]
        pair = pair_by_index[index]
        if participant.requires_accessible_seat and not pair.is_accessible:
            swap_index = next(
                other
                for other in sorted(emperor_holder)
                if pair_by_index[other].row_number == pair.row_number
                and pair_by_index[other].is_accessible
                and not emperor_holder[other].requires_accessible_seat
            )
            emperor_holder[index], emperor_holder[swap_index] = (
                emperor_holder[swap_index],
                participant,
            )
    for index, participant in emperor_holder.items():
        allocation[participant.participant_id] = pair_by_index[index].seat_ids

    for tier in ("BODHI", "MERIT"):
        members = [p for p in participants if p.contribution_tier == tier]
        members.sort(key=lambda p: (-p.contribution_amount_rm, p.participant_id))
        seats = [
            seat
            for row in bands.rows[tier]
            for seat in sorted(
                (s for s in floor_plan.seats_in_row(row) if not s.is_blocked),
                key=lambda s: s.priority_rank,
            )
        ]
        holder = {
            seat.seat_id: participant for participant, seat in zip(members, seats)
        }
        seat_by_id = {seat.seat_id: seat for seat in seats}
        for seat_id in sorted(holder):
            participant = holder[seat_id]
            seat = seat_by_id[seat_id]
            if participant.requires_accessible_seat and not seat.is_accessible:
                swap_id = next(
                    other_id
                    for other_id in sorted(holder)
                    if seat_by_id[other_id].row_number == seat.row_number
                    and seat_by_id[other_id].is_accessible
                    and not holder[other_id].requires_accessible_seat
                )
                holder[seat_id], holder[swap_id] = holder[swap_id], participant
        for seat_id, participant in holder.items():
            allocation[participant.participant_id] = (seat_id,)

    keep_count = round(len(participants) * keep_ratio)
    keep_ids = set(rng.sample(sorted(allocation.keys()), keep_count))
    return {pid: seats for pid, seats in allocation.items() if pid in keep_ids}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--output", type=Path, default=Path("data/mock_participants.json")
    )
    parser.add_argument(
        "--previous-output",
        type=Path,
        default=Path("data/previous_allocation.json"),
    )
    args = parser.parse_args(argv)

    participants = generate_participants(count=args.count, seed=args.seed)
    floor_plan = generate_floor_plan()
    rng = random.Random(args.seed + 1)
    previous = build_previous_allocation(participants, floor_plan, rng)

    participants = [
        replace(
            participant, previous_seat_ids=previous.get(participant.participant_id, ())
        )
        for participant in participants
    ]

    write_json(
        args.output,
        {
            "schema_version": SCHEMA_VERSION,
            "seed": args.seed,
            "participants": [p.to_dict() for p in participants],
        },
    )
    write_json(
        args.previous_output,
        {
            "schema_version": SCHEMA_VERSION,
            "allocations": [
                {"participant_id": pid, "seat_ids": list(seats)}
                for pid, seats in sorted(previous.items())
            ],
        },
    )
    print(
        f"wrote {len(participants)} participants to {args.output} and "
        f"{len(previous)} previous allocations to {args.previous_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
