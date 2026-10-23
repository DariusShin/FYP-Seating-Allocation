# Study B attempt 3: initial allocation results

Status: **completed**. Mode: **run**. Development only: **False**. Audits passed: **True**.

[Manifest](manifest.json) · [Checks](checks.json) · [Run records](tables/run-records.csv) · [Coverage](tables/coverage.csv) · [Matched penalties](tables/paired-objectives.csv) · [Phase timing](tables/phase-timing.csv)

## Coverage

| Batch | Allowance | Workers | Backend | Valid maps | Proven | Scheduled |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| diagnostic_30 | 30 s | 8 | cp_sat | 24 | 24 | 24 |
| diagnostic_30 | 30 s | 8 | scip | 17 | 17 | 24 |
| diagnostic_5 | 5 s | 8 | cp_sat | 0 | 0 | 24 |
| diagnostic_5 | 5 s | 8 | scip | 0 | 0 | 24 |
| primary | 60 s | 8 | cp_sat | 24 | 24 | 24 |
| primary | 60 s | 8 | scip | 24 | 24 | 24 |

At 60 seconds, valid-map coverage is the first decision measure. A valid unproved map is a `FEASIBLE` return. Compare production penalty only on matched valid cases, then proof coverage and complete local service-return time. Disabled preferences are excluded from penalty differences. Require zero invalid adopted maps. The 5- and 30-second jobs are fresh diagnostic endpoints and are not pooled with 60 seconds. The separate worker/thread sweep has its own denominator.

## Interpretation

60-second valid-map coverage ties; compare matched penalty, proof coverage and complete service time. Report unresolved trade-offs without forcing a default

The allowance covers normalization, model building and weighted search; independent validation, formatting, SQLite persistence and JSON encoding contribute to complete service return. A stage-return timestamp is not the first incumbent-discovery time. No staff response-time requirement has been established. Three executions per case are descriptive and do not estimate population reliability. Native SCIP launch counts establish concurrent solver instances, not sustained CPU utilization. This benchmark does not exercise a result cache, preference-update regeneration or absence repair.

## Figures

![attempt3-coverage-by-allowance](figures/attempt3-coverage-by-allowance.png)

[PDF](figures/attempt3-coverage-by-allowance.pdf) | [SVG](figures/attempt3-coverage-by-allowance.svg)

![attempt3-complete-service-time](figures/attempt3-complete-service-time.png)

[PDF](figures/attempt3-complete-service-time.pdf) | [SVG](figures/attempt3-complete-service-time.svg)

![attempt3-matched-penalties](figures/attempt3-matched-penalties.png)

[PDF](figures/attempt3-matched-penalties.pdf) | [SVG](figures/attempt3-matched-penalties.svg)
