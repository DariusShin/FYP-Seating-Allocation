# Development pilot diagnostics

These runs test the harness and workload projection. They are excluded from H1/RQ1/H3 and main-study figures.

| Event | Method | Batch | Allowance (s) | Execution | Solver | Valid | Worker total (s) |
|---|---|---|---:|---|---|---|---:|
| small-mixed | cp_sat | pilot | 5 | completed | OPTIMAL | True | 1.81792920792941 |
| small-mixed | scip | pilot | 5 | completed | OPTIMAL | True | 2.9213868329534307 |
| small-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 0.8496217080391943 |
| typical-mixed | cp_sat | pilot | 5 | completed | OPTIMAL | True | 5.955424833926372 |
| typical-mixed | scip | pilot | 5 | completed | OPTIMAL | True | 2.250547165982425 |
| typical-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 0.931095291976817 |
| full-mixed | cp_sat | pilot | 5 | completed | FEASIBLE | True | 7.318622416001745 |
| full-mixed | scip | pilot | 5 | completed | FEASIBLE | True | 6.285933415987529 |
| full-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 1.3273972499882802 |
| heavy-mixed | cp_sat | pilot | 5 | completed | FEASIBLE | True | 7.313175625051372 |
| heavy-mixed | scip | pilot | 5 | completed | OPTIMAL | True | 4.160505583975464 |
| heavy-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 1.1339760420378298 |
| heavy-mixed | cp_sat | pilot | 30 | completed | FEASIBLE | True | 32.31639366596937 |
| heavy-mixed | scip | pilot | 30 | completed | OPTIMAL | True | 4.145061416900717 |
| heavy-mixed | greedy | pilot | 30 | completed | CONSTRUCTION_FAILED | False | 1.1363409579498693 |
| heavy-mixed | cp_sat | pilot | 60 | completed | FEASIBLE | True | 62.330786834005266 |
| heavy-mixed | scip | pilot | 60 | completed | OPTIMAL | True | 4.150944916997105 |
| heavy-mixed | greedy | pilot | 60 | completed | CONSTRUCTION_FAILED | False | 1.114795499946922 |
| heavy-mixed | cp_sat | prototype | 60 | completed | OPTIMAL | True | 61.861586624989286 |

Projected complete main-run workload: **88.08 minutes**. Fits the 90-minute ceiling: **True**.

The projection uses full allocated search time and conservative measured overhead. It is not an observed main-study duration.

Detailed phase timings, memory, scores and bounds: `tables/run-records.csv`. Raw records: `runs/*.json`. Scope and missing-value definitions follow the harness README.
