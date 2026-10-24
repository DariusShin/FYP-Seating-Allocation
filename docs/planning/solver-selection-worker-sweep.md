# Study B worker/thread sweep: pre-registered design and interpretation rules

*Written 24 October 2026, before any sweep job was executed. This document must be committed before `sweep` is run so that the git history shows the interpretation rules were fixed before the results existed. Results must not change these rules. Any change after execution is an amendment, must be labelled as such, and must not replace the original rule.*

## Purpose

Study A (one worker) and Study B attempt 3 (eight workers) gave opposite timing rankings for CP-SAT and SCIP. Because the two studies also differed in harness, clock, case selection and repetition, the cause of the reversal could not be identified. This sweep holds the production harness, cases, clock, seeds and allowance fixed and varies only the worker/native-thread count. It answers one question: **does the solver ranking under the registered selection hierarchy change with the number of workers?**

The sweep is supporting evidence. The initial-generation solver selection rests on the Study B attempt 3 primary cohort (48 jobs at 60 seconds and eight workers). Sweep jobs have their own denominator and are never pooled into that cohort.

## Fixed design

The design is implemented in `research/experiments/production_benchmark/protocol.py` (`sweep_schedule`, `sweep_pilot_schedule`) and covered by `test_main_and_sweep_designs_are_fixed_and_separate`. It is not modified for this run.

| Factor | Levels |
| --- | --- |
| Event–setting pairs | `typical-mixed/current`, `heavy-mixed/current`, `full-tied/disabled`, `full-accessible/two` (Study B attempt 3 inputs, unchanged hashes) |
| Backends | CP-SAT, SCIP |
| Workers / native SCIP threads | 1, 2, 4, 8 |
| Executions per pair, backend and level | 3 (executions 1–2 original order; execution 3 semantics-preserving permutation) |
| Shared function allowance | 60 s |
| Seeds | Search seed 20260918, order seed 20261023 (as attempt 3) |
| Canonical selection | Off |
| Measured jobs | 96 (24 per worker level); nominal allowance 5,760 s; runner cap 9,000 s |
| Pilot | `heavy-mixed/current` at 1/2/4/8 for both backends (8 jobs; excluded from the denominator) |

Validity, adoption, proof and clock definitions are identical to Study B attempt 3: a candidate is adopted only if it passes independent validation and its weighted stage returns within the allowance; complete service return is the primary time measure.

## Decision rules applied separately at each worker level

At each worker level there are 12 matched pairs (4 event–setting pairs × 3 executions), of which 9 have active preferences. The registered hierarchy is applied in order, and the first rule that separates the backends decides the ranking at that level.

1. **Validity gate.** A backend with any invalid adopted map fails at that level regardless of later rules.
2. **Coverage.** The backend with more adopted validated maps out of 12 ranks first. Adopted `FEASIBLE` maps count.
3. **Cost.** Over active-preference pairs in which both backends adopted a map, the backend with the lower penalty in a strict majority of those pairs ranks first. If every such pair is equal, this rule ties.
4. **Proof.** The backend with more proven weighted optima out of 12 ranks first.
5. **Time.** Over pairs in which both backends adopted a map, the backend with the shorter complete service return in a strict majority of those pairs ranks first. When all 12 pairs are valid this means at least 7 of 12. The exact count and the median paired difference are always reported.

If no rule separates the backends, neither ranks first at that level. Consistency (identical coverage outcome and proven penalty across the three executions, and the spread of complete service return) is reported as supporting evidence and is not a ranking rule.

## Pre-registered interpretation (binding)

Scenarios are evaluated in the order below; the first that applies is the reading.

**Scenario 3 — eight-worker result not reproduced.** At 8 workers, SCIP ranks first or neither backend ranks first. *Reading:* the Study B attempt 3 selection stands, because its 48-job primary cohort is the registered decision evidence, but the chapter must report that the eight-worker CP-SAT advantage was not reproduced in this sensitivity check and must weaken the claim to "CP-SAT was faster in the primary comparison; this was not reproduced in the sweep." The sweep must not be rerun or omitted because of this outcome.

**Scenario 1 — configuration-dependent ranking.** SCIP ranks first at 1 worker and CP-SAT ranks first at 8 workers. *Reading:* the solver ranking depends on the parallel configuration, which explains the difference between Study A and Study B within a single harness. The 2- and 4-worker levels describe where the crossover occurs.

**Scenario 2 — CP-SAT first at every level.** CP-SAT ranks first at 1, 2, 4 and 8 workers. *Reading:* worker count does not explain Study A's single-worker result; the difference more plausibly arises from harness differences (model-construction path, clock definition). This is reported honestly as leaving the Study A reversal unexplained, while strengthening the CP-SAT selection.

**Scenario 4 — mixed or case-dependent.** Any pattern not covered above, including a level at which neither backend ranks first below 8 workers, or a non-monotonic sequence of winners. *Reading:* the configuration effect is case-dependent; results are reported per case and level, and no general claim about parallelism is made.

## What the sweep cannot establish

Four pairs, three executions and one workstation describe observed behaviour; they do not estimate population reliability or tail latency. Only three pairs have active preferences. The sweep does not isolate solver internals, does not test other allowances, and does not test greedy or any other method.

## Execution and failure handling

Run from the repository root on Windows 11 in `.venv-study-b`, after this document and the benchmark code are committed:

```powershell
.\.venv-study-b\Scripts\python.exe -m pytest research/experiments/tests/test_production_benchmark.py -q
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py plan-sweep --out docs/results/study-b-sweep-plan-2026-10-24
.\.venv-study-b\Scripts\python.exe research/experiments/production_solver_benchmark.py sweep --out docs/results/study-b-worker-sweep-2026-10-24
```

`sweep` performs its own preflight, pilot and report. If the run stops, its records are preserved and no partial result is described as complete. A fresh attempt in a new folder is permitted only for a documented infrastructure failure (for example a file-system or power interruption), recorded in an amendment note before the new attempt starts. An unwelcome result is never a reason for a new attempt.
