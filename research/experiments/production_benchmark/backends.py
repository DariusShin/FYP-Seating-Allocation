"""Instrumented production encodings for one weighted solve per request."""

from __future__ import annotations

from contextlib import contextmanager
import ctypes
import math
import os
from pathlib import Path
import re
import sys

from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from seat_solver.production.policy import TIERS
from seat_solver.production.production import build, initial_rows
from seat_solver.production.production_scoring import candidate_cost, eligible, options, packing_pairs

TOLERANCE = 1e-6


def flush_native():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (ValueError, AttributeError):
            pass
    try:
        ctypes.CDLL("msvcrt" if os.name == "nt" else None).fflush(None)
    except (AttributeError, OSError):
        pass


@contextmanager
def native_log(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flush_native()
    descriptors = (os.dup(1), os.dup(2))
    try:
        with path.open("wb") as stream:
            os.dup2(stream.fileno(), 1)
            os.dup2(stream.fileno(), 2)
            try:
                yield
            finally:
                flush_native()
    finally:
        os.dup2(descriptors[0], 1)
        os.dup2(descriptors[1], 2)
        for fd in descriptors:
            os.close(fd)


def parse_scip_log(text):
    statuses = re.findall(r"SCIP Status\s*:\s*(.+)", text)
    launched = sorted(set(re.findall(r"starting solve in concurrent solver '([^']+)'", text)))
    return dict(native_termination=statuses[-1].strip() if statuses else None,
                concurrent_solver_ids=launched, observed_concurrent_solvers=len(launched),
                gap_limit_reached=bool(re.search(r"gap limit", statuses[-1] if statuses else "", re.I)))


def proof_established(status, value, bound, native=None):
    return (status == "OPTIMAL" and value is not None and bound is not None
            and math.isfinite(bound) and abs(value - bound) <= TOLERANCE
            and not (native or {}).get("gap_limit_reached", False))


class CPSAT:
    name = "cp_sat"

    def __init__(self, request, cfg):
        self.model, self.variables, self.options, stages, self.canonical = build(request, cfg)
        self.weighted = stages[0][1]
        self.seed = request["solver"]["random_seed"]
        self.engine = None

    def configure(self, expression, seconds, workers):
        self.model.Minimize(expression)
        self.engine = cp_model.CpSolver()
        self.engine.parameters.max_time_in_seconds = seconds
        self.engine.parameters.num_search_workers = workers
        self.engine.parameters.random_seed = self.seed
        self.engine.parameters.absolute_gap_limit = 0
        self.engine.parameters.relative_gap_limit = 0
        self.engine.parameters.log_search_progress = True
        self.engine.parameters.log_to_stdout = True

    def run(self, log):
        with native_log(log):
            self.status = self.engine.Solve(self.model)

    def extract(self, expression, log):
        status = self.engine.StatusName(self.status)
        feasible = self.status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        choices = {pid: [s["seat_id"] for j, o in enumerate(self.options[pid])
                         if self.engine.Value(vs[j]) for s in o] for pid, vs in self.variables.items()} if feasible else None
        value = int(self.engine.Value(expression)) if feasible else None
        bound = self.engine.BestObjectiveBound() if feasible else None
        return dict(api_status=status, native_termination=status, choices=choices, value=value, best_bound=bound,
                    proven=proof_established(status, value, bound),
                    absolute_gap=max(0, value - bound) if feasible else None,
                    relative_gap=max(0, value - bound) / max(1, abs(value)) if feasible else None,
                    branches=self.engine.NumBranches(), conflicts=self.engine.NumConflicts())

    def fix(self, expression, value):
        self.model.Add(expression == value)


class SCIP:
    name = "scip"

    def __init__(self, request, cfg):
        self.model = pywraplp.Solver.CreateSolver("SCIP")
        if self.model is None:
            raise RuntimeError("SCIP backend unavailable; substitution is forbidden")
        self.seed = request["solver"]["random_seed"]
        self.options, self.variables, self.canonical = {}, {}, {}
        allowed = initial_rows(request)
        people = eligible(request)
        layout = request["layout"]
        occupancy = {s["seat_id"]: [] for s in layout["seats"]}
        rows, best, worst, costs = {}, {}, {}, []
        for person in people:
            pid = person["participant_id"]
            opts = sorted((o for o in options(request, person) if o[0]["row_number"] in allowed[pid]),
                          key=lambda o: tuple(s["seat_id"] for s in o))
            vs = [self.model.BoolVar(f"assign[{pid},{j}]") for j in range(len(opts))]
            self.options[pid], self.variables[pid] = opts, vs
            self.model.Add(self.model.Sum(vs) == 1)
            rows[pid] = self.model.Sum(v * o[0]["row_number"] for v, o in zip(vs, opts))
            orders = [[(s["row_number"] - 1) * layout["seats_per_row"] + s["priority_rank"] for s in o] for o in opts]
            best[pid] = self.model.Sum(v * min(order) for v, order in zip(vs, orders))
            worst[pid] = self.model.Sum(v * max(order) for v, order in zip(vs, orders))
            self.canonical[pid] = self.model.Sum(j * v for j, v in enumerate(vs))
            for v, option in zip(vs, opts):
                costs.append(v * candidate_cost(request, cfg, person, option)["weighted"]["total"])
                for seat in option:
                    occupancy[seat["seat_id"]].append(v)
        occupied = {sid: self.model.Sum(vs) for sid, vs in occupancy.items()}
        for expression in occupied.values():
            self.model.Add(expression <= 1)
        for tier in TIERS:
            levels = {}
            for person in people:
                if person["contribution_tier"] == tier:
                    levels.setdefault(-person["contribution_amount_rm"], []).append(person["participant_id"])
            ordered = sorted(levels)
            for i, (a, b) in enumerate(zip(ordered, ordered[1:])):
                boundary = self.model.IntVar(1, layout["row_count"], f"row_boundary[{tier},{i}]")
                for pid in levels[a]:
                    self.model.Add(rows[pid] <= boundary)
                for pid in levels[b]:
                    self.model.Add(rows[pid] >= boundary)
        groups = [[p["participant_id"] for p in people if p["contribution_tier"] == tier] for tier in TIERS]
        groups = [g for g in groups if g]
        for i, (higher, lower) in enumerate(zip(groups, groups[1:])):
            boundary = self.model.IntVar(1, layout["row_count"] * layout["seats_per_row"], f"tier_boundary[{i}]")
            for pid in higher:
                self.model.Add(worst[pid] <= boundary)
            for pid in lower:
                self.model.Add(best[pid] >= boundary + 1)
        for inner, outer in packing_pairs(layout):
            self.model.Add(occupied[outer] <= occupied[inner])
        demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in people)
        for row in range(1, layout["row_count"] + 1):
            seats = [s for s in layout["seats"] if s["row_number"] == row and not s["is_blocked"]]
            target = min(demand, len(seats))
            demand -= target
            self.model.Add(self.model.Sum(occupied[s["seat_id"]] for s in seats) == target)
        self.weighted = self.model.Sum(costs)

    def configure(self, expression, seconds, workers):
        if not self.model.SetNumThreads(workers):
            raise RuntimeError(f"SCIP rejected native SetNumThreads({workers})")
        parameters = (f"limits/gap = 0\nlimits/absgap = 0\nrandomization/randomseedshift = {self.seed}\n"
                      f"parallel/minnthreads = {workers}\nparallel/maxnthreads = {workers}\ndisplay/verblevel = 4")
        if not self.model.SetSolverSpecificParametersAsString(parameters):
            raise RuntimeError("SCIP rejected exact proof/thread settings")
        self.model.SetTimeLimit(max(1, int(seconds * 1000)))
        self.model.Minimize(expression)
        self.model.EnableOutput()
        self.parameters = pywraplp.MPSolverParameters()
        self.parameters.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, 0)

    def run(self, log):
        with native_log(log):
            self.status = self.model.Solve(self.parameters)

    def extract(self, expression, log):
        names = {0: "OPTIMAL", 1: "FEASIBLE", 2: "INFEASIBLE", 3: "UNBOUNDED",
                 4: "ABNORMAL", 5: "MODEL_INVALID", 6: "UNKNOWN"}
        status = names.get(self.status, f"STATUS_{self.status}")
        feasible = self.status in (self.model.OPTIMAL, self.model.FEASIBLE)
        choices = None
        if feasible:
            choices = {}
            for pid, variables in self.variables.items():
                values = [v.solution_value() for v in variables]
                if any(not math.isfinite(v) or abs(v - round(v)) > TOLERANCE for v in values) or sum(v > .5 for v in values) != 1:
                    raise ValueError("SCIP returned nonintegral or incomplete registration assignment")
                j = next(j for j, v in enumerate(values) if v > .5)
                choices[pid] = [s["seat_id"] for s in self.options[pid][j]]
        raw_value = self.model.Objective().Value() if feasible else None
        if feasible and (not math.isfinite(raw_value) or abs(raw_value - round(raw_value)) > TOLERANCE):
            raise ValueError("SCIP objective is not an integral production penalty")
        value = round(raw_value) if feasible else None
        bound = self.model.Objective().BestBound() if feasible else None
        if bound is not None and not math.isfinite(bound):
            bound = None
        native = parse_scip_log(Path(log).read_text(encoding="utf-8", errors="replace"))
        return dict(api_status=status, choices=choices, value=value, best_bound=bound,
                    proven=proof_established(status, value, bound, native),
                    absolute_gap=max(0, value - bound) if value is not None and bound is not None else None,
                    relative_gap=max(0, value - bound) / max(1, abs(value)) if value is not None and bound is not None else None,
                    nodes=self.model.nodes() if feasible else None, **native)

    def fix(self, expression, value):
        self.model.Add(expression == value)


BUILDERS = {"cp_sat": CPSAT, "scip": SCIP}
