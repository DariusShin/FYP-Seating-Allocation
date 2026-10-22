# Research experiments and reporting

This directory contains a research harness, not a production policy change. All participant records are synthetic. See `../../docs/methodologies/preference-parameter-study-2026-10-11.md` for rationale, sources and limitations.

## Study B: Windows production solver comparison

The isolated [Study B package and Windows commands](production_benchmark/README.md) implement the [production comparison protocol](../../docs/planning/solver-selection-production-follow-up.md). Use `setup_production_benchmark.py`, `.venv-study-b` and `production_solver_benchmark.py`; these are separate from the older controlled benchmark commands below. Study B covers the fixed 64-job CP-SAT/SCIP production schedule, native concurrency/correctness gates, canonical adoption, regeneration compatibility, two-hour cap and B1–B5 reporting. Native Windows validation and measured execution are pending; development checks are not dissertation observations. The app's production default and Study A evidence are unchanged.

## Planned execution sequence

See the [execution guide](../../docs/planning/experiment-execution-sequence.md), [hypotheses](../../docs/planning/experiment-hypotheses-and-analysis.md) and [confirmed 20 October scope amendment](../../docs/planning/solver-benchmark-scope-amendment-2026-10-20.md). The approved solver target is 21 events, 252 primary five-second runs, 72 fresh 30/60-second runs and four prototype checks, with a 28-job pilot inside **120 minutes**. **Executable amendment pending:** current scripts still implement 13 events, 156 primary runs, a 19-job pilot and **90 minutes**. Main execution has not occurred. Implement and validate the amendment before collecting its evidence. Weighting remains a separate, not-yet-implemented 12-event / 840-search study within **120 minutes**. Sequence: correctness/input certification, separate pilots, solver comparison, budget/prototype checks, then weighting and JSON-derived reporting. Human verification is future work. Use the local M4/24 GB Mac and sequential, separately recorded studies.

## Solver-selection benchmark: CP-SAT, SCIP and greedy

Start with the [setup, commands and output guide](solver_benchmark/README.md). The commands below describe the current 18 October implementation, not the approved 21-event amendment. From the repository root, using Python 3.12 or newer:

```sh
python3 research/experiments/setup_benchmark.py
.venv/bin/python -m pytest research/experiments/tests/test_solver_benchmark.py -q
.venv/bin/python research/experiments/solver_selection_benchmark.py pilot --out docs/results/my-new-solver-pilot
```

Inspect `docs/results/my-new-solver-pilot/pilot/results.md` and `pilot/projection.json`. Development evidence stays separate from dissertation results. The following main-command syntax will still execute the older scope until its implementation is amended; use a new directory when collecting an explicitly identified protocol:

```sh
.venv/bin/python research/experiments/solver_selection_benchmark.py run --out docs/results/my-new-solver-study
```

The current main command repeats correctness, input-certification and pilot gates and stops if its existing workload projects beyond 90 minutes. The approved 120-minute amendment still needs implementation. Outputs include `results.md`, `summary.json`, raw `runs/` JSON, `tables/` CSVs and `figures/` PNG/PDF/SVG exports. The detailed guide explains regeneration. The [setup validation record](../../docs/results/solver-benchmark-setup-2026-10-18.md) preserves the older implementation tests and pilots; the full main study has not run.

### Source-informed candidate inputs, 20 October 2026

The [new PJKIT sample-data bundle](../fixtures/pjkit-sample-2026-10-20/README.md) reconciles 599 masked registrations from the supplied 2021–2026 workbook and summary CSV. It contains six yearly cohorts, one prototype demo and 13 independently generated controlled cases with source-informed activity frequencies. Per the user's explicit instruction, those candidate requests encode full-history registration totals in the existing `events_joined_last_2_years` field; the override, actual lookback counts and one synthetic amount correction are documented separately. Industry-supervisor review remains pending.

The user explicitly declined adoption of the 13 source-informed controlled candidates in the confirmed 20 October amendment. They remain available alongside historical/yearly/demo data, outside the benchmark and unchanged weighting protocol. The new 179/212-seat families will use the original controlled generator and activity semantics. Prototype timing checks will use the declared benchmark events, not this separate demo. Data preparation did not run a solver experiment or change the current executable inputs.

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

## Saved-record solver-selection figures

`solver_selection_figures.py` only reads saved attempt 3 evidence and exports figures/tables. It imports no solver library and never runs an allocation service or experiment. The [expanded Study A package](../../docs/results/solver-selection-v4-attempt3-figures-2026-10-23/README.md) includes the necessary source subset, an identical renderer snapshot, hash provenance, checks and six PDF/SVG/PNG figures plus a combined PDF.

From the repository root, using Python with matplotlib, numpy and pypdf installed:

```sh
python research/experiments/solver_selection_figures.py --source docs/results/solver-selection-v4-attempt3-figures-2026-10-23/source-data --output /tmp/pjkit-study-a-reproduced --analysis-date 2026-10-23
```

The source and output directories must be separate and non-nested. Existing output is refused unless `--overwrite` explicitly selects a package previously generated by this renderer. The original evidence bundle is never edited. Study B is a [separate confirmed production comparison plan](../../docs/planning/solver-selection-production-follow-up.md); this reporting command does not implement or execute it.
