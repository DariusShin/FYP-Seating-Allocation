# Solver-selection benchmark

This research harness compares the maintained OR-Tools CP-SAT initial-allocation model (based on lazy clause generation), an equivalent mixed-integer linear formulation solved with SCIP, and the specified deterministic constraint-aware greedy method. It uses synthetic requests and isolated prototype stores. It does not change production policy or publish allocations.

The controlling documents are the [solver protocol](../../../docs/planning/solver-selection-benchmark.md), [hypotheses](../../../docs/planning/experiment-hypotheses-and-analysis.md), [execution guide](../../../docs/planning/experiment-execution-sequence.md), and [reporting plan](../../../docs/planning/benchmark-results-visualization.md). The rank-weighting runner is a separate, not-yet-implemented experiment.

Implementation and development checks are documented in the [setup validation record](../../../docs/results/solver-benchmark-setup-2026-10-18.md). A development pilot does not establish the dissertation hypotheses. The main study must be explicitly launched using `run`.

## Environment

From the repository root, use Python 3.12 or newer (the tested lock requires it):

```sh
python3 research/experiments/setup_benchmark.py
.venv/bin/python research/experiments/solver_selection_benchmark.py --help
```

Setup creates a repository-local `.venv` and installs the tested dependency lock, including OR-Tools 9.15.6755 and Matplotlib. `requirements-benchmark.txt` describes the direct dependency ranges; `requirements-benchmark-lock.txt` records the tested resolved environment. Each evidence bundle also records its own actual environment and `pip freeze`. SCIP backend availability is checked explicitly; there is no fallback to CBC or another solver. The CLI forces imports/resources to this checkout rather than an editable installation from another worktree.

Use the local M4/24 GB Mac, plugged in and awake, with stable power settings and no competing heavy workloads. The controlled methods run sequentially with one worker. The four prototype checks preserve the source fixture's actual settings, currently eight workers and canonicalization enabled. Local and Colab timings must not be pooled.

## Commands

Every command except `report` requires a **new** output directory and refuses to overwrite an existing one. Dates in the examples are labels; choose a new suffix for another invocation.

```sh
# Certify inputs and write the 232-job manifest; no algorithm comparison runs.
.venv/bin/python research/experiments/solver_selection_benchmark.py plan --out docs/results/solver-benchmark-plan-2026-10-18

# Exhaustive tiny-oracle, scoring and infeasibility gates only.
.venv/bin/python research/experiments/solver_selection_benchmark.py check --out docs/results/solver-benchmark-check-2026-10-18

# Separate-seed development pilot; this is not main dissertation evidence.
.venv/bin/python research/experiments/solver_selection_benchmark.py pilot --out docs/results/solver-benchmark-pilot-2026-10-18

# Rebuild a pilot's diagnostic table from its saved JSON, without solving.
.venv/bin/python research/experiments/solver_selection_benchmark.py report --out docs/results/solver-benchmark-pilot-2026-10-18

# Full declared study, including fresh preflight/pilot inside the 90-minute ceiling.
.venv/bin/python research/experiments/solver_selection_benchmark.py run --out docs/results/solver-selection-benchmark-2026-10-18

# Regenerate tables/figures from an existing main-study bundle; no solving.
.venv/bin/python research/experiments/solver_selection_benchmark.py report --out docs/results/solver-selection-benchmark-2026-10-18 --plots

# Implementation tests, separate from research observations.
.venv/bin/python -m pytest research/experiments/tests/test_solver_benchmark.py -q
```

`run` is the deliberate full-experiment command. It rechecks correctness and input witnesses, performs its own pilot, and evaluates the completion projection before starting main runs. A previous development pilot does not bypass these checks or move their cost outside the main runner's clock. No resume mode combines interrupted runs into an apparently complete original experiment.

For the first use, install the environment and run the implementation tests. `plan`, `check` and `pilot` are optional development commands for inspecting each stage separately. When ready to collect dissertation evidence, use one new `run` directory; that command repeats all required gates within its own clock. Do not edit solver code, configuration, input files or planning files while it runs. Exit status 0 means the command completed its requested mode; a stopped run returns a nonzero status with a reason in `manifest.json`. A completed pilot can still project more than 90 minutes: inspect `pilot/projection.json` before interpreting its completion as readiness.

## Where to find the results

The value passed to `--out` is the evidence directory. For a completed or partially completed **main** run, open its `results.md` first, then use these files:

| Location below `--out` | Contents and use |
|---|---|
| `manifest.json` | Protocol, exact environment/source hashes, seeds, full ordered 232-job schedule and completion/stop status |
| `inputs/*.json`, `witnesses/*.json`, `inventory.json` | Frozen synthetic events, independently audited feasibility witnesses and input certification; these are inputs, not solver outcomes |
| `runs/*.json` | Raw per-run data, complete seat maps, independent validation, costs/components, coefficients, available bounds/gaps, phase timings and memory scope |
| `correctness.json` | Exhaustive tiny-case and deliberately infeasible checks, excluded from benchmark denominators |
| `summary.json` | Machine-readable coverage, paired cost comparisons and budget contrasts used by the main report |
| `tables/run-records.csv` | Every planned run, its outcome, objective/components, timings and peak-memory measurements; nested component/weight fields are JSON cells |
| `tables/coverage.csv` | Planned, attempted and validated counts by batch, configuration, method and budget |
| `tables/paired-costs.csv` | Five-second CP-SAT cost differences against greedy/SCIP, with missing-pair reasons |
| `tables/budget-contrasts.csv` | Matched 5→30 and 30→60 outcomes and common-cost differences |
| `tables/budget-subset-coverage.csv` | Coverage on the same four-event subset at each budget; includes reused five-second records |
| `figures/figure-1-outcomes.*` | Five-second outcome heatmaps by event, method and configuration |
| `figures/figure-2-paired-costs.*` | Paired cost differences by configuration, conditional on both plans being valid |
| `figures/figure-3-budget-response.*` | Valid-map counts, paired cost changes and observed allocation times across budgets |
| `figures/illustration-230-seat.*` | The current-configuration, five-second seating maps for the 230-seat case, with explicit no-map panels when necessary |
| `prototype_outputs/`, `local_stores/` | Raw prototype service output and isolated synthetic SQLite stores |
| `source_snapshot/`, `requirements-lock.txt` | Measured source/configuration/planning snapshot and actual installed dependency versions |

Each figure is exported as **PNG at 300 dpi**, **PDF** and **SVG**. Use PNG for quick viewing and PDF/SVG for dissertation layout. A main `run` generates tables and figures automatically within its reporting allowance. The `report --plots` command regenerates them from saved records without rerunning solvers. A stopped run may have partial tables/figures; always check its manifest and coverage before discussion. If the reporting stage itself was interrupted, regenerate it using `report`.

The **pilot** writes `pilot/results.md`, `pilot/summary.json`, `pilot/tables/run-records.csv`, `pilot/runs/*.json` and `pilot/projection.json`. These diagnose development and runtime feasibility; the report refuses to generate main-study figures from a pilot bundle. A **plan** bundle has all 232 main jobs marked `not_started`; its zero attempted counts do not mean algorithm failures or zero costs. A **check** bundle contains correctness evidence only.

Costs are modeled preference penalties, with lower values preferred under the same coefficients. Blank CSV cells / JSON `null` mean unavailable, including costs for missing or invalid maps. Greedy has no optimality certificate or lower bound. First-incumbent time is unavailable for this matched comparison because SCIP's installed wrapper lacks comparable callbacks. Human satisfaction and a combined algorithm-accuracy score are not measured.

## Frozen design

- Primary: 13 events × four configurations × three methods = **156 runs at five seconds**.
- Budget sensitivity: the three full 232-seat base patterns and 230-seat Emperor-heavy mixed event × three active configurations × three methods × 30/60-second limits = **72 additional runs**. Reuse the primary five-second endpoints on those same 12 matched cases.
- Prototype: **four separate checks** in current/default preference order, with 60 seconds of configured function allowance. These are excluded from controlled solver comparisons.
- Comparative search allocation: **67 minutes**. Four prototype allowances add four nominal minutes, with service overhead additional. Preparation, pilot, validation, persistence and reporting must fit the overall **90-minute ceiling**. Measured batches stop by minute 85, preserving five minutes for reports.
- Seeds: base input `20261021`, Emperor-heavy input `20261022`, development input `20261020`, search `20261012`, execution order `20261018`.
- Accessibility derivatives select the first lexicographically ordered witness-compatible registration IDs, up to `max(1, N // 10)`; if fewer candidates exist, select all available. Every required bundle must be wholly accessible. This is a constructed-feasibility sample, not a population model.

Feasibility witnesses use a deterministic occupied-seat prefix ordered by tier and contribution. Their audit is saved separately. Neither their placements nor another method's solution is passed to a timed solver as a hint.

The development pilot uses mixed small/typical/full/Emperor-heavy events at five seconds for all three methods, then the Emperor-heavy event at 30 and 60 seconds for all three methods, plus one prototype check. The default pilot allowance is 600 seconds; `--pilot-seconds` can set a positive allowance up to 900 seconds. In `run`, pilot time is also bounded by the overall deadline. The projection uses full declared search allocations and a margin over observed preparation/build/audit/process overhead; it does not rely on favorable early solver termination. If the projection exceeds 90 minutes, the runner stops before main runs and preserves its diagnostic. A protocol amendment, not an automatic budget increase or case deletion, is then needed.

## Model and timing boundaries

`common.py` shares request validation, maintained legal options and initial-row pruning, the compact current-ratio weights and independent rescoring. Three active preferences use 4:3:2, reversed order 2:3:4 in contribution/activity/category coordinates, two active preferences 4:0:3, and all-disabled 0:0:0. Production prototype weights remain in their original scale.

The compiled option vectors use a pure Decimal reference formula to avoid repeated policy-file reads during shared preprocessing. Preflight checks every compiled option against the maintained production scorer; returned plans are also rescored by both. Frozen input hashes are checked before every trial.

`adapters.py` uses the maintained CP-SAT builder and replaces only its weighted objective with the shared compact coefficients. SCIP independently encodes exactly-one allocation, physical seat exclusivity, integer boundaries for within-tier contribution rows and strict all-seat tier precedence, local packing and row-occupancy targets. It does not relax these rules or use a big-M surrogate. Tiny physical assignment enumeration checks objective and feasibility equivalence against both solvers.

Greedy selects the registration with the fewest remaining legal bundles, breaking ties by registration ID. It scans bundles by common cost then seat IDs. Each tentative choice filters other domains against occupied seats, tier precedence, contribution row order and remaining row capacity. Forward checks require nonempty domains, forced/possible row demand within capacity, sufficient union-of-seat capacity and support for unfilled packing predecessors. These are necessary checks, not a complete feasibility proof. It commits once and never backtracks, restarts, repairs or calls an exact solver. Dead ends are `CONSTRUCTION_FAILED`, not `INFEASIBLE`.

Preprocessing and model construction are measured separately from search. Search includes greedy ordering/filtering/forward checks and the exact solver invocation. Final extraction, independent validation and reference scoring are recorded; only validated complete maps enter cost analysis. Search ceilings are backend limits; an outer process-group watchdog covers construction, native search, validation and service descendants even if a backend fails to return.

Prototype subprocesses use fresh SQLite stores inside the evidence bundle. Their return timer includes startup, JSON serialization, solving, final formatting and local persistence. A separate research audit follows. Browser/network/remote database latency is excluded. A 60-second configured function allowance is not a 60-second service-response guarantee.

Peak resident memory is recorded for each fresh trial worker, including imports, construction and audit. Prototype child peak memory is recorded separately; the two peaks are not added or represented as a simultaneous process-tree peak. The runner uses POSIX process groups and supports the intended macOS/Linux environments.

## Evidence and interpretation

Each bundle contains source snapshots/hashes, environment and dependency lock, the complete ordered manifest, inputs, audited witnesses, correctness records, separate pilot records/projection, per-run JSON, tables and a generated report. Every main job starts as `not_started`. A watchdog preserves interruption or `validation_pending` states; it does not turn an unfinished allocation into a valid solution. Raw prototype output and isolated stores remain separate. Process startup and persistence count toward the overall ceiling even when outside the inner allocation timer.

The report generates CSV tables and, for main-study records, PDF/SVG/300-dpi PNG exports for solver outcomes, paired costs, budget response and the 230-seat map. Weighting Figures 4/5 belong to the second experiment. Matplotlib is used for scientific plots; records are never filled with invented measurements. Unsupported first-incumbent timing remains unavailable because the installed SCIP wrapper lacks comparable callbacks.

Report H1 per preference configuration, explore SCIP comparisons without assuming a winner, and assess 5→30 and 30→60 budget effects on exactly the same subset. Separate valid-plan coverage, common cost, component penalties, runtime and proof. These are descriptive synthetic observations, not statistical population claims or measurements of human satisfaction. Fresh budget endpoints are not a continuous convergence trace.
