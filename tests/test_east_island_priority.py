"""Production row priority and compulsory 东单-before-西单 packing."""

import pytest

from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.production_validator import audit_result, validate_placements


PATTERN = [16, 15, 14, 13, 12, 11, 10, 9, 1, 2, 3, 4, 5, 6, 7, 8]


def request_for(emperor=0, merit=0, mode="INITIAL"):
    request = generate(emperor=emperor, merit=merit, bodhi=0)
    request["generation_mode"] = mode
    request["solver"].update(max_time_seconds=5, num_search_workers=1, canonicalize=False)
    for pref in request["preferences"]:
        pref["enabled"] = False
    return request


def assert_prefix(request, result):
    assert result["status"] == "success", result
    occupied = {sid for a in result["assignments"] for sid in a["seat_ids"]}
    # Independent physical-coordinate oracle: front rows, east outward, west outward.
    ordered = sorted(
        (s for s in request["layout"]["seats"] if not s["is_blocked"]),
        key=lambda s: (
            s["row_number"],
            0 if s["physical_position"] > 8 else 1,
            s["physical_position"] if s["physical_position"] > 8 else -s["physical_position"],
        ),
    )
    assert occupied == {s["seat_id"] for s in ordered[:len(occupied)]}
    assert audit_result(result)["passed"]


def test_current_priority_pattern_in_every_row():
    request = request_for()
    for row in range(1, 17):
        seats = sorted(
            (s for s in request["layout"]["seats"] if s["row_number"] == row),
            key=lambda s: s["physical_position"],
        )
        assert [s["priority_rank"] for s in seats] == PATTERN


@pytest.mark.parametrize("mode", ["INITIAL", "REGENERATE_DRAFT"])
@pytest.mark.parametrize("count", [0, 1, 7, 8, 9, 16, 17])
def test_east_fills_before_west_with_no_preferences(mode, count):
    request = request_for(merit=count, mode=mode)
    assert_prefix(request, solve(request))


@pytest.mark.parametrize("blocked", [(10, 16), tuple(range(9, 17)), (5, 6, 11, 12)])
def test_blocked_east_seats_do_not_prevent_west_occupancy(blocked):
    request = request_for(merit=9)
    for seat in request["layout"]["seats"]:
        if seat["row_number"] == 1:
            seat["is_blocked"] = seat["physical_position"] in blocked
    assert_prefix(request, solve(request))


@pytest.mark.parametrize("count", [1, 4, 5])
def test_emperor_pairs_fill_east_before_west(count):
    request = request_for(emperor=count)
    assert_prefix(request, solve(request))


def test_validator_rejects_west_occupancy_with_east_vacancy():
    request = request_for(merit=2)
    assignments = [
        {"participant_id": "P0001", "seat_ids": ["R01-S09"]},
        {"participant_id": "P0002", "seat_ids": ["R01-S08"]},
    ]
    report = validate_placements(request, assignments)
    assert not report["passed"]
    assert {i["rule_id"] for i in report["issues"]} == {"C16"}
    assert any(i["seat_id"] == "R01-S10" for i in report["issues"])


def test_accessibility_does_not_allow_bypassing_east_vacancies():
    request = request_for(merit=1)
    request["participants"][0]["requires_accessible_seat"] = True
    # Only west accessibility remains; east has assignable non-accessible seats.
    for seat in request["layout"]["seats"]:
        if seat["row_number"] == 1 and seat["physical_position"] in (15, 16):
            seat["is_blocked"] = True
    result = solve(request)
    assert result["error"]["code"] == "INFEASIBLE"


def test_stale_interleaved_input_ranks_are_rejected():
    request = request_for(merit=1)
    for seat in request["layout"]["seats"]:
        pos = seat["physical_position"]
        seat["priority_rank"] = 2 * (pos - 9) + 1 if pos > 8 else 2 * (8 - pos) + 2
    result = solve(request)
    assert result["error"]["code"] == "INVALID_INPUT"
    assert "Seat priority ranks" in result["error"]["message"]
