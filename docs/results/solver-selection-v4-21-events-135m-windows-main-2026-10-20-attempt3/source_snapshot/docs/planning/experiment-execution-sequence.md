# Experiment execution sequence and evidence recording

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status (20 October 2026): **expanded solver protocol implemented; Windows pilot completed; main execution pending**. The [scope amendment](solver-benchmark-scope-amendment-2026-10-20.md) specifies 21 events. After its pilot projected 125.16 minutes, the user authorized a [135-minute solver runtime amendment](solver-benchmark-runtime-amendment-2026-10-20.md); weighting retains its own 120 minutes. The [implementation guide](../../research/experiments/solver_benchmark/README.md) gives the current commands. The amended weighting runner remains pending. The [hypotheses and decision audit](experiment-hypotheses-and-analysis.md) records both closed interviews. This document starts no main experiment.

## Why solver benchmarking can precede weight selection

| Study | Variable under investigation | Controls |
|---|---|---|
| [Solver selection benchmark](solver-selection-benchmark.md) | CP-SAT, deterministic constraint-aware greedy and SCIP MIP | Same matched event, hard rules, scoring definitions and current-ratio coefficients for each preference configuration |
| [Budget comparison](solver-selection-benchmark.md#confirmed-q11q13--budget-sensitivity-and-prototype-timing) | Search allowance: 5, 30 and 60 seconds | Same 12 matched larger cases, each method/configuration compared separately; fresh single-worker runs with canonicalization disabled |
| Prototype timing checks | Actual complete-result return behavior under the configured 60-second allowance | Four larger events in current/default order; actual prototype settings recorded, separate from controlled comparative results |
| [Rank-weighting experiment](rank-weighting-experiment.md) | Current-ratio, rank sum, rank reciprocal and ROC | CP-SAT, matched inputs and fixed primary scoring definitions; scoring sensitivity is a separately labelled batch |

The benchmark does not need a finalized operational weighting rule. Its current-ratio rule is an experimental control, not a claim that its ratios are correct for PJKIT. Holding coefficients identical within each solver comparison allows differences to be attributed to the compared implementations under the declared budget.

The weighting study characterizes trade-offs under assumed rankings and scoring definitions. Synthetic weighted costs alone cannot identify PJKIT's true numerical preferences or select a universally best formula. The user has deferred PJKIT-led human verification until after FYP completion and live deployment; it is future work, not a dissertation experiment or a prerequisite for completing these computational runs. Any project default remains an assumption-based engineering choice until appropriately validated. Each formula's own minimized objective is not a common score for ranking formulas against one another.

Both studies generate seating maps. A valid returned map must assign every eligible registration its complete entitlement and pass the placement audit; obtaining a map and proving optimality are separate outcomes. Timeouts without a map must remain in the evidence. Five seconds is the benchmark's base search cutoff, not a completion guarantee; the weighting study retains its own four-second search limit.

Execution order is a practical recommendation, not a mathematical prerequisite. Reliability comes from correctness, frozen assumptions, complete reporting and separating development decisions from main evidence.

## Recommended sequence

1. **Implement and check the approved amendment and shared infrastructure.** Existing adapters share parsing, legal bundles, scoring, validation and records. Extend inventory, scheduling, projection, deadlines and report labels to the 21-event specification. Preserve CP-SAT/MIP objective-equivalence and tiny-case gates and the greedy definition without exact-solver rescue. Pin packages and record backend versions. Do not run the unchanged 13-event command as evidence for the amended protocol.
2. **Freeze and certify inputs.** Preserve the original generator and all 13 benchmark requests, verifying their hashes against historical evidence. Add high-occupancy 62/31/24 tier counts (117 registrations / 179 seats) and near-capacity 73/37/29 (139 / 212), each with mixed/conflict/tied/accessibility patterns. The benchmark totals 21 events; weighting stays at its original 12. Spreadsheet-derived candidates and the separate 2026 demo are outside these batches. Save new input hashes and independently audited witnesses, never used as search hints. Retain unresolved cases rather than replacing them based on performance.
3. **Complete each study's separate development pilot.** Use declared development seeds rather than main outcomes for tuning. The solver pilot has 28 jobs: six mixed families × three methods at five seconds, Emperor-heavy mixed × three methods at 30/60 seconds, and four selected prototype checks. Its 10-minute nominal allowance has a 15-minute default/maximum ceiling inside the overall clock. Assess complete-map return, build/search/audit/process overhead, memory and fit for the entire workload. High/near-capacity longer-run behavior is measured in main work, not this pilot. Weighting follows its separate pilot protocol. Freeze amendments before main work and keep pilot evidence separate.
4. **Execute the solver studies first.** Begin with 84 matched cases across three methods: 252 primary five-second runs. Then run the fixed 12-case mixed-event subset at 30/60 seconds, adding 72 fresh runs. The events are high-occupancy mixed, near-capacity mixed, full-capacity mixed and Emperor-heavy mixed, crossed with three active configurations. Reuse their five-second records and preserve fixed controls and recorded shuffled order. Finally run four separate prototype checks on those events in current/default order. These 328 main jobs, preparation/pilot, overhead and reporting share the amended **135-minute ceiling**. Report contradictory and supporting evidence. The solver protocol defines timer boundaries and deadline handling.
5. **Execute the rank-weighting study second.** Keep CP-SAT fixed and follow the 12-event, 840-search protocol with its four-second search limits and separate 120-minute overall ceiling. Preserve the primary, sensitivity and limited seed-repeat batches and their priorities. Do not change the weighting protocol in response to benchmark outcomes without a recorded amendment.
6. **Interpret and report the computational findings.** Generate JSON-derived tables and then the confirmed five analytical figures plus 230-seat illustration, with a sensitivity table substitution if clearer. Address H1/RQ1 (solver comparison), H2 (weighting trade-offs), H3 (5→30 and 30→60 budget contrasts) and the prototype verification question separately. Keep validity/coverage, cost, runtime and proof distinct. Human satisfaction and operational preference verification are outside this dissertation experiment scope.

### Deferred post-project work

After FYP completion and live deployment, PJKIT-led human evaluation may assess operational appropriateness, usability and preference calibration. Preserve the separately described reviewer-role and fresh-case safeguards if this work proceeds. It is not an additional stage required to complete the dissertation's computational experiments.

If a resulting policy/default differs materially from the benchmark's reference weighting or scoring, a separately declared targeted solver comparison can test whether prior conclusions still hold. Do not silently replace the original objectives or results. Human evaluation and any targeted recheck are outside both approved execution allowances.

Both runner ceilings include preparation/pilot, overhead and reporting. Retain artifact provenance; do not move actual computation outside timing boundaries merely to claim it fits. The separate ceilings allow **135 + 120 = 255 minutes (4 h 15 min)** sequentially, without guaranteeing completion. Solver search allocation is 75 minutes plus four nominal prototype minutes and other processing; weighting search allocation stays 56 minutes. Require fresh pilot overhead estimates. Development and later dissertation writing/stakeholder work are outside these allowances. Do not run studies concurrently. Stop solver measured work by minute 130, reserving five minutes for reports; weighting retains its minute-90 launch cutoff and 120-minute ceiling.

## Primary execution environment

For the amended solver run, use the user's current **Windows 11** environment with the verified local Python environment and SCIP backend. The pilot must establish actual resource use and overhead; test success is not a completion guarantee. Record the actual environment in every evidence bundle. If the separate weighting study runs on a different machine, keep its timings separate.

For the timed batches:

- Use one solver worker and sequential jobs for the controlled comparisons, with the recorded shuffled order required by each protocol. The four separate prototype checks preserve the actual configuration (currently eight search workers, canonicalization enabled); label that difference and exclude them from comparative solver aggregates. These implementations use CPU solving; a Colab GPU is not a reason to change platforms.
- Keep the Windows machine plugged in and awake, with consistent power settings; avoid other heavy workloads. Record relevant settings and any interruptions.
- Pin Python/package versions, record solver backend versions, and record the hardware model, architecture and macOS version. Preserve the source revision plus hashes or a snapshot of any uncommitted experiment code.
- Use monotonic clocks and the declared outer watchdogs. Keep construction, search, validation, persistence and total elapsed time distinguishable. Fixed random seeds do not guarantee identical time-limited outcomes across hardware or software versions.

Colab remains an option for sharing notebooks, analyzing saved JSON, or conducting a separately labelled portability study. Managed resource availability and usage limits can vary, and runtime files are temporary unless persisted. Google documents these properties in the [Colab FAQ](https://research.google.com/colaboratory/faq.html), checked 12 October 2026. Google also notes that selecting an accelerator does not automatically make code use it.

If main experiments are moved to Colab, record that environment before execution, verify the actual solver backends, and keep all methods in a matched comparison on the same environment. Persist checkpoints to durable storage. Do not pool local and Colab wall-clock measurements into one algorithm ranking. For a portability comparison, retain separate environment-labelled results using the same frozen code, inputs and configurations.

## JSON evidence bundles

Use separate, unique result directories:

- Solver benchmark: `docs/results/solver-selection-benchmark-<run-date>/`.
- Weighting study: `docs/results/rank-weighting-initial-<run-date>/`.

Use a run identifier suffix when needed to avoid overwriting a directory. Preserve the original 11 October evidence. Store at least:

| Artifact | Required information |
|---|---|
| `manifest.json` | Study/protocol version, run ID, code revision and hashes, Python/packages/backend versions, hardware/OS, seeds, budgets, timing boundaries, complete planned run order, dataset/configuration identifiers/hashes, larger-case subset membership and hypothesis/analysis identifiers |
| `inputs/*.json` | Frozen layouts, registration profiles, eligibility/accessibility, hard policy, scoring configuration and event metadata; save witnesses and their audits separately and link their hashes |
| `runs/*.json` | One record per method/case/seed/budget, with batch kind (`primary`, `budget_sensitivity`, `prototype`, or weighting batch), worker count/canonicalization, solver and execution statuses, returned whole-registration seat bundles, placement audit, common component scores, objective coefficients/value, available bound/gap/proof information and phase timings. Prototype records additionally identify complete formatted-output return, external audit time and total through audit, rather than relying on the internal pre-format timing field |
| `pilot/` | Separate pilot inputs, records and any resulting protocol-amendment record; never count these as main observations |
| Trace records | Weighting-study incumbent/bound events as specified by its protocol; benchmark first-incumbent events only when comparable instrumentation is available, otherwise mark unavailable. The installed SCIP wrapper does not expose comparable Python callbacks, so 5/30/60 fresh-run endpoints are not a convergence trace |
| `summary.json` and generated report | Planned/attempted/completed/validated denominators, failures and missing coverage, matched-case analyses and derived tables/figures traceable to raw records |

Persist each completed run atomically, and retain the full manifest even when interrupted. Use explicit unavailable values with reasons for missing bounds, maps or timings; do not substitute zeros. Keep solver-returned status separate from deadline interruption, not-started and validation-pending states. Retain failed audits and diagnostics. Only independently validated complete maps enter valid-plan quality comparisons.

Use separate batch labels or manifest links for 252 primary runs, 72 longer-budget runs and four prototype records. Prototype checks use explicit benchmark requests and fresh isolated research SQLite stores, because the service saves successful solves; never publish or modify live records. Time a fresh local subprocess through parsed final JSON, including startup/serialization/local persistence, with external audit separate. Browser/network/remote-store latency is outside this boundary. Primary coverage has 84 cases per method and 21 per configuration; budget analyses use the same 12 mixed cases. Do not double-count reused records or pool prototype observations with single-worker comparisons. Retain nonmonotonic budget outcomes. Preserve 18 October development bundles unchanged; they do not validate the expanded workload.

Save the full map, not just a scalar objective: an Emperor registration's record must retain both assigned seat IDs. Record whether reported memory is per-run or cumulative process peak; a suite-wide high-water mark cannot be presented as independent per-method memory use. Back up the evidence bundle after execution. Generate summaries and figures from saved records so analysis can be repeated without rerunning timed searches.

No new benchmark measurements, selected operational weights or stakeholder outcomes are asserted here.
