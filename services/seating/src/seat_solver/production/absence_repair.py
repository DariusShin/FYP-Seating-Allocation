"""Absence repair of a saved working map.

The deterministic stage fills the absence gap without any search: the
farthest-back registration that may legally and fairly take the earliest free
seat moves into it, and the seat it releases becomes the next hole, so the gap
migrates to the packing tail. Registrations restored to present while docked
take part as cost-free movers and are seated on the tail of their tier band.
When the gap shape, pairing, accessibility or fairness gate defeats that pass,
a progressively expanded CP-SAT repair of the saved working map takes over.
The generation solver is never called. Registrations outside the current row
neighbourhood remain constants in the shared hard-rule model. Optimality is
scoped to the first feasible neighbourhood, not claimed for the entire hall.
"""

import copy
import time

from ortools.sat.python import cp_model

from seat_solver.production.policy import TIERS, DomainError, policy
from seat_solver.production.production import build, error, format_result, now
from seat_solver.production.production_scoring import candidate_cost, eligible, options
from seat_solver.production.production_validator import validate_placements
from seat_solver.production.workspace import validate_state


def movement(ids, previous, seats):
    if not ids:
        return 0, 0
    if not previous:
        # Seating a restored registration is always a move; it owns no baseline.
        return 1, 0
    if set(ids) == set(previous):
        return 0, 0

    def centre(bundle, key):
        return 2 * sum(seats[s][key] for s in bundle) // len(bundle)

    return 1, sum(
        abs(centre(ids, k) - centre(previous, k))
        for k in ("row_number", "physical_position")
    )


def shift_forward_solutions(request, people, baseline, absent, state, seats):
    """Deterministic no-overtake repair of gaps and restored registrations.

    Seats are ordered by hall packing order (row-major over priority rank). A
    free seat with an occupied seat behind it is filled by the farthest-back
    registration unit that may legally take it; its released seats become the
    next hole, so the free seats always end as a suffix of the packing order.
    Registrations restored to present while docked are preferred movers: they
    must be seated anyway, so taking a hole costs no extra movement, measured
    against the seats they held before the absence. Any still unseated
    registration takes the farthest-back legal span inside its tier band, or
    the stage declines. Fairness extends C13: a mover may not be seated better
    than any same-tier registration with a strictly higher contribution amount
    that it passes, and C12 confines movers to seats at or behind every better
    tier seated behind the hole. Emperor units move as whole approved pairs
    only. Returns (placements, scope_rows) or None to decline to CP-SAT.
    """
    previous = {
        pid: state["items"][pid].get("previous_seat_ids") or [] for pid in absent
    }
    if any(not ids for ids in previous.values()):
        return None
    cells = sorted(
        (s for s in request["layout"]["seats"] if not s["is_blocked"]),
        key=lambda s: (s["row_number"], s["priority_rank"]),
    )
    index_of = {s["seat_id"]: i for i, s in enumerate(cells)}
    gap = set()
    for ids in previous.values():
        if any(s not in index_of for s in ids):
            return None
        gap.update(index_of[s] for s in ids)
    meta = {}
    docked = []
    for p in people:
        pid = p["participant_id"]
        info = {
            "tier": p["contribution_tier"],
            "amount": p["contribution_amount_rm"],
            "emperor": p["contribution_tier"] == "EMPEROR",
            "accessible": p["requires_accessible_seat"],
        }
        if baseline[pid]:
            home = [index_of.get(s) for s in baseline[pid]]
            if not home or any(i is None for i in home):
                return None
            meta[pid] = {**info, "origin": frozenset(home), "span": set(home)}
        else:
            old = [
                index_of[s]
                for s in state["items"][pid].get("previous_seat_ids") or []
                if s in index_of
            ]
            docked.append({**info, "pid": pid, "origin": old})
    docked.sort(key=lambda d: (TIERS.index(d["tier"]), d["pid"]))
    occupied = set().union(*(m["span"] for m in meta.values())) if meta else set()
    last = max(occupied, default=-1)
    free = set(range(len(cells))) - occupied
    if not any(i < last for i in free) and not docked:
        return None
    if any(i < last and i not in gap for i in free):
        return None
    approved = {tuple(sorted(pair)) for pair in request["layout"]["approved_pairs"]}
    tier_rank = {tier: i for i, tier in enumerate(TIERS)}

    def row_of(span):
        return cells[min(span)]["row_number"]

    def overtakes(target, origin, tier, amount):
        for m in meta.values():
            if m["tier"] != tier or m["amount"] <= amount:
                continue
            span = m["span"]
            if target < min(span) and max(span) < origin:
                return False
        return True

    def c13_fits(tier, amount, row):
        for m in meta.values():
            if m["tier"] != tier:
                continue
            r = row_of(m["span"])
            if r < row and m["amount"] < amount:
                return False
            if r > row and m["amount"] > amount:
                return False
        return True

    def gate(d, target):
        return overtakes(
            target, min(d["origin"]) if d["origin"] else 0, d["tier"], d["amount"]
        ) and c13_fits(d["tier"], d["amount"], row_of([target]))

    def occupied_now():
        return set().union(*(m["span"] for m in meta.values())) if meta else set()

    def take(mover, span):
        if isinstance(mover, dict):
            meta[mover["pid"]] = {
                **mover,
                "origin": frozenset(mover["origin"]),
                "span": set(span),
            }
            docked.remove(mover)
        else:
            meta[mover]["span"] = set(span)

    while True:
        occ = occupied_now()
        last_now = max(occ, default=-1)
        holes = sorted(i for i in set(range(len(cells))) - occ if i < last_now)
        if not holes:
            break
        a = holes[0]
        behind = [pid for pid, m in meta.items() if min(m["span"]) > a]
        floor_tier = min((tier_rank[meta[pid]["tier"]] for pid in behind), default=0)
        mover = None
        span = None
        if a + 1 < len(cells) and a + 1 not in occ:
            key = tuple(
                sorted(
                    (cells[a]["physical_position"], cells[a + 1]["physical_position"])
                )
            )
            if key in approved:
                pair_accessible = (
                    cells[a]["is_accessible"] and cells[a + 1]["is_accessible"]
                )
                mover = next(
                    (
                        d
                        for d in docked
                        if d["emperor"]
                        and (not d["accessible"] or pair_accessible)
                        and tier_rank[d["tier"]] <= floor_tier
                        and gate(d, a)
                    ),
                    None,
                )
                if mover is None:
                    candidates = [
                        pid
                        for pid in behind
                        if meta[pid]["emperor"]
                        and (not meta[pid]["accessible"] or pair_accessible)
                        and tier_rank[meta[pid]["tier"]] <= floor_tier
                        and overtakes(
                            a,
                            min(meta[pid]["span"]),
                            meta[pid]["tier"],
                            meta[pid]["amount"],
                        )
                    ]
                    if candidates:
                        mover = max(candidates, key=lambda pid: min(meta[pid]["span"]))
                if mover is not None:
                    span = (a, a + 1)
        if mover is None:
            mover = next(
                (
                    d
                    for d in docked
                    if not d["emperor"]
                    and (not d["accessible"] or cells[a]["is_accessible"])
                    and tier_rank[d["tier"]] <= floor_tier
                    and gate(d, a)
                ),
                None,
            )
            if mover is None:
                candidates = [
                    pid
                    for pid in behind
                    if not meta[pid]["emperor"]
                    and (not meta[pid]["accessible"] or cells[a]["is_accessible"])
                    and tier_rank[meta[pid]["tier"]] <= floor_tier
                    and overtakes(
                        a,
                        min(meta[pid]["span"]),
                        meta[pid]["tier"],
                        meta[pid]["amount"],
                    )
                ]
                if not candidates:
                    return None
                mover = max(candidates, key=lambda pid: min(meta[pid]["span"]))
            span = (a,)
        take(mover, span)
    for d in list(docked):
        best = None
        for a in range(len(cells)):
            span = None
            if d["emperor"]:
                if a + 1 < len(cells) and a + 1 not in occupied_now():
                    key = tuple(
                        sorted(
                            (
                                cells[a]["physical_position"],
                                cells[a + 1]["physical_position"],
                            )
                        )
                    )
                    if key in approved and (
                        not d["accessible"]
                        or (cells[a]["is_accessible"] and cells[a + 1]["is_accessible"])
                    ):
                        span = (a, a + 1)
            elif a not in occupied_now() and (
                not d["accessible"] or cells[a]["is_accessible"]
            ):
                span = (a,)
            if span is None:
                continue
            occ = occupied_now()
            if any(
                tier_rank[m["tier"]] < tier_rank[d["tier"]]
                and max(m["span"]) >= span[0]
                for m in meta.values()
            ):
                continue
            if any(
                tier_rank[m["tier"]] > tier_rank[d["tier"]]
                and min(m["span"]) <= span[-1]
                for m in meta.values()
            ):
                continue
            if not gate(d, span[0]):
                continue
            # The earliest legal span keeps every free seat behind the seated
            # region, so the placement itself never opens a new packing hole.
            if best is None or span[0] < best[0]:
                best = span
        if best is None:
            return None
        take(d, best)
    solutions = {}
    for p in people:
        pid = p["participant_id"]
        m = meta.get(pid)
        if m is None:
            solutions[pid] = list(baseline[pid])
        elif baseline[pid] and m["span"] == m["origin"]:
            solutions[pid] = list(baseline[pid])
        else:
            solutions[pid] = [cells[i]["seat_id"] for i in sorted(m["span"])]
    audit = validate_placements(
        request,
        [{"participant_id": pid, "seat_ids": ids} for pid, ids in solutions.items()],
    )
    if not audit["passed"]:
        return None
    moved_rows = {
        cells[i]["row_number"]
        for m in meta.values()
        if m["span"] != m["origin"]
        for i in m["span"] | set(m["origin"])
    }
    return solutions, sorted(moved_rows | {cells[i]["row_number"] for i in gap})


def repair(plan, state, preferences=None):
    started = time.perf_counter()
    request = validate_state(plan, state)
    request["generation_mode"] = "REPAIR_ABSENCE"
    if preferences is not None:
        request["preferences"] = copy.deepcopy(preferences)
    from seat_solver.production.policy import validate_request

    validate_request(request)
    seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
    people = eligible(request)
    baseline = {
        p["participant_id"]: state["items"][p["participant_id"]]["seat_ids"]
        for p in people
    }
    docked_present = [
        p["participant_id"] for p in people if not baseline[p["participant_id"]]
    ]
    if any(state["items"][pid].get("dock_reason") for pid in docked_present):
        raise DomainError(
            "INVALID_INPUT",
            "Seat present registrations from the temporary dock before absence repair",
        )
    absent = [
        pid
        for pid, item in state["items"].items()
        if item.get("attendance_status", "PRESENT") == "ABSENT"
    ]
    if not absent:
        raise DomainError(
            "INVALID_INPUT", "Absence repair requires an absent registration"
        )
    seeds = {
        seats[s]["row_number"]
        for pid in absent
        for s in state["items"][pid]["previous_seat_ids"]
    }
    for pid in docked_present:
        seeds.update(
            seats[s]["row_number"]
            for s in state["items"][pid].get("previous_seat_ids") or []
        )
    seeds = seeds or {1}
    deadline = started + request["solver"]["max_time_seconds"]
    attempts = []
    solutions = baseline
    audit = validate_placements(
        request,
        [{"participant_id": pid, "seat_ids": ids} for pid, ids in baseline.items()],
    )
    proof = []
    scope = []
    variable_count = 0
    integer_count = constraint_count = conflicts = branches = 0
    business_optimal = True
    stopped_stage = None
    fast = None
    if not audit["passed"]:
        fast = shift_forward_solutions(request, people, baseline, absent, state, seats)
    if fast is not None:
        solutions, fast_rows = fast
        scope = fast_rows
        attempts.append(
            {"rows": fast_rows, "status": "OPTIMAL", "engine": "shift-forward"}
        )
    elif not audit["passed"]:
        solutions = None
        for radius in range(request["layout"]["row_count"]):
            scope = sorted(
                r
                for r in range(1, request["layout"]["row_count"] + 1)
                if min(abs(r - seed) for seed in seeds) <= radius
            )
            domains = {}
            for p in people:
                pid = p["participant_id"]
                if not baseline[pid]:
                    domains[pid] = {
                        tuple(sorted(s["seat_id"] for s in o))
                        for o in options(request, p)
                        if o[0]["row_number"] in scope
                    }
                elif seats[baseline[pid][0]]["row_number"] in scope:
                    domains[pid] = {
                        tuple(sorted(s["seat_id"] for s in o))
                        for o in options(request, p)
                        if o[0]["row_number"] in scope
                    }
                else:
                    domains[pid] = {tuple(sorted(baseline[pid]))}
            model, variables, opts, preference_stages, _ = build(
                request, policy(), domains
            )
            variable_count = sum(
                not isinstance(v, int) for vs in variables.values() for v in vs
            )
            integer_count = len(model.Proto().variables) - variable_count
            constraint_count = len(model.Proto().constraints)
            moved = distance = 0
            for pid, vs in variables.items():
                for v, option in zip(vs, opts[pid]):
                    m, d = movement(
                        [s["seat_id"] for s in option], baseline[pid], seats
                    )
                    moved += v * m
                    distance += v * d
            proof = []
            infeasible = False
            for name, expr in [
                ("moved_registrations", moved),
                ("movement_distance_doubled", distance),
                *preference_stages,
            ]:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    if solutions is None:
                        return error(
                            "REPAIR_TIMEOUT",
                            "Repair time limit reached before finding a valid seating plan; saved and published maps are unchanged",
                            {"attempts": attempts},
                        )
                    business_optimal = False
                    stopped_stage = name
                    break
                engine = cp_model.CpSolver()
                engine.parameters.max_time_in_seconds = remaining
                engine.parameters.num_search_workers = request["solver"][
                    "num_search_workers"
                ]
                engine.parameters.random_seed = request["solver"]["random_seed"]
                model.Minimize(expr)
                status = engine.Solve(model)
                if status == cp_model.INFEASIBLE and solutions is None:
                    infeasible = True
                    attempts.append({"rows": scope, "status": "INFEASIBLE"})
                    break
                if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    if status == cp_model.MODEL_INVALID:
                        return error(
                            "REPAIR_MODEL_INVALID",
                            "Repair model could not be solved",
                            {"attempts": attempts, "stage": name},
                        )
                    if solutions is None:
                        return error(
                            "REPAIR_NO_SOLUTION",
                            "Repair search ended before finding a valid seating plan; try again",
                            {"attempts": attempts, "stage": name},
                        )
                    # A later stage may time out without an incumbent of its own.
                    # Keep the valid placement captured by the preceding stage.
                    business_optimal = False
                    stopped_stage = name
                    break
                solutions = {
                    pid: [
                        s["seat_id"]
                        for v, option in zip(variables[pid], opts[pid])
                        if engine.Value(v)
                        for s in option
                    ]
                    for pid in variables
                }
                conflicts, branches = engine.NumConflicts(), engine.NumBranches()
                value = int(engine.Value(expr))
                bound = engine.BestObjectiveBound()
                proof.append(
                    {
                        "stage": name,
                        "status": "OPTIMAL"
                        if status == cp_model.OPTIMAL
                        else "FEASIBLE",
                        "value": value,
                        "best_bound": bound,
                        "absolute_gap": max(0, value - bound),
                    }
                )
                if status == cp_model.FEASIBLE:
                    # Movement remains the active objective throughout this search.
                    # Return the best valid incumbent without requiring a proof or
                    # fixing its unproven score to optimize lower-priority terms.
                    business_optimal = False
                    stopped_stage = name
                    break
                model.Add(expr == value)
            if infeasible:
                continue
            attempts.append(
                {"rows": scope, "status": "OPTIMAL" if business_optimal else "FEASIBLE"}
            )
            break
    if solutions is None:
        return error(
            "REPAIR_INFEASIBLE",
            "No repair satisfies compulsory seating rules, even after expanding across the hall",
            {"attempts": attempts},
        )
    audit = validate_placements(
        request,
        [{"participant_id": pid, "seat_ids": ids} for pid, ids in solutions.items()],
    )
    if not audit["passed"]:
        return error(
            "OUTPUT_VALIDATION_FAILED", "Independent repair validation failed", audit
        )
    engine_name = (
        "Deterministic shift-forward repair"
        if fast is not None
        else "Google OR-Tools CP-SAT incremental repair"
    )
    # Preference delta over the population seated both before and after, so
    # restored registrations without a baseline never skew the comparison.
    seated_before = {pid: ids for pid, ids in baseline.items() if ids}

    def weighted_total(placements):
        return sum(
            candidate_cost(
                request,
                policy(),
                p,
                [seats[s] for s in placements[p["participant_id"]]],
            )["weighted"]["total"]
            for p in people
            if p["participant_id"] in placements
        )

    preference_before = weighted_total(seated_before)
    preference_after = weighted_total({pid: solutions[pid] for pid in seated_before})
    changes = [
        {
            "participant_id": pid,
            "from_seat_ids": baseline[pid],
            "to_seat_ids": ids,
            "distance_doubled": movement(ids, baseline[pid], seats)[1],
        }
        for pid, ids in solutions.items()
        if set(ids) != set(baseline[pid])
    ]
    stats = {
        "engine": engine_name,
        "status": "OPTIMAL" if business_optimal else "FEASIBLE",
        "proof": proof,
        "canonicalization_complete": False,
        "optimality_scope": "repair_neighbourhood",
        "wall_time_seconds": time.perf_counter() - started,
        "num_boolean_variables": variable_count,
        "num_integer_variables": integer_count,
        "num_constraints": constraint_count,
        "num_conflicts": conflicts,
        "num_branches": branches,
    }
    result = format_result(request, solutions, stats)
    result["repair_baseline"] = copy.deepcopy(baseline)
    result["repair_summary"] = {
        "baseline_plan_version_id": plan["plan_version_id"],
        "absent_registration_ids": absent,
        "moved_registrations": len(changes),
        "moved_physical_seats": sum(len(c["to_seat_ids"]) for c in changes),
        "distance_doubled": sum(c["distance_doubled"] for c in changes),
        "changes": changes,
        "attempts": attempts,
        "scope_rows": scope,
        "optimality_scope": "repair_neighbourhood",
        "optimality_proven": business_optimal,
        "stopped_stage": stopped_stage,
        "engine": engine_name,
        "preference_cost_before": preference_before,
        "preference_cost_after": preference_after,
    }
    result["operations"] = copy.deepcopy(state["items"])
    for pid, ids in solutions.items():
        item = result["operations"][pid]
        if set(ids) != set(item["seat_ids"]):
            if item["seat_ids"]:
                item["previous_seat_ids"] = item["seat_ids"]
            item["changed_at"] = now()
        item["seat_ids"] = ids
        item["dock_reason"] = ""
    from seat_solver.production.workspace import apply_display

    apply_display(result, result["operations"])
    return result
