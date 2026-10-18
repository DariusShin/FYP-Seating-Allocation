import copy
from collections import Counter
import csv
import time

import pytest

from research.experiments.solver_benchmark.cases import inventory, schedule
from research.experiments.solver_benchmark.checks import correctness, tiny
from research.experiments.solver_benchmark.common import (CONFIGS, compact_weights, digest, execute, preferences, prepare, read, save)
from research.experiments.solver_benchmark.report import compare, report
from research.experiments.solver_benchmark.runner import bounded_worker, job_request


def test_mutated_frozen_input_is_rejected(tmp_path):
    request = tiny()
    path = tmp_path / "event.json"
    save(path, request)
    payload = {"input": str(path), "input_sha256": digest(request),
               "job": {"configuration": "current", "budget_seconds": 5}}
    assert job_request(payload)["solver"]["max_time_seconds"] == 5
    request["participants"][0]["requires_accessible_seat"] = True
    save(path, request)
    with pytest.raises(ValueError, match="Frozen event input changed"):
        job_request(payload)
from seat_solver.production.production_validator import validate_placements


def test_exact_solvers_match_exhaustive_physical_oracles():
    result = correctness()
    assert result["passed"]
    assert len(result["cases"]) == 108
    assert result["checked_option_vectors"] > 0


def test_certified_inventory_and_manifest():
    events = inventory()
    assert len(events) == 13
    assert len({e["seed"] for e in events.values()}) == 2
    for event in events.values():
        assert validate_placements(event["request"], event["witness"]["placements"])["passed"]
    heavy = events["heavy-mixed"]["request"]
    counts = Counter(p["contribution_tier"] for p in heavy["participants"])
    assert counts == {"EMPEROR": 99, "MERIT": 19, "BODHI": 13}
    assert 2 * counts["EMPEROR"] + counts["MERIT"] + counts["BODHI"] == 230
    jobs = schedule()
    assert Counter(j["batch"] for j in jobs) == {"primary": 156, "budget_sensitivity": 72, "prototype": 4}
    assert len({j["id"] for j in jobs}) == 232
    assert sum(j["budget_seconds"] for j in jobs if j["batch"] != "prototype") == 4020
    assert jobs == schedule()
    assert all(j["configuration"] != "disabled" for j in jobs if j["batch"] == "budget_sensitivity")


def test_shared_weights_and_disabled_control():
    request = tiny()
    expected = {"current": (4, 3, 2), "reversed": (2, 3, 4), "two": (4, 0, 3), "disabled": (0, 0, 0)}
    for config in CONFIGS:
        request["preferences"] = preferences(config)
        assert tuple(compact_weights(request).values()) == expected[config]


def test_greedy_never_uses_exact_solver_or_reports_proof(monkeypatch):
    from research.experiments.solver_benchmark import adapters
    def forbidden(*args, **kwargs):
        raise AssertionError("Greedy called an exact solver")
    monkeypatch.setattr(adapters, "cp_adapter", forbidden)
    monkeypatch.setattr(adapters, "scip_adapter", forbidden)
    successful = execute(tiny(), "greedy", 2)
    assert successful["valid"] and successful["best_bound"] is None
    impossible = tiny(0, 1, 0)
    impossible["participants"][0]["requires_accessible_seat"] = True
    failed = execute(impossible, "greedy", 2)
    assert failed["solver_status"] == "CONSTRUCTION_FAILED"
    assert not failed["valid"] and failed["placements"] is None


def test_tampered_placements_fail_external_validation():
    request = tiny()
    result = execute(request, "cp_sat", 2)
    tampered = copy.deepcopy(result["placements"])
    tampered[1]["seat_ids"] = tampered[0]["seat_ids"]
    assert not validate_placements(request, tampered)["passed"]


def test_infeasible_capacity_and_absent_tiers():
    # The last tiny row has two available seats; demand over capacity cannot be relaxed.
    request = tiny(0, 3, 0, ((1, 9), (1, 10)))
    for method in ("cp_sat", "scip"):
        assert execute(request, method, 2)["solver_status"] == "INFEASIBLE"


def test_outer_watchdog_and_atomic_record(tmp_path):
    output = tmp_path / "killed.json"
    result = bounded_worker({"kind": "correctness"}, output, time.perf_counter() + .01)
    assert result["interrupted_by_deadline"]
    assert result["worker_exit_code"] is not None
    assert not result["valid"]
    assert read(output) == result
    assert not list(tmp_path.glob("*.tmp"))


def test_report_missing_pairs_and_unexecuted_budgets(tmp_path):
    save(tmp_path / "manifest.json", {"protocol": "unit-test-only", "mode": "plan", "execution_status": "planned", "jobs": schedule()})
    report(tmp_path)
    summary = read(tmp_path / "summary.json")
    assert all(g["valid_rate_attempted"] is None for g in summary["groups"])
    assert all(c["new_valid_map"] is None and c["cost_difference_per_registration"] is None for c in summary["budget_contrasts"])
    assert all(h["median_difference_per_registration"] is None for h in summary["H1_and_RQ1"])
    assert all(h["interpretation"] == "not_estimable" for h in summary["H1_and_RQ1"])
    with pytest.raises(ValueError, match="Main figures require"):
        report(tmp_path, plots=True)


def test_pilot_report_keeps_development_separate_and_exports_memory(tmp_path):
    from research.experiments.solver_benchmark.cases import pilot_schedule
    save(tmp_path / "manifest.json", {"mode": "pilot"})
    job = pilot_schedule()[0]
    save(tmp_path / "pilot/runs" / f"{job['id']}.json",
         {**job, "execution_status": "completed", "valid": False, "solver_status": "UNKNOWN",
          "timing": {"search_seconds": 5}, "memory": {"worker_peak_rss_bytes": 123456}})
    report(tmp_path)
    assert not (tmp_path / "summary.json").exists()
    summary = read(tmp_path / "pilot/summary.json")
    assert (summary["planned"], summary["attempted"], summary["completed"], summary["validated"]) == (19, 1, 1, 0)
    with (tmp_path / "pilot/tables/run-records.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["worker_peak_rss_bytes"] == "123456"
    assert rows[1]["objective"] == ""
    assert "excluded from H1/RQ1/H3" in (tmp_path / "pilot/results.md").read_text()


def test_cost_comparison_does_not_compare_different_weights():
    a = {"execution_status": "completed", "valid": True, "weights": {"a": 1}, "registrations": 2, "objective": 10}
    b = {**a, "objective": 12}
    assert compare(a, b) == -1
    assert compare(a, {**b, "valid": False}) is None
    with pytest.raises(ValueError):
        compare(a, {**b, "weights": {"a": 2}})


def test_partial_report_plots_preserve_missing_results(tmp_path):
    # A renderer fixture with NO invented observations; every planned job is missing.
    # This checks that an interrupted study produces explicit gaps/no-map panels.
    jobs = schedule()
    save(tmp_path / "manifest.json", {"protocol": "unit-test-only", "mode": "run", "execution_status": "stopped", "jobs": jobs})
    from research.experiments.solver_benchmark.cases import fixture
    save(tmp_path / "inputs/heavy-mixed.json", fixture("heavy", "mixed", 20261020))
    report(tmp_path, plots=True)
    assert len(list((tmp_path / "figures").glob("*.svg"))) == 4
    assert len(list((tmp_path / "figures").glob("*.pdf"))) == 4
    assert len(list((tmp_path / "figures").glob("*.png"))) == 4
    assert all(r["attempted"] == 0 for r in read(tmp_path / "summary.json")["budget_subset_coverage"])
