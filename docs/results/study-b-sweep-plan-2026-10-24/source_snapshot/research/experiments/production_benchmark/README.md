# Study B attempt 3

The [attempt 3 protocol](../../../docs/planning/solver-selection-production-attempt3.md) describes the Windows candidate-checkpoint repair and unchanged initial-generation comparison. Attempt 2 stopped after 125 completed jobs because Windows denied an atomic replacement of a checkpoint file. Its saved evidence remains untouched; attempt 3 uses fresh workers, stores and an entirely new output directory. The production default is unchanged.

The experimental function is injected into the real local `service.dispatch`, which uses a private SQLite store and serializes the returned response. Both backends reuse production constraints and penalty scoring. Canonical selection is disabled. A candidate is adopted as `FEASIBLE` or `OPTIMAL` only after independent validation and scoring. A missing, invalid or late candidate is not adopted. Proof is checked against incumbent, bound, API status and native SCIP gap termination.

Each candidate first has a pending checkpoint, then a separate validated-candidate checkpoint. JSON artifacts use unique temporary names, `fsync`, and bounded Windows sharing-lock retries before atomic replacement. Completed records and the final manifest hash these artifacts. Persistent file errors still stop measurement and preserve evidence.

From the repository root in the pinned Windows `.venv-study-b` environment:

```powershell
.\.venv-study-b\Scripts\python.exe -m pytest research/experiments/tests/test_production_benchmark.py -q
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py plan --out docs/results/study-b-attempt3-plan
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py check --out docs/results/study-b-attempt3-check
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py run --out docs/results/study-b-windows-2026-10-23-attempt3
```

Use `report --out <completed-folder>` to regenerate derived tables and figures without solving. Every `plan`, `check`, `run`, `plan-sweep`, or `sweep` needs a fresh folder. `run` executes its own preflight and pilot; `check` is optional early validation. The PowerShell wrapper `research/experiments/run_study_b_windows.ps1` supports the same modes. `--no-plots` suppresses figures while retaining records and tables.

The main design has 144 jobs: eight frozen workload/setting pairs, three repeats, two backends and fresh 5/30/60-second allowances. The 60-second group is primary. The optional 96-job worker/thread sweep has a separate denominator. The runner retains raw responses, pending and final candidate checkpoints, native logs, checksums, source snapshots, environment details and explicit unstarted records. The reporter re-audits saved candidates and production responses, and compares weighted minima only when proven. It does not require identical physical maps. Complete service-return time includes local validation, persistence and JSON encoding; no staff response-time target is implied.
