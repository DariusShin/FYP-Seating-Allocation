"""Soft-constraint behaviour: weight monotonicity and cost formulas."""

from __future__ import annotations

from dataclasses import replace

import pytest

from seat_solver.cost_calculator import activity_target_rank, desired_priority_rank
from seat_solver.solver import solve_seat_allocation

from conftest import make_participant


@pytest.fixture(scope="module")
def solve(participants, floor_plan, previous_allocation):
    def _solve(config, with_previous=True):
        result = solve_seat_allocation(
            participants,
            floor_plan,
            config,
            previous_allocation if with_previous else None,
        )
        assert result["status"] == "success", result.get("error")
        return result

    return _solve


def test_zero_soft_weights_keep_hard_constraints(solve, config):
    zeroed = replace(
        config,
        priority_seat_weight=0,
        category_zone_weight=0,
        movement_weight=0,
        activeness_weight=0,
    )
    result = solve(zeroed)
    assert result["hard_constraint_validation"]["all_constraints_satisfied"] is True
    assert result["solver"]["main_penalty"] == 0
    assert (
        result["penalty_summary"]["weighted"]["total"]
        == (result["penalty_summary"]["weighted"]["tie_break"])
    )


def test_higher_movement_weight_reduces_or_preserves_movement(
    solve, config, default_result
):
    heavier = solve(replace(config, movement_weight=60))
    assert (
        heavier["penalty_summary"]["unweighted"]["movement"]
        <= default_result["penalty_summary"]["unweighted"]["movement"]
    )


def test_higher_priority_weight_improves_or_preserves_priority_mismatch(
    solve, config, default_result
):
    heavier = solve(replace(config, priority_seat_weight=80))
    assert (
        heavier["penalty_summary"]["unweighted"]["priority_seat"]
        <= default_result["penalty_summary"]["unweighted"]["priority_seat"]
    )


def test_movement_penalty_zero_without_previous_allocation(solve, config):
    result = solve(config, with_previous=False)
    assert result["penalty_summary"]["unweighted"]["movement"] == 0
    assert result["penalty_summary"]["weighted"]["movement"] == 0
    for assignment in result["assignments"]:
        assert assignment["penalty"]["unweighted"]["movement"] == 0
        assert assignment["previous_seat_ids"] == []
        assert assignment["moved"] is None


def test_desired_priority_rank_precedence(config):
    general = make_participant("P901", "MERIT", 500)
    monk = make_participant("P902", "MERIT", 500, is_monk=True, category="MONASTIC")
    elderly = make_participant("P903", "MERIT", 500, age=70)
    accessible_elderly = make_participant(
        "P904", "MERIT", 500, age=70, requires_accessible_seat=True
    )
    assert desired_priority_rank(general, config) == 10
    assert desired_priority_rank(monk, config) == 1
    assert desired_priority_rank(elderly, config) == 3
    # Several rules apply: the highest priority (lowest rank) wins.
    assert desired_priority_rank(accessible_elderly, config) == 1


def test_activity_target_rank_bounds():
    assert activity_target_rank(20, 0, 20) == 1  # most active -> best rank
    assert activity_target_rank(0, 0, 20) == 16  # least active -> worst rank
    assert activity_target_rank(10, 0, 20) == 9  # 1 + round(7.5) rounds half up
    assert activity_target_rank(5, 5, 5) == 1  # degenerate span
    assert activity_target_rank(0, 0, 20, max_rank=12) == 12  # scale follows plan


def test_per_assignment_weighted_breakdown_consistent(default_result):
    weights = default_result["weights"]
    weight_map = {
        "priority_seat": weights["priority_seat_weight"],
        "category_zone": weights["category_zone_weight"],
        "movement": weights["movement_weight"],
        "activeness": weights["activeness_weight"],
    }
    constraint_config = default_result["constraint_config"]
    scale = constraint_config["normalization_scale"]
    maxima = constraint_config["component_maxima"]
    for assignment in default_result["assignments"]:
        penalty = assignment["penalty"]
        total = 0
        for key, weight in weight_map.items():
            raw = penalty["unweighted"][key]
            if constraint_config["normalize_penalties"]:
                max_raw = max(1, maxima[key])
                expected_norm = (2 * scale * raw + max_raw) // (2 * max_raw)
            else:
                expected_norm = raw
            assert penalty["normalized"][key] == expected_norm
            assert penalty["weighted"][key] == weight * penalty["normalized"][key]
            total += penalty["weighted"][key]
        assert penalty["weighted"]["total"] == total


def test_penalty_scaler_normalizes_to_0_100_round_half_up():
    from seat_solver.cost_calculator import PenaltyScaler

    scaler = PenaltyScaler(normalize=True, maxima={"movement": 139})
    assert scaler.normalized("movement", 0) == 0
    assert scaler.normalized("movement", 139) == 100
    assert scaler.normalized("movement", 70) == 50  # 50.36 rounds down
    assert scaler.normalized("movement", 71) == 51  # 51.08 rounds down to 51
    passthrough = PenaltyScaler(normalize=False, maxima={"movement": 139})
    assert passthrough.normalized("movement", 70) == 70


def test_component_maxima_for_default_scenario(floor_plan, config):
    from seat_solver.cost_calculator import compute_component_maxima

    assert compute_component_maxima(floor_plan, config) == {
        "priority_seat": 15,  # worst rank 16 vs best desired rank 1
        "category_zone": 16,  # an Emperor pair can sum two worst-zone seats
        "movement": 215,  # 20 fixed + 12*15 rows + 1*15 columns
        "activeness": 15,  # target rank 1..16 vs seat rank 1..16
    }


def test_normalization_makes_weights_comparable(default_result):
    """Every normalized component total must fit the same 0..100-per-assignment
    scale: no component's normalized total may exceed assignments * 100."""
    normalized = default_result["penalty_summary"]["normalized"]
    count = len(default_result["assignments"])
    scale = default_result["constraint_config"]["normalization_scale"]
    for value in normalized.values():
        assert 0 <= value <= count * scale
