"""Deterministic floor plan generator.

Generates the PJKIT 16-row by 16-seat hall (256 seats) with one centre aisle
between physical positions 8 and 9 and the mirrored priority-rank pattern
``[16, 14, 12, 10, 8, 6, 4, 2, 1, 3, 5, 7, 9, 11, 13, 15]`` (rank 1 is the
best seat, immediately right of the aisle).

The hall carries a structural blocked block in the centre of rows 6-9,
observed identically in the real 2023 and 2024 PJKIT layouts:

- rows 6 and 8: positions 5-12 blocked (8 seats each)
- rows 7 and 9: positions 5-6 and 11-12 blocked (4 seats each)

Seats carry no tier attribute: tier bands are derived from demand at solve
time, not fixed properties of the venue.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from seat_solver.models import SCHEMA_VERSION, FloorPlan, Seat, write_json

DEFAULT_ROWS = 16
DEFAULT_SEATS_PER_ROW = 16
DEFAULT_ACCESSIBLE_POSITIONS = (1, 8, 9, 16)

# Structural blocked pattern of the PJKIT hall (rows 6-9 centre block).
DEFAULT_BLOCKED_PATTERN: dict[int, tuple[int, ...]] = {
    6: tuple(range(5, 13)),
    7: (5, 6, 11, 12),
    8: tuple(range(5, 13)),
    9: (5, 6, 11, 12),
}


def default_blocked_seat_ids(
    rows: int = DEFAULT_ROWS, seats_per_row: int = DEFAULT_SEATS_PER_ROW
) -> tuple[str, ...]:
    """The PJKIT structural blocked seats; empty for non-default hall sizes."""
    if (rows, seats_per_row) != (DEFAULT_ROWS, DEFAULT_SEATS_PER_ROW):
        return ()
    return tuple(
        f"R{row:02d}-S{position:02d}"
        for row, positions in sorted(DEFAULT_BLOCKED_PATTERN.items())
        for position in positions
    )


def priority_rank_for_position(position: int, aisle_after: int) -> int:
    """Mirrored priority pattern around the centre aisle.

    Right of the aisle the ranks are the odd numbers 1, 3, 5, ... moving
    outward; left of the aisle they are the even numbers 2, 4, 6, ... moving
    outward, so the right seat always outranks its mirrored left seat.
    """
    if position > aisle_after:
        return 2 * (position - aisle_after - 1) + 1
    return 2 * (aisle_after - position) + 2


def zone_for_position(position: int, aisle_after: int, seats_per_row: int) -> str:
    if position <= aisle_after:
        outer_width = (aisle_after + 1) // 2
        return "LEFT_OUTER" if position <= outer_width else "LEFT_CENTER"
    right_width = seats_per_row - aisle_after
    center_width = (right_width + 1) // 2
    return "RIGHT_CENTER" if position <= aisle_after + center_width else "RIGHT_OUTER"


def generate_floor_plan(
    rows: int = DEFAULT_ROWS,
    seats_per_row: int = DEFAULT_SEATS_PER_ROW,
    accessible_positions: tuple[int, ...] = DEFAULT_ACCESSIBLE_POSITIONS,
    blocked_seat_ids: tuple[str, ...] | None = None,
) -> FloorPlan:
    if seats_per_row % 2 != 0:
        raise ValueError("seats_per_row must be even so the aisle splits the row")
    if blocked_seat_ids is None:
        blocked_seat_ids = default_blocked_seat_ids(rows, seats_per_row)
    aisle_after = seats_per_row // 2
    seats: list[Seat] = []
    for row_number in range(1, rows + 1):
        for position in range(1, seats_per_row + 1):
            seat_id = f"R{row_number:02d}-S{position:02d}"
            seats.append(
                Seat(
                    seat_id=seat_id,
                    row_number=row_number,
                    row_index=row_number - 1,
                    physical_position=position,
                    priority_rank=priority_rank_for_position(position, aisle_after),
                    side="LEFT" if position <= aisle_after else "RIGHT",
                    zone=zone_for_position(position, aisle_after, seats_per_row),
                    is_accessible=position in accessible_positions,
                    is_blocked=seat_id in blocked_seat_ids,
                )
            )
    return FloorPlan(
        row_count=rows,
        seats_per_row=seats_per_row,
        aisle_after_position=aisle_after,
        seats=tuple(seats),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--seats-per-row", type=int, default=DEFAULT_SEATS_PER_ROW)
    parser.add_argument("--output", type=Path, default=Path("data/floor_plan.json"))
    args = parser.parse_args(argv)

    plan = generate_floor_plan(rows=args.rows, seats_per_row=args.seats_per_row)
    payload = plan.to_dict()
    payload["schema_version"] = SCHEMA_VERSION
    write_json(args.output, payload)
    blocked = sum(1 for seat in plan.seats if seat.is_blocked)
    print(f"wrote {plan.total_seats} seats ({blocked} blocked) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
