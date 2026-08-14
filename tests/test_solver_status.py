"""Solver status handling and structured error documents."""

from __future__ import annotations

from seat_solver.solver import solve_seat_allocation

from conftest import make_participant


def test_default_scenario_is_optimal(default_result):
    stats = default_result["solver"]
    assert stats["status"] == "OPTIMAL"
    assert stats["optimality_gap"] == 0
    assert stats["objective_value"] == stats["best_objective_bound"]
    assert stats["engine"] == "Google OR-Tools CP-SAT"


def test_objective_reconstruction(default_result):
    stats = default_result["solver"]
    weighted = default_result["penalty_summary"]["weighted"]
    main = (
        weighted["priority_seat"]
        + weighted["category_zone"]
        + weighted["movement"]
        + weighted["activeness"]
    )
    assert stats["main_penalty"] == main
    assert stats["tie_break_penalty"] == weighted["tie_break"]
    assert (
        stats["objective_value"]
        == stats["main_objective_scale"] * main + weighted["tie_break"]
    )


def test_impossible_accessible_emperor_demand_returns_structured_error(
    floor_plan, config
):
    # 86 accessible-requiring Emperor units exceed the accessible pair supply
    # inside the derived Emperor band (4 accessible pairs per full row).
    participants = [
        make_participant(
            f"P{i:03d}", "EMPEROR", 2000 + i, requires_accessible_seat=True
        )
        for i in range(1, 87)
    ]
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TIER_CAPACITY_EXCEEDED"
    assert result["error"]["details"]


def test_band_overflow_returns_structured_error(floor_plan, config):
    # 86 Emperor pairs fill rows 1-13 and 12 Bodhi take row 14, so 33 Merit
    # exceed the 32 seats left in rows 15-16: the bands no longer fit.
    participants = (
        [make_participant(f"P{i:03d}", "EMPEROR", 2000 + i) for i in range(1, 87)]
        + [make_participant(f"P{i:03d}", "BODHI", 1500) for i in range(87, 99)]
        + [make_participant(f"P{i:03d}", "MERIT", 500) for i in range(99, 132)]
    )
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TIER_CAPACITY_EXCEEDED"


def test_total_capacity_exceeded_returns_structured_error(floor_plan, config):
    # 117 Emperor units demand 234 seats > 232 assignable, tripping HC11 first.
    participants = [
        make_participant(f"P{i:03d}", "EMPEROR", 2000 + i) for i in range(1, 118)
    ]
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["status"] == "error"
    assert result["error"]["code"] == "CAPACITY_EXCEEDED"


def test_invalid_input_returns_structured_error(floor_plan, config):
    # Contribution amount contradicts the declared tier.
    participants = [make_participant("P001", "EMPEROR", 800)]
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
    assert result["error"]["details"]["problems"]


def test_error_document_is_frontend_friendly(floor_plan, config):
    participants = [
        make_participant(f"P{i:03d}", "EMPEROR", 2000 + i) for i in range(1, 118)
    ]
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["schema_version"]
    assert result["run_id"]
    assert result["case_study"] == "PJ Kwan Inn Teng"
    assert set(result["error"]) == {"code", "message", "solver_status", "details"}
    assert set(result["solver"]) >= {
        "wall_time_seconds",
        "objective_value",
        "best_objective_bound",
    }
