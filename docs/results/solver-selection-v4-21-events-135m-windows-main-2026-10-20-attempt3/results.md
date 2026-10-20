# Solver-selection benchmark evidence

Protocol: `solver-selection-v4-21-events-135m-2026-10-20`. Mode: **run**. Status: **completed**.

All figures/tables derive from saved records. Pilot and correctness observations are separate from main-study evidence.

| Batch | Budget (s) | Configuration | Method | Planned | Attempted | Validated |
|---|---:|---|---|---:|---:|---:|
| primary | 5 | current | cp_sat | 21 | 21 | 15 |
| primary | 5 | current | scip | 21 | 21 | 9 |
| primary | 5 | current | greedy | 21 | 21 | 6 |
| primary | 5 | reversed | cp_sat | 21 | 21 | 16 |
| primary | 5 | reversed | scip | 21 | 21 | 7 |
| primary | 5 | reversed | greedy | 21 | 21 | 3 |
| primary | 5 | two | cp_sat | 21 | 21 | 19 |
| primary | 5 | two | scip | 21 | 21 | 10 |
| primary | 5 | two | greedy | 21 | 21 | 4 |
| primary | 5 | disabled | cp_sat | 21 | 21 | 20 |
| primary | 5 | disabled | scip | 21 | 21 | 17 |
| primary | 5 | disabled | greedy | 21 | 21 | 0 |
| budget_sensitivity | 30 | current | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 30 | current | scip | 4 | 4 | 4 |
| budget_sensitivity | 30 | current | greedy | 4 | 4 | 1 |
| budget_sensitivity | 30 | reversed | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 30 | reversed | scip | 4 | 4 | 4 |
| budget_sensitivity | 30 | reversed | greedy | 4 | 4 | 1 |
| budget_sensitivity | 30 | two | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 30 | two | scip | 4 | 4 | 4 |
| budget_sensitivity | 30 | two | greedy | 4 | 4 | 0 |
| budget_sensitivity | 60 | current | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 60 | current | scip | 4 | 4 | 4 |
| budget_sensitivity | 60 | current | greedy | 4 | 4 | 1 |
| budget_sensitivity | 60 | reversed | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 60 | reversed | scip | 4 | 4 | 4 |
| budget_sensitivity | 60 | reversed | greedy | 4 | 4 | 1 |
| budget_sensitivity | 60 | two | cp_sat | 4 | 4 | 4 |
| budget_sensitivity | 60 | two | scip | 4 | 4 | 4 |
| budget_sensitivity | 60 | two | greedy | 4 | 4 | 0 |
| prototype | 60 | current | cp_sat | 4 | 4 | 4 |

## Paired common-cost comparisons

Negative differences favor CP-SAT. Configurations remain separate; failed maps have no cost score.

| Configuration | Comparator | Both valid | CP lower / tie / higher | Median difference per registration |
|---|---|---:|---|---:|
| current | greedy | 5/21 | 5 / 0 / 0 | -22.208333333333332 |
| current | scip | 9/21 | 0 / 4 / 5 | 0.3958333333333333 |
| reversed | greedy | 2/21 | 2 / 0 / 0 | -13.100340780007574 |
| reversed | scip | 7/21 | 0 / 5 / 2 | 0.0 |
| two | greedy | 4/21 | 4 / 0 / 0 | -16.9375 |
| two | scip | 10/21 | 0 / 4 / 6 | 4.46875 |

## Budget subset coverage

Same four events per configuration at every allowance; this includes reused five-second records.

| Configuration | Method | Allowance (s) | Attempted / planned | Validated |
|---|---|---:|---|---:|
| current | cp_sat | 5 | 4/4 | 2 |
| current | cp_sat | 30 | 4/4 | 4 |
| current | cp_sat | 60 | 4/4 | 4 |
| current | scip | 5 | 4/4 | 1 |
| current | scip | 30 | 4/4 | 4 |
| current | scip | 60 | 4/4 | 4 |
| current | greedy | 5 | 4/4 | 1 |
| current | greedy | 30 | 4/4 | 1 |
| current | greedy | 60 | 4/4 | 1 |
| reversed | cp_sat | 5 | 4/4 | 2 |
| reversed | cp_sat | 30 | 4/4 | 4 |
| reversed | cp_sat | 60 | 4/4 | 4 |
| reversed | scip | 5 | 4/4 | 0 |
| reversed | scip | 30 | 4/4 | 4 |
| reversed | scip | 60 | 4/4 | 4 |
| reversed | greedy | 5 | 4/4 | 1 |
| reversed | greedy | 30 | 4/4 | 1 |
| reversed | greedy | 60 | 4/4 | 1 |
| two | cp_sat | 5 | 4/4 | 4 |
| two | cp_sat | 30 | 4/4 | 4 |
| two | cp_sat | 60 | 4/4 | 4 |
| two | scip | 5 | 4/4 | 1 |
| two | scip | 30 | 4/4 | 4 |
| two | scip | 60 | 4/4 | 4 |
| two | greedy | 5 | 4/4 | 0 |
| two | greedy | 30 | 4/4 | 0 |
| two | greedy | 60 | 4/4 | 0 |

## Prototype timing checks

Separate eight-worker/canonicalization configuration. Service return includes local persistence; production objective/proofs remain on their original scale.

| Event | Execution | Solver | Valid | Service return (s) | Total through research audit (s) |
|---|---|---|---|---:|---:|
| heavy-mixed | completed | OPTIMAL | True | 62.48663319973275 | 62.89675629977137 |
| near-mixed | completed | OPTIMAL | True | 62.51048790011555 | 62.94069320010021 |
| full-mixed | completed | OPTIMAL | True | 62.59963360009715 | 63.07022560015321 |
| high-mixed | completed | OPTIMAL | True | 62.55208930000663 | 62.91872119996697 |

Full phase timings, costs, components and bounds are in `tables/run-records.csv`; unmatched costs remain unavailable.

## Interpretation limits

- Synthetic related cases, no repeated timing trials or population significance tests.
- Costs conditioned on both-valid pairs; inspect failures and coverage.
- Budget comparisons are fresh-run endpoints, not convergence traces.
- Prototype settings differ from controlled comparisons; human satisfaction not measured.
