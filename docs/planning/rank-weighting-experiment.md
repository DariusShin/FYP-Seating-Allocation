# Rank-weighting experiment: confirmed protocol

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status: **confirmed amended protocol; implementation and execution pending**. Following the initial confirmation on 12 October 2026, the user requested a hardware-constrained experiment lasting no more than two hours and removal of the equal-weight method. This revision replaces the earlier scale and budgets while retaining research decisions Q1–Q9. No new experiment has been executed and no production weights have been changed by this planning work.

**Human-evaluation scope amendment, 12 October 2026:** the user subsequently deferred human/stakeholder verification until after FYP completion and live deployment. It is excluded from the dissertation experiment analyses, figures and required deliverables. Section 7 preserves future-work guidance only. This supersedes the earlier timing assumption that operational preference validation would accompany project usability testing; computational scope, datasets and budgets remain unchanged.

**Reporting/budget cross-reference amendment, Q10–Q13:** this study's 12 events, 840 searches, four-second limits and 120-minute runner ceiling remain unchanged. The separate solver studies now use a 90-minute ceiling and a fixed larger-case 5/30/60-second comparison; do not import those limits or the benchmark-only 230-seat event here. The [hypotheses and analysis plan](experiment-hypotheses-and-analysis.md) records H2, and the [confirmed figure package](benchmark-results-visualization.md) uses weighting component trade-offs and scoring sensitivity as Figures 4/5, allowing a sensitivity table substitution. The GrillMe questions for the current topic are settled; implementation/preflight remains pending.

## Amendment: hardware budget and candidate scope

The active design uses four methods, 12 primary datasets, four-second searches and a **120-minute overall runner deadline**. It plans 840 experimental searches with 56 minutes of allocated search time; remaining time covers preparation, a bounded pilot, model construction, validation, persistence and reporting. This is a scheduling allocation, not a measured completion guarantee. The former 45-dataset, ten-second, equal-weight-inclusive design and extended-proof batch are superseded.

Equal weighting is excluded because the research question now compares alternative representations of an assumed strict ordering of importance among enabled preferences. For K ≥ 2, each candidate has w₁ > … > w_K > 0. This coefficient ordering remains compensatory; it does not establish lexicographic allocation priority. Agreement on ranking does not validate any numerical ratio. Without an equal-weight control, the study cannot claim that unequal weighting improves outcomes over equal weighting.

The selected plan uses the upper end of the user's one-to-two-hour allowance. A one-hour-only design would require a further explicit protocol amendment; the runner must not silently reduce datasets or per-search budgets to force completion.

## Confirmed decisions

| Question | Confirmed decision | Consequence for the design |
|---|---|---|
| Q1: Meaning of preference priority | Compensatory relative importance | A higher-ranked preference can be outweighed by improvements in other preferences. No strict preference-priority guarantee is claimed. |
| Q2: Research claim | Assumption-based design: “This study compares published rank-weighting methods for implementing configurable seating preferences under the modeled PJKIT constraints.” | Synthetic experiments compare properties under stated assumptions; they do not independently establish PJKIT's true numerical trade-offs. |
| Q2: Subsequent validation, amended 12 October | Defer human verification until after FYP completion and live deployment | Outside dissertation experiments and required deliverables; retain preference/decision validation and usability as distinct future tasks. |
| Q3: Scope of weighting mechanism | A general rule supporting staff toggles and reprioritization before seating-map regeneration | Evaluate ordered enabled subsets, not only one three-preference vector. Derive weights using the number of enabled preferences. |
| Q4: Computational outcome | Characterize trade-offs rather than force a winning method | Stakeholder evaluation will inform the eventual default. Each method's own weighted objective is not a common measure of superiority. |
| Q5: Scoring assumptions | Keep current component definitions and category matrix fixed for the primary comparison; conduct a separate sensitivity analysis | Attribute primary differences to the weighting rule. Report any changes in conclusions under plausible alternative scoring assumptions. |
| Q6: All preferences disabled | Allow preference-free ordinary regeneration | Enforce compulsory rules and use a documented tie-breaker without restoring hidden preference weights. The separate movement/distance hierarchy in absence repair remains intact. |
| Q7: Workflow coverage | Study initial allocation only | Regeneration, seat movement from a saved map and absence repair are outside this experiment, even though the proposed weighting rule is intended for the configurable application. |
| Q8: Runtime interpretation | Measure runtime and solution quality at declared experimental budgets | No budget is presented as a validated staff waiting-time requirement. |
| Q9: Operational preference validation | PJKIT staff are the primary judges of seating appropriateness | Keep their assessments distinct from the industry supervisor's and product manager's assessments; do not pool all roles into an unexplained vote. |

The existing strict absence-repair hierarchy—moved registration units, then distance, then preference cost—remains distinct from the compensatory treatment of preferences within their own stage.

## Established context

- Current preference factors are contribution-seat matching, activeness and category-zone suitability.
- Candidate rank-based methods discussed are rank sum, rank reciprocal and rank-order centroid (ROC). Current 40:30:20 is a reference baseline, not an empirically validated policy.
- The earlier study already compared these candidates for one fixed preference order with all three enabled. The next study must extend the research question and coverage rather than merely repeat that comparison.
- Component penalty definitions, category-zone costs and normalization contain assumptions independent of the rank-to-weight formula.
- Technical familiarity is not required to compare understandable seating outcomes. Whether a weighting formula represents operational preferences requires evidence beyond interface usability alone.

## Execution order, environment and evidence

Follow the [shared execution sequence and JSON recording guide](experiment-execution-sequence.md). These plans specify experiments. The [solver benchmark runner](../../research/experiments/solver_benchmark/README.md) is now implemented; this amended weighting runner remains pending. The recommended order is shared correctness checks and frozen inputs, separate development pilots, the [solver benchmark](solver-selection-benchmark.md), then this weighting experiment and computational reporting. Human evaluation is deferred post-project future work. This is a practical sequence, not a requirement to establish final operational weights before solver benchmarking: the benchmark holds current-ratio coefficients fixed, whereas this study varies weighting rules with CP-SAT fixed.

Keep this study's 12 events and four-second search limits unchanged. The solver benchmark separately adds the 230-seat Emperor-heavy event, giving it 13 events; that addition does not silently expand this study. Use shared frozen inputs where prescribed and retain their hashes/provenance. Do not change this study's design based on benchmark outcomes without a documented amendment. Computational trade-offs alone do not identify PJKIT's true numerical preferences; later staff judgments inform the default.

Use the user's M4 Mac with 24 GB RAM and macOS as the primary measurement environment, subject to pilot memory/overhead checks. Run both studies sequentially, with the declared worker counts, pinned software, consistent power settings and no competing heavy workload. Colab can support sharing/analysis or a separate portability experiment; keep environment-labelled timing evidence separate. The shared guide cites Google's current resource/persistence limitations.

Save `manifest.json`, frozen input/witness JSON, per-run JSON including complete seat bundles and validation, incumbent/bound traces, separate pilot records and `summary.json` under the result location specified in section 8. Persist each run atomically and record failures and missing coverage. Retain exact coefficient vectors/aliases, scoring variants, source hashes, versions, seeds and timing boundaries so tables can be regenerated from records. Preserve the 120-minute overall runner ceiling; solver benchmarking, budget sensitivity and four prototype checks share a separate 90-minute ceiling. Neither cap includes a later stakeholder session or an additional final-policy solver recheck.

## Research questions and permitted conclusions

**H2:** on cases with conflicting preferences, alternative rank-weighting rules produce different trade-offs between contribution, activity and category penalties. Examine the predeclared conflict cases and distinct multi-preference objectives on the shared reference component scale; describe other patterns separately. Record unchanged outcomes as findings, not failed experiments. Equivalent vectors are correctness controls. At four-second limits, retain proof/bound and limited seed evidence: different returned incumbents do not necessarily establish different exact optimal trade-offs. This is a descriptive synthetic comparison, not a test of human satisfaction or a universal formula winner.

1. How do published rank-to-weight rules change initial-allocation component costs across configurable rankings and enabled subsets?
2. How do dataset characteristics and compulsory rules limit or expose those differences?
3. How sensitive are the observed trade-offs to alternative category penalties and score resolution?
4. What valid solutions and optimality evidence are obtained within declared computational budgets?

The computational study characterizes behavior. It will not choose a universal winner, infer staff satisfaction from penalty totals, or claim that a published formula establishes PJKIT's true numerical preferences. Subsequent stakeholder evidence can inform a default, including the possibility that no candidate is consistently preferred.

Scope is deliberately **initial allocation only**. Every preference configuration starts a fresh solve on the same synthetic input, without a previous seating plan or manual edits. Testing ranking configurations does not establish regeneration usability, movement stability or absence-repair performance.

## Consequences of the confirmed scope

For the three current preferences there are 16 distinct ordered enabled configurations: six with all three enabled, six ordered pairs, three single-preference configurations, and one all-disabled configuration. Changes to the ordering of disabled preferences do not create a distinct decision policy.

The weighting formulas must use the enabled count. Rank sum and rank reciprocal coincide at two enabled preferences (2:1); ROC gives 3:1. All three methods reduce to the same one-preference optimization, up to positive scaling. With no preferences enabled, there is no preference objective to normalize. Equivalent cases are correctness controls rather than independent demonstrations that one method is better.

## 1. Candidate mechanisms and controls

Compare rank sum, rank reciprocal and rank-order centroid, with the existing ratio as the reference control. Let K be the number of enabled preferences and j their rank, with 1 most important. For K greater than zero:

\[
w_j^{RS}=\frac{K-j+1}{K(K+1)/2},\qquad
w_j^{RR}=\frac{1/j}{\sum_{r=1}^{K}1/r},\qquad
w_j^{ROC}=\frac1K\sum_{r=j}^{K}\frac1r.
\]

Use exact rational arithmetic to derive integer coefficients, then divide by their greatest common divisor. Disabled preferences receive zero. Preserve the current baseline's active-rank assignment rather than incorrectly treating it as a published rank-sum method.

| Method | Three enabled | Two enabled | One enabled | None enabled |
|---|---|---|---|---|
| Current-ratio control | 4:3:2 | 4:3 | 1 | Zero preference objective |
| Rank sum | 3:2:1 | 2:1 | 1 | Zero preference objective |
| Rank reciprocal | 6:3:2 | 2:1 | 1 | Zero preference objective |
| ROC | 11:5:2 | 3:1 | 1 | Zero preference objective |

Coefficient reduction preserves exact minimizers, not necessarily time-limited search trajectories. This study therefore compares canonically represented objective rules, not the unmodified production service's runtime.

There are 64 logical method/configuration combinations per input, but only **46 distinct coefficient vectors** in fixed contribution/activity/category coordinates: 24 with three enabled, 18 with two, three with one and one with none. Solve each distinct vector once per data/scoring/search-seed/budget combination and retain every logical alias. Equivalent aliases must not be counted as independent observations or used to claim one equivalent method runs faster. Single-preference and all-disabled cases remain functional controls even though methods coincide in those cases.

## 2. Fixed primary model

Use the maintained initial-allocation hard-constraint builder and an independent placement validator. Keep tier precedence, contribution-row ordering, approved pairs, capacity, compulsory packing and accessibility rules identical for all candidates.

Freeze the current contribution/activity importance definitions, within-row seat disadvantage, category matrix, normalization bounds and half-up rounding for the primary comparison. Freeze inputs within each paired instance. Hash the code, layout, policy and scoring configuration before execution.

Report every plan's three component costs on the same reference scale, including disabled components as clearly labelled diagnostics. A disabled preference may still be correlated with a compulsory rule; turning off its soft penalty does not remove that rule.

Do not change objective coefficients in the deployed configuration as part of the experiment. The research runner supplies experimental coefficients independently, without mutating production policy.

## 3. Reduced synthetic benchmark

Use the current 232-seat venue. Retain three sizes for comparison with the earlier study:

| Size | Emperor / Merit / Bodhi registrations | Registrations | Required physical seats |
|---|---|---:|---:|
| Small | 8 / 8 / 8 | 24 | 32 |
| Typical fixture size | 56 / 24 / 16 | 96 | 152 |
| Full venue | 80 / 40 / 32 | 152 | 232 |

Cross these with three patterns: mixed attributes, contribution/activity conflict, and tied contributions with varying activity. Use one deterministic input seed, 20261021, for each size/pattern. This gives **nine base instances**, with no input-seed replication within a scenario. The distributions are stress-test assumptions, not estimates of PJKIT's population.

Establish and independently validate a feasibility witness for every base instance before labelling it known-feasible. Do not reuse these witnesses as search hints in the timed comparison. If a predeclared instance cannot be certified, retain and report it as unresolved rather than silently replacing its seed; its status must be resolved or documented in a protocol amendment before using the known-feasible denominator.

Add three accessibility cases, one per size for the mixed-attribute pattern using seed 20261021. Construct each from a validated witness allocation and mark accessibility requirements only where the assigned complete bundle meets them. This establishes feasibility without assuming that a random accessibility request is always compatible with compulsory packing. Retain the witness and construction record; label the selection bias of these constructed cases. Main benchmark target: **12 known-feasible instances**. Accessibility derivatives are related to their base events, not independent replications. Accessibility under conflict and tied-contribution patterns is not covered.

Keep a separate correctness suite for all-equal activity, absent tiers, empty input if supported by the contract, insufficient capacity, and deliberately incompatible accessibility/pairing conditions. Establish expected feasibility analytically or through an independently validated witness/proof. Do not mix deliberately infeasible cases into the known-feasible success-rate denominator.

Pilot the runner on three mixed-attribute instances, one per size, with the separate development seed 20261020. Use all three preferences in contribution/activity/category order and all four methods: 12 searches at two seconds each, or 24 seconds of allocated pilot search time. Formula/configuration coverage belongs in the correctness suite rather than additional pilot searches. Pilot outcomes are not main-study evidence. Measure build, validation and persistence overhead as well as search time. Resolve harness failures and document any protocol revision before the main batch. Do not choose main seeds based on which method performs well.

## 4. Search budgets, execution deadline and proof control

Primary search limit: **four seconds per distinct objective**, one worker, fixed search seed 20261012. Use a fresh solver without a previous method's incumbent as a hint. Predeclare a shuffled execution order using a recorded seed, balanced across dataset sizes/patterns and method configurations, and run jobs sequentially to reduce resource-contention bias. Preserve the full manifest even if a deadline prevents completion; no method or difficult case may be preferentially skipped based on observed results.

Record incumbent and bound events with elapsed search timestamps and report performance at **1 and 4 seconds along that same search trajectory**. These are observational checkpoints, not independent restarts. If a solve finishes early with proof, carry that result forward to later checkpoints. Keep model construction and external validation times separate from search time.

The primary batch has **12 × 46 = 552 distinct searches**, allocating 2,208 seconds (**36 minutes 48 seconds**) of search time if every search exhausts its limit. Early optimality proofs can shorten this. Construction, checking and file output are additional elapsed time.

**No extended-proof batch is included.** Quality claims requiring exact optima use only results proved within the declared search budget. Retain FEASIBLE and UNKNOWN outcomes, bounds and gaps; do not treat a lack of proof as infeasibility or silently grant difficult objectives extra time.

On the three base mixed-attribute instances (one per size), repeat the 24 distinct three-enabled objective vectors with one additional search seed, 20261013. These **72 searches** allocate 288 seconds (**4 minutes 48 seconds**) and provide a limited search-stability check. Logical aliases and search repetitions are not additional independent event instances.

### Overall wall-clock budget

| Batch | Searches | Search allocation |
|---|---:|---:|
| Primary | 552 | 36 min 48 sec |
| Scoring sensitivity | 216 | 14 min 24 sec |
| Additional search seed | 72 | 4 min 48 sec |
| **Experimental total** | **840** | **56 min** |

Reserve up to 15 minutes for preparation, witness generation, correctness checks and the pilot; 75 minutes for experimental batches including their overhead; 20 minutes for aggregation/tables/figures; and 10 minutes of contingency. These allowances sum to 120 minutes. Pilot search is additional to the 56-minute experimental allocation but contained within the preparation allowance. Harness development and later human interpretation or stakeholder sessions are outside runner execution time.

Implement the deadline from runner start using a monotonic clock and an outer watchdog able to stop child work during model construction, search or reporting. Per-solve CP-SAT limits alone do not enforce an end-to-end runtime ceiling. Stop launching experimental searches by minute 90, reserving the remaining time for validation/persistence/reporting. Bound preparation to its allowance: if correctness or input feasibility cannot be established, stop with a diagnostic instead of running an invalid comparison. Use the pilot to estimate whether the complete batches fit; if they do not, report the projection before the main batch rather than silently changing this design.

Execute primary comparisons first, sensitivity second and seed repeats last. Persist records atomically as they complete, including independent audit status. At the deadline, stop all runner child work and preserve available results; do not extend the session automatically. Distinguish `not_started`, `interrupted_by_deadline` and `validation_pending` execution states from solver-returned statuses such as UNKNOWN or INFEASIBLE. Only independently validated plans enter valid-plan analyses. Report attempted/completed/validated counts against the full planned manifest, and restrict paired comparisons to cases with both required records. Any incomplete batch limits coverage and must be identified prominently in the results. Resumability is for recovery; it does not authorize exceeding the agreed total budget.

Any later budget reduction or dataset change must be documented as a protocol amendment. Do not silently omit difficult runs or merge pilot and main results. The two-hour cap limits execution, not a guarantee that all planned evidence or figures will be produced on the available hardware.

## 5. Measurements and interpretation

Let F_k(z) be aggregate normalized penalty for criterion k and N the number of registrations. Report F_k/N where N is positive; use not-applicable for empty inputs.

| Measurement | Definition and interpretation |
|---|---|
| Hard-rule validity | Independent pass/fail plus violations by rule; a low penalty cannot compensate for invalid seating |
| Valid-solution return rate | Returned complete valid plans divided by attempted searches on the known-feasible set; UNKNOWN is neither a valid plan nor proof of infeasibility |
| Component trade-offs | Contribution, activity and category totals and per-registration means on the fixed reference scale; lower is better, but values are not satisfaction percentages |
| Objective and proof gap | Own-objective incumbent, lower bound, status and `(UB-LB)/max(1,abs(UB))`; compare bounds only within the same objective |
| Time behavior | Time to first incumbent later validated, checkpoint quality, time to proof when attained, and separately measured build/audit costs |
| Single-criterion excess | Where the single-criterion optimum F_k* is proved, report `(F_k(z)-F_k*)/N`; otherwise label the reference unproved and omit exact-excess claims |
| Responsiveness to ranking | Paired changes in component costs when an enabled criterion changes rank, including unchanged outcomes; promotion does not imply a general guarantee that its individual cost decreases |
| Sampled dominance | Whether another returned plan is no worse on every enabled component and strictly better on one; this is comparison within the observed candidate set, not enumeration of the global Pareto frontier |
| Sensitivity | Changes in component trade-offs and objective-based comparisons under the separately specified scoring variants |

Do not rank methods by their own differently weighted totals. Do not use interface task success as a proxy for seating quality. For zero objectives, relative gap is not a useful preference-quality measure; report feasibility and tie-breaking status.

Summarize paired differences by input size, pattern and enabled configuration. Use descriptive paired differences, ranges and distributions with explicit denominators. Preserve event-level pairing. There is only one input seed per size/pattern, so there is no within-scenario input replication from which to estimate population variability. Do not present correlated rankings, search seeds or accessibility derivatives as independent events, or use the 840 searches to imply a large independent sample. The primary report is descriptive, without population-level significance claims.

### Tied optima and all-disabled behavior

Different seat maps do not by themselves show a weighting effect. Evaluate an incumbent under the alternative objective. A strictly better valid alternative establishes that the incumbent is not optimal for that alternative objective; stronger attribution to changed weights requires the original baseline to have been proved optimal too. Equal objective values and proof can establish that the same incumbent remains optimal, even when another map was returned.

The capped computational run retains non-canonical incumbents and performs no extra canonicalization searches. All-disabled inputs have zero preference cost and retain only compulsory rules; label their returned maps non-canonical, without restoring hidden preference weights. This does not implement or validate the application's intended neutral tie-breaking behaviour. Disclose tie limitations for all map/component comparisons.

Representative maps for later stakeholder sessions require a separately budgeted preparation phase: fix a proved primary optimum, then apply registration-ID order followed by ordered legal seat-bundle identifiers as the neutral canonical tie-breaker. Record its time and any incomplete canonicalization. Do not run that later phase as an uncounted extension of this two-hour experiment or claim unique maps before it is completed.

## 6. Separate sensitivity study

Run this after the primary study without changing its recorded results. Use the three base mixed-attribute cases, one per size with seed 20261021, and only the 24 distinct three-enabled objective vectors. Select this subset before observing outcomes; it does not cover conflict/tied-contribution patterns, accessibility derivatives or disabled-preference sensitivity.

Vary one scoring assumption at a time:

1. **Squared category entries:** square every existing entry, recompute the common category maximum, and keep preference ordering/ties within each category intact.
2. **Ordinal category entries:** replace each category's distinct cost levels with 0,1,... while preserving ties; use the same stated global-normalization rule. This changes both gaps and relative category strength, so it is a structural sensitivity scenario, not stakeholder calibration.
3. **Finer rounding resolution:** compute all normalized components on a 0–1000 integer scale instead of 0–100, using the same raw scores and bounds. Divide by ten for displaying native component scores, and additionally rescore every plan with the original 0–100 reference evaluator. This tests discretization, not a new validated preference scale.

This adds **3 × 24 × 3 = 216 searches** at the same four-second search limit: **14 minutes 24 seconds** of allocated search time. Together, the primary, repeat-seed and sensitivity batches have **840 searches and 56 minutes of allocated search time**, subject to the overall wall-clock deadline in section 4.

For each variant, retain both native and original-reference component scores. Never directly compare native weighted totals from different matrices or resolutions. Conclusions are conditional on the tested assumptions; no sensitivity scenario is synthetic ground truth for what staff want.

### Required limitations in the discussion

- One input seed per scenario limits conclusions to these synthetic events; broad population robustness is not established.
- Four-second searches can conflate weighting effects with incomplete optimization. Separate proved comparisons from time-limited observations.
- Sensitivity and repeat-seed evidence covers only three mixed-attribute base cases; accessibility covers only three constructed derivatives.
- One additional search seed is a limited stability check, not a reliable characterization of runtime variability.
- Excluding equal weighting prevents claims that rank-based weighting outperforms treating preferences equally.
- Initial-allocation experiments do not validate regeneration, absence repair, movement costs or stakeholder satisfaction. No universal best method or validated staff waiting-time threshold follows from this study.

Suggested dissertation wording: “This exploratory experiment compares four representations of assumed ranked preference importance under fixed seating constraints and declared computational budgets. Equal weighting is excluded because it does not distinguish preference ranks. Findings describe the tested synthetic scenarios and require subsequent stakeholder evaluation; they do not establish that unequal weighting is superior to equal weighting.”

## 7. Deferred post-project stakeholder validation (future work only)

This section is excluded from the dissertation experiment analysis and deliverables. It records potential work after FYP completion and live deployment, as requested by the user. No human data collection, acceptance/satisfaction metric, stakeholder figure or operational calibration claim is required or supplied by the current computational studies. A default used during the project remains explicitly assumption-based.

PJKIT staff provide the primary operational appropriateness judgments. Record the industry project supervisor's and product manager's evaluations separately; they can also assess usability, explainability and product suitability. Participant recruitment counts and availability must be reported, not invented or inferred from the number of plan comparisons.

Separate two tasks in the later session:

- **Interface usability:** whether participants can understand, reorder and toggle preferences, identify the all-disabled state, and interpret the resulting map. Report task completion, errors, assistance and review time.
- **Decision appropriateness:** whether participants prefer one feasible allocation over another, consider them equivalent, or find neither acceptable. Ask for reasons in ordinary operational language.

Generate a reserved pool of synthetic events using new seeds (proposed 20261031–20261034) before selecting reviewer examples. Keep these events separate from any examples used to refine scoring or explain the methods. Use the same participants, hard rules and requested ranking for each within-event comparison. Hide weighting-method names and randomize/counterbalance A/B placement. Include representative agreement cases as well as trade-off cases; do not select only dramatic examples favoring a candidate.

Explain the case facts, enabled factors and seat-layout conventions before judging plans. Include indifference, neither-acceptable and cannot-judge responses. Capture contextual reasons, fatigue and reviewer role. Report individual and role-separated results, with denominators and ties explicit. Disagreement may indicate different operational priorities rather than a faulty respondent.

These judgments may support a default appropriate to the evaluated scenarios. They do not automatically generalize to every event. If they motivate changing costs or the formula, freeze the revision and evaluate it on fresh cases rather than claiming the same judgments independently validate the tuned design. Regeneration/repair usability is separate from this initial-allocation computational study.

## 8. Deliverables, checks and execution boundary

Planned implementation deliverables:

- A dedicated rank-weighting experiment runner under `research/experiments/`, with pure formula generation, alias mapping, incremental persistence, a 120-minute outer deadline and explicit output paths. The existing preference-sensitivity runner is not an implementation of this amended protocol.
- Focused correctness checks for formula ratios at enabled counts 0–3, disabled weights, all 16 configurations, 64 logical combinations mapping to 46 vectors (24/18/3/1 by enabled count), preserved hard constraints, and independent objective recomputation. Verify deadline cleanup and execution-status handling with bounded fixtures before the timed study.
- New evidence under `docs/results/rank-weighting-initial-<run-date>/`: protocol/version, source hashes or verified snapshot, inputs/witnesses, seed/configuration manifest, alias map, event traces, placements, audits and analyses.
- Tables of common-scale component trade-offs, quality over time and sensitivity; the confirmed main-chapter package uses weighting trade-offs in Figure 4 and scoring sensitivity in Figure 5, with a sensitivity table substitution if clearer. Additional plots belong in the appendix. No forced winner table.
- A clear future-work statement that human verification is deferred after project completion and live deployment; a stakeholder instrument or collected human evaluation record is not a deliverable of this computational experiment.

Correctness checks precede pilot and main runs. A failed audit or scorer mismatch is a harness defect to investigate, not a result to discard silently. Preserve the failed record and document the corrected runner version. Continue independent valid cases only when the failure is understood well enough not to undermine them.

Keep the original 11 October evidence unchanged. Do not alter deployment policy, UI behavior, database state or unrelated in-progress application edits. Suggested implementation commit scopes are `research`, `methodology` and `results`, with separate production changes only if later authorized.

**Planning complete:** shared understanding is confirmed. The next implementation phase is to build the experiment harness, complete correctness checks and run the pilot before the main batches. Q1–Q9 need not be re-asked; any protocol amendment should update the affected section and its execution estimate.

## Related material

- [Experiment hypotheses, analysis and confirmed decision audit](experiment-hypotheses-and-analysis.md)
- [Confirmed dissertation tables and figure package](benchmark-results-visualization.md)
- [Shared experiment execution sequence, environment and JSON evidence](experiment-execution-sequence.md)
- [Solver selection and supporting benchmark](solver-selection-benchmark.md)
- [Domain glossary](../../CONTEXT.md)
- [Parameter research and previous experiment design](../methodologies/preference-parameter-study-2026-10-11.md)
- [Recorded previous results](../results/preference-sensitivity-2026-10-11/results.md)
- [Preference elicitation template](../methodologies/preference-elicitation-template.md)

No new measurements or stakeholder-validation outcomes are asserted in this document.
