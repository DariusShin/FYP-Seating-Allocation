# Synthetic preference sensitivity: measured results

Generated from saved run records. These are diagnostic results, not stakeholder validation.

Instances: 18. Runs: 306. Status counts: {'OPTIMAL': 178, 'FEASIBLE': 119, 'UNKNOWN': 9}.
Returned solutions passing placement validation: 297.
Independently checked option-cost vectors: 248,200.
Total experiment elapsed time: 343.05 seconds, including generation, checks and file output.
OR-Tools 9.15.6755; arm64; one worker; 1.5 seconds per search; fixed seeds.
Full Python/platform and source hashes are recorded in manifest.json.

## Search outcomes

| Instance size | Runs | Optimal | Feasible, unproved | Unknown | Infeasible | Median search seconds |
|---|---:|---:|---:|---:|---:|---:|
| small | 102 | 100 | 2 | 0 | 0 | 0.284 |
| typical | 102 | 59 | 42 | 1 | 0 | 0.872 |
| full | 102 | 19 | 75 | 8 | 0 | 1.500 |

UNKNOWN means no incumbent was returned within the budget; it is not proof of infeasibility. The configurations on an instance share hard constraints, so another configuration's validated plan can demonstrate feasibility. Search timing excludes shared model construction and external validation. These are not repeated runtime trials.

## Sensitivity with a proved baseline

A strict comparison below requires the current-weight/base-matrix baseline to be OPTIMAL. An alternative feasible plan with a strictly better alternative-objective score proves that this baseline is no longer optimal under that objective. This avoids mistaking poor baseline search quality for a weight effect. The alternative need not itself be proved optimal for that strict conclusion.

| Alternative matrix / weights | Eligible paired cases | Baseline strictly worse | Baseline also proved optimal | Unresolved |
|---|---:|---:|---:|---:|
| base / equal | 10 | 8 | 2 | 0 |
| base / rank_sum | 10 | 6 | 3 | 1 |
| base / rank_reciprocal | 10 | 4 | 5 | 1 |
| base / roc | 9 | 7 | 2 | 0 |
| base / flatter | 10 | 4 | 5 | 1 |
| base / steeper | 10 | 6 | 4 | 0 |
| base / contribution_only | 9 | 5 | 4 | 0 |
| base / activity_only | 10 | 10 | 0 | 0 |
| base / category_only | 10 | 8 | 1 | 1 |
| squared / current | 10 | 7 | 3 | 0 |
| squared / equal | 10 | 9 | 1 | 0 |
| squared / roc | 10 | 10 | 0 | 0 |
| ordinal / current | 10 | 10 | 0 | 0 |
| ordinal / equal | 10 | 10 | 0 | 0 |
| ordinal / roc | 10 | 10 | 0 | 0 |
| zero / current | 10 | 10 | 0 | 0 |

## Worked example

Instance `small-mixed-20261011`: 24 registrations, 32 physical seats. The table uses the same original component scales for every plan. Lower is better in each column. These are aggregate normalized penalty points, not percentages of satisfaction.

| Weights | Proof status | Contribution cost | Activity cost | Category cost |
|---|---|---:|---:|---:|
| current | OPTIMAL | 407 | 617 | 492 |
| equal | OPTIMAL | 435 | 610 | 454 |
| rank_sum | OPTIMAL | 407 | 596 | 530 |
| rank_reciprocal | OPTIMAL | 407 | 617 | 492 |
| roc | OPTIMAL | 388 | 635 | 530 |
| flatter | OPTIMAL | 429 | 617 | 454 |
| steeper | OPTIMAL | 407 | 596 | 530 |

A solution optimal for one weighting need not be optimal for another. The current and ROC rows illustrate an explicit trade-off without comparing incompatible weighted totals.

## Limits of these results

- No stakeholder choices, real registration distributions, or satisfaction labels were used. No best PJKIT weights are inferred.
- Validity applies to returned plans; missing incumbents are counted separately. Tests omit requested accessibility and absence repair.
- Two data seeds and one search seed provide preliminary coverage, not statistical generalization.
- Matrix experiments alter both within-category gaps and relative penalty strength across categories.
- Tied optima can give different seat maps. The sensitivity table compares objective values with proof conditions, not seat-map identity.
- Default scoring weights are reduced from 40/30/20 to the equivalent 4/3/2. All-entry category doubling passed exact normalization checks.
- The study did not evaluate competing allocation algorithms, time to first solution, memory use, or operational review time.
