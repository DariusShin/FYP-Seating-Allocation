"""Derive Study B tables and B1–B5 figures from saved observations only."""

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import textwrap

from seat_solver.production.policy import mapped_weights, policy
from seat_solver.production.production_scoring import eligible
from seat_solver.production.production_validator import audit_result, validate_placements
from research.experiments.solver_benchmark.common import reference_components

from .protocol import (BACKENDS, DIAGNOSTIC, KEYS, PRIMARY, STUDY, digest, file_digest,
                       map_hash, read, request_for, save, semantic_hash)

NAMES = {"cp_sat": "CP-SAT", "scip": "SCIP"}
OUTCOMES = ("accepted", "late_canonical", "valid_unproved", "valid_uncanonical", "no_candidate",
            "invalid", "execution_error", "not_started", "unmet_prerequisite")
CODES = ("A", "L", "F", "C", "U", "I", "E", "N", "P")
COLORS = ("#175a2f", "#71b5ab", "#b7d8a1", "#97b5da", "#f0c66a", "#aa7dc2", "#dd8b82", "#dadde0", "#bcb5ce")
LABELS = ("A: accepted new canonical map", "L: canonical but allowance exceeded", "F: valid, weighted optimum unproved",
          "C: valid, canonical selection incomplete", "U: no validated candidate", "I: invalid candidate",
          "E: execution error/watchdog", "N: not executed/missing", "P: unmet baseline prerequisite")
PHASES = ("normalization", "model_build", "weighted_search", "canonical_search", "extraction", "model_updates",
          "validation_scoring", "format_response", "other_function", "service_overhead")
PHASE_LABELS = ("Normalization", "Model build", "Weighted search", "Canonical search", "Extraction", "Model updates",
                "Independent scoring/audit", "Formatting", "Other function", "Service/JSON overhead")
PHASE_COLORS = ("#9cc6c4", "#557fa9", "#e4a154", "#987aac", "#bbaacb", "#b7c7dc", "#79a56e", "#b9d1aa", "#b7bbc1", "#6b737f")


def outcome(record):
    execution = record.get("execution_status", "not_started")
    if execution == "unmet_prerequisite":
        return "unmet_prerequisite"
    if execution in ("not_started", "missing"):
        return "not_started"
    if execution != "completed":
        return "execution_error"
    candidate = record.get("candidate")
    if record.get("returned_new_map"):
        return "accepted"
    if not candidate:
        return "no_candidate"
    if not candidate.get("valid"):
        return "invalid"
    telemetry = record["telemetry"]
    if telemetry.get("canonicalization_complete"):
        return "late_canonical"
    return "valid_uncanonical" if telemetry.get("weighted_proven") else "valid_unproved"


def csv_write(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else ["no_observations"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_records(out, manifest):
    records = []
    for trial in manifest["jobs"]:
        path = out / "runs" / f"{trial['id']}.json"
        row = read(path) if path.exists() else {**trial, "execution_status": "missing", "returned_new_map": False}
        if any(row.get(key) != value for key, value in trial.items()):
            raise ValueError(f"Record identity differs from schedule: {trial['id']}")
        records.append(row)
    return records


def verify_records(out, records, manifest):
    """Re-audit candidate placements and public responses, including objective scale."""
    verified = 0
    defects = []
    cfg = policy()
    for rel, sha in manifest.get("record_sha256", {}).items():
        if file_digest(out / rel) != sha:
            raise ValueError(f"Saved record changed after execution: {rel}")
    for rel, sha in manifest.get("native_log_sha256", {}).items():
        if file_digest(out / rel) != sha:
            raise ValueError(f"Native/worker log changed after execution: {rel}")
    for row in records:
        if row["execution_status"] != "completed":
            continue
        request = request_for(read(out / "inputs" / f"{row['event']}.json"), row)
        if digest(request) != row["request_sha256"] or semantic_hash(request) != row["semantic_input_sha256"]:
            raise ValueError("Request identity differs from the fixed schedule")
        for field, checksum in (("response_path", "response_file_sha256"), ("candidate_path", "candidate_file_sha256")):
            if row.get(field) and row.get(checksum) and file_digest(out / row[field]) != row[checksum]:
                raise ValueError(f"Artifact checksum mismatch: {row[field]}")
        candidate = row.get("candidate")
        if candidate:
            audit = validate_placements(request, candidate["placements"])
            if not audit["passed"]:
                if candidate.get("valid") or row.get("returned_new_map"):
                    raise ValueError("Invalid candidate was marked valid/adopted")
                defects.append(f"Invalid candidate: {row['id']}")
                continue
            if not candidate.get("valid"):
                raise ValueError("Valid candidate was inconsistently marked invalid")
            lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
            people = {p["participant_id"]: p for p in eligible(request)}
            totals = dict.fromkeys(KEYS, 0)
            for assignment in candidate["placements"]:
                components = reference_components(request, cfg, people[assignment["participant_id"]],
                                                  [lookup[sid] for sid in assignment["seat_ids"]])
                for key in KEYS:
                    totals[key] += components[key]
            weights = mapped_weights(request["preferences"])
            if totals != candidate["components"] or weights != candidate["weights"] or sum(weights[k] * totals[k] for k in KEYS) != candidate["objective"]:
                raise ValueError("Saved candidate differs from independent production rescoring")
            if map_hash(candidate["placements"]) != candidate["physical_map_sha256"]:
                raise ValueError("Candidate physical-map checksum mismatch")
            verified += 1
        if row.get("returned_new_map"):
            response = read(out / row["response_path"])
            telemetry = row["telemetry"]
            if (not audit_result(response)["passed"] or not telemetry["weighted_proven"]
                    or not telemetry["canonicalization_complete"] or not telemetry["within_shared_allowance"]
                    or map_hash(response["assignments"]) != row["physical_map_sha256"]
                    or row["physical_map_sha256"] != candidate["physical_map_sha256"]):
                raise ValueError("Accepted return lacks the complete adoption contract")
    from .runner import check_consistency
    try:
        check_consistency(records)
    except ValueError as exc:
        defects.append(str(exc))
    defects.extend(f"Known-feasible input reported infeasible: {r['id']}" for r in records
                   if r.get("telemetry", {}).get("solver_status") == "INFEASIBLE")
    return dict(passed=not defects, model_defects=defects, candidates_independently_rescored=verified,
                completed_records=sum(r["execution_status"] == "completed" for r in records),
                scheduled_records=len(records), record_checksums_verified=bool(manifest.get("record_sha256")))


def rows_for(records, batch, event, config, backend):
    return [r for r in records if (r["batch"], r["event"], r["configuration"], r["backend"]) == (batch, event, config, backend)]


def phases(row):
    telemetry = row.get("telemetry", {})
    values = {key: sum(p["duration_seconds"] for p in telemetry.get("phases", []) if p["name"] == key) for key in PHASES}
    values["other_function"] = telemetry.get("unclassified_function_overhead_seconds", 0)
    total = row.get("complete_service_return_seconds")
    values["service_overhead"] = max(0, total - telemetry.get("function_return_seconds", 0)) if total is not None else 0
    if total is not None and abs(sum(values.values()) - total) > 1e-5:
        raise ValueError("Overlapping or incomplete phase clocks")
    return values


def comparisons(records):
    result = []
    for event, config in PRIMARY:
        for backend in BACKENDS:
            group = rows_for(records, "primary", event, config, backend)
            by_repeat = {r["repetition"]: r for r in group}
            for label, a, b in (("raw_repeat", 1, 2), ("semantic_permutation", 1, 3)):
                pair = [by_repeat.get(a), by_repeat.get(b)]
                available = all(r and r.get("returned_new_map") for r in pair)
                result.append(dict(event=event, configuration=config, comparison=label, backend=backend,
                                   available=available, equal=(pair[0]["physical_map_sha256"] == pair[1]["physical_map_sha256"]) if available else None,
                                   first_run=pair[0]["id"] if pair[0] else None, second_run=pair[1]["id"] if pair[1] else None,
                                   prior_map_preserved=None))
        pair = [next((r for r in rows_for(records, "primary", event, config, backend) if r.get("returned_new_map")), None) for backend in BACKENDS]
        available = all(pair)
        result.append(dict(event=event, configuration=config, comparison="cross_backend", backend="both",
                           available=available, equal=pair[0]["physical_map_sha256"] == pair[1]["physical_map_sha256"] if available else None,
                           first_run=pair[0]["id"] if pair[0] else None, second_run=pair[1]["id"] if pair[1] else None, prior_map_preserved=None))
    for row in records:
        if row["batch"] == "regeneration":
            result.append(dict(event=row["event"], configuration=row["configuration"], comparison="regeneration", backend=row["origin_backend"],
                               available=row.get("returned_new_map", False), equal=row.get("regeneration_same_map"),
                               first_run=row.get("baseline_source"), second_run=row["id"], prior_map_preserved=row.get("prior_map_preserved")))
    return result


def make_tables(out, records):
    coverage = []
    for batch, backend in sorted({(r["batch"], r["backend"]) for r in records}):
        group = [r for r in records if (r["batch"], r["backend"]) == (batch, backend)]
        counts = Counter(outcome(r) for r in group)
        coverage.append(dict(batch=batch, backend=backend, scheduled=len(group),
                             completed=sum(r["execution_status"] == "completed" for r in group),
                             candidate_valid=sum(bool((r.get("candidate") or {}).get("valid")) for r in group),
                             weighted_proven=sum(r.get("telemetry", {}).get("weighted_proven", False) for r in group),
                             canonical_complete=sum(r.get("telemetry", {}).get("canonicalization_complete", False) for r in group),
                             accepted_new_maps=counts["accepted"], **{s: counts[s] for s in OUTCOMES if s != "accepted"}))
    csv_write(out / "tables/coverage.csv", coverage)
    columns = []
    timing = []
    for row in records:
        candidate, telemetry = row.get("candidate") or {}, row.get("telemetry", {})
        columns.append(dict(id=row["id"], batch=row["batch"], event=row["event"], configuration=row["configuration"],
                            backend=row["backend"], origin_backend=row.get("origin_backend"), repetition=row["repetition"],
                            permutation=row["permutation"], budget_seconds=row["budget_seconds"], execution_status=row["execution_status"],
                            outcome=outcome(row), candidate_valid=candidate.get("valid", False), objective=candidate.get("objective"),
                            weighted_proven=telemetry.get("weighted_proven", False), canonical_complete=telemetry.get("canonicalization_complete", False),
                            canonical_stages_required=telemetry.get("canonical_stages_required"), canonical_stages_completed=telemetry.get("canonical_stages_completed"),
                            within_shared_allowance=telemetry.get("within_shared_allowance"), accepted_new_map=row.get("returned_new_map", False),
                            weighted_proof_reported_seconds=telemetry.get("weighted_proof_reported_seconds"),
                            canonical_complete_seconds=telemetry.get("canonical_complete_seconds"),
                            complete_service_return_seconds=row.get("complete_service_return_seconds"), worker_elapsed_seconds=row.get("worker_elapsed_seconds"),
                            physical_map_sha256=row.get("physical_map_sha256"), semantic_input_sha256=row.get("semantic_input_sha256"),
                            prior_map_preserved=row.get("prior_map_preserved"), regeneration_same_map=row.get("regeneration_same_map")))
        timing.append(dict(id=row["id"], batch=row["batch"], outcome=outcome(row), **phases(row),
                           complete_service_return_seconds=row.get("complete_service_return_seconds")))
    csv_write(out / "tables/run-records.csv", columns)
    csv_write(out / "tables/phase-timing.csv", timing)
    comparison = comparisons(records)
    csv_write(out / "tables/map-comparisons.csv", comparison)
    paired = []
    for event, config in PRIMARY:
        for repeat in (1, 2, 3):
            group = [next(r for r in rows_for(records, "primary", event, config, b) if r["repetition"] == repeat) for b in BACKENDS]
            candidates = [r.get("candidate") or {} for r in group]
            both = all(c.get("valid") for c in candidates)
            paired.append(dict(event=event, configuration=config, repetition=repeat, both_candidates_valid=both,
                               both_accepted=all(r.get("returned_new_map") for r in group),
                               cp_sat_objective=candidates[0].get("objective"), scip_objective=candidates[1].get("objective"),
                               cp_minus_scip=(candidates[0]["objective"] - candidates[1]["objective"]) if both and config != "disabled" else None,
                               disabled_quality_control=config == "disabled"))
    csv_write(out / "tables/paired-objectives.csv", paired)
    return coverage, comparison


def plots(out, records, comparison, formats=("pdf", "svg", "png")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch, Rectangle
    import numpy as np

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42,
                         "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False})
    directory = out / "figures"
    directory.mkdir(exist_ok=True)
    is_test = read(out / "manifest.json").get("development_only", False)
    prefix = "DEVELOPMENT ONLY | " if is_test else "Study B | "

    def footer(fig, text):
        fig.text(.5, .012, textwrap.fill(text, 150), fontsize=8, color="#444", ha="center", va="bottom")

    def export(fig, name):
        for extension in formats:
            path = directory / f"{name}.{extension}"
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
            if extension == "svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
        plt.close(fig)

    def grid(ax, cells, rows, cols):
        values = np.array([[OUTCOMES.index(outcome(r)) for r in line] for line in cells])
        ax.imshow(values, cmap=ListedColormap(COLORS), vmin=0, vmax=len(OUTCOMES)-1, aspect="auto")
        ax.set_xticks(range(len(cols)), cols)
        ax.set_yticks(range(len(rows)), rows)
        ax.tick_params(length=0, labelsize=9)
        for y, line in enumerate(values):
            for x, code in enumerate(line):
                ax.text(x, y, CODES[code], ha="center", va="center", color="white" if code == 0 else "#222", weight="bold")
        ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(rows), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.5)
        ax.tick_params(which="minor", length=0)

    def phase_bars(ax, selected, labels):
        offset = np.zeros(len(selected))
        for key, color in zip(PHASES, PHASE_COLORS):
            values = np.array([phases(r)[key] for r in selected])
            ax.barh(range(len(selected)), values, left=offset, color=color, height=.7)
            offset += values
        for i, row in enumerate(selected):
            if row.get("complete_service_return_seconds") is not None:
                ax.text(offset[i]+.6, i, CODES[OUTCOMES.index(outcome(row))], va="center", fontsize=8)
        ax.set_yticks(range(len(selected)), labels)
        ax.invert_yaxis()
        ax.set_xlabel("Complete local service return (seconds)")
        ax.grid(axis="x", alpha=.18)
        ax.set_axisbelow(True)

    def phase_legend(fig, y=.06):
        fig.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(PHASE_COLORS, PHASE_LABELS)],
                   loc="lower center", bbox_to_anchor=(.5, y), ncol=5, fontsize=8, frameon=False)

    cells, labels = [], []
    for event, config in PRIMARY:
        for repeat in (1, 2, 3):
            cells.append([next(r for r in rows_for(records, "primary", event, config, b) if r["repetition"] == repeat) for b in BACKENDS])
            labels.append(f"{event} / {config} / {'permuted' if repeat == 3 else 'raw '+str(repeat)}")
    fig, ax = plt.subplots(figsize=(11, 11))
    fig.subplots_adjust(left=.35, right=.95, top=.91, bottom=.19)
    grid(ax, cells, labels, ["CP-SAT", "SCIP"])
    fig.suptitle(prefix + "Primary 60-second production outcomes", fontsize=15, y=.98)
    fig.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(COLORS, LABELS)], loc="lower center",
               bbox_to_anchor=(.5, .065), ncol=3, fontsize=8, frameon=False)
    footer(fig, "Eight predefined workload/settings; two raw repeats and one semantic permutation per backend (48 jobs). "
           "A requires independent validity, weighted proof, complete canonical selection within the shared allowance and service adoption. N is not a no-map solve.")
    export(fig, "b1-production-outcomes")

    fig, axes = plt.subplots(2, 1, figsize=(13, 12), gridspec_kw={"height_ratios": [3, 1.2]})
    fig.subplots_adjust(left=.29, right=.96, top=.93, bottom=.15, hspace=.28)
    for y, pair in enumerate(cells):
        for i, row in enumerate(pair):
            if row.get("complete_service_return_seconds") is not None:
                axes[0].scatter(row["complete_service_return_seconds"], y+(i-.5)*.22,
                                marker=("o" if i == 0 else "s") if row.get("returned_new_map") else "x",
                                color=("#2463a6", "#bd591b")[i], s=34)
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    axes[0].axvline(60, color="#777", linestyle="--", linewidth=1)
    axes[0].set_xlim(left=0)
    axes[0].set_xlabel("Complete local service return (seconds); x = no acceptable new map")
    axes[0].grid(axis="x", alpha=.2)
    selected = [next(r for r in rows_for(records, "primary", e, c, b) if r["repetition"] == 1)
                for e, c in DIAGNOSTIC for b in BACKENDS]
    phase_bars(axes[1], selected, [f"{r['event']} / {NAMES[r['backend']]} / raw 1" for r in selected])
    fig.suptitle(prefix + "Complete-result time and predefined phase examples", fontsize=15, y=.985)
    phase_legend(fig, .065)
    footer(fig, "Blue = CP-SAT; orange = SCIP. All recorded primary calls are shown, including errors/no new maps. Dashed 60 s is the internal allowance, "
           "not a service SLA. Final audits, formatting, SQLite adoption and JSON encoding can extend service time. Worker startup/baseline hydration are separate.")
    export(fig, "b2-service-time-and-phases")

    columns = [("raw_repeat", "cp_sat"), ("semantic_permutation", "cp_sat"), ("raw_repeat", "scip"),
               ("semantic_permutation", "scip"), ("cross_backend", "both"), ("regeneration", "cp_sat"), ("regeneration", "scip")]
    col_labels = ["CP-SAT\nraw repeat", "CP-SAT\npermutation", "SCIP\nraw repeat", "SCIP\npermutation", "Across\nbackends", "CP-origin\nCP regen", "SCIP-origin\nCP regen"]
    values = []
    for event, config in PRIMARY:
        line = []
        for label, backend in columns:
            item = next((r for r in comparison if (r["event"], r["configuration"], r["comparison"], r["backend"]) == (event, config, label, backend)), None)
            line.append(3 if item is None else 2 if not item["available"] else 0 if item["equal"] else 1)
        values.append(line)
    fig, ax = plt.subplots(figsize=(13, 5.7))
    fig.subplots_adjust(left=.25, right=.98, top=.79, bottom=.24)
    ax.imshow(values, cmap=ListedColormap(("#a5d5ab", "#dd8b82", "#c8c0d5", "#dadde0")), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(col_labels)), col_labels, fontsize=9)
    ax.set_yticks(range(len(PRIMARY)), [e+" / "+c for e, c in PRIMARY], fontsize=9)
    for y, line in enumerate(values):
        for x, value in enumerate(line):
            ax.text(x, y, ("=", "!", "P", "N")[value], ha="center", va="center", weight="bold")
    fig.suptitle(prefix + "Physical-map repeatability and regeneration", fontsize=15, y=.98)
    fig.text(.5, .105, "= equal accepted maps     ! mismatch (defect)     P accepted-map prerequisite missing     N not scheduled", ha="center", fontsize=9)
    footer(fig, "Raw and permutation checks compare primary raw 1 with raw 2/permuted 3; missing raw 1 is not substituted. Cross-backend uses first scheduled "
           "accepted primary results. Regeneration uses its recorded origin baseline. Preserving an old map is not a successful new regeneration.")
    export(fig, "b3-reproducibility-and-regeneration")

    diag_cells, diag_labels, detail = [], [], []
    for event, config in DIAGNOSTIC:
        for repeat in (1, 2):
            line = []
            for backend in BACKENDS:
                for batch in ("primary", "diagnostic"):
                    row = next(r for r in rows_for(records, batch, event, config, backend) if r["repetition"] == repeat)
                    line.append(row)
                    detail.append(row)
            diag_cells.append(line)
            diag_labels.append(f"{event} / raw {repeat}")
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={"height_ratios": [1, 3]})
    fig.subplots_adjust(left=.28, right=.96, top=.92, bottom=.16, hspace=.28)
    grid(axes[0], diag_cells, diag_labels, ["CP-SAT 60 s", "CP-SAT 180 s", "SCIP 60 s", "SCIP 180 s"])
    phase_bars(axes[1], detail, [f"{r['event']} / {NAMES[r['backend']]} / {r['budget_seconds']} s / raw {r['repetition']}" for r in detail])
    fig.suptitle(prefix + "Predefined 60/180-second fresh-run diagnostics", fontsize=15, y=.985)
    phase_legend(fig, .065)
    footer(fig, "Only heavy-mixed/current and full-tied/disabled, with both raw repetitions at each allowance. Letter meanings match B1. "
           "Fresh 180-second outcomes do not replace failed 60-second outcomes. Disabled ordinary preferences are a canonical/feasibility control, not meaningful quality.")
    export(fig, "b4-extended-diagnostic")

    request = read(out / "inputs/heavy-mixed.json")
    people = {p["participant_id"]: p for p in request["participants"]}
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    primary_maps = [next((r for r in rows_for(records, "primary", "heavy-mixed", "current", b) if r.get("returned_new_map")), None) for b in BACKENDS]
    include_diag = any(r is None for r in primary_maps)
    batches = ("primary", "diagnostic") if include_diag else ("primary",)
    fig, axes = plt.subplots(len(batches), 2, figsize=(12.5, 8.4*len(batches)), squeeze=False)
    fig.subplots_adjust(left=.05, right=.97, top=.91, bottom=.11, wspace=.18, hspace=.35)
    tiers = {"EMPEROR": "#e9c66d", "MERIT": "#8db8db", "BODHI": "#a5c995"}
    for row_index, batch in enumerate(batches):
        for col, backend in enumerate(BACKENDS):
            ax = axes[row_index, col]
            row = next((r for r in rows_for(records, batch, "heavy-mixed", "current", backend) if r.get("returned_new_map")), None)
            budget = 60 if batch == "primary" else 180
            ax.set_title(f"{NAMES[backend]} / {batch} / {budget}-second shared allowance", fontsize=11, pad=28)
            if row is None:
                ax.text(.5, .5, "No acceptable new map\nat this allowance", transform=ax.transAxes, ha="center", va="center", fontsize=14)
                ax.set_axis_off()
                continue
            telemetry = row["telemetry"]
            ax.text(.5, 1.015, f"r{row['repetition']} | penalty {row['candidate']['objective']:,} | proof {telemetry['weighted_proof_reported_seconds']:.2f} s | "
                    f"canonical {telemetry['canonical_complete_seconds']:.2f} s | return {row['complete_service_return_seconds']:.2f} s",
                    transform=ax.transAxes, ha="center", fontsize=8)
            owners = {sid: a["participant_id"] for a in row["candidate"]["placements"] for sid in a["seat_ids"]}
            for seat in lookup.values():
                x = seat["physical_position"] + (seat["physical_position"] > 8)
                y = seat["row_number"]
                pid = owners.get(seat["seat_id"])
                color = "#7b7f84" if seat["is_blocked"] else tiers[people[pid]["contribution_tier"]] if pid else "white"
                ax.add_patch(Rectangle((x-.43, y-.35), .86, .7, facecolor=color, edgecolor="#666", linewidth=.45))
                if pid:
                    ax.text(x, y, pid[-3:], ha="center", va="center", fontsize=5)
            ax.set_xlim(.4, 17.6)
            ax.set_ylim(16.8, .4)
            ax.set_aspect("equal")
            ax.set_xticks([x+(x>8) for x in range(1,17)], range(1,17), fontsize=7)
            ax.set_yticks(range(1,17), range(1,17), fontsize=7)
            ax.set_xlabel("Physical seat position; center aisle")
            ax.set_ylabel("Row (front at top)")
    fig.suptitle(prefix + "230-seat canonical physical allocations", fontsize=16, y=.985)
    fig.legend(handles=[Patch(facecolor=c, label=k.title()) for k,c in tiers.items()] + [Patch(facecolor="#7b7f84", label="Blocked"), Patch(facecolor="white", edgecolor="#777", label="Unused usable")],
               loc="lower center", bbox_to_anchor=(.5,.055), ncol=5, frameon=False, fontsize=9)
    footer(fig, "99 Emperor registrations (198 seats), 19 Merit and 13 Bodhi; current production weights. First scheduled accepted map per backend/batch; "
           "missing primary maps remain missing even if a separate 180-second diagnostic succeeds. Proof time is stage return, not first optimal-incumbent discovery.")
    export(fig, "b5-230-seat-canonical-maps")
    return ["b1-production-outcomes", "b2-service-time-and-phases", "b3-reproducibility-and-regeneration", "b4-extended-diagnostic", "b5-230-seat-canonical-maps"]


def report(out, plots=True):
    out = Path(out)
    manifest = read(out / "manifest.json")
    if manifest.get("study") != STUDY:
        raise ValueError("This reporter accepts Study B evidence only; never pool Study A")
    from .runner import source_hashes
    if source_hashes() != manifest["environment"]["source_sha256"]:
        raise ValueError("Sources differ from the recorded study; use its archived source_snapshot reporter and dependency lock")
    for event, info in manifest["inputs"].items():
        if digest(read(out / "inputs" / f"{event}.json")) != info["input_sha256"]:
            raise ValueError(f"Frozen input changed: {event}")
    records = load_records(out, manifest)
    checks = verify_records(out, records, manifest)
    coverage, comparison = make_tables(out, records)
    observed = any(r["execution_status"] not in ("not_started", "missing") for r in records)
    figures = globals()["plots"](out, records, comparison) if plots and observed else []
    summary = dict(study=STUDY, execution_status=manifest["execution_status"], development_only=manifest.get("development_only", False),
                   checks=checks, coverage=coverage, comparisons=comparison, figures=figures,
                   measured_jobs_scheduled=64, measured_jobs_completed=checks["completed_records"],
                   selection_conclusion="No automatic winner: interpret availability, proof, canonical adoption and complete-service time together")
    save(out / "summary.json", summary)
    save(out / "checks.json", checks)
    gallery = "\n\n".join(f"![{name}](figures/{name}.png)\n\n[PDF](figures/{name}.pdf) | [SVG](figures/{name}.svg)" for name in figures)
    coverage_lines = "\n".join(f"| {r['batch']} | {NAMES[r['backend']]} | {r['scheduled']} | {r['completed']} | {r['candidate_valid']} | {r['weighted_proven']} | {r['canonical_complete']} | {r['accepted_new_maps']} |" for r in coverage)
    text = f"""# Study B: saved production-comparison results

Status: **{manifest['execution_status']}**. Mode: **{manifest['mode']}**. Development only: **{manifest.get('development_only', False)}**. Data/model checks passed: **{checks['passed']}**.

This is a separate production study, not another attempt 3 sample. [Manifest](manifest.json), [checks](checks.json), [summary](summary.json), [run table](tables/run-records.csv), [coverage](tables/coverage.csv), [paired objectives](tables/paired-objectives.csv), [phase timings](tables/phase-timing.csv), [map comparisons](tables/map-comparisons.csv).

## Coverage and acceptance

| Batch | Backend | Scheduled | Completed | Valid candidate | Weighted proof | Canonical complete | Accepted new map |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{coverage_lines}

These levels are distinct, overlapping counts. Invalid/failed/not-started and unmet-prerequisite counts are retained in coverage.csv. A preserved baseline is not a successful new regeneration. Pilot and correctness runs are separate from all measured denominators. A failed or interrupted runner is not a completed comparison.

## Interpretation limits

Eight primary workload-setting pairs have two raw repetitions and one semantic permutation per backend. Three executions do not estimate population reliability or tail latency. Raw-repeat/permutation comparisons require raw 1; cross-backend and regeneration comparisons use their recorded first scheduled accepted primary baselines. No missing baseline is fabricated. Only two predefined workload pairs have fresh 180-second diagnostics; those do not replace 60-second outcomes.

Candidate validity, weighted proof, canonical completion within the shared allowance and actual service adoption are reported independently. An OPTIMAL API label alone is insufficient; objective-bound agreement and native gap-limit status are checked. Nonzero model penalties are preferences, not hard-rule violations. Disabled-preference costs are a control and are excluded from quality differences. Production coefficients/scales must not be mixed with Study A's compact objective or averaged across settings.

Stage time means elapsed time when a solve stage returns; first optimal-incumbent discovery is not instrumented. The 60/180 seconds are shared function allowances covering normalization/model construction/weighted and canonical searches. Complete local JSON service time also includes final validation, formatting and SQLite adoption; process imports/baseline hydration have separate worker/preparation clocks. No browser or network latency is claimed. Phase stacks use disjoint clocks with explicit residual/service overhead.

No automatic solver winner is generated. Failed correctness/concurrency/source gates, contradictory canonical outputs or unmet baselines must be resolved or reported explicitly. Read raw requests, responses, stage/native logs and their checksums alongside the tables. Native concurrent-solver launch counts verify the selected SCIP build; they do not measure eight-core utilization throughout every solve.

## Figures

{gallery if figures else 'No measured observations available for plotting (or plots explicitly disabled). No hypothetical result figures were generated.'}
"""
    (out / "results.md").write_text(text, encoding="utf-8")
    return dict(figures=len(figures), **checks)
