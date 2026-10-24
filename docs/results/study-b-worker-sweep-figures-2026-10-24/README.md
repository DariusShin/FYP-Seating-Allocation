# Worker/thread sweep: derived figures and tables

Rendered from the completed sweep's [run records](../study-b-worker-sweep-2026-10-24/tables/run-records.csv) only; no solver was run. [`manifest.json`](manifest.json) records the source hash, the best-setting summary and the hash of every output.

- **Figure B5** (`b5-sweep-time-cpu-memory`): complete service return, process CPU time and peak working set for every run at 1, 2, 4 and 8 workers/threads. Hollow markers are complete CP-SAT candidates that returned after the 60-second boundary and were not adopted; they are kept so that no run disappears. Table: [`level-summary.csv`](tables/level-summary.csv).
- **Figure B6** (`b6-best-setting-comparison`): each solver at its best observed setting (CP-SAT 8 workers, SCIP 1 thread) on the 12 matched runs. Every pair adopted and proved the same optimal penalty. This is an exploratory comparison and not part of the pre-registered decision rules. Table: [`best-setting-pairs.csv`](tables/best-setting-pairs.csv).

CPU time and peak working set are whole-process Windows measurements from fresh workers, including the Python service and native solver threads; they are not per-stage profiles.

Regenerate into a fresh folder from the repository root:

```powershell
.\.venv-study-b\Scripts\python.exe research/experiments/study_b_sweep_figures.py --source docs/results/study-b-worker-sweep-2026-10-24 --out docs/results/<new-folder>
```
