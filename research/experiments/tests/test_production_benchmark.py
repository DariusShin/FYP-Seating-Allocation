"""Study B protocol, independent oracles, adoption and runner regressions."""

import copy
from collections import Counter
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from research.experiments.production_benchmark import backends, engine, protocol, report, runner
from research.experiments.production_benchmark.checks import bridge_check, correctness, oracle, tiny_cases
from seat_solver.production.production_scoring import options


def test_fixed_schedule_and_predeclared_diagnostics():
    jobs = protocol.schedule()
    assert Counter(j["batch"] for j in jobs) == {"primary": 48, "diagnostic": 8, "regeneration": 8}
    assert len({j["id"] for j in jobs}) == 64
    assert sum(j["budget_seconds"] for j in jobs) == 4800
    assert jobs == protocol.schedule()
    assert all(j["backend"] == "cp_sat" for j in jobs if j["batch"] == "regeneration")
    assert {(j["event"], j["configuration"]) for j in jobs if j["batch"] == "diagnostic"} == set(protocol.DIAGNOSTIC)
    assert sum(j["permutation"] for j in jobs) == 16
    assert sum(j["budget_seconds"] for j in protocol.pilot_schedule()) == 600


def test_semantic_identity_preserves_preference_ranking_and_ignores_incidental_order():
    raw = tiny_cases()["singles"]
    job = protocol.job("primary", "tiny", "current", "cp_sat", 60, 3, True)
    first = protocol.request_for(raw, job | {"permutation": False})
    permuted = protocol.request_for(raw, job)
    assert protocol.digest(first) != protocol.digest(permuted)
    assert protocol.semantic_hash(first) == protocol.semantic_hash(permuted)
    changed = copy.deepcopy(first)
    changed["preferences"] = protocol.preferences("reversed")
    assert protocol.semantic_hash(first) != protocol.semantic_hash(changed)
    changed = copy.deepcopy(first)
    changed["solver"]["max_time_seconds"] = 180
    changed["generation_mode"] = "REGENERATE_DRAFT"
    assert protocol.semantic_hash(first) == protocol.semantic_hash(changed)


def test_physical_map_hash_excludes_metadata_and_order_but_detects_moves():
    a = [{"participant_id": "A", "seat_ids": ["S2", "S1"], "generated_at": "today"},
         {"participant_id": "B", "seat_ids": ["S3"]}]
    b = [{"participant_id": "B", "seat_ids": ["S3"]}, {"participant_id": "A", "seat_ids": ["S1", "S2"]}]
    assert protocol.map_hash(a) == protocol.map_hash(b)
    b[0]["seat_ids"] = ["S4"]
    assert protocol.map_hash(a) != protocol.map_hash(b)
    with pytest.raises(ValueError, match="Repeated registration"):
        protocol.map_hash(a + [a[0]])


@pytest.mark.parametrize("status,value,bound,native,expected", [
    ("OPTIMAL", 10, 10, {}, True), ("OPTIMAL", 10, 9, {}, False),
    ("FEASIBLE", 10, 10, {}, False), ("OPTIMAL", 10, float("inf"), {}, False),
    ("OPTIMAL", 10, 10, {"gap_limit_reached": True}, False),
])
def test_api_optimal_is_not_a_proof_by_itself(status, value, bound, native, expected):
    assert backends.proof_established(status, value, bound, native) == expected


def test_native_concurrency_log_requires_distinct_launched_solvers():
    text = "\n".join(f"starting solve in concurrent solver 'scip-{n}'" for n in range(1, 9))
    text += "\nSCIP Status : solving was interrupted [gap limit reached]\n"
    parsed = backends.parse_scip_log(text + text)
    assert parsed["observed_concurrent_solvers"] == 8
    assert parsed["gap_limit_reached"]
    assert backends.parse_scip_log("SetNumThreads(8) returned true")["observed_concurrent_solvers"] == 0


def test_production_encodings_and_canonical_maps_match_independent_oracles(tmp_path):
    result = correctness(tmp_path)
    assert result["passed"] and result["executions"] == 72
    assert all(r["canonical_match"] for r in result["oracle_cases"])


def test_real_service_regeneration_and_rejected_candidate_preservation(tmp_path):
    from seat_solver.production import service
    original = service.solve
    result = bridge_check(tmp_path)
    assert result["passed"] and len(result["links"]) == 2
    assert result["forced_incomplete_canonical_preserves_baseline"]
    assert service.solve is original


def clock_backend(request, expected, clock, durations, seen):
    class Stub:
        weighted = "weighted"
        canonical = {p["participant_id"]: p["participant_id"] for p in request["participants"]}
        options = {p["participant_id"]: options(request, p) for p in request["participants"]}

        def __init__(self, req, cfg):
            self.expression = None

        def configure(self, expression, seconds, workers):
            self.expression = expression
            seen.append((seconds, workers))

        def run(self, log):
            clock[0] += next(durations)

        def extract(self, expression, log):
            value = expected["objective"] if expression == "weighted" else 0
            return dict(api_status="OPTIMAL", native_termination="OPTIMAL", value=value, best_bound=value,
                        proven=True, absolute_gap=0, relative_gap=0,
                        choices={a["participant_id"]: a["seat_ids"] for a in expected["placements"]})

        def fix(self, expression, value):
            pass
    return Stub


def test_one_shared_deadline_is_not_restarted_for_canonical_stages(monkeypatch, tmp_path):
    request = tiny_cases()["singles"]
    request["preferences"] = protocol.preferences("current")
    request["solver"].update(num_search_workers=8, max_time_seconds=3, canonicalize=True)
    expected = oracle(request)
    clock, seen = [0.0], []
    monkeypatch.setattr(engine.time, "perf_counter", lambda: clock[0])
    monkeypatch.setitem(backends.BUILDERS, "clock", clock_backend(request, expected, clock, iter((2, 2)), seen))
    solve = engine.AllocationFunction("clock", tmp_path)
    response = solve(request)
    assert [seconds for seconds, _ in seen] == [3, 1]
    assert [workers for _, workers in seen] == [8, 1]
    assert response["status"] == "error" and solve.candidate["valid"]
    assert not solve.telemetry["canonicalization_complete"]


def test_late_canonical_completion_is_recorded_but_not_adopted(monkeypatch, tmp_path):
    request = tiny_cases()["singles"]
    request["participants"] = request["participants"][:1]
    request["preferences"] = protocol.preferences("current")
    request["solver"].update(num_search_workers=8, max_time_seconds=3, canonicalize=True)
    expected = oracle(request)
    clock, seen = [0.0], []
    monkeypatch.setattr(engine.time, "perf_counter", lambda: clock[0])
    monkeypatch.setitem(backends.BUILDERS, "clock", clock_backend(request, expected, clock, iter((2, 2)), seen))
    solve = engine.AllocationFunction("clock", tmp_path)
    response = solve(request)
    assert solve.telemetry["canonicalization_complete"] and not solve.telemetry["within_shared_allowance"]
    assert response["error"]["code"] == "ALLOCATION_ALLOWANCE_EXCEEDED"
    assert report.outcome(dict(execution_status="completed", candidate=solve.candidate, telemetry=solve.telemetry)) == "late_canonical"


def test_regeneration_never_substitutes_diagnostic_baseline(tmp_path):
    jobs = protocol.schedule()
    for trial in jobs:
        record = trial | {"execution_status": "completed", "returned_new_map": trial["batch"] == "diagnostic", "response_path": "not-used.json"}
        protocol.save(tmp_path / "runs" / f"{trial['id']}.json", record)
    regen = next(j for j in jobs if j["batch"] == "regeneration" and j["event"] == "heavy-mixed")
    row = runner.run_trial(tmp_path, regen, time.perf_counter()+1, jobs)
    assert row["execution_status"] == "unmet_prerequisite"
    assert not row["returned_new_map"]


def test_projection_counts_full_allowances_and_missing_pilot_regeneration():
    trial = protocol.pilot_schedule()[0]
    rows = [trial | {"execution_status": "completed", "worker_elapsed_seconds": 184,
                     "telemetry": {"shared_work_elapsed_seconds": 180}}]
    estimate = runner.projection(rows, 1000)
    assert estimate["nominal_measured_allowance_seconds"] == 4800
    assert estimate["fits"] and not estimate["regeneration_overhead_measured"]
    assert not runner.projection(rows, 3000)["fits"]
    rows[0]["worker_elapsed_seconds"] = 220
    assert not runner.projection(rows, 100)["fits"]


def test_watchdog_terminates_native_worker_process(tmp_path, monkeypatch):
    # Kill before it can import or start any solver; retained job stays a timeout.
    output = tmp_path / "timeout.json"
    protocol.save(output, {"execution_status": "running", "returned_new_map": False})
    result = runner.bounded_worker(tmp_path, {"kind": "preflight", "directory": str(tmp_path)}, output,
                                   time.perf_counter() + .01)
    assert result["execution_status"] == "watchdog_timeout"
    assert result["worker_exit_code"] is not None
    assert not result["returned_new_map"]


def test_non_windows_cannot_start_measurement(monkeypatch):
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="posix"))
    with pytest.raises(RuntimeError, match="Windows 11"):
        runner.require_windows11()
    runner.require_windows11(development=True)


def test_windows_watchdog_uses_native_tree_kill(monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(runner.subprocess, "run", lambda args, **kwargs: calls.append(args))
    process = SimpleNamespace(pid=1234, poll=lambda: None, kill=lambda: calls.append("kill"),
                              wait=lambda **kwargs: calls.append("wait"))
    runner.terminate_tree(process)
    assert calls == [["taskkill", "/PID", "1234", "/T", "/F"], "kill", "wait"]


def test_insufficient_time_does_not_shorten_and_launch_a_trial(tmp_path, monkeypatch):
    trial = protocol.schedule()[0]
    monkeypatch.setattr(runner, "bounded_worker", lambda *args, **kwargs: pytest.fail("Shortened run launched"))
    row = runner.run_trial(tmp_path, trial, time.perf_counter()+5, protocol.schedule())
    assert row["execution_status"] == "not_started"
    assert row["budget_seconds"] == 60


def test_plan_and_report_do_not_run_optimization_or_generate_fake_figures(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Plan/report attempted a solve")
    monkeypatch.setattr(backends.CPSAT, "run", forbidden)
    monkeypatch.setattr(backends.SCIP, "run", forbidden)
    out = tmp_path / "plan"
    manifest = runner.prepare(out, "plan")
    assert len(manifest["inputs"]) == 8
    result = report.report(out)
    assert result["passed"] and result["completed_records"] == 0
    assert result["figures"] == 0 and not (out / "figures").exists()
    assert sum(r["scheduled"] for r in protocol.read(out / "summary.json")["coverage"]) == 64
    with pytest.raises(FileExistsError):
        runner.prepare(out, "plan")


def test_completed_canonical_disagreement_is_a_defect_not_a_winner():
    base = dict(event="heavy-mixed", configuration="current", returned_new_map=True,
                semantic_input_sha256="same", physical_map_sha256="map-a", candidate={"objective": 12}, origin_backend=None)
    with pytest.raises(ValueError, match="disagree"):
        runner.check_consistency([base, base | {"physical_map_sha256": "map-b"}])


def test_fresh_trial_worker_and_cross_backend_regeneration_artifacts(tmp_path):
    # Genuine tiny correctness calls, explicitly outside the measured schedule.
    raw = tiny_cases()["singles"]
    protocol.save(tmp_path / "inputs/tiny.json", raw)
    protocol.save(tmp_path / "manifest.json", dict(development_only=True,
        environment={"source_sha256": runner.source_hashes()}, inputs={"tiny": {"input_sha256": protocol.digest(raw)}}))
    first = protocol.job("development", "tiny", "current", "scip", 60)
    initial = runner.bounded_worker(tmp_path, dict(kind="trial", directory=str(tmp_path), job=first),
                                    tmp_path / "initial.json", time.perf_counter()+15)
    assert initial["execution_status"] == "completed" and initial["returned_new_map"]
    assert protocol.file_digest(tmp_path / initial["response_path"]) == initial["response_file_sha256"]
    assert protocol.file_digest(tmp_path / initial["candidate_path"]) == initial["candidate_file_sha256"]
    second = protocol.job("development_regeneration", "tiny", "current", "cp_sat", 60, origin="scip")
    regenerated = runner.bounded_worker(tmp_path, dict(kind="trial", directory=str(tmp_path), job=second,
        baseline_response=initial["response_path"], baseline_job=initial["id"]), tmp_path / "regenerated.json", time.perf_counter()+15)
    assert regenerated["execution_status"] == "completed" and regenerated["returned_new_map"]
    assert regenerated["regeneration_same_map"]
    assert regenerated["candidate"]["objective"] == initial["candidate"]["objective"]
    assert regenerated["physical_map_sha256"] == initial["physical_map_sha256"]
    assert sum(report.phases(regenerated).values()) == pytest.approx(regenerated["complete_service_return_seconds"])


def test_full_runner_bookkeeping_without_measured_solves(tmp_path, monkeypatch):
    # Stub wall-clock results only; fixture stays explicitly DEVELOPMENT ONLY.
    calls = []
    monkeypatch.setattr(runner, "require_windows11", lambda *args, **kwargs: None)

    def simulated(out, payload, output, deadline):
        if payload["kind"] != "trial":
            row = dict(execution_status="completed", passed=True, test_stub=True)
        else:
            trial = payload["job"]
            calls.append(trial)
            row = trial | dict(execution_status="completed", returned_new_map=False,
                telemetry={"shared_work_elapsed_seconds": trial["budget_seconds"]},
                worker_elapsed_seconds=trial["budget_seconds"]+2, test_stub=True)
        protocol.save(output, row)
        return row

    monkeypatch.setattr(runner, "bounded_worker", simulated)
    out = tmp_path / "DEVELOPMENT-SCHEDULER-TEST"
    runner.execute(out, "run", development=True, plots=False)
    manifest = protocol.read(out / "manifest.json")
    assert manifest["development_only"] and manifest["execution_status"] == "completed"
    assert Counter(j["batch"] for j in calls) == {"pilot": 4, "primary": 48, "diagnostic": 8}
    main = [protocol.read(out / "runs" / f"{j['id']}.json") for j in manifest["jobs"]]
    assert sum(r["execution_status"] == "unmet_prerequisite" for r in main) == 8
    assert not any(r["execution_status"] == "not_started" for r in main)


def test_all_five_plot_layouts_with_explicitly_synthetic_fixture(tmp_path):
    # Layout-only mocks deliberately do not pass the production data auditor.
    # Their penalty 999 is not research evidence; only PNGs are rendered here.
    protocol.save(tmp_path / "manifest.json", dict(study="LAYOUT-TEST-NOT-STUDY-B", development_only=True))
    request = protocol.read(protocol.SOURCE / "inputs/heavy-mixed.json")
    witness = protocol.read(protocol.SOURCE / "witnesses/heavy-mixed.json")["placements"]
    protocol.save(tmp_path / "inputs/heavy-mixed.json", request)
    records = [j | dict(execution_status="not_started", returned_new_map=False) for j in protocol.schedule()]
    durations = dict(normalization=1, model_build=2, weighted_search=3, canonical_search=4,
                     extraction=.2, model_updates=.3, validation_scoring=.4, format_response=.1)
    for row in records:
        if row["repetition"] == 1 and row["batch"] in ("primary", "diagnostic"):
            accepted = not (row["backend"] == "scip" and row["batch"] == "primary" and row["event"] == "heavy-mixed")
            row.update(execution_status="completed", returned_new_map=accepted,
                complete_service_return_seconds=12.5, physical_map_sha256="TEST-NOT-EVIDENCE",
                candidate=dict(valid=True, objective=999, placements=witness),
                telemetry=dict(phases=[dict(name=k, duration_seconds=v) for k,v in durations.items()],
                    function_return_seconds=11.5, unclassified_function_overhead_seconds=.5,
                    canonicalization_complete=accepted, weighted_proven=True,
                    weighted_proof_reported_seconds=4, canonical_complete_seconds=9))
    names = report.plots(tmp_path, records, report.comparisons(records), formats=("png",))
    assert len(names) == 5
    assert all((tmp_path / "figures" / f"{name}.png").stat().st_size > 1000 for name in names)
    assert not list(tmp_path.rglob("*.pdf"))
    # Preserve a deterministic copy for visual review outside evidence folders.
    import os
    import shutil
    if os.environ.get("STUDY_B_LAYOUT_QA"):
        target = Path(os.environ["STUDY_B_LAYOUT_QA"])
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copyfile(tmp_path / "figures" / f"{name}.png", target / f"{name}.png")
