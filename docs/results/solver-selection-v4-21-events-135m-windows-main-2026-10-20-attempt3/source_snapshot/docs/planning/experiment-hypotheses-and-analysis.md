# Experiment hypotheses, analysis and confirmed decisions

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status (20 October 2026): **expanded scope confirmed through the occupancy-session Q6 A; executable amendment and fresh validation pending; main execution pending**. The [20 October amendment](solver-benchmark-scope-amendment-2026-10-20.md) sets 21 events, a revised four-event longer-budget/prototype subset, a 28-job pilot and a 120-minute solver ceiling. Current scripts and historical development evidence still describe the 18 October 13-event / 90-minute version. Original H1/RQ1/H2/H3 and the figure package remain; no new measurements or operational weights are recorded.

## Overall dissertation claim

> The implemented approach can express PJKIT's hard constraints and configurable preferences and generate complete, independently validated seating allocations for the evaluated synthetic events within declared computational limits.

The solver benchmark evaluates the already-selected CP-SAT implementation; it does not imply that this unexecuted benchmark originally determined its selection. Separate solver suitability, weighting trade-offs and the benefit of additional computation. A result contradicting an expectation is a reportable finding, not a reason to replace difficult cases or change the hypothesis after execution.

## Questions, hypotheses and operational analysis

| Study | Hypothesis or research question | Analysis and permitted conclusion |
|---|---|---|
| Solver comparison | **H1:** Under the common five-second search allowance, CP-SAT produces lower modeled preference penalties than the constraint-aware greedy baseline on matched cases where both return valid plans. **RQ1:** How does CP-SAT compare with SCIP in valid-plan coverage, cost, runtime and optimality evidence? | For each of the three preference-active configurations separately, calculate the median of `(C_CP-SAT - C_greedy) / N` over both-valid pairs. A negative median supports that configuration's H1 prediction; zero/positive values do not. Show individual differences, win/tie/loss counts and pair counts. Report the same descriptive comparisons against SCIP without presupposing superiority. Keep complete-plan coverage beside cost results; successful-case quality alone cannot establish overall suitability. |
| Rank-weighting comparison | **H2:** On cases with conflicting preferences, alternative rank-weighting rules produce different trade-offs between contribution, activity and category penalties. | Compare component vectors on the same fixed reference scale with CP-SAT and inputs fixed. Examine the predeclared contribution/activity-conflict cases, then describe other patterns separately. Identify which distinct rules change at least one enabled component and the magnitude/direction of each change. Equivalent objectives are controls, not independent evidence of formula effects. Identical outcomes are legitimate findings: compulsory rules, aligned preferences or incomplete search may limit observed differences. Do not compare formulas by their own differently weighted totals. |
| Search-budget comparison | **H3:** Additional search time produces additional complete valid plans or lower modeled preference costs on at least some predeclared larger cases. Examine **5→30 seconds** and **30→60 seconds** separately. | For each method, report valid-plan counts and paired cost changes for each contrast and preference configuration. Distinguish newly obtained maps, retained/lost valid outcomes and quality changes among both-valid pairs. Report proof/bound changes separately; better proof alone does not establish better seating. No observed benefit is evidence against a claimed benefit on these cases, not evidence that longer search can never help. |
| Prototype timing check | **Verification question:** What complete-result return time and allocation outcome does the prototype achieve with its configured 60-second allowance? | Run the four predeclared larger events under the current/default preference order and actual prototype solver configuration, with isolated research stores. Measure fresh local service invocation through parsed final output, including startup/serialization and local persistence; record the external audit separately and total through audit. Report complete-map outcomes and phase/total timings. Do not pool these runs with the controlled single-worker solver comparisons or claim live UI latency. |

H1 is three configuration-specific predictions, not a pooled algorithm winner score. Each active configuration has 21 events and at most 21 both-valid pairs per comparator. If no both-valid pairs exist, its cost comparison is not estimable; preserve failures and the denominator. H3 concerns the revised four mixed-profile events only; conflict, tied and accessibility cases have primary five-second comparisons. Its coverage and quality outcomes are separate evidence. These are bounded descriptive synthetic studies, not population-level hypothesis tests; no p-values or runtime-variance claims are justified by one run per solver/case/budget. Added occupancy families also vary participant count and profile composition, so performance differences do not isolate a causal occupancy effect. Spreadsheet-derived candidate activity distributions are outside this benchmark.

Correctness is a prerequisite: every accepted output must assign each eligible registration its complete entitlement and pass every hard-rule check. Tiny independently solved equivalence cases and deliberately infeasible cases belong in the separate correctness suite. Correctness checks are not a comparative speed ranking. An INFEASIBLE claim for a witnessed feasible case is a discrepancy to investigate.

Weighting results describe observable behavior at the declared four-second budget. Keep optimum proofs, bounds, the 1/4-second checkpoints and limited additional-seed results visible; differences between time-limited incumbents alone do not prove differences between the true optimal allocations. The study does not discover PJKIT's true numerical preferences, validate attendee satisfaction or require a universally winning formula. Human verification is deferred until after FYP completion and live deployment.

## Confirmed experiment package

Use the [solver protocol](solver-selection-benchmark.md) for adapter definitions, controls and deadlines, the [weighting protocol](rank-weighting-experiment.md) for weighting batches, and the [execution guide](experiment-execution-sequence.md) for sequence and JSON provenance.

| Batch | Frozen coverage | Runs | Allocated solving time |
|---|---|---:|---:|
| Primary solver benchmark | 21 events × four configurations × three methods; five-second search allowance | 252 | 1,260 s = **21 min** |
| Longer-budget comparison | Four larger events × three preference-active configurations × three methods × two additional budgets (30/60 s) | 72 | 3,240 s = **54 min** |
| Prototype timing checks | Four larger events × current/default preference order; configured 60-second prototype allowance | 4 | **4 min of configured allowance**, plus pipeline overhead; not a search-only or response-time upper bound |
| Separate solver development pilot | Six mixed families × three methods at 5 s; heavy mixed × three methods at 30/60 s; four prototype checks | 28 | **10 min nominal**, capped at 15 min including pilot overhead, inside the solver runner ceiling |
| Rank-weighting study, unchanged | Primary 552 + scoring sensitivity 216 + additional search seed 72 | 840 | 3,360 s = **56 min** |

The revised larger-event subset is fixed before observing main results: high-occupancy mixed (62/31/24 tier registrations, 117 registrations / 179 seats), near-capacity mixed (73/37/29, 139 / 212), full-capacity mixed (80/40/32, 152 / 232) and Emperor-heavy mixed (99/19/13, 131 / 230). This replaces full-conflict and full-tied in the earlier subset; both remain primary cases. Cross these four mixed events with contribution > activity > category, category > activity > contribution, and contribution > category with activity disabled. Reuse their primary five-second results. Conflict, tied, accessibility and all-disabled cases are excluded from longer-budget comparisons.

Thus there are **324 comparative solver runs plus four separate prototype checks**, or 328 main jobs before pilot/correctness work. Each method has 84 primary outcomes and 12 outcomes at each longer budget. Within a long-budget preference configuration there are four matched events, not 12 independent event replications. Do not pool primary 84-case and longer 12-case rates as though coverage were identical; compare 5/30/60 only on the same subset. The 21 events include five constructed accessibility derivatives related to their mixed bases.

The solver studies and prototype checks share the confirmed **120-minute runner ceiling**, superseding the 18 October 90-minute limit. Comparative search allocation totals **75 minutes**. Adding prototype allowances gives a nominal **79 minutes**, leaving 41 minutes for preparation/pilot, construction, auditing, output and reporting. The pilot's nominal 10 minutes is part of that remainder, with a 15-minute pilot ceiling. End measured work by minute 115, reserving five minutes for reporting. This is not a measured completion forecast; require a fresh projection and preserve incomplete records if stopped. The separate weighting ceiling remains **120 minutes**. Combined permitted sequential runner execution is at most **240 minutes (4 h)**, excluding development and later dissertation writing.

Use 5/30/60 seconds, with no ten-second batch. Five seconds supplies the short-budget reference; 30 seconds tests whether the extra half-minute to 60 provides a benefit. Lewis & Carroll used five seconds for approximate comparability with their tabu search runtime and 600 seconds for a broader investigation of IP behavior ([author manuscript, §5](https://rhydlewis.eu/papers/LewisCarroll.pdf)). This supports investigating time allowances, not treating either limit as a universal seating standard or copying their numerical results.

## Budget interpretation and decision rules

- If 30 and 60 seconds yield the same complete-map coverage and costs on the selected cases, report that 30 seconds was sufficient to match the observed 60-second outcomes on those cases. This does not establish the minimum necessary time or a universal guarantee.
- If 60 seconds obtains additional valid maps or lower costs, report the cases and magnitudes alongside extra elapsed time. A small numerical gain is not automatically a meaningful operational benefit.
- If only proof/bounds improve, describe a proof benefit rather than better seating quality.
- If outcomes worsen or maps remain missing, retain those observations. Fresh runs with different limits are not guaranteed to follow the same trajectory or yield monotonic endpoints.
- Keeping 60 seconds as a conservative engineering ceiling is allowed; the experiment is allowed to recommend a shorter allowance. It cannot establish that staff accept the waiting time, that every future event will finish, or that 60 seconds is universally optimal.

## Main-chapter evidence package

Q10 confirms five analytical figures plus one 230-seat Emperor-heavy illustration: solver outcome heatmap, paired solver costs, budget-response panels, weighting component trade-offs, and weighting scoring sensitivity. The 20 October amendment retains this package: expand the outcome heatmap to 21 rows and use the revised mixed subset for budget panels. A compact sensitivity table may replace Figure 5. Keep phase runtime and proof in the main solver table; additional runtime-versus-demand, solver component and proof figures remain secondary. Use three main result tables, an event inventory in methodology and full records in the appendix. See the [reporting plan](benchmark-results-visualization.md).

Generate JSON records first, derive tables, then plot those same filtered records. Figures must explain a distinct hypothesis/question and retain failures and missing coverage. No fabricated convergence traces, composite accuracy, financial-cost interpretation, satisfaction percentages or unexplained overall winner scores are included.

## GrillMe decision audit and remaining work

The table preserves the original Q1–Q13 answers through 18 October. Their 13-event / 90-minute scope is superseded by the separately numbered [20 October Q1–Q6 amendment](solver-benchmark-scope-amendment-2026-10-20.md#decision-audit-and-closure), confirmed through Q6 A. Both interviews are closed with no unanswered research-design question. The amendment records original-input retention, nonadoption of spreadsheet-derived candidates, both new four-pattern families, revised mixed subset, 28-job pilot and 120-minute ceiling.

| Question | Settled decision |
|---|---|
| Q1 | Conditional engineering justification of the already-selected CP-SAT implementation, supported by a shared comparator harness |
| Q2 | Separate solver-study execution allowance; its original provisional 30-minute ceiling is superseded by Q12 |
| Q3 | Representative preference configurations with current-ratio weighting fixed for solver comparison |
| Q4 | Known-feasible synthetic scenarios; deliberately infeasible cases remain separate |
| Q5 | SCIP MIP and deterministic constraint-aware greedy, supported by cited research with adaptation limits |
| Q6 | Separate validity, coverage, cost/components, runtime and proof reporting |
| Q7 | Five-second primary search reference and common timing controls, extended explicitly by Q12/Q13 |
| Q8 | First-draft shared understanding confirmed; later amendments recorded rather than silently replacing it |
| Q9 | Tier proportions are registration counts; confirmed 99/19/13 composition occupies 230 seats |
| Q10 | Five analytical figures plus near-capacity illustration; sensitivity table substitution allowed |
| Q11 | Allow evidence to show a shorter allowance is sufficient; do not force a conclusion that 60 seconds is necessary |
| Q12 | A: expand solver-study runner ceiling to 90 minutes, preserving the weighting study's 120 minutes |
| Q13 | Confirm 5/30/60 design, fixed 12-case longer-budget subset, four prototype checks and unchanged weighting protocol |

**No unanswered research-design or figure-scope question remains in this GrillMe session.** The user's instruction to update these plans follows confirmation of Q10/Q13 and closes the current planning interview. Weighting-protocol Q1–Q9 were already confirmed and are a separate numbering sequence. Human evaluation is explicitly deferred future work, not an unanswered question blocking this study.

The [solver harness](../../research/experiments/solver_benchmark/README.md) implements the common infrastructure for the earlier scope. Its [development validation record](../results/solver-benchmark-setup-2026-10-18.md) is historical, separate from main evidence. Remaining work includes implementing the confirmed 21-event amendment, preserving original input hashes, updating schedule/projection/deadline/reporting checks, fresh certification/pilot and gated main execution, plus the separate weighting runner/study. These are implementation/preflight tasks rather than unanswered preference questions. If the pilot cannot fit, reveals inequivalent formulations or requires a substantive scope change, stop with diagnostics and record an amendment before main work. Do not silently reduce coverage or extend deadlines.
