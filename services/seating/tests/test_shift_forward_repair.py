"""Deterministic no-overtake shift-forward absence repair."""
import copy

from test_absence_repair import absent, command, save, saved_session
from test_production import tiny

from research.fixtures.synthetic_participants import generate
from seat_solver.production.production_validator import audit_result
from seat_solver.production.service import dispatch
from seat_solver.production.workspace import initial_state

FAST_ENGINE = "Deterministic shift-forward repair"


def with_amounts(request, amounts):
    for p in request["participants"]:
        p["contribution_amount_rm"] = amounts[p["participant_id"]]
    return request


def placed(state, mapping):
    state = copy.deepcopy(state)
    for pid, ids in mapping.items():
        state["items"][pid]["seat_ids"] = ids
    return state


def restored(state, pid):
    """Attendance recovered while the registration stays docked, as the UI does."""
    state = copy.deepcopy(state)
    item = state["items"][pid]
    item.update(attendance_status="PRESENT", seat_ids=[], dock_reason="")
    return state


def rank_seats(plan):
    cells = {s["seat_id"]: s for s in plan["source_request"]["layout"]["seats"]}
    return sorted(cells.values(), key=lambda s: (s["row_number"], s["priority_rank"]))


def test_fair_tail_jump_moves_only_the_rearmost_unit(tmp_path):
    request = tiny(4)
    with_amounts(request, {f"P{i:04d}": 3000 for i in range(1, 5)})
    store, ws, plan = saved_session(tmp_path, request)
    ranks = rank_seats(plan)
    ids = [f"P{i:04d}" for i in range(1, 5)]
    seat_of = {pid: ranks[i]["seat_id"] for i, pid in enumerate(ids)}
    state = placed(initial_state(plan), {pid: [seat_of[pid]] for pid in ids})
    saved = save(ws, plan, absent(state, "P0002"))
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 1
    assert "preference_cost_before" in result["repair_summary"]
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    assert assignment["P0004"] == [seat_of["P0002"]]
    assert assignment["P0001"] == [seat_of["P0001"]]
    assert assignment["P0003"] == [seat_of["P0003"]]
    assert result["operations"]["P0002"]["attendance_status"] == "ABSENT"
    opened = ws.open(plan["event_id"], "staff", result["plan_version_id"])
    assert opened["state"]["items"]["P0004"]["seat_ids"] == [seat_of["P0002"]]


def test_no_overtake_gate_blocks_the_lowest_contributor_from_leapfrogging(tmp_path):
    request = tiny(4)
    with_amounts(request, {"P0001": 3000, "P0002": 3100, "P0003": 3000, "P0004": 3000})
    store, ws, plan = saved_session(tmp_path, request)
    ranks = rank_seats(plan)
    seat_of = {pid: ranks[i]["seat_id"] for i, pid in enumerate(
        ["P0001", "P0002", "P0003", "P0004"])}
    state = placed(initial_state(plan), {
        "P0004": [seat_of["P0004"]],
        "P0002": [seat_of["P0003"]],
        "P0003": [seat_of["P0002"]],
        "P0001": [seat_of["P0001"]],
    })
    saved = save(ws, plan, absent(state, "P0003"))
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 2
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    assert assignment["P0002"] == [seat_of["P0002"]]
    assert assignment["P0004"] == [seat_of["P0003"]]
    assert assignment["P0001"] == [seat_of["P0001"]]


def test_emperor_gap_is_filled_by_the_rearmost_pair_bundle(tmp_path):
    store, ws, plan = saved_session(tmp_path, tiny(2, "EMPEROR"))
    ranks = rank_seats(plan)
    pids = [a["participant_id"] for a in plan["assignments"]]
    state = placed(initial_state(plan), {
        pids[1]: [ranks[0]["seat_id"], ranks[1]["seat_id"]],
        pids[0]: [ranks[2]["seat_id"], ranks[3]["seat_id"]],
    })
    saved = save(ws, plan, absent(state, pids[1]))
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 1
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    assert set(assignment[pids[0]]) == {ranks[0]["seat_id"], ranks[1]["seat_id"]}
    opened = ws.open(plan["event_id"], "staff", result["plan_version_id"])
    assert opened["state"]["items"][pids[1]]["attendance_status"] == "ABSENT"


def test_pre_existing_gap_declines_to_the_cp_sat_repair(tmp_path):
    request = tiny(4)
    with_amounts(request, {f"P{i:04d}": 3000 for i in range(1, 5)})
    store, ws, plan = saved_session(tmp_path, request)
    ranks = rank_seats(plan)
    ids = [f"P{i:04d}" for i in range(1, 5)]
    seat_of = {pid: ranks[i]["seat_id"] for i, pid in enumerate(ids)}
    state = placed(initial_state(plan), {
        "P0001": [seat_of["P0001"]],
        "P0003": [seat_of["P0003"]],
        "P0004": [ranks[9]["seat_id"]],
    })
    saved = save(ws, plan, absent(state, "P0002"))
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == "Google OR-Tools CP-SAT incremental repair"


def test_mid_hall_absence_pulls_the_hall_tail_forward_when_fair(tmp_path):
    request = generate(emperor=0, merit=20, bodhi=0)
    request["layout"]["row_count"] = 2
    request["layout"]["seats"] = [s for s in request["layout"]["seats"] if s["row_number"] <= 2]
    request["layout_version_id"] = request["layout"]["layout_version_id"] = "test-two-rows-v1"
    request["solver"].update(max_time_seconds=5, num_search_workers=1, canonicalize=False)
    with_amounts(request, {f"P{i:04d}": 3000 for i in range(1, 21)})
    store, ws, plan = saved_session(tmp_path, request)
    ordered = rank_seats(plan)
    ids = [f"P{i:04d}" for i in range(1, 21)]
    state = placed(initial_state(plan), {pid: [ordered[i]["seat_id"]] for i, pid in enumerate(ids)})
    saved = save(ws, plan, absent(state, ids[2]))
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 1
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    assert assignment[ids[19]] == [ordered[2]["seat_id"]]


def test_restored_registration_returns_to_its_vacated_seat_without_search(tmp_path):
    request = tiny(4)
    with_amounts(request, {f"P{i:04d}": 3000 for i in range(1, 5)})
    store, ws, plan = saved_session(tmp_path, request)
    ranks = rank_seats(plan)
    ids = [f"P{i:04d}" for i in range(1, 5)]
    seat_of = {pid: ranks[i]["seat_id"] for i, pid in enumerate(ids)}
    state = placed(initial_state(plan), {pid: [seat_of[pid]] for pid in ids})
    state = absent(state, "P0003")
    state = absent(state, "P0004")
    state = restored(state, "P0004")
    saved = save(ws, plan, state)
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 1
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    # The earliest legal span: the restored unit re-packs behind the seated
    # units, taking the still-absent registration's released seat.
    assert assignment["P0004"] == [seat_of["P0003"]]
    assert assignment["P0001"] == [seat_of["P0001"]]
    assert assignment["P0002"] == [seat_of["P0002"]]
    opened = ws.open(plan["event_id"], "staff", result["plan_version_id"])
    assert opened["state"]["items"]["P0004"]["attendance_status"] == "PRESENT"
    assert opened["state"]["items"]["P0004"]["previous_seat_ids"] == [seat_of["P0004"]]


def test_restored_emperor_preferred_mover_fills_the_absent_pair(tmp_path):
    request = tiny(3, "EMPEROR")
    with_amounts(request, {"P0001": 5000, "P0002": 5000, "P0003": 7000})
    store, ws, plan = saved_session(tmp_path, request)
    ranks = rank_seats(plan)
    state = placed(initial_state(plan), {
        "P0001": [ranks[0]["seat_id"], ranks[1]["seat_id"]],
        "P0002": [ranks[2]["seat_id"], ranks[3]["seat_id"]],
        "P0003": [ranks[4]["seat_id"], ranks[5]["seat_id"]],
    })
    state = absent(state, "P0001")
    state = absent(state, "P0003")
    state = restored(state, "P0003")
    saved = save(ws, plan, state)
    result = dispatch(command(saved), store)
    assert result["status"] == "success", result
    assert audit_result(result)["passed"]
    assert result["repair_summary"]["engine"] == FAST_ENGINE
    assert result["repair_summary"]["moved_registrations"] == 1
    assignment = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
    assert set(assignment["P0003"]) == {ranks[0]["seat_id"], ranks[1]["seat_id"]}
    assert set(assignment["P0002"]) == {ranks[2]["seat_id"], ranks[3]["seat_id"]}


def test_repair_seats_a_restored_registration_when_its_tier_band_is_full(tmp_path):
    request = generate(emperor=8, merit=2, bodhi=0)
    request["layout"]["row_count"] = 2
    request["layout"]["seats"] = [s for s in request["layout"]["seats"] if s["row_number"] <= 2]
    request["layout_version_id"] = request["layout"]["layout_version_id"] = "test-two-rows-v1"
    request["solver"].update(max_time_seconds=20, num_search_workers=1, canonicalize=False)
    store, ws, plan = saved_session(tmp_path, request)
    ordered = rank_seats(plan)
    participants = plan["source_request"]["participants"]
    emperors = [p["participant_id"] for p in participants if p["contribution_tier"] == "EMPEROR"]
    merits = [p["participant_id"] for p in participants if p["contribution_tier"] == "MERIT"]
    mapping = {pid: [ordered[2 * i]["seat_id"], ordered[2 * i + 1]["seat_id"]]
               for i, pid in enumerate(emperors)}
    mapping.update({pid: [ordered[16 + i]["seat_id"]] for i, pid in enumerate(merits)})
    state = placed(initial_state(plan), mapping)
    gone_a, gone_b = emperors[2], emperors[3]
    state = absent(state, gone_a)
    state = absent(state, gone_b)
    saved = save(ws, plan, state)
    first = dispatch(command(saved), store)
    assert first["status"] == "success", first
    assert audit_result(first)["passed"]
    reopened = ws.open(plan["event_id"], "staff", first["plan_version_id"])
    saved2 = save(ws, first, restored(reopened["state"], gone_a), reopened["revision"])
    second = dispatch(command(saved2), store)
    assert second["status"] == "success", second
    assert audit_result(second)["passed"]
    assignment = {a["participant_id"]: a["seat_ids"] for a in second["assignments"]}
    assert len(assignment[gone_a]) == 2
    assert second["operations"][gone_b]["attendance_status"] == "ABSENT"
    assert second["operations"][gone_a]["attendance_status"] == "PRESENT"
    assert second["operations"][gone_a]["previous_seat_ids"] == mapping[gone_a]
    assert second["repair_summary"]["engine"] == "Google OR-Tools CP-SAT incremental repair"
    opened = ws.open(plan["event_id"], "staff", second["plan_version_id"])
    assert opened["state"]["items"][gone_a]["seat_ids"] == assignment[gone_a]
