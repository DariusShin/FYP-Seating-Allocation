# Study B: production solver comparison and figure plan

Status: **experiment setup implemented; native Windows 11 validation and measured execution pending**. Recorded 23 October 2026. The isolated implementation is on `codex/study-b-production-benchmark`; see the [Windows execution guide](../../research/experiments/production_benchmark/README.md). Development oracles and bridge checks are excluded from measured study denominators. This page reports no measured Study B outcomes and does not change the application's production default.

## Relationship to Study A

**Study A** is the completed attempt 3 controlled benchmark: CP-SAT, SCIP and the implemented custom greedy constructor, with one worker, no canonicalization and a five-second search allowance across 21 synthetic events and four preference settings. Its additional 30/60-second runs cover only four large mixed events and three active settings. The four older CP-SAT production-path checks remain a separate diagnostic batch. See the [expanded Study A package](../results/solver-selection-v4-attempt3-figures-2026-10-23/README.md).

**Study B** compares instrumented production allocation functions using CP-SAT and SCIP through the real local service, result formatter, validation and isolated SQLite adoption. It asks whether the advantage observed for SCIP in Study A survives production modeling, canonical selection, validation and result return. The CP-SAT arm reuses the maintained model builder; both arms share the added timing/canonical adoption contract inside the experimental worker. It also checks whether an initial map from either backend remains compatible with CP-SAT regeneration through that service path. The two studies answer different questions and must retain separate methods, denominators, tables and figure numbering. Old prototype checks are not Study B observations.

Keep Study A in the dissertation and technical paper as candidate screening and controlled budget-response evidence. It motivates the production comparison without predetermining its winner. The implemented greedy constructor can be excluded from the production shortlist for its observed reliability/quality trade-offs, but it did not lose every metric: it was faster in the both-valid primary comparisons and returned maps on two five-second cases where neither exact method returned one. This evidence does not eliminate every possible greedy algorithm.

## Agreed decision and acceptance rules

The project title, *Intelligent Automated Seating Allocation System for Large Scale Assemblies Using Configurable Constraint Optimization*, does not determine the solver brand. Compare implementations of the same feasible allocation set and the same preference objective. The current prototype uses CP-SAT; a production comparison favoring SCIP on validity, modeled preference quality and complete-result time can justify making SCIP the default for **initial allocation only**. CP-SAT regeneration and absence repair remain in scope as compatibility dependencies; this study does not establish a replacement absence-repair implementation.

Validated feasibility and proof of optimality must be reported separately. An unproved feasible map is not automatically incorrect, and a no-map timeout is not a proof of infeasibility. However, the agreed reproducibility requirement adds a stricter adoption gate: **incomplete canonical selection must not replace the seating map**. Preserve an existing map when available; otherwise report that no acceptable new map was returned. A preserved old map is not a successful fresh generation. The experimental function enforces this gate; the application's existing default function remains unchanged. If native search returns a completed canonical result after the shared allowance, record it separately as late completion and reject adoption. Final validation/formatting/persistence can still extend actual service return after timely canonical completion.

Canonical selection means both backends apply the same ordered tie-breaking procedure after the preference objective is fixed at its proven minimum. With identical effective inputs and a fully completed unique canonical procedure, backend identity, raw input order and repeated execution should produce the same physical registration-to-seat mapping. Preference optimality alone does not establish that property. The current post-optimal procedure depends on proving the weighted optimum first; it may therefore reject an otherwise feasible result when the shared allowance expires. Report this availability cost explicitly.

No staff response-time requirement has been established. The 60-second allowance is an engineering configuration being evaluated, not a validated business deadline or a promise that the full web request returns in 60 seconds.

## Configurations and clocks

| Item | Agreed comparison |
| --- | --- |
| Preference search | CP-SAT configured for up to eight workers; SCIP configured for up to eight threads only after native concurrency is verified on the intended build |
| Canonical stages | One worker/thread for both; identical participant ordering, seat ordering and tie-breaking objectives |
| Objective | Freeze the production scoring coefficients and normalization, including the production 40:30:20 current-order coefficients; audit the common objective independently |
| Inputs | Same policy, layout, participant semantics, accessibility and Emperor-pair rules; deterministic normalization before model construction |
| Primary allowance | One shared 60-second allocation-function allowance, including input preparation, model construction, weighted search and all canonical stages |
| Extended diagnostic | Fresh 180-second runs on two predefined workload-setting pairs; separate results, never substitutes for primary failures |
| Adoption | Independent validity audit plus completed shared canonical selection; record weighted-objective proof separately |

The current production example request sets `max_time_seconds: 60`, `num_search_workers: 8`, `canonicalize: true` and `require_optimal: false` in [production_request.json](../../services/seating/data/production_request.json). The function starts its deadline before preparation/model construction; final validation, response formatting and service overhead can extend elapsed return time beyond that allowance. Instrument both the internal deadline and actual complete-result return. The web process watchdog is a different clock.

SCIP configuration requires the integration's native threading API, such as OR-Tools `SetNumThreads`, and a build that supports the intended concurrent solve. Acceptance of a parameter string alone does not demonstrate eight-thread execution. Record solver/library versions, build support, thread-setting result and evidence of actual concurrency. If the intended configuration cannot be verified, stop at the pilot and amend the protocol explicitly; do not silently publish a single-thread run as an eight-thread comparison. A third full single-thread SCIP arm is outside the agreed two-hour run budget.

For an OPTIMAL label, retain termination reason, independently recomputed incumbent objective, best bound and absolute/relative gap. Verify the wrapper's status mapping and exact proof settings: a native gap-limit termination must not be presented as a zero-gap proof merely because an API maps it to OPTIMAL. Within the model's integer objective and solver tolerances, verify that the reported bound establishes the claimed optimum.

## Workloads and execution schedule

The following eight workload-setting pairs are fixed before observing production results:

| Workload | Preference setting |
| --- | --- |
| `typical-mixed` | `current` |
| `high-mixed` | `current` |
| `near-mixed` | `current` |
| `full-mixed` | `current` |
| `heavy-mixed` | `current` |
| `full-conflict` | `reversed` |
| `full-tied` | `disabled` |
| `full-accessible` | `two` |

Each backend receives three primary executions per workload: two fresh runs of the same raw input and a fresh run with participant/seat input order permuted while preserving effective semantics. Record the permutation and hashes. Alternate or deterministically interleave backend order and run jobs sequentially to avoid cross-job resource contention. Three executions are a limited repeatability/order check, not a reliable estimate of tail latency or a large independent sample.

| Batch | Calculation | Jobs | Nominal shared allowance |
| --- | --- | ---: | ---: |
| Primary initial allocation | 8 workload pairs × 2 backends × 3 executions × 60 s | 48 | 48 min |
| Extended diagnostic | `heavy-mixed/current` and `full-tied/disabled` × 2 backends × 2 fresh raw-input repetitions × 180 s | 8 | 24 min |
| CP-SAT regeneration links | 4 workload pairs × 2 initial backends × 60 s | 8 | 8 min |
| Total measured schedule | Separate batch labels retained | 64 | 80 min |

The regeneration subset is `typical-mixed/current`, `full-mixed/current`, `heavy-mixed/current` and `full-accessible/two`. For each origin backend, use its first scheduled canonical-complete primary result as the baseline and submit unchanged effective inputs/preferences to CP-SAT `REGENERATE_DRAFT`. Audit validity, returned physical-map equality, proof, canonical completion and return time. If no acceptable baseline exists, report an unmet prerequisite rather than inventing a baseline or silently dropping the case. This checks unchanged-input regeneration interoperability. Changed soft constraints and absence repair require their own tests before any broader migration claim.

Execute the two predefined 180-second workload pairs regardless of primary outcomes. They distinguish a short-allowance limitation from unresolved implementation/modeling differences; they are not selected after finding a preferred solver's failures. The disabled-preferences workload is a feasibility/canonical tie stress case, not an allocation-quality comparison.

The overall runner cap is two hours: 80 minutes nominal measured allowances, 5 minutes correctness preflight, 15 minutes pilot, 15 minutes measured-batch overhead and 5 minutes reporting. Implementation and dissertation writing are outside this execution cap. A possible pilot uses both backends on the disabled tie case at 180 seconds, both on the heavy current case at 60 seconds and two 60-second regeneration links: 10 minutes nominal plus 5 minutes overhead. Pilot results remain separately labeled. Project the actual runtime before the measured batch; if it cannot fit, stop and revise the schedule explicitly. Do not shorten selected runs or omit difficult cases to claim completion within the cap.

## Required measurements

Save a manifest, immutable request/policy hashes, normalized semantic-input hash, backend/version/build, hardware, thread configuration, seed, run order, batch and repetition/permutation identity. Save placements, normalized physical-map hash and independently scored objective/components for every returned candidate. A physical-map hash uses sorted registration IDs and physical seat IDs; do not hash timestamped response JSON or internal bundle-variable IDs.

Record these outcomes independently:

- Execution completed, failed or not started; deadline/termination reason and error details.
- Candidate returned; independent hard-rule audit; preference incumbent, bound, gap and proof status.
- Canonicalization requested, stages attempted/completed and complete unique selection established.
- Candidate adopted, rejected or prior map preserved; whether an acceptable new map reached the caller.
- Time for normalization/preparation, model build, weighted-objective stage, canonical stages, extraction, audit/formatting and complete service return, plus residual elapsed overhead.
- For regeneration, baseline provenance and prerequisite availability, output validity and exact physical-map equality.

For the requested "time to an optimal seating plan," separate **time when the solver reports proof of the weighted optimum**, **time when canonical selection completes**, and **time when the validated complete response returns**. Proof-stage elapsed time is not the timestamp of first encountering an optimal incumbent. Record first-incumbent or anytime traces only if comparable, tested instrumentation exists for both backends. The saved Study A records cannot supply these timestamps retrospectively. The implemented service clock covers real local dispatch, SQLite adoption and JSON serialization, but excludes interpreter imports and baseline hydration; those have separate worker/preparation clocks. It does not include HTTP, browser or network latency.

The 60-second allowance is shared across stages; do not grant a fresh 60 seconds to each stage. Report actual complete-result time even when it exceeds the internal allowance. If phase clocks overlap, do not stack them as additive durations; instrument disjoint boundaries or show overlaps explicitly. Record memory/CPU only if the collection method is comparable across backend processes and native worker threads.

## Study B figure package, after execution

Use B numbering and a distinct result directory, for example `docs/results/solver-selection-production-<run-date>/`. Do not generate measured-looking blank charts, zero-filled results or hypothetical winner maps now.

| Figure | Display and purpose | Required records |
| --- | --- | --- |
| B1. Production outcomes | Paired workload-by-backend matrix for all three primary executions; distinguish valid candidate, weighted proof, canonical completion and acceptable new return. Show numerator/denominator and missing execution separately. Establish operational availability before discussing quality. | Per-run audit, proof, canonical/adoption and coverage fields |
| B2. Complete-result time and phases | Paired points for all repetitions, with a disjoint phase breakdown for predefined representative cases. Annotate observed totals and the internal allowance. Explain whether search, canonical selection or integration dominates elapsed time. | Stage timestamps, residual overhead and complete-service clock |
| B3. Reproducibility and regeneration | Physical-map equality table/matrix for identical-input repeats, semantic permutations, cross-backend completed maps and CP-SAT regeneration links. Show unmet prerequisites separately from unequal outputs. | Semantic hash, canonical status, physical-map hash and regeneration baseline |
| B4. Primary versus extended diagnostic | Matched 60/180-second outcome and phase panels for the two predefined pairs. Keep all fresh repetitions visible; distinguish budget limitation from unresolved defects. | Separate primary/diagnostic batch records and all failure statuses |
| B5. 230-seat physical illustration | Same-scale CP-SAT/SCIP canonical maps for `heavy-mixed/current`, with validated penalty, proof-stage time, canonical-completion time and actual complete return. Use the first scheduled acceptable primary map for each backend; show no-map explicitly if absent. If only a diagnostic succeeds, label it 180 seconds in a separate panel. | Saved independently audited placements and stage times |

A small paired objective table should accompany B1. With a shared objective and completed unique canonical procedure, accepted results should agree on both cost and physical mapping. A disagreement triggers a modeling, scoring, normalization or canonicalization investigation; it is not automatically evidence that one proven optimum is better. Candidate costs from incomplete canonical runs can be reported separately, with their proof and adoption status.

Optional appendix figures can show raw preference components, resource use or comparable incumbent/bound traces if measured correctly. Avoid pooling different preference weights into one average penalty, treating disabled preferences as meaningful quality, presenting three repeats as population confidence, or drawing a continuous convergence curve through independent budget endpoints.

## Implementation gates before execution

These gates are implemented in the isolated runner; their success on the intended Windows installation must still be recorded. A development pass on another OS does not certify the Windows build.

1. Establish encoding equivalence with independent hard-rule and objective checks, including accessibility, blocked/unique seats, registration entitlements and approved Emperor pairs.
2. Implement the common normalized input/output contract, full canonical procedure, proof reporting and incomplete-canonical adoption gate for both initial backends.
3. Verify the intended SCIP native concurrent build and comparable configured resources; pin versions and proof/gap settings.
4. Verify the disjoint clocks, saved artifacts, physical-map hashing and CP-SAT regeneration bridge; keep failure/prerequisite records.
5. Run the separately labeled correctness pilot and demonstrate the capped schedule can fit before measured execution.

The final solver recommendation remains conditional on measured production evidence and implementation correctness. The isolated research service bridge is implemented; the application default has not changed and no measured Study B run has been performed. `plan` freezes inputs/schedule without optimization; `check` and `pilot` remain separate from measured denominators; `run` performs its own preflight/pilot and enforces the fixed two-hour cap. No hypothetical result figures are created before measured observations exist.
