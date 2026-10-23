"""Audit and report Study B attempt 3 without canonical-map requirements."""

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path

from seat_solver.production.policy import mapped_weights, policy
from seat_solver.production.production_scoring import eligible
from seat_solver.production.production_validator import audit_result, validate_placements
from research.experiments.solver_benchmark.common import reference_components

from .protocol import BACKENDS, KEYS, STUDY, digest, file_digest, map_hash, read, request_for, save, semantic_hash

OUTCOMES = ("optimal_map", "feasible_map", "no_map", "late_candidate", "invalid_candidate",
            "execution_error", "not_started")
PHASES = ("normalization", "model_build", "model_updates", "weighted_search", "extraction",
          "validation_scoring", "format_response", "other_function", "service_overhead")


def outcome(row):
    if row.get("execution_status") in ("not_started", "missing"):
        return "not_started"
    if row.get("execution_status") != "completed":
        return "execution_error"
    candidate = row.get("candidate") or {}
    if candidate and not candidate.get("valid"):
        return "invalid_candidate"
    if row.get("returned_new_map"):
        return "optimal_map" if row.get("telemetry", {}).get("weighted_proven") else "feasible_map"
    if candidate.get("valid") and row.get("telemetry", {}).get("within_shared_allowance") is False:
        return "late_candidate"
    return "no_map"


def csv_write(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else ["no_observations"])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_records(out, manifest):
    rows = []
    for trial in manifest["jobs"]:
        path = out / "runs" / f"{trial['id']}.json"
        row = read(path) if path.exists() else {**trial, "execution_status": "missing", "returned_new_map": False}
        if any(row.get(key) != value for key, value in trial.items()):
            raise ValueError(f"Record identity differs from schedule: {trial['id']}")
        rows.append(row)
    return rows


def verify_records(out, rows, manifest):
    cfg = policy()
    verified = 0
    defects = []
    for field in ("record_sha256", "candidate_artifact_sha256", "native_log_sha256"):
        for rel, checksum in manifest.get(field, {}).items():
            if file_digest(out / rel) != checksum:
                raise ValueError(f"Saved evidence changed: {rel}")
    for row in rows:
        if row["execution_status"] != "completed":
            continue
        request = request_for(read(out / "inputs" / f"{row['event']}.json"), row)
        if digest(request) != row["request_sha256"] or semantic_hash(request) != row["semantic_input_sha256"]:
            raise ValueError(f"Request identity changed: {row['id']}")
        for field, checksum in (("response_path", "response_file_sha256"),
                                ("candidate_path", "candidate_file_sha256"),
                                ("pending_candidate_path", "pending_candidate_file_sha256")):
            if row.get(field) and file_digest(out / row[field]) != row.get(checksum):
                raise ValueError(f"Artifact checksum changed: {row[field]}")
        candidate = row.get("candidate")
        pending = read(out / row["pending_candidate_path"]) if row.get("pending_candidate_path") else None
        if pending and (pending.get("validation_pending") is not True or
                        (candidate and candidate.get("valid") and map_hash(pending["placements"]) != candidate.get("physical_map_sha256"))):
            raise ValueError(f"Pending candidate checkpoint differs from final candidate: {row['id']}")
        telemetry = row.get("telemetry", {})
        stages = telemetry.get("stages", [])
        weighted = stages[0] if stages else None
        if len(stages) > 1 or (weighted and weighted["stage"] != "weighted_preferences"):
            raise ValueError(f"Unexpected solve stages: {row['id']}")
        if weighted:
            from .backends import proof_established
            native = {"gap_limit_reached": weighted.get("gap_limit_reached", False)}
            proven = proof_established(weighted["api_status"], weighted["value"], weighted["best_bound"], native)
            if proven != weighted["proven"] or proven != telemetry["weighted_proven"]:
                raise ValueError(f"Proof claim inconsistent with native status/bound: {row['id']}")
            if telemetry["weighted_stage_return_seconds"] != weighted["returned_seconds"]:
                raise ValueError(f"Weighted stage clock differs: {row['id']}")
        if candidate:
            audit = validate_placements(request, candidate["placements"])
            if not audit["passed"]:
                if candidate.get("valid") or row.get("returned_new_map"):
                    raise ValueError(f"Invalid map marked valid or adopted: {row['id']}")
                defects.append(f"Invalid candidate: {row['id']}")
                continue
            if not candidate.get("valid"):
                raise ValueError(f"Valid map marked invalid: {row['id']}")
            lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
            people = {p["participant_id"]: p for p in eligible(request)}
            totals = dict.fromkeys(KEYS, 0)
            for assignment in candidate["placements"]:
                components = reference_components(request, cfg, people[assignment["participant_id"]],
                                                  [lookup[s] for s in assignment["seat_ids"]])
                for key in KEYS:
                    totals[key] += components[key]
            weights = mapped_weights(request["preferences"])
            objective = sum(weights[k] * totals[k] for k in KEYS)
            if (totals != candidate["components"] or weights != candidate["weights"]
                    or objective != candidate["objective"] or map_hash(candidate["placements"]) != candidate["physical_map_sha256"]
                    or not weighted or objective != weighted["value"]):
                raise ValueError(f"Candidate differs from independent rescoring or native incumbent: {row['id']}")
            verified += 1
        response = read(out / row["response_path"])
        if row.get("returned_new_map"):
            if (not candidate or not candidate["valid"] or not telemetry.get("within_shared_allowance")
                    or response.get("status") != "success" or not audit_result(response)["passed"]
                    or map_hash(response["assignments"]) != row["physical_map_sha256"]
                    or row["physical_map_sha256"] != candidate["physical_map_sha256"]
                    or response["solver"]["main_penalty"] != candidate["objective"]
                    or response["solver"]["status"] != ("OPTIMAL" if telemetry["weighted_proven"] else "FEASIBLE")):
                raise ValueError(f"Adopted map violates attempt 3 contract: {row['id']}")
        elif response.get("status") == "success":
            raise ValueError(f"Unadopted success response: {row['id']}")
        elif candidate and candidate.get("valid") and telemetry.get("within_shared_allowance"):
            defects.append(f"Timely valid candidate was not adopted: {row['id']}")
        if telemetry.get("solver_status") == "INFEASIBLE":
            defects.append(f"Known-feasible source reported infeasible: {row['id']}")
    from .runner import check_consistency
    try:
        check_consistency(rows)
    except ValueError as exc:
        defects.append(str(exc))
    return dict(passed=not defects, model_defects=defects, candidates_independently_rescored=verified,
                invalid_adopted=sum(bool(r.get("returned_new_map") and (r.get("candidate") or {}).get("valid") is False) for r in rows),
                completed_records=sum(r["execution_status"] == "completed" for r in rows),
                scheduled_records=len(rows), record_checksums_verified=bool(manifest.get("record_sha256")))


def phases(row):
    telemetry = row.get("telemetry", {})
    values = {key: sum(p["duration_seconds"] for p in telemetry.get("phases", []) if p["name"] == key) for key in PHASES}
    values["other_function"] = telemetry.get("unclassified_function_overhead_seconds", 0)
    total = row.get("complete_service_return_seconds")
    values["service_overhead"] = max(0, total - telemetry.get("function_return_seconds", 0)) if total is not None else 0
    if total is not None and abs(sum(values.values()) - total) > 1e-5:
        raise ValueError(f"Phase clocks do not reconcile: {row['id']}")
    return values


def make_tables(out, rows):
    coverage = []
    for batch, workers, backend in sorted({(r["batch"], r["workers"], r["backend"]) for r in rows}):
        group = [r for r in rows if (r["batch"], r["workers"], r["backend"]) == (batch, workers, backend)]
        counts = Counter(outcome(r) for r in group)
        coverage.append(dict(batch=batch, budget_seconds=group[0]["budget_seconds"], workers=workers, backend=backend,
                             scheduled=len(group), completed=sum(r["execution_status"] == "completed" for r in group),
                             valid_maps=counts["optimal_map"] + counts["feasible_map"],
                             proof_maps=counts["optimal_map"], **{name: counts[name] for name in OUTCOMES}))
    csv_write(out / "tables/coverage.csv", coverage)
    run_rows, timing = [], []
    for row in rows:
        candidate, telemetry = row.get("candidate") or {}, row.get("telemetry", {})
        stage = (telemetry.get("stages") or [{}])[0]
        run_rows.append(dict(id=row["id"], batch=row["batch"], event=row["event"], configuration=row["configuration"],
                             backend=row["backend"], workers=row["workers"], repetition=row["repetition"], permutation=row["permutation"],
                             budget_seconds=row["budget_seconds"], execution_status=row["execution_status"], outcome=outcome(row),
                             valid_map=row.get("returned_new_map", False), objective=candidate.get("objective"),
                             proven=telemetry.get("weighted_proven", False), incumbent=stage.get("value"), best_bound=stage.get("best_bound"),
                             absolute_gap=stage.get("absolute_gap"), native_status=stage.get("api_status"),
                             native_concurrent_solvers=stage.get("observed_concurrent_solvers"),
                             weighted_stage_return_seconds=telemetry.get("weighted_stage_return_seconds"),
                             complete_service_return_seconds=row.get("complete_service_return_seconds"),
                             worker_elapsed_seconds=row.get("worker_elapsed_seconds"),
                             service_process_cpu_seconds=row.get("service_process_cpu_seconds"),
                             memory_bytes=(row.get("memory") or {}).get("bytes"),
                             memory_method=(row.get("memory") or {}).get("method")))
        if row.get("complete_service_return_seconds") is not None:
            timing.append(dict(id=row["id"], **phases(row)))
    csv_write(out / "tables/run-records.csv", run_rows)
    csv_write(out / "tables/phase-timing.csv", timing, ["id", *PHASES])
    paired = []
    groups = sorted({(r["batch"], r["event"], r["configuration"], r["workers"], r["repetition"]) for r in rows})
    for batch, event, config, workers, repeat in groups:
        pair = {r["backend"]: r for r in rows if (r["batch"], r["event"], r["configuration"], r["workers"], r["repetition"]) ==
                (batch, event, config, workers, repeat)}
        if set(pair) != set(BACKENDS):
            raise ValueError("Scheduled pair is incomplete")
        cp, scip = (pair[b] for b in BACKENDS)
        both = cp.get("returned_new_map") and scip.get("returned_new_map")
        paired.append(dict(batch=batch, budget_seconds=cp["budget_seconds"], event=event, configuration=config,
                           workers=workers, repetition=repeat, both_valid=bool(both),
                           cp_sat_objective=(cp.get("candidate") or {}).get("objective") if cp.get("returned_new_map") else None,
                           scip_objective=(scip.get("candidate") or {}).get("objective") if scip.get("returned_new_map") else None,
                           cp_minus_scip=(cp["candidate"]["objective"] - scip["candidate"]["objective"]) if both and config != "disabled" else None,
                           disabled_quality_control=config == "disabled"))
    csv_write(out / "tables/paired-objectives.csv", paired)
    return coverage, paired


def plots(out, rows, coverage, paired, formats=("pdf", "svg", "png")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    folder = out / "figures"
    folder.mkdir(exist_ok=True)
    prefix = "DEVELOPMENT ONLY | " if read(out / "manifest.json").get("development_only") else "Study B attempt 3 | "
    names = []

    def export(fig, name):
        for suffix in formats:
            fig.savefig(folder / f"{name}.{suffix}", dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        names.append(name)

    if rows[0]["batch"] == "sweep":
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for backend, color in (("cp_sat", "#2b659b"), ("scip", "#c16a28")):
            group = [r for r in coverage if r["backend"] == backend]
            axes[0].plot([r["workers"] for r in group], [r["valid_maps"] / r["scheduled"] for r in group], "o-", color=color, label=backend)
            axes[1].plot([r["workers"] for r in group], [r["proof_maps"] / r["scheduled"] for r in group], "o-", color=color, label=backend)
        for ax, title in zip(axes, ("Valid-map coverage", "Weighted proof coverage")):
            ax.set_xticks([1, 2, 4, 8]); ax.set_ylim(0, 1.05); ax.set_xlabel("Workers / native SCIP threads"); ax.set_ylabel("Share of scheduled jobs"); ax.set_title(title); ax.grid(alpha=.2)
        axes[0].legend()
        fig.suptitle(prefix + "separate concurrency sensitivity")
        export(fig, "attempt3-sweep-coverage")
        return names

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
    for backend, color in (("cp_sat", "#2b659b"), ("scip", "#c16a28")):
        group = sorted((r for r in coverage if r["backend"] == backend), key=lambda r: r["budget_seconds"])
        budgets = [r["budget_seconds"] for r in group]
        axes[0].plot(budgets, [r["valid_maps"] / r["scheduled"] for r in group], "o-", color=color, label=backend)
        axes[1].plot(budgets, [r["proof_maps"] / r["scheduled"] for r in group], "o-", color=color, label=backend)
    for ax, title in zip(axes, ("Valid-map coverage", "Weighted proof coverage")):
        ax.set_xticks([5, 30, 60]); ax.set_ylim(0, 1.05); ax.set_xlabel("Fresh allocation allowance (seconds)"); ax.set_ylabel("Share of scheduled jobs"); ax.set_title(title); ax.grid(alpha=.2)
    axes[0].legend()
    fig.suptitle(prefix + "initial allocation coverage")
    export(fig, "attempt3-coverage-by-allowance")

    fig, ax = plt.subplots(figsize=(10.5, 5))
    selected = [r for r in rows if r["batch"] == "primary" and r.get("complete_service_return_seconds") is not None]
    for backend, color, marker in (("cp_sat", "#2b659b", "o"), ("scip", "#c16a28", "s")):
        subset = [r for r in selected if r["backend"] == backend]
        ax.scatter([r["complete_service_return_seconds"] for r in subset],
                   [r["event"] + "/" + str(r["repetition"]) for r in subset], c=color, marker=marker, label=backend, s=30)
    ax.axvline(60, color="#777", linestyle="--", label="60 s function allowance")
    ax.set_xlabel("Complete local service return (seconds)"); ax.set_ylabel("Workload / repeat")
    ax.set_title("All recorded primary calls; no-map calls retain their service times"); ax.legend(); ax.grid(axis="x", alpha=.2)
    export(fig, "attempt3-complete-service-time")

    values = [r for r in paired if r["batch"] == "primary" and r["cp_minus_scip"] is not None]
    fig, ax = plt.subplots(figsize=(10.5, 4.5))
    if values:
        x = np.arange(len(values))
        ax.scatter(x, [r["cp_minus_scip"] for r in values], c="#624b8e", s=30)
        ax.set_xticks(x, [r["event"] + "/" + str(r["repetition"]) for r in values], rotation=75, ha="right", fontsize=7)
    else:
        ax.text(.5, .5, "No matched valid primary cases", transform=ax.transAxes, ha="center", va="center")
    ax.axhline(0, color="#777", linewidth=1); ax.set_ylabel("CP-SAT penalty minus SCIP penalty")
    ax.set_title("Matched valid primary cases; disabled preferences excluded"); ax.grid(axis="y", alpha=.2)
    export(fig, "attempt3-matched-penalties")
    return names


def report(out, plots=True):
    out = Path(out)
    manifest = read(out / "manifest.json")
    if manifest.get("study") != STUDY:
        raise ValueError("This reporter accepts Study B attempt 3 evidence only")
    from .runner import source_hashes
    if source_hashes() != manifest["environment"]["source_sha256"]:
        raise ValueError("Sources differ from snapshot; use archived reporter and lock")
    for event, info in manifest["inputs"].items():
        if digest(read(out / "inputs" / f"{event}.json")) != info["input_sha256"]:
            raise ValueError(f"Frozen input changed: {event}")
    rows = load_records(out, manifest)
    checks = verify_records(out, rows, manifest)
    coverage, paired = make_tables(out, rows)
    observed = any(r["execution_status"] not in ("not_started", "missing") for r in rows)
    figures = globals()["plots"](out, rows, coverage, paired) if plots and observed else []
    primary = [r for r in coverage if r["batch"] == "primary"]
    complete = manifest["execution_status"] == "completed" and checks["passed"] and checks["invalid_adopted"] == 0
    conclusion = "Incomplete or failed run; no selection conclusion"
    if manifest["mode"] in ("sweep", "plan-sweep"):
        conclusion = "Separate worker/thread sensitivity evidence; do not pool with the 60-second initial-selection denominator"
    elif complete and primary:
        cp, scip = (next(r for r in primary if r["backend"] == b) for b in BACKENDS)
        if cp["valid_maps"] != scip["valid_maps"]:
            conclusion = f"Coverage lead at 60 s: {'CP-SAT' if cp['valid_maps'] > scip['valid_maps'] else 'SCIP'}; inspect paired penalty, proof, and return time before a default change"
        else:
            conclusion = "60-second valid-map coverage ties; compare matched penalty, proof coverage and complete service time. Report unresolved trade-offs without forcing a default"
    summary = dict(study=STUDY, execution_status=manifest["execution_status"], mode=manifest["mode"],
                   development_only=manifest.get("development_only", False), checks=checks, coverage=coverage,
                   figures=figures, measured_jobs_scheduled=len(rows), measured_jobs_completed=checks["completed_records"],
                   selection_conclusion=conclusion)
    save(out / "summary.json", summary)
    save(out / "checks.json", checks)
    lines = ["| Batch | Allowance | Workers | Backend | Valid maps | Proven | Scheduled |",
             "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
    lines += [f"| {r['batch']} | {r['budget_seconds']} s | {r['workers']} | {r['backend']} | {r['valid_maps']} | {r['proof_maps']} | {r['scheduled']} |" for r in coverage]
    gallery = "\n\n".join(f"![{name}](figures/{name}.png)\n\n[PDF](figures/{name}.pdf) | [SVG](figures/{name}.svg)" for name in figures)
    guidance = ("This is a separate 60-second worker/thread sensitivity study. Compare each backend's 1/2/4/8 settings for valid-map and proof coverage, matched valid-case penalty, complete service time, native SCIP launches, process CPU seconds and peak working set. Do not pool these jobs with the main solver-selection denominator."
                if manifest["mode"] in ("sweep", "plan-sweep") else
                "At 60 seconds, valid-map coverage is the first decision measure. A valid unproved map is a `FEASIBLE` return. Compare production penalty only on matched valid cases, then proof coverage and complete local service-return time. Disabled preferences are excluded from penalty differences. Require zero invalid adopted maps. The 5- and 30-second jobs are fresh diagnostic endpoints and are not pooled with 60 seconds. The separate worker/thread sweep has its own denominator.")
    content = f"""# Study B attempt 3: initial allocation results

Status: **{manifest['execution_status']}**. Mode: **{manifest['mode']}**. Development only: **{manifest.get('development_only', False)}**. Audits passed: **{checks['passed']}**.

[Manifest](manifest.json) · [Checks](checks.json) · [Run records](tables/run-records.csv) · [Coverage](tables/coverage.csv) · [Matched penalties](tables/paired-objectives.csv) · [Phase timing](tables/phase-timing.csv)

## Coverage

{chr(10).join(lines)}

{guidance}

## Interpretation

{conclusion}

The allowance covers normalization, model building and weighted search; independent validation, formatting, SQLite persistence and JSON encoding contribute to complete service return. A stage-return timestamp is not the first incumbent-discovery time. No staff response-time requirement has been established. Three executions per case are descriptive and do not estimate population reliability. Native SCIP launch counts establish concurrent solver instances, not sustained CPU utilization. This benchmark does not exercise a result cache, preference-update regeneration or absence repair.

## Figures

{gallery if figures else 'No measured observations were available for figures, or plotting was disabled.'}
"""
    (out / "results.md").write_text(content, encoding="utf-8")
    return dict(figures=len(figures), **checks)
