# Study B attempt 3: Windows checkpoint repair

Attempt 2 stopped after 125 of 144 scheduled initial-generation jobs. Its manifest says `failed`: the third 60-second `heavy-mixed/current` SCIP job raised Windows `PermissionError [WinError 5]` while replacing its candidate checkpoint. The weighted stage had returned `OPTIMAL` in 24.02 seconds with matching incumbent and bound, and the saved final-candidate temporary file passed independent validation. The failure occurred during evidence persistence, before the service could return and adopt that map. One job failed and 18 were not started. Attempt 2 remains incomplete evidence and must not be treated as a completed 60-second comparison.

## Repair and evidence rules

- Attempt 3 keeps the attempt 2 solver contract, inputs, settings, seeds, schedules, 5/30/60-second function allowances, and decision hierarchy. It changes checkpoint persistence and the study version. No production solver default changes.
- The raw pending candidate and independently validated candidate now have different destination files. This avoids immediately replacing the pending checkpoint with the final one, the operation that failed in attempt 2. Both paths and hashes are saved in completed records; all candidate artifacts are covered by the final manifest hashes.
- JSON writes use a unique temporary file in the target directory, flush and `fsync` it, then atomically replace the target. On Windows, only sharing/access-denied replacement errors (5, 32, 33) receive a bounded retry. A persistent failure still fails the run, preserving the temporary artifact for diagnosis. The service-return clock includes any retry delay.
- Every attempt 3 job uses a fresh worker and SQLite store. No attempt 2 record or candidate is replayed, repaired in place, or pooled with attempt 3. A fresh output directory is mandatory.

## Selection contract

The eight frozen workload/setting pairs each receive two raw repeats and one semantic permutation per backend at fresh 5-, 30- and 60-second allowances: 144 jobs, of which 48 are the primary 60-second jobs. Both CP-SAT and SCIP use eight workers/native threads. Canonical selection is off. A complete independently audited map returned within the shared function allowance may be adopted as `FEASIBLE` or `OPTIMAL`; proof coverage remains separate. No invalid adopted map is allowed. Compare 60-second valid-map coverage first, then penalty on matched valid cases, proof coverage, and complete local service-return time. Report unresolved trade-offs. The 5- and 30-second endpoints are diagnostics, not staff response-time requirements. Preference-update regeneration and absence repair remain outside this selection run.

The separate 96-job worker/thread sensitivity sweep remains optional and has its own denominator and 9,000-second overall cap. It tests 1/2/4/8 workers or native SCIP threads at 60 seconds on four predefined workload/setting pairs. Its results are not pooled into the main solver choice.

## Run on this Windows checkout

From the repository root, in the pinned `.venv-study-b` environment:

```powershell
.\.venv-study-b\Scripts\python.exe -m pytest research/experiments/tests/test_production_benchmark.py -q
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py plan --out docs/results/study-b-attempt3-plan
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py check --out docs/results/study-b-attempt3-check
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py run --out docs/results/study-b-windows-2026-10-23-attempt3
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py report --out docs/results/study-b-windows-2026-10-23-attempt3
```

Each command except `report` needs its own new output folder. `run` performs its own preflight and pilot, so a separate `check` is useful for early validation but is not a prerequisite. The overall main-run cap is 7,200 seconds; jobs are never silently shortened. A failure retains completed and unstarted records, and no partial run is called complete. The original attempt 2 directory is preserved unchanged.
