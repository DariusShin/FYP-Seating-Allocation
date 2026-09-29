"""Production CP-SAT engine: shared rows, ranked preferences and paid-seat retention."""

from __future__ import annotations

import copy
import time
import uuid
from datetime import datetime, timezone

from ortools.sat.python import cp_model

from seat_solver.production.policy import (
    TIERS,
    DomainError,
    mapped_weights,
    policy,
    validate_request,
)
from seat_solver.production.production_scoring import (
    candidate_cost,
    eligible,
    options,
    packing_pairs,
    quality,
)
from seat_solver.production.production_validator import validate_placements


def now():
    return datetime.now(timezone.utc).isoformat()


def error(code, message, details=None, status=None):
    return {
        "schema_version": "2.0.0",
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "solver_status": status,
        },
    }


def initial_rows(request):
    """Sound row pruning from global front packing and ordered equal-size groups."""
    slots = [
        s["row_number"]
        for s in sorted(
            request["layout"]["seats"],
            key=lambda s: (s["row_number"], s["physical_position"]),
        )
        if not s["is_blocked"]
    ]
    groups = {}
    for p in eligible(request):
        groups.setdefault(
            (TIERS.index(p["contribution_tier"]), -p["contribution_amount_rm"]), []
        ).append(p)
    offset = 0
    result = {}
    for (tier, _), members in sorted(groups.items()):
        size = len(members) * (2 if tier == 0 else 1)
        rows = set(slots[offset : offset + size])
        offset += size
        for p in members:
            result[p["participant_id"]] = rows
    return result


def build(request, cfg):
    model = cp_model.CpModel()
    ps = eligible(request)
    layout = request["layout"]
    vars_by = {}
    option_by = {}
    rowexpr = {}
    bestexpr = {}
    worstexpr = {}
    costexpr = []
    occupants = {s["seat_id"]: [] for s in layout["seats"]}
    canon = {}
    allowed = initial_rows(request)
    for p in ps:
        pid = p["participant_id"]
        opts = options(request, p)
        if allowed is not None:
            opts = [o for o in opts if o[0]["row_number"] in allowed[pid]]
        opts = sorted(opts, key=lambda o: tuple(s["seat_id"] for s in o))
        vs = []
        option_by[pid] = opts
        for j, o in enumerate(opts):
            v = model.NewBoolVar(f"assign[{pid},{j}]")
            vs.append(v)
            for s in o:
                occupants[s["seat_id"]].append(v)
            costexpr.append(v * candidate_cost(request, cfg, p, o)["weighted"]["total"])
        model.AddExactlyOne(vs)
        vars_by[pid] = vs
        rowexpr[pid] = sum(v * o[0]["row_number"] for v, o in zip(vs, opts))
        # Row-major priority includes BOTH physical seats of an Emperor option.
        orders = [
            [(s["row_number"] - 1) * layout["seats_per_row"] + s["priority_rank"]
             for s in o]
            for o in opts
        ]
        bestexpr[pid] = sum(v * min(order) for v, order in zip(vs, orders))
        worstexpr[pid] = sum(v * max(order) for v, order in zip(vs, orders))
        canon[pid] = sum(v * j for j, v in enumerate(vs))
    occ = {sid: sum(vs) for sid, vs in occupants.items()}
    for vs in occupants.values():
        if len(vs) > 1:
            model.AddAtMostOne(vs)
    # Within-tier contribution ordering remains a row-only rule (C13).
    for tier in TIERS:
        levels = {}
        for p in ps:
            if p["contribution_tier"] == tier:
                levels.setdefault(-p["contribution_amount_rm"], []).append(
                    rowexpr[p["participant_id"]]
                )
        ordered = sorted(levels)
        for i, (a, b) in enumerate(zip(ordered, ordered[1:])):
            boundary = model.NewIntVar(1, layout["row_count"], f"row_boundary[{tier},{i}]")
            for expr in levels[a]:
                model.Add(expr <= boundary)
            for expr in levels[b]:
                model.Add(expr >= boundary)
    # C12: all seats of a higher tier precede every seat of the next nonempty
    # tier. Adjacent nonempty boundaries imply every cross-tier comparison.
    tiers = [[p["participant_id"] for p in ps if p["contribution_tier"] == tier]
             for tier in TIERS]
    tiers = [members for members in tiers if members]
    for i, (higher, lower) in enumerate(zip(tiers, tiers[1:])):
        boundary = model.NewIntVar(
            1, layout["row_count"] * layout["seats_per_row"], f"tier_boundary[{i}]"
        )
        for pid in higher:
            model.Add(worstexpr[pid] <= boundary)
        for pid in lower:
            model.Add(bestexpr[pid] > boundary)
    for inner, outer in packing_pairs(layout):
        model.Add(occ[outer] <= occ[inner])
    demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in ps)
    for r in range(1, layout["row_count"] + 1):
        seats = [s for s in layout["seats"] if s["row_number"] == r and not s["is_blocked"]]
        target = min(demand, len(seats))
        demand -= target
        model.Add(sum(occ[s["seat_id"]] for s in seats) == target)
    stages = [("weighted_preferences", sum(costexpr))]
    return model, vars_by, option_by, stages, canon


def solve(request):
    started = time.perf_counter()
    timing = {}
    try:
        request = validate_request(request)
        cfg = policy()
        timing["input_validation"] = time.perf_counter() - started
        ps = eligible(request)
        demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in ps)
        available = sum(not s["is_blocked"] for s in request["layout"]["seats"])
        if demand > available:
            raise DomainError(
                "CAPACITY_EXCEEDED",
                "Physical seat demand exceeds assignable capacity",
                {"required": demand, "available": available},
            )
        for p in ps:
            if not options(request, p):
                raise DomainError(
                    "TIER_CAPACITY_EXCEEDED",
                    "Registration has no accessible/legal seat or pair",
                    {"participant_id": p["participant_id"]},
                )
        deadline = started + request["solver"]["max_time_seconds"]
        t = time.perf_counter()
        model, variables, opts, stages, canon = build(request, cfg)
        timing["model_build"] = (
            timing.get("model_build", 0) + time.perf_counter() - t
        )
        solutions = None
        proof = []
        status_name = "UNKNOWN"
        canonical_complete = False
        stage_failed = False
        for name, expr in stages:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                status_name = "FEASIBLE" if solutions is not None else "UNKNOWN"
                stage_failed = True
                break
            model.Minimize(expr)
            engine = cp_model.CpSolver()
            engine.parameters.max_time_in_seconds = remaining
            engine.parameters.num_search_workers = request["solver"][
                "num_search_workers"
            ]
            engine.parameters.random_seed = request["solver"]["random_seed"]
            st = engine.Solve(model)
            status_name = engine.StatusName(st)
            timing["solver"] = timing.get("solver", 0) + engine.WallTime()
            if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                solutions = {
                    pid: [
                        s["seat_id"]
                        for j, o in enumerate(opts[pid])
                        if engine.Value(variables[pid][j])
                        for s in o
                    ]
                    for pid in variables
                }
                value = int(engine.Value(expr))
                bound = engine.BestObjectiveBound()
                proof.append(
                    {
                        "stage": name,
                        "status": status_name,
                        "value": value,
                        "best_bound": bound,
                        "absolute_gap": max(0, value - bound),
                        "relative_gap": max(0, value - bound) / max(1, abs(value)),
                    }
                )
                if st == cp_model.OPTIMAL:
                    model.Add(expr == value)
                else:
                    stage_failed = True
                    break
            else:
                proof.append(
                    {
                        "stage": name,
                        "status": status_name,
                        "value": None,
                        "best_bound": None,
                    }
                )
                stage_failed = True
                if solutions is not None:
                    status_name = "FEASIBLE"
                break
        if solutions is None:
            return error(
                status_name
                if status_name in ("INFEASIBLE", "MODEL_INVALID")
                else "SOLVER_UNKNOWN",
                "No valid allocation established under the current compulsory rules. Check strict tier seat precedence, accessibility, pairing, contribution order and initial packing.",
                {"proof": proof},
                status_name,
            )
        business_optimal = not stage_failed
        if business_optimal and request["solver"]["canonicalize"]:
            canonical_complete = True
            for pid in sorted(canon):
                if len(opts[pid]) <= 1:
                    continue
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    canonical_complete = False
                    break
                model.Minimize(canon[pid])
                engine = cp_model.CpSolver()
                engine.parameters.max_time_in_seconds = remaining
                engine.parameters.num_search_workers = 1
                engine.parameters.random_seed = request["solver"]["random_seed"]
                st = engine.Solve(model)
                timing["solver"] = timing.get("solver", 0) + engine.WallTime()
                if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    solutions = {
                        key: [
                            s["seat_id"]
                            for j, o in enumerate(opts[key])
                            if engine.Value(variables[key][j])
                            for s in o
                        ]
                        for key in variables
                    }
                if st != cp_model.OPTIMAL:
                    canonical_complete = False
                    break
                model.Add(canon[pid] == engine.Value(canon[pid]))
        if request["solver"]["require_optimal"] and not business_optimal:
            return error(
                "OPTIMAL_NOT_PROVEN",
                "Strict benchmark requires proven business objectives",
                {"proof": proof},
                "FEASIBLE",
            )
        t = time.perf_counter()
        audit = validate_placements(
            request,
            [
                {"participant_id": pid, "seat_ids": ids}
                for pid, ids in solutions.items()
            ],
            )
        timing["independent_validation"] = time.perf_counter() - t
        if not audit["passed"]:
            return error(
                "OUTPUT_VALIDATION_FAILED",
                "Independent hard validation failed",
                audit,
            )
        stats = {
            "engine": "Google OR-Tools CP-SAT",
            "status": "OPTIMAL" if business_optimal else "FEASIBLE",
            "proof": proof,
            "canonicalization_complete": canonical_complete,
            "optimality_scope": "full_model",
        "wall_time_seconds": timing.get("solver", 0),
            "timing": timing,
            "end_to_end_seconds": time.perf_counter() - started,
            "num_boolean_variables": sum(len(v) for v in variables.values()),
            "num_integer_variables": len(model.Proto().variables)
            - sum(len(v) for v in variables.values()),
            "num_constraints": len(model.Proto().constraints),
            "num_conflicts": engine.NumConflicts(),
            "num_branches": engine.NumBranches(),
            "response_stats": engine.ResponseStats(),
        }
        result = format_result(request, solutions, stats)
        return result
    except DomainError as exc:
        return error(exc.code, str(exc), exc.details)


def format_result(request, placements, stats):
    cfg = policy()
    q = quality(request, cfg, placements)
    weights = mapped_weights(request["preferences"])
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    assignments = []
    seat_owner = {}
    display = {}

    def legacy(c):
        return {
            "priority_seat": c["contribution_seat"],
            "category_zone": c["category_zone"],
            "activeness": c["activeness"],
        }

    for p in eligible(request):
        pid = p["participant_id"]
        seats = [lookup[s] for s in placements[pid]]
        ordered = sorted(seats, key=lambda s: s["priority_rank"])
        for i, s in enumerate(ordered):
            display[s["seat_id"]] = (
                p["full_name"]
                if i == 0 or not p["adjacent_person_name"]
                else p["adjacent_person_name"]
            )
            seat_owner[s["seat_id"]] = pid
        cost = q["penalties"][pid]
        lp = {k: legacy(cost[k]) for k in ("unweighted", "normalized", "weighted")}
        lp["weighted"]["total"] = cost["weighted"]["total"]
        assignments.append(
            {
                **p,
                "is_monk": p["participant_category"] == "MONASTIC",
                "is_elderly": p["age"] >= 60,
                "allocation_type": "EMPEROR_PAIR" if len(seats) == 2 else "SINGLE",
                "seat_ids": [s["seat_id"] for s in seats],
                "seats": [
                    {
                        k: s[k]
                        for k in (
                            "seat_id",
                            "row_number",
                            "physical_position",
                            "priority_rank",
                            "zone",
                        )
                    }
                    | {"display_name": display[s["seat_id"]]}
                    for s in seats
                ],
                "pair_priority": sum(s["priority_rank"] for s in seats) / len(seats)
                if len(seats) == 2
                else None,
                "penalty": lp,
            }
        )
    tier_by_pid = {
        p["participant_id"]: p["contribution_tier"] for p in eligible(request)
    }
    last = max((lookup[s]["row_number"] for s in seat_owner), default=0)
    rows = []
    bands = {t: [] for t in TIERS}
    for r in range(1, request["layout"]["row_count"] + 1):
        cells = []
        for s in sorted(
            (s for s in lookup.values() if s["row_number"] == r),
            key=lambda s: s["physical_position"],
        ):
            pid = seat_owner.get(s["seat_id"])
            cells.append(
                {
                    **s,
                    "occupancy_status": "BLOCKED"
                    if s["is_blocked"]
                    else "OCCUPIED"
                    if pid
                    else "EMPTY",
                    "participant_id": pid,
                    "display_name": display.get(s["seat_id"]),
                    "tier": tier_by_pid.get(pid),
                    "section": "NUMBERED" if r <= last else "FREE_SEATING",
                }
            )
        tiers = [t for t in TIERS if any(c["tier"] == t for c in cells)]
        for t in tiers:
            bands[t].append(r)
        rows.append(
            {
                "row_number": r,
                "tier_band": tiers[0] if len(tiers) == 1 else None,
                "tier_bands": tiers,
                "seats": cells,
            }
        )
    ps = eligible(request)
    demand = sum(len(v) for v in placements.values())
    blocked = sum(s["is_blocked"] for s in lookup.values())
    normalized = legacy(q["normalized"])
    weighted = legacy(q["weighted"])
    weighted.update(total=q["weighted"]["total"], tie_break=0)
    stats = copy.deepcopy(stats)
    stats.update(
        main_penalty=q["weighted"]["total"],
        objective_value=q["weighted"]["total"],
        main_objective_scale=1,
        tie_break_penalty=0,
    )
    prefproof = next(
        (p for p in stats.get("proof", []) if p["stage"] == "weighted_preferences"),
        None,
    )
    stats["best_objective_bound"] = prefproof["best_bound"] if prefproof else None
    stats["optimality_gap"] = prefproof.get("absolute_gap") if prefproof else None
    return {
        "schema_version": "2.0.0",
        "status": "success",
        "run_id": str(uuid.uuid4()),
        "generated_at": now(),
        "event_id": request["event_id"],
        "generation_mode": request["generation_mode"],
        "policy_version_id": request["policy_version_id"],
        "layout_version_id": request["layout_version_id"],
        "preference_profile_version": request["preference_profile_version"],
        "normalization_version": cfg["normalization_version"],
        "preferences": copy.deepcopy(request["preferences"]),
        "effective_weights": weights,
        "source_request": copy.deepcopy(request),
        "manually_modified": False,
        "publication_status": "DRAFT",
        "solver_status_at_generation": stats["status"],
        "solver": stats,
        "quality": q,
        "input_summary": {
            "submitted_registration_count": len(request["participants"]),
            "eligible_registration_count": len(ps),
            "excluded_registration_count": len(request["participants"]) - len(ps),
            "allocation_unit_count": len(ps),
            "primary_participant_count": len(ps),
            "emperor_count": sum(p["contribution_tier"] == "EMPEROR" for p in ps),
            "merit_count": sum(p["contribution_tier"] == "MERIT" for p in ps),
            "bodhi_count": sum(p["contribution_tier"] == "BODHI" for p in ps),
            "required_seat_count": demand,
            "total_seat_count": len(lookup),
            "available_seat_count": len(lookup) - blocked,
            "blocked_seat_count": blocked,
            "empty_seat_count": len(lookup) - blocked - demand,
        },
        "weights": {
            "priority_seat_weight": weights["contribution_seat"],
            "activeness_weight": weights["activeness"],
            "category_zone_weight": weights["category_zone"],
        },
        "constraint_config": {
            "enforce_front_fill": True,
            "enforce_middle_fill": True,
            "normalize_penalties": True,
            "normalization_scale": 100,
        },
        "penalty_summary": {
            "unweighted": legacy(q["unweighted"]),
            "normalized": normalized,
            "weighted": weighted,
        },
        "tier_bands": bands,
        "floor_plan": {
            "row_count": request["layout"]["row_count"],
            "seats_per_row": request["layout"]["seats_per_row"],
            "aisle_after_position": request["layout"]["aisle_after_position"],
            "total_seats": len(lookup),
            "rows": rows,
        },
        "assignments": assignments,
        "empty_seat_ids": [
            s for s in lookup if s not in seat_owner and not lookup[s]["is_blocked"]
        ],
        "excluded_participants": [
            {"participant_id": p["participant_id"], "reason": p["registration_status"]}
            for p in request["participants"]
            if p not in ps
        ],
        "unassigned_participants": [],
        "hard_constraint_validation": {
            "all_constraints_satisfied": True,
            "duplicate_seat_count": 0,
            "unassigned_count": 0,
        },
    }
