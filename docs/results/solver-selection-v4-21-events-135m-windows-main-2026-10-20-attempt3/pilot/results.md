# Development pilot diagnostics

These runs test the harness and workload projection. They are excluded from H1/RQ1/H3 and main-study figures.

| Event | Method | Batch | Allowance (s) | Execution | Solver | Valid | Worker total (s) |
|---|---|---|---:|---|---|---|---:|
| small-mixed | cp_sat | pilot | 5 | completed | OPTIMAL | True | 3.920723299961537 |
| small-mixed | scip | pilot | 5 | completed | FEASIBLE | True | 6.153933700174093 |
| small-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 1.488203499931842 |
| typical-mixed | cp_sat | pilot | 5 | completed | FEASIBLE | True | 10.25869800010696 |
| typical-mixed | scip | pilot | 5 | completed | OPTIMAL | True | 4.8160196002572775 |
| typical-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 1.7751635001040995 |
| high-mixed | cp_sat | pilot | 5 | completed | UNKNOWN | False | 11.552445199806243 |
| high-mixed | scip | pilot | 5 | completed | UNKNOWN | False | 6.8961786003783345 |
| high-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 2.1475979001261294 |
| near-mixed | cp_sat | pilot | 5 | completed | UNKNOWN | False | 12.067653000354767 |
| near-mixed | scip | pilot | 5 | completed | UNKNOWN | False | 6.7619373998604715 |
| near-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 2.2660297001712024 |
| full-mixed | cp_sat | pilot | 5 | completed | FEASIBLE | True | 13.484047600068152 |
| full-mixed | scip | pilot | 5 | completed | UNKNOWN | False | 7.172025199979544 |
| full-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 3.1461940999142826 |
| heavy-mixed | cp_sat | pilot | 5 | completed | FEASIBLE | True | 13.654207000043243 |
| heavy-mixed | scip | pilot | 5 | completed | UNKNOWN | False | 7.095026399940252 |
| heavy-mixed | greedy | pilot | 5 | completed | CONSTRUCTION_FAILED | False | 2.39710390008986 |
| heavy-mixed | cp_sat | pilot | 30 | completed | FEASIBLE | True | 38.3497178000398 |
| heavy-mixed | scip | pilot | 30 | completed | OPTIMAL | True | 9.044139300007373 |
| heavy-mixed | greedy | pilot | 30 | completed | CONSTRUCTION_FAILED | False | 2.4667857997119427 |
| heavy-mixed | cp_sat | pilot | 60 | completed | FEASIBLE | True | 68.45894499961287 |
| heavy-mixed | scip | pilot | 60 | completed | OPTIMAL | True | 9.055702099576592 |
| heavy-mixed | greedy | pilot | 60 | completed | CONSTRUCTION_FAILED | False | 2.4229103000834584 |
| high-mixed | cp_sat | prototype | 60 | completed | OPTIMAL | True | 64.16395680001006 |
| near-mixed | cp_sat | prototype | 60 | completed | OPTIMAL | True | 64.41864830022678 |
| full-mixed | cp_sat | prototype | 60 | completed | OPTIMAL | True | 64.79437209991738 |
| heavy-mixed | cp_sat | prototype | 60 | completed | OPTIMAL | True | 64.2954076002352 |

Projected complete main-run workload: **127.09 minutes**. Fits the 135-minute ceiling: **True**.

The projection uses full allocated search time and conservative measured overhead. It is not an observed main-study duration.

Detailed phase timings, memory, scores and bounds: `tables/run-records.csv`. Raw records: `runs/*.json`. Scope and missing-value definitions follow the harness README.
