"""v2 requirement tests, independent tiny oracle, lifecycle and adversarial audits."""

import copy
import itertools
import json
from dataclasses import replace
from pathlib import Path

import pytest
from ortools.sat.python import cp_model

from seat_solver.production.plan_store import PlanStore, participant_view
from seat_solver.production.policy import (
    DEFAULT_PREFERENCES,
    DomainError,
    mapped_weights,
    policy,
    validate_request,
)
from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.production_validator import (
    audit_result,
    validate_placements,
)
from seat_solver.production.service import dispatch


def tiny(n=3, tier="MERIT"):
    counts = {"emperor": 0, "merit": 0, "bodhi": 0}
    counts[tier.lower()] = n
    r = generate(**counts)
    r["layout"]["row_count"] = 1
    r["layout"]["seats"] = [s for s in r["layout"]["seats"] if s["row_number"] == 1]
    r["layout_version_id"] = r["layout"]["layout_version_id"] = "test-one-row-v1"
    r["solver"].update(max_time_seconds=5, num_search_workers=1, canonicalize=True)
    return r


def profiles():
    keys = ["contribution_seat", "activeness", "category_zone"]
    for n in range(4):
        for enabled in itertools.permutations(keys, n):
            yield [{"key": k, "enabled": True} for k in enabled] + [
                {"key": k, "enabled": False} for k in keys if k not in enabled
            ]


def test_layout_current_and_historical():
    r = generate()
    l = r["layout"]
    blocked = {
        (s["row_number"], s["physical_position"]) for s in l["seats"] if s["is_blocked"]
    }
    assert blocked == (
        {(row, pos) for row in (6, 8) for pos in range(5, 13)}
        | {(row, pos) for row in (7, 9) for pos in (5, 6, 11, 12)}
    )
    old = json.loads(Path("data/historical/report-232.json").read_text())
    assert sum(not s["is_blocked"] for s in old["seats"]) == 232
    assert sum(not s["is_blocked"] for s in l["seats"]) == 232


@pytest.mark.parametrize("prefs", list(profiles()))
def test_all_16_profiles(prefs):
    r = tiny()
    r["preferences"] = prefs
    out = solve(r)
    assert out["status"] == "success", out
    assert audit_result(out)["passed"]
    enabled = [p for p in prefs if p["enabled"]]
    weights = mapped_weights(prefs)
    assert [weights[p["key"]] for p in enabled] == [40, 30, 20][: len(enabled)]
    assert all(
        out["quality"]["weighted"][p["key"]] == 0 for p in prefs if not p["enabled"]
    )


def test_profile_reenable_and_bad_inputs():
    prefs = [
        {"key": "contribution_seat", "enabled": True},
        {"key": "category_zone", "enabled": False},
        {"key": "activeness", "enabled": True},
    ]
    assert mapped_weights(prefs) == {
        "contribution_seat": 40,
        "category_zone": 0,
        "activeness": 30,
    }
    prefs[1]["enabled"] = True
    assert mapped_weights(prefs)["category_zone"] == 30
    for malformed in (
        [prefs[0]] * 3,
        [dict(prefs[0], enabled="false")] + prefs[1:],
        prefs[:-1],
    ):
        with pytest.raises(DomainError):
            mapped_weights(malformed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("age", -1),
        ("requires_accessible_seat", "false"),
        ("registration_status", "MAYBE"),
        ("contribution_amount_rm", 3000.2),
    ],
)
def test_reject_before_coercion(field, value):
    r = tiny()
    r["participants"][0][field] = value
    out = solve(r)
    assert out["error"]["code"] == "INVALID_INPUT"


def test_explicit_tier_no_upper_bound():
    r = tiny(1, "BODHI")
    r["participants"][0]["contribution_amount_rm"] = 10000
    assert solve(r)["status"] == "success"


def test_shared_all_three_tiers_and_precedence():
    r = tiny(1, "EMPEROR")
    more = tiny(2)["participants"]
    more[0]["participant_id"] = "M"
    more[1]["participant_id"] = "B"
    more[1]["contribution_tier"] = "BODHI"
    r["participants"] += more
    o = solve(r)
    assert o["status"] == "success", o
    assert o["floor_plan"]["rows"][0]["tier_bands"] == ["EMPEROR", "MERIT", "BODHI"]
    assert audit_result(o)["passed"]


def test_initial_accessibility_conflict_is_not_silently_relaxed():
    r = tiny(1)
    r["participants"][0]["requires_accessible_seat"] = True
    assert solve(r)["error"]["code"] == "INFEASIBLE"


def test_accessible_full_row():
    r = tiny(16)
    r["participants"][0]["requires_accessible_seat"] = True
    o = solve(r)
    a = next(a for a in o["assignments"] if a["requires_accessible_seat"])
    assert a["seats"][0]["physical_position"] in (1, 2, 15, 16)


def test_empty_event_and_exclusion():
    r = tiny(1)
    r["participants"][0]["registration_status"] = "PENDING"
    o = solve(r)
    assert o["status"] == "success" and o["input_summary"]["required_seat_count"] == 0
    assert len(o["excluded_participants"]) == 1 and audit_result(o)["passed"]


def test_tampering_participant_seat_cost_and_map():
    o = solve(tiny())
    for mutate in (
        lambda x: x["assignments"][1].update(
            participant_id=x["assignments"][0]["participant_id"]
        ),
        lambda x: x["assignments"][1].update(seat_ids=x["assignments"][0]["seat_ids"]),
        lambda x: x["quality"]["weighted"].update(total=0),
        lambda x: x["floor_plan"]["rows"][0]["seats"][0].update(
            occupancy_status="OCCUPIED"
        ),
    ):
        t = copy.deepcopy(o)
        mutate(t)
        assert not audit_result(t)["passed"]


def test_validator_rejects_gap_and_tier_inversion():
    r = tiny(2)
    a = [
        {"participant_id": p["participant_id"], "seat_ids": [f"R01-S{pos:02d}"]}
        for p, pos in zip(r["participants"], [1, 9])
    ]
    assert not validate_placements(r, a)["passed"]


def test_canonical_input_order_invariant():
    r = tiny()
    a = solve(r)
    r["participants"].reverse()
    r["layout"]["seats"].reverse()
    b = solve(r)
    assert (
        a["solver"]["canonicalization_complete"]
        and b["solver"]["canonicalization_complete"]
    )
    assert [(p["participant_id"], p["seat_ids"]) for p in a["assignments"]] == [
        (p["participant_id"], p["seat_ids"]) for p in b["assignments"]
    ]


def test_oracle_two_singles():
    # Enumerate without solver-domain or scoring helpers. East-first packing
    # permits only {9,10}. Both assignments are compared.
    r = tiny(2)
    r["preferences"] = [
        {"key": "contribution_seat", "enabled": True},
        {"key": "activeness", "enabled": False},
        {"key": "category_zone", "enabled": False},
    ]
    r["participants"][0]["contribution_amount_rm"] = 3000
    r["participants"][1]["contribution_amount_rm"] = 4000
    o = solve(r)
    lookup = {s["physical_position"]: s for s in r["layout"]["seats"]}
    best = None
    for positions in ((9, 10),):
        for arrangement in itertools.permutations(positions):
            total = 0
            for coefficient, pos in zip((1, 100), arrangement):
                raw = coefficient * 2 * (lookup[pos]["priority_rank"] - 1)
                total += 40 * ((200 * raw + 3000) // 6000)
            best = total if best is None else min(best, total)
    assert o["quality"]["weighted"]["total"] == best


def published(store, r):
    p = store.save(solve(r), "tester")
    for action in ("submit", "approve", "publish"):
        p = store.transition(
            p["plan_version_id"], action, "tester", p["validation_revision"]
        )
    return p


def test_lifecycle_and_public_privacy(tmp_path):
    store = PlanStore(tmp_path / "plans.db")
    r = tiny()
    p = store.save(solve(r), "tester")
    assert store.published(r["event_id"]) is None
    with pytest.raises(DomainError):
        store.transition(
            p["plan_version_id"], "publish", "tester", p["validation_revision"]
        )
    for action in ("submit", "approve", "publish"):
        p = store.transition(
            p["plan_version_id"], action, "tester", p["validation_revision"]
        )
    guest = participant_view(p, p["assignments"][0]["participant_id"])
    assert "source_request" not in guest and "quality" not in guest
    assert all(
        s["participant_id"] in (None, guest["assignment"]["participant_id"])
        for row in guest["floor_plan"]["rows"]
        for s in row["seats"]
    )
    assert store.published(r["event_id"])["plan_version_id"] == p["plan_version_id"]


def test_stale_publication(tmp_path):
    st = PlanStore(tmp_path / "plans.db")
    r = tiny()
    a = st.save(solve(r), "a")
    b = st.save(solve(r), "b")
    for p in (a, b):
        for action in ("submit", "approve"):
            st.transition(
                p["plan_version_id"], action, "actor", p["validation_revision"]
            )
    st.transition(a["plan_version_id"], "publish", "a", a["validation_revision"])
    with pytest.raises(DomainError, match="Another plan"):
        st.transition(b["plan_version_id"], "publish", "b", b["validation_revision"])
    assert st.published(r["event_id"])["plan_version_id"] == a["plan_version_id"]


def test_manual_validation_rescore_provenance(tmp_path):
    st = PlanStore(tmp_path / "plans.db")
    p = st.save(solve(tiny()), "actor")
    assignments = [
        {"participant_id": a["participant_id"], "seat_ids": a["seat_ids"]}
        for a in p["assignments"]
    ]
    assignments[0]["seat_ids"], assignments[1]["seat_ids"] = (
        assignments[1]["seat_ids"],
        assignments[0]["seat_ids"],
    )
    edited = st.edit(
        p["plan_version_id"], assignments, "actor", p["validation_revision"]
    )
    assert (
        edited["manually_modified"]
        and edited["solver"]["status"] == "MANUALLY_MODIFIED"
    )
    assert (
        edited["solver_status_at_generation"] == "OPTIMAL"
        and audit_result(edited)["passed"]
    )
    assert edited["plan_version_id"] != p["plan_version_id"]






def test_feasible_incumbent_preserved(monkeypatch):
    # Run a real solve, exposing it as an unfinished proof to test status handling.
    real = cp_model.CpSolver.Solve

    def feasible(self, model, *args, **kwargs):
        status = real(self, model, *args, **kwargs)
        return cp_model.FEASIBLE if status == cp_model.OPTIMAL else status

    monkeypatch.setattr(cp_model.CpSolver, "Solve", feasible)
    r = tiny()
    o = solve(r)
    assert o["status"] == "success" and o["solver"]["status"] == "FEASIBLE"
    assert not o["solver"]["canonicalization_complete"] and audit_result(o)["passed"]
    r["solver"]["require_optimal"] = True
    assert solve(r)["error"]["code"] == "OPTIMAL_NOT_PROVEN"


def test_capacity_and_coordinates():
    r = tiny(17)
    assert solve(r)["error"]["code"] == "CAPACITY_EXCEEDED"
    r = tiny()
    r["layout"]["seats"][0]["physical_position"] = 99
    assert solve(r)["error"]["code"] == "INVALID_INPUT"


def test_manual_edit_invalidates_approval_atomically(tmp_path):
    store = PlanStore(tmp_path / "plans.sqlite3")
    plan = store.save(solve(tiny()), "admin")
    for action in ("submit", "approve"):
        plan = store.transition(
            plan["plan_version_id"], action, "admin", plan["validation_revision"]
        )
    edited = store.edit(
        plan["plan_version_id"],
        plan["assignments"],
        "editor",
        plan["validation_revision"],
    )
    assert edited["publication_status"] == "DRAFT"
    old = store.get(plan["plan_version_id"])
    assert old["publication_status"] == "SUPERSEDED" and old["approved_by"] is None
    with pytest.raises(DomainError):
        store.transition(
            plan["plan_version_id"], "publish", "admin", plan["validation_revision"]
        )
    assert store.published(plan["event_id"]) is None










def test_public_view_event_details_and_own_seat_names():
    request = tiny(1, "EMPEROR")
    request["participants"][0]["adjacent_person_name"] = "同行者姓名"
    plan = solve(request)
    plan["plan_version_id"] = "public-preview"
    view = participant_view(plan, request["participants"][0]["participant_id"])
    assert view["event_details"] == request["event_details"]
    assert view["assignment"]["full_name"] == request["participants"][0]["full_name"]
    assert all(
        s["display_name"] is None
        for row in view["floor_plan"]["rows"]
        for s in row["seats"]
    )
    assert {s["seat_id"]: s["display_name"] for s in view["assignment"]["seats"]} == {
        s["seat_id"]: s["display_name"] for s in plan["assignments"][0]["seats"]
    }
    assert "同行者姓名" in {s["display_name"] for s in view["assignment"]["seats"]}
    assert participant_view(plan, "OTHER")["assignment"] is None
    assert len(view["assignment"]["seat_ids"]) == 2
    assert all(
        set(s) == {"seat_id", "row_number", "physical_position", "display_name"}
        for s in view["assignment"]["seats"]
    )


def test_regeneration_uses_current_obstacles_and_priorities_for_existing_hall(monkeypatch):
    from seat_solver.production import service

    current = generate()
    old = copy.deepcopy(current)
    old["layout_version_id"] = old["layout"]["layout_version_id"] = "pjkit-2026-v1"
    for seat in old["layout"]["seats"]:
        pos = seat["physical_position"]
        seat["priority_rank"] = 2 * (pos - 9) + 1 if pos > 8 else 2 * (8 - pos) + 2
        if seat["row_number"] in (7, 9):
            seat["is_blocked"] = False

    class ExistingStore:
        def latest(self, event):
            return {
                "source_request": old,
                "policy_version_id": old["policy_version_id"],
            }

    captured = {}

    def capture(request):
        captured.update(request)
        return {"status": "captured"}

    monkeypatch.setattr(service, "solve", capture)
    dispatch({"command": "solve", "generation_mode": "INITIAL"}, ExistingStore())
    assert captured["layout_version_id"] == "pjkit-2026-v3"
    assert sum(s["is_blocked"] for s in captured["layout"]["seats"]) == 24
    assert captured["layout"] == current["layout"]
    assert captured["participants"] == old["participants"]


def test_current_layout_files_agree_and_new_blocks_have_no_pair_options():
    from seat_solver.production.production_scoring import options

    request = generate()
    for name in ("data/floor_plan.json", "data/layouts/production_2026.json"):
        assert json.loads(Path(name).read_text()) == request["layout"]
    blocked = {s["seat_id"] for s in request["layout"]["seats"] if s["is_blocked"]}
    # Both pair and single-seat solver options must exclude every obstacle.
    for tier in ("EMPEROR", "MERIT", "BODHI"):
        participant = {"contribution_tier": tier, "requires_accessible_seat": False}
        assert all(
            seat["seat_id"] not in blocked
            for option in options(request, participant)
            for seat in option
        )
    for row in (7, 9):
        for position in (5, 6, 11, 12):
            assert f"R{row:02d}-S{position:02d}" in blocked
