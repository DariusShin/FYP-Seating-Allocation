"""Regression coverage for hard priority across contribution tiers (pjkit-v4)."""
import copy
import itertools

import pytest
from ortools.sat.python import cp_model

from seat_solver.production.policy import DomainError, TIERS, validate_request
from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.production_validator import audit_result, validate_placements


def mixed():
    req = generate(emperor=0, merit=1, bodhi=2)
    req["solver"].update(max_time_seconds=5, num_search_workers=1, canonicalize=False)
    for p in req["participants"]:
        p.update(participant_category="GENERAL_DEVOTEE", events_joined_last_2_years=0)
    req["participants"][1]["events_joined_last_2_years"] = 100
    return req


def assert_order(result):
    assert result["status"] == "success", result
    assignments = result["assignments"]
    # Independent tuple comparison, not the model's scalar/boundary expressions.
    for higher, lower in itertools.permutations(assignments, 2):
        if TIERS.index(higher["contribution_tier"]) < TIERS.index(lower["contribution_tier"]):
            assert max((s["row_number"], s["priority_rank"]) for s in higher["seats"]) < min(
                (s["row_number"], s["priority_rank"]) for s in lower["seats"]
            )
    assert audit_result(result)["passed"]


@pytest.mark.parametrize("mode", ["INITIAL", "REGENERATE_DRAFT"])
@pytest.mark.parametrize("keys", list(itertools.permutations(["contribution_seat", "activeness", "category_zone"])))
@pytest.mark.parametrize("contribution_enabled", [True, False])
def test_high_activity_bodhi_never_precedes_merit(mode, keys, contribution_enabled):
    req = mixed()
    req["generation_mode"] = mode
    req["preferences"] = [{"key": k, "enabled": k != "contribution_seat" or contribution_enabled} for k in keys]
    assert_order(solve(req))


@pytest.mark.parametrize("counts", [(1, 1, 1), (1, 0, 2), (0, 2, 2), (2, 1, 0)])
def test_pairs_and_missing_tiers_with_all_preferences_disabled(counts):
    req = generate(emperor=counts[0], merit=counts[1], bodhi=counts[2])
    req["solver"].update(max_time_seconds=5, canonicalize=False)
    for pref in req["preferences"]:
        pref["enabled"] = False
    assert_order(solve(req))


def test_validator_rejects_same_row_swap_with_actionable_seat_details():
    req = mixed()
    result = solve(req)
    assert_order(result)
    assignments = copy.deepcopy(result["assignments"])
    merit = next(a for a in assignments if a["contribution_tier"] == "MERIT")
    bodhi = next(a for a in assignments if a["contribution_tier"] == "BODHI")
    merit["seat_ids"], bodhi["seat_ids"] = bodhi["seat_ids"], merit["seat_ids"]
    report = validate_placements(req, assignments)
    issue = next(i for i in report["issues"] if i["rule_id"] == "C12")
    assert issue["higher_tier"] == "MERIT"
    assert issue["lower_tier"] == "BODHI"
    assert issue["higher_seats"][0]["priority_rank"] > issue["lower_seats"][0]["priority_rank"]


def test_validator_rejects_emperor_pair_after_merit():
    req = generate(emperor=1, merit=1, bodhi=0)
    # Emperor has ranks 3 and 4, while Merit has rank 1.
    assignments = [
        {"participant_id": req["participants"][0]["participant_id"], "seat_ids": ["R01-S11", "R01-S12"]},
        {"participant_id": req["participants"][1]["participant_id"], "seat_ids": ["R01-S09"]},
    ]
    assert any(i["rule_id"] == "C12" for i in validate_placements(req, assignments)["issues"])


def test_blocked_seats_and_cross_row_boundary():
    req = mixed()
    for seat in req["layout"]["seats"]:
        if seat["row_number"] == 1:
            seat["is_blocked"] = seat["physical_position"] != 9
    result = solve(req)
    assert_order(result)
    merit = next(a for a in result["assignments"] if a["contribution_tier"] == "MERIT")
    assert merit["seat_ids"] == ["R01-S09"]
    assert all(a["seats"][0]["row_number"] == 2 for a in result["assignments"] if a["contribution_tier"] == "BODHI")


def test_accessibility_conflict_is_not_exempted_from_tier_order():
    req = generate(emperor=0, merit=1, bodhi=15)
    req["participants"][0]["requires_accessible_seat"] = True
    req["solver"].update(max_time_seconds=5, canonicalize=False)
    result = solve(req)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INFEASIBLE"
    assert "tier seat precedence" in result["error"]["message"]




def test_feasible_incumbent_still_satisfies_hard_tier_order(monkeypatch):
    original = cp_model.CpSolver.Solve
    def feasible(self, *args, **kwargs):
        status = original(self, *args, **kwargs)
        return cp_model.FEASIBLE if status == cp_model.OPTIMAL else status
    monkeypatch.setattr(cp_model.CpSolver, "Solve", feasible)
    result = solve(mixed())
    assert result["solver"]["status"] == "FEASIBLE"
    assert_order(result)


def test_priority_ranks_are_unique_within_each_row():
    req = mixed()
    req["layout"]["seats"][0]["priority_rank"] = req["layout"]["seats"][1]["priority_rank"]
    with pytest.raises(DomainError, match="unique within each row"):
        validate_request(req)
