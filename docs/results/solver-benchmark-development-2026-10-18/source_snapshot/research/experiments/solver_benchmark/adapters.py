"""Three full-policy adapters with a common compact integer objective."""

import math
import time

from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from seat_solver.production.policy import TIERS
from seat_solver.production.production import build
from .common import compatible


def build_adapter(problem, method, seconds, seed):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Search allowance must be positive and finite")
    return {"cp_sat": cp_adapter, "scip": scip_adapter, "greedy": greedy_adapter}[method](problem, seconds, seed)


def cp_adapter(p, seconds, seed):
    domains = {pid: {tuple(sorted(b.ids)) for b in bs} for pid, bs in p.bundles.items()}
    model, variables, options, _, _ = build(p.request, p.cfg, domains=domains)
    for pid, bs in p.bundles.items():
        if [tuple(s["seat_id"] for s in o) for o in options[pid]] != [b.ids for b in bs]:
            raise ValueError("Production builder domains differ from common domains")
    model.Minimize(sum(v * b.cost for pid, vs in variables.items() for v, b in zip(vs, p.bundles[pid])))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    def run():
        status = solver.Solve(model)
        feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        chosen = {pid: next(j for j, v in enumerate(vs) if solver.Value(v))
                  for pid, vs in variables.items()} if feasible else None
        return {"solver_status": solver.StatusName(status), "chosen": chosen,
                "reported_objective": solver.ObjectiveValue() if feasible else None,
                "best_bound": solver.BestObjectiveBound() if feasible else None,
                "backend": "OR-Tools CP-SAT", "solver_wall_seconds": solver.WallTime(),
                "branches": solver.NumBranches(), "conflicts": solver.NumConflicts()}
    return run


def scip_adapter(p, seconds, seed):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("SCIP backend unavailable; no substitute solver is allowed")
    if not solver.SetNumThreads(1):
        raise RuntimeError("SCIP rejected single-thread setting")
    if not solver.SetSolverSpecificParametersAsString(f"randomization/randomseedshift = {seed}\nparallel/maxnthreads = 1"):
        raise RuntimeError("SCIP rejected reproducibility settings")
    solver.SetTimeLimit(max(1, round(seconds * 1000)))
    xs = {pid: [solver.BoolVar(f"assign[{pid},{j}]") for j in range(len(bs))] for pid, bs in p.bundles.items()}
    occupancy = {s["seat_id"]: [] for s in p.request["layout"]["seats"]}
    rows, best, worst = {}, {}, {}
    for pid, vs in xs.items():
        solver.Add(solver.Sum(vs) == 1)
        bs = p.bundles[pid]
        rows[pid] = solver.Sum(v * b.row for v, b in zip(vs, bs))
        best[pid] = solver.Sum(v * b.best for v, b in zip(vs, bs))
        worst[pid] = solver.Sum(v * b.worst for v, b in zip(vs, bs))
        for v, b in zip(vs, bs):
            for sid in b.ids:
                occupancy[sid].append(v)
    occ = {sid: solver.Sum(vs) for sid, vs in occupancy.items()}
    for expr in occ.values():
        solver.Add(expr <= 1)
    for tier in TIERS:
        levels = {}
        for pid, person in p.people.items():
            if person["contribution_tier"] == tier:
                levels.setdefault(-person["contribution_amount_rm"], []).append(pid)
        ordered = sorted(levels)
        for a, b in zip(ordered, ordered[1:]):
            boundary = solver.IntVar(1, p.request["layout"]["row_count"], f"row_boundary[{tier},{a}]")
            for pid in levels[a]:
                solver.Add(rows[pid] <= boundary)
            for pid in levels[b]:
                solver.Add(rows[pid] >= boundary)
    groups = [[pid for pid, person in p.people.items() if person["contribution_tier"] == tier] for tier in TIERS]
    groups = [g for g in groups if g]
    for i, (higher, lower) in enumerate(zip(groups, groups[1:])):
        boundary = solver.IntVar(1, p.request["layout"]["row_count"] * p.request["layout"]["seats_per_row"], f"tier_boundary[{i}]")
        for pid in higher:
            solver.Add(worst[pid] <= boundary)
        for pid in lower:
            solver.Add(best[pid] >= boundary + 1)
    for inner, outer in p.packing:
        solver.Add(occ[outer] <= occ[inner])
    for row, target in p.targets.items():
        solver.Add(solver.Sum(occ[s["seat_id"]] for s in p.request["layout"]["seats"]
                              if s["row_number"] == row and not s["is_blocked"]) == target)
    solver.Minimize(solver.Sum(v * b.cost for pid, vs in xs.items() for v, b in zip(vs, p.bundles[pid])))
    names = {solver.OPTIMAL: "OPTIMAL", solver.FEASIBLE: "FEASIBLE", solver.INFEASIBLE: "INFEASIBLE",
             solver.UNBOUNDED: "UNBOUNDED", solver.ABNORMAL: "ABNORMAL", solver.NOT_SOLVED: "UNKNOWN",
             solver.MODEL_INVALID: "MODEL_INVALID"}
    def run():
        status = solver.Solve()
        feasible = status in (solver.OPTIMAL, solver.FEASIBLE)
        chosen = None
        if feasible:
            chosen = {}
            for pid, vs in xs.items():
                values = [v.solution_value() for v in vs]
                if any(abs(v - round(v)) > 1e-6 for v in values) or sum(v > .5 for v in values) != 1:
                    raise ValueError("Nonintegral or incomplete SCIP extraction")
                chosen[pid] = next(j for j, v in enumerate(values) if v > .5)
        bound = solver.Objective().BestBound() if feasible else None
        return {"solver_status": names.get(status, f"UNKNOWN_{status}"), "chosen": chosen,
                "reported_objective": solver.Objective().Value() if feasible else None,
                "best_bound": bound if bound is not None and math.isfinite(bound) else None,
                "backend": solver.SolverVersion(), "nodes": solver.nodes()}
    return run


def greedy_adapter(p, seconds, seed):
    """Fail-first, cost-ordered construction; no undo, repairs or exact solver calls."""
    def run():
        deadline = time.perf_counter() + seconds
        chosen = {}
        occupied = set()
        used = dict.fromkeys(p.targets, 0)
        domains = {pid: list(range(len(bs))) for pid, bs in p.bundles.items()}
        attempted = 0
        def check_time():
            if time.perf_counter() >= deadline:
                raise TimeoutError
        def forward(pid, j):
            check_time()
            candidate = p.bundles[pid][j]
            remaining = {r: p.targets[r] - used[r] - (len(candidate.ids) if candidate.row == r else 0)
                         for r in p.targets}
            if min(remaining.values(), default=0) < 0:
                return None
            next_domains = {}
            support = set()
            forced, possible = dict.fromkeys(p.targets, 0), dict.fromkeys(p.targets, 0)
            for qid, js in domains.items():
                check_time()
                if qid == pid:
                    continue
                legal = [k for k in js if len(p.bundles[qid][k].ids) <= remaining[p.bundles[qid][k].row]
                         and compatible(p.people[pid], candidate, p.people[qid], p.bundles[qid][k])]
                if not legal:
                    return None
                next_domains[qid] = legal
                reachable = {p.bundles[qid][k].row for k in legal}
                size = len(p.bundles[qid][legal[0]].ids)
                for row in reachable:
                    possible[row] += size
                if len(reachable) == 1:
                    forced[next(iter(reachable))] += size
                for k in legal:
                    support.update(p.bundles[qid][k].ids)
            if any(forced[r] > remaining[r] or possible[r] < remaining[r] for r in remaining):
                return None
            taken = occupied | set(candidate.ids)
            if any(outer in taken and inner not in taken and inner not in support for inner, outer in p.packing):
                return None
            # Necessary union-capacity check: overlapping legal options are not counted as distinct capacity.
            for row, required in remaining.items():
                available = {sid for qid, js in next_domains.items() for k in js
                             if p.bundles[qid][k].row == row for sid in p.bundles[qid][k].ids}
                if len(available) < required:
                    return None
            return next_domains
        status = "FEASIBLE"
        try:
            if p.targets.get(0, 0):
                status = "CONSTRUCTION_FAILED"
            else:
                while domains:
                    check_time()
                    pid = min(domains, key=lambda key: (len(domains[key]), key))
                    accepted = False
                    for j in sorted(domains[pid], key=lambda k: (p.bundles[pid][k].cost, p.bundles[pid][k].ids)):
                        attempted += 1
                        after = forward(pid, j)
                        if after is None:
                            continue
                        chosen[pid] = j
                        bundle = p.bundles[pid][j]
                        used[bundle.row] += len(bundle.ids)
                        occupied.update(bundle.ids)
                        domains = after
                        accepted = True
                        break
                    if not accepted:
                        status = "CONSTRUCTION_FAILED"
                        break
        except TimeoutError:
            status = "TIME_LIMIT"
        return {"solver_status": status, "chosen": chosen if status == "FEASIBLE" else None,
                "best_bound": None, "reported_objective": None, "backend": "deterministic forward-checking greedy v1",
                "candidates_tested": attempted, "committed_registrations": len(chosen)}
    return run
