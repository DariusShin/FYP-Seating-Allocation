"""Summarize saved runs; optionally plot a fixed illustrative instance with matplotlib."""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    root = args.directory
    summary = json.loads((root / "summary.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    rows = [r for p in sorted((root / "runs").glob("*.json"))
            for r in json.loads(p.read_text())["runs"]]
    assert len(rows) == summary["total_runs"]
    by_instance = {}
    for r in rows:
        by_instance.setdefault(r["instance"], []).append(r)
    text = ["# Synthetic preference sensitivity: measured results", "",
            "Generated from saved run records. These are diagnostic results, not stakeholder validation.", "",
            f"Instances: {len(by_instance)}. Runs: {len(rows)}. Status counts: {summary['statuses']}.",
            f"Returned solutions passing placement validation: {summary['valid_returned_solutions']}.",
            f"Independently checked option-cost vectors: {summary['checked_option_vectors']:,}.",
            f"Total experiment elapsed time: {summary['elapsed_seconds']:.2f} seconds, including generation, checks and file output.",
            f"OR-Tools {manifest['ortools']}; {manifest['machine']}; one worker; {manifest['time_limit_seconds_per_solve']} seconds per search; fixed seeds.",
            "Full Python/platform and source hashes are recorded in manifest.json.", "",
            "## Search outcomes", "",
            "| Instance size | Runs | Optimal | Feasible, unproved | Unknown | Infeasible | Median search seconds |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for size in manifest["sizes"]:
        subset = [r for r in rows if r["instance"].startswith(size + "-")]
        counts = Counter(r["status"] for r in subset)
        text.append(f"| {size} | {len(subset)} | {counts['OPTIMAL']} | {counts['FEASIBLE']} | {counts['UNKNOWN']} | {counts['INFEASIBLE']} | {statistics.median(r['solve_seconds'] for r in subset):.3f} |")
    text += ["", "UNKNOWN means no incumbent was returned within the budget; it is not proof of infeasibility. "
             "The configurations on an instance share hard constraints, so another configuration's validated plan can demonstrate feasibility. "
             "Search timing excludes shared model construction and external validation. These are not repeated runtime trials.", "",
             "## Sensitivity with a proved baseline", "",
             "A strict comparison below requires the current-weight/base-matrix baseline to be OPTIMAL. "
             "An alternative feasible plan with a strictly better alternative-objective score proves that this baseline is no longer optimal under that objective. "
             "This avoids mistaking poor baseline search quality for a weight effect. The alternative need not itself be proved optimal for that strict conclusion.", "",
             "| Alternative matrix / weights | Eligible paired cases | Baseline strictly worse | Baseline also proved optimal | Unresolved |",
             "|---|---:|---:|---:|---:|"]
    profile_names = list(dict.fromkeys((r["matrix"], r["weight"]) for r in rows))
    proof_counts = {}
    for matrix, weight in profile_names:
        if (matrix, weight) == ("base", "current"):
            continue
        counts = Counter()
        for subset in by_instance.values():
            base = next(r for r in subset if (r["matrix"], r["weight"]) == ("base", "current"))
            alternative = next(r for r in subset if (r["matrix"], r["weight"]) == (matrix, weight))
            if base["status"] != "OPTIMAL" or "objective" not in alternative:
                continue
            counts["paired"] += 1
            scored = sum(w * c for w, c in zip(alternative["weights"], base["components_by_matrix"][matrix]))
            if scored > alternative["objective"]:
                counts["strict"] += 1
            elif scored == alternative["objective"] and alternative["status"] == "OPTIMAL":
                counts["also"] += 1
            else:
                counts["unresolved"] += 1
        proof_counts[matrix + "/" + weight] = dict(counts)
        text.append(f"| {matrix} / {weight} | {counts['paired']} | {counts['strict']} | {counts['also']} | {counts['unresolved']} |")
    name = "small-mixed-20261011"
    sample = [r for r in by_instance.get(name, []) if r["matrix"] == "base" and r["weight"] in ("current", "equal", "rank_sum", "rank_reciprocal", "roc", "flatter", "steeper")]
    text += ["", "## Worked example", "", f"Instance `{name}`: 24 registrations, 32 physical seats. "
             "The table uses the same original component scales for every plan. Lower is better in each column. "
             "These are aggregate normalized penalty points, not percentages of satisfaction.", "",
             "| Weights | Proof status | Contribution cost | Activity cost | Category cost |",
             "|---|---|---:|---:|---:|"]
    for r in sample:
        c = r["components_by_matrix"]["base"]
        text.append(f"| {r['weight']} | {r['status']} | {c[0]} | {c[1]} | {c[2]} |")
    text += ["", "A solution optimal for one weighting need not be optimal for another. "
             "The current and ROC rows illustrate an explicit trade-off without comparing incompatible weighted totals.", "",
             "## Limits of these results", "",
             "- No stakeholder choices, real registration distributions, or satisfaction labels were used. No best PJKIT weights are inferred.",
             "- Validity applies to returned plans; missing incumbents are counted separately. Tests omit requested accessibility and absence repair.",
             "- Two data seeds and one search seed provide preliminary coverage, not statistical generalization.",
             "- Matrix experiments alter both within-category gaps and relative penalty strength across categories.",
             "- Tied optima can give different seat maps. The sensitivity table compares objective values with proof conditions, not seat-map identity.",
             "- Default scoring weights are reduced from 40/30/20 to the equivalent 4/3/2. All-entry category doubling passed exact normalization checks.",
             "- The study did not evaluate competing allocation algorithms, time to first solution, memory use, or operational review time.", ""]
    if args.plot and sample:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5.4))
        # Duplicate objective vectors are combined so labels do not imply unique seat maps.
        vectors = {}
        for r in sample:
            vectors.setdefault(tuple(r["components_by_matrix"]["base"]), []).append(r["weight"])
        xs, ys, cs = zip(*vectors)
        dots = ax.scatter(xs, ys, c=cs, cmap="viridis_r", s=140, edgecolor="black", linewidth=0.6)
        offsets = {(407, 617, 492): (9, 7), (407, 596, 530): (9, 7),
                   (388, 635, 530): (9, 7), (429, 617, 454): (-80, 12), (435, 610, 454): (-52, -20)}
        for vector, labels in vectors.items():
            ax.annotate(" / ".join(labels), vector[:2], xytext=offsets.get(vector, (8, 8)),
                        textcoords="offset points", fontsize=9)
        ax.set_xlabel("Contribution penalty (lower is better)")
        ax.set_ylabel("Activity penalty (lower is better)")
        ax.set_title("Weight choices trade off seating preferences\n24 synthetic registrations · identical hard constraints", pad=14)
        fig.colorbar(dots, ax=ax, label="Category penalty (lower is better)")
        ax.margins(x=0.22, y=0.3)
        ax.grid(alpha=0.2)
        ax.set_axisbelow(True)
        fig.tight_layout()
        fig.savefig(root / "tradeoffs.png", dpi=180)
        fig.savefig(root / "tradeoffs.svg")
        plt.close(fig)
        text += ["![Common-scale component trade-offs](tradeoffs.png)", ""]
    (root / "results.md").write_text("\n".join(text))
    (root / "proof_comparisons.json").write_text(json.dumps(proof_counts, indent=2) + "\n")
    print("Wrote", root / "results.md")


if __name__ == "__main__":
    main()
