"""Hard-constraint verification against the default OPTIMAL solution."""

from __future__ import annotations

import copy

from seat_solver.validator import count_middle_fill_violations

VALID_PAIR_POSITIONS = {
    (1, 2),
    (3, 4),
    (5, 6),
    (7, 8),
    (9, 10),
    (11, 12),
    (13, 14),
    (15, 16),
}


def _seat_lookup(result):
    return {
        seat["seat_id"]: {**seat, "row_number": row["row_number"]}
        for row in result["floor_plan"]["rows"]
        for seat in row["seats"]
    }


def test_every_emperor_has_two_approved_adjacent_seats(default_result):
    seats = _seat_lookup(default_result)
    emperors = [
        a for a in default_result["assignments"] if a["contribution_tier"] == "EMPEROR"
    ]
    assert len(emperors) == 86
    for assignment in emperors:
        assert assignment["allocation_type"] == "EMPEROR_PAIR"
        assert len(assignment["seat_ids"]) == 2
        first, second = sorted(
            (seats[s] for s in assignment["seat_ids"]),
            key=lambda s: s["physical_position"],
        )
        assert first["row_number"] == second["row_number"]
        positions = (first["physical_position"], second["physical_position"])
        assert positions in VALID_PAIR_POSITIONS


def test_no_emperor_pair_crosses_the_aisle(default_result):
    seats = _seat_lookup(default_result)
    aisle = default_result["floor_plan"]["aisle_after_position"]
    for assignment in default_result["assignments"]:
        if assignment["allocation_type"] != "EMPEROR_PAIR":
            continue
        positions = sorted(
            seats[s]["physical_position"] for s in assignment["seat_ids"]
        )
        assert positions != [aisle, aisle + 1]


def test_no_seat_is_duplicated(default_result):
    used = [s for a in default_result["assignments"] for s in a["seat_ids"]]
    assert len(used) == len(set(used)) == 208
    assert len(default_result["empty_seat_ids"]) == 24


def test_tier_band_constraints(default_result):
    """Tier bands are demand-derived: Emperor rows 1-13, Bodhi row 14,
    Merit rows 15-16 for the 86/12/24 default; rows are tier-exclusive and
    ordered Emperor before Bodhi before Merit."""
    bands = default_result["tier_bands"]
    assert bands["EMPEROR"] == list(range(1, 14))
    assert bands["BODHI"] == [14]
    assert bands["MERIT"] == [15, 16]
    seats = _seat_lookup(default_result)
    for assignment in default_result["assignments"]:
        allowed = set(bands[assignment["contribution_tier"]])
        for seat_id in assignment["seat_ids"]:
            assert seats[seat_id]["row_number"] in allowed


def test_rows_are_tier_exclusive(default_result):
    seats = _seat_lookup(default_result)
    tiers_by_row: dict[int, set[str]] = {}
    for assignment in default_result["assignments"]:
        for seat_id in assignment["seat_ids"]:
            tiers_by_row.setdefault(seats[seat_id]["row_number"], set()).add(
                assignment["contribution_tier"]
            )
    for row_number, tiers in tiers_by_row.items():
        assert len(tiers) == 1, f"row {row_number} mixes tiers {tiers}"


def test_contribution_ordering_inside_each_tier(default_result):
    seats = _seat_lookup(default_result)
    by_tier: dict[str, list[tuple[int, int]]] = {}
    for assignment in default_result["assignments"]:
        row = max(seats[s]["row_number"] for s in assignment["seat_ids"])
        by_tier.setdefault(assignment["contribution_tier"], []).append(
            (assignment["contribution_amount_rm"], row)
        )
    for members in by_tier.values():
        for contribution_i, row_i in members:
            for contribution_j, row_j in members:
                if contribution_i > contribution_j:
                    assert row_i <= row_j


def test_accessibility_satisfied(default_result):
    seats = _seat_lookup(default_result)
    checked = 0
    for assignment in default_result["assignments"]:
        if not assignment["requires_accessible_seat"]:
            continue
        checked += 1
        flags = [seats[s]["is_accessible"] for s in assignment["seat_ids"]]
        if assignment["allocation_type"] == "SINGLE":
            assert all(flags)
        else:
            assert any(flags)
    assert checked >= 5


def test_no_blocked_seat_used(default_result):
    seats = _seat_lookup(default_result)
    for assignment in default_result["assignments"]:
        for seat_id in assignment["seat_ids"]:
            assert not seats[seat_id]["is_blocked"]


def test_front_fill_rows_within_each_band(default_result):
    """HC13: empty seats may only sit in the last occupied row of a band.

    With 86 Emperor pairs, 12 Bodhi, and 24 Merit the exact per-row occupancy
    is forced: rows 1-5 full pairs (8 each), the blocked-centre rows 6-9 hold
    4/6/4/6 pairs, rows 10-12 full (8 each), row 13 holds the last 2 pairs,
    row 14 holds the 12 Bodhi, row 15 is full of Merit, and row 16 holds the
    last 8 Merit.
    """
    seats = _seat_lookup(default_result)
    empty_rows = {
        seats[seat_id]["row_number"] for seat_id in default_result["empty_seat_ids"]
    }
    assert empty_rows == {13, 14, 16}
    expected_occupancy = {
        1: 16,
        2: 16,
        3: 16,
        4: 16,
        5: 16,
        6: 8,
        7: 12,
        8: 8,
        9: 12,
        10: 16,
        11: 16,
        12: 16,
        13: 4,
        14: 12,
        15: 16,
        16: 8,
    }
    for row in default_result["floor_plan"]["rows"]:
        occupied = sum(
            1 for seat in row["seats"] if seat["occupancy_status"] == "OCCUPIED"
        )
        assert occupied == expected_occupancy[row["row_number"]]
    block = default_result["hard_constraint_validation"]
    assert block["front_fill_violation_count"] == 0


def test_middle_fill_outward_from_aisle(default_result):
    """HC14: on each side of each row the occupied seats form one contiguous
    block starting at the centre aisle, so no gap can appear between the
    aisle and the outermost occupied seat."""
    aisle = default_result["floor_plan"]["aisle_after_position"]
    for row in default_result["floor_plan"]["rows"]:
        available = [
            seat for seat in row["seats"] if seat["occupancy_status"] != "BLOCKED"
        ]
        left_outward = sorted(
            (seat for seat in available if seat["physical_position"] <= aisle),
            key=lambda seat: seat["physical_position"],
            reverse=True,
        )
        right_outward = sorted(
            (seat for seat in available if seat["physical_position"] > aisle),
            key=lambda seat: seat["physical_position"],
        )
        for side in (left_outward, right_outward):
            statuses = [seat["occupancy_status"] for seat in side]
            if "EMPTY" in statuses:
                first_empty = statuses.index("EMPTY")
                assert all(status == "EMPTY" for status in statuses[first_empty:])
    block = default_result["hard_constraint_validation"]
    assert block["middle_fill_violation_count"] == 0


def test_middle_fill_counter_detects_a_gap(default_result):
    """The independent HC14 audit flags an occupied seat separated from the
    aisle by an empty seat."""
    tampered = copy.deepcopy(default_result)
    aisle = tampered["floor_plan"]["aisle_after_position"]
    row = next(r for r in tampered["floor_plan"]["rows"] if r["row_number"] == 2)
    for seat in row["seats"]:
        if seat["physical_position"] <= aisle:
            seat["occupancy_status"] = (
                "OCCUPIED" if seat["physical_position"] == 1 else "EMPTY"
            )
    assert count_middle_fill_violations(tampered) == 1


def test_embedded_hard_constraint_block_reports_clean(default_result):
    block = default_result["hard_constraint_validation"]
    assert block["all_constraints_satisfied"] is True
    assert all(
        value == 0 for key, value in block.items() if key != "all_constraints_satisfied"
    )
