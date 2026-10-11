# Mathematical model review and dissertation planning

Reviewed: 11 October 2026.

Scope: review of `maths-model-draft.md` against the current layout, scorer, generation model and absence-repair implementation. Statements in the draft about what must be removed are treated as material to assess, not instructions to follow. The original draft is unchanged. The formulations below distinguish verified implementation behavior, the student's confirmed dissertation scope, and parameters that still lack stakeholder validation.

## Verdict

The central legal-option formulation is mathematically valid. It is suitable as the foundation of a dissertation model after corrections to scope, definitions, indices, and justification of preference parameters. The draft is explanatory working material, not yet a complete dissertation-ready specification.

The main decision is a binary selection of a legal seat bundle for each registration. This is a linear integer optimization formulation once legal options and their cost coefficients have been computed. The same mathematical model can be encoded for CP-SAT or a MIP solver. Solver choice belongs after the formulation, not inside the definition of PJKIT's requirements.

Implementation consistency establishes that equations describe the software. It does not establish that every rule or numerical preference has been validated by PJKIT. Interview evidence, approved requirements or explicitly identified design assumptions are still needed.

## Findings in the draft

| Location in draft | Assessment | Required clarification or correction |
|---|---|---|
| Sections 1, 36 and 51; lines 27, 1708, 2339 | Stale scope claims | Remove the blanket claim that movement, previous allocations and incremental repair must not appear. They are relevant to the requested second model and are implemented in `absence_repair.py`. |
| Section 5; line 158 | Stale eligibility claim | Keep confirmed registration records separate from the active set requiring seats. The current scorer excludes ABSENT registrations. Attendance is an input parameter, not a solver decision. |
| Sections 9 and 11; lines 418 and 528 | Correct idea, inconsistent notation | Options should consistently be sets of globally identified seats, including singleton sets. Position pairs such as (1,2) need a row index when reused across rows. |
| Sections 10–18 | Sound core constraints | Exactly-one option, unique seat occupancy, whole-bundle tier precedence and within-tier row ordering are valid. Include every applicable index and variable domain. |
| Compact models; lines 2229 and 3793 | Incomplete indexing | A tier boundary belongs to a specific adjacent nonempty-tier pair. A contribution boundary belongs to one tier and one adjacent contribution-level pair. Do not use one unqualified boundary across all unequal contribution pairs. |
| Sections 20–21; lines 974 and 1049 | Correct but stronger than a general preference | Front-fill plus within-row prefix packing fixes the occupied seat set for a fixed demand. Explain this consequence and potential conflicts with accessibility/pairs. |
| Section 27; line 1281 | Correct formula, incomplete interpretation | Minimum contribution importance is exactly 1. Maximum importance is 100 only when contributions vary within the tier. If all are equal, everyone receives 1. |
| Sections 25 and 29 | Correct within-row cost | The disadvantage uses priority rank within a row, not global row-major order. Do not claim this soft term penalizes later rows directly. |
| Section 32; line 1540 | Correct for positive bounds | Define each normalization bound; handle a zero bound explicitly. The current implementation protects the denominator with max(1,M). |
| Sections 31 and 33 | Valid parameters, not mathematical facts | The zone-cost matrix and 40/30/20 weights are configured choices. Document their source and sensitivity; code alone does not establish stakeholder approval. |
| Sections 37–39 | Conditional determinism | A canonical assignment is guaranteed by completing every tie-breaking stage under fixed data/domains/order. A timed-out canonicalization is not that guarantee. |
| Section 44 and methodology outline | Stale research-objective mapping | Absence reallocation is the requested optimization extension. Safeguard checking is a supporting validation/governance layer. |
| Final argmin expression; line 4195 | Minor formal notation | Write z* in argmin when optima may be non-unique, or explicitly state that a tie-breaking rule selects one member. |

## Numerical checks

The current `data/layouts/production_2026.json` contains 16 rows, 16 positions per row, 256 positions, 24 blocked positions and 232 assignable seats. Its approved position pairs are (1,2), (3,4), (5,6), (7,8), (9,10), (11,12), (13,14), and (15,16), filtered by actual seat availability and accessibility.

For row width C=16, doubled mean rank disadvantage is

\[
d_o=\frac{2}{|o|}\sum_{s\in o}(\rho_s-1).
\]

It is integer for the permitted bundle sizes 1 and 2. Examples checked:

| Rank(s) | d_o | Raw contribution cost at importance 100 | Normalized cost using bound 3000 |
|---|---:|---:|---:|
| 1 | 0 | 0 | 0 |
| 8 | 14 | 1400 | 47 |
| 1,2 | 1 | 100 | 3 |
| 7,8 | 13 | 1300 | 43 |
| 16 | 30 | 3000 | 100 |
| 15,16 | 29 | 2900 | 97 |

The value 3000 is a common safe bound, not a claim that every registration's legal domain attains it. For approved pairs, the worst pair in a full row has disadvantage 29, not 30. Rounding also means small raw-cost differences can disappear after normalization.

Distinguish four kinds of numbers in the chapter:

1. Observed instance data: venue dimensions and blocked seats, supported by the venue specification.
2. Business parameters: tier entitlements, priority order and approved pairs, supported by elicited rules.
3. Derived quantities: demand, remaining row capacity, disadvantage and normalization bounds.
4. Design parameters: the 0–100 scoring scale, relative preference weights, category penalties and chosen distance metric. Justify and test these; do not label them empirically validated without evidence.

## Clean notation for the initial-allocation model

This is a solver-independent formulation of the current strict generation policy. It is not a declaration that every policy has been confirmed by PJKIT.

### Sets and fixed parameters

- \(\mathcal P\): all confirmed paid registration records.
- \(a_p\in\{0,1\}\): input absence flag, with 1 meaning absent.
- \(P=\{p\in\mathcal P:a_p=0\}\): registrations requiring seats in this allocation. Before absence information is supplied, all flags may be initialized to zero.
- \(S^{all}\): all physical positions; \(S\subseteq S^{all}\): nonblocked assignable seats.
- \(\mathcal R=\{1,\ldots,R\}\): row indices; \(S_r\subseteq S\): available seats in row r.
- \(r_s,j_s,\rho_s\): row, physical position, and within-row priority rank of seat s.
- \(t_p\): registered tier, an input; \(m_p\): contribution in RM; \(e_p\): activity count; \(k_p\): category.
- \(d_p\in\{1,2\}\): entitlement, with 2 for Emperor and 1 for Merit/Bodhi.
- \(\mathcal A\subseteq\{o\subseteq S:|o|=2\}\): approved available pairs. Every pair shares a row, lies on one side of the aisle, and obeys the approved pairing pattern.
- \(h_p\in\{0,1\}\): accessibility requirement; \(\alpha_s\in\{0,1\}\): accessibility of a seat.

Define legal options explicitly:

\[
O_p=\begin{cases}
\{\{s\}:s\in S,\ h_p\le\alpha_s\},&d_p=1,\\
\{o\in\mathcal A:h_p\le\alpha_s\ \forall s\in o\},&d_p=2.
\end{cases}
\]

This reproduces the current requirement that both seats of an accessibility-requiring Emperor bundle are accessible. If only one occupant needs an accessible chair, that is a separate policy choice requiring a different domain definition.

Tier membership must not be inferred solely from contribution thresholds: the current input supplies the tier and checks its minimum contribution. No exclusive upper contribution bound is implied.

### Variables and selected-option expressions

\[
z_{po}\in\{0,1\}\qquad(p\in P,\ o\in O_p).
\]

Here z_po=1 means registration p receives the entire bundle o. Seat occupancy is a derived expression:

\[
y_s=\sum_{p\in P}\sum_{\substack{o\in O_p\\s\in o}}z_{po}.
\]

Define constants

\[
\pi_s=(r_s-1)C+\rho_s,\qquad
\ell_o=\min_{s\in o}\pi_s,\qquad u_o=\max_{s\in o}\pi_s,
\]

and let r_o denote the common row of option o. Then

\[
R_p=\sum_{o\in O_p}r_o z_{po},\quad
L_p=\sum_{o\in O_p}\ell_o z_{po},\quad
U_p=\sum_{o\in O_p}u_o z_{po}.
\]

The minima/maxima above concern known option data. They do not make the optimization constraints nonlinear.

### Hard constraints

\[
\sum_{o\in O_p}z_{po}=1\qquad\forall p\in P. \tag{1}
\]

\[
y_s\le1\qquad\forall s\in S. \tag{2}
\]

Let \(t_p\prec t_q\) mean Emperor precedes Merit precedes Bodhi. The direct mathematical rules are

\[
U_p+1\le L_q\qquad\forall p,q\in P:t_p\prec t_q, \tag{3}
\]

\[
R_p\le R_q\qquad\forall p,q\in P:t_p=t_q,\ m_p>m_q. \tag{4}
\]

The +1 form is equivalent to strict inequality because seat orders are integer.

For packing, let \(D=\sum_{p\in P}d_p\) and \(A_r=|S_r|\). Define row targets as input-derived constants:

\[
q_r=\min\left(A_r,\max\left(0,D-\sum_{i<r}A_i\right)\right).
\]

Then impose

\[
\sum_{s\in S_r}y_s=q_r\qquad\forall r\in\mathcal R. \tag{5}
\]

Enumerate available seats of row r in the required east-first order as \(s_{r,1},\ldots,s_{r,A_r}\), skipping blocked positions. Impose

\[
y_{s_{r,j+1}}\le y_{s_{r,j}}
\quad\forall r\in\mathcal R,\ j=1,\ldots,A_r-1. \tag{6}
\]

Rows with fewer than two available seats contribute no prefix inequalities. With integer binary selections and (2), occupancy is automatically binary. Together (5) and (6) fix the first q_r available seats of each row as occupied. Thus a fixed D determines the entire occupied set.

Capacity \(D\le|S|\) is necessary, not sufficient: pairing, accessibility and precedence may conflict even when there are enough seats. If any required O_p is empty, (1) is infeasible; do not silently drop the registration.

### Optional compact boundary encoding

For adjacent nonempty tiers \(t_i,t_{i+1}\), introduce \(\beta_i\in\{1,\ldots,RC\}\) and replace the corresponding direct tier comparisons with

\[
U_p\le\beta_i\quad\forall p\in P_{t_i},\qquad
L_q\ge\beta_i+1\quad\forall q\in P_{t_{i+1}}.
\]

Within tier t, let \(G_{t,1},\ldots,G_{t,K_t}\) be nonempty equal-contribution groups in descending contribution order. For each g=1,...,K_t-1, introduce \(\gamma_{t,g}\in\{1,\ldots,R\}\):

\[
R_p\le\gamma_{t,g}\quad\forall p\in G_{t,g},\qquad
R_q\ge\gamma_{t,g}\quad\forall q\in G_{t,g+1}.
\]

Transitivity gives the other comparisons. These are alternative encodings of the direct rules, not additional business requirements. Present direct rules first, then this implementation optimization. Explain row-domain pruning separately and state the assumptions under which it preserves all feasible assignments.

### Cost coefficients and objective

Use \(K_{po}\) for the precomputed option cost, reserving \(F\) for the total objective and \(Q_{k,z}\) for category-zone costs. This avoids using Z for both an objective and a matrix.

For nonnegative n and positive d, define

\[
H(n,d)=\left\lfloor\frac{2n+d}{2d}\right\rfloor.
\]

Within each nonempty active tier, define observed minimum/maximum contribution and activity. Current importance scores are

\[
I_p^C=1+H\left(99(m_p-m_t^{min}),\max(1,m_t^{max}-m_t^{min})\right),
\]

\[
I_p^A=H\left(100(e_p-e_t^{min}),\max(1,e_t^{max}-e_t^{min})\right).
\]

Thus \(I_p^C\in\{1,\ldots,100\}\), \(I_p^A\in\{0,\ldots,100\}\). When a tier's contributions are identical, all I_p^C=1; when activities are identical, all I_p^A=0. Empty tiers require no extrema or participant costs.

Define

\[
r^C_{po}=I_p^C d_o,\quad r^A_{po}=I_p^A d_o,\quad
r^Z_{po}=\frac{2}{|o|}\sum_{s\in o}Q_{k_p,zone(s)}.
\]

With integer category costs and permitted bundle sizes these raw quantities are integers. Current bounds are

\[
M_C=M_A=200(C-1),\qquad M_Z=2\max_{k,z}Q_{k,z}.
\]

Normalize each component with

\[
n^k_{po}=H(100r^k_{po},\max(1,M_k)),\qquad k\in\{C,A,Z\}.
\]

The max guard agrees with the implementation and handles an all-zero category matrix. With valid nonnegative bounded raw costs, normalized values lie in 0,...,100.

\[
K_{po}=w_C n^C_{po}+w_A n^A_{po}+w_Z n^Z_{po},
\qquad
\min_z F(z)=\sum_{p\in P}\sum_{o\in O_p}K_{po}z_{po}. \tag{7}
\]

All weights/costs are fixed before optimization. This is a linear objective. Neither the scaling nor relative weights establish lexicographic preference priorities. If all preferences are disabled, every feasible assignment has F=0.

The within-row rank cost repeats across rows. The hard row-ordering rule, rather than this penalty, enforces contribution order across rows. Pair averaging gives preference influence per registration, not per individual person; document this choice.

For formal optimum notation use \(z^*\in\arg\min_{z\in\mathcal F}F(z)\), with \(\mathcal F\) defined by the constraints. Post-optimal canonicalization selects a particular optimal assignment only if all its stages finish.

## Absence-reallocation extension: confirmed dissertation scope

The student confirmed that the dissertation should describe the current policy: count moved registration units, retain compulsory front-fill and east-before-west packing, and prioritize movement count, then distance, then preferences.

Let A be newly absent registrations and let \(P'=P^0\setminus A\) be the surviving active registrations from the baseline. For each p in P', let \(b_p\subseteq S\) be its saved pre-repair seat bundle. Each surviving registration must have a complete baseline bundle; newly arriving participants and partially absent Emperor pairs are outside this formulation.

Rebuild the feasible set \(\mathcal F(P')\), including the compulsory demand-based packing targets. Never count release of an absent registration's seats as movement by a surviving registration.

For each candidate option, precompute

\[
\delta_{po}=\begin{cases}0,&o=b_p,\\1,&o\ne b_p.\end{cases}
\]

Bundle equality ignores ordering of seat identifiers. Then define

\[
\mu_p=\sum_{o\in O'_p}\delta_{po}z_{po},\qquad
M(z)=\sum_{p\in P'}\mu_p.
\]

Exactly-one selection makes \(\mu_p\) binary automatically. Minimizing M counts affected registration units. A changed Emperor bundle counts as one unit. The symbol \(m_p\) remains reserved for contribution amount.

An optional descriptive statistic is \(M_{people}(z)=\sum_{p\in P'}d_p\mu_p\), counting everyone in a changed bundle as affected. This is not the chosen optimization objective. Counting exactly which named individual changes chair would require person-to-seat identities; the present bundle model does not encode that distinction.

For the current distance metric, define the doubled bundle centroid

\[
\bar r_2(o)=\frac{2}{|o|}\sum_{s\in o}r_s,\qquad
\bar j_2(o)=\frac{2}{|o|}\sum_{s\in o}j_s,
\]

and fixed option distance

\[
\ell_{po}=|\bar r_2(o)-\bar r_2(b_p)|+|\bar j_2(o)-\bar j_2(b_p)|.
\]

\[
L(z)=\sum_{p\in P'}\sum_{o\in O'_p}\ell_{po}z_{po}.
\]

These are integer grid-coordinate distances, not physical walking distances in metres. Absolute values are computed from fixed old/new option coordinates before solving, so the resulting objective remains linear.

The current objective hierarchy is

\[
\operatorname{lexmin}_{z\in\mathcal F(P')}\big(M(z),L(z),F'(z)\big).
\]

Interpretation: first minimize the number of changed registrations; among those optima, minimize movement distance; among those ties, minimize current seating-preference cost. An arbitrary weighted sum does not guarantee that priority.

In staged solution, fix M=M* only after proving its optimum, then optimize/fix L, then optimize F'. If a deadline permits only a feasible incumbent at a stage, retain it and identify which priorities remain unproven. A feasible result does not establish minimum movement.

### Global target versus implemented local repair

The global formulation permits every surviving registration to move. The current implementation instead starts around absence rows, freezes outside registrations, and expands only after a neighborhood is proved infeasible.

For selected rows N, define domains

\[
O'_p(N)=\begin{cases}
\{o\in O_p:r_o\in N\},&r(b_p)\in N,\\
\{b_p\}\cap O_p,&r(b_p)\notin N.
\end{cases}
\]

This yields \(\mathcal F_N(P')\subseteq\mathcal F(P')\). Replacing the global feasible set by this restricted set produces the implemented local subproblem. Its optimum need not be the global minimum-movement result. For the confirmed current-implementation scope, present the global objective as a reference target and the restricted neighborhood as the implemented solution strategy; claim only the optimality actually proved within that neighborhood.

If packing is removed and the baseline satisfied all remaining hard rules, retaining all surviving assignments is feasible and gives M=0. That is necessarily optimal for the primary movement objective. Thus the requirement to close gaps is substantive: without another reason to rearrange, minimum-movement repair can correctly be a no-op.

The current scorer recalculates contribution/activity extrema over the remaining active tier members. Consequently F' may use different importance scores from the baseline even for unchanged participants. The requested current-implementation model retains this recomputation. Freezing the original scoring reference population would be a separate proposed variant. Do not compare pre/post weighted totals as if their coefficients were unchanged unless they were held fixed for that comparison.

## Recommended methodology sequence

1. Describe the operational problem, research objectives and allocation unit.
2. Present requirement elicitation and a traceability table: PJKIT rule, evidence, hard/soft status and equation number.
3. Define assumptions, sets, indices, input parameters and decision variables in one notation table.
4. Derive legal options and the initial-allocation constraints, explaining each equation immediately after it.
5. Derive scoring, normalization and weighted cost; identify the origin of every numerical choice.
6. Give one complete small worked example with explicit physical coordinates, ranks, pairs and evaluated costs.
7. Extend the model for absence, saved baselines, movement and the chosen objective hierarchy.
8. Explain CP-SAT encoding, pruning, boundary variables, search limits and any local repair strategy.
9. Describe independent validation, solver-status interpretation, canonicalization and the separate manual-review policy.
10. Define experiments for feasibility, preference quality, runtime, proof gaps, movement and parameter sensitivity.

Use background/theory for general constraint optimization concepts; methodology for your own formalization and justified choices; results/discussion for measured performance and limitations. Document actual research chronology rather than claiming a model preceded implementation if it was developed iteratively.

## Confirmed choices and remaining evidence

- Movement is counted by registration unit; an Emperor pair counts as one.
- Front-fill and east-before-west packing remain hard after absence.
- The dissertation describes the current implementation, with strict movement-count, distance, preference priorities.
- The student confirmed that 40/30/20 and the category-zone matrix are provisional design choices, without experimental validation or confirmed stakeholder calibration. They must not be described as established PJKIT numerical preferences.
- Synthetic participant data are authorized by Netizen eXperience according to the student's statement, for development, experiments, presentation and demonstrations. This permits privacy-preserving experiments; it does not establish the statistical representativeness of generated data.

See `docs/methodologies/preference-parameter-study-2026-10-11.md` for research, executed sensitivity experiments and the evidence still needed to justify preference parameters.

The current model treats absence at registration level, requires both seats of an accessibility-requiring Emperor pair to be accessible, and rescales preferences over the remaining active population. Partial attendance of an Emperor pair is outside this formulation. Organizational confirmation of these underlying operational assumptions remains separate from confirmation that the dissertation should describe the current implementation.

## Evidence consulted

- Original draft: `docs/methodologies/maths-model-draft.md`.
- Current mathematical description: `docs/mathematical_model.md`.
- Initial model and boundary encodings: `services/seating/services/seating/src/seat_solver/production/production.py`, especially `initial_rows()` and `build()`.
- Eligibility, domains and numerical costs: `services/seating/services/seating/src/seat_solver/production/production_scoring.py`.
- Policy/validation: `services/seating/services/seating/src/seat_solver/production/policy.py` and `services/seating/config/production_policy.json`.
- Repair scope, movement and staged solving: `services/seating/services/seating/src/seat_solver/production/absence_repair.py` and `docs/absence-reallocation.md`.
- Layout counts: `data/layouts/production_2026.json`.
- [Google CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver), checked for integer modeling and status semantics.
- [Perron, Didier and Gay (2023), The CP-SAT-LP Solver](https://doi.org/10.4230/LIPIcs.CP.2023.3), checked for solver architecture. This describes solving technology, not validation of PJKIT's rules or weights.

Validation performed for this review: static equation/code comparison, aggregate inspection of layout data, and recomputation of the arithmetic examples. No new solver-performance or stakeholder-validation claims are made.
