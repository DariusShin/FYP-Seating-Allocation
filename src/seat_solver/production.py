"""Production CP-SAT engine: shared rows, ranked preferences and protected repair."""

from __future__ import annotations

import copy
import time
import uuid
from datetime import datetime, timezone

from ortools.sat.python import cp_model

from seat_solver.policy import (
    TIERS,
    DomainError,
    mapped_weights,
    policy,
    validate_request,
)
from seat_solver.production_scoring import (
    baseline_maps,
    candidate_cost,
    changed_ids,
    eligible,
    movement,
    options,
    packing_pairs,
    quality,
)
from seat_solver.production_validator import validate_placements


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


def repair_scopes(request, baseline):
    old, oldps = baseline_maps(baseline)
    changes = changed_ids(request, baseline)
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    oldlookup = {s["seat_id"]: s for s in baseline["source_request"]["layout"]["seats"]}
    affected_seats = {sid for pid in changes for sid in old.get(pid, ())}
    affected_rows = {oldlookup[s]["row_number"] for s in affected_seats}
    last = max(
        (oldlookup[s]["row_number"] for ids in old.values() for s in ids), default=1
    )
    if not affected_rows:
        affected_rows = {last}
    newps = {p["participant_id"]: p for p in request["participants"]}
    tiers = {
        p["contribution_tier"]
        for pid in changes
        for p in (oldps.get(pid), newps.get(pid))
        if p
    }
    tier_rows = {
        oldlookup[s]["row_number"]
        for pid, ids in old.items()
        if oldps[pid]["contribution_tier"] in tiers
        for s in ids
    } | affected_rows
    neighbouring = {r + d for r in tier_rows for d in (-1, 0, 1)}
    return [
        (0, affected_seats, set()),
        (1, None, affected_rows),
        (2, None, tier_rows),
        (3, None, neighbouring),
        (4, None, set(range(1, request["layout"]["row_count"] + 1))),
    ]


def build(request, cfg, baseline=None, scope=None):
    model = cp_model.CpModel()
    ps = eligible(request)
    layout = request["layout"]
    changes = changed_ids(request, baseline)
    old, _ = baseline_maps(baseline)
    vars_by = {}
    option_by = {}
    rowexpr = {}
    costexpr = []
    moveexpr = []
    distexpr = []
    occupants = {s["seat_id"]: [] for s in layout["seats"]}
    canon = {}
    frozen = []
    allowed = initial_rows(request) if not baseline else None
    for p in ps:
        pid = p["participant_id"]
        opts = options(request, p)
        if allowed is not None:
            opts = [o for o in opts if o[0]["row_number"] in allowed[pid]]
        if scope:
            number, direct, rows = scope
            old_rows = {
                s["row_number"]
                for s in baseline["source_request"]["layout"]["seats"]
                if s["seat_id"] in old.get(pid, ())
            }
            freeze = pid not in changes and (number == 0 or not old_rows & rows)
            if freeze:
                frozen.append(pid)
                opts = [
                    o
                    for o in opts
                    if {s["seat_id"] for s in o} == set(old.get(pid, ()))
                ]
            elif number == 0:
                opts = [o for o in opts if all(s["seat_id"] in direct for s in o)]
            else:
                opts = [o for o in opts if o[0]["row_number"] in rows]
        opts = sorted(opts, key=lambda o: tuple(s["seat_id"] for s in o))
        vs = []
        option_by[pid] = opts
        for j, o in enumerate(opts):
            v = model.NewBoolVar(f"assign[{pid},{j}]")
            vs.append(v)
            for s in o:
                occupants[s["seat_id"]].append(v)
            costexpr.append(v * candidate_cost(request, cfg, p, o)["weighted"]["total"])
            m, d = movement(p, o, baseline, request)
            moveexpr.append(v * m * (pid not in changes))
            distexpr.append(v * d)
        model.AddExactlyOne(vs)
        vars_by[pid] = vs
        rowexpr[pid] = sum(v * o[0]["row_number"] for v, o in zip(vs, opts))
        canon[pid] = sum(v * j for j, v in enumerate(vs))
    occ = {sid: sum(vs) for sid, vs in occupants.items()}
    for vs in occupants.values():
        if len(vs) > 1:
            model.AddAtMostOne(vs)
    # Adjacent levels imply all cross-tier and within-tier contribution comparisons.
    levels = {}
    for p in ps:
        levels.setdefault(
            (TIERS.index(p["contribution_tier"]), -p["contribution_amount_rm"]), []
        ).append(rowexpr[p["participant_id"]])
    ordered = sorted(levels)
    for i, (a, b) in enumerate(zip(ordered, ordered[1:])):
        boundary = model.NewIntVar(1, layout["row_count"], f"boundary[{i}]")
        for expr in levels[a]:
            model.Add(expr <= boundary)
        for expr in levels[b]:
            model.Add(expr >= boundary)
    gaps = []
    for i, (inner, outer) in enumerate(packing_pairs(layout)):
        if not baseline:
            model.Add(occ[outer] <= occ[inner])
        elif cfg["repair_local_packing"]:
            gap = model.NewBoolVar(f"gap[{i}]")
            model.Add(gap >= occ[outer] - occ[inner])
            model.Add(gap <= occ[outer])
            model.Add(gap <= 1 - occ[inner])
            gaps.append(gap)
    if not baseline:
        demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in ps)
        for r in range(1, layout["row_count"] + 1):
            seats = [
                s
                for s in layout["seats"]
                if s["row_number"] == r and not s["is_blocked"]
            ]
            target = min(demand, len(seats))
            demand -= target
            model.Add(sum(occ[s["seat_id"]] for s in seats) == target)
    stages = []
    if baseline:
        stages.extend(
            [
                ("unaffected_moved_units", sum(moveexpr)),
                ("distance_doubled", sum(distexpr)),
            ]
        )
        if cfg["repair_local_packing"]:
            stages.append(("local_packing", sum(gaps)))
    stages.append(("weighted_preferences", sum(costexpr)))
    return model, vars_by, option_by, stages, canon, frozen


def solve(request, baseline=None):
    started = time.perf_counter()
    timing = {}
    try:
        request = validate_request(request)
        cfg = policy()
        timing["input_validation"] = time.perf_counter() - started
        repair = request["generation_mode"] == "REPAIR_PUBLISHED"
        if repair:
            if (
                not baseline
                or baseline["event_id"] != request["event_id"]
                or baseline["plan_version_id"] != request["baseline_plan_version_id"]
            ):
                raise DomainError(
                    "STALE_BASELINE",
                    "Published baseline is required and must match the event/version",
                )
            if baseline["policy_version_id"] != request["policy_version_id"]:
                raise DomainError(
                    "INVALID_INPUT",
                    "Repair across policy versions requires explicit full regeneration",
                )
            oldlayout = baseline["source_request"]["layout"]
            newlayout = request["layout"]
            if (
                oldlayout["row_count"],
                oldlayout["seats_per_row"],
                oldlayout["aisle_after_position"],
            ) != (
                newlayout["row_count"],
                newlayout["seats_per_row"],
                newlayout["aisle_after_position"],
            ):
                raise DomainError(
                    "INVALID_INPUT",
                    "Repair cannot reinterpret physical geometry; use full regeneration",
                )

            def geom(l):
                return {
                    s["seat_id"]: (s["row_number"], s["physical_position"])
                    for s in l["seats"]
                }

            if geom(oldlayout) != geom(newlayout):
                raise DomainError(
                    "INVALID_INPUT",
                    "Repair seat identities have changed physical meaning",
                )
        elif baseline is not None:
            raise DomainError(
                "INVALID_INPUT", "Initial/regeneration cannot use a movement baseline"
            )
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
        scopes = repair_scopes(request, baseline) if repair else [None]
        attempts = []
        for scope in scopes:
            t = time.perf_counter()
            model, variables, opts, stages, canon, frozen = build(
                request, cfg, baseline, scope
            )
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
                attempts.append(
                    {"scope": scope[0] if scope else None, "status": status_name}
                )
                if status_name == "INFEASIBLE" and scope and scope[0] < 4:
                    continue
                return error(
                    status_name
                    if status_name in ("INFEASIBLE", "MODEL_INVALID")
                    else "SOLVER_UNKNOWN",
                    "No valid allocation established under the current compulsory rules. Check accessibility, pairing, contribution order and initial packing.",
                    {"attempts": attempts, "proof": proof},
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
                baseline,
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
                "optimality_scope": "restricted_repair"
                if repair
                else "full_initial_model",
                "repair_scope": scope[0] if scope else None,
                "scope_attempts": attempts,
                "frozen_units": frozen,
                "changed_units": sorted(changed_ids(request, baseline))
                if repair
                else [],
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
            result = format_result(request, solutions, stats, baseline)
            return result
        return error("INFEASIBLE", "No repair scope satisfies compulsory rules")
    except DomainError as exc:
        return error(exc.code, str(exc), exc.details)


def format_result(request, placements, stats, baseline=None):
    cfg = policy()
    q = quality(request, cfg, placements, baseline)
    weights = mapped_weights(request["preferences"])
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    assignments = []
    old, _ = baseline_maps(baseline)
    seat_owner = {}
    display = {}

    def legacy(c):
        return {
            "priority_seat": c["contribution_seat"],
            "category_zone": c["category_zone"],
            "activeness": c["activeness"],
            "movement": 0,
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
                "previous_seat_ids": list(old.get(pid, ())),
                "moved": set(old[pid]) != set(placements[pid]) if pid in old else None,
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
        "baseline_snapshot": (
            {
                k: copy.deepcopy(baseline[k])
                for k in (
                    "plan_version_id",
                    "event_id",
                    "policy_version_id",
                    "source_request",
                    "assignments",
                )
            }
            if baseline
            else None
        ),
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
            "movement_weight": 0,
        },
        "constraint_config": {
            "enforce_front_fill": baseline is None,
            "enforce_middle_fill": baseline is None,
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
