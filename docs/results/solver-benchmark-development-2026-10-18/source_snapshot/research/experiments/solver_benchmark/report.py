"""Regenerate descriptive tables and scientific figures from immutable run records."""

from collections import Counter
import csv
import json
from pathlib import Path
from statistics import median

from .cases import LARGE_EVENTS
from .common import CONFIGS, METHODS, read, save


def valid(row):
    return row.get("execution_status") == "completed" and row.get("valid") is True


def compare(a, b):
    # Difference is a minus b, with exactly matched event/configuration and coefficients.
    if not valid(a) or not valid(b):
        return None
    if a["weights"] != b["weights"] or a["registrations"] != b["registrations"]:
        raise ValueError("Cannot compare unlike objectives/populations")
    return (a["objective"] - b["objective"]) / a["registrations"] if a["registrations"] else None


def csv_table(path, rows, fields):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                             for key, value in row.items() if key in fields})


def report(out, plots=False):
    out = Path(out)
    manifest = read(out / "manifest.json")
    rows = []
    for job in manifest["jobs"]:
        path = out / "runs" / f"{job['id']}.json"
        rows.append(read(path) if path.exists() else {**job, "execution_status": "not_started", "valid": False})
    table_dir = out / "tables"
    table_dir.mkdir(exist_ok=True)
    groups = []
    for batch, budgets, configs, methods in (("primary", (5,), CONFIGS, METHODS),
                                             ("budget_sensitivity", (30, 60), tuple(CONFIGS)[:3], METHODS),
                                             ("prototype", (60,), ("current",), ("cp_sat",))):
        for budget in budgets:
            for config in configs:
                for method in methods:
                    selected = [r for r in rows if (r["batch"], r["budget_seconds"], r["configuration"], r["method"]) == (batch, budget, config, method)]
                    attempted = sum(r.get("execution_status") != "not_started" for r in selected)
                    passed = sum(valid(r) for r in selected)
                    groups.append({"batch": batch, "budget_seconds": budget, "configuration": config, "method": method,
                                   "planned": len(selected), "attempted": attempted, "validated": passed,
                                   "valid_rate_attempted": passed / attempted if attempted else None,
                                   "coverage": attempted / len(selected) if selected else None,
                                   "execution_statuses": dict(Counter(r.get("execution_status", "unknown") for r in selected)),
                                   "solver_statuses": dict(Counter(r.get("solver_status") or "unavailable" for r in selected))})
    indexed = {(r["event"], r["configuration"], r["method"], r["budget_seconds"]): r
               for r in rows if r["batch"] != "prototype"}
    pairs, hypothesis = [], []
    events = sorted({r["event"] for r in rows if r["batch"] == "primary"})
    for config in tuple(CONFIGS)[:3]:
        for other in ("greedy", "scip"):
            differences = []
            for event in events:
                a = indexed[event, config, "cp_sat", 5]
                b = indexed[event, config, other, 5]
                difference = compare(a, b)
                pairs.append({"event": event, "configuration": config, "comparator": other,
                              "cp_valid": valid(a), "comparator_valid": valid(b),
                              "difference_per_registration": difference,
                              "exclusion": None if difference is not None else "No both-valid complete pair"})
                if difference is not None:
                    differences.append(difference)
            hypothesis.append({"configuration": config, "comparator": other, "both_valid_pairs": len(differences),
                               "planned_pairs": len(events), "median_difference_per_registration": median(differences) if differences else None,
                               "cp_lower": sum(d < 0 for d in differences), "ties": sum(d == 0 for d in differences),
                               "cp_higher": sum(d > 0 for d in differences),
                               "interpretation": "not_estimable" if not differences else
                               ("supports_H1_in_this_configuration" if median(differences) < 0 else "does_not_support_H1_in_this_configuration") if other == "greedy" else "exploratory_SCIP_comparison"})
    contrasts = []
    for event in LARGE_EVENTS:
        for config in tuple(CONFIGS)[:3]:
            for method in METHODS:
                for earlier, later in ((5, 30), (30, 60)):
                    a, b = indexed[event, config, method, later], indexed[event, config, method, earlier]
                    observed = all(r.get("execution_status") == "completed" for r in (a, b))
                    contrasts.append({"event": event, "configuration": config, "method": method,
                                      "earlier_seconds": earlier, "later_seconds": later,
                                      "both_observed": observed, "earlier_valid": valid(b), "later_valid": valid(a),
                                      "new_valid_map": (valid(a) and not valid(b)) if observed else None,
                                      "lost_valid_map": (valid(b) and not valid(a)) if observed else None,
                                      "cost_difference_per_registration": compare(a, b),
                                      "earlier_proof": b.get("solver_status"), "later_proof": a.get("solver_status"),
                                      "exclusion": None if observed else "Unexecuted/interrupted/error record; not an observed budget effect"})
    summary = {"protocol": manifest["protocol"], "mode": manifest["mode"], "study_status": manifest["execution_status"],
               "groups": groups, "solver_pairs": pairs, "H1_and_RQ1": hypothesis, "budget_contrasts": contrasts,
               "limitations": ["Synthetic related cases, no repeated timing trials or population significance tests",
                               "Costs conditioned on both-valid pairs; inspect failures and coverage",
                               "Budget comparisons are fresh-run endpoints, not convergence traces",
                               "Prototype settings differ from controlled comparisons; human satisfaction not measured"]}
    save(out / "summary.json", summary)
    flat = [{**r, **r.get("timing", {})} for r in rows]
    fields = ["id", "batch", "event", "configuration", "method", "budget_seconds", "worker_count", "canonicalize",
              "execution_status", "solver_status", "valid", "registrations", "physical_seats", "weights", "objective",
              "cost_per_registration", "components", "component_means", "best_bound", "absolute_gap", "relative_gap",
              "preprocessing_seconds", "model_build_seconds", "search_seconds", "validation_scoring_seconds",
              "allocation_total_seconds", "service_return_seconds", "worker_elapsed_seconds"]
    csv_table(table_dir / "run-records.csv", flat, fields)
    csv_table(table_dir / "coverage.csv", groups, list(groups[0]))
    csv_table(table_dir / "paired-costs.csv", pairs, list(pairs[0]))
    csv_table(table_dir / "budget-contrasts.csv", contrasts, list(contrasts[0]))
    lines = ["# Solver-selection benchmark evidence", "", f"Protocol: `{manifest['protocol']}`. Mode: **{manifest['mode']}**. Status: **{manifest['execution_status']}**.",
             "", "All figures/tables derive from saved records. Pilot and correctness observations are separate from main-study evidence.", "",
             "| Batch | Budget (s) | Configuration | Method | Planned | Attempted | Validated |",
             "|---|---:|---|---|---:|---:|---:|"]
    for group in groups:
        lines.append("| " + " | ".join(str(group[k]) for k in ("batch", "budget_seconds", "configuration", "method", "planned", "attempted", "validated")) + " |")
    lines += ["", "## Paired common-cost comparisons", "", "Negative differences favor CP-SAT. Configurations remain separate; failed maps have no cost score.", "",
              "| Configuration | Comparator | Both valid | CP lower / tie / higher | Median difference per registration |",
              "|---|---|---:|---|---:|"]
    for h in hypothesis:
        value = h["median_difference_per_registration"]
        lines.append(f"| {h['configuration']} | {h['comparator']} | {h['both_valid_pairs']}/{h['planned_pairs']} | {h['cp_lower']} / {h['ties']} / {h['cp_higher']} | {value if value is not None else 'N/A'} |")
    lines += ["", "## Interpretation limits", ""] + [f"- {s}." for s in summary["limitations"]]
    if manifest.get("stop_reason"):
        lines += ["", f"Execution stopped: {manifest['stop_reason']}"]
    if manifest["mode"] in ("pilot", "check", "plan"):
        lines += ["", "**No main benchmark measurements were collected in this command.**"]
    (out / "results.md").write_text("\n".join(lines) + "\n")
    if plots:
        if manifest["mode"] != "run":
            raise ValueError("Main figures require a main-study bundle; pilot/check/plan outputs cannot masquerade as results")
        figures(out, manifest, rows, pairs, contrasts)
    return {"passed": True, "records": len(rows), "validated_comparative": sum(valid(r) for r in rows if r["batch"] != "prototype")}


def figures(out, manifest, rows, pairs, contrasts):
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(out / "plot-cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Rectangle
    directory = out / "figures"
    directory.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    colors = dict(zip(METHODS, ("#2463a6", "#c15a16", "#278248")))
    markers = dict(zip(METHODS, ("o", "s", "^")))
    def export(fig, name):
        fig.tight_layout()
        for extension in ("pdf", "svg", "png"):
            fig.savefig(directory / f"{name}.{extension}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    primary = {(r["event"], r["configuration"], r["method"]): r for r in rows if r["batch"] == "primary"}
    events = sorted({key[0] for key in primary})
    def outcome(r):
        if valid(r): return 0 if r.get("solver_status") == "OPTIMAL" else 1
        if r.get("execution_status") != "completed": return 5
        if r.get("placements") is not None: return 4
        return 3 if r.get("solver_status") == "CONSTRUCTION_FAILED" else 2
    fig, axes = plt.subplots(1, 4, figsize=(12, 5), sharey=True)
    for ax, config in zip(axes, CONFIGS):
        ax.imshow([[outcome(primary[e, config, m]) for m in METHODS] for e in events], vmin=0, vmax=5,
                  cmap=ListedColormap(("#175a2f", "#8bca96", "#e8b354", "#d57069", "#7f3b85", "#dddddd")), aspect="auto")
        ax.set_xticks(range(3), METHODS, rotation=35)
        ax.set_yticks(range(len(events)), events)
        ax.set_title(config)
    fig.suptitle("Five-second outcomes: dark green optimal; green valid; amber no map; red construction failure; purple invalid; gray incomplete", fontsize=9)
    export(fig, "figure-1-outcomes")
    fig, axes = plt.subplots(1, 3, figsize=(12, 5), sharey=True)
    for ax, config in zip(axes, tuple(CONFIGS)[:3]):
        for comparator, offset in (("greedy", -.12), ("scip", .12)):
            data = [r for r in pairs if r["configuration"] == config and r["comparator"] == comparator and r["difference_per_registration"] is not None]
            ax.scatter([r["difference_per_registration"] for r in data], [events.index(r["event"]) + offset for r in data],
                       label=f"vs {comparator} (n={len(data)})", marker=markers[comparator], color=colors[comparator])
        ax.axvline(0, color="gray", linewidth=.8)
        ax.set_yticks(range(len(events)), events)
        ax.set_title(config)
        ax.set_xlabel("(CP-SAT cost − comparator cost) / registrations")
        ax.legend(fontsize=7)
    export(fig, "figure-2-paired-costs")
    indexed = {(r["event"], r["configuration"], r["method"], r["budget_seconds"]): r for r in rows if r["batch"] != "prototype"}
    fig, axes = plt.subplots(3, 3, figsize=(12, 10))
    for col, config in enumerate(tuple(CONFIGS)[:3]):
        for method in METHODS:
            counts = [sum(valid(indexed[e, config, method, b]) for e in LARGE_EVENTS) for b in (5, 30, 60)]
            axes[0, col].plot((5, 30, 60), counts, marker=markers[method], color=colors[method], label=method)
            for x, (earlier, later) in enumerate(((5, 30), (30, 60))):
                for c in contrasts:
                    if (c["configuration"], c["method"], c["earlier_seconds"], c["later_seconds"]) == (config, method, earlier, later) and c["cost_difference_per_registration"] is not None:
                        axes[1, col].scatter(x + (METHODS.index(method) - 1) * .15, c["cost_difference_per_registration"], marker=markers[method], color=colors[method])
            for b in (5, 30, 60):
                for event in LARGE_EVENTS:
                    row = indexed[event, config, method, b]
                    elapsed = row.get("timing", {}).get("allocation_total_seconds")
                    if elapsed is not None:
                        axes[2, col].scatter(b, elapsed, marker=markers[method] if valid(row) else "x", color=colors[method])
        axes[0, col].set_title(config)
        axes[0, col].set_ylabel("Validated maps / 4 planned events")
        axes[0, col].set_ylim(-.1, 4.2)
        axes[0, col].set_xticks((5, 30, 60))
        axes[0, col].legend(fontsize=7)
        axes[1, col].axhline(0, color="gray", linewidth=.8)
        axes[1, col].set_xticks((0, 1), ("5→30", "30→60"))
        axes[1, col].set_ylabel("Paired cost change / registration")
        axes[2, col].set_xlabel("Configured search allowance (seconds)")
        axes[2, col].set_ylabel("Observed allocation total (seconds)")
    fig.suptitle("Fresh-run budget endpoints; count missing execution separately in coverage table; x = no valid returned map", fontsize=10)
    export(fig, "figure-3-budget-response")
    request = read(out / "inputs/heavy-mixed.json")
    fig, axes = plt.subplots(1, 3, figsize=(15, 10))
    tier_colors = {"EMPEROR": "#e8c464", "MERIT": "#86b9e4", "BODHI": "#a4ce9a"}
    people = {p["participant_id"]: p for p in request["participants"]}
    for ax, method in zip(axes, METHODS):
        row = primary["heavy-mixed", "current", method]
        if not valid(row):
            ax.text(.5, .5, f"No validated map\n{row.get('solver_status', row['execution_status'])}", ha="center", transform=ax.transAxes)
            ax.axis("off")
            ax.set_title(method)
            continue
        occupants = {sid: a["participant_id"] for a in row["placements"] for sid in a["seat_ids"]}
        lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
        for seat in lookup.values():
            x = seat["physical_position"] + (1 if seat["physical_position"] > 8 else 0)
            y = seat["row_number"]
            pid = occupants.get(seat["seat_id"])
            color = "#777777" if seat["is_blocked"] else tier_colors[people[pid]["contribution_tier"]] if pid else "white"
            ax.add_patch(Rectangle((x, y), .9, .8, facecolor=color, edgecolor="gray", linewidth=.4))
            if pid:
                ax.text(x + .45, y + .4, pid[-3:], ha="center", va="center", fontsize=4)
        for assignment in row["placements"]:
            if len(assignment["seat_ids"]) == 2:
                seat = min((lookup[s] for s in assignment["seat_ids"]), key=lambda s: s["physical_position"])
                x = seat["physical_position"] + (1 if seat["physical_position"] > 8 else 0)
                ax.add_patch(Rectangle((x-.04, seat["row_number"]-.04), 1.98, .88, fill=False, edgecolor="black", linewidth=.8))
        ax.set_xlim(.5, 18.5)
        ax.set_ylim(request["layout"]["row_count"] + 1, .5)
        ax.set_aspect("equal")
        ax.set_title(f"{method}: {row['solver_status']}\ncost={row['objective']}, total={row['timing']['allocation_total_seconds']:.2f}s")
        ax.set_xlabel("Physical seats; center aisle")
        ax.set_ylabel("Row (front at top)")
    fig.suptitle("230 seats: 99 Emperor pairs, 19 Merit, 13 Bodhi; current preference order; five-second search")
    export(fig, "illustration-230-seat")
