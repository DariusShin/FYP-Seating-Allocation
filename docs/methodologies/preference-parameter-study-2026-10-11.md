# Justifying PJKIT preference parameters

Research and experiment date: 11 October 2026.

## Conclusion and evidence status

The current weights and category-zone costs are mathematically admissible **provisional design parameters**. They are not yet validated PJKIT preferences. The student explicitly confirmed that neither stakeholder calibration nor earlier experiments established 40/30/20 or the matrix entries. A defensible dissertation can retain these as a baseline, document their assumptions, compare alternatives, and report sensitivity. It cannot turn synthetic performance into evidence that PJKIT prefers those trade-offs.

Three distinct claims need separate evidence:

| Claim | Evidence needed | Current status |
|---|---|---|
| The implementation computes the stated objective and obeys hard rules | Equation/code comparison, coefficient checks, independent placement validation | Reviewed; additional checks are included in the executed study |
| Conclusions are stable across plausible parameter choices | Paired experiments on the same instances, component costs, bounds and sensitivity | The accompanying synthetic study provides preliminary evidence |
| Numerical trade-offs reflect PJKIT's preferences | Recorded stakeholder judgments and evaluation on choices not used to fit parameters | Not established |

Synthetic participants are permitted according to the student's statement of Netizen eXperience's authorization. The generator replaces all participant records; no registration database is accessed. Synthetic distributions are controlled stress scenarios, not estimates of PJKIT's real participant population.

## Research supporting the methodology

This is a focused search using Undermind, publisher records, an author manuscript and official documentation, not a systematic review. Sources support methods of justification; none supplies PJKIT's correct constants.

| Source and access level | Relevant finding | Use in this project |
|---|---|---|
| Department for Communities and Local Government (2009), *Multi-criteria analysis: a manual*, full official manual, sections 6.2.9–6.2.14 | Weights depend on the preference difference between defined scale endpoints; swing weighting elicits these differences. Sensitivity checks investigate effects of uncertain scores and weights. | Use explicit score anchors and stakeholder trade-off questions. Do not ask only which criterion sounds most important. [Official manual](https://assets.publishing.service.gov.uk/media/5a790545e5274a2acd18b975/1132618.pdf) |
| Barron and Barrett (1996), *Decision Quality Using Ranked Attribute Weights*, publisher abstract | Rank-order centroid (ROC) performs well against the other rank-based formulas in their study. | Include ROC as a literature-based alternative when only an ordering is available; its results do not establish PJKIT-specific superiority. [DOI](https://doi.org/10.1287/mnsc.42.11.1515) |
| Burk and Nehring (2022 online; 2023 issue), *An Empirical Comparison of Rank-Based Surrogate Weights in Additive Multiattribute Decision Analysis*, publisher abstract | In their real elicited-weight comparison, sum reciprocal performed best on average; ROC was relatively poor. | Evidence against claiming one surrogate method is universally best. Rank reciprocal and **sum reciprocal are different methods**; our experiment implements the former, not the latter. [DOI](https://doi.org/10.1287/deca.2022.0456) |
| Kunsch and Ishizaka (2019), *A note on using centroid weights in additive multi-criteria decision analysis*, full author manuscript | Comparative results depend on how assumed “true” weights are generated. They examine hit rate and ranking agreement. | Do not generate artificial truth using the current weights and then claim that recovering them validates the weights. [Author manuscript](https://pure.port.ac.uk/ws/files/13178142/ISHIZAKA_2019_cright_EJOR_Short_Communication_A_note_on_using_centroid_weights_in_additive_Multi_Criteria_Decision_Analysis.pdf), [DOI](https://doi.org/10.1016/j.ejor.2019.02.021) |
| Bana e Costa and Vansnick (1994), *MACBETH—An Interactive Path Towards the Construction of Cardinal Value Functions*, publisher abstract | Qualitative pairwise differences in attractiveness can be converted to numerical scales through linear programming, with inconsistency feedback. | A principled approach to obtaining category-zone penalty gaps. A simple questionnaire inspired by this idea is not a full MACBETH implementation. [DOI](https://doi.org/10.1111/j.1475-3995.1994.00325.x) |
| Lewis and Carroll (2016), *Creating seating plans: a practical application*, full author paper | Their implemented seating system uses preferences and optimization; its experiments compare solution cost and runtime against IP. | Seating-specific precedent for explicit preference modeling and cost/time evaluation. Its table-assignment penalties cannot calibrate PJKIT's physical-zone preferences. [Paper](https://rhydlewis.eu/papers/LewisCarroll.pdf), [DOI](https://doi.org/10.1057/jors.2016.34) |
| Gurobi, *Multiple Objectives*, official implementation documentation | Supports blended weighted objectives and hierarchical priorities. | Independent implementation precedent for distinguishing within-stage preference weights from strict movement/distance priorities. Our experiments use CP-SAT, not Gurobi. [Documentation](https://docs.gurobi.com/projects/optimizer/en/current/features/multiobjective.html) |

Additional relevant lead: Roberts and Goodwin (2002), *Weight approximations in multi-attribute decision models*, DOI [10.1002/mcda.320](https://doi.org/10.1002/mcda.320). Undermind's abstract distinguishes point-allocation from unrestricted direct-rating assumptions; the [authors' university record](https://researchportal.bath.ac.uk/en/publications/weight-approximations-in-multi-attribute-decision-models/) verifies bibliographic details. Full text was not inspected, so this report does not rely on unverified numerical results from it.

## What 40/30/20 means mathematically

For fixed input data and the same normalized costs, write

\[
F_w(z)=w_C C(z)+w_A A(z)+w_Z Z(z),\qquad
C(z)=\sum_{p,o}c^C_{po}z_{po},
\]

with analogous sums for activity and category. Smaller values are preferred. The production scorer computes each option component on an integer 0–100 scale, before aggregation.

Multiplying every weight by the same positive constant preserves the set of exact minimizers. Therefore 40:30:20 is equivalent to 4:3:2. This algebraic equivalence does not guarantee identical timed-out incumbents or search times. Its normalized shares are **44.44%, 33.33%, 22.22%**, not 40%, 30%, 20%. The configured fourth rank weight, 10, is unused when there are three enabled criteria. These percentages describe coefficients, not realized satisfaction or contributions to the final objective.

For two feasible plans, the trade-off is

\[
\Delta F=40\Delta C+30\Delta A+20\Delta Z.
\]

For example, reducing C by 3 and increasing A by 4 is a tie if Z stays constant. This is a checkable hypothetical interpretation, not evidence that PJKIT accepts that exchange. A higher weight does not create absolute priority. Initial preferences remain compensatory; absence movement uses a separate lexicographic hierarchy.

| Experimental profile | Integer weights C:A:Z | Interpretation |
|---|---|---|
| Current | 4:3:2 | Existing provisional ratio |
| Equal | 1:1:1 | Neutral comparison, not a claim of fairness |
| Rank sum | 3:2:1 | Linear decrease with preference rank |
| Rank reciprocal | 6:3:2 | Weights proportional to 1/rank |
| ROC | 11:5:2 | Standard three-criterion ROC ratios |
| Flatter | 36:30:24 | Local perturbation toward more category influence |
| Steeper | 44:30:16 | Local perturbation toward more contribution influence |
| Three ablations | 1:0:0, 0:1:0, 0:0:1 | Isolate each objective; not proposed deployment policies |

For K ranked criteria, rank sum is proportional to K-j+1, reciprocal to 1/j, and

\[
w_j^{ROC}=\frac1K\sum_{k=j}^K\frac1k.
\]

For K=3 this gives 11/18, 5/18, 2/18. Ranking alone does not uniquely identify any of these cardinal weight vectors. The study assumes the experimental order contribution, activity, category; it does not establish that PJKIT confirmed that ordering. Production supports other enabled orders, which need their own evaluation.

## How to justify category-zone costs

The Monastic row 0/2/4/8 contains both an order and cardinal differences: the last increase is twice either earlier increase. Those gaps need separate justification. The current matrix also implies differing strengths across categories because it uses one global maximum: Monastic's 0–8 span is four times General Devotee's 0–2 span before rounding. Establishing only each category's zone ranking would not justify that cross-category difference.

For a single seat, current category normalization is

\[
c^Z_{ps}=H(100Q_{k_p,zone(s)},Q_{max}),\qquad Q_{max}=8.
\]

Thus Monastic's normalized penalties are 0,25,50,100. Pairs use the mean of the two seat costs before rounding. Doubling **every** matrix entry also doubles the global maximum and leaves all normalized costs unchanged. Increasing a single entry can instead change the global maximum and therefore rescale other entries. It is incorrect to assess category penalties without their normalization rule.

The executed study examines the base matrix, squared entries (larger relative gaps near the worst penalties), ordinal equal-step entries within each category with ties preserved, and a zero-category ablation. Squared and ordinal variants preserve each category's ordering, but change cardinal gaps and cross-category relative strength. They test structural uncertainty, not only small numerical noise. Their raw totals are evaluated on the original matrix as well as their own matrix.

Proposed elicitation for this project:

1. Show the actual zone layout and confirm rankings and ties for each category, including whether zone preferences depend on accessibility or another condition.
2. Define common best/worst reference situations. Ask how much worse each transition is, using concrete placements; record the response and uncertainty. Do not assume independent per-category 0–100 rescaling preserves the current cross-category trade-offs.
3. If only ordinal information is available, use a disclosed surrogate scale and compare plausible alternatives. If respondents give pairwise difference judgments, consider a full MACBETH workflow or explicitly label a simpler method as a project adaptation.
4. Elicit criterion weights after fixing the component scales. Compare reductions in penalty over specified ranges using feasible examples; revise inconsistent or misunderstood judgments.
5. Check the resulting parameters against previously unseen feasible plan pairs. Record stakeholder role, date, rationale and disagreement; stakeholder endorsement is distinct from student design choice.

This protocol is a proposed application of the research to PJKIT. It has not been carried out with PJKIT and should not be described as an interview result.

## Executed synthetic study

Source: `research/experiments/preference_sensitivity.py`. Data, manifests, solutions and objective bounds: `docs/results/preference-sensitivity-2026-10-11/`. The recorded manifest lists source paths from the pre-relocation `experiments/` location; see the bundle's relocation note. The companion `results.md` summarizes the recorded outcomes.

The experiment uses the current production hard-constraint builder and row pruning. It replaces only the objective coefficients in memory. Every returned placement is checked by the separate production placement validator. An independent Decimal-based calculation checks every precomputed normalized option vector against the production scorer. Doubling all category entries is checked on every option, not inferred from a few selected plans.

The design crosses three sizes with three participant patterns and two fixed data seeds, yielding 18 synthetic instances:

| Size | Emperor / Merit / Bodhi registrations | Registrations | Physical seat demand |
|---|---|---|---|
| Small | 8 / 8 / 8 | 24 | 32 |
| Typical fixture size | 56 / 24 / 16 | 96 | 152 |
| Full venue | 80 / 40 / 32 | 152 | 232 |

Patterns: the repository's mixed random generator; activity inversely related to contribution within each tier to expose conflict; and tied contributions within each tier while activity varies. Categories are sampled by the generator. No registration requires accessibility in this study. Each instance uses 17 configurations: ten weight profiles on the base matrix; current/equal/ROC weights on each of squared and ordinal matrices; and current weights with zero category cost. Total planned executions: 306.

All solves use OR-Tools 9.15.6755, one worker, fixed solver seed 20261011, and a 1.5-second search budget per configuration. Input seeds are 20261011 and 20261012. Objective models are reused, but each solve uses a fresh solver, no carried solution hint, and no post-optimal canonicalization. Build time is recorded separately and shared across configurations. The experiment measures search time, not application end-to-end latency. The manifest records Python/platform versions and source hashes.

Measures: complete validated solution count; OPTIMAL/FEASIBLE/UNKNOWN/INFEASIBLE status; own-objective incumbent and bound; search time; and all three component totals scored under a common reference matrix. For minimization,

\[
g=\frac{UB-LB}{\max(1,|UB|)}
\]

is the reported relative gap (bounded below by zero for numerical noise). A different objective's UB is not comparable as a quality score. The full logs retain each run's weights and matrix.

To detect meaningful sensitivity despite multiple optimal assignments, the analysis evaluates the baseline plan under the alternative objective. If a valid alternative plan has strictly lower cost under that same objective, the baseline is demonstrably suboptimal there, even if the alternative's global optimum is not proved. If the alternative optimum is proved and the baseline has the same cost, the baseline also remains optimal. An unresolved tie with an unproved incumbent establishes neither claim. Merely obtaining different seat maps is insufficient evidence of parameter sensitivity.

These are diagnostic experiments, not a parameter-selection competition. The three single-objective runs reveal trade-offs; without maximizing each component they do not establish its full attainable range. The two seeds are illustrative paired replications, insufficient for broad statistical generalization or runtime rankings. Exact reruns near a wall-clock deadline can return different incumbents on a different machine despite a fixed seed.

### Recorded outcomes

The completed experiment ran 306 solves across 18 instances in approximately 343 seconds, including data generation and checks. There were 178 OPTIMAL results, 119 FEASIBLE results without proof, and 9 UNKNOWN results without an incumbent. All 297 returned allocations passed placement validation. Independent calculations matched 248,200 option-cost vectors, and uniform category-matrix scaling checks passed.

Among ten paired cases with a proved current baseline and an available equal-weight solution, the selected baseline became strictly worse under equal weights in eight cases; in two it remained proved optimal. For the ordinal category matrix with current weights, the selected baseline was strictly worse in all ten eligible comparisons. These counts concern this designed test suite and the returned baseline plans, not a population estimate or a claim about every possible tied baseline optimum.

For the 24-registration mixed instance with seed 20261011, the current weights produced component totals (407,617,492); ROC produced (388,635,530), ordered contribution/activity/category. Both were proved optimal for their own objective. ROC reduced contribution penalty while increasing the other two penalties. This illustrates an actual trade-off; it does not establish that ROC is preferable for PJKIT.

Detailed counts, proof-conditioned comparisons and the worked-example table are in [the generated results](../results/preference-sensitivity-2026-10-11/results.md).

## Interpretation and subsequent validation

Hard tier/contribution ordering and compulsory packing already determine many allocation properties. Insensitivity can indicate constrained freedom, not well-calibrated weights. Conversely, demonstrated cost trade-offs identify questions that stakeholders need to resolve; they do not identify a universally best weight vector.

Do not tune weights by asking which vector produces its own smallest weighted total. Those totals use different units and changing weights changes the definition of success. Likewise, training a synthetic “expert” on 40/30/20 and measuring agreement with it establishes recovery of an assumption, not validation of that assumption.

For a later selection study, use independent judgments on feasible synthetic plans. Split by complete event instance before fitting, reserve unseen instances for final evaluation, and keep related plan pairs from one event in the same split. Report pairwise agreement on non-tied judgments, tie frequency, acceptance/manual-edit counts, and disagreement between reviewers. State the denominator for every agreement rate. More random seeds and accessibility stress cases can broaden coverage, but they cannot substitute for preference evidence.

The absence model uses the confirmed hierarchy

\[
\operatorname{lexmin}(M,L,F_w),\quad M=\sum_p\mu_p,
\]

where each changed registration counts once. Compulsory packing remains in the feasible set. Preference weights should affect only the final stage once earlier optima are proved and fixed. The current repair neighborhood restriction must also be reported: neighborhood optimality does not establish a full-hall minimum. This study evaluates initial allocation only; it provides no measured absence-repair performance results.

## Dissertation wording

Suggested methodology statement:

> The initial preference coefficients were selected as provisional design parameters. Their numerical values were not assumed to represent empirically established PJKIT utility. A sensitivity study compared the baseline with equal, rank-based and perturbed weight profiles, together with alternative category penalty scales, using identical hard constraints and synthetic registration instances. Returned allocations were independently validated and decomposed into criterion costs. Stakeholder calibration remains a separate validation requirement.

In Results and Discussion, cite the companion results tables, distinguish proved optima from incumbents, and describe the observed trade-offs. In limitations, state that the test population is synthetic and the preference values have not been validated against stakeholder judgments. The mathematical model is valid as a stated design model; its policy validity remains a separate empirical question.
