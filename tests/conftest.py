"""Shared fixtures: loaded default dataset plus a cached default solve."""

from __future__ import annotations

from pathlib import Path

import pytest

from seat_solver.models import (
    CATEGORY_IMPORTANCE,
    Participant,
    load_floor_plan,
    load_participants,
    load_previous_allocation,
    load_solver_config,
    read_json,
)
from seat_solver.solver import solve_seat_allocation

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def participants():
    return load_participants(ROOT / "data" / "mock_participants.json")


@pytest.fixture(scope="session")
def participants_payload():
    return read_json(ROOT / "data" / "mock_participants.json")


@pytest.fixture(scope="session")
def floor_plan():
    return load_floor_plan(ROOT / "data" / "floor_plan.json")


@pytest.fixture(scope="session")
def floor_plan_payload():
    return read_json(ROOT / "data" / "floor_plan.json")


@pytest.fixture(scope="session")
def config():
    return load_solver_config(ROOT / "config" / "solver_config.json")


@pytest.fixture(scope="session")
def config_payload():
    return read_json(ROOT / "config" / "solver_config.json")


@pytest.fixture(scope="session")
def previous_allocation():
    return load_previous_allocation(ROOT / "data" / "previous_allocation.json")


@pytest.fixture(scope="session")
def default_result(participants, floor_plan, config, previous_allocation):
    """One shared default-scenario solve (the acceptance scenario)."""
    result = solve_seat_allocation(
        participants, floor_plan, config, previous_allocation
    )
    assert result["status"] == "success", result.get("error")
    return result


def make_participant(
    participant_id: str,
    tier: str,
    contribution: int,
    *,
    category: str = "GENERAL_DEVOTEE",
    age: int = 40,
    is_monk: bool = False,
    requires_accessible_seat: bool = False,
    events: int = 5,
    adjacent_person_name: str | None = None,
    previous_seat_ids: tuple[str, ...] = (),
) -> Participant:
    """Small synthetic-participant factory for constraint and error tests."""
    return Participant(
        participant_id=participant_id,
        full_name=f"Synthetic {participant_id}",
        is_synthetic=True,
        contribution_amount_rm=contribution,
        contribution_tier=tier,
        age=age,
        is_elderly=age >= 60,
        is_monk=is_monk,
        requires_accessible_seat=requires_accessible_seat,
        participant_category=category,
        category_importance=CATEGORY_IMPORTANCE[category],
        events_joined_last_2_years=events,
        adjacent_person_name=adjacent_person_name,
        previous_seat_ids=previous_seat_ids,
    )
