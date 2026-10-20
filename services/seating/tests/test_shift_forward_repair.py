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
