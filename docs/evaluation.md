# v2 evaluation

Run `PYTHONPATH=src .venv/bin/python -m pytest -q` for historical reproduction plus production requirement tests. Production tests cover the full 16 effective ordered/enabled preference profiles, strict types, status/replacement validation, shared rows, exact ID multiset, accessibility/packing conflict, objective/representation tampering, canonical input order, independent tiny optimum enumeration, FEASIBLE handling, manual rescoring, published repair and transactional lifecycle/privacy.

Use `seat_solver.production.evaluation --suite core|profiles|random|saturation --budget SECONDS --output FILE`. Random uses `--runs 100` by default. Every record includes seed, input hash, layout version, registration count, physical demand, status, independent validity, component penalties, stage proof, movement and timing where applicable. Stats include median, IQR, p95, extremes and status counts/rates over all runs, including intended failures. Recorded RSS is measured process peak, not mislabelled current RSS. Suite runs use canonicalize=false to measure optimization separately; canonical repeatability is tested with completion enabled.

The core suite has 20 deterministic scenarios: tiny assignments, realistic synthetic loads, saturation, pair/mixed-boundary/accessibility cases, absence and replacement repair, empty event, over-capacity, structural infeasibility and malformed input. The default synthetic example is 96 units/152 seats, explicitly distinct from the report benchmark. Historical and current venue capacities must never be pooled without version labels.

The profile suite evaluates all 16 effective preference orders/enabled sets; six full permutations, six ordered pairs, three individual preferences, all-off. Disabled full-order permutations that produce the same active ordering are not distinct objectives. A geometric change is not required for every preference reorder.

The random suite generates 100 seeded approximately fixed-registration-load instances, varying Emperor proportion, contribution, category, activity and accessibility. Genuine accessibility/packing conflicts are expected in some cases and must be reported as infeasible, not hidden. Saturation varies physical demand and pair/unit composition rather than using registration count alone.

For difficult cases, use multiple budgets/workers and inspect proof stage, bounds/gaps and normalized component trade-offs. Do not compare weighted totals across different profiles as if the objective were unchanged. Restricted repair proof is scoped; compare its movement and ordinary-quality trade-off separately against explicit full regeneration for that scenario. No global-movement claim follows from the smallest feasible scope.

Generated JSON reports in `output/evaluation/` document local runs. Timings are machine-specific observations, not guaranteed service latency. Additional host deployment acceptance must measure Lambda cold/warm invocation latency, serialization/storage/auth integration, and target-environment performance. This repository does not fabricate those measurements.

## Recorded local v2 run

| Suite | Cases | OPTIMAL | Expected/observed failures | Median seconds | p95 seconds |
|---|---:|---:|---|---:|---:|
| Core | 20 | 17 | 1 capacity, 1 infeasible, 1 invalid input | 0.044 | 0.407 |
| Profiles | 16 | 16 | 0 | 0.054 | 0.059 |
| Random | 100 | 98 | 2 infeasible | 0.195 | 0.259 |
| Saturation | 21 | 21 | 0 | 0.545 | 0.977 |

All successful outputs passed independent validation. Raw environment details and individual cases are preserved in `output/evaluation/*-v2.json`. The sample sizes and solve budgets are recorded there; these figures exclude canonicalization and cloud overhead.
