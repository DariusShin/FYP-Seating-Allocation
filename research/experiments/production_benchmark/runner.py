"""Sequential Windows-safe subprocess runner, durable records and hard cap."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import traceback

import psutil

from .protocol import (BACKENDS, PILOT_SECONDS, PREFLIGHT_SECONDS, REPORT_SECONDS, ROOT, RUNNER_SECONDS,
                       STUDY, THREADS, digest, file_digest, frozen_inputs, pilot_schedule, read, request_for,
                       save, schedule, semantic_hash)

ENTRY = ROOT / "research/experiments/production_solver_benchmark.py"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def source_files():
    paths = set((ROOT / "research/experiments/production_benchmark").rglob("*.py"))
    paths.update((ROOT / "services/seating/src").rglob("*.py"))
    for folder in ("config", "schemas"):
        paths.update((ROOT / "services/seating" / folder).glob("*.json"))
    paths.update(ROOT / rel for rel in (
        "services/seating/data/production_request.json", "research/fixtures/synthetic_participants.py",
        "research/experiments/solver_benchmark/common.py", "research/experiments/solver_benchmark/checks.py",
        "research/experiments/solver_benchmark/cases.py", "research/experiments/solver_benchmark/__init__.py",
        "research/experiments/setup_production_benchmark.py", "research/experiments/requirements-study-b.txt",
        "research/experiments/requirements-benchmark-lock.txt",
        "research/experiments/tests/test_production_benchmark.py", "research/experiments/tests/conftest.py", "pytest.ini",
        "research/experiments/run_study_b_windows.ps1", "research/experiments/production_benchmark/README.md",
        "docs/planning/solver-selection-production-follow-up.md"))
    paths.add(ENTRY)
    return sorted(paths)


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): file_digest(p) for p in source_files()}


def environment(out):
    versions = {name: importlib.metadata.version(name) for name in ("ortools", "jsonschema", "psutil", "matplotlib", "pytest")}
    if versions["ortools"] != "9.15.6755":
        raise RuntimeError("Study B requires pinned OR-Tools 9.15.6755; run setup_production_benchmark.py")
    hashes = source_hashes()
    for rel in hashes:
        destination = out / "source_snapshot" / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / rel).read_bytes())
    freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, encoding="utf-8", timeout=30)
    (out / "requirements-lock.txt").write_text(freeze, encoding="utf-8")
    return dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                machine=platform.machine(), processor=platform.processor(), logical_cpus=psutil.cpu_count(),
                physical_cpus=psutil.cpu_count(logical=False), memory_bytes=psutil.virtual_memory().total,
                package_versions=versions, source_sha256=hashes,
                git_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
                power_conditions="Operator keeps machine awake/on stable power, with no competing heavy jobs")


def prepare(out, mode, development=False):
    from .protocol import SOURCE
    if any(parent == out or parent in out.parents for parent in (ROOT / "research", ROOT / "services", SOURCE)):
        raise ValueError("Evidence output must be outside source-code directories and the immutable Study A bundle")
    out.mkdir(parents=True, exist_ok=False)
    # Native logs are scientific provenance; databases remain local scratch state.
    (out / ".gitignore").write_text("!*.log\n!**/*.log\nstores/\n", encoding="utf-8")
    manifest = dict(study=STUDY, mode=mode, development_only=development, created_at=utcnow(),
                    execution_status="preparing", runner_cap_seconds=RUNNER_SECONDS,
                    clock="Shared allocation-function allowance; separate complete-service and worker clocks",
                    workers=THREADS, canonical_workers=1, inputs=frozen_inputs(out),
                    jobs=schedule(), pilot_jobs=pilot_schedule(), environment=environment(out))
    manifest["execution_status"] = "planned"
    save(out / "manifest.json", manifest)
    for folder, jobs in (("runs", manifest["jobs"]), ("pilot/runs", manifest["pilot_jobs"])):
        for trial in jobs:
            save(out / folder / f"{trial['id']}.json", {**trial, "execution_status": "not_started", "returned_new_map": False,
                                                        "reason": f"Not executed ({mode})"})
    return manifest


def require_windows11(development=False):
    if development:
        return
    if os.name != "nt" or sys.getwindowsversion().build < 22000 or sys.maxsize <= 2**32:
        raise RuntimeError("Measured Study B/pilot requires native 64-bit Windows 11. Use check --development only for non-Windows development validation")


def peak_memory():
    info = psutil.Process().memory_info()
    if os.name == "nt":
        return dict(bytes=info.peak_wset, method="Windows process lifetime peak working set; includes native solver threads")
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return dict(bytes=peak * (1 if sys.platform == "darwin" else 1024),
                method="Development only: process lifetime maximum RSS; not pooled with Windows measurements")


def terminate_tree(process):
    """Use Windows' tree kill; POSIX groups are only a development fallback."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=10, check=False)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
        return
    descendants = []
    try:
        parent = psutil.Process(process.pid)
        descendants = parent.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
        # A sandbox may prohibit a system process inventory. This worker owns
        # a fresh session, so its process group still provides tree isolation.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            if process.poll() is None:
                process.kill()
    try:
        for child in reversed(descendants):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        process.kill()
        psutil.wait_procs(descendants, timeout=5)
    except (psutil.NoSuchProcess, ProcessLookupError):
        pass
    process.wait(timeout=10)


def bounded_worker(out, payload, output, deadline):
    output = Path(output)
    payload_path = output.with_suffix(".payload.json")
    save(payload_path, payload)
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        result = {**payload.get("job", {}), "execution_status": "not_started", "returned_new_map": False,
                  "reason": "No wall-clock allowance remains"}
        save(output, result)
        return result
    log = output.with_suffix(".log")
    started = time.perf_counter()
    flags = dict(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else dict(start_new_session=True)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "SEAT_SOLVER_ROOT": str(ROOT), "SEAT_SOLVER_RESOURCES": str(ROOT / "services/seating"),
           "PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "services/seating/src")))}
    with log.open("wb") as stream:
        process = subprocess.Popen([sys.executable, str(ENTRY), "_worker", "--payload", str(payload_path), "--out", str(output)],
                                   cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, **flags)
        interrupted = None
        try:
            process.wait(timeout=max(.001, deadline - time.perf_counter()))
        except subprocess.TimeoutExpired:
            interrupted = "watchdog_timeout"
            terminate_tree(process)
        except KeyboardInterrupt:
            terminate_tree(process)
            raise
    result = read(output) if output.exists() else {}
    if interrupted or process.returncode or result.get("execution_status") not in ("completed", "unmet_prerequisite"):
        result.update(execution_status=interrupted or "error", returned_new_map=False)
    result.update(worker_elapsed_seconds=time.perf_counter() - started, worker_exit_code=process.returncode,
                  worker_log=log.relative_to(out).as_posix())
    save(output, result)
    return result


def worker(payload, output):
    out = Path(payload["directory"])
    trial = payload.get("job", {})
    try:
        if source_hashes() != read(out / "manifest.json")["environment"]["source_sha256"]:
            raise ValueError("Sources changed after the study snapshot")
        if payload["kind"] == "preflight":
            from .checks import bridge_check, certify_inputs, concurrency_probe, correctness
            require_windows11(payload.get("development", False))
            result = dict(execution_status="completed", passed=True,
                          native_concurrency=concurrency_probe(out / "preflight"),
                          correctness=correctness(out / "preflight/oracles"),
                          regeneration_bridge=bridge_check(out / "preflight/bridge"), inputs=certify_inputs(out))
        elif payload["kind"] == "report":
            from .report import report
            info = report(out, plots=payload.get("plots", True))
            result = dict(execution_status="completed", passed=info["passed"], report=info)
        else:
            from .engine import invoke
            manifest = read(out / "manifest.json")
            raw = read(out / "inputs" / f"{trial['event']}.json")
            if digest(raw) != manifest["inputs"][trial["event"]]["input_sha256"]:
                raise ValueError("Frozen trial input changed")
            request = request_for(raw, trial)
            baseline = read(out / payload["baseline_response"]) if payload.get("baseline_response") else None
            root = out / ("pilot" if trial["batch"].startswith("pilot") else "main")
            response_path = root / "responses" / f"{trial['id']}.json"
            candidate_path = root / "candidates" / f"{trial['id']}.json"
            execution = invoke(request, trial["backend"], out / "stores" / trial["id"] / "plans.sqlite3",
                               root / "native" / trial["id"], baseline=baseline, workers=trial["workers"],
                               checkpoint=lambda candidate: save(candidate_path, candidate))
            save(response_path, execution.pop("response"))
            result = dict(**trial, execution_status="completed", **execution,
                          request_sha256=digest(request), semantic_input_sha256=semantic_hash(request),
                          response_path=response_path.relative_to(out).as_posix(),
                          response_file_sha256=file_digest(response_path),
                          candidate_path=candidate_path.relative_to(out).as_posix() if candidate_path.exists() else None,
                          candidate_file_sha256=file_digest(candidate_path) if candidate_path.exists() else None,
                          native_log_directory=(root / "native" / trial["id"]).relative_to(out).as_posix(),
                          baseline_source=payload.get("baseline_job"), memory=peak_memory())
        save(output, result)
        return 0
    except Exception as exc:
        save(output, {**trial, "execution_status": "error", "passed": False, "returned_new_map": False,
                      "error": str(exc), "error_type": type(exc).__name__, "traceback": traceback.format_exc()})
        return 1


def find_baseline(out, trial, jobs, folder):
    for previous in jobs:
        if (previous["event"], previous["configuration"], previous["backend"]) != (trial["event"], trial["configuration"], trial["origin_backend"]):
            continue
        if previous["origin_backend"]:
            continue
        record = read(out / folder / f"{previous['id']}.json")
        if record.get("returned_new_map"):
            return record
    return None


def run_trial(out, trial, deadline, jobs, pilot=False):
    folder = "pilot/runs" if pilot else "runs"
    output = out / folder / f"{trial['id']}.json"
    payload = dict(kind="trial", directory=str(out), job=trial)
    if trial["origin_backend"]:
        origins = jobs if pilot else [j for j in jobs if j["batch"] == "primary"]
        baseline = find_baseline(out, trial, origins, folder)
        if baseline is None:
            result = {**trial, "execution_status": "unmet_prerequisite", "returned_new_map": False,
                      "reason": "No canonical-complete primary baseline from the origin backend"}
            save(output, result)
            return result
        payload.update(baseline_response=baseline["response_path"], baseline_job=baseline["id"])
    if deadline - time.perf_counter() < trial["budget_seconds"] + 30:
        result = {**trial, "execution_status": "not_started", "returned_new_map": False,
                  "reason": "Insufficient remaining time for the full unchanged allowance and watchdog margin"}
        save(output, result)
        return result
    save(output, {**trial, "execution_status": "running", "returned_new_map": False})
    result = bounded_worker(out, payload, output, min(deadline, time.perf_counter() + trial["budget_seconds"] + 30))
    print(f"{trial['id']}: {result['execution_status']}; new_map={result.get('returned_new_map', False)}", flush=True)
    return result


def defect(record):
    if record["execution_status"] not in ("completed", "unmet_prerequisite"):
        return True
    if record.get("telemetry", {}).get("solver_status") == "INFEASIBLE":
        return True
    return bool(record.get("candidate") and not record["candidate"].get("valid"))


def projection(pilot_rows, elapsed):
    regular, regeneration = [], []
    for row in pilot_rows:
        if row.get("execution_status") != "completed":
            continue
        work = min(row["budget_seconds"], row.get("telemetry", {}).get("shared_work_elapsed_seconds", 0))
        overhead = max(0, row["worker_elapsed_seconds"] - work)
        (regeneration if row["origin_backend"] else regular).append(overhead)
    base = max([5.0, *regular])
    regen = max(regeneration) if regeneration else 2 * base
    overhead = 1.25 * (56 * base + 8 * regen)
    projected = elapsed + 4800 + overhead + REPORT_SECONDS
    return dict(nominal_measured_allowance_seconds=4800, elapsed_preparation_pilot_seconds=elapsed,
                initial_diagnostic_overhead_seconds=base, regeneration_overhead_seconds=regen,
                regeneration_overhead_measured=bool(regeneration), overhead_safety_factor=1.25,
                projected_measured_overhead_seconds=overhead, reporting_reserve_seconds=REPORT_SECONDS,
                projected_runner_seconds=projected, fits=projected <= RUNNER_SECONDS and overhead <= 900,
                method="Full 80-minute measured allowance, max observed overhead (5-second floor), 1.25 safety factor; unobserved regeneration uses twice initial overhead")


def check_consistency(records):
    """Only completed canonical returns are comparable unique maps."""
    groups = {}
    for row in records:
        if not row.get("returned_new_map"):
            continue
        key = (row["event"], row["configuration"])
        value = (row["semantic_input_sha256"], row["physical_map_sha256"], row["candidate"]["objective"])
        if key in groups and groups[key] != value:
            raise ValueError(f"Completed canonical outputs disagree for {key}: modeling/scoring/normalization defect")
        groups[key] = value
        if row["origin_backend"] and row.get("regeneration_same_map") is not True:
            raise ValueError("Unchanged-input regeneration changed a canonical baseline")


def execute(out, mode, development=False, plots=True):
    require_windows11(development if mode == "check" else False)
    started = time.perf_counter()
    deadline = started + RUNNER_SECONDS
    manifest = prepare(out, mode, development)
    manifest["execution_status"] = "preflight"
    save(out / "manifest.json", manifest)
    status, failure = "failed", None
    try:
        gate = bounded_worker(out, dict(kind="preflight", directory=str(out), development=development),
                              out / "preflight.json", min(deadline - REPORT_SECONDS, started + PREFLIGHT_SECONDS))
        if not gate.get("passed") or gate["execution_status"] != "completed":
            raise RuntimeError("Preflight failed; measured jobs were not started. Inspect preflight.json/log")
        if mode == "check":
            status = "validation_only"
            return
        manifest["execution_status"] = "pilot"
        save(out / "manifest.json", manifest)
        pilot_deadline = min(deadline - REPORT_SECONDS, time.perf_counter() + PILOT_SECONDS)
        pilot_rows = []
        for trial in manifest["pilot_jobs"]:
            row = run_trial(out, trial, pilot_deadline, manifest["pilot_jobs"], pilot=True)
            pilot_rows.append(row)
            if defect(row):
                raise RuntimeError(f"Pilot defect/timeout: {trial['id']}")
        check_consistency(pilot_rows)
        estimate = projection(pilot_rows, time.perf_counter() - started)
        save(out / "pilot/projection.json", estimate)
        if not estimate["fits"]:
            raise RuntimeError("Pilot cannot demonstrate the fixed schedule fits; amend protocol explicitly before a fresh run")
        if mode == "pilot":
            status = "pilot_only"
            return
        manifest["execution_status"] = "measured"
        save(out / "manifest.json", manifest)
        records = []
        for trial in manifest["jobs"]:
            if source_hashes() != manifest["environment"]["source_sha256"]:
                raise RuntimeError("Source changed while running; no further jobs launched")
            row = run_trial(out, trial, deadline - REPORT_SECONDS, manifest["jobs"])
            records.append(row)
            if defect(row):
                raise RuntimeError(f"Measured defect/deadline: {trial['id']}; remaining jobs stay explicitly not_started")
            check_consistency(records)
        status = "completed"
    except KeyboardInterrupt:
        status, failure = "interrupted", "Operator interrupted; no resume or silent workload reduction"
    except Exception as exc:
        failure = str(exc)
    finally:
        manifest.update(execution_status=status, ended_at=utcnow(), elapsed_before_reporting_seconds=time.perf_counter() - started,
                        failure=failure, source_hashes_unchanged=source_hashes() == manifest["environment"]["source_sha256"],
                        record_sha256={p.relative_to(out).as_posix(): file_digest(p)
                                       for folder in ("runs", "pilot/runs") for p in (out / folder).glob("*.json")
                                       if not p.name.endswith(".payload.json")},
                        native_log_sha256={p.relative_to(out).as_posix(): file_digest(p) for p in out.rglob("*.log")})
        save(out / "manifest.json", manifest)
        report_deadline = min(deadline - 10, time.perf_counter() + REPORT_SECONDS)
        report_result = bounded_worker(out, dict(kind="report", directory=str(out), plots=plots), out / "report-status.json", report_deadline)
        manifest.update(report_completed=report_result.get("execution_status") == "completed",
                        report_validated=report_result.get("passed", False), runner_elapsed_seconds=time.perf_counter() - started)
        if time.perf_counter() > deadline:
            manifest["runner_cap_reached"] = True
            if status == "completed":
                manifest["execution_status"] = "reporting_exceeded_cap"
        save(out / "manifest.json", manifest)
        if not manifest["report_validated"]:
            raise RuntimeError("Reporting failed or found model/data defects; inspect report-status.json and checks.json")
    if failure:
        raise RuntimeError(failure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("plan", "check", "pilot", "run", "report"):
        command = sub.add_parser(name)
        command.add_argument("--out", type=Path, required=True, help="Fresh evidence directory, except report")
        if name == "check":
            command.add_argument("--development", action="store_true", help="Label non-Windows correctness validation; never measured evidence")
        if name in ("check", "pilot", "run", "report"):
            command.add_argument("--no-plots", action="store_true")
    worker_command = sub.add_parser("_worker", help=argparse.SUPPRESS)
    worker_command.add_argument("--payload", type=Path, required=True)
    worker_command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "_worker":
            return worker(read(args.payload), args.out)
        out = args.out.resolve()
        if args.mode == "plan":
            manifest = prepare(out, "plan")
            print(json.dumps(dict(out=str(out), measured_jobs=len(manifest["jobs"]),
                                  batch_counts=dict(Counter(j["batch"] for j in manifest["jobs"])), solver_executions=0), indent=2))
        elif args.mode == "report":
            from .report import report
            print(json.dumps(report(out, plots=not args.no_plots), indent=2))
        else:
            execute(out, args.mode, getattr(args, "development", False), plots=not args.no_plots)
        return 0
    except Exception as exc:
        print(f"Study B stopped: {exc}", file=sys.stderr)
        return 1
