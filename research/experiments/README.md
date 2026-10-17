# Preference sensitivity experiments

This directory contains a research harness, not a production policy change. All participant records are synthetic. See `../../docs/methodologies/preference-parameter-study-2026-10-11.md` for rationale, sources and limitations.

## Planned rank-weighting experiment

The [amended implementation protocol](../../docs/planning/rank-weighting-experiment.md) specifies a separate, not-yet-implemented runner: current-ratio, rank sum, rank reciprocal and ROC, excluding equal weighting. It covers 12 initial-allocation datasets and all 16 ordered enabled configurations (46 distinct objectives per dataset), plus limited sensitivity and seed-repeat batches. The 840 planned experimental searches allocate 56 minutes at four seconds each, within a **120-minute overall runner deadline** including preparation, pilot, validation and reporting. Extended-proof and canonicalization searches are excluded from this capped run.

Follow that protocol for implementation, deadline handling and limitations. The commands below run the earlier preference-sensitivity harness; they do not execute the amended protocol or enforce its overall deadline. Preserve the original 11 October results and source snapshot. New evidence belongs under `docs/results/rank-weighting-initial-<run-date>/`.

## Existing preference-sensitivity harness

Run from the repository root using its existing virtual environment:

```sh
.venv/bin/python research/experiments/preference_sensitivity.py --out docs/results/my-new-run
.venv/bin/python research/experiments/summarize_preference_sensitivity.py docs/results/my-new-run
```

The generator refuses to overwrite an existing results directory. Each configuration receives 1.5 seconds of search by default; use `--seconds` to change that budget. A small exploratory run can use:

```sh
.venv/bin/python research/experiments/preference_sensitivity.py --out docs/results/my-small-run --sizes small --patterns mixed --seeds 20261011
```

The saved 11 October study uses all three sizes, all three patterns and both default data seeds. It contains 18 input instances and 306 solves. It was recorded from the pre-relocation `experiments/` location; its bundle now lives under `docs/results/preference-sensitivity-2026-10-11/` with a relocation note and a source snapshot, and `manifest.json` still records the original paths and hashes. Each input and returned placement is saved. `manifest.json` records environment details, configuration and source hashes; `summary.json` records checks and aggregate outcomes; `runs/` retains objectives, lower bounds, times, validation, and placements. `results.md` is generated from these records.

The experiment independently checks the scorer's integer normalization with Decimal arithmetic and checks uniform matrix scaling for every option. Returned solutions are validated independently of the CP-SAT model using the project's placement validator. The study keeps proof status separate from feasibility and compares preference components on a shared scale. It does not infer stakeholder preferences from synthetic scores.

The summary's strongest sensitivity comparisons require an OPTIMAL baseline to separate parameter effects from incomplete baseline optimization. The broader `summary.json` comparisons also include unproved baselines; inspect status before interpreting them. Seat-map changes alone are not used to establish sensitivity because optima can be non-unique.

Optional: the summarizer's `--plot` argument requires matplotlib in the selected Python environment. It plots the fixed small mixed instance when available. The recorded study's tables do not require plotting dependencies.

Search-budget reproducibility is conditional on machine and software versions. A fixed seed does not guarantee identical timed-out results. No timing comparison between CP-SAT and another solver is performed here. Accessibility requests and absence-repair experiments are outside this harness's current scope.
