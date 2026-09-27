import copy

import pytest
from test_production import tiny

from seat_solver.production.plan_store import PlanStore, participant_view
from seat_solver.production.policy import DomainError
from seat_solver.production.production import solve
from seat_solver.production.production_validator import audit_result
from seat_solver.production.workspace import WorkspaceStore, initial_state


@pytest.fixture
def setup(tmp_path):
    store = PlanStore(tmp_path / "plans.db")
    plan = store.save(solve(tiny(2, "EMPEROR")), "generator")
    return store, WorkspaceStore(store), plan


def action(ws, plan, command, revision=0, **kwargs):
    return ws.action(
        plan["event_id"],
        "staff",
        dict(
            command=command,
            revision=revision,
            plan_version_id=plan["plan_version_id"],
            **kwargs,
        ),
    )


def test_display_names_publish_and_snapshot_isolation(setup):
    store, ws, plan = setup
    state = initial_state(plan)
    pid = next(iter(state["items"]))
    original = state["participants"][0]["full_name"]
    state["items"][pid]["display_names"] = ["陳思恩", "林慧婷"]
    saved = action(ws, plan, "workspace_save", state=state)
    published = action(
        ws,
        plan,
        "workspace_publish",
        saved["revision"],
    )
    result = published["base"]
    assert audit_result(result)["passed"]
    assert result["source_request"]["participants"][0]["full_name"] == original
    assert [s["display_name"] for s in result["assignments"][0]["seats"]] == [
        "陳思恩",
        "陳思恩",
    ]
    assert (
        participant_view(result, pid)["assignment"]["seats"][0]["display_name"]
        == "陳思恩"
    )
    state["items"][pid]["note"] = "new private note"
    action(ws, result, "workspace_save", published["revision"], state=state)
    assert store.published(plan["event_id"])["operations"][pid]["note"] == ""
    with pytest.raises(DomainError, match="newer draft"):
        action(ws, plan, "workspace_publish", saved["revision"], acknowledgements=[])


def test_unlinked_partner_releases_seat_and_publishes(setup):
    _store, ws, plan = setup
    state = initial_state(plan)
    # Choose outermost allocation on either side, release its outer seat, retain inner.
    lookup = {s["seat_id"]: s for s in plan["source_request"]["layout"]["seats"]}
    pid, item = max(
        state["items"].items(),
        key=lambda kv: max(lookup[s]["priority_rank"] for s in kv[1]["seat_ids"]),
    )
    ordered = sorted(item["seat_ids"], key=lambda s: lookup[s]["priority_rank"])
    released = ordered[-1]
    item.update(
        companion_absent=True,
        absence_reason="Partner confirmed absent; no replacement",
        seat_ids=ordered[:1],
    )
    saved = action(ws, plan, "workspace_save", state=state)
    published = action(
        ws,
        plan,
        "workspace_publish",
        saved["revision"],
    )["base"]
    a = next(a for a in published["assignments"] if a["participant_id"] == pid)
    assert a["contribution_tier"] == "EMPEROR" and a["allocation_type"] == "SINGLE"
    assert released in published["empty_seat_ids"]
    assert audit_result(published)["passed"]
    assert published["input_summary"]["required_seat_count"] == 3


def test_absence_reason_required_and_registration_name_protected(setup):
    _, ws, plan = setup
    state = initial_state(plan)
    pid = next(iter(state["items"]))
    state["items"][pid]["companion_absent"] = True
    with pytest.raises(DomainError, match="reason"):
        action(ws, plan, "workspace_save", state=state)
    state = initial_state(plan)
    state["participants"][0]["full_name"] = "overwrite"
    with pytest.raises(DomainError, match="read-only"):
        action(ws, plan, "workspace_save", state=state)


def test_released_partner_seat_can_be_assigned_to_replacement(tmp_path):
    store = PlanStore(tmp_path / "release.db")
    ws = WorkspaceStore(store)
    request = tiny(1, "EMPEROR")
    single = copy.deepcopy(request["participants"][0])
    single.update(
        participant_id="WAIT",
        full_name="林慧婷",
        contribution_tier="MERIT",
        contribution_amount_rm=3000,
        registration_status="WAITLISTED",
    )
    request["participants"].append(single)
    plan = store.save(solve(request), "staff")
    state = initial_state(plan)
    pair = state["items"]["P0001"]
    released = pair["seat_ids"][1]
    pair.update(
        companion_absent=True,
        absence_reason="Confirmed absent",
        seat_ids=pair["seat_ids"][:1],
    )
    # A new individually registered attendee can occupy the released physical seat.
    state["participants"][1]["registration_status"] = "CONFIRMED"
    state["items"]["WAIT"]["seat_ids"] = [released]
    saved = action(ws, plan, "workspace_save", state=state)
    result = action(
        ws,
        plan,
        "workspace_publish",
        saved["revision"],
    )["base"]
    assert len(result["assignments"]) == 2
    assert result["input_summary"]["required_seat_count"] == 2
    assert audit_result(result)["passed"]


def test_initial_pair_order_identifies_contributor_before_partner(setup):
    _, _, plan = setup
    state = initial_state(plan)
    for p in plan["source_request"]["participants"]:
        m = state["items"][p["participant_id"]]
        assert m["display_names"][0] == p["full_name"]
        assert m["display_names"][1] == p["full_name"]


def test_legacy_partner_override_is_removed_on_save_reload_and_publication(setup):
    from seat_solver.production.service import dispatch

    store, ws, plan = setup
    state = initial_state(plan)
    pid = next(iter(state["items"]))
    assert "partner_name_edited" not in state["items"][pid]
    state["items"][pid].update(
        partner_name_edited=True, display_names=["陳思恩", "林慧婷"]
    )
    saved = action(ws, plan, "workspace_save", state=state)
    assert ws.load(plan["event_id"])["state"]["items"][pid]["display_names"] == ["陳思恩", "陳思恩"]
    published = action(
        ws,
        plan,
        "workspace_publish",
        saved["revision"],
    )["base"]
    assert "partner_name_edited" not in published["operations"][pid]
    venue = dispatch({"command": "venue", "event_id": plan["event_id"]}, store)
    assert venue["pair_display"][pid] == {"primary_name": "陳思恩"}
    assert audit_result(published)["passed"]


def test_synthetic_name_refresh_preserves_staff_edits(tmp_path):
    from seat_solver.production.production_data import refresh_synthetic_display_names

    store = PlanStore(tmp_path / "synthetic.db")
    ws = WorkspaceStore(store)
    req = tiny(2, "EMPEROR")
    for i, p in enumerate(req["participants"]):
        p["full_name"] = f"Synthetic participant {i + 1}"
    plan = store.save(solve(req), "local-development")
    state = initial_state(plan)
    state["items"]["P0001"]["display_names"] = ["員工已校對", "員工已校對"]
    state["items"]["P0001"]["partner_name_edited"] = True
    state["items"]["P0001"]["note"] = "Keep this note"
    action(ws, plan, "workspace_save", state=state)
    assert refresh_synthetic_display_names(store) == 2
    loaded = ws.load(plan["event_id"])["state"]
    assert loaded["items"]["P0001"]["display_names"][1] == "員工已校對"
    assert loaded["items"]["P0001"]["note"] == "Keep this note"
    assert all(
        "Synthetic" not in n
        for m in loaded["items"].values()
        for n in m["display_names"]
    )
    assert refresh_synthetic_display_names(store) == 0


@pytest.mark.parametrize(
    "names",
    [
        ["陳思恩", " \t陳\u3000思\n恩 "],
        ["Lee Shin", "Lee\u00a0Shin"],
        ["Darius Lee", "\ufeffDarius\u200bLee"],
    ],
)
def test_matching_display_names_remerge_published_pair(setup, names):
    from seat_solver.production.service import dispatch

    store, ws, plan = setup
    state = initial_state(plan)
    pid = next(iter(state["items"]))
    state["items"][pid].update(display_names=names, partner_name_edited=True)
    saved = action(ws, plan, "workspace_save", state=state)
    action(
        ws,
        plan,
        "workspace_publish",
        saved["revision"],
    )
    venue = dispatch({"command": "venue", "event_id": plan["event_id"]}, store)
    assert venue["pair_display"][pid]["primary_name"] == names[0]
    # Legacy partner overrides normalize to the payer name.
    restored = ws.load(plan["event_id"])["state"]["items"][pid]
    assert restored["display_names"] == [names[0], names[0]]
    assert "partner_name_edited" not in restored


def test_dock_save_refresh_and_stale_write(setup):
    store, ws, plan = setup
    state = initial_state(plan)
    pid = next(iter(state["items"]))
    state["items"][pid]["seat_ids"] = []
    saved = action(ws, plan, "workspace_save", state=state)
    assert ws.load(plan["event_id"])["state"] == state
    with pytest.raises(DomainError, match="newer draft"):
        action(ws, plan, "workspace_save", state=state)
    with pytest.raises(DomainError, match="Assign every attending"):
        action(ws, plan, "workspace_publish", saved["revision"])
    assert store.published(plan["event_id"]) is None


def test_locked_moves_and_overlapping_assignments_fail(setup):
    _, ws, plan = setup
    state = initial_state(plan)
    pid, other = state["items"]
    state["items"][pid]["locked"] = True
    saved = action(ws, plan, "workspace_save", state=state)
    moved = copy.deepcopy(state)
    moved["items"][pid]["seat_ids"] = []
    with pytest.raises(DomainError, match="Unlock"):
        action(ws, plan, "workspace_save", saved["revision"], state=moved)
    moved = copy.deepcopy(state)
    moved["items"][other]["seat_ids"] = moved["items"][pid]["seat_ids"]
    with pytest.raises(DomainError, match="overlap"):
        action(ws, plan, "workspace_save", saved["revision"], state=moved)


def test_publication_without_review_creates_workspace_and_rejects_stale_writes(setup):
    store, ws, plan = setup
    result = action(ws, plan, "workspace_publish")
    assert result["base"]["publication_status"] == "PUBLISHED"
    assert (
        ws.load(plan["event_id"])["base"]["plan_version_id"]
        == result["base"]["plan_version_id"]
    )
    assert result["revision"] == 1
    assert "review_acknowledgements" not in result["base"]
    assert result["base"]["hard_constraint_validation"] == {"checked": False}
    assert result["base"]["approved_by"] is None
    with store.connection() as db:
        actions = [
            r[0]
            for r in db.execute(
                "SELECT action FROM audit WHERE plan=?",
                (result["base"]["plan_version_id"],),
            )
        ]
    assert actions == ["PUBLISHED"]
    with pytest.raises(DomainError, match="newer draft"):
        action(ws, plan, "workspace_save", state=initial_state(plan))


def test_retired_review_command_is_rejected(setup):
    _, ws, plan = setup
    with pytest.raises(DomainError, match="Unknown workspace operation"):
        action(ws, plan, "workspace_check")


def test_publication_does_not_run_contribution_or_packing_review(tmp_path):
    from seat_solver.production.production_validator import validate_placements

    store = PlanStore(tmp_path / "plans.db")
    ws = WorkspaceStore(store)
    from seat_solver.production.production_data import generate

    request = generate(emperor=0, merit=2, bodhi=0)
    request["layout"]["row_count"] = 2
    request["layout"]["seats"] = [
        s for s in request["layout"]["seats"] if s["row_number"] <= 2
    ]
    request["solver"].update(max_time_seconds=5, num_search_workers=1)
    request["participants"][0]["contribution_amount_rm"] = 5000
    request["participants"][1]["contribution_amount_rm"] = 3000
    plan = store.save(solve(request), "staff")
    state = initial_state(plan)
    state["items"]["P0001"]["seat_ids"] = ["R02-S01"]
    state["items"]["P0002"]["seat_ids"] = ["R01-S01"]
    saved = action(ws, plan, "workspace_save", state=state)
    result = action(ws, plan, "workspace_publish", saved["revision"])["base"]
    assert result["publication_status"] == "PUBLISHED"
    # The engine's validator is retained; staff publication no longer calls it.
    rules = {
        f["rule_id"]
        for f in validate_placements(result["source_request"], result["assignments"])[
            "issues"
        ]
    }
    assert "C13" in rules and "C15" in rules
    assert (
        store.published(plan["event_id"])["plan_version_id"]
        == result["plan_version_id"]
    )


def test_legacy_workspace_schema_still_saves_and_publishes(setup):
    store, ws, plan = setup
    with store.connection() as db:
        db.execute("ALTER TABLE workspaces ADD COLUMN checked_revision INTEGER")
    state = initial_state(plan)
    saved = action(ws, plan, "workspace_save", state=state)
    with store.connection() as db:
        db.execute("UPDATE workspaces SET checked_revision=999")
    result = action(ws, plan, "workspace_publish", saved["revision"])
    assert result["base"]["publication_status"] == "PUBLISHED"


def test_unsaved_payload_cannot_override_saved_publication(setup):
    _, ws, plan = setup
    state = initial_state(plan)
    saved = action(ws, plan, "workspace_save", state=state)
    changed = copy.deepcopy(state)
    changed["items"]["P0001"]["display_names"] = ["不應公布", "不應公布"]
    result = action(ws, plan, "workspace_publish", saved["revision"], state=changed)
    assert result["state"] == state
    assert result["base"]["operations"] == state["items"]


def test_changed_public_pointer_rejects_workspace_publication(setup):
    store, ws, plan = setup
    saved = action(ws, plan, "workspace_save", state=initial_state(plan))
    other = store.save(solve(tiny(2, "EMPEROR")), "another staff member")
    for command in ("submit", "approve", "publish"):
        other = store.transition(
            other["plan_version_id"],
            command,
            "another staff member",
            other["validation_revision"],
        )
    with pytest.raises(DomainError, match="published plan changed"):
        action(ws, plan, "workspace_publish", saved["revision"])
    assert (
        store.published(plan["event_id"])["plan_version_id"] == other["plan_version_id"]
    )
