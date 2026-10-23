# Connecting Study A attempt 3 with Study B attempt 3

*23 October 2026. Read alongside the [Study A results and discussion](solver-selection-v4-attempt3-results-and-discussion.md) and the [Study B attempt 3 interpretation](study-b-windows-2026-10-23-attempt3/interpretation.md). This document explains why their solver rankings differ and what follows for the initial-generation service.*

## The two questions

**Study A** compared CP-SAT, SCIP and a greedy constructor across a broad synthetic event set using controlled one-worker solver/search allowances. It asked which methods could produce legal maps and good preference scores at several search budgets. **Study B** narrowed the choice to CP-SAT and SCIP in the local production initial-allocation function, with eight workers/native concurrent solvers, a shared function allowance, independent candidate validation and the complete local service response recorded. Study B attempt 3 is a fresh completed run; stopped Study B attempts are not included. Its [manifest](study-b-windows-2026-10-23-attempt3/manifest.json) and [audit](study-b-windows-2026-10-23-attempt3/checks.json) provide provenance.

| Design feature | Study A attempt 3 | Study B attempt 3 |
| --- | --- | --- |
| Main comparison | CP-SAT, SCIP, greedy | CP-SAT, SCIP |
| Controlled cohort | 21 events × 4 settings at 5 s; four large mixed events × 3 active settings at 30/60 s | Eight selected event/setting pairs at 5/30/60 s |
| Parallel setting | One worker in 324 controlled trials | Eight CP-SAT workers and eight launched SCIP native concurrent solvers |
| Clock | Solver/search allowance; reported allocation total is a separate measure | Shared allocation-function allowance; complete local service return measured separately |
| Repetitions | One execution per controlled case/backend/allowance | Two original-order repeats and one semantic input permutation per case/backend/allowance |
| Preference objective | Compact Study A coefficients (for example, current 4:3:2) | Production-mapped integer coefficients; absolute penalty scale differs |
| Decision scope | Method comparison and motivation for production testing | Initial-generation solver choice at the current 60-second engineering setting |

Study A also recorded four older eight-worker CP-SAT production-path checks with canonicalization requested. Those four checks are separate from its 324 controlled trials and from Study B's paired 48-job primary cohort. Study B's canonical selection is off under the agreed contract; exact physical-map repeatability is assigned to application state/cache behavior and was not tested here.

## What changed in the observed ranking

| Evidence | Study A controlled result | Study B production-function result |
| --- | --- | --- |
| Short endpoint | At a **5-second search allowance**, active-preference valid maps were CP-SAT **50/63**, SCIP **26/63**, greedy **13/63**. | At a **5-second shared function allowance**, neither exact backend had an adopted map: **0/24 each**. Normalization and model building often consumed the allowance before weighted search. |
| Longer-endpoint coverage | On the predefined 12 large mixed active cases, both exact backends returned **12/12 valid maps** at 30 and 60 seconds. | At 60 seconds, both returned **24/24 valid maps**. At the 30-second diagnostic endpoint, CP-SAT returned **24/24** and SCIP **17/24** within the strict boundary; SCIP's other seven valid, proven candidates were late. |
| Penalty and proof | At 60 seconds on those 12 cases, SCIP proved **12/12** optima; CP-SAT proved **0/12**. CP-SAT's penalty was higher in 11 cases and equal in one. | At 60 seconds, both proved **24/24** optima. On the 21 matched active-preference repetitions, their weighted penalties were equal in every pair. |
| Observed return time | At the 60-second search setting, SCIP's allocation total was shorter in all 12 matched large-case comparisons; medians were about **10.76 s SCIP** versus **65.64 s CP-SAT**. | At the 60-second function setting, CP-SAT's complete local service response was shorter in all 24 paired executions; means were **9.990 s CP-SAT** versus **28.645 s SCIP**. |

The five-second figures cannot be pooled or treated as contradictory because the clocks differ. Study A allowed search after construction; Study B starts its allowance at the function boundary and rejects a candidate whose weighted stage returns late. Similarly, the opposite longer-endpoint time rankings describe **different configurations and measured quantities**. Eight-worker parallelism is a plausible contributor, but the data do not isolate it: objective mapping, model encodings, preprocessing, validation/service work, selected cases and repeated execution also differ. The planned worker/thread sensitivity sweep is the appropriate test of parallelism's separate effect.

### The 230-seat `heavy-mixed/current` example

Study A's one-worker 60-second run returned CP-SAT `FEASIBLE` at penalty **21,679** after **66.729 s** of allocation total; SCIP returned `OPTIMAL` at **20,515** after **8.390 s**. Study B's three eight-worker 60-second runs per backend returned **proven optima on both sides**, each with the production-mapped penalty **205,150**. Their mean complete local service returns were **10.375 s CP-SAT** and **28.566 s SCIP**. The Study B penalty is on a different integer scale; 205,150 should not be read as ten times worse seating. This shared example shows why the initial-generation decision changes under the measured production contract. It does not prove which single design change caused the reversal.

## Decision and boundaries

The agreed selection hierarchy is 60-second valid-map coverage, then penalty on matched valid cases, proof coverage, and complete local service-return time, with zero invalid adopted maps required. In Study B attempt 3, the first three comparisons tie and both backends pass the invalid-map gate; CP-SAT returns sooner in every primary matched execution. **Retain CP-SAT for initial generation under the tested configuration.** The data do not justify switching the production default to SCIP merely because Study A's one-worker long-budget subset favored it. Study A remains valid evidence about its own controlled setup and explains why the follow-up was necessary.

This choice is bounded by eight selected known-feasible synthetic pairs, three executions per pair, one Windows environment, and the current 60-second engineering setting. It is not a staff response-time promise or proof of future coverage. The result cache, preference-update regeneration and absence repair were outside Study B. A worker/thread sensitivity sweep can test whether a different parallel setting changes the choice before broader deployment claims are made. Greedy was not rerun in Study B, so its Study A findings are not silently transferred into a new matched comparison.

The [Study A chapter](solver-selection-v4-attempt3-results-and-discussion.md) was written before Study B ran. Its statements that Study B is unexecuted, or that canonicalization is a future adoption gate, describe the historical plan and are **superseded for this initial-generation selection** by the completed [Study B attempt 3 protocol](../planning/solver-selection-production-attempt3.md) and [results](study-b-windows-2026-10-23-attempt3/interpretation.md). Its recorded Study A observations and figures remain the source for Study A claims above.
