"""Independent solution validation.

Works purely from the serialized result dictionary (never from solver
internals), so the same code both audits a fresh solve and powers the
standalone ``cli validate`` command. Implements the twenty checks from the
project guide plus the hard-constraint counter block embedded in the result.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import jsonschema

from seat_solver.models import SCHEMA_VERSION, read_json

SCHEMA_DIR_ENV = "SEAT_SOLVER_SCHEMA_DIR"


def schema_dir() -> Path:
    override = os.environ.get(SCHEMA_DIR_ENV)
    if override:
        return Path(override)
    packaged = Path(__file__).resolve().parents[2] / "schemas"
    if packaged.is_dir():
        return packaged
    return Path("schemas")


def load_schema(name: str) -> dict[str, Any]:
    return read_json(schema_dir() / name)


def validate_against_schema(payload: Any, schema_name: str) -> list[str]:
    """Return a list of schema violation messages (empty when valid)."""
    schema = load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(payload)
    ][:20]


def _seat_lookup(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in result["floor_plan"]["rows"]:
        for seat in row["seats"]:
            lookup[seat["seat_id"]] = {
                **seat,
                "row_number": row["row_number"],
                "tier_band": row["tier_band"],
            }
    return lookup


def _tier_rows(result: dict[str, Any]) -> dict[str, set[int]]:
    """Declared band rows per tier, from the result's tier_bands block."""
    return {tier: set(rows) for tier, rows in result.get("tier_bands", {}).items()}


def _recompute_bands(result: dict[str, Any]) -> dict[str, set[int]]:
    """Independently re-derive the demand-driven tier bands from the result.

    Uses only the serialized floor plan (seat positions and blocked flags)
    and the tier demand in the input summary: rows are consumed front to
    back by EMPEROR (valid-pair capacity: odd-even adjacent non-blocked
    positions, never spanning the aisle), then BODHI and MERIT (non-blocked
    seat capacity), mirroring the engine's band derivation.
    """
    summary = result["input_summary"]
    aisle = result["floor_plan"]["aisle_after_position"]
    demand = {
        "EMPEROR": summary["emperor_count"],
        "BODHI": summary["bodhi_count"],
        "MERIT": summary["merit_count"],
    }
    pair_capacity: dict[int, int] = {}
    seat_capacity: dict[int, int] = {}
    for row in result["floor_plan"]["rows"]:
        row_number = row["row_number"]
        available = {
            seat["physical_position"] for seat in row["seats"] if not seat["is_blocked"]
        }
        seat_capacity[row_number] = len(available)
        pairs = 0
        for position in sorted(available):
            if position % 2 == 1 and position + 1 in available:
                if (position, position + 1) != (aisle, aisle + 1):
                    pairs += 1
        pair_capacity[row_number] = pairs

    bands: dict[str, set[int]] = {}
    next_row = 1
    max_row = max(seat_capacity, default=0)
    for tier in ("EMPEROR", "BODHI", "MERIT"):
        capacity = pair_capacity if tier == "EMPEROR" else seat_capacity
        remaining = demand[tier]
        band: set[int] = set()
        while remaining > 0 and next_row <= max_row:
            take = min(remaining, capacity.get(next_row, 0))
            if take > 0:
                band.add(next_row)
                remaining -= take
            next_row += 1
        bands[tier] = band
    return bands


def compute_hard_constraint_validation(result: dict[str, Any]) -> dict[str, Any]:
    """Recount every hard-constraint violation directly from the result JSON."""
    seats = _seat_lookup(result)
    tier_rows = _tier_rows(result)
    aisle = result["floor_plan"]["aisle_after_position"]
    assignments = result["assignments"]

    seat_usage: dict[str, int] = {}
    tier_band_violations = 0
    adjacency_violations = 0
    aisle_violations = 0
    accessibility_violations = 0
    blocked_violations = 0

    for assignment in assignments:
        assigned = [seats[s["seat_id"]] for s in assignment["seats"]]
        for seat in assigned:
            seat_usage[seat["seat_id"]] = seat_usage.get(seat["seat_id"], 0) + 1
            if seat["is_blocked"]:
                blocked_violations += 1
            if seat["row_number"] not in tier_rows.get(
                assignment["contribution_tier"], set()
            ):
                tier_band_violations += 1

        if assignment["allocation_type"] == "EMPEROR_PAIR":
            if len(assigned) != 2:
                adjacency_violations += 1
            else:
                first, second = sorted(assigned, key=lambda s: s["physical_position"])
                positions = (first["physical_position"], second["physical_position"])
                same_row = first["row_number"] == second["row_number"]
                adjacent = positions[1] - positions[0] == 1 and positions[0] % 2 == 1
                if positions == (aisle, aisle + 1):
                    aisle_violations += 1
                elif not (same_row and adjacent):
                    adjacency_violations += 1
        elif len(assigned) != 1:
            adjacency_violations += 1

        if assignment["requires_accessible_seat"]:
            if assignment["allocation_type"] == "SINGLE":
                if not assigned[0]["is_accessible"]:
                    accessibility_violations += 1
            elif not any(seat["is_accessible"] for seat in assigned):
                accessibility_violations += 1

    duplicate_seats = sum(1 for count in seat_usage.values() if count > 1)

    order_violations = 0
    by_tier: dict[str, list[dict[str, Any]]] = {}
    for assignment in assignments:
        by_tier.setdefault(assignment["contribution_tier"], []).append(assignment)
    for members in by_tier.values():
        rows = [
            (
                member["contribution_amount_rm"],
                max(seats[s["seat_id"]]["row_number"] for s in member["seats"]),
            )
            for member in members
        ]
        for contribution_i, row_i in rows:
            for contribution_j, row_j in rows:
                if contribution_i > contribution_j and row_i > row_j:
                    order_violations += 1

    counters = {
        "duplicate_seat_count": duplicate_seats,
        "unassigned_count": len(result["unassigned_participants"]),
        "tier_band_violation_count": tier_band_violations,
        "contribution_order_violation_count": order_violations,
        "emperor_adjacency_violation_count": adjacency_violations,
        "aisle_crossing_violation_count": aisle_violations,
        "accessibility_violation_count": accessibility_violations,
        "blocked_seat_violation_count": blocked_violations,
        "front_fill_violation_count": count_front_fill_violations(result),
        "middle_fill_violation_count": count_middle_fill_violations(result),
    }
    counters["all_constraints_satisfied"] = all(
        value == 0 for value in counters.values() if isinstance(value, int)
    )
    return counters


def count_front_fill_violations(result: dict[str, Any]) -> int:
    """HC13: inside each tier zone, a row with an empty available seat must
    not be followed by an occupied row. Counts each earlier row that still
    has an empty seat while a later zone row holds any occupant. Returns 0
    when front-fill enforcement is disabled in the run's constraint config.
    """
    constraint_config = result.get("constraint_config", {})
    if not constraint_config.get("enforce_front_fill", False):
        return 0
    band_rows: dict[str, list[dict[str, Any]]] = {}
    for row in result["floor_plan"]["rows"]:
        if row["tier_band"] is None:
            continue
        band_rows.setdefault(row["tier_band"], []).append(row)
    violations = 0
    for rows in band_rows.values():
        ordered = sorted(rows, key=lambda row: row["row_number"])
        for index, row in enumerate(ordered):
            has_empty = any(
                seat["occupancy_status"] == "EMPTY" for seat in row["seats"]
            )
            later_occupied = any(
                seat["occupancy_status"] == "OCCUPIED"
                for later in ordered[index + 1 :]
                for seat in later["seats"]
            )
            if has_empty and later_occupied:
                violations += 1
    return violations


def count_middle_fill_violations(result: dict[str, Any]) -> int:
    """HC14: on each side of each row the occupied seats must form one
    contiguous block starting at the centre aisle. Walking outward from the
    aisle over the non-blocked seats, every occupied seat found after an
    empty seat is one violation. Returns 0 when middle-fill enforcement is
    disabled in the run's constraint config.
    """
    constraint_config = result.get("constraint_config", {})
    if not constraint_config.get("enforce_middle_fill", False):
        return 0
    aisle = result["floor_plan"]["aisle_after_position"]
    violations = 0
    for row in result["floor_plan"]["rows"]:
        available = [
            seat for seat in row["seats"] if seat["occupancy_status"] != "BLOCKED"
        ]
        left_outward = sorted(
            (seat for seat in available if seat["physical_position"] <= aisle),
            key=lambda seat: seat["physical_position"],
            reverse=True,
        )
        right_outward = sorted(
            (seat for seat in available if seat["physical_position"] > aisle),
            key=lambda seat: seat["physical_position"],
        )
        for side in (left_outward, right_outward):
            seen_empty = False
            for seat in side:
                if seat["occupancy_status"] == "EMPTY":
                    seen_empty = True
                elif seen_empty and seat["occupancy_status"] == "OCCUPIED":
                    violations += 1
    return violations


def _check(
    checks: list[dict[str, Any]],
    check_id: str,
    name: str,
    passed: bool,
    details: str = "",
) -> None:
    checks.append(
        {"check_id": check_id, "name": name, "passed": bool(passed), "details": details}
    )


def validate_result(
    result: dict[str, Any], generated_at: str, result_file: str | None = None
) -> dict[str, Any]:
    """Run the full twenty-point independent validation of a success result."""
    checks: list[dict[str, Any]] = []

    if result.get("status") != "success":
        _check(
            checks,
            "C00",
            "Result has success status",
            False,
            f"status is {result.get('status')!r}; error results cannot be validated "
            "as allocations",
        )
        return _report(checks, generated_at, result_file)

    summary = result["input_summary"]
    assignments = result["assignments"]
    seats = _seat_lookup(result)
    tier_rows = _tier_rows(result)

    expected_primary = (
        summary["emperor_count"] + summary["bodhi_count"] + summary["merit_count"]
    )
    _check(
        checks,
        "C01",
        "Exactly 122 primary participants processed",
        len(assignments) + len(result["unassigned_participants"]) == expected_primary
        and summary["primary_participant_count"] == expected_primary
        and expected_primary == 122,
        f"assignments={len(assignments)}, "
        f"unassigned={len(result['unassigned_participants'])}",
    )

    occupied_ids = [s["seat_id"] for a in assignments for s in a["seats"]]
    occupied_status_count = sum(
        1
        for row in result["floor_plan"]["rows"]
        for seat in row["seats"]
        if seat["occupancy_status"] == "OCCUPIED"
    )
    _check(
        checks,
        "C02",
        "Exactly 208 physical seats occupied",
        len(occupied_ids)
        == summary["required_seat_count"]
        == occupied_status_count
        == 208,
        f"occupied={len(occupied_ids)}",
    )
    blocked_status_count = sum(
        1
        for row in result["floor_plan"]["rows"]
        for seat in row["seats"]
        if seat["occupancy_status"] == "BLOCKED"
    )
    _check(
        checks,
        "C03",
        "Exactly 24 seats empty (and 24 blocked)",
        len(result["empty_seat_ids"]) == summary["empty_seat_count"] == 24
        and blocked_status_count == summary["blocked_seat_count"] == 24
        and len(result["empty_seat_ids"])
        == summary["available_seat_count"] - len(occupied_ids),
        f"empty={len(result['empty_seat_ids'])}, blocked={blocked_status_count}",
    )
    _check(
        checks,
        "C04",
        "No physical seat duplicated",
        len(occupied_ids) == len(set(occupied_ids)),
        "",
    )

    bodhi = [a for a in assignments if a["contribution_tier"] == "BODHI"]
    merit = [a for a in assignments if a["contribution_tier"] == "MERIT"]
    emperor = [a for a in assignments if a["contribution_tier"] == "EMPEROR"]
    _check(
        checks,
        "C05",
        "Every Bodhi participant has exactly one seat",
        len(bodhi) == summary["bodhi_count"]
        and all(len(a["seat_ids"]) == 1 for a in bodhi),
        f"bodhi={len(bodhi)}",
    )
    _check(
        checks,
        "C06",
        "Every Merit participant has exactly one seat",
        len(merit) == summary["merit_count"]
        and all(len(a["seat_ids"]) == 1 for a in merit),
        f"merit={len(merit)}",
    )
    _check(
        checks,
        "C07",
        "Every Emperor allocation has exactly two seats",
        len(emperor) == summary["emperor_count"]
        and all(len(a["seat_ids"]) == 2 for a in emperor),
        f"emperor={len(emperor)}",
    )

    aisle = result["floor_plan"]["aisle_after_position"]
    adjacency_ok = True
    aisle_ok = True
    for a in emperor:
        pair = sorted(
            (seats[s["seat_id"]] for s in a["seats"]),
            key=lambda s: s["physical_position"],
        )
        if len(pair) != 2:
            adjacency_ok = False
            continue
        positions = (pair[0]["physical_position"], pair[1]["physical_position"])
        if positions == (aisle, aisle + 1):
            aisle_ok = False
        if (
            pair[0]["row_number"] != pair[1]["row_number"]
            or positions[1] - positions[0] != 1
            or positions[0] % 2 == 0
        ):
            adjacency_ok = False
    _check(checks, "C08", "Every Emperor pair is a valid adjacent pair", adjacency_ok)
    _check(checks, "C09", "No Emperor pair crosses the centre aisle", aisle_ok)

    def tier_in_band(members: list[dict[str, Any]], tier: str) -> bool:
        return all(
            seats[s["seat_id"]]["row_number"] in tier_rows.get(tier, set())
            for member in members
            for s in member["seats"]
        )

    _check(
        checks,
        "C10",
        "Every allocation sits inside its tier's band; rows are tier-exclusive",
        tier_in_band(emperor, "EMPEROR")
        and tier_in_band(bodhi, "BODHI")
        and tier_in_band(merit, "MERIT")
        and not (tier_rows.get("EMPEROR", set()) & tier_rows.get("BODHI", set()))
        and not (tier_rows.get("EMPEROR", set()) & tier_rows.get("MERIT", set()))
        and not (tier_rows.get("BODHI", set()) & tier_rows.get("MERIT", set())),
    )

    def band_ordered(front: set[int], back: set[int]) -> bool:
        if not front or not back:
            return True
        return max(front) < min(back)

    _check(
        checks,
        "C11",
        "Tier bands are ordered Emperor before Bodhi before Merit",
        band_ordered(tier_rows.get("EMPEROR", set()), tier_rows.get("BODHI", set()))
        and band_ordered(tier_rows.get("BODHI", set()), tier_rows.get("MERIT", set()))
        and band_ordered(
            tier_rows.get("EMPEROR", set()), tier_rows.get("MERIT", set())
        ),
    )

    recomputed = _recompute_bands(result)
    _check(
        checks,
        "C12",
        "Declared tier bands match the demand-derived front packing",
        all(tier_rows.get(tier, set()) == recomputed[tier] for tier in recomputed),
        f"declared={ {t: sorted(r) for t, r in tier_rows.items()} }, "
        f"recomputed={ {t: sorted(r) for t, r in recomputed.items()} }",
    )

    order_ok = True
    for members in (emperor, bodhi, merit):
        rows = [
            (
                m["contribution_amount_rm"],
                max(seats[s["seat_id"]]["row_number"] for s in m["seats"]),
            )
            for m in members
        ]
        for contribution_i, row_i in rows:
            for contribution_j, row_j in rows:
                if contribution_i > contribution_j and row_i > row_j:
                    order_ok = False
    _check(checks, "C13", "Contribution ordering holds inside each tier", order_ok)

    accessibility_ok = True
    for a in assignments:
        if not a["requires_accessible_seat"]:
            continue
        flags = [seats[s["seat_id"]]["is_accessible"] for s in a["seats"]]
        satisfied = all(flags) if a["allocation_type"] == "SINGLE" else any(flags)
        if not satisfied:
            accessibility_ok = False
    _check(checks, "C14", "Accessibility requirements satisfied", accessibility_ok)

    _check(
        checks,
        "C15",
        "No blocked seat is used",
        not any(
            seats[s["seat_id"]]["is_blocked"] for a in assignments for s in a["seats"]
        ),
    )

    weights = result["weights"]
    weight_map = {
        "priority_seat": weights["priority_seat_weight"],
        "category_zone": weights["category_zone_weight"],
        "movement": weights["movement_weight"],
        "activeness": weights["activeness_weight"],
    }
    constraint_config = result["constraint_config"]
    normalize = constraint_config["normalize_penalties"]
    norm_scale = constraint_config["normalization_scale"]
    maxima = constraint_config["component_maxima"]

    def expected_normalized(key: str, raw: int) -> int:
        if not normalize:
            return raw
        max_raw = max(1, maxima[key])
        return (2 * norm_scale * raw + max_raw) // (2 * max_raw)

    unweighted_totals = {key: 0 for key in weight_map}
    normalized_totals = {key: 0 for key in weight_map}
    weighted_totals = {key: 0 for key in weight_map}
    penalty_consistent = True
    for a in assignments:
        penalty = a["penalty"]
        weighted_sum = 0
        for key, weight in weight_map.items():
            unweighted = penalty["unweighted"][key]
            normalized = penalty["normalized"][key]
            weighted = penalty["weighted"][key]
            if normalized != expected_normalized(key, unweighted):
                penalty_consistent = False
            if weighted != weight * normalized:
                penalty_consistent = False
            unweighted_totals[key] += unweighted
            normalized_totals[key] += normalized
            weighted_totals[key] += weighted
            weighted_sum += weighted
        if penalty["weighted"]["total"] != weighted_sum:
            penalty_consistent = False
    summary_penalty = result["penalty_summary"]
    if summary_penalty["unweighted"] != unweighted_totals:
        penalty_consistent = False
    if summary_penalty["normalized"] != normalized_totals:
        penalty_consistent = False
    expected_weighted = {
        **weighted_totals,
        "tie_break": summary_penalty["weighted"]["tie_break"],
        "total": sum(weighted_totals.values())
        + summary_penalty["weighted"]["tie_break"],
    }
    if summary_penalty["weighted"] != expected_weighted:
        penalty_consistent = False
    _check(
        checks, "C16", "Penalty totals are internally consistent", penalty_consistent
    )

    solver_stats = result["solver"]
    main_penalty = sum(weighted_totals.values())
    reconstructed = (
        solver_stats["main_objective_scale"] * main_penalty
        + summary_penalty["weighted"]["tie_break"]
    )
    _check(
        checks,
        "C17",
        "Reconstructed weighted objective matches solver objective",
        solver_stats["main_penalty"] == main_penalty
        and solver_stats["tie_break_penalty"]
        == summary_penalty["weighted"]["tie_break"]
        and solver_stats["objective_value"] == reconstructed,
        f"reconstructed={reconstructed}, reported={solver_stats['objective_value']}",
    )

    schema_errors = validate_against_schema(result, "solver_result.schema.json")
    _check(
        checks,
        "C18",
        "Result conforms to solver_result.schema.json",
        not schema_errors,
        "; ".join(schema_errors),
    )
    _check(
        checks, "C19", "Solver status is OPTIMAL", solver_stats["status"] == "OPTIMAL"
    )
    _check(
        checks,
        "C20",
        "Optimality gap equals zero",
        solver_stats["optimality_gap"] == 0,
        f"gap={solver_stats['optimality_gap']}",
    )

    if constraint_config["enforce_front_fill"]:
        front_fill_violations = count_front_fill_violations(result)
        _check(
            checks,
            "C21",
            "Rows fill front to back inside each tier band",
            front_fill_violations == 0,
            f"violating_rows={front_fill_violations}",
        )

    if constraint_config.get("enforce_middle_fill", False):
        middle_fill_violations = count_middle_fill_violations(result)
        _check(
            checks,
            "C22",
            "Row occupancy fills outward from the centre aisle",
            middle_fill_violations == 0,
            f"violating_seats={middle_fill_violations}",
        )

    return _report(checks, generated_at, result_file)


def _report(
    checks: list[dict[str, Any]], generated_at: str, result_file: str | None
) -> dict[str, Any]:
    passed = sum(1 for c in checks if c["passed"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "result_file": result_file,
        "overall_passed": passed == len(checks),
        "summary": {
            "total_checks": len(checks),
            "passed_checks": passed,
            "failed_checks": len(checks) - passed,
        },
        "checks": checks,
    }
