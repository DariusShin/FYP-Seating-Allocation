"""Regeneration behaviour: determinism and previous-seat preservation."""

from __future__ import annotations

from dataclasses import replace

from seat_solver.solver import solve_seat_allocation


def _seat_map(result):
    return {
        assignment["participant_id"]: sorted(assignment["seat_ids"])
        for assignment in result["assignments"]
    }


def test_identical_input_produces_identical_layout(
    participants, floor_plan, config, previous_allocation, default_result
):
    repeat = solve_seat_allocation(
        participants, floor_plan, config, previous_allocation
    )
    assert repeat["status"] == "success"
    assert _seat_map(repeat) == _seat_map(default_result)
    assert (
        repeat["solver"]["objective_value"]
        == default_result["solver"]["objective_value"]
    )


def test_regeneration_preserves_previous_seats_where_possible(
    participants, floor_plan, config, previous_allocation
):
    """With movement dominating the objective, every participant that has a
    (hard-constraint-consistent) previous seat must keep it."""
    movement_dominant = replace(
        config,
        priority_seat_weight=0,
        category_zone_weight=0,
        movement_weight=100,
        activeness_weight=0,
    )
    result = solve_seat_allocation(
        participants, floor_plan, movement_dominant, previous_allocation
    )
    assert result["status"] == "success"
    assert result["penalty_summary"]["unweighted"]["movement"] == 0
    for assignment in result["assignments"]:
        if assignment["previous_seat_ids"]:
            assert sorted(assignment["previous_seat_ids"]) == sorted(
                assignment["seat_ids"]
            )
            assert assignment["moved"] is False


def test_moved_flags_are_consistent(default_result):
    """`moved` must reflect the previous seats exactly: None without a
    previous assignment, otherwise the set comparison of previous vs
    assigned seat ids."""
    holders = [a for a in default_result["assignments"] if a["previous_seat_ids"]]
    assert len(holders) == 85
    for assignment in default_result["assignments"]:
        if not assignment["previous_seat_ids"]:
            assert assignment["moved"] is None
        else:
            assert assignment["moved"] == (
                set(assignment["previous_seat_ids"]) != set(assignment["seat_ids"])
            )


def test_higher_movement_weight_keeps_more_previous_holders(
    participants, floor_plan, config, previous_allocation, default_result
):
    """Raising the movement weight must not decrease the number of
    previous-seat holders who keep their seats."""
    stickier = replace(config, movement_weight=80)
    result = solve_seat_allocation(
        participants, floor_plan, stickier, previous_allocation
    )
    assert result["status"] == "success"

    def kept(res):
        return sum(1 for a in res["assignments"] if a["moved"] is False)

    assert kept(result) >= kept(default_result)
