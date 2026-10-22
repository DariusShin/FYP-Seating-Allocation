# Study B: production solver comparison on Windows 11

Implementation branch: `codex/study-b-production-benchmark`, based on `codex/experiment-workspace-setup`. **The measured study has not been run.** This package implements the [agreed protocol](../../../docs/planning/solver-selection-production-follow-up.md). It is separate from [Study A](../../../docs/results/solver-selection-v4-attempt3-results-and-discussion.md), and never rewrites its evidence.

## What is being compared

Both initial-allocation implementations go through the real local `service.dispatch`, `PlanStore`, result formatter, placement audit and JSON serialization in a fresh worker and isolated SQLite store. The experimental worker injects its allocation function into that worker's service module, then restores the original reference. Application source files and the app's CP-SAT default are unchanged. This is a production-path experiment, not deployment of a new default solver.

CP-SAT reuses the maintained `production.build`. SCIP expresses the same binary seat-bundle assignment, entitlement, uniqueness, blocked/accessibility, tier precedence, contribution-row order, front fill and side packing constraints with MPSolver. Both use the production scorer and rank coefficients: current 40:30:20, reversed 20:30:40, two 40:0:30 and disabled 0:0:0. An independent Decimal scorer and physical-map validator check the encodings. Study A's compact penalty magnitudes are not mixed with these production penalties.

Weighted optimization requests eight workers/threads. Both canonical procedures use one worker and the same registration-ID/lexicographic seat-bundle ordering, fixing each proven minimum before proceeding. SCIP uses native `SetNumThreads(8)`; setting only `parallel/maxnthreads` is insufficient in the pinned MPSolver integration. All native proof/gap/thread parameters are re-applied on every solve, and gap tolerances are explicitly zero. A returned API OPTIMAL label is not sufficient for proof: incumbent/bound agreement within 1e-6 and native gap-limit termination are checked separately.

SCIP uses `INCREMENTALITY_OFF` on every stage to recreate native state from the retained MPSolver model, avoiding interrupted/transformed state leaking from concurrent weighted optimization into sequential canonical solves. All accumulated hard constraints and proven objective fixes are retained. Native re-extraction time is inside the recorded solve call and consumes the shared allowance; it is not granted an extra budget.

Canonical selection must complete inside one shared 60/180-second function allowance before a new map is adopted. Valid but unproved, incomplete-canonical or late-canonical candidates are saved separately and rejected. A prior map is preserved. Final audit, formatting, service persistence and JSON encoding can extend actual service return past the internal allowance. The late-canonical category identifies native solve/processing overruns rather than concealing them.

## Windows 11 installation

Use native 64-bit Windows 11, at least eight logical CPUs, stable power and no competing heavy jobs. Python 3.14 matches the Study A interpreter family; 64-bit Python 3.12+ is supported by the setup. Git must be available for provenance. First make this branch's committed checkout available on the Windows machine; the setup does not push, pull or change branches for you.

From the repository root in PowerShell:

```powershell
git switch codex/study-b-production-benchmark
py -3.14 research/experiments/setup_production_benchmark.py
.\.venv-study-b\Scripts\python.exe -m pytest research/experiments/tests/test_production_benchmark.py -q
```

If Python 3.14 is unavailable, use an installed 64-bit Python 3.12/3.13 launcher, for example `py -3.12`. The setup creates only `.venv-study-b`, uses an exact dependency lock plus psutil, and never runs the measured study. Existing unowned environments are refused. It does not modify the production `.venv` or system Python. No activation script or execution-policy change is required for the direct Python commands.

## Commands and execution order

Each command except `report` requires a **new output directory**. Do not reuse check/pilot evidence as the measured sample. Replace example dates/attempt suffixes as appropriate.

```powershell
# Freeze the schedule/inputs/source snapshot, without any optimization calls:
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py plan --out docs/results/study-b-plan-2026-10-23

# Separate installation/correctness/concurrency validation (no measured jobs):
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py check --out docs/results/study-b-check-2026-10-23

# Optional standalone pilot; still excludes all measured denominators:
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py pilot --out docs/results/study-b-pilot-2026-10-23

# Complete fixed run: its OWN preflight, pilot, measured batches and reporting:
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py run --out docs/results/study-b-windows-2026-10-23-attempt1

# Regenerate derived tables/figures from saved records, without any solves:
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py report --out docs/results/study-b-windows-2026-10-23-attempt1
```

An equivalent wrapper is `./research/experiments/run_study_b_windows.ps1 -Mode run -Out docs/results/study-b-windows-2026-10-23-attempt1`. If local policy disallows `.ps1`, use the direct interpreter commands. `--no-plots` is available for check/pilot/run/report; it does not remove trial records or tables. No solver or reporting command resumes, silently reduces the workload or replaces the source evidence.

The `run` command enforces a 7,200-second overall wall-clock cap including input/source preparation, up to five minutes preflight, up to fifteen minutes pilot, the measured schedule and a five-minute reporting reserve. The pilot projects the full 80 minutes of nominal measured allowances plus conservative observed overhead. It stops before measurement when the schedule cannot fit, or when overhead exceeds the planned fifteen-minute reserve. Interruptions and deadlines retain checkpoints and mark unexecuted jobs explicitly. A new attempt must use a new folder.

A job is not launched when there is insufficient time for its full original allowance plus watchdog margin; it is marked not started and the batch stops. Reporting leaves ten seconds for forced cleanup/final metadata. These guards may stop a run conservatively; they never change selected search allowances to squeeze in the schedule. Do not edit snapshotted sources while a run is active.

## Fixed schedule and input provenance

Eight predefined pairs are `typical-mixed/current`, `high-mixed/current`, `near-mixed/current`, `full-mixed/current`, `heavy-mixed/current`, `full-conflict/reversed`, `full-tied/disabled` and `full-accessible/two`. Their input JSON and constructive witnesses are copied from the completed Study A bundle and checked against its manifest hashes. No new participants are synthesized and no old performance observations enter Study B.

| Batch | Design | Jobs | Nominal allowance |
| --- | --- | ---: | ---: |
| Primary | 8 pairs × 2 backends × 3 executions × 60 s | 48 | 48 min |
| Diagnostic | Heavy/current and full-tied/disabled × 2 backends × 2 raw repeats × 180 s | 8 | 24 min |
| Regeneration | Typical/current, full/current, heavy/current, full-accessible/two × 2 origin backends → CP-SAT × 60 s | 8 | 8 min |
| Total | Separate batch labels retained | 64 | 80 min |

Primary executions are raw repeat 1, raw repeat 2 and one deterministic permutation of participant/seat/pair array order. The seed stays 20260918 and the permutation seed is 20261023. Backend order alternates deterministically; jobs never run concurrently. Normalization sorts incidental arrays while preserving preference ranking. The semantic hash excludes execution configuration and generation-mode labels; other request content remains part of its identity. Physical-map hashes contain sorted registration-to-physical-seat IDs, not generated timestamps, JSON response order or internal variable IDs.

Regeneration uses the first scheduled accepted **primary** baseline for its origin backend. A full production response is seeded into a fresh store, then the service receives unchanged preferences with `REGENERATE_DRAFT` and CP-SAT. The recorded baseline identity, map equality and preservation state make this bridge auditable. If no primary baseline exists, the link is `unmet_prerequisite`; a diagnostic result is never substituted. This evaluates unchanged-input interoperability, not changed-preference or absence repair performance.

The six separate pilot jobs are both backends on full-tied/disabled at 180 seconds, both on heavy/current at 60 seconds and two CP-SAT regeneration links from the heavy origins. If a pilot origin is unavailable, its regeneration is explicitly unmet. Projection uses a conservative doubled initial-overhead estimate for regeneration when no measured pilot link exists, and labels that estimate. It does not invent a baseline.

## Gates and Windows-specific behavior

Preflight records the installed versions/hardware, requires the pinned OR-Tools version, and performs:

1. A short, non-seating knapsack probe with an independently computed dynamic-programming optimum. Passing requires **eight distinct native SCIP concurrent-solver launch messages**, the expected objective and a matching proof bound in a saved log. A parameter returning true alone cannot pass. Unsupported builds stop with no single-thread fallback.
2. Seventy-two tiny oracle comparisons (nine cases × four settings × two backends) for objective minima, hard feasibility and the unique canonical map, including infeasible, empty, pair, tier, two-row and accessibility cases.
3. Real service/SQLite initial and regeneration round-trips from both backends on tiny inputs, plus an intentionally interrupted canonical procedure verifying preservation of the baseline. These are correctness checks, not measured workload observations.
4. Independent audits of all eight frozen constructive witnesses, row-pruned domains and every candidate scoring vector under the production coefficients.

Native launch messages establish concurrent-build support, not eight-core utilization for every solve. Easy cases may finish in presolve before concurrent instances launch; each stage retains its actual native log and observed launch count. The gate must pass again on Windows even if development checks passed on another OS. An unproved/time-limited probe cannot pass; the probe and the separate placement/canonical oracles both establish their respective correctness requirements.

Windows workers use fresh subprocesses, UTF-8 JSON/logging, portable interpreter paths, psutil memory handling, native `taskkill /T` and atomic record replacement. Windows has no `resource` or POSIX process-group dependency; POSIX groups are used only as a non-Windows development fallback. The outer watchdog covers native solves and descendants. A Windows process lifetime peak working set includes native solver threads; development RSS uses a separately labeled method and is never pooled with Windows measurements. SQLite stores are private to jobs and excluded from version control.

## Evidence, clocks and reporting

`manifest.json` records the complete fixed schedule, immutable input/witness/source hashes, environment/pip freeze, branch revision, execution status and cap/projection. `source_snapshot/` includes code, configuration, schemas, request fixture, dependency lock and protocol. Every scheduled job has a record before execution. `runs/`, `pilot/runs/`, payloads, raw responses, candidate checkpoints and native logs retain unsuccessful outcomes as well as successes. Native logs are explicitly unignored in the evidence folder so concurrency provenance can be committed. Scratch `stores/` are ignored.

Measurements separate raw candidate validity, weighted proof, canonical progress/completion, completion inside the shared allowance, adoption, and actual complete service return. Stage-return time is not first optimal-incumbent discovery. Disjoint phase timings cover normalization, model build, weighted/canonical search, model updates, extraction, independent audit/scoring and formatting; residual function and service/JSON overhead reconcile totals. The service clock ends when the real dispatch result is serialized, including SQLite adoption. It excludes interpreter imports and baseline hydration, which have separate worker/preparation clocks. No HTTP/browser/network latency is claimed.

The reporter revalidates saved candidates and production responses, rescoring with Decimal arithmetic; accepted maps must satisfy the full gate. Completed canonical results for equivalent inputs must agree on both objective and physical-map hash. Disagreement is a defect, not a preferred solver's win. Tables distinguish missing execution, no candidate, valid but unproved, incomplete canonical selection, late completion, invalid candidate and unmet baseline prerequisites.

When measured observations exist, the reporter creates:

- **B1:** primary outcomes for all 48 jobs, retaining repeat/permutation identity and adoption states.
- **B2:** complete service-return times for all primary calls, with predefined heavy/tied raw-1 phase examples.
- **B3:** exact physical-map equality for raw repeats, permutations, cross-backend returns and regeneration; missing prerequisites remain explicit.
- **B4:** matched 60/180-second diagnostic statuses and phase times, including both raw repetitions.
- **B5:** first scheduled accepted 230-seat primary maps, labeled with weighted-proof stage return, canonical completion and complete service time. Missing 60-second maps remain missing; a separate 180-second row is added when needed.

Figures export PDF/SVG/300-dpi PNG. A coverage table, per-run records, paired objective table, disjoint phase table, comparison provenance, checks, summary and `results.md` accompany them. No measured-looking placeholder figures are generated for plan/check/pilot-only folders. Disabled costs are not meaningful preference-quality evidence. Three executions are a limited repeatability/order check, not a population confidence or tail-latency study. The reporter selects no automatic winner and no production default.

If source files have changed after the run, use the same pinned environment with the archived entry point at `<run-folder>/source_snapshot/research/experiments/production_solver_benchmark.py report --out <absolute-run-folder>`. The reporter rejects changed inputs, record/log checksums and live source drift instead of silently analyzing with a different model/scorer. SQLite scratch state is not required to regenerate reports.

## Local development only

```sh
.venv-study-b/bin/python -m pytest research/experiments/tests/test_production_benchmark.py -q
.venv-study-b/bin/python research/experiments/production_solver_benchmark.py check --development --out /tmp/study-b-development-check
```

`--development` is accepted only by `check`. Measured `run` and standalone `pilot` require native Windows 11. Development output is labeled and excluded from dissertation denominators. No Windows execution or production suitability is established merely by passing local tests.

## Primary implementation references

The [pinned OR-Tools SCIP interface](https://github.com/google/or-tools/blob/v9.15/ortools/linear_solver/scip_interface.cc) documents the native threading switch, per-solve parameter reset and GAPLIMIT status mapping. The [SCIP concurrent-solving guide](https://scipopt.org/doc/html/CONCSCIP.php) describes the build requirement and concurrent API. These motivate the native-log gate; they do not certify a particular installed Windows wheel.
