"""Study B attempt 3: fixed design, valid-map adoption and evidence checks."""

import copy
from collections import Counter
import time

import pytest

from research.experiments.production_benchmark import backends, engine, protocol, report, runner
from research.experiments.production_benchmark.checks import bridge_check, correctness, oracle, tiny_cases


def test_main_and_sweep_designs_are_fixed_and_separate():
    jobs = protocol.schedule()
    assert Counter(j["batch"] for j in jobs) == {"diagnostic_5": 48, "diagnostic_30": 48, "primary": 48}
    assert len({j["id"] for j in jobs}) == 144
    assert sum(j["budget_seconds"] for j in jobs) == 4560
    assert sum(j["permutation"] for j in jobs) == 48
    assert all(j["workers"] == 8 for j in jobs)
    sweep = protocol.sweep_schedule()
    assert len(sweep) == 96 and len({j["id"] for j in sweep}) == 96
    assert sum(j["budget_seconds"] for j in sweep) == 5760
    assert Counter(j["workers"] for j in sweep) == {1: 24, 2: 24, 4: 24, 8: 24}
    assert {j["event"] for j in sweep} == {event for event, _ in protocol.SWEEP}
    assert all(j["batch"] == "sweep" for j in sweep)


def test_semantic_identity_and_request_contract():
    raw = tiny_cases()["singles"]
    trial = protocol.job("primary", "tiny", "current", "cp_sat", 60, 3, True)
    first = protocol.request_for(raw, trial | {"permutation": False})
    permuted = protocol.request_for(raw, trial)
    assert protocol.digest(first) != protocol.digest(permuted)
    assert protocol.semantic_hash(first) == protocol.semantic_hash(permuted)
    assert first["generation_mode"] == "INITIAL"
    assert not first["solver"]["canonicalize"]
    changed = copy.deepcopy(first)
    changed["preferences"] = protocol.preferences("reversed")
    assert protocol.semantic_hash(first) != protocol.semantic_hash(changed)
    changed = copy.deepcopy(first)
    changed["solver"]["max_time_seconds"] = 5
    assert protocol.semantic_hash(first) == protocol.semantic_hash(changed)


@pytest.mark.parametrize("status,value,bound,native,expected", [
    ("OPTIMAL", 10, 10, {}, True), ("OPTIMAL", 10, 9, {}, False),
    ("FEASIBLE", 10, 10, {}, False), ("OPTIMAL", 10, float("inf"), {}, False),
    ("OPTIMAL", 10, 10, {"gap_limit_reached": True}, False),
])
def test_proof_requires_native_status_and_matching_bound(status, value, bound, native, expected):
    assert backends.proof_established(status, value, bound, native) == expected


def test_scip_native_log_counts_distinct_solver_launches():
    log = "\n".join(f"starting solve in concurrent solver 'scip-{n}'" for n in range(1, 9))
    assert backends.parse_scip_log(log + log)["observed_concurrent_solvers"] == 8
    assert backends.parse_scip_log("SetNumThreads(8) returned true")["observed_concurrent_solvers"] == 0


def test_tiny_encodings_match_independent_optimum_without_map_identity(tmp_path):
    result = correctness(tmp_path)
    assert result["passed"] and result["executions"] == 72
    assert all(r["valid_and_optimal"] for r in result["oracle_cases"])


def test_service_adopts_valid_unproved_and_rejects_invalid(tmp_path):
    from seat_solver.production import service
    original = service.solve
    result = bridge_check(tmp_path)
    assert result["passed"] and result["valid_unproved_adopted"] and result["invalid_candidate_rejected"]
    assert len(result["links"]) == 2
    assert service.solve is original


def clock_backend(expected, clock, duration, proven):
    class Stub:
        weighted = "weighted"

        def __init__(self, request, cfg):
            pass

        def configure(self, expression, seconds, workers):
            self.configured = (seconds, workers)

        def run(self, log):
            clock[0] += duration

        def extract(self, expression, log):
            value = expected["objective"]
            return dict(api_status="OPTIMAL" if proven else "FEASIBLE", value=value,
                        best_bound=value if proven else value - 1, proven=proven,
                        absolute_gap=0 if proven else 1, relative_gap=0 if proven else 1/max(1, value),
                        choices={a["participant_id"]: a["seat_ids"] for a in expected["placements"]})
    return Stub


@pytest.mark.parametrize("duration,proven,status", [(2, False, "FEASIBLE"), (2, True, "OPTIMAL"), (4, False, "error")])
def test_shared_allowance_and_feasible_return(monkeypatch, tmp_path, duration, proven, status):
    request = tiny_cases()["singles"]
    request["preferences"] = protocol.preferences("current")
    request["solver"].update(num_search_workers=8, max_time_seconds=3, canonicalize=False)
    expected = oracle(request)
    clock = [0.0]
    monkeypatch.setattr(engine.time, "perf_counter", lambda: clock[0])
    monkeypatch.setitem(engine.BUILDERS, "cp_sat", clock_backend(expected, clock, duration, proven))
    function = engine.AllocationFunction("cp_sat", tmp_path)
    response = function(request)
    assert function.candidate["valid"]
    assert function.telemetry["weighted_proven"] == proven
    assert len(function.telemetry["stages"]) == 1
    if status == "error":
        assert response["error"]["code"] == "ALLOCATION_ALLOWANCE_EXCEEDED"
        assert not function.telemetry["within_shared_allowance"]
    else:
        assert response["status"] == "success" and response["solver"]["status"] == status
        assert not response["solver"]["canonicalization_complete"]


def test_consistency_allows_different_optimal_maps_but_not_different_minima():
    base = dict(execution_status="completed", event="heavy-mixed", configuration="current",
                returned_new_map=True, semantic_input_sha256="same", physical_map_sha256="map-a",
                candidate={"objective": 12}, telemetry={"weighted_proven": True})
    runner.check_consistency([base, base | {"physical_map_sha256": "map-b"}])
    with pytest.raises(ValueError, match="Proven weighted minima disagree"):
        runner.check_consistency([base, base | {"candidate": {"objective": 13}}])


def test_projection_uses_scheduled_allowances_and_pilot_overhead():
    row = protocol.pilot_schedule()[0] | dict(execution_status="completed", worker_elapsed_seconds=9,
                                                telemetry={"shared_work_elapsed_seconds": 5})
    estimate = runner.projection([row], 100, protocol.schedule())
    assert estimate["nominal_measured_allowance_seconds"] == 4560 and estimate["fits"]
    assert runner.projection([row], 3000, protocol.schedule())["fits"] is False
    assert runner.projection([row], 100, protocol.sweep_schedule())["nominal_measured_allowance_seconds"] == 5760


def test_plan_and_report_have_no_measured_figures(tmp_path, monkeypatch):
    monkeypatch.setattr(backends.CPSAT, "run", lambda *args: pytest.fail("Plan attempted a solve"))
    monkeypatch.setattr(backends.SCIP, "run", lambda *args: pytest.fail("Plan attempted a solve"))
    out = tmp_path / "plan"
    manifest = runner.prepare(out, "plan")
    assert len(manifest["inputs"]) == 8 and not manifest["canonicalize"]
    result = report.report(out)
    assert result["passed"] and result["completed_records"] == 0 and result["figures"] == 0
    assert sum(r["scheduled"] for r in protocol.read(out / "summary.json")["coverage"]) == 144
    with pytest.raises(FileExistsError):
        runner.prepare(out, "plan")


def test_real_subprocess_record_passes_saved_evidence_auditor(tmp_path):
    raw = tiny_cases()["singles"]
    trial = protocol.job("development", "tiny", "current", "scip", 10)
    protocol.save(tmp_path / "inputs/tiny.json", raw)
    manifest = dict(environment={"source_sha256": runner.source_hashes()}, jobs=[trial],
                    inputs={"tiny": {"input_sha256": protocol.digest(raw)}})
    protocol.save(tmp_path / "manifest.json", manifest)
    result = runner.bounded_worker(tmp_path, {"kind": "trial", "directory": str(tmp_path), "job": trial},
                                   tmp_path / "runs" / f"{trial['id']}.json", time.perf_counter() + 20)
    assert result["execution_status"] == "completed" and result["returned_new_map"]
    assert result["pending_candidate_path"] != result["candidate_path"]
    assert protocol.file_digest(tmp_path / result["pending_candidate_path"]) == result["pending_candidate_file_sha256"]
    assert protocol.read(tmp_path / result["pending_candidate_path"])["validation_pending"]
    audited = report.verify_records(tmp_path, [result], manifest)
    assert audited["passed"] and audited["candidates_independently_rescored"] == 1
    pending = tmp_path / result["pending_candidate_path"]
    pending.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum changed"):
        report.verify_records(tmp_path, [result], manifest)


def test_json_save_retries_windows_sharing_lock_without_losing_atomicity(tmp_path, monkeypatch):
    target = tmp_path / "candidate.json"
    protocol.save(target, {"generation": "pending"})
    original_replace = protocol.os.replace
    calls, sleeps = [], []

    class SharingLock(PermissionError):
        winerror = 5

    def flaky_replace(source, destination):
        calls.append((source, destination))
        if len(calls) == 1:
            assert protocol.read(target) == {"generation": "pending"}
            raise SharingLock("Transient Windows sharing violation")
        return original_replace(source, destination)

    monkeypatch.setattr(protocol.os, "replace", flaky_replace)
    monkeypatch.setattr(protocol.time, "sleep", sleeps.append)
    protocol.save(target, {"generation": "validated"})
    assert len(calls) == 2 and len(sleeps) == 1
    assert calls[0][0] == calls[1][0] and calls[0][1] == target
    assert protocol.read(target) == {"generation": "validated"}


def test_json_save_keeps_last_good_artifact_on_persistent_denial(tmp_path, monkeypatch):
    target = tmp_path / "candidate.json"
    protocol.save(target, {"generation": "pending"})

    class SharingLock(PermissionError):
        winerror = 32

    monkeypatch.setattr(protocol.os, "replace", lambda *args: (_ for _ in ()).throw(SharingLock("locked")))
    monkeypatch.setattr(protocol.time, "sleep", lambda seconds: None)
    with pytest.raises(SharingLock):
        protocol.save(target, {"generation": "validated"})
    assert protocol.read(target) == {"generation": "pending"}
    assert len(list(tmp_path.glob(".candidate.json.*.tmp"))) == 1


def test_sweep_plan_keeps_separate_denominator(tmp_path):
    out = tmp_path / "sweep"
    manifest = runner.prepare(out, "plan-sweep")
    assert len(manifest["jobs"]) == 96
    result = report.report(out)
    assert result["scheduled_records"] == 96 and result["figures"] == 0
    assert "Separate worker/thread sensitivity" in protocol.read(out / "summary.json")["selection_conclusion"]


@pytest.mark.parametrize("mode,expected,cap", [("run", 144, 7200), ("sweep", 96, 9000)])
def test_complete_runner_bookkeeping_without_measured_solves(tmp_path, monkeypatch, mode, expected, cap):
    monkeypatch.setattr(runner, "require_windows11", lambda *args, **kwargs: None)
    launched = []

    def simulated(out, payload, output, deadline):
        if payload["kind"] == "trial":
            trial = payload["job"]
            launched.append(trial)
            row = trial | dict(execution_status="completed", returned_new_map=False,
                               semantic_input_sha256=f"{trial['event']}:{trial['configuration']}",
                               telemetry={"shared_work_elapsed_seconds": trial["budget_seconds"]},
                               worker_elapsed_seconds=trial["budget_seconds"] + 2)
        else:
            row = dict(execution_status="completed", passed=True)
        protocol.save(output, row)
        return row

    monkeypatch.setattr(runner, "bounded_worker", simulated)
    out = tmp_path / mode
    runner.execute(out, mode, plots=False)
    manifest = protocol.read(out / "manifest.json")
    assert manifest["execution_status"] == "completed" and manifest["runner_cap_seconds"] == cap
    assert len(manifest["jobs"]) == expected and len([j for j in launched if j["batch"] != "pilot"]) == expected
    assert all(protocol.read(out / "runs" / f"{j['id']}.json")["execution_status"] == "completed" for j in manifest["jobs"])


def test_insufficient_time_keeps_full_allowance(tmp_path, monkeypatch):
    trial = protocol.schedule()[0]
    monkeypatch.setattr(runner, "bounded_worker", lambda *args, **kwargs: pytest.fail("Shortened trial launched"))
    result = runner.run_trial(tmp_path, trial, time.perf_counter() + 1)
    assert result["execution_status"] == "not_started" and result["budget_seconds"] == 5


def test_outcome_separates_valid_unproved_from_missing():
    row = dict(execution_status="completed", candidate={"valid": True}, returned_new_map=True,
               telemetry={"weighted_proven": False})
    assert report.outcome(row) == "feasible_map"
    assert report.outcome(row | {"telemetry": {"weighted_proven": True}}) == "optimal_map"
    assert report.outcome(row | {"returned_new_map": False}) == "no_map"
    assert report.outcome(row | {"execution_status": "not_started"}) == "not_started"


@pytest.mark.parametrize("sweep,expected", [(False, 3), (True, 1)])
def test_attempt3_figure_layouts_use_separate_denominators(tmp_path, sweep, expected):
    protocol.save(tmp_path / "manifest.json", {"development_only": True})
    jobs = protocol.sweep_schedule() if sweep else protocol.schedule()
    rows = [j | {"execution_status": "not_started", "returned_new_map": False} for j in jobs]
    rows[0].update(execution_status="completed", complete_service_return_seconds=1.2)
    coverage, paired = report.make_tables(tmp_path, rows)
    names = report.plots(tmp_path, rows, coverage, paired, formats=("png",))
    assert len(names) == expected
    assert all((tmp_path / "figures" / f"{name}.png").stat().st_size > 1000 for name in names)
