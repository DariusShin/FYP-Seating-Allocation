# Solver selection and supporting benchmark

Date: 12 October 2026 (Asia/Kuala_Lumpur).

Status (implementation update, 18 October 2026): **solver harness implemented; development checks/pilots separate; main execution pending**. Q10–Q13 confirm the figure package, allow shorter-budget conclusions, expand the solver-study runner ceiling to 90 minutes, and add the fixed 30/60-second subset and four prototype timing checks. The five-second primary benchmark and weighting protocol remain intact. See the [hypotheses, analysis and decision audit](experiment-hypotheses-and-analysis.md). The [implementation guide](../../research/experiments/solver_benchmark/README.md) provides setup, preflight, pilot, run and report commands. See the [development validation record](../results/solver-benchmark-setup-2026-10-18.md); development observations are not main-study results.

## Confirmed decision: Q1

The dissertation will justify the solver choice as follows:

> CP-SAT was selected because it expresses PJKIT's compulsory seating constraints and configurable weighted preferences and achieves measured performance on the evaluated events, supported by a small comparative benchmark where feasible.

The intended contribution is a justified engineering choice. It is not a claim of universal algorithm superiority. Report results that qualify or challenge the choice as well as results that support it. Because CP-SAT is already implemented, describe subsequent experiments as evaluation of the selected approach rather than implying that a completed benchmark originally determined its selection.

The proposed comparator set is the existing OR-Tools CP-SAT solver, a constraint-aware greedy method, and a MIP solver. The user confirmed using one experiment harness with shared inputs, scoring, independent placement validation and timing conventions. Separate method adapters may be needed, but they must solve the same declared problem. A comparator that cannot encode the full policy cannot be silently substituted with a relaxed problem.

Use the terminology “OR-Tools CP-SAT, based on lazy clause generation” in the dissertation; LCG is part of the solver architecture. An integer-programming formulation and the MIP solver used to solve it must be identified separately.

## Confirmed decisions: Q2–Q3

- **Q2 — Separate execution allowance, amended by Q12:** the user selected a separate allowance, initially provisionally 30 minutes. Q12 A supersedes that limit with **90 minutes** covering primary benchmarking, the longer-budget subset, four prototype checks, preparation/pilot, overhead and reporting. Preserve the weighting study's separate two-hour cap. Implementation effort is outside runner execution time.
- **Q3 — Representative preference coverage:** the user selected B, a small representative selection of enabled/ranked configurations with the current-ratio weighting rule fixed. Q4 below freezes their definitions. The all-disabled case measures feasibility/runtime, with zero ordinary preference objective; it cannot establish better weighted preference quality.

## Confirmed decisions: Q4–Q6

**Q4 — Case coverage, amended by Q9:** reuse the weighting protocol's 12 synthetic initial-allocation events after feasibility witnesses are established and independently validated, and append the required 230-seat Emperor-heavy event below. The original 12 comprise nine size/pattern base events and three related accessibility derivatives; they are not 12 independent samples of real events. Apply four preference configurations to each of the resulting 13 events:

| Configuration | Enabled preference order |
|---|---|
| Current order | Contribution > activity > category |
| Reversed order | Category > activity > contribution |
| Two preferences | Contribution > category; activity disabled |
| Feasibility/runtime control | All ordinary preferences disabled |

Use the fixed current-ratio rule, including its compact active-rank semantics. All hard rules remain active in every configuration. Following the Q9 scale amendment, 13 events crossed with four configurations produce **52 matched cases in total**. Each of three methods evaluates those same cases, producing **156 primary method runs**, before any repetitions. These counts supersede the original 48 cases/144 runs. Deliberately infeasible cases belong to a separate correctness suite, outside the known-feasible return-rate denominator.

**Q5 — Comparator definition:** on clarification the user accepted A, the proposed SCIP MIP backend plus deterministic constraint-aware greedy with forward checks and no backtracking. The user additionally requires support from valid research studies. The evidence and adaptation boundaries are documented below. The greedy method has no repair/restarts and must not call CP-SAT or SCIP to complete its allocation. A dead end is construction failure, not proof of infeasibility.

**Q6 — Evidence and conclusion:** report hard-rule validity, common-objective quality and component means, valid-plan return rate, runtime/deadline quality, and exact-solver proof/bounds separately. Explain trade-offs. Do not invent a combined algorithm-accuracy percentage or an overall winner score without justified trade-off weights. Staff appropriateness judgments remain separate from computational metrics and experienced attendee satisfaction.

## Confirmed decision: Q7 — Base timing protocol

The user accepted this base protocol; Q12/Q13 explicitly amend the overall ceiling and supplementary coverage below:

- Five seconds of search per method per matched case. Greedy stops when complete or at a dead end; it is not made to consume unused time. Its ordering, candidate scans and forward checks count as search work.
- One primary run per method/case: following Q9, 52 cases × three methods = 156 runs, allocating at most 780 seconds (13 minutes) of search. No seed repetitions; do not claim measured runtime variability across repetitions.
- Sequential runs in a recorded shuffled order, one worker for each solver, fresh solver state and no other method's incumbent or witness as a hint. Disable additional canonicalization solves.
- Record shared preprocessing, method-specific construction, search, validation and total elapsed wall time separately. Model construction is outside the five-second search allowance but inside the overall deadline; search time alone is not application latency.
- Separate **90-minute overall runner ceiling**, shared with the confirmed longer-budget comparison and prototype checks. The previous 30-minute ceiling and 5/20/5-minute subdivision are superseded. Reserve the final five minutes for aggregation/reporting; preparation, pilot and measured batches must fit the preceding 85 minutes. Development and later interpretation are outside runner execution time.
- A pilot checks overhead and completion projections before the main batch. Stop with diagnostics if correctness/preparation fails or the projection does not fit; do not silently shorten runs or drop difficult cases.
- Use a monotonic deadline and outer child-process watchdog covering construction, search and reporting. End measured-batch work by minute 85 to preserve reporting time; do not start a run that cannot receive its declared allowance plus the pilot-estimated overhead within the remaining batch window. Preserve partial records and the full manifest, with `not_started`, `interrupted_by_deadline` and `validation_pending` distinct from solver status. Only independently validated complete plans enter cost comparisons.
- First internal feasible-incumbent time is an additional measurement only if comparable event instrumentation is supported by both solver adapters. Otherwise mark it unavailable and report observed valid-plan return time; do not relabel final solve-return time as first-incumbent time or add repeated solves to simulate a trace.

The five-second limit is a project resource choice, not a literature-established optimum or a validated staff waiting-time requirement. Q7 does not extend the weighting study's two-hour cap.

## Confirmed Q11–Q13 — Budget sensitivity and prototype timing

**Q11:** the experiment may conclude that a shorter allowance is sufficient on the evaluated cases, with 60 seconds retained only as a conservative maximum. Do not design or reinterpret the study to force the conclusion that 60 seconds is necessary.

**Q12 A:** the solver-study runner ceiling is 90 minutes. **Q13:** retain all 156 primary runs at five seconds and add fresh 30- and 60-second comparative runs on this predeclared subset:

| Larger event | Registration / physical-seat coverage |
|---|---|
| Full-size mixed profiles | 80 Emperor / 40 Merit / 32 Bodhi; 152 registrations, 232 seats |
| Full-size contribution/activity conflict | Same tier counts and demand; distinct predeclared profile pattern |
| Full-size tied contributions, varying activity | Same tier counts and demand; distinct predeclared profile pattern |
| Emperor-heavy mixed profiles | 99 Emperor / 19 Merit / 13 Bodhi; 131 registrations, 230 seats |

Cross these four events with the three preference-active configurations in Q4, yielding **12 matched cases**. The all-disabled configuration and accessibility derivatives are not in this extension. Reuse their existing primary five-second observations; do not rerun them merely for a budget plot. At each additional allowance, run all three methods with fresh state, the same fixed objective and inputs, one worker, no hints and canonicalization disabled. Freeze and record search/order seeds before execution; do not select cases based on short-budget results.

This adds **12 × three methods × two budgets = 72 runs**, allocating **12 × three × (30 + 60) = 3,240 seconds (54 minutes)**. Total comparative coverage is **228 runs and 67 minutes of allocated search**. Greedy still exits on completion or construction failure; extra budget does not introduce backtracking, repair or restarts. No ten-second batch or repeated timing trials are included.

Use separate fresh runs at 5/30/60 seconds and describe their outputs as **budget-comparison endpoints**. Installed CP-SAT supports incumbent callbacks, but the installed OR-Tools `pywraplp.MPSolver` SCIP interface does not expose comparable Python incumbent callbacks. Do not promise intermediate SCIP maps from one 60-second trajectory, substitute separate runs for convergence observations, force monotonic curves or relabel final return time as first-incumbent time. A different instrumentation adapter would require verification and an explicit change if it alters the protocol.

Analyze the **5→30** and **30→60** contrasts for each method/configuration on the same 12-case subset, with four events per configuration. Record additional/lost valid maps and cost changes only among both-valid pairs; retain no-map outcomes and unavailable comparisons. Keep proof/bound improvements separate. Do not pool 52-case primary rates with 12-case longer-budget rates or use all-disabled costs as quality evidence. The [hypothesis plan](experiment-hypotheses-and-analysis.md) specifies H1/RQ1/H3 and permitted conclusions.

### Four separate prototype checks

Run the same four larger events in the current/default order (contribution > activity > category), using the actual prototype's initial-allocation path and configured solver settings, currently **60 seconds, eight search workers, canonicalization enabled** in the default request fixture. Preserve settings rather than altering production policy. Use explicit local synthetic requests and a fresh isolated research SQLite store per event: the maintained service saves successful solves, so it must not point at an operational store. Do not publish or modify live records. Save a returned map and external audit per event. These are verification observations under a different configuration, not additional matched solver results.

The current implementation starts its deadline at `solve()` entry: input validation, legal-option checks and model construction consume the configured allowance, and optimization/canonicalization share the remaining time. Final placement validation and `format_result()` follow the deadline checks. Existing `end_to_end_seconds` is sampled before formatting, so it does not measure complete service return. The web subprocess watchdog is 330 seconds, not a 60-second response guarantee. These facts were checked in `services/seating/src/seat_solver/production/production.py`, `service.py`, the default `data/production_request.json`, and `apps/web/src/lib/production-service.ts`; record the measured source/configuration hashes in the run manifest.

Instrument a fresh local service subprocess from invocation with the complete synthetic request through parsed final JSON response, then record the research audit separately and total through that audit. Include process startup, request/response serialization, service validation and access/persistence to the isolated research store in this return boundary; identify those overheads separately where available. Browser/network and remote production-database latency are outside this local measurement. Preserve internal phase timings and canonicalization-complete status. Do not use the pre-format internal statistic as the complete-result timer. Return time may exceed 60 seconds because the configured allowance is neither pure search time nor a hard service deadline. This is local prototype service timing, not a live user-interface latency claim.

Four checks allocate **four minutes of configured allowance plus pipeline overhead**. With the 67-minute comparative search allocation, nominal allowances sum to 71 minutes, leaving 19 minutes inside the 90-minute ceiling for preparation/pilot, construction, validation, persistence and reporting. This is a feasibility projection, not a guaranteed completion time. Include the prototype path and longer-budget overhead in the separate-seed pilot projection. Execute primary comparison, longer-budget batches in recorded balanced order, then prototype checks; preserve all planned records if the outer deadline stops execution. If the projection cannot fit, propose an amendment before the main batch rather than silently shortening limits or dropping difficult cases.

## Confirmed Q9 — Registration-based scale amendment

The user requires a case occupying 230 seats with Emperor registrations at least 75%, approximately 15% Merit and 10% Bodhi, and asks whether the five-second budget actually permits a complete seating-map result. In Q9 the user confirmed A, percentages based on registration counts, selecting the proposed 99 Emperor / 19 Merit / 13 Bodhi composition. The event is included in the amended plan and the user subsequently confirmed Q8 as the first draft. The implemented preflight saves independently audited feasibility witnesses; main-study timing evidence remains pending.

The original full-size case already demands all 232 available seats (80 Emperor, 40 Merit, 32 Bodhi registrations; 152 registrations total). Thus the study was not restricted to small events, but that case has only 52.63% Emperor registrations and does not meet the newly requested mix.

For physical seat demand S and tier registration counts E, M, B, use S = 2E + M + B and N = E + M + B. At exactly 230 occupied seats, the confirmed registration-based rounding is:

| Tier | Registrations | Physical seats | Share of registrations |
|---|---:|---:|---:|
| Emperor | 99 | 198 | 75.57% |
| Merit | 19 | 19 | 14.50% |
| Bodhi | 13 | 13 | 9.92% |
| Total | 131 | 230 | 100% |

This leaves two empty seats in the current 232-seat venue. Exact 75/15/10 registration proportions require counts 15k/3k/2k and 35k physical seats; 230 cannot match them exactly. The confirmed rounding maintains Emperor at least 75% of registrations. Do not interpret these proportions as physical seat/attendee shares.

Append one Emperor-heavy mixed-attribute event, preserving the existing 12. This produces 13 events × four configurations = **52 matched cases and 156 primary method runs**, allocating at most 13 minutes of search at five seconds per run. Freeze a separate input seed and certify a full feasibility witness, including pairs, tier order and packing, before including it in the known-feasible denominator. The weighting study's inputs and cap are unchanged by this supporting-benchmark amendment.

**Completion versus proof:** five seconds is a common experimental cutoff, not a promise of a returned map. A valid incumbent must assign every eligible registration its complete bundle and pass all hard-rule checks; it need not have an optimality proof. A timeout with no incumbent means no complete map was obtained. The earlier [full-size CP-SAT sensitivity results](../results/preference-sensitivity-2026-10-11/results.md) returned 94/102 full-size valid plans at a 1.5-second search limit, with eight UNKNOWN outcomes. This is prior evidence that some large cases can return complete maps quickly, not verification of five-second behavior, the new Emperor-heavy composition, or another comparator.

Before the main experiment, include a separate-seed near-capacity Emperor-heavy input in the development pilot. Assess valid-map return, solver/model overhead, longer-budget/prototype overhead and fit within the confirmed 90-minute ceiling. The Q13 extension is already declared; failures at five seconds remain primary evidence rather than triggering automatic retries or replacement of primary records. Any further revision requires a documented amendment. Do not shrink the event, grant one method extra unreported time, replace failed cases or exceed the ceiling. More time cannot guarantee that irreversible greedy escapes a construction dead end. Pilot work counts within the runner allowance.

## Research support and adaptation boundaries

Checked 12 October 2026 using Undermind metadata discovery, primary author manuscripts, publisher/proceedings records and solver authors' reports. Publication venue and study relevance must be assessed separately: an arXiv or Optimization Online record is citable research but does not itself establish peer review.

| Comparator/design choice | Primary evidence | What it supports and what it does not |
|---|---|---|
| Constraint-first seating construction | Lewis & Carroll (2016), *Creating seating plans: a practical application*, *Journal of the Operational Research Society* 67(11), 1353–1362. [DOI](https://doi.org/10.1057/jors.2016.34), [author manuscript](https://rhydlewis.eu/papers/LewisCarroll.pdf), §3.1. Peer-reviewed journal article. | DSATUR selects highly constrained guest groups first. The complete method also uses TABUCOL repair and tabu optimization and can increase table count. It supports constructive seating heuristics, not a claim that our irreversible greedy is their complete algorithm or DSATUR. |
| Forward checking | Haralick & Elliott (1980), *Increasing tree search efficiency for constraint satisfaction problems*, *Artificial Intelligence* 14(3), 263–313. [DOI](https://doi.org/10.1016/0004-3702(80)90051-X), [author-hosted journal paper](https://haralick.org/journals/haralick_elliot.pdf). Peer-reviewed journal article. | Supports forward checking and fail-first reasoning in binary CSP tree search. Borrowing these checks into greedy construction does not confer completeness or the paper's measured speedups. Undermind's internal `Har79` metadata conflates the earlier conference version with the journal DOI; use the journal's verified 1980 year and 263–313 pages. |
| Greedy seating baseline alongside IP | Ipsen et al. (2026), *Beyond Manual Planning: Seating Allocation for Large Organizations*. [Preprint](https://arxiv.org/abs/2602.05875), §3.2, Algorithm 3. | Direct precedent for greedy versus integer-programming seating allocation. Its capacity/regret construction, k-means++ initialization and iterative central-seat updates differ from the proposed deterministic PJKIT method. Supplementary preprint evidence, not peer-reviewed validation of our exact baseline. |
| Full-policy integer-programming comparator | Lewis & Carroll (2016), above, §5. | Compares a seating heuristic with an equivalent IP formulation under time limits, using objective quality, runtime and proof information. Their backend is XPressMP; do not claim they evaluated SCIP or PJKIT's physical seat constraints. |
| SCIP backend | Hojny et al. (2025), *The SCIP Optimization Suite 10.0*. [Authors' technical report](https://arxiv.org/abs/2511.18580), [university-hosted report](https://www.or.rwth-aachen.de/files/research/repORt/scipopt-100.pdf). | Documents the solver family/version used by the installed backend. It is solver technical evidence, not a seating benchmark or proof of superiority over CP-SAT. Do not assume the default wrapper enables the report's optional rational-exact mode. |
| CP-SAT identity | Perron, Didier & Gay (2023), *The CP-SAT-LP Solver (Invited Talk)*, LIPIcs CP 2023, 3:1–3:2. [Proceedings](https://doi.org/10.4230/LIPIcs.CP.2023.3). | Supports the LCG architecture, linear relaxation and solver terminology. This short invited-talk paper is not a PJKIT seating-performance comparison. |

Suggested methodology wording (future tense until implemented):

> A PJKIT-specific deterministic constructive greedy baseline will be adapted from constraint-first seating heuristics and forward-checking principles from constraint-satisfaction research. An equivalent integer-programming formulation solved with SCIP will provide a second comparator. These methods will use the same inputs, hard rules, objective coefficients and placement audit as CP-SAT. The adapted greedy baseline is not a reproduction of a published solver.

### Proposed reproducible greedy specification

This is a transparent project adaptation supported by the above principles; freeze its exact pseudocode and rules before the main benchmark, without tuning on main results:

1. Share legal whole-registration seat-bundle generation and fixed integer option costs with both exact methods. Never split pairs or drop accessibility/priority/packing requirements.
2. Recompute each unassigned registration's remaining options consistent with assignments already committed. Select the registration with the fewest remaining options (fail-first); break ties by a fixed recorded registration identifier. This is not DSATUR's saturation rule.
3. Scan that registration's options by increasing common weighted cost, breaking ties by a fixed seat-bundle order. Tentatively test candidates before committing one; rejecting a candidate before commitment is not backtracking over committed assignments.
4. Reject candidates that violate already-decidable hard rules, empty another remaining domain, or fail declared inexpensive necessary capacity/row/pair/accessibility checks. Specify each check against the frozen policy. Partial gaps must not be treated as final packing violations when later assignments could fill them.
5. Commit the first passing candidate and never undo a committed placement. If no candidate passes, record `CONSTRUCTION_FAILED`; if the budget expires, record a timeout. Necessary checks and nonempty individual domains do not guarantee a jointly feasible completion.
6. Audit and rescore the complete output using the shared placement validator. Invalid outputs are validation failures, not low-quality feasible solutions. Retain diagnostics; never compare partial-plan costs with valid complete costs.

The MIP adapter must express the same compulsory rules and option costs, with its integer solution independently audited after numerical extraction. Tiny cases with independently enumerated solutions check formulation and objective equivalence before performance runs. A failed equivalence check blocks the benchmark rather than justifying relaxation of a comparator's problem.

## Relationship to existing research

The [algorithm literature note](../methodologies/seating-algorithm-research-2026-10-08.md) supports screening comparator families. The [rank-weighting protocol](rank-weighting-experiment.md) studies weighting rules while holding CP-SAT fixed. Its confirmed two-hour runner cap is unchanged. Q12 establishes the separate 90-minute allowance for the solver studies and prototype checks.

To attribute benchmark differences to solver methods, hold the scoring definitions, category matrix, preference configuration and objective coefficients identical within every matched comparison. Do not mix a changed weighting method with a changed solver and attribute the result solely to the solver.

Computational quality means fit to the declared scoring model. On 12 October 2026 the user excluded human evaluation from the dissertation experiments and deferred operational verification until after FYP completion and live deployment. It is future work, not a required benchmark phase. Neither the solver benchmark nor the weighting study establishes experienced attendee satisfaction or empirically validates PJKIT's numerical preferences.

Keep **solution cost and runtime** as core comparison dimensions, following the methodological precedent of Lewis & Carroll's seating comparison (§§4–5). Cost here means the matched weighted preference penalty, not money. Record search wall time and total allocation wall time with phase boundaries; comparable process CPU time is an optional separately labelled supplement. The [reporting plan](benchmark-results-visualization.md#explicit-cost-and-runtime-measurements) defines these quantities and distinguishes the paper's CPU timing from this benchmark's primary wall-clock timing. No 600-second extension is added by citing their study.

## Execution order, environment and evidence

Follow the [shared execution sequence and JSON recording guide](experiment-execution-sequence.md). These Markdown documents are specifications. The [solver runner](../../research/experiments/solver_benchmark/README.md) is implemented; the separate weighting runner remains pending. After correctness checks, frozen inputs/feasibility witnesses and separate development pilots, run this solver benchmark before the rank-weighting study. Final operational weights are not a prerequisite: this benchmark deliberately uses the fixed current-ratio rule as a control. The later weighting study varies formulas while holding CP-SAT fixed; synthetic results characterize trade-offs rather than establish PJKIT's true preferences.

Use the user's M4/24 GB macOS device as the primary measurement environment, subject to pilot resource checks. Execute sequentially with one worker, consistent power conditions and pinned software. Colab is suitable for sharing/analysis or a separately labelled portability run; do not mix hardware environments within a matched timing comparison or pool their timings. The guide records the current official Colab limitations and persistence requirements.

Save a separate JSON evidence bundle under `docs/results/solver-selection-benchmark-<run-date>/`, using a unique run suffix when needed. Include the full manifest, frozen inputs and witness audits, per-run complete maps/statuses/validation/costs/bounds/phase timings, separate pilot records and derived summaries. Tag primary, budget-sensitivity and prototype records separately, with budget, workers, canonicalization and timer boundaries. Persist runs incrementally and preserve failures, missing coverage, software/source hashes and timing provenance. Keep the 90-minute overall deadline separate from the weighting study's 120-minute deadline; no concurrent execution or uncounted extension is included.

If later stakeholder-informed weights or scoring differ materially from this reference, use a separately declared targeted solver recheck rather than rewriting the original benchmark. Its budget is outside these two planned studies.

## Protocol safeguards and interpretation

The [confirmed result tables and dissertation figure plan](benchmark-results-visualization.md) maps these measurements to reporting views and identifies unsupported visual claims. Q10 confirms five analytical figures across solver/budget/weighting studies plus the near-capacity illustration. Its reporting does not add timed runs beyond Q13.

- Keep the supporting benchmark small and focused on initial allocation; absence repair has a distinct movement hierarchy and needs its own experiment.
- Use the existing current-ratio reference as a fixed weighting rule for the solver comparison. This is an experimental control, not validation of its numerical policy ratios.
- Use Q4's four frozen configurations; do not cross every solver with every candidate weighting formula.
- Reuse Q4's frozen synthetic event inputs with independent validation and recorded layout/policy/scoring versions. Identify reused events and their limited independence.
- Report complete valid-solution return rate, component costs, common-objective incumbent cost, available bounds/proof status and total time with preparation/validation overhead separately identifiable. First-incumbent time is optional only under the comparable-instrumentation rule; final valid-plan return time is not its substitute. Do not compare infeasible partial plans with complete valid plans on cost alone.
- Keep end-to-end experiment runtime limits distinct from per-solve budgets and from any future staff waiting-time requirement.
- Test model/scoring equivalence before timed experiments, including tiny cases with independently known solutions. Record unknown outcomes and baseline failures rather than treating them as infeasibility proofs.

## Confirmed Q8 — First-draft shared understanding

The user confirmed Q8's first draft: 13 events/52 matched cases/156 primary runs, CP-SAT/greedy/SCIP, a five-second reference and separate validity/quality/time/proof reporting. Q10–Q13 subsequently confirm the reporting package and explicitly supersede the original 30-minute ceiling with 90 minutes, adding 72 longer-budget runs and four separate prototype checks. The [decision audit](experiment-hypotheses-and-analysis.md#grillme-decision-audit-and-remaining-work) records all answers and closes the current GrillMe session with no unanswered design question. Implementation, correctness checks, feasibility witnesses and development pilots are tracked in the [development validation record](../results/solver-benchmark-setup-2026-10-18.md). Main execution remains pending; protocol confirmation is not evidence of benchmark success. Later substantive changes require a recorded amendment. The settled weighting-study decisions remain intact.

The experiment worktree now has a local virtual environment with a checked dependency lock and verified SCIP backend. The setup script requires Python 3.12 or newer. The controlled CP-SAT adapter uses the maintained builder; the separate SCIP formulation implements the same full policy. Exhaustive tiny physical-assignment oracles check feasibility and objective agreement. Backend availability and tiny-case checks do not establish comparative performance on the main events.

Base case counts and timing were settled in Q4/Q7; Q9 amends coverage with the confirmed registration-based 230-seat event. Record actual software versions, input/scoring hashes, seeds, greedy pseudocode, timing boundaries and correctness outcomes with the implementation manifest. No benchmark results or winner are asserted here.
