"""Render Study A from saved records only; this module never invokes a solver.

The output is a separate, self-contained presentation revision. The original
evidence bundle, including its historical figures and source snapshots, is read
only. Study B is documented separately and has no generated result figures.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import shutil
import textwrap
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
import numpy as np
from pypdf import PdfReader, PdfWriter


PACKAGE = "pjkit-study-a-saved-record-figures-v1"
METHODS = ("cp_sat", "scip", "greedy")
NAMES = {"cp_sat": "CP-SAT", "scip": "SCIP", "greedy": "Greedy"}
COLORS = {"cp_sat": "#2463a6", "scip": "#bd591b", "greedy": "#267b50"}
MARKERS = {"cp_sat": "o", "scip": "s", "greedy": "^"}
CONFIGS = ("current", "reversed", "two", "disabled")
CONFIG_NAMES = {
    "current": "Current: contribution > activity > category",
    "reversed": "Reversed: category > activity > contribution",
    "two": "Two: contribution > category; activity off",
    "disabled": "All ordinary preferences disabled",
}
WEIGHTS = {
    "current": {"contribution_seat": 4, "activeness": 3, "category_zone": 2},
    "reversed": {"contribution_seat": 2, "activeness": 3, "category_zone": 4},
    "two": {"contribution_seat": 4, "activeness": 0, "category_zone": 3},
    "disabled": {"contribution_seat": 0, "activeness": 0, "category_zone": 0},
}
LARGE = ("high-mixed", "near-mixed", "full-mixed", "heavy-mixed")
STATUSES = ("OPTIMAL", "FEASIBLE", "NO_MAP", "CONSTRUCTION_FAILED", "INVALID", "INCOMPLETE")
STATUS_COLORS = ("#175a2f", "#a5d5ab", "#f0c66a", "#dd8b82", "#aa7dc2", "#d6d8dc")
STATUS_CODES = ("O", "F", "U", "C", "I", "E")
STATUS_LABELS = (
    "O: validated optimal", "F: validated feasible", "U: no validated map",
    "C: construction failure", "I: invalid output", "E: incomplete execution",
)
FIGURES = (
    ("a1-five-second-outcomes", "Five-second outcomes on the complete primary cohort"),
    ("a2-matched-budget-outcomes", "Matched outcomes at 5, 30 and 60 seconds"),
    ("a3-paired-preference-costs", "Paired preference-penalty differences"),
    ("a4-budget-response", "Coverage, paired cost changes and observed allocation time"),
    ("a5-phase-timing-60s", "Recorded allocation phases at the 60-second search allowance"),
    ("a6-230-seat-60s", "The 230-seat case at a common 60-second search allowance"),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path):
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    for row in rows:
        for field in ("budget_seconds", "worker_count", "registrations", "physical_seats"):
            row[field] = int(row[field])
        for field in ("valid", "canonicalize"):
            if row[field] not in ("True", "False"):
                raise ValueError(f"Unexpected Boolean {field}: {row[field]}")
            row[field] = row[field] == "True"
        for field in ("objective", "cost_per_registration", "preprocessing_seconds", "model_build_seconds",
                      "search_seconds", "extraction_seconds", "validation_scoring_seconds",
                      "allocation_total_seconds", "service_return_seconds", "worker_elapsed_seconds"):
            row[field] = float(row[field]) if row[field] else None
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate source run IDs")
    return rows


def outcome(row):
    if row["execution_status"] != "completed":
        return "INCOMPLETE"
    if row["valid"]:
        if row["solver_status"] not in ("OPTIMAL", "FEASIBLE"):
            raise ValueError("Validated record has an unexpected solver status")
        return row["solver_status"]
    if row["objective"] is not None:
        return "INVALID"
    return "CONSTRUCTION_FAILED" if row["solver_status"] == "CONSTRUCTION_FAILED" else "NO_MAP"


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def event_label(event):
    return "Emperor-heavy / mixed" if event == "heavy-mixed" else event.replace("-", " / ")


def event_sort(event):
    size, pattern = event.split("-", 1)
    return (("small", "typical", "high", "near", "heavy", "full").index(size),
            ("mixed", "conflict", "tied", "accessible").index(pattern))


def footer(fig, message, width=150, y=.012):
    fig.text(.5, y, textwrap.fill(message, width), ha="center", va="bottom", fontsize=8.2, color="#434a54")


def legend_outcomes(fig, y=.075):
    handles = [Patch(facecolor=color, edgecolor="white", label=label)
               for color, label in zip(STATUS_COLORS, STATUS_LABELS)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, y), ncol=3,
               frameon=False, fontsize=8.8, columnspacing=2)


def status_grid(ax, grid, row_labels, col_labels, show_rows=True):
    codes = np.array([[STATUSES.index(s) for s in line] for line in grid])
    ax.imshow(codes, cmap=ListedColormap(STATUS_COLORS), vmin=0, vmax=5, aspect="auto")
    ax.set_xticks(range(len(col_labels)), col_labels)
    ax.set_yticks(range(len(row_labels)), row_labels if show_rows else [])
    ax.set_xticks(np.arange(-.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6)
    ax.tick_params(which="both", length=0, labelsize=9)
    for y, line in enumerate(codes):
        for x, code in enumerate(line):
            ax.text(x, y, STATUS_CODES[code], ha="center", va="center", fontsize=9,
                    color="white" if code == 0 else "#17212b", weight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)


def export(fig, output, name):
    for extension in ("pdf", "svg", "png"):
        fig.savefig(output / "figures" / f"{name}.{extension}", dpi=300, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig)


def render_primary(output, index, events):
    fig, axes = plt.subplots(1, 4, figsize=(14, 10.5))
    fig.subplots_adjust(left=.15, right=.99, top=.90, bottom=.15, wspace=.14)
    for i, (ax, config) in enumerate(zip(axes, CONFIGS)):
        grid = [[outcome(index[e, config, method, 5]) for method in METHODS] for e in events]
        status_grid(ax, grid, [event_label(e) for e in events], [NAMES[m] for m in METHODS], i == 0)
        ax.set_title(textwrap.fill(CONFIG_NAMES[config], 30), fontsize=10, pad=12)
    fig.suptitle("Study A | Complete primary cohort: five-second search allowance", fontsize=16, y=.98)
    legend_outcomes(fig, .065)
    footer(fig, "21 events per setting; one worker; no canonicalization. Letters preserve outcome distinctions in grayscale. "
           "No invalid outputs or incomplete scheduled executions occurred. Disabled preferences are a feasibility control.")
    export(fig, output, FIGURES[0][0])


def render_matched(output, index):
    labels = [f"{event_label(e)} / {NAMES[m]}" for e in LARGE for m in METHODS]
    fig, axes = plt.subplots(1, 3, figsize=(14, 7.6))
    fig.subplots_adjust(left=.20, right=.99, top=.86, bottom=.20, wspace=.12)
    for i, (ax, config) in enumerate(zip(axes, CONFIGS[:3])):
        grid = [[outcome(index[e, config, m, b]) for b in (5, 30, 60)] for e in LARGE for m in METHODS]
        status_grid(ax, grid, labels, ["5 s", "30 s", "60 s"], i == 0)
        for boundary in (2.5, 5.5, 8.5):
            ax.axhline(boundary, color="#687280", linewidth=1)
        ax.set_title(textwrap.fill(CONFIG_NAMES[config], 34), fontsize=10, pad=12)
        ax.set_xlabel("Configured search allowance")
    fig.suptitle("Study A | Matched outcomes as search allowance increases", fontsize=16, y=.98)
    legend_outcomes(fig, .075)
    footer(fig, "Only four predefined large mixed-profile events and three active preference settings were tested at every allowance. "
           "Each column is a fresh run. Other events and the disabled setting were not tested at 30/60 seconds.", width=145)
    export(fig, output, FIGURES[1][0])


def make_pairs(index, events):
    rows = []
    for config in CONFIGS[:3]:
        for event in events:
            cp = index[event, config, "cp_sat", 5]
            for method in ("greedy", "scip"):
                other = index[event, config, method, 5]
                both = cp["valid"] and other["valid"]
                rows.append(dict(event=event, configuration=config, comparator=method, registrations=cp["registrations"],
                                 both_valid=both, cp_status=cp["solver_status"], comparator_status=other["solver_status"],
                                 cp_cost=cp["objective"] if cp["valid"] else None,
                                 comparator_cost=other["objective"] if other["valid"] else None,
                                 difference_per_registration=(cp["objective"] - other["objective"]) / cp["registrations"] if both else None))
    return rows


def render_pairs(output, pairs, events):
    bound = max(5, math.ceil(max(abs(p["difference_per_registration"]) for p in pairs if p["both_valid"]) / 5) * 5)
    fig, axes = plt.subplots(1, 3, figsize=(14, 10.3), sharex=True)
    fig.subplots_adjust(left=.16, right=.99, top=.87, bottom=.12, wspace=.12)
    for col, (ax, config) in enumerate(zip(axes, CONFIGS[:3])):
        ax.axvspan(-bound, 0, color="#f4f7fb", zorder=0)
        ax.axvline(0, color="#59636e", linewidth=1)
        for method, offset in (("greedy", .14), ("scip", -.14)):
            selected = [p for p in pairs if p["configuration"] == config and p["comparator"] == method and p["both_valid"]]
            ax.scatter([p["difference_per_registration"] for p in selected],
                       [events.index(p["event"]) + offset for p in selected], marker=MARKERS[method],
                       color=COLORS[method], s=43, zorder=3,
                       label=f"vs {NAMES[method]}: {len(selected)}/21 pairs")
        ax.set_xlim(-bound - 2, bound + 2)
        ax.set_ylim(len(events) - .5, -.5)
        ax.set_yticks(range(len(events)), [event_label(e) for e in events] if col == 0 else [])
        ax.grid(axis="y", color="#e9edf1", linewidth=.6)
        ax.set_xlabel("(CP-SAT penalty - comparator penalty)\nper registration", fontsize=10)
        ax.set_title(textwrap.fill(CONFIG_NAMES[config], 35), fontsize=10, pad=30)
        ax.text(.24, 1.012, "CP-SAT lower", transform=ax.transAxes, ha="center", fontsize=9, color=COLORS["cp_sat"])
        ax.text(.77, 1.012, "Comparator lower", transform=ax.transAxes, ha="center", fontsize=9, color="#744526")
        ax.legend(loc="lower right", fontsize=8, framealpha=.95)
        ax.tick_params(labelsize=9)
    fig.suptitle("Study A | Paired preference penalties at five-second search", fontsize=16, y=.98)
    footer(fig, "Zero means equal modeled penalties, not zero-cost seating or a presumed optimum. Blank rows have no both-valid pair. "
           "CP-SAT is the subtraction reference only. Settings use different weights and must not be pooled into one quality score.", width=155)
    export(fig, output, FIGURES[2][0])


def budget_tables(index):
    coverage, contrasts = [], []
    for config in CONFIGS[:3]:
        for method in METHODS:
            for budget in (5, 30, 60):
                rows = [index[e, config, method, budget] for e in LARGE]
                counts = Counter(outcome(r) for r in rows)
                coverage.append(dict(configuration=config, method=method, budget_seconds=budget, planned=4,
                                     attempted=sum(r["execution_status"] != "not_started" for r in rows),
                                     completed=sum(r["execution_status"] == "completed" for r in rows),
                                     not_started=sum(r["execution_status"] == "not_started" for r in rows),
                                     validated=sum(r["valid"] for r in rows),
                                     **{s.lower(): counts[s] for s in STATUSES}))
            for event in LARGE:
                for earlier, later in ((5, 30), (30, 60)):
                    a, b = index[event, config, method, earlier], index[event, config, method, later]
                    both = a["valid"] and b["valid"]
                    contrasts.append(dict(event=event, configuration=config, method=method, earlier_seconds=earlier,
                                          later_seconds=later, earlier_valid=a["valid"], later_valid=b["valid"], both_valid=both,
                                          cost_change_per_registration=(b["objective"] - a["objective"]) / a["registrations"] if both else None,
                                          earlier_status=a["solver_status"], later_status=b["solver_status"]))
    return coverage, contrasts


def render_budgets(output, index, contrasts):
    fig, axes = plt.subplots(3, 3, figsize=(14, 11.8))
    fig.subplots_adjust(left=.075, right=.985, top=.91, bottom=.14, wspace=.25, hspace=.40)
    for col, config in enumerate(CONFIGS[:3]):
        top, middle, bottom = axes[:, col]
        for mi, method in enumerate(METHODS):
            counts = [sum(index[e, config, method, b]["valid"] for e in LARGE) for b in (5, 30, 60)]
            top.plot((5, 30, 60), counts, marker=MARKERS[method], color=COLORS[method], linewidth=1.5, label=NAMES[method])
            for b, count in zip((5, 30, 60), counts):
                offset = 8 if method == "scip" and count == 0 else (8, -15, 10)[mi]
                top.annotate(f"{count}/4", (b, count), xytext=(0, offset),
                             textcoords="offset points", ha="center", fontsize=8, color=COLORS[method])
            for ci, (earlier, later) in enumerate(((5, 30), (30, 60))):
                selected = [r for r in contrasts if (r["configuration"], r["method"], r["earlier_seconds"], r["later_seconds"])
                            == (config, method, earlier, later) and r["both_valid"]]
                xs = [ci + (mi - 1) * .18 + (LARGE.index(r["event"]) - 1.5) * .025 for r in selected]
                middle.scatter(xs, [r["cost_change_per_registration"] for r in selected],
                               marker=MARKERS[method], color=COLORS[method], s=35, zorder=3)
            for budget in (5, 30, 60):
                for event in LARGE:
                    row = index[event, config, method, budget]
                    bottom.scatter(budget, row["allocation_total_seconds"], marker=MARKERS[method] if row["valid"] else "x",
                                   color=COLORS[method], s=34, linewidths=1.2)
        top.set_title(textwrap.fill(CONFIG_NAMES[config], 36), fontsize=10, pad=10)
        top.set_ylim(-.25, 4.75)
        top.set_yticks(range(5))
        top.set_ylabel("Validated maps / 4 events")
        middle.axhline(0, color="#59636e", linewidth=1)
        middle.set_xticks((0, 1), ("5 to 30 s", "30 to 60 s"))
        middle.set_xlim(-.4, 1.4)
        middle.set_ylabel("Paired penalty change\nper registration")
        bottom.set_ylabel("Observed allocation total (s)")
        bottom.set_xlabel("Configured search allowance (s)")
        bottom.set_ylim(-2, 73)
        for ax in (top, bottom):
            ax.set_xticks((5, 30, 60))
            ax.set_xlim(1, 64)
        for ax in (top, middle, bottom):
            ax.grid(axis="y", color="#e9edf1", linewidth=.7)
            ax.tick_params(labelsize=9)
    fig.suptitle("Study A | Fresh-run budget endpoints: availability, quality and elapsed time", fontsize=15, y=.98)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .065), ncol=3, frameon=False, fontsize=9)
    footer(fig, "Same four large mixed events; one worker; no canonicalization. Middle = (later - earlier) penalty / registrations, "
           "both-valid only; negative means lower penalty. "
           "Bottom row includes all executions; x marks no validated map. Endpoints are not a continuous solve trajectory or a time-to-first-solution trace.", width=160)
    export(fig, output, FIGURES[3][0])


def phase_rows(index):
    result = []
    fields = ("preprocessing_seconds", "model_build_seconds", "search_seconds", "extraction_seconds", "validation_scoring_seconds")
    for config in CONFIGS[:3]:
        for event in LARGE:
            for method in METHODS:
                row = index[event, config, method, 60]
                parts = {field: row[field] for field in fields}
                if any(v is None or not math.isfinite(v) or v < 0 for v in parts.values()):
                    raise ValueError("Missing/negative/nonfinite recorded phase")
                residual = row["allocation_total_seconds"] - sum(parts.values())
                if residual < -1e-6:
                    raise ValueError(f"Overlapping phase measurements: {row['id']}: {residual}")
                result.append(dict(event=event, configuration=config, method=method, outcome=outcome(row),
                                   **parts, other_recorded_overhead=max(0., residual),
                                   allocation_total_seconds=row["allocation_total_seconds"]))
    return result


def render_phases(output, phases):
    keys = ("preprocessing_seconds", "model_build_seconds", "search_seconds", "extraction_seconds",
            "validation_scoring_seconds", "other_recorded_overhead")
    labels = ("Shared preprocessing", "Model/construction", "Search call", "Extraction", "Validation/scoring", "Other elapsed overhead")
    colors = ("#97c5c3", "#547caa", "#df9a48", "#a68cb7", "#77a36b", "#b7bbc1")
    fig, axes = plt.subplots(1, 3, figsize=(14, 8))
    fig.subplots_adjust(left=.19, right=.98, top=.85, bottom=.20, wspace=.12)
    for col, (ax, config) in enumerate(zip(axes, CONFIGS[:3])):
        selected = [p for p in phases if p["configuration"] == config]
        left = np.zeros(len(selected))
        for key, color in zip(keys, colors):
            vals = np.array([p[key] for p in selected])
            ax.barh(range(len(selected)), vals, left=left, color=color, height=.73)
            left += vals
        for i, row in enumerate(selected):
            ax.text(row["allocation_total_seconds"] + .7, i, STATUS_CODES[STATUSES.index(row["outcome"])], va="center", fontsize=8)
        ax.set_yticks(range(len(selected)),
                      [f"{event_label(p['event'])} / {NAMES[p['method']]}" for p in selected] if col == 0 else [])
        ax.set_ylim(len(selected) - .5, -.5)
        ax.set_xlim(0, 73)
        for boundary in (2.5, 5.5, 8.5):
            ax.axhline(boundary, color="#d9dee5", linewidth=.6)
        ax.set_title(textwrap.fill(CONFIG_NAMES[config], 35), fontsize=10, pad=12)
        ax.set_xlabel("Recorded allocation time (s)")
        ax.grid(axis="x", color="#e9edf1", linewidth=.5)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=9)
    fig.suptitle("Study A | Where allocation time was spent at the 60-second search allowance", fontsize=15, y=.98)
    fig.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(colors, labels)],
               loc="lower center", bbox_to_anchor=(.5, .085), ncol=3, frameon=False, fontsize=9)
    footer(fig, "Each bar is one saved execution, not an average. O = validated optimal; F = validated feasible; C = construction failure. "
           "Native presolve is inside the search call; these measurements do not isolate a SCIP startup phase. No service/network timing is included.", width=160)
    export(fig, output, FIGURES[4][0])


def verify_map(request, raw, csv_row):
    if raw["valid"] != csv_row["valid"] or raw["solver_status"] != csv_row["solver_status"] or raw["objective"] != csv_row["objective"]:
        raise ValueError("Seat-map source disagrees with source CSV")
    if not raw["valid"]:
        if raw.get("placements") is not None:
            raise ValueError("Unexpected invalid placements in selected illustration")
        return
    if not raw["validation"]["passed"]:
        raise ValueError("Selected placement lacks its saved independent audit")
    people = {p["participant_id"]: p for p in request["participants"]}
    seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
    assignments = raw["placements"]
    if Counter(a["participant_id"] for a in assignments) != Counter(people.keys()):
        raise ValueError("Seat illustration does not cover every registration exactly once")
    used = [s for a in assignments for s in a["seat_ids"]]
    if len(used) != 230 or len(set(used)) != 230:
        raise ValueError("Wrong demand or overlapping seats")
    approved = {tuple(pair) for pair in request["layout"]["approved_pairs"]}
    for a in assignments:
        person, bundle = people[a["participant_id"]], [seats[s] for s in a["seat_ids"]]
        if any(s["is_blocked"] for s in bundle):
            raise ValueError("Blocked seat in illustration")
        if len(bundle) != (2 if person["contribution_tier"] == "EMPEROR" else 1):
            raise ValueError("Incorrect entitlement")
        if person["requires_accessible_seat"] and not all(s["is_accessible"] for s in bundle):
            raise ValueError("Inaccessible selected bundle")
        if len(bundle) == 2:
            if bundle[0]["row_number"] != bundle[1]["row_number"] or tuple(sorted(s["physical_position"] for s in bundle)) not in approved:
                raise ValueError("Invalid Emperor pair")


def render_map(output, source, index):
    request = json.loads((source / "inputs/heavy-mixed.json").read_text())
    people = {p["participant_id"]: p for p in request["participants"]}
    if Counter(p["contribution_tier"] for p in people.values()) != Counter(EMPEROR=99, MERIT=19, BODHI=13):
        raise ValueError("Incorrect heavy-event composition")
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    tier_colors = {"EMPEROR": "#e9c66d", "MERIT": "#8db8db", "BODHI": "#a5c995"}
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 8.1))
    fig.subplots_adjust(left=.04, right=.985, top=.82, bottom=.18, wspace=.13)
    for ax, method in zip(axes, METHODS):
        row = index["heavy-mixed", "current", method, 60]
        raw = json.loads((source / "runs" / f"{row['id']}.json").read_text())
        verify_map(request, raw, row)
        ax.set_box_aspect(16 / 17)
        ax.set_xlim(.45, 17.55)
        ax.set_ylim(16.9, .4)
        title = f"{NAMES[method]}: {row['solver_status']}\n"
        title += f"Penalty: {int(row['objective']):,}\n" if row["valid"] else "Penalty: unavailable\n"
        title += f"Observed allocation total: {row['allocation_total_seconds']:.2f} s"
        ax.set_title(title, fontsize=11, pad=16)
        if not row["valid"]:
            ax.text(.5, .54, "No validated seating map\n\nConstruction dead end\nat the 60-second endpoint",
                    transform=ax.transAxes, ha="center", va="center", fontsize=13, color="#6d3c36")
            ax.set_axis_off()
            continue
        occupants = {sid: a["participant_id"] for a in raw["placements"] for sid in a["seat_ids"]}
        for seat in lookup.values():
            x = seat["physical_position"] + (seat["physical_position"] > 8)
            y = seat["row_number"]
            pid = occupants.get(seat["seat_id"])
            color = "#7b7f84" if seat["is_blocked"] else tier_colors[people[pid]["contribution_tier"]] if pid else "white"
            ax.add_patch(Rectangle((x - .43, y - .35), .86, .70, facecolor=color, edgecolor="#70757d", linewidth=.45))
            if pid:
                ax.text(x, y, pid[-3:], ha="center", va="center", fontsize=5.2, color="#252b33")
        for assignment in raw["placements"]:
            if len(assignment["seat_ids"]) == 2:
                seat = min((lookup[s] for s in assignment["seat_ids"]), key=lambda s: s["physical_position"])
                x = seat["physical_position"] + (seat["physical_position"] > 8)
                ax.add_patch(Rectangle((x - .47, seat["row_number"] - .39), 1.94, .78, fill=False, edgecolor="#222", linewidth=.65))
        ax.set_xticks([x + (x > 8) for x in range(1, 17)], range(1, 17))
        ax.set_yticks(range(1, 17))
        ax.tick_params(length=0, labelsize=7)
        ax.set_xlabel("Physical seat position; central aisle", fontsize=9)
        ax.set_ylabel("Row (front at top)", fontsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Study A | The 230-seat event at a common 60-second search allowance", fontsize=16, y=.98)
    fig.text(.5, .928, "99 Emperor registrations (198 seats), 19 Merit and 13 Bodhi; 131 registration units; current preference order",
             ha="center", fontsize=11)
    fig.legend(handles=[Patch(facecolor=c, edgecolor="#777", label=t.title()) for t, c in tier_colors.items()] +
               [Patch(facecolor="#7b7f84", label="Blocked"), Patch(facecolor="white", edgecolor="#777", label="Unused usable seat"),
                Patch(facecolor="none", edgecolor="#222", label="Emperor pair outline")],
               loc="lower center", bbox_to_anchor=(.5, .075), ncol=6, frameon=False, fontsize=9)
    footer(fig, "Identical controlled settings: one worker; no canonicalization; fresh 60-second searches. CP-SAT remained feasible without proof; "
           "SCIP proved the minimum. Greedy returned no map. Registration numbers identify placements, not preference quality.", width=165)
    export(fig, output, FIGURES[5][0])


def make_readme(output, source, date, checks):
    gallery = "\n\n".join(f"### {name.upper()}: {title}\n\n![{title}](figures/{name}.png)\n\n"
                           f"[PDF](figures/{name}.pdf) | [SVG](figures/{name}.svg) | [PNG](figures/{name}.png)"
                           for name, title in FIGURES)
    text = f"""# Study A: expanded attempt 3 figure package

Presentation revision: {date} (Asia/Kuala_Lumpur). **Saved-record postprocessing only. No solver was invoked.**

[Combined vector PDF](attempt3-figure-package.pdf) | [Checks](checks.json) | [Provenance](manifest.json)

## Separation of the two studies

- **Study A is completed evidence:** the attempt 3 Windows benchmark, with 252 primary five-second runs, 72 additional 30/60-second runs and four separate production-path checks. There were no seed repetitions. Controlled comparisons use one worker and no canonicalization.
- **Study B is a confirmed future study:** production CP-SAT versus SCIP, with verified up-to-eight-thread preference optimization, shared canonical selection and service/regeneration checks. It has not been implemented or executed. Its [figure and measurement plan](../../planning/solver-selection-production-follow-up.md) contains no result figures or invented measurements.
- Four old CP-SAT production checks are retained in the source CSV for completeness. They are not Study B results and are excluded from the controlled plots.

The original evidence directory is `{source}`. It was not changed. `source-data/` copies only the saved table, heavy-event input, selected map records and original manifest needed for this package; it is not a replacement for the full original evidence bundle.

The common benchmark coefficients for (contribution, activity, category) are current **(4, 3, 2)**, reversed **(2, 3, 4)**, two **(4, 0, 3)** and disabled **(0, 0, 0)**. All methods in a setting use the same scorer. The denominator is registration units, including one registration for each two-seat Emperor pair. These are the saved benchmark's coefficients, not the production example's 40:30:20 current-order scale; the older prototype's common rescored cost must not be confused with its native service objective or timing.

## What changed

1. A1 retains all 21 events and four preference settings at five seconds, with explicit status letters and consistent colors.
2. A2 adds a matched 5/30/60-second status matrix for the four large mixed events and three active preference settings. Other long-budget cases were not tested, not failures.
3. A3 labels both directions of the paired penalty difference. Zero means equal penalties; it does not assume CP-SAT is optimal. Missing pairs remain unavailable.
4. A4 retains coverage, within-method paired penalty changes and actual allocation time, labelled as separate fresh-run endpoints. It is not a convergence or first-solution trace.
5. A5 adds the recorded phase breakdown. Native presolve remains inside search; these records do not identify a causal SCIP startup limitation.
6. A6 replaces the five-second-only main illustration with the common 60-second endpoint. It shows the saved CP-SAT FEASIBLE map, SCIP OPTIMAL map and greedy construction failure, without changing or fabricating their statuses.

## Interpretation and captions

### Coverage

The complete primary cohort contains 21 events per preference setting. The matched budget cohort contains four events per active setting, or 12 matched event-setting cases. It has CP-SAT validated counts 8/12, 12/12, 12/12; SCIP 2/12, 12/12, 12/12; and greedy 2/12 at every allowance. All 12 SCIP 30- and 60-second results are OPTIMAL; CP-SAT remains FEASIBLE on those endpoints.

No invalid returned allocations or incomplete scheduled executions occurred in the 328 saved jobs. An UNKNOWN/no-map outcome is not an invalid allocation or a proof of infeasibility. Additional unscheduled long-budget events must never be colored as failed or incomplete trials.

### Paired preference penalties

A3 uses `(CP-SAT penalty - comparator penalty) / registrations` on the same event and setting, conditional on both maps being validated. Negative favors CP-SAT; positive favors the comparator; zero is a tie. CP-SAT is an arithmetic reference, not a presumed optimum. Active pair counts are 26 against SCIP and 11 against greedy. CP-SAT lower/tied/higher counts against SCIP are 0/13/13; all 11 greedy pairs favor CP-SAT's penalty. These conditional quality comparisons do not replace availability reporting. All-disabled costs are omitted. Different setting weights must not be pooled into one quality scale.

### Search allowance and actual elapsed time

Across the same 12 cases, CP-SAT median allocation totals are approximately 10.52, 35.62 and 65.64 seconds at 5/30/60-second search allowances. SCIP medians are 5.42, 10.80 and 10.76 seconds; greedy medians are 0.88, 0.90 and 0.86 seconds. These include unsuccessful executions, with no-map markers retained in A4.

CP-SAT generally consumes its search allowance without proving the optimum on this subset. SCIP returns after proving the optimum, so 30 and 60 seconds give similar observed times. Greedy terminates on success or an irreversible construction dead end. The data support search-budget response, not a demonstrated SCIP startup delay or a continuous time-to-first-map curve. One fresh run per endpoint cannot estimate repeated-run timing variance.

### The 230-seat illustration

A6 uses the same controlled 60-second search allowance for every method. CP-SAT returned cost 21,679 in 66.729 seconds, FEASIBLE. SCIP returned cost 20,515 in 8.390 seconds, OPTIMAL. Greedy returned no map in 0.797 seconds. The selected physical allocations are checked against their saved audit and CSV, full registration coverage, entitlement, physical-seat uniqueness, blocked seats, accessibility and approved pairs.

The older eight-worker CP-SAT production check also attained common cost 20,515, but with incomplete canonicalization and different settings. It is not substituted into the controlled comparison. No saved comparable first-optimal timestamp exists. The future study must measure weighted-objective stage completion, canonical completion and complete service return separately.

### Dissertation and technical-paper use

Use A1/A2 for availability and proof outcomes, A3 for matched quality, A4 for budget response, and A6 as the main physical illustration. A5 is a supporting timing figure suitable for an appendix or for a timing-focused discussion. Keep every figure's cohort, settings and missing comparisons in its caption. These are descriptive results for related synthetic events, not human satisfaction measurements, statistical population estimates or universal solver rankings.

## Reproduce without running experiments

Requires Python, matplotlib, numpy and pypdf. The renderer imports no optimization library and does not call the service or an experiment runner.

```sh
python research/experiments/solver_selection_figures.py --source docs/results/solver-selection-v4-attempt3-figures-2026-10-23/source-data --output /tmp/pjkit-study-a-reproduced --analysis-date {date}
```

Alternatively run the identical archived renderer at `source_snapshot/solver_selection_figures.py`. Existing output directories are rejected unless `--overwrite` explicitly selects an existing package generated by this renderer. Source data cannot be overwritten. Figure exports are PDF/SVG/300-dpi PNG; the combined PDF contains the same six vector figure pages.

## Verification

{checks['source_run_count']} source records; {checks['primary_run_count']} primary, {checks['long_budget_run_count']} long-budget, {checks['prototype_run_count']} separate prototype. All source statuses and cohort combinations were checked. The execution-coverage table separates completed execution from map availability; the matched-budget table uses only its predefined four-event cohort. Paired values were cross-checked against the original paired table. Controlled OPTIMAL records have objective/bound agreement and negligible gaps within an absolute tolerance of 1e-6 objective units; one SCIP record has a floating-point gap of about 9e-13. Prototype CSV bounds are absent and were excluded from that check as well as from the plots. Timing phases reconcile to their totals with explicit residual overhead. Original source hashes are checked again after rendering. See `checks.json` and `tables/` for exact values.

## Figures

{gallery}
"""
    (output / "README.md").write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--analysis-date", required=True, help="Client-local YYYY-MM-DD")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Source and output must be separate, non-nested directories")
    if output.exists():
        marker = output / "manifest.json"
        if not args.overwrite or not marker.exists() or json.loads(marker.read_text()).get("package") != PACKAGE:
            raise ValueError("Output already exists; only an explicitly selected generated package may be overwritten")
    source_files = [Path("tables/run-records.csv"), Path("tables/paired-costs.csv"), Path("inputs/heavy-mixed.json"), Path("manifest.json")]
    source_files += [Path(f"runs/budget_sensitivity__heavy-mixed__current__{m}__60s.json") for m in METHODS]
    hashes = {str(path): sha256(source / path) for path in source_files}
    rows = load_rows(source / "tables/run-records.csv")
    batch_counts = Counter(r["batch"] for r in rows)
    if batch_counts != Counter(primary=252, budget_sensitivity=72, prototype=4):
        raise ValueError(f"Unexpected attempt 3 inventory: {batch_counts}")
    if json.loads((source / "manifest.json").read_text())["execution_status"] != "completed":
        raise ValueError("Source is not the completed attempt 3 study")
    if any(r["execution_status"] != "completed" for r in rows):
        raise ValueError("Expected completed attempt 3 records")
    for row in rows:
        if row["batch"] != "prototype" and row["solver_status"] == "OPTIMAL":
            if (not row["valid"] or not math.isclose(float(row["best_bound"]), row["objective"], abs_tol=1e-6, rel_tol=0)
                    or not 0 <= float(row["absolute_gap"]) <= 1e-6 or not 0 <= float(row["relative_gap"]) <= 1e-6):
                raise ValueError(f"Controlled optimal label lacks matching bound: {row['id']}")
    controlled = [r for r in rows if r["batch"] != "prototype"]
    if any(r["worker_count"] != 1 or r["canonicalize"] for r in controlled):
        raise ValueError("Controlled plots require one worker and no canonicalization")
    if any(json.loads(r["weights"]) != WEIGHTS[r["configuration"]] for r in controlled):
        raise ValueError("Controlled comparison has unexpected objective coefficients")
    index = {(r["event"], r["configuration"], r["method"], r["budget_seconds"]): r for r in controlled}
    events = sorted({r["event"] for r in rows if r["batch"] == "primary"}, key=event_sort)
    if len(events) != 21:
        raise ValueError("Expected 21 primary events")
    expected = {(e, c, m, 5) for e in events for c in CONFIGS for m in METHODS}
    expected |= {(e, c, m, b) for e in LARGE for c in CONFIGS[:3] for m in METHODS for b in (30, 60)}
    if set(index) != expected:
        raise ValueError("Cohort or scheduled-combination mismatch")
    pairs = make_pairs(index, events)
    original_pairs = list(csv.DictReader((source / "tables/paired-costs.csv").open()))
    original = {(p["event"], p["configuration"], p["comparator"]): p for p in original_pairs}
    for p in pairs:
        reference = original[p["event"], p["configuration"], p["comparator"]]["difference_per_registration"]
        if p["both_valid"]:
            if not reference or not math.isclose(float(reference), p["difference_per_registration"], abs_tol=1e-9):
                raise ValueError("Recomputed pair differs from original paired table")
        elif reference:
            raise ValueError("Unavailable pair was assigned a cost difference")
    if sum(p["both_valid"] for p in pairs) != 37:
        raise ValueError("Unexpected pair coverage")
    coverage, contrasts = budget_tables(index)
    phases = phase_rows(index)
    counts = Counter(outcome(r) for r in rows)
    checks = dict(source_run_count=len(rows), primary_run_count=252, long_budget_run_count=72, prototype_run_count=4,
                  controlled_settings_verified=True, controlled_objective_weights_verified=True,
                  scheduled_combinations_verified=True, paired_values_verified=True,
                  valid_cost_pairs=37, scip_cost_pairs=26, greedy_cost_pairs=11,
                  invalid_outputs=counts["INVALID"], incomplete_executions=counts["INCOMPLETE"],
                  controlled_optimal_objective_bounds_verified=True, objective_bound_absolute_tolerance=1e-6,
                  prototype_bound_check="excluded: no bounds in source CSV", phase_totals_reconciled=True,
                  selected_seat_maps_checked=True, solver_executions=0)
    for subdir in ("figures", "tables", "source-data", "source_snapshot"):
        (output / subdir).mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(
        dict(package=PACKAGE, execution_status="rendering", analysis_date=args.analysis_date), indent=2) + "\n")
    for path in source_files:
        target = output / "source-data" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / path, target)
    script = Path(__file__).resolve()
    shutil.copyfile(script, output / "source_snapshot/solver_selection_figures.py")
    write_csv(output / "tables/paired-costs.csv", pairs)
    groups = sorted({(r["batch"], r["configuration"], r["method"], r["budget_seconds"]) for r in rows})
    execution_coverage = []
    for batch, config, method, budget in groups:
        group = [r for r in rows if (r["batch"], r["configuration"], r["method"], r["budget_seconds"])
                 == (batch, config, method, budget)]
        counts = Counter(outcome(r) for r in group)
        execution_coverage.append(dict(batch=batch, configuration=config, method=method, budget_seconds=budget,
                                       scheduled=len(group), completed=sum(r["execution_status"] == "completed" for r in group),
                                       not_started=sum(r["execution_status"] == "not_started" for r in group),
                                       validated=sum(r["valid"] for r in group),
                                       **{s.lower(): counts[s] for s in STATUSES}))
    write_csv(output / "tables/execution-coverage.csv", execution_coverage)
    write_csv(output / "tables/matched-budget-outcomes.csv", coverage)
    write_csv(output / "tables/budget-contrasts.csv", contrasts)
    write_csv(output / "tables/phase-timing-60s.csv", phases)
    heavy = [r for r in controlled if r["event"] == "heavy-mixed" and r["configuration"] == "current"]
    write_csv(output / "tables/230-seat-endpoints.csv", [{k: r[k] for k in
              ("method", "budget_seconds", "solver_status", "valid", "objective", "allocation_total_seconds", "model_build_seconds", "search_seconds")}
              for r in sorted(heavy, key=lambda r: (METHODS.index(r["method"]), r["budget_seconds"]))])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "svg.fonttype": "none", "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False})
    render_primary(output, index, events)
    render_matched(output, index)
    render_pairs(output, pairs, events)
    render_budgets(output, index, contrasts)
    render_phases(output, phases)
    render_map(output, source, index)
    writer = PdfWriter()
    for name, _ in FIGURES:
        reader = PdfReader(output / "figures" / f"{name}.pdf")
        if len(reader.pages) != 1:
            raise ValueError("Expected one vector page per figure")
        writer.add_page(reader.pages[0])
    writer.add_metadata({"/Title": "PJKIT Study A: expanded attempt 3 figures", "/Subject": "Saved-record postprocessing; no solver experiments", "/Author": "PJKIT FYP research"})
    with (output / "attempt3-figure-package.pdf").open("wb") as stream:
        writer.write(stream)
    make_readme(output, source, args.analysis_date, checks)
    if hashes != {str(path): sha256(source / path) for path in source_files}:
        raise ValueError("Original evidence changed during rendering")
    checks["original_source_hashes_unchanged"] = True
    checks["combined_pdf_pages"] = len(PdfReader(output / "attempt3-figure-package.pdf").pages)
    (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    manifest = dict(package=PACKAGE, execution_status="completed", analysis_date=args.analysis_date, source_evidence_directory=str(source),
                    source_sha256=hashes, renderer_sha256=sha256(script), study="A", mode="saved-record postprocessing only",
                    render_environment=dict(python=platform.python_version(),
                                            **{name: version(name) for name in ("matplotlib", "numpy", "pypdf")}),
                    study_b="planned separately; no measured results", solver_executions=0,
                    figures=[dict(id=name, title=title, formats=["pdf", "svg", "png"]) for name, title in FIGURES])
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(output), "figures": len(FIGURES), "pdfs": len(FIGURES) + 1, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
