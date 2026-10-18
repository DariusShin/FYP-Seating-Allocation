# Experiment hypotheses, analysis and confirmed decisions

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status: **confirmed planning scope; implementation and execution pending**. The user confirmed visualization Q10 and experiment-scope Q13 after accepting Q11 (allow shorter-budget conclusions) and Q12 A (a 90-minute solver-study runner ceiling). This document connects the existing protocols to the dissertation claims. It records no new measurements or selected operational weights.

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

H1 is three configuration-specific predictions, not a pooled algorithm winner score. If no both-valid pairs exist, the corresponding cost comparison is not estimable; preserve the failures and denominator. H3's coverage and quality outcomes are separate evidence, even if one improves and the other does not. These are bounded descriptive synthetic studies, not population-level hypothesis tests; no p-values or runtime-variance claims are justified by one run per solver/case/budget.

Correctness is a prerequisite: every accepted output must assign each eligible registration its complete entitlement and pass every hard-rule check. Tiny independently solved equivalence cases and deliberately infeasible cases belong in the separate correctness suite. Correctness checks are not a comparative speed ranking. An INFEASIBLE claim for a witnessed feasible case is a discrepancy to investigate.

Weighting results describe observable behavior at the declared four-second budget. Keep optimum proofs, bounds, the 1/4-second checkpoints and limited additional-seed results visible; differences between time-limited incumbents alone do not prove differences between the true optimal allocations. The study does not discover PJKIT's true numerical preferences, validate attendee satisfaction or require a universally winning formula. Human verification is deferred until after FYP completion and live deployment.

## Confirmed experiment package

Use the [solver protocol](solver-selection-benchmark.md) for adapter definitions, controls and deadlines, the [weighting protocol](rank-weighting-experiment.md) for weighting batches, and the [execution guide](experiment-execution-sequence.md) for sequence and JSON provenance.

| Batch | Frozen coverage | Runs | Allocated solving time |
|---|---|---:|---:|
| Primary solver benchmark | 13 events × four configurations × three methods; five-second search allowance | 156 | 780 s = **13 min** |
| Longer-budget comparison | Four larger events × three preference-active configurations × three methods × two additional budgets (30/60 s) | 72 | 3,240 s = **54 min** |
| Prototype timing checks | Four larger events × current/default preference order; configured 60-second prototype allowance | 4 | **4 min of configured allowance**, plus pipeline overhead; not a search-only or response-time upper bound |
| Rank-weighting study, unchanged | Primary 552 + scoring sensitivity 216 + additional search seed 72 | 840 | 3,360 s = **56 min** |

The larger-event subset is fixed before observing results: the three 232-seat base events (mixed profiles, contribution/activity conflict, tied contributions with varying activity) and the 230-seat Emperor-heavy mixed event (99 Emperor, 19 Merit, 13 Bodhi registrations). Accessibility derivatives are outside the longer-budget subset. Cross these four events with contribution > activity > category, category > activity > contribution, and contribution > category with activity disabled. Their five-second results are reused from the primary benchmark, not rerun. All-disabled cases remain primary feasibility controls and are excluded from the longer-budget extension.

Thus there are **228 comparative solver runs plus four separate prototype checks**, before pilot/correctness work. Each method has 52 primary outcomes and 12 outcomes at each longer budget. Within a long-budget preference configuration there are four matched events, not 12 independent event replications. Do not pool the primary 52-case and longer 12-case rates as though their coverage were identical; compare 5/30/60 only on the same 12-case subset.

The solver studies and prototype checks share the confirmed **90-minute runner ceiling**, superseding the earlier 30-minute ceiling. Comparative search allocation totals **67 minutes**. Adding four configured prototype allowances gives a nominal **71 minutes**, leaving 19 minutes for preparation/pilot, construction, auditing, output and reporting if all these allowances are consumed. This arithmetic is not a measured completion forecast: prototype processing can exceed its configured allowance, and construction/pilot overhead must be measured. Early completion can shorten runs. The separate weighting ceiling remains **120 minutes**. Combined permitted sequential runner execution is at most **210 minutes (3 h 30 min)**, excluding harness development and later dissertation writing.

Use 5/30/60 seconds, with no ten-second batch. Five seconds supplies the short-budget reference; 30 seconds tests whether the extra half-minute to 60 provides a benefit. Lewis & Carroll used five seconds for approximate comparability with their tabu search runtime and 600 seconds for a broader investigation of IP behavior ([author manuscript, §5](https://rhydlewis.eu/papers/LewisCarroll.pdf)). This supports investigating time allowances, not treating either limit as a universal seating standard or copying their numerical results.

## Budget interpretation and decision rules

- If 30 and 60 seconds yield the same complete-map coverage and costs on the selected cases, report that 30 seconds was sufficient to match the observed 60-second outcomes on those cases. This does not establish the minimum necessary time or a universal guarantee.
- If 60 seconds obtains additional valid maps or lower costs, report the cases and magnitudes alongside extra elapsed time. A small numerical gain is not automatically a meaningful operational benefit.
- If only proof/bounds improve, describe a proof benefit rather than better seating quality.
- If outcomes worsen or maps remain missing, retain those observations. Fresh runs with different limits are not guaranteed to follow the same trajectory or yield monotonic endpoints.
- Keeping 60 seconds as a conservative engineering ceiling is allowed; the experiment is allowed to recommend a shorter allowance. It cannot establish that staff accept the waiting time, that every future event will finish, or that 60 seconds is universally optimal.

## Main-chapter evidence package

Q10 confirms five analytical figures plus one 230-seat illustration: solver outcome heatmap, paired solver costs, budget-response panels, weighting component trade-offs, and weighting scoring sensitivity. A compact sensitivity table may replace Figure 5 if clearer. Keep phase runtime and proof information in the main solver table; additional runtime-versus-demand, solver component and proof figures are secondary. Use three main result tables (solver, budgets/prototype, weighting), with a compact event inventory in the methodology and full records in the appendix. See the [confirmed reporting plan](benchmark-results-visualization.md).

Generate JSON records first, derive tables, then plot those same filtered records. Figures must explain a distinct hypothesis/question and retain failures and missing coverage. No fabricated convergence traces, composite accuracy, financial-cost interpretation, satisfaction percentages or unexplained overall winner scores are included.

## GrillMe decision audit and remaining work

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

Implementation work remains: build the common harness/adapters and reproducible reports; freeze exact input/search/order seeds and hashes (including the added Emperor-heavy input); implement the specified greedy checks and verify MIP equivalence; instrument the prototype's complete local return boundary; certify feasibility witnesses; and complete the development pilot. These are implementation/preflight tasks rather than additional preference questions. If the pilot cannot fit the declared workload, reveals inequivalent formulations or requires a substantive scope change, stop with diagnostics and propose a protocol amendment before the affected main batch. Do not silently reduce coverage or extend deadlines.
