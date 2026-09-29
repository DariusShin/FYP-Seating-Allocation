"""Independent audit of placements against original request, never CP-SAT variables."""

from collections import Counter

from seat_solver.production.policy import TIERS, DomainError, policy, validate_request
from seat_solver.production.production_scoring import eligible, options, packing_pairs, quality


def validate_placements(request, assignments, baseline=None, companion_absent=None):
    validate_request(request)
    companion_absent = companion_absent or set()
    issues = []
    if request["generation_mode"] == "REPAIR_PUBLISHED" and (
        not baseline
        or baseline.get("plan_version_id") != request["baseline_plan_version_id"]
        or baseline.get("event_id") != request["event_id"]
    ):
        return {
            "passed": False,
            "issues": [
                {
                    "rule_id": "FR14",
                    "message": "Repair requires the matching event baseline snapshot",
                }
            ],
        }

    def fail(rule, message, **details):
        issues.append({"rule_id": rule, "message": message, **details})

    ps = eligible(request)
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    if not isinstance(assignments, list):
        return {
            "passed": False,
            "issues": [{"rule_id": "C1", "message": "Assignments must be an array"}],
        }
    if any(
        not isinstance(a, dict)
        or not isinstance(a.get("participant_id"), str)
        or not isinstance(a.get("seat_ids"), list)
        or any(not isinstance(s, str) for s in a["seat_ids"])
        for a in assignments
    ):
        return {
            "passed": False,
            "issues": [{"rule_id": "C1", "message": "Malformed assignment"}],
        }
    ids = [a["participant_id"] for a in assignments]
    if Counter(ids) != Counter(p["participant_id"] for p in ps):
        fail(
            "C1",
            "Assignments must contain every eligible ID exactly once; excluded IDs forbidden",
        )
    placements = {a["participant_id"]: a["seat_ids"] for a in assignments}
    seats = [s for a in assignments for s in a["seat_ids"]]
    if len(seats) != len(set(seats)):
        fail("C2", "Physical seats are duplicated")
    for sid in seats:
        if sid not in lookup:
            fail("C4", "Unknown physical seat", seat_id=sid)
        elif lookup[sid]["is_blocked"]:
            fail("C3", "Blocked seat used", seat_id=sid)
    if issues:
        return {"passed": False, "issues": issues}
    rows = {}
    for p in ps:
        chosen = placements[p["participant_id"]]
        valid_options = options(request, p)
        if (
            p["participant_id"] in companion_absent
            and p["contribution_tier"] == "EMPEROR"
        ):
            valid_options = [
                (s,)
                for s in lookup.values()
                if not s["is_blocked"]
                and (not p["requires_accessible_seat"] or s["is_accessible"])
            ]
        if tuple(sorted(chosen)) not in {
            tuple(sorted(s["seat_id"] for s in o)) for o in valid_options
        }:
            fail(
                "C10" if p["contribution_tier"] == "EMPEROR" else "C1",
                "Wrong allocation size, invalid pair or inaccessible placement",
                participant_id=p["participant_id"],
            )
            if p["requires_accessible_seat"]:
                fail(
                    "C17",
                    "Required accessible option not satisfied",
                    participant_id=p["participant_id"],
                )
        if chosen:
            rows[p["participant_id"]] = lookup[chosen[0]]["row_number"]
    if issues:
        return {"passed": False, "issues": issues}
    # Reconstruct priority from the submitted physical seats, independently of
    # the CP-SAT expressions. Reuse details for all cross-tier comparisons.
    seat_details = {
        pid: [
            {
                "seat_id": sid,
                "row_number": lookup[sid]["row_number"],
                "priority_rank": lookup[sid]["priority_rank"],
                "order": (lookup[sid]["row_number"] - 1)
                * request["layout"]["seats_per_row"] + lookup[sid]["priority_rank"],
            }
            for sid in chosen
        ]
        for pid, chosen in placements.items()
    }
    for i, p in enumerate(ps):
        for q in ps[i + 1 :]:
            pi = TIERS.index(p["contribution_tier"])
            qi = TIERS.index(q["contribution_tier"])
            rp = rows[p["participant_id"]]
            rq = rows[q["participant_id"]]
            if pi != qi:
                higher, lower = (p, q) if pi < qi else (q, p)
                hs = seat_details[higher["participant_id"]]
                ls = seat_details[lower["participant_id"]]
                if max(s["order"] for s in hs) >= min(s["order"] for s in ls):
                    fail(
                        "C12", "Tier seat precedence violated",
                        participants=[higher["participant_id"], lower["participant_id"]],
                        higher_tier=higher["contribution_tier"],
                        lower_tier=lower["contribution_tier"],
                        higher_seats=hs, lower_seats=ls,
                    )
            if (
                pi == qi
                and (p["contribution_amount_rm"] - q["contribution_amount_rm"])
                * (rp - rq)
                > 0
            ):
                fail(
                    "C13",
                    "Contribution row ordering violated",
                    participants=[p["participant_id"], q["participant_id"]],
                )
    occupied = set(seats)
    if request["generation_mode"] != "REPAIR_PUBLISHED":
        last = max(rows.values(), default=0)
        for s in lookup.values():
            if (
                not s["is_blocked"]
                and s["row_number"] < last
                and s["seat_id"] not in occupied
            ):
                fail(
                    "C15",
                    "Empty available seat before an occupied row",
                    seat_id=s["seat_id"],
                )
        for inner, outer in packing_pairs(request["layout"]):
            if outer in occupied and inner not in occupied:
                fail("C16", "Centre-out packing gap", seat_id=inner)
    return {"passed": not issues, "issues": issues}


def audit_result(result):
    try:
        request = result["source_request"]
        baseline = result.get("baseline_snapshot")
        from seat_solver.production.workspace import apply_display, validate_metadata

        metadata = result.get("operations", {})
        validate_metadata(request, metadata)
        absent = {pid for pid, m in metadata.items() if m["companion_absent"]}
        report = validate_placements(request, result["assignments"], baseline, absent)
        if not report["passed"]:
            return report
        placements = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
        scored = quality(request, policy(), placements, baseline)
        if result["quality"] != scored:
            report["issues"].append(
                {"rule_id": "FR16", "message": "Recomputed quality metrics differ"}
            )
        expected_stages = {
            "weighted_preferences": scored["weighted"]["total"],
            "unaffected_moved_units": scored["movement"]["unaffected_moved_units"],
            "distance_doubled": scored["movement"]["distance_doubled"],
            "local_packing": scored["local_packing"],
        }
        if (
            result["solver"].get("main_penalty") != scored["weighted"]["total"]
            or result["solver"].get("objective_value") != scored["weighted"]["total"]
        ):
            report["issues"].append(
                {
                    "rule_id": "FR16",
                    "message": "Reported preference objective differs from reconstruction",
                }
            )
        for stage in result["solver"].get("proof", []):
            if stage.get("value") is not None and (
                stage.get("stage") not in expected_stages
                or stage["value"] != expected_stages[stage["stage"]]
            ):
                report["issues"].append(
                    {
                        "rule_id": "FR16",
                        "message": "Reported objective stage differs from reconstructed assignment",
                    }
                )

        {s["seat_id"]: s for s in request["layout"]["seats"]}
        from seat_solver.production.production import format_result

        expected = format_result(request, placements, result["solver"], baseline)
        apply_display(expected, metadata)
        for key in (
            "floor_plan",
            "input_summary",
            "tier_bands",
            "empty_seat_ids",
            "excluded_participants",
            "penalty_summary",
            "effective_weights",
            "weights",
            "assignments",
        ):
            if result.get(key) != expected[key]:
                report["issues"].append(
                    {"rule_id": "FR16", "message": f"Inconsistent {key}"}
                )
        report["passed"] = not report["issues"]
        return report
    except (KeyError, TypeError, ValueError, DomainError) as exc:
        return {"passed": False, "issues": [{"rule_id": "FR16", "message": str(exc)}]}
