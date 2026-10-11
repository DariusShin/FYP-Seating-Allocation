"""Historical v1 prototype fixtures; production tests build their own v4 requests.

BASE is this baseline directory; REPO is the repository root, which still holds
the shared historical data and config fixtures read below.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
for path_entry in (str(BASE.parent), str(REPO)):
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

from legacy_cp_sat.models import (
    CATEGORY_IMPORTANCE,
    Participant,
    load_floor_plan,
    load_participants,
    load_previous_allocation,
    load_solver_config,
    read_json,
)
from legacy_cp_sat.solver import solve_seat_allocation


@pytest.fixture(scope="session")
def root() -> Path:
    return REPO


@pytest.fixture(scope="session")
def participants():
    return load_participants(REPO / "data" / "mock_participants.json")


@pytest.fixture(scope="session")
def participants_payload():
    return read_json(REPO / "data" / "mock_participants.json")


@pytest.fixture(scope="session")
def floor_plan():
    return load_floor_plan(REPO / "data" / "historical" / "report-232.json")


@pytest.fixture(scope="session")
def floor_plan_payload():
    return read_json(REPO / "data" / "historical" / "report-232.json")


@pytest.fixture(scope="session")
def config():
    return load_solver_config(REPO / "config" / "historical" / "solver_config.v1.json")


@pytest.fixture(scope="session")
def config_payload():
    return read_json(REPO / "config" / "historical" / "solver_config.v1.json")


@pytest.fixture(scope="session")
def previous_allocation():
    return load_previous_allocation(REPO / "data" / "previous_allocation.json")


@pytest.fixture(scope="session")
def default_result(participants, floor_plan, config, previous_allocation):
    """One cached historical prototype solve, not production v4 acceptance."""
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
