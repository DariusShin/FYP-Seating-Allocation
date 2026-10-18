# Benchmark result tables and dissertation figures

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status: **confirmed reporting plan, Q10/Q13; implementation and execution pending**. The main package is five analytical figures across solver, budget and weighting studies plus one 230-seat illustration. A compact sensitivity table may replace Figure 5 if clearer. The [solver protocol](solver-selection-benchmark.md) includes the confirmed 5/30/60-second design and 90-minute ceiling; the [weighting protocol](rank-weighting-experiment.md) retains its 120-minute ceiling. No new results, mock measurements or plots have been produced.

Scope amendment confirmed by the user on 12 October 2026: exclude human/stakeholder evaluation from the dissertation's experiment analyses and figure package. Operational human verification is deferred until after FYP completion and live system deployment. Preserve it only as future work, not as a pending requirement for completing these computational experiments. The user's latest Q10 answer confirms this amended figure package, superseding the earlier five-solver-figure proposal.

## Purpose and evidence limits

Use figures to explain whether the evaluated implementations return complete valid maps, their modeled preference costs, resource/time behavior and available proof information. The dissertation's confirmed claim is a justified CP-SAT engineering choice on evaluated PJKIT scenarios, not universal algorithm superiority. Evidence contradicting the choice must remain visible.

The primary solver benchmark is 13 synthetic events × four preference configurations = 52 matched cases, evaluated by three methods = 156 primary runs at five seconds. Q13 adds 72 fresh 30/60-second runs on 12 matched larger cases and four separately configured prototype checks. There is one run per method/case/budget, not repeated timing trials or 228 independent event samples. The three constructed accessibility derivatives are related to their mixed-attribute base events. Compare budget rates on the same 12-case subset, never the full 52-case primary denominator against the smaller subset. See the [hypothesis-to-analysis mapping](experiment-hypotheses-and-analysis.md).

Lewis & Carroll's peer-reviewed seating study plots solution costs and runtime against problem characteristics and compares a heuristic with IP under time limits. This supports discussing quality and time together; their figures do not establish what PJKIT's unrun benchmark will show. See [author manuscript, §§4–5 and Figures 4–5](https://rhydlewis.eu/papers/LewisCarroll.pdf), [journal DOI](https://doi.org/10.1057/jors.2016.34), checked 12 October 2026. The figure choices below are project recommendations adapted to the current design.

## Experiments and analyses to distinguish

| Activity | Question | Evidence and boundary |
|---|---|---|
| Correctness and equivalence suite | Do model, scorer and placement audit implement the same declared rules? | Tiny independently solved cases, known-feasible witnesses and separate deliberately infeasible/invalid cases. This is a gate before performance measurement, not a solver-speed ranking. Greedy is not expected to prove infeasibility. |
| Solver comparison | Which method returns a valid map, at what cost and time, under the common search budget? | 52 matched cases × CP-SAT/greedy/SCIP; fixed current-ratio rule within each preference configuration. Primary dissertation solver-selection evidence. |
| Scenario analyses of that benchmark | How do outcomes differ with demand, attribute conflict, ties, accessibility and Emperor-heavy demand? | Slices of the same 156 runs, not additional independent experiments. Emphasize the 230-seat case and full 232-seat cases. |
| Budget comparison | What additional valid maps, lower costs or stronger proofs are observed at 30 and 60 seconds? | Four fixed larger events × three active configurations × three methods; reuse primary five-second endpoints and add 72 fresh runs. H3 contrasts 5→30 and 30→60 separately. |
| Prototype timing verification | What complete-result return time does the configured 60-second prototype achieve? | Four separately labelled local initial-allocation checks under current/default order and actual prototype settings; report complete output and audit, not just search time. Exclude these from matched solver comparisons. |
| Weighting comparison | How do current-ratio, rank sum, rank reciprocal and ROC represent ranked preferences? | Separate CP-SAT-only protocol with 12 events and its declared batches; report common-scale components rather than rank formulas by their different objectives. |
| Scoring sensitivity and limited seed check | Are weighting observations sensitive to scoring assumptions or one extra search seed? | Already-defined weighting-study subsets, not solver-wide sensitivity/robustness experiments. |

The dissertation experiments are **computational evaluations on synthetic event profiles** once actually executed. Before execution, expected outcomes are hypotheses, not findings. These experiments can supply measured modeled quality and performance without a live deployment; they do not measure human satisfaction or validate PJKIT's numerical preference trade-offs. Deferred post-project human evaluation is outside the table above and outside the main result figures.

## Explicit cost and runtime measurements

Cost and runtime are already core measurements in the solver benchmark and must remain prominent in the main discussion. Lewis & Carroll minimize the combined wedding-model objective f1 + f2 (seating relationship cost and table-occupancy imbalance), plot CPU time in seconds in Figure 4, and compare IP formulations with their tabu method under five-second and 600-second limits in §5/Figure 5. Their IP backend is XPressMP. This is methodological precedent for examining quality, time and feasibility together, not a basis for copying their objective or comparing their numeric runtimes with PJKIT on different hardware.

| PJKIT measurement | Definition | Proposed display |
|---|---|---|
| Total solution cost C | C = w_c F_c + w_a F_a + w_k F_k, where each F is the aggregate fixed-reference normalized preference penalty and matched solvers use identical integer coefficients | Exact table values and paired cost differences in Figure 2; lower is better |
| Cost per registration | C/N for N > 0; preserve the same objective coefficients within a matched case | Matched differences normalized by registration count; keep preference configurations in separate panels |
| Component mean costs | F_c/N, F_a/N, F_k/N; disabled components are diagnostics | Solver table and optional secondary solver component plot; weighting trade-offs in Figure 4 |
| Search wall time | Elapsed wall-clock seconds inside the declared method search boundary | Solver table and Figure 3 budget panels; label 5/30/60-second allowances separately from observed return time |
| Total measured allocation wall time | Elapsed time for input/preprocessing, model or heuristic preparation, search and external audit; record persistence/reporting overhead separately | Main solver/budget tables; optional runtime-versus-demand plot. This is research-harness time, not deployed UI/network latency |
| Prototype complete-result return time | Local service-boundary elapsed time through final formatted output, plus separately recorded external audit and total through audit | Budget/prototype table with eight-worker/canonicalization settings visible; not an extra controlled solver point or a guaranteed 60-second response |
| Optional process CPU time | Comparably measured user + system CPU seconds for the run, with process/child boundaries stated | Supplemental table/plot only if implemented consistently; never relabel wall time as CPU time |

PJKIT's solution cost is modeled preference penalty, not financial cost, contribution money, or a satisfaction percentage. CPU time and elapsed wall time measure different quantities. Primary PJKIT timing remains wall-clock time as already confirmed; adding comparable CPU counters would not add solver runs. Only independently validated complete maps enter cost comparison. All-disabled ordinary cost is zero and supplies no preference-quality ranking.

## Tabular evidence before plotting

Generate tables from the saved JSON described in the [execution guide](experiment-execution-sequence.md), then derive plots from the same filtered records. Keep an exportable full record table in the evidence bundle/appendix; the main chapter can use compact summaries.

| Table | Grain and key columns |
|---|---|
| Event inventory | 13 event rows: event ID, pattern, registration count, tier counts, physical seat demand, Emperor registration share, accessibility provenance and witness status |
| Run outcomes | 228 planned comparative method-run rows plus four separately labelled prototype rows: batch, event/configuration/method/budget, worker/canonicalization settings, execution and solver statuses, complete-map return, independent audit, objective coefficients/cost, three component means, bound/proof, construction/search/audit/total time |
| Matched comparisons | One row per eligible method pair and matched case: both-valid flag, paired cost/time/component differences and reasons for exclusion; keep the complete planned case list visible |
| Coverage and outcomes | By method/configuration/scenario: planned, attempted, completed, validated, no-map, invalid and not-started/interrupted counts; validated/attempted known-feasible rate alongside coverage against the manifest |
| Near-capacity case detail | All four configurations for the 230-seat event, with each method's outcome, costs, component means, phase times and proof; give the full-size mixed event a separate clearly identified comparison |
| Budget contrasts | For each method/configuration, 5→30 and 30→60 on the same four larger events: both-valid count, additional/lost valid maps, paired cost/component differences, time difference and proof change |
| Weighting results | Rule/configuration/event/scoring variant/seed, distinct objective aliases, component vector, validity, proof/bound and 1/4-second checkpoint availability |

Display unavailable values with reasons, not zeros. Bound/gap is N/A for greedy and for unavailable exact-solver information. A method claiming INFEASIBLE on an independently witnessed known-feasible input is a discrepancy to investigate, not a successful infeasibility result.

The main chapter uses **three compact result tables**: solver outcomes/cost/runtime/proof; budget contrasts with a separately labelled prototype subsection; and weighting outcomes/sensitivity. Place the event inventory in methodology and complete run/comparison tables in the appendix or evidence bundle. All tables and graphs must come from the same saved JSON records and reproducible filters.

## Confirmed main-chapter figures

These are five analytical figure families across all studies, plus one map illustration. Panels can keep the chapter compact. Main figures answer distinct hypotheses/questions; runtime and proof do not each require a separate main figure.

### Figure 1 — Complete-map outcomes

Use a categorical outcome heatmap with 13 event rows, three method columns and four panels for the preference configurations. Group event rows by base scenario/accessibility derivative and mark the additional Emperor-heavy case. A small companion count table can provide denominators.

Show independently validated optimal/feasible outputs, no-map timeout/unknown, greedy construction failure, invalid output, and unexecuted/interrupted/validation-pending records distinctly. Keep solver proof and audit meanings clear; a solver's OPTIMAL label does not override a failed placement audit. All-disabled feasibility is a control, not evidence of preference-quality superiority.

Discussion: whether each method reliably returned a complete hard-valid map on the tested cases within the declared budget. Count outcomes descriptively; do not infer population reliability from 52 correlated cases.

### Figure 2 — Matched preference-cost differences

Use paired difference dot plots for CP-SAT versus SCIP and CP-SAT versus greedy, faceted by the three nonzero-objective preference configurations. For each both-valid matched case, plot `(cost_CP-SAT - cost_comparator) / N`, where N is the registration count. Negative means a lower CP-SAT cost; zero means an observed tie, not necessarily a common proved optimum. Use a zero reference line and show case identifiers or scenario markers. Record each panel's eligible pair count and excluded outcomes. Report an all-three-valid subset separately if useful, not as an undisclosed filter.

Costs must be independently rescored under identical coefficients for the matched case. Per-registration normalization prevents raw event totals alone from reflecting different numbers of registrations, but does not remove scoring/population assumptions. Keep panels separate; active-count/rank coefficients differ across configurations, so do not average these costs into a single global algorithm score. Exclude all-disabled cases from preference-quality ranking. If a comparator returns no valid matched plans, report that comparison as not estimable rather than forcing a cost plot.

Discussion: where methods find better modeled allocations within the cutoff, and whether any difference is established optimal or only a difference between time-limited incumbents.

### Figure 3 — Budget response at 5, 30 and 60 seconds

Use aligned panels for valid-plan counts/rates, paired preference-cost changes, and observed elapsed time under the three search allowances. Use only the predeclared 12 matched larger cases at all three budgets, with four events per active configuration and 12 per method across configurations. Show denominators and execution coverage. Keep configuration-specific costs separate and plot each method's 5→30 and 30→60 paired changes on both-valid cases. If a comparison has no valid pair, show it as unavailable, not zero improvement.

The x-axis is **configured search allowance**, not elapsed time along a single solve. These are separate fresh runs; connecting endpoints is only a comparison guide, not a convergence trajectory. Do not force monotonic results or interpolate unobserved budgets. Search and total return time have distinct units/boundaries even when both are seconds. Failed-run duration is not time to a valid map. Report prototype observations separately in the budget table rather than mixing eight-worker canonicalized observations with the one-worker comparison.

Discussion: H3's additional valid maps, cost changes, proof-only gains and extra elapsed time. Explain when 30 seconds matches observed 60-second outcomes, when 60 helps, and where neither succeeds. No conclusion establishes a universal minimum or staff-approved wait.

### Figure 4 — Weighting component trade-offs

Use three aligned dot-plot panels or a labelled component heatmap for contribution-seat, activity and category mean penalties under current-ratio, rank sum, rank reciprocal and ROC. Compare rules on matched events/configurations with the primary scoring definitions fixed. A pair counts as one registration, consistent with the scorer. Lower is better; these are modeled penalties, not satisfaction percentages. Show distinct objective aliases so equivalent two-, one- and zero-preference controls are not presented as independent solver trials.

Emphasize the predeclared conflict cases and multi-preference configurations for H2, with matched pattern/ranking panels where legible. Retain other configurations/events in the appendix. The weighting study has 12 events and does not contain the benchmark-only 230-seat event. Mark disabled components as diagnostic. Retain no-map outcomes and proof status beside the component comparisons; time-limited incumbents are not automatically exact optimal responses to a weight change.

Discussion: how weighting rules change observed trade-offs, where rules agree, and where compulsory constraints limit response. Never rank formulas by their own differently weighted objective totals or infer equal cardinal meaning from normalized component endpoints.

### Figure 5 — Weighting scoring sensitivity

Show whether the weighting observations change under the predeclared alternative category penalties and score resolution. Rescore returned maps on the original reference component scale and use matched baseline/variant differences with event/configuration identifiers. This uses the weighting protocol's existing 216 sensitivity searches; it adds no runs. Preserve validity, missing comparisons and proof qualifications. Keep the limited 72-search additional-seed check separately labelled rather than pooling it as independent input replication.

If observations are unchanged or a compact table communicates the effect better, replace this figure with the sensitivity subsection of the weighting table, as confirmed in Q10. Do not manufacture a visually dramatic chart from negligible or absent effects.

Discussion: which conclusions depend on the scoring assumptions and which persist across the tested variants. Robustness here is limited to those declared variants; it does not validate PJKIT's true preference strengths.

## Near-capacity map illustration

Include one additional case illustration beside the 230-seat results table: aligned returned seating maps with identical geometry, tier colors/pair outlines and blocked/empty-seat conventions. Use the primary five-second outputs in current preference order for the predeclared 230-seat event. Label 99 Emperor pairs, 19 Merit, 13 Bodhi; 131 registrations, 230 occupied seats out of 232 available; event/configuration, validity, objective/proof and timing.

Show every comparator's outcome, including a no-map panel when appropriate. Use saved returned incumbents without extra canonicalization searches. Different-looking layouts can have identical costs or tied optima; visual appearance alone is not evidence of superiority. A corresponding 232-seat mixed-event illustration may be placed in an appendix. This is interpretation of stored outputs, not an additional solver experiment.

## Conditional and secondary figures

- **Anytime/convergence curves:** only if comparable incumbent/bound events are captured during the original solver runs. Use step curves with search time on the x-axis and cost/bound on the y-axis; the curve is undefined until a complete valid incumbent exists. Do not invent intermediate points, join separate case endpoints into a trajectory, or repeat solves to simulate a trace within the approved budget. This is optional in the solver protocol; endpoint figures remain the confirmed primary package.
- **Runtime versus workload:** use observed physical demands 32, 152, 230 and 232, annotated with registration counts 24, 96, 131 and 152 and profile/accessibility markers. Search, construction and audit times remain distinct. Demand/composition vary together, so do not infer a participant-count causal effect or an empirical complexity law. Do not smooth/interpolate unsupported scalability curves.
- **Solver component explanation:** show aligned contribution/activity/category mean penalties for the primary 230-seat/current-order case, retaining no-map panels. If no comparable maps exist, retain that outcome and use the predeclared full-size mixed case as a secondary illustration. Never select a case because it favors CP-SAT.
- **Solver proof information:** retain bounds/gaps/proof in the main table; add a secondary status/gap figure only when useful. Greedy bounds are N/A, unavailable bounds are missing, all-disabled zero objectives are separate and a small nonzero gap is not proof. Equal unproved costs do not establish a shared optimum.
- **Accessibility paired comparison:** connect each mixed base event with its constructed accessibility derivative, with method and configuration fixed. Show cost/time and outcome changes. This is limited to the constructed cases, not broad accessibility robustness.
- **Quality/time scatter:** an optional trade-off view of both-valid matched outputs, labelled by event/configuration. With one endpoint per run it is not a convergence curve or proof of a global Pareto frontier.
- **Weighting-study figures:** component trade-off dots/heatmaps, paired rank-response plots, observed-candidate nondominance views, scoring-sensitivity panels on the original reference scale, and the specified 1/4-second checkpoints. Never rank weighting formulas by their own differently weighted objective totals. The extra seed check is limited evidence, not a large timing distribution.
- **Memory:** add a per-run memory figure only if comparable per-run instrumentation exists. The older harness's cumulative process-peak RSS does not support per-method memory bars.

## Graphical safeguards and dissertation use

- Show raw observed dots and matched differences. With one run per method/case, do not present error bars or boxplots as repeated-run runtime variability. Across-case medians/ranges may be descriptive if the case grouping, sample count and dependence are explicit. The first draft does not support population-level significance claims.
- Retain complete-map failures and missing coverage beside cost/runtime figures to prevent selective-success comparisons. Do not turn a cutoff without a map into a completed solution time.
- Avoid an invented algorithm-accuracy percentage, a satisfaction percentage derived from penalties, and a single winner score. Avoid radar charts for the main comparison: they obscure units and trade-offs already addressed by aligned panels.
- Use consistent method colors plus shapes/line styles and direct labels so figures remain understandable in grayscale. Use consistent axes for matched panels, legible legends and captions identifying event/configuration, budget, units, lower-is-better direction, denominator and exclusions.
- Export dissertation plots as PDF/SVG with a high-resolution PNG fallback. Create scientific plots from saved records with standard plotting tools; no generated chart artwork or invented data. Exact formatting/export tooling can be settled during reporting implementation.
- Discuss outcomes in this order: coverage/validity, valid-map quality, time/workload, component explanations, proof limits, then the near-capacity example and threats to validity. Cite tables and figures as evidence for conditional conclusions; do not write results before the main records exist.
- Derive tables/figures from saved JSON with reproducible filters. Essential reporting must fit existing runner allowances. If final publication formatting is completed later, identify it as postprocessing of frozen records without extending solver execution or losing the deadline diagnostics.

## Confirmed Q10 and closed interview

The user confirmed the amended main package: five analytical figures (solver outcomes, solver cost, budget response, weighting trade-offs and weighting sensitivity) plus the 230-seat illustration, allowing a sensitivity table substitution when clearer. Three main results tables preserve exact values; complete records and secondary plots belong in the appendix/evidence bundle. This supersedes the earlier proposal to use five solver-only figures.

Q13 confirms the timed experiment scope underlying these views. No unanswered figure-scope question remains. See the [complete decision audit and implementation work](experiment-hypotheses-and-analysis.md#grillme-decision-audit-and-remaining-work); no figures or measured findings have yet been produced.
