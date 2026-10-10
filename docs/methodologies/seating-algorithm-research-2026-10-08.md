# Seating allocation: algorithm comparisons and evaluation measures

Research date: 8 October 2026. Prepared for the PJKIT seating allocation FYP using Undermind discovery, primary papers, official solver documentation, and the current project documentation. This is a focused literature search and a proposed experimental design, not a systematic review or a set of measured project results.

## Recommendation

Compare the existing OR-Tools CP-SAT solver with **an integer-programming model solved by a MIP solver, a constraint-aware greedy baseline, and tabu search**. Add a **genetic algorithm** if a fourth comparator is practical. Simulated annealing is a defensible alternative to tabu search or GA. These choices cover exact mathematical optimization, constructive heuristics, local search, and population-based search without requiring an excessive implementation workload.

Use the same PJKIT constraints and objective for every implementation. Published algorithms require adaptation: wedding table assignment, office team allocation, exam seating, and physical-distance seat selection solve related but different problems. Their reported costs and runtimes cannot be copied into a common ranking of algorithms for PJKIT.

Call the chosen technology **“OR-Tools CP-SAT, a constraint-programming solver based on lazy clause generation, augmented with linear-programming relaxation and portfolio search.”** LCG is an underlying solving technique, rather than the complete identity of CP-SAT. The architecture reference is Perron, Didier, and Gay (2023), not a two-author reference. [R7]

## Studies supporting the comparisons

### 1. Event seating: tabu search and integer programming

**Lewis and Carroll (2016), “Creating seating plans: a practical application.”** Journal of the Operational Research Society, 67(11), 1353–1362. [R1]

The paper assigns guest groups to wedding/gala tables using a two-stage method: DSATUR construction and TABUCOL for hard separation requirements, followed by tabu search for soft preferences and balanced table occupancy. It compares the method with quadratic and linearized integer-programming formulations using XPressMP.

**Verified evaluation measures:** final objective cost, runtime, ability to obtain a feasible solution, and certificates of infeasibility/optimality. Sections 4–5 and Figures 4–5 examine approximately 225 guests in 50 groups, varying table count and constraint density. IP budgets include 5 and 600 seconds. Tabu search produced better costs than the IP approach under the short budget in these experiments.

**Application:** strong precedent for including both tabu search and MIP. Its group-preserving representation is relevant to Emperor pairs, but table groups must be adapted to physical seat bundles. The paper does not establish that tabu search outperforms CP-SAT.

### 2. Organizational seating: exact IP, greedy, clustering, and local search

**Ipsen et al. (2026), “Beyond Manual Planning: Seating Allocation for Large Organizations.”** arXiv:2602.05875; cite as a preprint. [R2]

The paper compares integer-programming seat allocation (IPSA), greedy allocation, iterative clustering (ICA/ICA++), and ICA with local IP search, within hierarchical team allocation.

**Verified evaluation measures:** central-seat distance, office distance, execution time, and qualitative assessment of layouts. Section 4 and Table 1 use three floor plans; heuristic results are averaged over 30 runs. The table caption labels timing uncertainty as **standard error**. Distances are in image pixels, and the authors explicitly avoid comparing distances across different floor plans. The 10-minute limit applies to individual subproblems, not necessarily an entire hierarchical allocation.

**Application:** supports a greedy baseline and examining quality–time trade-offs. Central-seat and office distances are not PJKIT's contribution/activity/category penalties. Warm-starting the local IP improves its incumbent objective; this alone does not establish minimum disruption to a previous event plan.

### 3. Massive events: region growing and local improvement

**Muñoz, Montaner, and López, “Seat allocation for massive events based on region growing techniques.”** The university lists a 2006 technical report, IIiA 06-01-RR. [R3]

This report constructs allocations by growing contiguous seat regions for ticket subgroups, treats unassigned groups, and applies local search. It uses Formula 1 data and experiments at a much larger scale than this project.

**Verified evaluation measures:** composite fitness, ticket/seat rank matching, group arrangement quality, optional spatial sparsity, number of unassigned tickets, time to construct an initial candidate, and additional improvement time. Section 5 and Figures 9–12 distinguish initial allocation from improvement; a reported example reduces 40 unassigned tickets to zero. Fitness is improved upward in that example, unlike PJKIT's minimized penalty.

**Application:** supports a constructive-plus-improvement comparator and separating initial-solution time from improvement time. Preserve Emperor pairs and hard ordering when adapting it. Its dispersion objective should not be imported into PJKIT's front-packed seating policy.

**Version caution:** the separate 2006 conference entry has Muñoz, Montaner, and **de la Rosa** as authors and pages 179–186. Do not combine its authors with the López report or retain the archived review's unsupported 2005 date.

### 4. Exam seating: genetic algorithms

**Ağalday and Nizam (2022), “Performance Improvement of Genetic Algorithm Based Exam Seating Solution by Parameter Optimization.”** Journal of Innovative Science and Engineering, 6(2), 220–232. [R4]

The study investigates mutation/crossover/population parameters and a modified elitism method for GA exam seating.

**Verified evaluation measures:** penalty score over generations, convergence/saturation behavior, repeated-run averages, and invalid/misplaced student assignments. Sections 3.6–4 report ten repetitions per test; Figure 9 reports reaching zero penalty at generation 30 versus generation 50 for the preceding method in that experiment. This is a generation-count comparison, not a demonstrated wall-clock speedup.

**Application:** supports GA as a comparator and reporting both solution quality and convergence. Its use of the word “accuracy” does not provide a universal seating-accuracy formula. A PJKIT GA needs bundle-preserving encoding/decoding and a clear way to handle infeasible offspring.

**Additional lead:** Chandra et al. (2022), “A Comparison of Genetic Algorithm Operators for the Seat Allocation Problem,” ICAC3N, 148–155, DOI 10.1109/ICAC3N56670.2022.10074446. Undermind metadata and abstract were checked; its detailed experimental metrics were not verified from full text, so it is not used as metric evidence here. [R9]

### 5. Physical-seat selection: simulated annealing

**Dundar (2025), “A simulated annealing with graph-based search for the social-distancing problem in enclosed areas during pandemics.”** PLOS ONE, 20(2), e0318380. [R5]

The paper combines greedy randomized initialization with simulated annealing and a graph-based neighborhood, comparing against CPLEX for a maximum-diversity seating formulation.

**Verified evaluation measures:** best/worst objective values, average CPU time over 100 simulations, and comparison against proven optima or time-limited solver incumbents. See the Computational experiments section and Tables 2–5.

**Application:** supports SA as a local-search alternative and repeated-run evaluation. Its distance-maximization objective differs from assigning named registrations under PJKIT rules. Matching an independently proven optimum is evidence of an optimal result; SA itself does not provide the proof. CPU time and wall-clock time must remain separately labelled.

### 6. Capacity and preserving existing allocations

**Barry et al. (2021), “Optimal Seat Allocation Under Social Distancing Constraints.”** arXiv:2105.05017; cite as a preprint. [R6]

The paper compares a constrained random-walk heuristic, graph partitioning, and an integer linear program solved using CPLEX.

**Verified evaluation measures:** number of allocatable workspaces across floor plans and distance requirements (Tables I–II). Section III.C.1 explicitly introduces objective terms to discourage changes from a previous allocation.

**Application:** supports allocation coverage/capacity measures and an explicit movement objective for reallocation. It does not report a full moved-registration-rate benchmark equivalent to the proposed PJKIT evaluation. The paper contains inconsistencies between some narrative and table counts, so isolated numeric comparisons should be checked against the particular table before quoting.

## Comparator design for the current system

The following are project recommendations inferred from the studies and current implementation, not claims that the papers implemented PJKIT's rules.

| Method | Proposed role | Adaptation and limitation |
|---|---|---|
| CP-SAT | Existing method under evaluation | Record objective, bounds, status, time budget, workers, and independent validity. Keep business optimization separate from canonicalization. |
| Integer programming with a MIP solver | Main exact comparison | Use binary variables for legal registration-to-seat-bundle options. Enforce identical occupancy, pairing, accessibility, ordering and packing rules. Specify the solver/version and formulation; “ILP” describes the model, while the solver performs the search. |
| Greedy construction | Simple practical baseline | Process constrained registrations with a fixed documented tie-breaking policy; select legal placements by incremental cost. If it cannot complete a layout, report failure to find a feasible plan, not proof of infeasibility. |
| Tabu search | Main heuristic comparison | Use whole-registration relocations, swaps and compound moves. Respect pairs and audit complete solutions. Define feasibility recovery and neighborhood restrictions explicitly. |
| GA | Optional population-based comparator | Use permutations or bundle choices with a decoder/repair operator. Include decoding and repair time in the budget and report unsuccessful runs. |
| Simulated annealing | Alternative to tabu/GA | Use the same scoring and hard rules, with a documented cooling schedule and feasible initialization. Compound moves may be necessary under strict packing. |

A restrictive move operator can prevent local search from reaching good feasible plans. Poor performance with single-seat swaps could therefore reflect the representation rather than the metaheuristic. Do not break pairs or relax rules merely to improve the baseline's score. If CP-SAT creates a baseline's initial solution, identify it as a hybrid and include that initialization cost.

**Hungarian/linear assignment:** useful only for a simplified subproblem with one independent seat per registration and additive registration-seat costs. Joint adjacent pairs, overlapping bundle choices, tier relationships and packing rules fall outside that basic formulation. Use it as a labelled reduced-problem experiment if desired, not as a full-policy competitor. Official OR-Tools documentation describes the specialized linear assignment solver's narrower scope. [R10]

**Plain CP/backtracking:** possible as an additional solver comparison, but no sufficiently close seating benchmark was verified in this focused search to prioritize it over MIP/tabu/GA. A comparison with another LCG solver would compare implementations of a related architecture, not “LCG versus non-LCG.”

## Measures to collect

Symbols: N = number of present eligible registrations; S = assignable physical seats; d_p = seats required by registration p; A_p = its allocated seat bundle. Count an Emperor registration as one unit requiring two physical seats. Exclude absent registrations from demand. Handle N=0 explicitly instead of dividing by zero.

| Measure | Operational definition for PJKIT | Basis and interpretation |
|---|---|---|
| Hard-constraint validity | Independently validate complete plans. Report total violations and counts by rule, plus pass/fail. | Feasibility is central in R1/R3. Zero violations is mandatory for an accepted allocation. |
| Feasible-solution rate | 100 × runs yielding a complete independently valid plan / attempted runs on the known-feasible benchmark set. | Adaptation of R1's feasible-solution reporting. Keep known-infeasible and unresolved instances separate. |
| Complete-registration coverage | 100 × registrations with their full valid entitlement / N. Also report unassigned registrations and unmet physical-seat demand. | Adapts R3's unassigned-ticket measure. Do not count half an Emperor pair as a completed registration. |
| Weighted soft cost | F(A) = sum over registrations p and enabled preferences k of w_k c_pk(A), minimized. | Penalty/fitness precedents in R1/R3/R4; the actual PJKIT cost is project-specific. Only compare valid complete plans. |
| Component quality | Mean contribution-seat, activity and category-zone penalties, each on the implemented 0–100 scale. | Makes the project objective interpretable and exposes trade-offs hidden by its total. It is not a respondent satisfaction percentage. |
| Time to first valid solution | Seconds from the declared start point to the first complete feasible incumbent; mark timeouts as censored. | Initial-versus-improvement distinction in R3. Use an independent final audit and keep audit overhead separately identifiable. |
| Quality at fixed time | Best feasible F at common deadlines, for example 1, 3, 10 and 30 seconds. | Adapts the budgeted comparisons of R1/R5. These proposed budgets are not taken from the papers. |
| Total algorithm and application time | Record preprocessing/model building, solving, validation, canonicalization, and end-to-end time separately. | Runtime is reported in R1/R2/R3/R5. Whole-service timing is an additional project measure. |
| Optimality evidence | Objective, valid lower bound, absolute/relative gap, proof status, time to proof. | Exact-versus-heuristic distinction in R1 and solver status definitions in R8. |
| Run-to-run variation | Best, median, IQR, mean, standard deviation and failure count over repeated runs. | Repeated-run precedents in R2/R4/R5; the chosen summary set is this recommendation. |
| Scalability | Plot quality, validity rate and runtime against physical demand, occupancy pressure, pair fraction and constraint difficulty. | Instance-size studies in R2/R3/R5 motivate this adaptation. Registration count alone hides pair demand. |
| Memory | Per-run process peak RSS in MiB using a fresh process or a justified equivalent. | Additional engineering measure proposed here; not claimed as a consistently reported metric in the selected studies. |
| Human review | Staff acceptability ratings, required manual edits, and review time using a fixed rubric. | R2 provides qualitative precedent, not a validated survey instrument. Human acceptance and optimized cost are different outcomes. |

For current production, S = 232 from the 16×16 layout minus 24 blocked seats. The default synthetic request has 96 registrations requiring 152 seats, not 96 occupied seats and not the unconfirmed 150-person report benchmark.

**Occupancy utilization**, 100 × occupied valid seats / S, is useful context. But if every method seats the same fixed demand, utilization is identical and cannot rank their optimization quality. R6 maximizes capacity under distancing; PJKIT generally fixes demand and optimizes preferences.

**Cost is not necessarily money.** The current weighted penalty is dimensionless. It is not RM expenditure or revenue merely because contribution is an input. Monetary operating cost would require separate compute/deployment measurements.

### Defining a defensible gap

For minimization, let U be the evaluated feasible cost and L a valid lower bound on the *same unrestricted model and objective*:

    absolute gap = U - L
    relative bound gap (%) = 100 × (U - L) / max(1, abs(U))

This is a proposed reporting convention; document it because solver-native definitions can differ. If a proven optimum F* is available, report absolute regret U−F*, and relative regret 100×(U−F*)/max(1, abs(F*)). When F*=0, emphasize absolute regret because a conventional percentage above zero is undefined. Without an optimum or bound, call a comparison “deviation from best known,” not an optimality gap. A common valid bound may also be used to assess a heuristic's returned plan, while making the source of the bound explicit.

Record CP-SAT statuses distinctly: OPTIMAL, FEASIBLE, INFEASIBLE, MODEL_INVALID, UNKNOWN. A time limit without a solution is not proof of infeasibility. Record gap tolerances: if nonzero tolerance settings terminate a solve, explain the achieved gap rather than silently claiming an exact optimum. An independent validator establishes constraint validity, not optimality. [R8]

## Separate experiment for absence repair

Compare three methods on identical saved baseline maps and identical absences:

1. Full regeneration optimizing the ordinary preferences.
2. Full-hall reoptimization minimizing moved registrations, then distance, then preferences, lexicographically.
3. The current incremental neighborhood repair using that same objective order.

This isolates the value of a movement objective from the value of restricting the search neighborhood. Baseline 2 is a proposed experiment, not a claim that this benchmark is already implemented.

For remaining present registrations P, let B_p be the saved original bundle and A_p the repaired bundle:

    moved registrations M = sum[p in P] indicator(A_p != B_p)
    preservation rate (%) = 100 × (1 - M / len(P))
    moved physical seats = sum[p in P] d_p × indicator(A_p != B_p)

The “moved physical seats” convention above follows the project rule: a changed Emperor bundle counts as two. It is distinct from counting changed individual seat IDs, particularly when old and new pairs overlap. Define which measure appears in the report.

Also report the implemented doubled Manhattan distance between old and new bundle centroids, weighted preference cost, runtime, validity, scope size, and number of neighborhood expansions. Exclude absent registrations from movement counts. “Distance” in row/position coordinates is not walking distance in metres.

The current repair stops at its first feasible neighborhood and freezes outside assignments. Therefore, even proven optimality is restricted to that neighborhood. It does not prove globally minimum movement over the full hall. Record which lexicographic stages were proven and which returned only feasible incumbents. R6 supports preserving prior allocations, but these exact measures and experiments are project-specific proposals.

## Fair experimental protocol

1. Freeze the layout/policy version, objective coefficients, normalization and hard constraints. Use the same independent validator and rescoring function for every method.
2. Build known-feasible tiny instances with exhaustive optimum checks; representative current-venue instances; near-capacity cases with different Emperor fractions; and a separate infeasible/invalid-input suite. Sample low/medium/high constraint difficulty, not only participant count.
3. Use the same instances for every algorithm. For stochastic methods, 30 independent seeds per instance/budget is a practical proposed starting point, not a statistical guarantee. Use separate seeds/instances for parameter tuning and final evaluation.
4. Control CPU/memory, worker counts, software versions and time budgets. Use a single-core comparison for algorithmic fairness, and optionally a separately labelled production comparison with realistic parallel CP-SAT settings. Record initialization/repair/model-building costs.
5. Disable canonicalization for the primary optimization comparison; measure its production overhead separately. Exact map equality is not solution quality when many equally good assignments exist.
6. Compare weighted totals only within the same preference profile. The 40/30/20 coefficients are relative weights, not percentages or lexicographic priorities. All-preferences-off instances test feasibility and speed, because every valid plan has zero ordinary cost.
7. Include all failures and timeouts. Report cost distributions on common successfully solved instances alongside success rates, so a method solving only easy instances is not rewarded by selective averages. Separate solver-only timing from service latency.
8. Present quality-versus-time curves, runtime/quality distributions and scale plots. Across independent matched instances, use paired differences with uncertainty intervals; optional paired nonparametric tests should match the design. Repeated seeds of one instance are not independent problem instances.
9. For absence repair include front/middle/tail absences, pairs, multiple absent units, accessibility constraints, and saved manually edited plans. Compare the same baseline and remaining demand for each method.

Suggested result-table columns:

| Algorithm/configuration | Instances/runs | Feasible % | Median cost on common valid cases | Bound gap | First-feasible time | Total time median/IQR | Peak RSS | Proof/status counts |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Populate after experiments | — | — | — | — | — | — | — | — |

For repair, add moved registrations, preserved %, movement distance, preference cost and neighborhood scope. Use N/A for unavailable bounds rather than zero.

## How to frame the results and discussion

Before experiments, describe these as **literature-supported expectations or hypotheses**. A defensible hypothesis is that CP-SAT offers strong constraint handling and useful proof information, greedy construction offers low overhead, and metaheuristics may offer competitive feasible quality within tight budgets. None is a measured conclusion about PJKIT.

After experiments, discuss whether differences arise from finding feasibility, improving preferences, proving optimality, pair/packing restrictions, or preprocessing costs. A faster feasible solution and a faster optimality proof answer different questions. For repair, explain the measured trade-off between movement, preferences, time and restricted search scope.

Avoid claims such as “100% accurate because CP-SAT is exact,” “GA cannot satisfy hard constraints,” “MIP cannot certify optimality,” or “CP-SAT is guaranteed to be fastest for 200 people.” Neither the selected literature nor the architecture alone justifies them.

## References and verification notes

- **R1.** Lewis, R., & Carroll, F. (2016). Creating seating plans: a practical application. *Journal of the Operational Research Society, 67*(11), 1353–1362. [DOI](https://doi.org/10.1057/jors.2016.34). [Author manuscript](https://rhydlewis.eu/papers/LewisCarroll.pdf). Full experimental sections checked.
- **R2.** Ipsen, A., Cashmore, M., Fielding, K., Marchesotti, N., Zehtabi, P., Magazzeni, D., & Veloso, M. (2026). *Beyond Manual Planning: Seating Allocation for Large Organizations* [Preprint]. [arXiv](https://arxiv.org/abs/2602.05875). Full evaluation and local PDF Table 1 checked. Local source: `FYP1/research-papers/Beyond Manual Planning Seating Allocation for Large Organizations.pdf`.
- **R3.** Muñoz, V., Montaner, M., & López, B. (2006, as catalogued by the university). *Seat allocation for massive events based on region growing techniques* (IIiA 06-01-RR). Universitat de Girona. [University publication list](https://exit.udg.edu/ca/publicacions/). Local report text checked, particularly Sections 3 and 5: `FYP1/research-papers/Seat_allocation_for_massive_events_based_on_region.pdf`. The local title page does not print a year; distinguish this report from the de la Rosa conference version.
- **R4.** Ağalday, F., & Nizam, A. (2022). Performance Improvement of Genetic Algorithm Based Exam Seating Solution by Parameter Optimization. *Journal of Innovative Science and Engineering, 6*(2), 220–232. [DOI](https://doi.org/10.38088/jise.1006070). [Publisher record](https://jise.btu.edu.tr/en/pub/article/1006070). [Full-text copy checked](https://pdfs.semanticscholar.org/7b47/a86fdd21cc9ad431d9029069f4563a51d24f.pdf). Acceptance was July 2022; the publisher gives December 2022 as publication.
- **R5.** Dundar, B. (2025). A simulated annealing with graph-based search for the social-distancing problem in enclosed areas during pandemics. *PLOS ONE, 20*(2), e0318380. [Article and full text](https://doi.org/10.1371/journal.pone.0318380). Computational experiments checked.
- **R6.** Barry, M., Gambella, C., Lorenzi, F., Sheehan, J., & Ploennigs, J. (2021). *Optimal Seat Allocation Under Social Distancing Constraints* [Preprint]. [arXiv](https://arxiv.org/abs/2105.05017). Full formulation and results checked; the abstract's “linear programming” refers to an integer model in the body.
- **R7.** Perron, L., Didier, F., & Gay, S. (2023). The CP-SAT-LP Solver (Invited Talk). In *29th International Conference on Principles and Practice of Constraint Programming*, LIPIcs 280, 3:1–3:2. [DOI](https://doi.org/10.4230/LIPIcs.CP.2023.3). A short solver-architecture paper, not a seating benchmark.
- **R8.** Google. *CP-SAT Solver*. [Official documentation](https://developers.google.com/optimization/cp/cp_solver). Consulted for solver semantics, not independent comparative performance claims.
- **R9.** Chandra, S. K., Kamble, S. P., Dalvi, S. S., Mane, S. S., & Nair, D. (2022). A Comparison of Genetic Algorithm Operators for the Seat Allocation Problem. *ICAC3N*, 148–155. [DOI](https://doi.org/10.1109/ICAC3N56670.2022.10074446). Abstract/metadata only; detailed metrics unverified.
- **R10.** Google. *Linear Sum Assignment Solver*. [Official documentation](https://developers.google.com/optimization/assignment/linear_assignment). Consulted for the scope of specialized assignment.

Project context checked: `README.md`, `docs/evaluation.md`, `docs/mathematical_model.md`, `docs/solver-mathematical-background.md`, and `docs/absence-reallocation.md`. Existing evaluation infrastructure is useful, but comparative experiments across these algorithms and broader repair benchmarks still need to be run. This research note does not change implementation or existing reports.
