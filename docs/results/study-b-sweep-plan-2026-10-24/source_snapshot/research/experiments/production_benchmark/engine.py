"""Study B allocation function and bridge through the real local JSON service.

Production modules are reused, not edited. Only this worker's service.solve
reference is injected. Each job owns a fresh SQLite store and the original
function reference is restored before returning.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import time

from seat_solver.production.policy import DomainError, mapped_weights, policy, validate_request
from seat_solver.production.production import error, format_result
from seat_solver.production.production_scoring import candidate_cost, eligible, options
from seat_solver.production.production_validator import audit_result, validate_placements
from research.experiments.solver_benchmark.common import reference_components

from .backends import BUILDERS
from .protocol import KEYS, digest, map_hash, normalize, physical_map, save, semantic_hash


class AllocationFunction:
    def __init__(self, backend, log_directory, workers=8, checkpoint=None):
        self.backend, self.workers = backend, workers
        self.log_directory = Path(log_directory)
        self.checkpoint = checkpoint
        self.telemetry = {}
        self.candidate = None
        self.choices = None
        self.phases = []

    @contextmanager
    def phase(self, name):
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self.phases.append(dict(name=name, start_seconds=start - self.started,
                                    end_seconds=end - self.started, duration_seconds=end - start))

    def __call__(self, raw):
        self.started = time.perf_counter()
        self.phases, self.choices, self.candidate = [], None, None
        self.telemetry = dict(backend=self.backend, weighted_proven=False, stages=[],
                              weighted_proof_reported_seconds=None, weighted_stage_return_seconds=None)
        result = None
        try:
            result = self.solve(raw)
        except DomainError as exc:
            result = error(exc.code, str(exc), exc.details)
        finally:
            ended = time.perf_counter()
            self.telemetry.update(phases=self.phases, function_return_seconds=ended - self.started,
                                  unclassified_function_overhead_seconds=max(0, ended - self.started - sum(p["duration_seconds"] for p in self.phases)))
        if result and result["status"] == "success":
            result["solver"]["end_to_end_seconds"] = self.telemetry["function_return_seconds"]
        return result

    def stage(self, model, name, expression, workers):
        remaining = self.deadline - time.perf_counter()
        if remaining <= 0:
            return None
        with self.phase("model_updates"):
            model.configure(expression, remaining, workers)
        if time.perf_counter() >= self.deadline:
            return None
        number = len(self.telemetry["stages"])
        log = self.log_directory / f"{number:03d}.log"
        with self.phase("weighted_search"):
            model.run(log)
        returned = time.perf_counter() - self.started
        with self.phase("extraction"):
            report = model.extract(expression, log)
        choices = report.pop("choices")
        report.update(stage=name, workers=workers, returned_seconds=returned, native_log=str(log.name))
        if report["best_bound"] is not None and report["value"] is not None and report["best_bound"] > report["value"] + 1e-6:
            raise ValueError("Solver lower bound exceeds integral incumbent")
        self.telemetry["stages"].append(report)
        if choices is not None:
            self.choices = choices
        if report["api_status"] in ("MODEL_INVALID", "ABNORMAL", "UNBOUNDED"):
            raise ValueError(f"Backend defect in {name}: {report['api_status']}")
        return report

    def solve(self, raw):
        with self.phase("normalization"):
            request = normalize(validate_request(raw))
            if request["generation_mode"] != "INITIAL":
                raise DomainError("INVALID_INPUT", "Study B attempt 3 covers initial allocation only")
            if request["solver"]["canonicalize"] or request["solver"]["num_search_workers"] != self.workers:
                raise DomainError("INVALID_INPUT", "Study B attempt 3 requires canonical selection off and declared workers")
            cfg = policy()
            self.deadline = self.started + request["solver"]["max_time_seconds"]
            self.telemetry.update(budget_seconds=request["solver"]["max_time_seconds"],
                                  raw_request_sha256=digest(raw), semantic_input_sha256=semantic_hash(request),
                                  normalized_request_sha256=digest(request), weights=mapped_weights(request["preferences"]))
            people = eligible(request)
            demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in people)
            if demand > sum(not s["is_blocked"] for s in request["layout"]["seats"]):
                raise DomainError("CAPACITY_EXCEEDED", "Demand exceeds available seats")
            if any(not options(request, p) for p in people):
                raise DomainError("TIER_CAPACITY_EXCEEDED", "A registration has no accessible legal bundle")
        with self.phase("model_build"):
            model = BUILDERS[self.backend](request, cfg)
        weighted = self.stage(model, "weighted_preferences", model.weighted, self.workers)
        if weighted and weighted["api_status"] == "INFEASIBLE":
            self.telemetry["solver_status"] = "INFEASIBLE"
        self.telemetry["weighted_proven"] = bool(weighted and weighted["proven"])
        self.telemetry["weighted_stage_return_seconds"] = weighted["returned_seconds"] if weighted else None
        if self.telemetry["weighted_proven"]:
            self.telemetry["weighted_proof_reported_seconds"] = weighted["returned_seconds"]
        if self.choices is not None and self.checkpoint:
            self.checkpoint(dict(validation_pending=True, placements=physical_map(self.choices),
                                 weighted_stage=weighted))
        self.telemetry["shared_work_elapsed_seconds"] = time.perf_counter() - self.started
        self.telemetry["within_shared_allowance"] = bool(weighted and
            weighted["returned_seconds"] <= request["solver"]["max_time_seconds"])
        if self.choices is None:
            return error("SOLVER_UNKNOWN", "No candidate was established within the shared allowance",
                         {"weighted_proven": False},
                         weighted["api_status"] if weighted else "UNKNOWN")
        with self.phase("validation_scoring"):
            placements = physical_map(self.choices)
            audit = validate_placements(request, placements)
            if not audit["passed"]:
                self.candidate = dict(valid=False, validation=audit, placements=placements)
                self.telemetry["encoding_defect"] = True
                if self.checkpoint:
                    self.checkpoint(self.candidate)
                return error("OUTPUT_VALIDATION_FAILED", "Independent hard-rule audit rejected candidate", audit)
            lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
            totals = dict.fromkeys(KEYS, 0)
            weights = mapped_weights(request["preferences"])
            for person in people:
                seats = [lookup[sid] for sid in self.choices[person["participant_id"]]]
                independent = reference_components(request, cfg, person, seats)
                if independent != candidate_cost(request, cfg, person, seats)["normalized"]:
                    raise ValueError("Independent Decimal scorer differs from production scorer")
                for key in KEYS:
                    totals[key] += independent[key]
            objective = sum(weights[k] * totals[k] for k in KEYS)
            if not weighted or objective != weighted["value"]:
                raise ValueError("Final candidate differs from weighted-stage objective")
            self.candidate = dict(valid=True, validation=audit, placements=placements, objective=objective,
                                  components=totals, weights=weights, physical_map_sha256=map_hash(placements),
                                  weighted_proven=self.telemetry["weighted_proven"])
        if self.checkpoint:
            self.checkpoint(self.candidate)
        if not self.telemetry["within_shared_allowance"]:
            return error("ALLOCATION_ALLOWANCE_EXCEEDED", "Weighted search returned after the shared allowance",
                         {"candidate_valid": True, "weighted_proven": self.telemetry["weighted_proven"]}, weighted["api_status"])
        proof = [{k: weighted[k] for k in ("stage", "value", "best_bound", "absolute_gap", "relative_gap")} |
                 {"status": "OPTIMAL" if self.telemetry["weighted_proven"] else "FEASIBLE"}]
        stats = dict(engine="Google OR-Tools CP-SAT" if self.backend == "cp_sat" else model.model.SolverVersion(),
                     status="OPTIMAL" if self.telemetry["weighted_proven"] else "FEASIBLE",
                     proof=proof, canonicalization_complete=False, optimality_scope="full_model",
                     wall_time_seconds=sum(p["duration_seconds"] for p in self.phases if p["name"] == "weighted_search"),
                     timing={name: sum(p["duration_seconds"] for p in self.phases if p["name"] == name)
                             for name in {p["name"] for p in self.phases}})
        with self.phase("format_response"):
            return format_result(request, self.choices, stats)


def invoke(request, backend, store_path, logs, workers=8, checkpoint=None):
    """Include real service dispatch, validation, SQLite adoption and JSON encoding.

    Interpreter imports are outside the service clock;
    the parent worker clock records these separately. No browser/network is used.
    """
    from seat_solver.production import service
    from seat_solver.production.plan_store import PlanStore

    if Path(store_path).exists():
        raise FileExistsError("Every job requires a fresh isolated SQLite store")
    preparation = time.perf_counter()
    store = PlanStore(store_path)
    event = request["event_id"]
    body = dict(command="solve", event_id=event, actor="study-b", request=request)
    engine = AllocationFunction(backend, logs, workers, checkpoint)
    original = service.solve
    service.solve = engine
    ready = time.perf_counter()
    try:
        response = service.dispatch(body, store=store)
        encoded = json.dumps(response, ensure_ascii=False, allow_nan=False)
    finally:
        service.solve = original
    returned = time.perf_counter()
    response = json.loads(encoded)
    latest = store.latest(event)
    public_valid = response.get("status") == "success" and audit_result(response)["passed"]
    adopted = bool(public_valid and latest and latest["plan_version_id"] == response["plan_version_id"])
    if response.get("status") == "success" and not adopted:
        raise ValueError("Service returned success without a validated persisted map")
    if not adopted and latest is not None:
        raise ValueError("Rejected candidate was persisted")
    return dict(response=response, candidate=engine.candidate, telemetry=engine.telemetry,
                returned_new_map=adopted, bridge_preparation_seconds=ready - preparation,
                complete_service_return_seconds=returned - ready,
                response_bytes=len(encoded.encode("utf-8")),
                physical_map_sha256=map_hash(response["assignments"]) if adopted else None)
