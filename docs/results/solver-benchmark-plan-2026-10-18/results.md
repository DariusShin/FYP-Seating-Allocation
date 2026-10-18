# Solver-selection benchmark evidence

Protocol: `solver-selection-v1-2026-10-18`. Mode: **plan**. Status: **planned**.

All figures/tables derive from saved records. Pilot and correctness observations are separate from main-study evidence.

| Batch | Budget (s) | Configuration | Method | Planned | Attempted | Validated |
|---|---:|---|---|---:|---:|---:|
| primary | 5 | current | cp_sat | 13 | 0 | 0 |
| primary | 5 | current | scip | 13 | 0 | 0 |
| primary | 5 | current | greedy | 13 | 0 | 0 |
| primary | 5 | reversed | cp_sat | 13 | 0 | 0 |
| primary | 5 | reversed | scip | 13 | 0 | 0 |
| primary | 5 | reversed | greedy | 13 | 0 | 0 |
| primary | 5 | two | cp_sat | 13 | 0 | 0 |
| primary | 5 | two | scip | 13 | 0 | 0 |
| primary | 5 | two | greedy | 13 | 0 | 0 |
| primary | 5 | disabled | cp_sat | 13 | 0 | 0 |
| primary | 5 | disabled | scip | 13 | 0 | 0 |
| primary | 5 | disabled | greedy | 13 | 0 | 0 |
| budget_sensitivity | 30 | current | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 30 | current | scip | 4 | 0 | 0 |
| budget_sensitivity | 30 | current | greedy | 4 | 0 | 0 |
| budget_sensitivity | 30 | reversed | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 30 | reversed | scip | 4 | 0 | 0 |
| budget_sensitivity | 30 | reversed | greedy | 4 | 0 | 0 |
| budget_sensitivity | 30 | two | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 30 | two | scip | 4 | 0 | 0 |
| budget_sensitivity | 30 | two | greedy | 4 | 0 | 0 |
| budget_sensitivity | 60 | current | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 60 | current | scip | 4 | 0 | 0 |
| budget_sensitivity | 60 | current | greedy | 4 | 0 | 0 |
| budget_sensitivity | 60 | reversed | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 60 | reversed | scip | 4 | 0 | 0 |
| budget_sensitivity | 60 | reversed | greedy | 4 | 0 | 0 |
| budget_sensitivity | 60 | two | cp_sat | 4 | 0 | 0 |
| budget_sensitivity | 60 | two | scip | 4 | 0 | 0 |
| budget_sensitivity | 60 | two | greedy | 4 | 0 | 0 |
| prototype | 60 | current | cp_sat | 4 | 0 | 0 |

## Paired common-cost comparisons

Negative differences favor CP-SAT. Configurations remain separate; failed maps have no cost score.

| Configuration | Comparator | Both valid | CP lower / tie / higher | Median difference per registration |
|---|---|---:|---|---:|
| current | greedy | 0/13 | 0 / 0 / 0 | N/A |
| current | scip | 0/13 | 0 / 0 / 0 | N/A |
| reversed | greedy | 0/13 | 0 / 0 / 0 | N/A |
| reversed | scip | 0/13 | 0 / 0 / 0 | N/A |
| two | greedy | 0/13 | 0 / 0 / 0 | N/A |
| two | scip | 0/13 | 0 / 0 / 0 | N/A |

## Budget subset coverage

Same four events per configuration at every allowance; this includes reused five-second records.

| Configuration | Method | Allowance (s) | Attempted / planned | Validated |
|---|---|---:|---|---:|
| current | cp_sat | 5 | 0/4 | 0 |
| current | cp_sat | 30 | 0/4 | 0 |
| current | cp_sat | 60 | 0/4 | 0 |
| current | scip | 5 | 0/4 | 0 |
| current | scip | 30 | 0/4 | 0 |
| current | scip | 60 | 0/4 | 0 |
| current | greedy | 5 | 0/4 | 0 |
| current | greedy | 30 | 0/4 | 0 |
| current | greedy | 60 | 0/4 | 0 |
| reversed | cp_sat | 5 | 0/4 | 0 |
| reversed | cp_sat | 30 | 0/4 | 0 |
| reversed | cp_sat | 60 | 0/4 | 0 |
| reversed | scip | 5 | 0/4 | 0 |
| reversed | scip | 30 | 0/4 | 0 |
| reversed | scip | 60 | 0/4 | 0 |
| reversed | greedy | 5 | 0/4 | 0 |
| reversed | greedy | 30 | 0/4 | 0 |
| reversed | greedy | 60 | 0/4 | 0 |
| two | cp_sat | 5 | 0/4 | 0 |
| two | cp_sat | 30 | 0/4 | 0 |
| two | cp_sat | 60 | 0/4 | 0 |
| two | scip | 5 | 0/4 | 0 |
| two | scip | 30 | 0/4 | 0 |
| two | scip | 60 | 0/4 | 0 |
| two | greedy | 5 | 0/4 | 0 |
| two | greedy | 30 | 0/4 | 0 |
| two | greedy | 60 | 0/4 | 0 |

## Prototype timing checks

Separate eight-worker/canonicalization configuration. Service return includes local persistence; production objective/proofs remain on their original scale.

| Event | Execution | Solver | Valid | Service return (s) | Total through research audit (s) |
|---|---|---|---|---:|---:|
| full-conflict | not_started | N/A | False | N/A | N/A |
| full-mixed | not_started | N/A | False | N/A | N/A |
| heavy-mixed | not_started | N/A | False | N/A | N/A |
| full-tied | not_started | N/A | False | N/A | N/A |

Full phase timings, costs, components and bounds are in `tables/run-records.csv`; unmatched costs remain unavailable.

## Interpretation limits

- Synthetic related cases, no repeated timing trials or population significance tests.
- Costs conditioned on both-valid pairs; inspect failures and coverage.
- Budget comparisons are fresh-run endpoints, not convergence traces.
- Prototype settings differ from controlled comparisons; human satisfaction not measured.

**No main benchmark measurements were collected in this command.**
