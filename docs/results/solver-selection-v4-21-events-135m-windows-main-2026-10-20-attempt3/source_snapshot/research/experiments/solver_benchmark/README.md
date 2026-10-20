# Solver-selection benchmark

This research harness compares the maintained OR-Tools CP-SAT initial-allocation model (based on lazy clause generation), an equivalent mixed-integer linear formulation solved with SCIP, and the specified deterministic constraint-aware greedy method. It uses synthetic requests and isolated prototype stores. It does not change production policy or publish allocations.

The controlling documents are the [solver protocol](../../../docs/planning/solver-selection-benchmark.md), [hypotheses](../../../docs/planning/experiment-hypotheses-and-analysis.md), [execution guide](../../../docs/planning/experiment-execution-sequence.md), and [reporting plan](../../../docs/planning/benchmark-results-visualization.md). The rank-weighting runner is a separate, not-yet-implemented experiment.

The [18 October setup record](../../../docs/results/solver-benchmark-setup-2026-10-18.md) and its result bundles belong to the earlier protocol. A development pilot does not establish the dissertation hypotheses. The amended main study must be explicitly launched using `run` in a fresh directory.

## Confirmed amendment and current implementation

The user confirmed the [20 October scope amendment](../../../docs/planning/solver-benchmark-scope-amendment-2026-10-20.md): retain the original 13 inputs and generator, add two four-pattern families at 179/212 seats, reselect the longer-budget/prototype subset, and use 21 events / 328 main jobs / 28 pilot jobs. The completed Windows pilot projected 125.16 minutes, and the user authorized a separate [135-minute runtime amendment](../../../docs/planning/solver-benchmark-runtime-amendment-2026-10-20.md). Spreadsheet-derived candidate inputs remain excluded.

**The executable amendment is implemented.** The 28-job Windows development pilot completed under the earlier 120-minute protocol. The first v4 main attempt [stopped after a Windows file-replacement denial](../../../docs/results/solver-selection-v4-21-events-135m-windows-main-2026-10-20/manifest.json); its partial results remain separate evidence. The second attempt stopped on the same error during its pilot because the D: checkout still had the old writer. The [persistence amendment](../../../docs/planning/solver-benchmark-persistence-amendment-2026-10-20.md) adds bounded retries for transient Windows file-sharing denials, and the [checkpoint amendment](../../../docs/planning/solver-benchmark-checkpoint-amendment-2026-10-20.md) separates intermediate records from each trial's final JSON. The runner checks retained input digests, certifies the eight added events and their witnesses, and stops before main runs if its fresh pilot projection exceeds the amended 135-minute ceiling.

## Environment

From the repository root on Windows 11, use Python 3.12 or newer. The setup script now chooses the platform's virtual-environment interpreter. If `.venv` already exists and can import SCIP, use it directly:

```powershell
$python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
& $python --version
& $python -c "from ortools.linear_solver import pywraplp; s=pywraplp.Solver.CreateSolver('SCIP'); assert s is not None; print(s.SolverVersion())"
```

For a new environment, run `python research/experiments/setup_benchmark.py` with a Python 3.12+ interpreter. It creates the repository-local `.venv`, installs the tested dependency lock and checks SCIP availability. Each evidence bundle records its actual environment and `pip freeze`. There is no fallback to another MIP solver.

For this run, use the local Windows 11 machine plugged in and awake, with no competing heavy workloads. The controlled methods run sequentially with one worker. The four prototype checks preserve the source fixture's actual settings, currently eight workers and canonicalization enabled. Do not pool timings from different operating systems or hardware.

## Commands

These commands execute protocol `solver-selection-v4-21-events-135m-2026-10-20` with the recorded persistence and checkpoint safeguards. Use a distinct, previously nonexistent output directory for every `plan`, `check`, `pilot` or `run` invocation. `report` reads an existing bundle. Keep both stopped v4 attempts separate.

Every command except `report` requires a **new** output directory and refuses to overwrite an existing one. Dates in the examples are labels; choose a new suffix for another invocation.

```powershell
$python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
& $python -m pytest research/experiments/tests/test_solver_benchmark.py -q
& $python research/experiments/solver_selection_benchmark.py plan --out docs/results/solver-selection-v4-21-events-135m-windows-plan-2026-10-20-attempt3
# Optional separate development pilot. The main run repeats this gate inside its own clock.
& $python research/experiments/solver_selection_benchmark.py pilot --out docs/results/solver-selection-v4-21-events-135m-windows-pilot-2026-10-20-attempt3
# The main run repeats the pilot and can run for up to 135 minutes.
& $python research/experiments/solver_selection_benchmark.py run --out docs/results/solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3
# Rebuild reports from saved records without solving.
& $python research/experiments/solver_selection_benchmark.py report --out docs/results/solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3 --plots
```

`run` is the deliberate full-experiment command. It rechecks correctness and input witnesses, performs its own pilot, and evaluates the completion projection before starting main runs. A previous development pilot does not bypass these checks or move their cost outside the main runner's clock. No resume mode combines interrupted runs into an apparently complete original experiment.

The evidence writer retries short-lived Windows access-denied, sharing-violation or lock-violation errors during JSON publication. Trial checkpoints are stored under `runs/checkpoints/<id>/`; the parent publishes `runs/<id>.json` once after the worker exits. Persistent permissions still stop execution. Keep the new output directory on a writable local drive, avoid opening live evidence files with tools that hold them open, and preserve both stopped bundles. Verify `execution_status: completed`, all 328 jobs, and report completion before updating the dissertation's final results and discussion.

`plan` certifies the inputs and writes the full 328-job schedule without solving. Check `manifest.json` for 252 primary, 72 budget-sensitivity and four prototype jobs, and `inventory.json` for 21 events. `pilot` is separate development evidence; inspect `pilot/projection.json`. `run` repeats correctness, input certification and the 28-job pilot within its 135-minute clock. Do not edit solver code, configuration, inputs or planning files while it runs. Exit status 0 means the requested mode completed; stopped runs return nonzero with a reason in `manifest.json`.

## Where to find the results

The value passed to `--out` is the evidence directory. For a completed or partially completed **main** run, open its `results.md` first, then use these files:

| Location below `--out` | Contents and use |
|---|---|
| `manifest.json` | Protocol, exact environment/source hashes, seeds, full ordered 328-job schedule and completion/stop status |
| `inputs/*.json`, `witnesses/*.json`, `inventory.json` | Frozen synthetic events, independently audited feasibility witnesses and input certification; these are inputs, not solver outcomes |
| `runs/*.json` | Raw per-run data, complete seat maps, independent validation, costs/components, coefficients, available bounds/gaps, phase timings and memory scope |
| `runs/checkpoints/<id>/*.json` | Separate started, validation, service-return and worker records; diagnostic evidence only, never counted as validated results without a final run record |
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

The **pilot** writes `pilot/results.md`, `pilot/summary.json`, `pilot/tables/run-records.csv`, `pilot/runs/*.json` and `pilot/projection.json`. These diagnose development and runtime feasibility; the report refuses to generate main-study figures from a pilot bundle. A **plan** bundle has all 328 main jobs marked `not_started`; its zero attempted counts do not mean algorithm failures or zero costs. A **check** bundle contains correctness evidence only.

Costs are modeled preference penalties, with lower values preferred under the same coefficients. Blank CSV cells / JSON `null` mean unavailable, including costs for missing or invalid maps. Greedy has no optimality certificate or lower bound. First-incumbent time is unavailable for this matched comparison because SCIP's installed wrapper lacks comparable callbacks. Human satisfaction and a combined algorithm-accuracy score are not measured.

## Currently implemented design: 20 October 2026

- Primary: 21 events × four configurations × three methods = **252 runs at five seconds**.
- Budget sensitivity: high-, near-, full-capacity and Emperor-heavy mixed events × three active configurations × three methods × 30/60-second limits = **72 additional runs**. Reuse the primary five-second endpoints on those same 12 matched cases.
- Prototype: **four separate checks** in current/default preference order, with 60 seconds of configured function allowance. These are excluded from controlled solver comparisons.
- Comparative search allocation: **75 minutes**. Four prototype allowances add four nominal minutes, with service overhead additional. Preparation, pilot, validation, persistence and reporting must fit the overall **135-minute ceiling**. Measured batches stop by minute 130, preserving five minutes for reports.
- Seeds: base input `20261021`, Emperor-heavy input `20261022`, development input `20261020`, search `20261012`, execution order `20261018`.
- Accessibility derivatives select the first lexicographically ordered witness-compatible registration IDs, up to `max(1, N // 10)`; if fewer candidates exist, select all available. Every required bundle must be wholly accessible. This is a constructed-feasibility sample, not a population model.

Feasibility witnesses use a deterministic occupied-seat prefix ordered by tier and contribution. Their audit is saved separately. Neither their placements nor another method's solution is passed to a timed solver as a hint.

The development pilot uses six mixed events at five seconds for all three methods, then Emperor-heavy mixed at 30 and 60 seconds for all three methods, plus four prototype checks: 28 jobs and 600 seconds of nominal allowances. The default and maximum pilot ceiling are 900 seconds. In `run`, pilot time is also bounded by the overall deadline. The projection uses the complete declared schedule and a margin over measured preparation/build/audit/process overhead; it does not rely on favorable early solver termination. If the fresh projection exceeds 135 minutes, the runner stops before main runs and preserves its diagnostic.

## Model and timing boundaries

`common.py` shares request validation, maintained legal options and initial-row pruning, the compact current-ratio weights and independent rescoring. Three active preferences use 4:3:2, reversed order 2:3:4 in contribution/activity/category coordinates, two active preferences 4:0:3, and all-disabled 0:0:0. Production prototype weights remain in their original scale.

The compiled option vectors use a pure Decimal reference formula to avoid repeated policy-file reads during shared preprocessing. Preflight checks every compiled option against the maintained production scorer; returned plans are also rescored by both. Frozen input hashes are checked before every trial.

`adapters.py` uses the maintained CP-SAT builder and replaces only its weighted objective with the shared compact coefficients. SCIP independently encodes exactly-one allocation, physical seat exclusivity, integer boundaries for within-tier contribution rows and strict all-seat tier precedence, local packing and row-occupancy targets. It does not relax these rules or use a big-M surrogate. Tiny physical assignment enumeration checks objective and feasibility equivalence against both solvers.

Greedy selects the registration with the fewest remaining legal bundles, breaking ties by registration ID. It scans bundles by common cost then seat IDs. Each tentative choice filters other domains against occupied seats, tier precedence, contribution row order and remaining row capacity. Forward checks require nonempty domains, forced/possible row demand within capacity, sufficient union-of-seat capacity and support for unfilled packing predecessors. These are necessary checks, not a complete feasibility proof. It commits once and never backtracks, restarts, repairs or calls an exact solver. Dead ends are `CONSTRUCTION_FAILED`, not `INFEASIBLE`.

Preprocessing and model construction are measured separately from search. Search includes greedy ordering/filtering/forward checks and the exact solver invocation. Final extraction, independent validation and reference scoring are recorded; only validated complete maps enter cost analysis. Search ceilings are backend limits; an outer process-group watchdog covers construction, native search, validation and service descendants even if a backend fails to return.

Prototype subprocesses use fresh SQLite stores inside the evidence bundle. Their return timer includes startup, JSON serialization, solving, final formatting and local persistence. A separate research audit follows. Browser/network/remote database latency is excluded. A 60-second configured function allowance is not a 60-second service-response guarantee.

Peak resident memory is recorded for each fresh trial worker, including imports, construction and audit. On Windows, prototype child peak memory is unavailable from the standard library and remains blank. The watchdog terminates the process tree on Windows and POSIX process groups on macOS/Linux.

## Evidence and interpretation

Each bundle contains source snapshots/hashes, environment and dependency lock, the complete ordered manifest, inputs, audited witnesses, correctness records, separate pilot records/projection, per-run JSON, tables and a generated report. The manifest lists every scheduled main job; a missing final record without a checkpoint is reported as `not_started`. A watchdog and separate checkpoints preserve interruption or `validation_pending` evidence without turning an unfinished allocation into a valid solution. Raw prototype output and isolated stores remain separate. Process startup and persistence count toward the overall ceiling even when outside the inner allocation timer.

The report generates CSV tables and, for main-study records, PDF/SVG/300-dpi PNG exports for solver outcomes, paired costs, budget response and the 230-seat map. Weighting Figures 4/5 belong to the second experiment. Matplotlib is used for scientific plots; records are never filled with invented measurements. Unsupported first-incumbent timing remains unavailable because the installed SCIP wrapper lacks comparable callbacks.

Report H1 per preference configuration, explore SCIP comparisons without assuming a winner, and assess 5→30 and 30→60 budget effects on exactly the same subset. Separate valid-plan coverage, common cost, component penalties, runtime and proof. These are descriptive synthetic observations, not statistical population claims or measurements of human satisfaction. Fresh budget endpoints are not a continuous convergence trace.
