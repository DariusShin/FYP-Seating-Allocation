"""Tests for the floor plan generator and priority pattern."""

from __future__ import annotations

from seat_solver.floor_plan_generator import DEFAULT_BLOCKED_PATTERN

EXPECTED_PRIORITY_PATTERN = [16, 14, 12, 10, 8, 6, 4, 2, 1, 3, 5, 7, 9, 11, 13, 15]


def test_floor_plan_dimensions(floor_plan):
    assert floor_plan.row_count == 16
    assert floor_plan.seats_per_row == 16
    assert floor_plan.total_seats == 256
    assert len({seat.seat_id for seat in floor_plan.seats}) == 256


def test_priority_pattern_in_every_row(floor_plan):
    for row_number in range(1, 17):
        seats = floor_plan.seats_in_row(row_number)
        pattern = [seat.priority_rank for seat in seats]
        assert pattern == EXPECTED_PRIORITY_PATTERN


def test_centre_aisle_after_position_8(floor_plan):
    assert floor_plan.aisle_after_position == 8
    for seat in floor_plan.seats:
        expected_side = "LEFT" if seat.physical_position <= 8 else "RIGHT"
        assert seat.side == expected_side


def test_seat_ids_follow_row_and_position(floor_plan):
    for seat in floor_plan.seats:
        assert seat.seat_id == f"R{seat.row_number:02d}-S{seat.physical_position:02d}"
        assert seat.row_index == seat.row_number - 1


def test_zones_split_each_side(floor_plan):
    zone_by_position = {
        1: "LEFT_OUTER",
        2: "LEFT_OUTER",
        3: "LEFT_OUTER",
        4: "LEFT_OUTER",
        5: "LEFT_CENTER",
        6: "LEFT_CENTER",
        7: "LEFT_CENTER",
        8: "LEFT_CENTER",
        9: "RIGHT_CENTER",
        10: "RIGHT_CENTER",
        11: "RIGHT_CENTER",
        12: "RIGHT_CENTER",
        13: "RIGHT_OUTER",
        14: "RIGHT_OUTER",
        15: "RIGHT_OUTER",
        16: "RIGHT_OUTER",
    }
    for seat in floor_plan.seats:
        assert seat.zone == zone_by_position[seat.physical_position]


def test_right_side_outranks_mirrored_left(floor_plan):
    row = floor_plan.seats_in_row(1)
    by_position = {seat.physical_position: seat for seat in row}
    for left, right in (
        (8, 9),
        (7, 10),
        (6, 11),
        (5, 12),
        (4, 13),
        (3, 14),
        (2, 15),
        (1, 16),
    ):
        assert by_position[right].priority_rank < by_position[left].priority_rank


def test_structural_blocked_pattern(floor_plan):
    """Rows 6/8 block positions 5-12; rows 7/9 block 5-6 and 11-12 (24 seats)."""
    blocked = {
        (seat.row_number, seat.physical_position)
        for seat in floor_plan.seats
        if seat.is_blocked
    }
    expected = {
        (row, position)
        for row, positions in DEFAULT_BLOCKED_PATTERN.items()
        for position in positions
    }
    assert blocked == expected
    assert len(blocked) == 24


def test_accessible_flags(floor_plan):
    accessible = [seat for seat in floor_plan.seats if seat.is_accessible]
    assert all(seat.physical_position in (1, 8, 9, 16) for seat in accessible)
    assert len(accessible) == 64
