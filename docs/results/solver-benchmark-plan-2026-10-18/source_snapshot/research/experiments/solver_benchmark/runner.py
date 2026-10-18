"""Bounded subprocess runner. The main study never resumes or silently shrinks."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import time
import traceback

import ortools
from ortools.linear_solver import pywraplp

from .cases import inventory, pilot_schedule, schedule
from .common import (ROOT, PROTOCOL, SEARCH_SEED, ORDER_SEED, INPUT_SEED, HEAVY_SEED, PILOT_SEED,
                     METHODS, Problem, compact_weights, digest, execute, preferences, prepare, read, save, score_and_audit,
                     verify_option_scores)

ENTRY = ROOT / "research/experiments/solver_selection_benchmark.py"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def source_files():
    paths = set((ROOT / "research/experiments/solver_benchmark").glob("*.py"))
    paths.update((ROOT / "services/seating/src").rglob("*.py"))
    paths.update((ROOT / "services/seating/config").glob("*.json"))
    paths.update((ROOT / "services/seating/schemas").glob("*.json"))
    paths.update((ROOT / "docs/planning").glob("*experiment*.md"))
    paths.update(ROOT / p for p in ("research/fixtures/synthetic_participants.py",
                                   "services/seating/data/production_request.json",
                                   "docs/planning/solver-selection-benchmark.md",
                                   "docs/planning/benchmark-results-visualization.md",
                                   "research/experiments/requirements-benchmark.txt",
                                   "research/experiments/requirements-benchmark-lock.txt",
                                   "research/experiments/setup_benchmark.py"))
    paths.add(ENTRY)
    return sorted(paths)


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()}


def environment(out):
    backend = pywraplp.Solver.CreateSolver("SCIP")
    if backend is None:
        raise RuntimeError("SCIP is unavailable in the selected interpreter")
    for name in ("ortools", "jsonschema", "matplotlib"):
        importlib.metadata.version(name)
    snapshot = hashes()
    for name in snapshot:
        target = out / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, timeout=30)
    (out / "requirements-lock.txt").write_text(freeze)
    hardware = {}
    if platform.system() == "Darwin":
        for key in ("hw.model", "hw.memsize", "machdep.cpu.brand_string"):
            value = subprocess.run(["/usr/sbin/sysctl", "-n", key], capture_output=True, text=True, timeout=5)
            hardware[key] = value.stdout.strip() if value.returncode == 0 else "unavailable"
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(), "hardware": hardware,
            "machine": platform.machine(), "processor": platform.processor(), "cpu_count": os.cpu_count(),
            "ortools": ortools.__version__, "scip": backend.SolverVersion(), "source_sha256": snapshot,
            "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
            "timezone": "Asia/Kuala_Lumpur", "power_conditions": "Operator must keep plugged in/awake, stable power settings, no competing heavy workloads"}


def frozen_input(payload):
    request = read(payload["input"])
    if digest(request) != payload["input_sha256"]:
        raise ValueError("Frozen event input changed after certification")
    return request


def job_request(payload):
    request = frozen_input(payload)
    request["preferences"] = preferences(payload["job"]["configuration"])
    request["solver"].update(max_time_seconds=payload["job"]["budget_seconds"], num_search_workers=1,
                              random_seed=SEARCH_SEED, canonicalize=False, require_optimal=False)
    return request


def prototype(payload, output):
    from seat_solver.production.policy import policy
    from seat_solver.production.production_scoring import eligible
    request = frozen_input(payload)
    request["preferences"] = preferences("current")
    request["solver"] = read(ROOT / "services/seating/data/production_request.json")["solver"]
    # Preserve actual settings from the frozen request fixture; do not import controlled-search settings.
    if request["solver"]["max_time_seconds"] != 60:
        raise ValueError("Prototype source allowance changed from the declared 60 seconds")
    store = Path(payload["store"])
    if store.exists():
        raise FileExistsError("Prototype store must be fresh")
    store.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "services/seating/src"), "SEAT_PLAN_DB": str(store),
           "SEAT_SOLVER_ROOT": str(ROOT), "SEAT_SOLVER_RESOURCES": str(ROOT / "services/seating")}
    started = time.perf_counter()
    child = subprocess.run([sys.executable, "-m", "seat_solver.production.service"],
                           input=json.dumps({"command": "solve", "event_id": request["event_id"],
                                             "actor": "research-benchmark", "request": request}),
                           text=True, capture_output=True, cwd=ROOT, env=env, check=True)
    raw = json.loads(child.stdout)
    returned = time.perf_counter()
    save(Path(payload["raw_output"]), raw)
    successful = raw.get("status") == "success"
    record = {**payload["job"], "execution_status": "validation_pending" if successful else "completed",
              "solver_status": raw.get("solver", {}).get("status") if successful else raw.get("error", {}).get("solver_status"),
              "valid": False, "objective": None, "best_bound": None, "validation": None,
              "request_sha256": digest(request), "worker_count": request["solver"]["num_search_workers"],
              "canonicalize": request["solver"]["canonicalize"], "prototype_settings": request["solver"],
              "placements": raw.get("assignments"), "production_proof": raw.get("solver", {}).get("proof"),
              "production_objective": raw.get("solver", {}).get("objective_value"),
              "canonicalization_complete": raw.get("solver", {}).get("canonicalization_complete"),
              "timing": {"service_return_seconds": returned - started, "production_internal": raw.get("solver", {}).get("timing")},
              "error": raw.get("error"), "registrations": len(eligible(request)),
              "physical_seats": sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in eligible(request))}
    save(output, record)
    if successful:
        p = Problem(request, policy(), {q["participant_id"]: q for q in eligible(request)}, {}, {}, [], compact_weights(request))
        audit, scores = score_and_audit(p, raw["assignments"])
        record.update(validation=audit, valid=audit["passed"], weights=p.weights)
        if scores:
            record.update(scores)
    record["execution_status"] = "completed"
    record["timing"].update(external_audit_and_persistence_seconds=time.perf_counter() - returned,
                            allocation_total_seconds=time.perf_counter() - started)
    return record


def worker(payload_path, output):
    payload = read(payload_path)
    try:
        if payload["kind"] == "inventory":
            events = inventory(pilot=payload["pilot"])
            meta = {}
            for name, event in events.items():
                request = event.pop("request")
                proof = event.pop("witness")
                directory = Path(payload["directory"])
                problem = prepare(request)
                checked = verify_option_scores(problem)
                for assignment in proof["placements"]:
                    if tuple(sorted(assignment["seat_ids"])) not in {tuple(sorted(b.ids)) for b in problem.bundles[assignment["participant_id"]]}:
                        raise ValueError("Shared row/domain pruning excludes the audited witness")
                save(directory / "inputs" / f"{name}.json", request)
                save(directory / "witnesses" / f"{name}.json", proof)
                meta[name] = {**event, "input_sha256": digest(request), "witness_sha256": digest(proof), "checked_option_vectors": checked,
                              "registrations": len(request["participants"]),
                              "physical_seats": sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in request["participants"])}
            result = {"passed": True, "events": meta}
        elif payload["kind"] == "correctness":
            from .checks import correctness
            result = correctness()
        elif payload["kind"] == "report":
            from .report import report
            result = report(Path(payload["directory"]), plots=payload["plots"])
        elif payload["job"]["batch"] == "prototype":
            result = prototype(payload, output)
        else:
            result = execute(job_request(payload), payload["job"]["method"], payload["job"]["budget_seconds"],
                             checkpoint=lambda record: save(output, {**payload["job"], **record}))
            result = {**payload["job"], **result}
        if payload["kind"] == "trial":
            rss_to_bytes = 1 if sys.platform == "darwin" else 1024
            result["memory"] = {"worker_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * rss_to_bytes,
                                "scope": "Fresh per-trial worker lifetime peak; includes imports, model and audit; not solver-only"}
            if payload["job"]["batch"] == "prototype":
                result["memory"]["service_child_peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * rss_to_bytes
                result["memory"]["child_scope"] = "Service child peak, recorded separately; not a simultaneous parent-plus-child peak"
        save(output, result)
        return 0
    except Exception as exc:
        save(output, {**payload.get("job", {}), "execution_status": "error", "passed": False, "valid": False,
                      "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()})
        return 1


def bounded_worker(payload, output, deadline):
    """A process-group watchdog also covers native solves and prototype descendants."""
    output = Path(output)
    payload_path = output.parent / (output.stem + ".payload.json")
    save(payload_path, payload)
    started = time.perf_counter()
    remaining = deadline - started
    if remaining <= 0:
        return {"execution_status": "not_started", "passed": False, "valid": False}
    child = subprocess.Popen([sys.executable, str(ENTRY), "_worker", "--payload", str(payload_path), "--out", str(output)],
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=remaining)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
    elapsed = time.perf_counter() - started
    result = read(output) if output.exists() else {"execution_status": "interrupted_by_deadline" if timed_out else "error",
                                                   "passed": False, "valid": False}
    result["worker_elapsed_seconds"] = elapsed
    result["worker_exit_code"] = child.returncode
    if timed_out:
        result["interrupted_by_deadline"] = True
    if child.returncode and not timed_out:
        result["execution_status"] = "error"
        result["passed"] = False
    if stderr or stdout:
        output.with_suffix(".log").write_text(stdout + "\n" + stderr)
    save(output, result)
    return result


def run_job(out, job, input_dir, deadline, pilot=False):
    folder = out / "pilot" / "runs" if pilot else out / "runs"
    output = folder / f"{job['id']}.json"
    payload = {"kind": "trial", "job": job, "input": str(input_dir / "inputs" / f"{job['event']}.json"),
               "input_sha256": read(input_dir / "inventory.json")["events"][job["event"]]["input_sha256"],
               "store": str(out / "local_stores" / ("pilot" if pilot else "main") / job["id"] / "plans.sqlite3"),
               "raw_output": str(out / "prototype_outputs" / ("pilot" if pilot else "main") / f"{job['id']}.json")}
    save(output, {**job, "execution_status": "running", "valid": False})
    result = bounded_worker(payload, output, deadline)
    # A killed worker can leave the initial running record or a validation-pending checkpoint.
    result = {**job, **result}
    if result["execution_status"] == "running":
        result["execution_status"] = "interrupted_by_deadline" if result.get("interrupted_by_deadline") else "error"
    save(output, result)
    print(f"{job['id']}: {result.get('solver_status', result['execution_status'])}; valid={result.get('valid', False)}", flush=True)
    return result


def defect(result):
    if result.get("execution_status") != "completed":
        return True
    if result.get("placements") is not None and not result.get("valid"):
        return True
    return result.get("solver_status") in ("INFEASIBLE", "MODEL_INVALID", "ABNORMAL", "UNBOUNDED")


def projection(rows, elapsed):
    overhead = {}
    for method in METHODS:
        measured = [max(0, r["worker_elapsed_seconds"] - r.get("timing", {}).get("search_seconds", 0))
                    for r in rows if r["method"] == method and r["batch"] != "prototype"]
        overhead[method] = max(measured, default=0) * 1.25 + .25
    proto = max((max(0, r["worker_elapsed_seconds"] - 60) for r in rows if r["batch"] == "prototype"), default=0) * 1.25 + 1
    projected = elapsed + 4020 + sum(76 * v for v in overhead.values()) + 4 * (60 + proto) + 300
    return {"elapsed_preparation_seconds": elapsed, "comparative_search_allocation_seconds": 4020,
            "overhead_seconds_per_method": overhead, "prototype_extra_seconds": proto,
            "report_reserve_seconds": 300, "projected_total_seconds": projected,
            "fits_90_minutes": projected <= 5400,
            "method": "Full allocated search + 1.25x maximum pilot overhead + fixed margins; no assumed greedy early exit"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Shared CP-SAT / SCIP / greedy benchmark. Default command does not run the main study.")
    parser.add_argument("command", choices=("plan", "check", "pilot", "run", "report", "_worker"))
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory (existing bundle only for report)")
    parser.add_argument("--payload", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--pilot-seconds", type=float, default=600, help="Development-only pilot ceiling, maximum 900 s")
    parser.add_argument("--plots", action="store_true", help="Generate PDF/SVG/PNG figures for report")
    args = parser.parse_args(argv)
    if sys.flags.optimize:
        parser.error("Do not use Python -O: correctness assertions must remain enabled")
    out = args.out.resolve()
    if args.command == "_worker":
        return worker(args.payload, out)
    if args.command == "report":
        from .report import report
        report(out, plots=args.plots)
        return 0
    if not 0 < args.pilot_seconds <= 900:
        parser.error("--pilot-seconds must be in (0, 900]")
    started = time.perf_counter()
    ceiling = 5400 if args.command == "run" else args.pilot_seconds
    deadline = started + ceiling
    main_deadline = deadline - 300 if args.command == "run" else deadline
    out.mkdir(parents=True, exist_ok=False)
    jobs = schedule()
    manifest = {"protocol": PROTOCOL, "mode": args.command, "created_at": utcnow(), "execution_status": "preparing",
                "seeds": {"input": INPUT_SEED, "heavy_input": HEAVY_SEED, "pilot_input": PILOT_SEED,
                          "search": SEARCH_SEED, "execution_order": ORDER_SEED},
                "runner_ceiling_seconds": ceiling, "jobs": jobs,
                "planned_counts": dict(Counter(j["batch"] for j in jobs)),
                "budget_kind": "prototype shared function allowance; comparative search-only allowance",
                "study_scope": "INITIAL synthetic events; human satisfaction excluded"}
    save(out / "manifest.json", manifest)
    try:
        manifest["environment"] = environment(out)
        save(out / "manifest.json", manifest)
        if args.command in ("plan", "run"):
            events = bounded_worker({"kind": "inventory", "pilot": False, "directory": str(out)}, out / "inventory.json", main_deadline)
            if not events.get("passed"):
                raise RuntimeError("Main input certification failed or exceeded the deadline")
            manifest["events"] = events["events"]
            for job in jobs:
                save(out / "runs" / f"{job['id']}.json", {**job, "execution_status": "not_started", "valid": False})
        if args.command != "plan":
            checked = bounded_worker({"kind": "correctness"}, out / "correctness.json", min(main_deadline, time.perf_counter() + 240))
            if not checked.get("passed"):
                raise RuntimeError("Correctness gate failed; main experiment prohibited")
        if args.command in ("pilot", "run"):
            pilot_dir = out / "pilot"
            pilot_end = min(main_deadline, time.perf_counter() + args.pilot_seconds)
            result = bounded_worker({"kind": "inventory", "pilot": True, "directory": str(pilot_dir)}, pilot_dir / "inventory.json", pilot_end)
            if not result.get("passed"):
                raise RuntimeError("Pilot input certification failed")
            rows = []
            for job in pilot_schedule():
                if pilot_end - time.perf_counter() < job["budget_seconds"] + 2:
                    raise RuntimeError("Pilot allowance insufficient for next complete run; main experiment prohibited")
                row = run_job(out, job, pilot_dir, pilot_end, pilot=True)
                rows.append(row)
                if defect(row):
                    raise RuntimeError(f"Pilot failed validation/correctness or execution: {job['id']}")
            estimate = projection(rows, time.perf_counter() - started)
            save(out / "pilot" / "projection.json", estimate)
            manifest["pilot_projection"] = estimate
            if args.command == "run" and not estimate["fits_90_minutes"]:
                raise RuntimeError("Pilot projection exceeds 90 minutes; protocol amendment required before main runs")
        if args.command == "run":
            manifest["execution_status"] = "running"
            save(out / "manifest.json", manifest)
            for job in jobs:
                if hashes() != manifest["environment"]["source_sha256"]:
                    raise RuntimeError("Experiment sources changed during execution")
                overhead = estimate["prototype_extra_seconds"] if job["batch"] == "prototype" else estimate["overhead_seconds_per_method"][job["method"]]
                if main_deadline - time.perf_counter() < job["budget_seconds"] + overhead:
                    raise RuntimeError("Insufficient remaining allowance; remaining jobs preserved as not_started")
                row = run_job(out, job, out, main_deadline)
                if defect(row):
                    raise RuntimeError(f"Main validation/correctness or execution failure: {job['id']}")
        manifest["execution_status"] = {"plan": "planned", "check": "correctness_passed", "pilot": "pilot_completed", "run": "completed"}[args.command]
    except (Exception, KeyboardInterrupt) as exc:
        manifest["execution_status"] = "stopped"
        manifest["stop_reason"] = str(exc) or type(exc).__name__
        print(f"Stopped: {manifest['stop_reason']}", file=sys.stderr, flush=True)
    manifest["ended_at"] = utcnow()
    manifest["elapsed_seconds_before_reporting"] = time.perf_counter() - started
    save(out / "manifest.json", manifest)
    if args.command in ("run", "plan") and time.perf_counter() < deadline:
        result = bounded_worker({"kind": "report", "directory": str(out), "plots": args.command == "run"},
                                out / "report-status.json", deadline)
        manifest["report_completed"] = result.get("passed", False)
        if not manifest["report_completed"] and manifest["execution_status"] != "stopped":
            manifest["execution_status"] = "stopped"
            manifest["stop_reason"] = "Report generation failed or exceeded the deadline; raw records preserved"
    manifest["runner_elapsed_seconds"] = time.perf_counter() - started
    save(out / "manifest.json", manifest)
    print(f"Evidence: {out}; status={manifest['execution_status']}", flush=True)
    return 0 if manifest["execution_status"] != "stopped" else 1
