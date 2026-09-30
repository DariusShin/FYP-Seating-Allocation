"""Paid entitlements cannot be released by attendance metadata or replacement APIs."""
import copy

import pytest
from test_production import tiny
from test_workspace import setup, action

from seat_solver.production.policy import DomainError
from seat_solver.production.production import solve
from seat_solver.production.production_validator import audit_result
from seat_solver.production.workspace import initial_state
from seat_solver.production.service import dispatch


@pytest.mark.parametrize("status", ["ABSENT", "REPLACED", "REPLACEMENT_CONFIRMED"])
def test_retired_statuses_are_rejected(status):
    request = tiny()
    request["participants"][0]["registration_status"] = status
    assert solve(request)["error"]["code"] == "INVALID_INPUT"


@pytest.mark.parametrize("field,value", [("replacement_for_participant_id", "P0002"), ("attendance_confirmed", False)])
def test_attendance_and_replacement_links_are_not_request_fields(field, value):
    request = tiny()
    request["participants"][0][field] = value
    assert solve(request)["error"]["code"] == "INVALID_INPUT"


@pytest.mark.parametrize("mode", ["REPAIR_PUBLISHED", "FULL_REGENERATION"])
def test_retired_generation_modes_are_rejected(mode):
    request = tiny()
    request["generation_mode"] = mode
    assert solve(request)["error"]["code"] == "INVALID_INPUT"


def test_solver_result_has_no_repair_state():
    result = solve(tiny(2, "EMPEROR"))
    assert audit_result(result)["passed"]
    assert "baseline_snapshot" not in result
    assert "movement" not in result["quality"]
    assert "repair_scope" not in result["solver"]
    assert all(len(a["seat_ids"]) == 2 for a in result["assignments"])


@pytest.mark.parametrize("field,value", [("name_checked", True), ("attendance_confirmed", False), ("seat_reviewed", True), ("locked", True), ("companion_absent", True), ("absence_reason", "Not attending")])
def test_retired_workspace_flags_cannot_be_saved(setup, field, value):
    _, ws, plan = setup
    state = initial_state(plan)
    state["items"]["P0001"][field] = value
    with pytest.raises(DomainError, match="Unsupported"):
        action(ws, plan, "workspace_save", state=state)


def test_pair_cannot_be_reduced_to_single_or_published_from_dock(setup):
    store, ws, plan = setup
    state = initial_state(plan)
    state["items"]["P0001"]["seat_ids"].pop()
    with pytest.raises(DomainError, match="paid seat count"):
        action(ws, plan, "workspace_save", state=state)
    state["items"]["P0001"]["seat_ids"] = []
    saved = action(ws, plan, "workspace_save", state=state)
    with pytest.raises(DomainError, match="every paid"):
        action(ws, plan, "workspace_publish", saved["revision"])
    assert store.published(plan["event_id"]) is None


@pytest.mark.parametrize("change", ["delete", "add", "status", "name"])
def test_working_draft_cannot_change_registration_entitlement(setup, change):
    _, ws, plan = setup
    state = initial_state(plan)
    if change == "delete":
        state["participants"].pop()
    elif change == "add":
        new = copy.deepcopy(state["participants"][0])
        new["participant_id"] = "NEW"
        state["participants"].append(new)
    elif change == "status":
        state["participants"][0]["registration_status"] = "CANCELLED"
    else:
        state["participants"][0]["full_name"] = "Someone else"
    with pytest.raises(DomainError, match="read-only"):
        action(ws, plan, "workspace_save", state=state)


def test_manual_swap_and_details_preserve_all_paid_names_until_explicit_publication(setup):
    store, ws, plan = setup
    published = action(ws, plan, "workspace_publish")
    state = copy.deepcopy(published["state"])
    a, b = state["items"].values()
    a["seat_ids"], b["seat_ids"] = b["seat_ids"], a["seat_ids"]
    a["note"] = "Contributor will not attend; retain both paid seats"
    saved = action(ws, published["base"], "workspace_save", published["revision"], state=state)
    assert store.published(plan["event_id"])["operations"] == published["state"]["items"]
    result = action(ws, published["base"], "workspace_publish", saved["revision"])["base"]
    assert len(result["assignments"]) == 2
    assert sum(len(a["seat_ids"]) for a in result["assignments"]) == 4
    assert {a["full_name"] for a in result["assignments"]} == {p["full_name"] for p in state["participants"]}


def test_overlap_cannot_be_saved(setup):
    _, ws, plan = setup
    state = initial_state(plan)
    state["items"]["P0002"]["seat_ids"] = state["items"]["P0001"]["seat_ids"]
    with pytest.raises(DomainError, match="overlap"):
        action(ws, plan, "workspace_save", state=state)


def test_old_store_is_rejected_instead_of_migrated():
    old = solve(tiny())
    old["policy_version_id"] = "pjkit-v3"
    class OldStore:
        def latest(self, event):
            return old
    with pytest.raises(DomainError, match="fresh paid-seats-v4"):
        dispatch({"command": "solve", "generation_mode": "REGENERATE_DRAFT"}, OldStore())


def test_regeneration_retains_registration_names_and_published_snapshot(setup):
    store, ws, plan = setup
    published = action(ws, plan, "workspace_publish")["base"]
    preferences = list(reversed(plan["preferences"]))
    result = dispatch({"command": "solve", "event_id": plan["event_id"], "generation_mode": "REGENERATE_DRAFT", "preferences": preferences}, store)
    assert result["status"] == "success"
    assert result["source_request"]["participants"] == plan["source_request"]["participants"]
    assert store.published(plan["event_id"])["plan_version_id"] == published["plan_version_id"]
    assert result["publication_status"] == "DRAFT"
