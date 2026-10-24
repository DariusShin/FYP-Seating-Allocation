"""Render the Study B attempt 3 heavy-mixed seat maps from saved records only.

This module never invokes a solver. It reads the frozen Study B attempt 3 input,
the saved primary-cohort candidates for execution 1 of each backend and the run
records, re-checks each map against the compulsory rules used in the Study A
illustration, and draws CP-SAT and SCIP side by side. Drawing conventions follow
``solver_selection_figures.render_map`` so the two studies' maps read the same.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

PACKAGE = "pjkit-study-b-attempt3-map-figure-v1"
EVENT, CONFIG, BATCH, REPEAT = "heavy-mixed", "current", "primary", 1
BACKENDS = ("cp_sat", "scip")
NAMES = {"cp_sat": "CP-SAT", "scip": "SCIP"}
COMPONENT_NAMES = {"contribution_seat": "contribution", "activeness": "activity", "category_zone": "category"}
TIER_COLORS = {"EMPEROR": "#e9c66d", "MERIT": "#8db8db", "BODHI": "#a5c995"}
FIGURE = "b4-heavy-mixed-60s-maps"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def job_id(backend: str) -> str:
    return f"{BATCH}__{EVENT}__{CONFIG}__{backend}__w8__r{REPEAT}"


def verify(request: dict, candidate: dict, record: dict) -> None:
    """Re-check the saved candidate; any disagreement stops rendering."""
    if not (candidate["valid"] and candidate["validation"]["passed"] and candidate["weighted_proven"]):
        raise ValueError("Selected candidate is not a validated, proven map")
    if record["outcome"] != "optimal_map" or int(float(record["objective"])) != candidate["objective"]:
        raise ValueError("Candidate disagrees with the run record")
    if sum(candidate["weights"][k] * candidate["components"][k] for k in candidate["weights"]) != candidate["objective"]:
        raise ValueError("Penalty does not equal the weighted component sum")
    people = {p["participant_id"]: p for p in request["participants"]}
    seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
    placements = candidate["placements"]
    if Counter(a["participant_id"] for a in placements) != Counter(people.keys()):
        raise ValueError("Map does not cover every registration exactly once")
    used = [s for a in placements for s in a["seat_ids"]]
    if len(used) != 230 or len(set(used)) != 230:
        raise ValueError("Wrong physical seat demand or overlapping seats")
    approved = {tuple(pair) for pair in request["layout"]["approved_pairs"]}
    for a in placements:
        person, bundle = people[a["participant_id"]], [seats[s] for s in a["seat_ids"]]
        if any(s["is_blocked"] for s in bundle):
            raise ValueError("Blocked seat used")
        if len(bundle) != (2 if person["contribution_tier"] == "EMPEROR" else 1):
            raise ValueError("Incorrect seat entitlement")
        if person["requires_accessible_seat"] and not all(s["is_accessible"] for s in bundle):
            raise ValueError("Accessibility requirement not met")
        if len(bundle) == 2 and (bundle[0]["row_number"] != bundle[1]["row_number"] or
                                 tuple(sorted(s["physical_position"] for s in bundle)) not in approved):
            raise ValueError("Invalid Emperor pair")


def draw(ax, request: dict, candidate: dict) -> None:
    people = {p["participant_id"]: p for p in request["participants"]}
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    occupants = {sid: a["participant_id"] for a in candidate["placements"] for sid in a["seat_ids"]}
    ax.set_box_aspect(16 / 17)
    ax.set_xlim(.45, 17.55)
    ax.set_ylim(16.9, .4)
    for seat in lookup.values():
        x = seat["physical_position"] + (seat["physical_position"] > 8)
        y = seat["row_number"]
        pid = occupants.get(seat["seat_id"])
        color = "#7b7f84" if seat["is_blocked"] else TIER_COLORS[people[pid]["contribution_tier"]] if pid else "white"
        ax.add_patch(Rectangle((x - .43, y - .35), .86, .70, facecolor=color, edgecolor="#70757d", linewidth=.45))
        if pid:
            ax.text(x, y, pid[-3:], ha="center", va="center", fontsize=5.2, color="#252b33")
    for a in candidate["placements"]:
        if len(a["seat_ids"]) == 2:
            seat = min((lookup[s] for s in a["seat_ids"]), key=lambda s: s["physical_position"])
            x = seat["physical_position"] + (seat["physical_position"] > 8)
            ax.add_patch(Rectangle((x - .47, seat["row_number"] - .39), 1.94, .78, fill=False, edgecolor="#222", linewidth=.65))
    ax.set_xticks([x + (x > 8) for x in range(1, 17)], range(1, 17))
    ax.set_yticks(range(1, 17))
    ax.tick_params(length=0, labelsize=7)
    ax.set_xlabel("Physical seat position; central aisle", fontsize=9)
    ax.set_ylabel("Row (front at top)", fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Completed Study B attempt 3 folder (read only)")
    parser.add_argument("--out", type=Path, required=True, help="Fresh output folder for the derived figure")
    args = parser.parse_args(argv)
    source, out = args.source, args.out
    (out / "figures").mkdir(parents=True, exist_ok=False)

    input_path = source / "inputs" / f"{EVENT}.json"
    records_path = source / "tables" / "run-records.csv"
    request = json.loads(input_path.read_text(encoding="utf-8"))
    people = {p["participant_id"]: p for p in request["participants"]}
    if Counter(p["contribution_tier"] for p in people.values()) != Counter(EMPEROR=99, MERIT=19, BODHI=13):
        raise ValueError("Incorrect heavy-event composition")
    with records_path.open(newline="", encoding="utf-8") as handle:
        records = {r["id"]: r for r in csv.DictReader(handle)}

    candidates, sources = {}, {}
    for backend in BACKENDS:
        path = source / "main" / "candidates" / f"{job_id(backend)}.json"
        candidates[backend] = json.loads(path.read_text(encoding="utf-8"))
        verify(request, candidates[backend], records[job_id(backend)])
        sources[backend] = path
    bundles = {b: {a["participant_id"]: tuple(sorted(a["seat_ids"])) for a in c["placements"]} for b, c in candidates.items()}
    moved = sorted(pid for pid in people if bundles["cp_sat"][pid] != bundles["scip"][pid])

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 8.3))
    fig.subplots_adjust(left=.05, right=.985, top=.80, bottom=.19, wspace=.12)
    summary = {}
    for ax, backend in zip(axes, BACKENDS):
        cand, rec = candidates[backend], records[job_id(backend)]
        draw(ax, request, cand)
        comps = ", ".join(f"{COMPONENT_NAMES[k]} {cand['components'][k]:,}" for k in COMPONENT_NAMES)
        seconds = float(rec["complete_service_return_seconds"])
        ax.set_title(f"{NAMES[backend]} (eight workers): OPTIMAL\nPenalty {cand['objective']:,} ({comps})\n"
                     f"Complete service return: {seconds:.2f} s", fontsize=10.5, pad=14)
        summary[backend] = dict(job=job_id(backend), objective=cand["objective"], components=cand["components"],
                                complete_service_return_seconds=seconds,
                                physical_map_sha256=cand["physical_map_sha256"])
    fig.suptitle("Study B attempt 3 | The 230-seat event at the 60-second function allowance", fontsize=15, y=.975)
    fig.text(.5, .905, "99 Emperor registrations (198 seats), 19 Merit and 13 Bodhi; 131 registration units; current preference order; "
             "execution 1 of each backend", ha="center", fontsize=10)
    fig.legend(handles=[Patch(facecolor=c, edgecolor="#777", label=t.title()) for t, c in TIER_COLORS.items()] +
               [Patch(facecolor="#7b7f84", label="Blocked"), Patch(facecolor="white", edgecolor="#777", label="Unused usable seat"),
                Patch(facecolor="none", edgecolor="#222", label="Emperor pair outline")],
               loc="lower center", bbox_to_anchor=(.5, .085), ncol=6, frameon=False, fontsize=8.8)
    fig.text(.5, .012, textwrap.fill(
        f"Both maps are independently validated and proven optimal with the same production-scale penalty, but they are different "
        f"physical maps: {len(moved)} of {len(people)} registration units hold different seats, and the three preference penalties "
        "balance differently. Registration numbers identify placements, not preference quality.", 150),
        ha="center", va="bottom", fontsize=8.2, color="#434a54")
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / "figures" / f"{FIGURE}.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    manifest = dict(package=PACKAGE, solver_executions=0, event=EVENT, configuration=CONFIG, batch=BATCH, execution=REPEAT,
                    registration_units=len(people), units_with_different_seats=len(moved), backends=summary,
                    sources={"input": dict(path=input_path.as_posix(), sha256=sha256(input_path)),
                             "run_records": dict(path=records_path.as_posix(), sha256=sha256(records_path)),
                             **{b: dict(path=p.as_posix(), sha256=sha256(p)) for b, p in sources.items()}},
                    figures={ext: sha256(out / "figures" / f"{FIGURE}.{ext}") for ext in ("pdf", "svg", "png")})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(out=str(out), units_with_different_seats=len(moved),
                          objectives={b: s["objective"] for b, s in summary.items()}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
