"""Independent tiny enumeration, native concurrency and frozen-input gates."""

from __future__ import annotations

import copy
import itertools
import os
from pathlib import Path
import random

from ortools.linear_solver import pywraplp
from seat_solver.production.policy import TIERS, mapped_weights, policy
from seat_solver.production.production import initial_rows
from seat_solver.production.production_scoring import candidate_cost, eligible, options
from seat_solver.production.production_validator import validate_placements
from research.experiments.solver_benchmark.checks import tiny
from research.experiments.solver_benchmark.common import reference_components

from .backends import native_log, parse_scip_log
from .engine import AllocationFunction, invoke
from .protocol import BACKENDS, CONFIGS, KEYS, THREADS, digest, map_hash, preferences, read, save


def concurrency_probe(directory):
    """A non-seating knapsack with an independent dynamic-programming optimum."""
    if (os.cpu_count() or 0) < THREADS:
        raise RuntimeError("Study B requires at least eight logical CPUs; do not silently reduce workers")
    model = pywraplp.Solver.CreateSolver("SCIP")
    if model is None or not model.SetNumThreads(THREADS):
        raise RuntimeError("SCIP/native SetNumThreads(8) is unavailable")
    parameters = ("limits/gap = 0\nlimits/absgap = 0\nparallel/minnthreads = 8\nparallel/maxnthreads = 8\n"
                  "presolving/maxrounds = 0\nrandomization/randomseedshift = 20261023\ndisplay/verblevel = 4")
    if not model.SetSolverSpecificParametersAsString(parameters):
        raise RuntimeError("SCIP rejected concurrency preflight settings")
    rng = random.Random(17)
    weights = [rng.randrange(1, 31) for _ in range(40)]
    values = [rng.randrange(1, 61) for _ in weights]
    capacity = sum(weights) // 3
    dp = [0] * (capacity + 1)
    for weight, value in zip(weights, values):
        for amount in range(capacity, weight - 1, -1):
            dp[amount] = max(dp[amount], dp[amount - weight] + value)
    variables = [model.BoolVar(f"x{i}") for i in range(len(weights))]
    model.Add(model.Sum(w*v for w, v in zip(weights, variables)) <= capacity)
    model.Maximize(model.Sum(v*x for v, x in zip(values, variables)))
    model.SetTimeLimit(2000)
    model.EnableOutput()
    log = Path(directory) / "scip-concurrency.log"
    with native_log(log):
        status = model.Solve()
    observation = parse_scip_log(log.read_text(encoding="utf-8", errors="replace"))
    if observation["observed_concurrent_solvers"] != THREADS:
        raise RuntimeError(f"Native SCIP concurrency not verified: {observation}; inspect {log}. No single-thread fallback is permitted")
    if status != model.OPTIMAL or abs(model.Objective().Value() - dp[capacity]) > 1e-6 or abs(model.Objective().BestBound() - dp[capacity]) > 1e-6:
        raise RuntimeError("Concurrent SCIP failed the independent knapsack optimum/proof check")
    return dict(passed=True, requested_workers=THREADS, set_num_threads_accepted=True,
                solver_version=model.SolverVersion(), probe_api_status=status,
                oracle_objective=dp[capacity], concurrent_optimum_verified=True,
                verification="Eight distinct native 'starting solve in concurrent solver' messages",
                log=str(log.name), **observation)


def oracle(request):
    """Enumerate physical placements, independently of both encodings/pruning.

    Hard front/side packing fixes the occupied priority prefix. Check entitlements,
    approved physical pairs, accessibility, overlap and all pairwise order rules.
    The physical-ID order only makes the oracle deterministic; either solver
    may return any equally optimal physical map.
    """
    people = eligible(request)
    cfg, weights = policy(), mapped_weights(request["preferences"])
    demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in people)
    available = sorted((s for s in request["layout"]["seats"] if not s["is_blocked"]),
                       key=lambda s: (s["row_number"], s["priority_rank"]))
    if demand > len(available):
        return None
    occupied = available[:demand]
    lookup = {(s["row_number"], s["physical_position"]): s for s in occupied}
    domains = []
    for person in people:
        if person["contribution_tier"] == "EMPEROR":
            candidates = [(lookup[row, a], lookup[row, b]) for row in range(1, request["layout"]["row_count"] + 1)
                          for a, b in request["layout"]["approved_pairs"] if (row, a) in lookup and (row, b) in lookup]
        else:
            candidates = [(s,) for s in occupied]
        domains.append([o for o in candidates if not person["requires_accessible_seat"] or all(s["is_accessible"] for s in o)])
    best = None
    width = request["layout"]["seats_per_row"]
    for arrangement in itertools.product(*domains):
        if len({s["seat_id"] for option in arrangement for s in option}) != demand:
            continue
        valid = True
        for i, p in enumerate(people):
            for j in range(i + 1, len(people)):
                q = people[j]
                pt, qt = TIERS.index(p["contribution_tier"]), TIERS.index(q["contribution_tier"])
                po = [(s["row_number"] - 1) * width + s["priority_rank"] for s in arrangement[i]]
                qo = [(s["row_number"] - 1) * width + s["priority_rank"] for s in arrangement[j]]
                if (pt < qt and max(po) >= min(qo)) or (pt > qt and max(qo) >= min(po)):
                    valid = False
                if pt == qt and (p["contribution_amount_rm"] - q["contribution_amount_rm"]) * (arrangement[i][0]["row_number"] - arrangement[j][0]["row_number"]) > 0:
                    valid = False
        if not valid:
            continue
        value = sum(sum(weights[k] * reference_components(request, cfg, p, option)[k] for k in KEYS)
                    for p, option in zip(people, arrangement))
        ids = tuple(tuple(sorted(s["seat_id"] for s in option)) for option in arrangement)
        key = (value, ids)
        if best is None or key < best[0]:
            placements = [{"participant_id": p["participant_id"], "seat_ids": list(bundle)} for p, bundle in zip(people, ids)]
            best = (key, placements)
    return None if best is None else dict(objective=best[0][0], placements=best[1], physical_map_sha256=map_hash(best[1]))


def tiny_cases():
    cases = dict(singles=tiny(), mixed_tiers=tiny(1, 1, 1), two_pairs=tiny(2, 0, 0),
                 two_rows=tiny(0, 4, 0, ((1, 9), (1, 10), (2, 9), (2, 10))),
                 empty=tiny(0, 0, 0), capacity_infeasible=tiny(0, 5, 0))
    inaccessible = tiny(0, 1, 0)
    inaccessible["participants"][0]["requires_accessible_seat"] = True
    cases["accessibility_infeasible"] = inaccessible
    accessible = tiny(1, 0, 0, ((1, 15), (1, 16)))
    accessible["participants"][0]["requires_accessible_seat"] = True
    cases["accessible_pair"] = accessible
    equal = tiny()
    for p in equal["participants"]:
        p.update(contribution_amount_rm=3000, events_joined_last_2_years=0)
    cases["equal_scores"] = equal
    return cases


def correctness(directory):
    records = []
    for name, original in tiny_cases().items():
        for config in CONFIGS:
            request = copy.deepcopy(original)
            request["preferences"] = preferences(config)
            request["solver"].update(max_time_seconds=3, num_search_workers=1, canonicalize=False, require_optimal=False)
            expected = oracle(request)
            for backend in BACKENDS:
                engine = AllocationFunction(backend, Path(directory) / name / config / backend, workers=1)
                response = engine(request)
                if expected is None:
                    if response["status"] != "error" or engine.candidate is not None:
                        raise ValueError(f"Infeasible oracle disagreement: {name}/{config}/{backend}")
                    if response["error"]["code"] == "SOLVER_UNKNOWN" and response["error"]["solver_status"] != "INFEASIBLE":
                        raise ValueError("Tiny infeasible case timed out instead of establishing infeasibility")
                else:
                    if (response["status"] != "success" or not engine.candidate["valid"]
                            or engine.candidate["objective"] != expected["objective"]
                            or not engine.telemetry["weighted_proven"]):
                        raise ValueError(f"Optimum/validity oracle disagreement: {name}/{config}/{backend}: {response.get('error')}")
                records.append(dict(case=name, configuration=config, backend=backend,
                                    feasible=expected is not None, objective=expected["objective"] if expected else None,
                                    valid_and_optimal=expected is None or (engine.candidate["valid"] and engine.telemetry["weighted_proven"])))
    return dict(passed=True, oracle_cases=records, executions=len(records),
                scope="Tiny development/correctness oracles only; excluded from measured study denominators")


def certify_inputs(out):
    metadata = read(Path(out) / "manifest.json")["inputs"]
    result = {}
    cfg = policy()
    for event, info in metadata.items():
        request = read(Path(out) / "inputs" / f"{event}.json")
        witness = read(Path(out) / "witnesses" / f"{event}.json")
        if digest(request) != info["input_sha256"] or digest(witness) != info["witness_sha256"]:
            raise ValueError("Frozen input/witness changed")
        request["preferences"] = preferences(info["configuration"])
        audit = validate_placements(request, witness["placements"])
        if not audit["passed"]:
            raise ValueError(f"Input witness failed: {event}: {audit}")
        allowed = initial_rows(request)
        domains, checked = {}, 0
        for person in eligible(request):
            pid = person["participant_id"]
            domains[pid] = set()
            for option in options(request, person):
                if option[0]["row_number"] not in allowed[pid]:
                    continue
                domains[pid].add(tuple(sorted(s["seat_id"] for s in option)))
                if reference_components(request, cfg, person, option) != candidate_cost(request, cfg, person, option)["normalized"]:
                    raise ValueError(f"Independent production scorer mismatch: {event}/{pid}")
                checked += 1
        if any(tuple(sorted(a["seat_ids"])) not in domains[a["participant_id"]] for a in witness["placements"]):
            raise ValueError(f"Row pruning excludes feasible witness: {event}")
        result[event] = dict(passed=True, checked_option_vectors=checked,
                             production_weights=mapped_weights(request["preferences"]), witness_validation=audit)
    return dict(passed=True, events=result)


def bridge_check(directory):
    """Actual initial service/SQLite calls, including valid unproved adoption."""
    from unittest.mock import patch
    request = tiny()
    request["preferences"] = preferences("current")
    request["solver"].update(max_time_seconds=10, num_search_workers=8, canonicalize=False, require_optimal=False)
    directory = Path(directory)
    rows = []
    for backend in BACKENDS:
        initial = invoke(request, backend, directory / f"{backend}-initial.sqlite3", directory / f"{backend}-initial")
        if not initial["returned_new_map"] or not initial["candidate"]["valid"]:
            raise ValueError(f"Tiny configured production initial call failed: {backend}")
        rows.append(dict(backend=backend, adopted=True, status=initial["response"]["solver"]["status"]))
    original = AllocationFunction.stage
    def unproved(self, model, name, expression, workers):
        result = original(self, model, name, expression, workers)
        if result and result["value"] is not None:
            result["proven"] = False
            result["api_status"] = "FEASIBLE"
        return result
    with patch.object(AllocationFunction, "stage", unproved):
        feasible = invoke(request, "cp_sat", directory / "feasible.sqlite3", directory / "feasible")
    if not feasible["returned_new_map"] or feasible["response"]["solver"]["status"] != "FEASIBLE":
        raise ValueError("Valid unproved candidate was not adopted as FEASIBLE")
    def invalid(self, model, name, expression, workers):
        result = original(self, model, name, expression, workers)
        if self.choices:
            first = next(iter(self.choices))
            self.choices[first] = ["NONEXISTENT-SEAT"]
        return result
    with patch.object(AllocationFunction, "stage", invalid):
        rejected = invoke(request, "cp_sat", directory / "invalid.sqlite3", directory / "invalid")
    if rejected["returned_new_map"] or rejected["candidate"]["valid"]:
        raise ValueError("Invalid candidate was adopted")
    return dict(passed=True, links=rows, valid_unproved_adopted=True, invalid_candidate_rejected=True,
                scope="Tiny correctness tests only, not measured workload results")
