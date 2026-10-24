"""Render worker/thread sweep figures and tables from saved records only.

Never invokes a solver. Reads the completed sweep's run records and writes, to a
fresh folder: (1) per-run time, CPU and peak-memory response to worker count for
both solvers, keeping late (non-adopted) runs visible; (2) a paired comparison of
each solver at its best observed setting (CP-SAT 8 workers, SCIP 1 thread); and
CSV tables behind both. Colours and markers match the other study figures.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics as st
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PACKAGE = "pjkit-study-b-worker-sweep-figures-v1"
NAMES = {"cp_sat": "CP-SAT", "scip": "SCIP"}
COLORS = {"cp_sat": "#2463a6", "scip": "#bd591b"}
MARKERS = {"cp_sat": "o", "scip": "s"}
LEVELS = (1, 2, 4, 8)
EVENTS = ("typical-mixed", "heavy-mixed", "full-accessible", "full-tied")
EVENT_LABELS = {"typical-mixed": "typical-mixed / current", "heavy-mixed": "heavy-mixed / current",
                "full-accessible": "full-accessible / two", "full-tied": "full-tied / disabled"}
INK, MUTED, GRID = "#252b33", "#5b636e", "#e3e5e8"
BEST = {"cp_sat": 8, "scip": 1}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for r in rows:
        r["workers"] = int(r["workers"])
        r["repetition"] = int(r["repetition"])
        r["adopted"] = r["valid_map"] == "True"
        r["time"] = float(r["complete_service_return_seconds"])
        r["cpu"] = float(r["service_process_cpu_seconds"])
        r["mem"] = float(r["memory_bytes"]) / 2 ** 20
    if len(rows) != 96 or any(r["execution_status"] != "completed" for r in rows):
        raise ValueError("Expected 96 completed sweep records")
    return rows


def style(ax, ylabel, title):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=8)
    ax.set_ylabel(ylabel, fontsize=9.5, color=MUTED)
    ax.grid(axis="y", color=GRID, linewidth=.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#9aa0a8")
    ax.tick_params(colors=MUTED, labelsize=9)


def render_response(rows, out: Path):
    metrics = (("time", "Seconds", "(a) Complete service return"),
               ("cpu", "CPU seconds", "(b) Service process CPU time"),
               ("mem", "MiB", "(c) Peak working set (memory)"))
    offset = {"cp_sat": -.17, "scip": .17}
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.4))
    fig.subplots_adjust(left=.055, right=.99, top=.80, bottom=.25, wspace=.26)
    for ax, (key, ylabel, title) in zip(axes, metrics):
        style(ax, ylabel, title)
        for backend in NAMES:
            means = []
            for i, w in enumerate(LEVELS):
                group = [r for r in rows if r["backend"] == backend and r["workers"] == w]
                means.append(st.mean(r[key] for r in group))
                for j, r in enumerate(sorted(group, key=lambda r: (r["event"], r["repetition"]))):
                    x = i + offset[backend] + (j - 5.5) * .012
                    ax.scatter(x, r[key], s=30, marker=MARKERS[backend], linewidths=1.1, zorder=3,
                               facecolor=COLORS[backend] if r["adopted"] else "white",
                               edgecolor=COLORS[backend], alpha=.9)
            ax.plot([i + offset[backend] for i in range(4)], means, color=COLORS[backend], linewidth=2, zorder=2)
            ax.text(3 + offset[backend] + .12, means[-1], f"{NAMES[backend]}", fontsize=8.5, color=INK, va="center")
        if key == "time":
            ax.axhline(60, color="#7b7f84", linestyle="--", linewidth=1.1, zorder=1)
            ax.text(2.45, 56.5, "60 s function\nallowance", fontsize=8, color=MUTED, ha="center", va="top")
        ax.set_xticks(range(4), [str(w) for w in LEVELS])
        ax.set_xlim(-.55, 3.75)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Workers (CP-SAT) / native threads (SCIP)", fontsize=9.5, color=MUTED)
    fig.suptitle("Worker/thread sweep | how each solver responds to added workers", fontsize=14, color=INK, y=.975)
    fig.text(.5, .895, "4 event–setting pairs × 3 executions = 12 runs per solver and level; 60-second allowance; lines join level means",
             ha="center", fontsize=10, color=MUTED)
    handles = [Line2D([], [], marker=MARKERS[b], color=COLORS[b], markerfacecolor=COLORS[b], linewidth=2, markersize=7,
                      label=f"{NAMES[b]}: adopted validated map") for b in NAMES]
    handles += [Line2D([], [], marker=MARKERS[b], color=COLORS[b], markerfacecolor="white", linewidth=0, markersize=7,
                       label=f"{NAMES[b]}: complete but late, not adopted") for b in NAMES
                if any(r["backend"] == b and not r["adopted"] for r in rows)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .085), ncol=len(handles), frameon=False, fontsize=9)
    fig.text(.5, .012, textwrap.fill(
        "Hollow markers are complete candidates returned 25–126 ms after the 60-second boundary without a proof; their times and resource use "
        "are retained. CP-SAT with 1–4 workers searched the full allowance; with 8 workers it proved every optimum quickly. SCIP proved every "
        "optimum at every level but became slower and used more CPU and memory as threads were added. CPU time and peak working set are "
        "whole-process measurements from fresh workers, including native solver threads.", 175),
        ha="center", va="bottom", fontsize=8.2, color=MUTED)
    export(fig, out, "b5-sweep-time-cpu-memory")


def best_pairs(rows):
    index = {(r["backend"], r["workers"], r["event"], r["repetition"]): r for r in rows}
    pairs = []
    for event in EVENTS:
        for rep in (1, 2, 3):
            a, b = index["cp_sat", 8, event, rep], index["scip", 1, event, rep]
            if not (a["adopted"] and b["adopted"] and a["objective"] == b["objective"]):
                raise ValueError("Best-setting pair is not matched, adopted and equal-penalty")
            pairs.append((event, rep, a, b))
    return pairs


def render_best(pairs, out: Path):
    metrics = (("time", "Seconds", "(a) Complete service return"),
               ("cpu", "CPU seconds", "(b) Service process CPU time"),
               ("mem", "MiB", "(c) Peak working set (memory)"))
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.9), sharey=True)
    fig.subplots_adjust(left=.13, right=.99, top=.78, bottom=.27, wspace=.10)
    for ax, (key, xlabel, title) in zip(axes, metrics):
        style(ax, "", title)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID, linewidth=.8)
        for y, event in enumerate(EVENTS):
            group = [p for p in pairs if p[0] == event]
            for k, (_, rep, a, b) in enumerate(group):
                dy = (k - 1) * .14
                ax.plot([a[key], b[key]], [y + dy, y + dy], color="#c9cdd2", linewidth=1, zorder=1)
                for r, backend in ((a, "cp_sat"), (b, "scip")):
                    ax.scatter(r[key], y + dy, s=42, marker=MARKERS[backend], facecolor=COLORS[backend],
                               edgecolor="white", linewidth=1.2, zorder=3)
        ax.set_yticks(range(len(EVENTS)), [EVENT_LABELS[e] for e in EVENTS])
        ax.set_ylim(len(EVENTS) - .5, -.5)
        ax.set_xlim(left=0)
        ax.set_xlabel(xlabel, fontsize=9.5, color=MUTED)
    fig.suptitle("Each solver at its best observed setting | CP-SAT 8 workers vs SCIP 1 thread", fontsize=14, color=INK, y=.975)
    fig.text(.56, .875, "12 matched runs (4 event–setting pairs × 3 executions); every pair adopted and proved the same optimal penalty",
             ha="center", fontsize=10, color=MUTED)
    handles = [Line2D([], [], marker=MARKERS[b], color="none", markerfacecolor=COLORS[b], markeredgecolor="white", markersize=8,
                      label=f"{NAMES[b]} ({BEST[b]} {'workers' if b == 'cp_sat' else 'thread'})") for b in NAMES]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.56, .09), ncol=2, frameon=False, fontsize=9.5)
    fig.text(.56, .012, textwrap.fill(
        "Exploratory comparison, not part of the pre-registered decision rules. Grey segments join the two solvers' runs for the same "
        "event and execution. CPU time and peak working set are whole-process measurements, including the Python service and native "
        "solver threads.", 165), ha="center", va="bottom", fontsize=8.2, color=MUTED)
    export(fig, out, "b6-best-setting-comparison")


def export(fig, out: Path, name: str):
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / "figures" / f"{name}.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def summarize(values):
    return dict(mean=round(st.mean(values), 3), median=round(st.median(values), 3),
                min=round(min(values), 3), max=round(max(values), 3))


def write_tables(rows, pairs, out: Path):
    level_rows = []
    for w in LEVELS:
        for backend in NAMES:
            g = [r for r in rows if r["backend"] == backend and r["workers"] == w]
            level_rows.append(dict(workers=w, backend=backend, runs=len(g), adopted=sum(r["adopted"] for r in g),
                                   time_mean=round(st.mean(r["time"] for r in g), 3),
                                   cpu_mean=round(st.mean(r["cpu"] for r in g), 3),
                                   memory_mib_mean=round(st.mean(r["mem"] for r in g), 1)))
    with (out / "tables/level-summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(level_rows[0]))
        writer.writeheader()
        writer.writerows(level_rows)
    with (out / "tables/best-setting-pairs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["event", "repetition", "objective", "cp_sat_w8_time", "scip_w1_time", "cp_sat_w8_cpu", "scip_w1_cpu",
                         "cp_sat_w8_memory_mib", "scip_w1_memory_mib"])
        for event, rep, a, b in pairs:
            writer.writerow([event, rep, a["objective"], round(a["time"], 3), round(b["time"], 3), round(a["cpu"], 3),
                             round(b["cpu"], 3), round(a["mem"], 1), round(b["mem"], 1)])
    best = {}
    for key in ("time", "cpu", "mem"):
        diffs = [b[key] - a[key] for _, _, a, b in pairs]
        best[key] = dict(cp_sat_w8=summarize([a[key] for *_, a, _ in pairs]),
                         scip_w1=summarize([b[key] for *_, b in pairs]),
                         cp_sat_lower_in=sum(d > 0 for d in diffs), pairs=len(diffs),
                         median_scip_minus_cp_sat=round(st.median(diffs), 3))
    best["cpu_per_wall_second"] = dict(
        cp_sat_w8=round(st.mean(a["cpu"] for *_, a, _ in pairs) / st.mean(a["time"] for *_, a, _ in pairs), 2),
        scip_w1=round(st.mean(b["cpu"] for *_, b in pairs) / st.mean(b["time"] for *_, b in pairs), 2))
    return level_rows, best


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Completed sweep folder (read only)")
    parser.add_argument("--out", type=Path, required=True, help="Fresh output folder")
    args = parser.parse_args(argv)
    (args.out / "figures").mkdir(parents=True, exist_ok=False)
    (args.out / "tables").mkdir()
    records = args.source / "tables" / "run-records.csv"
    rows = load(records)
    pairs = best_pairs(rows)
    render_response(rows, args.out)
    render_best(pairs, args.out)
    level_rows, best = write_tables(rows, pairs, args.out)
    manifest = dict(package=PACKAGE, solver_executions=0, source=dict(path=records.as_posix(), sha256=sha256(records)),
                    best_setting_comparison=best, pre_registered=False,
                    files={p.relative_to(args.out).as_posix(): sha256(p) for p in sorted(args.out.rglob("*")) if p.is_file()})
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(best, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
