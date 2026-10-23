# Study B attempt 2: initial-generation solver selection

Attempt 1 remains immutable evidence. Its strict canonical-map adoption gate prevented otherwise valid allocations from being returned. Attempt 2 removes that gate from the experimental allocation function and measures the initial generation workflow only. The production default and `production.py` are unchanged.

## Service contract

- Both backends use the same production request, hard constraints, policy, preference weights and fixed seed. Each call uses the real local service, fresh SQLite store, formatter and JSON serialization.
- The weighted search has one shared allocation-function allowance. Canonical selection is off. A complete candidate returned by the weighted stage inside the allowance is independently audited and rescored. A valid candidate is returned and persisted even if weighted optimality is unproved; its solver status is `FEASIBLE`. A proven weighted minimum is `OPTIMAL`. No candidate, late candidate or invalid candidate is not adopted. Zero invalid adopted maps is mandatory.
- Record incumbent, best bound, gap, native status and native logs. A proof claim requires the API status, incumbent/bound agreement and no native gap-limit termination. Recompute every candidate's production penalty independently. Equal physical-map hashes are not required. Equivalent proven minima must agree on penalty.
- An identical-input cache may be a future system feature. The experiment does not use a cache and does not test map identity as a solver acceptance criterion.

## Fixed initial-generation schedule

The eight frozen Study A workload/setting pairs are `typical-mixed/current`, `high-mixed/current`, `near-mixed/current`, `full-mixed/current`, `heavy-mixed/current`, `full-conflict/reversed`, `full-tied/disabled`, and `full-accessible/two`. Each backend receives two raw repeats and one deterministic semantic permutation for each pair at each fresh allowance of 5, 30 and 60 seconds. Jobs run sequentially, alternating backend order. Search workers/SCIP native threads are both eight. The 60-second primary set has 48 jobs; the two diagnostic sets have 48 jobs each. Total nominal allowances are 4,560 seconds. The runner's overall cap remains 7,200 seconds including preflight, pilot, jobs and reporting. It projects overhead from the pilot and stops before measurement if the fixed work cannot fit. All nonstarted jobs stay explicit.

The 60 seconds is a current engineering setting, not an established staff response-time requirement. The 5- and 30-second results are diagnostic endpoints, not substitutes for 60-second results. A stage-return clock is not first incumbent discovery. Complete local service return additionally includes audit, formatting, SQLite persistence and JSON encoding; it excludes process startup and browser/network time.

## Selection rule

First compare valid-map coverage among all scheduled 60-second jobs. Then compare production penalty on matched valid pairs, proof coverage, and complete service-return time. Do not compare penalty for disabled preferences or across different settings. Record no-map/error counts and zero invalid adopted maps. A completed, audited run is required for a selection judgment. If the measures trade off without a clear winner, report the trade-off and do not force a new default. Three repeats describe these cases and do not establish a population reliability estimate.

Preference-setting regeneration and absence repair are deferred until the initial-generation solver decision is confirmed. No production refactor follows automatically from this experiment.

## Separate concurrency sensitivity

Run a separate sweep on `typical-mixed/current`, `heavy-mixed/current`, `full-tied/disabled`, and `full-accessible/two`: 1, 2, 4 and 8 CP-SAT workers versus the same native SCIP thread levels; both backends, two raw repeats and one semantic permutation at 60 seconds. This is 96 jobs and 5,760 nominal seconds with a separate 9,000-second overall runner cap for preflight, pilot, measurements and reporting. The main selection denominator is unaffected. Record native SCIP concurrent-instance launches per call, process CPU seconds around the service call, process peak working set, penalty, proof and complete service time. Native launches demonstrate concurrency support but are not a utilization measurement. Windows peak working set is a process-lifetime measure; interpret it with that limitation.

## Windows commands

From the repository root, use the pinned `.venv-study-b` after running `py -3.14 research/experiments/setup_production_benchmark.py` if the environment has not been prepared. Every plan/check/run needs a fresh output directory. Never reuse or modify attempt 1.

```powershell
.\.venv-study-b\Scripts\python.exe -m pytest research/experiments/tests/test_production_benchmark.py -q
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py plan --out docs/results/study-b-attempt2-plan
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py check --out docs/results/study-b-attempt2-check
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py run --out docs/results/study-b-windows-2026-10-23-attempt2
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py report --out docs/results/study-b-windows-2026-10-23-attempt2
```

The optional separate sweep uses `plan-sweep` and `sweep`, each with a fresh output directory. `check` does not run measured jobs. `run` and `sweep` perform their own preflight and pilot. Review `manifest.json`, `checks.json`, `summary.json`, `results.md`, CSV tables, figures, native logs and saved candidate/response records together. Failed source, native concurrency or correctness gates stop measurement. A fresh attempt receives a new directory; nothing resumes or silently shortens allowances.
