# Revised Section 2 — Literature Review (ready to paste into the interim report)

**Purpose:** Replacement text for Section 2 of `Draft_Interim_Report_To_GPT`, implementing the items in `Literature_Review_Response_Roadmap.md` and the examiner guidance in `Literature_Review_Comment.md`.

**Ground truth applied:** 16 rows × 16 seats = 256 seats, 8 seats per side of the centre aisle (so the aisle falls between positions 8 and 9), 232 assignable after the 24-seat structural block; contribution tier order **fixed** as Emperor → Merit → Bodhi from the front; a boundary row **may** be shared between two adjacent tiers.

**Structure:** eight subsections replacing the current five. New material is §2.1 (search strategy), §2.3 (reallocation literature), and the corrected complexity argument in §2.6. Existing §2.1/§2.2 become §2.4/§2.5.

> ⚠ **Read §"Sources to obtain before submission" at the end of this file first.** Several recommended citations have not been retrieved and read in preparing this revision. Do not paste citations for works you have not read.

---

# 2. Literature Review

## 2.1 Literature Search Strategy

Literature for this review was identified through a two-stage search. In the first stage, database searches were conducted on Google Scholar, IEEE Xplore, the ACM Digital Library and Scopus using combinations of the keywords *seating allocation*, *seat assignment*, *spectator allocation*, *office space allocation*, *constraint optimization*, *constraint programming*, *CP-SAT*, *minimal perturbation*, *reallocation stability* and *large neighbourhood search*, restricted to English-language publications. A work was included when it either addressed the assignment of people to physical seats, or presented a constraint-optimization or repair technique transferable to that problem. A work was excluded when it addressed the apportionment of seat *counts* to groups rather than the assignment of individuals to physical seats, when it addressed revenue management or overbooking rather than allocation of already-sold seats, or when it addressed pedestrian-flow and evacuation simulation rather than seat assignment.

In the second stage, backward snowballing was applied to the reference lists of the most directly relevant works located in the first stage, in particular Ipsen et al. (2026), in order to surface earlier seating-allocation studies that keyword search did not return.

The search established that literature treating seating allocation *as an optimization problem* is limited relative to the general combinatorial-assignment literature, and that what exists is distributed across three loosely connected streams — office space allocation, legislative and assembly seat allocation, and event or venue spectator seating — rather than forming a single coherent research area. This dispersion is itself relevant to the present project, because it means no single established problem formulation can be adopted wholesale for the PJKIT case.

## 2.2 Academic Studies on Seating and Space Allocation

**Hierarchical office seating allocation.** Ipsen et al. (2026) formalize the Hierarchical Seating Allocation Problem (HSAP), in which organizationally nested teams must be assigned to seats on an office floor plan so that hierarchically related teams sit near one another. They decompose the problem into per-level Seat Allocation sub-problems solved top-down, and compare four sub-problem solvers: an exact integer program that selects a central seat per team and minimizes the distance from team members to it; an iterative clustering heuristic resembling k-means; a regret-based greedy baseline; and a warm-started local search that re-optimizes only the seats near an incumbent solution. They also address distance estimation on real floor plans, replacing Euclidean distance — which underestimates walking cost across walls — with a probabilistic roadmap constructed using rapidly-exploring random trees.

Three findings transfer to the present project. First, exact optimization is tractable at sub-problem scale but only when the problem is deliberately decomposed; PJKIT's demand-derived tier bands play a comparable decomposition role, and are exploited in this project's model by creating decision variables only for band-eligible participant–seat combinations. Second, their warm-started local search demonstrates that re-optimizing a bounded region around an incumbent solution is the practical mechanism for keeping successive plans stable. Third, and least comfortably for any optimization-based approach, their qualitative evaluation shows that a solution proven optimal against the stated objective can still diverge from what a human decision-maker would choose — which is why the present project retains organizer review before publication rather than publishing solver output directly.

The limitation of HSAP for the present purpose is that its objective is proximity of related teams on an unstructured floor plan. It contains no notion of a fixed row-and-position geometry, no multi-seat allocation unit, no precedence ordering among individuals, and — importantly for Objective 2 — no mechanism for repairing a plan that has *already been communicated to the people it affects*. Their local search improves a solution *within a single planning run*; it does not preserve a prior public commitment.

**Legislative and assembly seat allocation.** Hales and García (2019) address the allocation of physical seats to parties in a legislative chamber using mathematical optimization, and it is from this formulation that Ipsen et al. adapt their own integer program. Of the reviewed works this is contextually the closest to the PJKIT case, because a legislative chamber shares the essential features of a community assembly hall: a fixed geometry of rows and seats, groups entitled to blocks of adjacent seating, and a status ordering that determines which blocks are more desirable. It nevertheless differs in that group membership rather than individual contribution ranking drives placement, and no per-individual ordering constraint of the kind PJKIT applies within each tier is present.

**Spectator allocation for massive events.** Muñoz et al. (2006) address ticket-group-to-seat allocation for a Formula 1 Grand Prix at scales up to 50,000 seats. Ticket groups carry a category, a priority rank and a dispersion flag; seats carry a zone, row, category, rank and status. Their rules divide explicitly into *mandatory* rules — a ticket group must be assigned seats of matching category and status — and nine *optional* rules covering subgroup splitting, rank alignment between ticket and seat, minimum and maximum tickets per row, never leaving a single ticket isolated, avoiding empty seats at row edges, and enforcing an even distribution of occupancy so that a partially sold venue still appears full. Their solver adapts *region growing* from computer-vision image segmentation: a seed seat is selected for each ticket subgroup and grown outward by iteratively annexing the best-scoring neighbouring seat, after which a local-search pass improves the first candidate solution. The method is anytime — a usable solution appears within minutes, and improves if more time is allowed.

Two aspects are directly relevant. Substantively, their mandatory/optional division independently arrives at the same hard/soft constraint architecture adopted in this project, which supports the claim that the distinction is intrinsic to the seating domain rather than an artefact of one modelling choice. Their optional rules also identified a *class* of constraint that had not been considered during initial elicitation for PJKIT — namely rules governing row-level packing and the distribution of vacant seats. Comparison against PJKIT's historical 2023 and 2024 seating charts then determined the specific form this class takes at PJKIT: rather than avoiding isolated seats and edge gaps, PJKIT packs each row outward from the centre aisle and fills the numbered section front to back with no vacant seat, which is recorded as constraints C15 and C16 in Section 3.5.3. The literature therefore supplied the constraint category and empirical validation determined its content — an instance of literature-informed, evidence-validated requirement elicitation.

Methodologically, however, region growing is a constructive heuristic. It offers no completeness or optimality guarantee, reports no solver status from which the organizer could judge whether a better plan exists, and encodes its rules inside a growth-scoring function rather than declaratively, so that changing a rule means changing the algorithm. For a system whose organizer must defend seating decisions to a community, the absence of any falsifiable quality claim is disqualifying, and the method is therefore reviewed as a comparison point in Section 2.7 rather than adopted.

**Distance-constrained and capacity-constrained venue seating.** Barry et al. (2021) and Stoll (2022) address seat allocation in fixed-row venues under distance constraints arising from public-health separation requirements. Their relevance here is not the distancing objective, which does not apply to PJKIT, but the demonstration that adjacency and separation requirements over a fixed row-and-position geometry can be expressed and solved as explicit optimization constraints. This is the structural feature PJKIT shares through its two-seat Emperor allocation units and its centre-aisle restriction, and these works are the closest published treatments of that specific geometry.

**Aisle-interrupted row geometry.** Sun (2020) contributes a combinatorial model rather than an allocation method, treating stadium rows interrupted periodically by access aisles as an arithmetic sequence with a periodic jump, and deriving closed-form expressions for per-row seat counts and cumulative capacity. PJKIT's venue is simpler, comprising sixteen uniform rows of sixteen seats with eight seats on each side of a single centre aisle. Sun's model nevertheless corroborates, from an independent mathematical direction, this project's treatment of the aisle as a *structural break* in row geometry rather than an ordinary gap between consecutive seats — the property that underlies the hard rule that physical adjacency is computed over physical seat positions and that no Emperor pair may span positions 8 and 9.

**Adjacent problem class: office space allocation.** For completeness of scope, the Office Space Allocation problem (Ülker, 2013; Awadallah et al., 2012) allocates people or entities to rooms and floors subject to space and adjacency requirements, typically using metaheuristics. It is distinguished from seating allocation in that it allocates *areas* rather than individual numbered seats, and is noted here to bound what the present project is not addressing.

**Research gap.** Across the reviewed studies, none provides the combination of capabilities the PJKIT case requires. Ipsen et al. (2026) and Hales and García (2019) achieve exact optimization, but through bespoke formulations built for one venue and one rule set, with no configurable rule layer and no mechanism for repairing an already-published plan after a data change. Muñoz et al. (2006) achieve scale and anytime behaviour, but with no optimality or completeness guarantee and no explicit status reporting. Barry et al. (2021) and Stoll (2022) treat fixed-row adjacency constraints, but under a single distancing objective rather than a configurable multi-criteria one. Sun (2020) models venue geometry but does not address allocation. None of the reviewed works models a multi-seat allocation unit, a demand-derived tier band with a shareable boundary row, or a within-tier precedence ordering among individuals; and none treats post-publication repair as a first-class problem.

Accordingly, this project does not claim that no solution exists anywhere for any part of this problem. The defensible claim, and the one this review supports, is narrower: **none of the reviewed academic studies or commercial systems provides the combined capability the PJKIT case requires** — configurable participant-profile-based constraints, constraint-based optimization with falsifiable status reporting, controlled movement-minimizing repair of a published plan, versioned publishing, and participant-facing lookup, within a single workflow.

## 2.3 Stability-Preserving Reallocation and Repair-Based Optimization

Objective 2 concerns a different problem from Objective 1. Once a seating plan has been published and communicated, a subsequent participant change does not call for a new plan but for a *repair* of the existing one, in which assignments already announced to participants are preserved wherever possible. Two established literatures address exactly this situation, and together they supply the theoretical basis for the incremental repair mechanism described in Section 3.

**The minimal perturbation problem.** Given a solution to a constraint satisfaction problem and a subsequent change to the problem, the minimal perturbation problem seeks a new solution that differs from the original in as few assignments as possible. El Sakkout and Wallace (2000) formalize this for dynamic scheduling, and the line of work by Müller, Rudová and Barták applies it to course timetabling, where an already-published timetable must absorb a late change while disrupting as few existing commitments as possible. Course timetabling is a close structural analogue of the PJKIT case: a plan has been published to the people it governs, a change arrives, and the cost of the repair is measured primarily in how many previously-communicated assignments are disturbed rather than in the abstract quality of the new plan. This is the literature that justifies why Objective 2's objective function ranks the number of unaffected participants moved above ordinary seating-preference penalties, rather than treating movement as one soft criterion among equals.

**Large neighbourhood search.** The technique of freezing most of an incumbent solution and re-optimizing only a bounded neighbourhood around the region of interest originates with Shaw (1998) in constraint-programming approaches to vehicle routing, and is surveyed by Pisinger and Ropke (2010). This is precisely the mechanism by which this project's reallocation operates: on a participant change, unaffected assignments are locked, the affected seats are released, and a reduced constraint model is constructed over only the affected participants and a limited set of candidate seats, with the neighbourhood progressively expanded if no feasible repair is found within it. Naming the technique matters because it establishes that the escalation strategy in Section 3 is a recognized method with known behaviour, rather than a heuristic invented for this project, and because it explains why the repair model is expected to be substantially smaller and faster than the initial-generation model.

**Solution reuse in dynamic constraint satisfaction.** Verfaillie and Schiex (1994) address the more general question of reusing a previous solution when the constraints of a problem change, and provide the earlier framing within which both of the above sit.

**Switching costs in dynamic constraint optimization.** Hoang (2022) formulates the Proactive Dynamic Distributed Constraint Optimization Problem, whose objective over a sequence of time steps comprises a per-step utility term less a weighted *switching-cost* term penalizing any change to a decision variable's value between consecutive steps, together with bounds on the quality loss incurred by finite-horizon approximation. PJKIT's requirement to repair a published plan while minimizing seat movement is a single-step instance of this switching-cost structure, which places the movement-minimization term of constraint C9 within a formally analyzed framework. Two limitations bound the transfer: Hoang's setting is *distributed*, with autonomous agents coordinating by message passing, whereas the engine in this project performs a single centralized solve; and his continuous-domain extensions do not apply to a finite discrete set of seats. The objective structure is therefore adopted, while the solution architecture is not.

Taken together, these four sources establish that stability-preserving repair of an existing assignment is a studied problem with established formulations, and that the mechanism proposed for Objective 2 — a bounded repair neighbourhood with a movement-dominant objective and progressive expansion on infeasibility — is a domain-specific instantiation of that body of work. What is absent from the literature, and what this project contributes, is the application of these techniques to seating allocation specifically, where the repaired artefact is a public commitment to named individuals and where the structural constraints include multi-seat units and tier precedence.

## 2.4 Existing Seat and Space Allocation Systems

Existing tooling was reviewed across five categories of solution, selected to span the range of software an organizer in PJKIT's position could plausibly adopt: manual practice, enterprise event management, dedicated seating planners with automatic assignment, consumer seating-chart tools, and adjacent systems that allocate numbered seats under rules in other domains. One or two representative products were examined per category. Assessments are based on each vendor's publicly available product documentation and feature pages, inspected in June 2026.

| No | Existing System | Category | Main Capability | Limitation |
|---|---|---|---|---|
| 1 | Manual Excel / spreadsheet planning | Manual | Records participant names, seat numbers, groupings and remarks in a predefined template. | No automated allocation, no fairness or quality metric, no optimization, and rework of the whole plan on any change. |
| 2 | Manual seating chart / paper layout | Manual | Places participants on a physical or printed venue layout. | Wholly dependent on human judgement; does not scale to hundreds of participants; no means of verifying rule compliance. |
| 3 | Cvent / Social Tables | Enterprise event management | Event management, diagramming, collaboration and floor planning. | Strong in planning and visualization; no configurable weighted-constraint optimization over participant attributes. |
| 4 | PerfectTablePlan | Dedicated seating planner | Guest details, RSVPs, proximity preferences, genetic-algorithm automatic assignment, drag-and-drop editing, printed plans. | The most capable reviewed tool, but optimizes guest proximity preferences around tables; provides no configurable participant-profile rule layer, no falsifiable optimality or status reporting, and no controlled repair workflow. |
| 5 | WeddingWire seating chart tool | Consumer seating chart | Drag-and-drop charts, RSVP tracking, table-shape customization, sharing, printing, export. | Visualization-oriented; no optimization or rule configuration. |
| 6 | Zola seating chart tool | Consumer seating chart | Table assignment, floor-plan customization, guest grouping, printing, download, sharing. | Visualization-oriented; no constraint optimization, no dynamic reallocation. |
| 7 | Reserved-seat ticketing platforms (e.g. Eventbrite reserved seating) | Ticketing | Numbered-seat inventory, seat selection at purchase, and per-ticket seat lookup by the attendee. | The attendee-facing seat lookup this project requires does exist here, but seats are *self-selected at purchase* rather than allocated by an administrator under rules; no organizer-side rule configuration or repair workflow. |
| 8 | Congregation and non-profit management systems | Faith-based / non-profit | Membership records, contribution and donation tracking, event registration and attendance history. | Maintain precisely the participant attributes PJKIT allocates on — contribution amount and attendance history — but provide no seating allocation function at all, so the attributes cannot be acted upon. |
| 9 | Examination and classroom seating tools | Rule-based seating, adjacent domain | Assign candidates to numbered seats under separation rules such as preventing same-subject or same-class candidates from sitting adjacently. | Demonstrates rule-based numbered-seat allocation, but optimizes *separation* rather than priority and contribution ordering, and offers no participant-profile weighting or post-publication repair. |

Two observations follow from broadening the review in this way. First, the individual capabilities PJKIT needs all exist somewhere: reserved-seat ticketing provides participant-facing seat lookup; congregation management systems hold the contribution and attendance attributes; examination seating tools perform rule-based numbered-seat assignment; and PerfectTablePlan performs automated optimization. Second, they exist in mutually exclusive products, and none combines them. This strengthens rather than weakens the case for the present project, because it locates the gap in *integration under a configurable rule layer* rather than in the novelty of any single feature.

## 2.5 White Space Analysis

| Existing Method / System | Participant-Facing Seat Lookup After Admin Allocation | Configurable Participant-Profile-Based Allocation | Controlled Dynamic Reallocation | Constraint-Based Optimization | Supports PJKIT-Specific Structural Rules¹ |
|---|---|---|---|---|---|
| Manual Excel / seating chart | No | No | No | No | Only by human effort; unverifiable |
| Cvent / Social Tables | Partial | Partial / limited | Partial editing with synchronization | No | No |
| PerfectTablePlan | No | Partial, through guest proximity preferences | Partial last-minute editing | Yes, genetic-algorithm automatic assignment | No |
| WeddingWire / Zola | Sharable | Weak | Manual adjustment | No | No |
| Reserved-seat ticketing platforms | Yes, but seat is self-selected at purchase | No | No | No | No |
| Congregation / non-profit management systems | No | Holds the attributes but performs no allocation | No | No | No |
| Examination / classroom seating tools | No | Partial, through separation rules | No | Partial, rule-based assignment | No |
| **Proposed FYP system** | **Yes (designed)** | **Yes (designed)** | **Yes (designed)** | **Yes (designed)** | **Yes (designed)** |

¹ Two-seat Emperor allocation units confined to valid within-row pairs; no pair spanning the centre aisle between positions 8 and 9; demand-derived tier bands ordered Emperor → Merit → Bodhi with a shareable boundary row; within-tier contribution ordering; centre-out row fill and front-to-back packing of the numbered section; side-of-hall placement for accessibility.

The analysis yields four findings.

First, a **participant-facing seat accessibility gap** persists in the event-planning category. Existing planners allow charts to be printed, exported or shared, which is not the same as an authenticated route on which a participant sees the seat assigned to them from the latest administrator-approved plan. Reserved-seat ticketing platforms do provide per-attendee seat lookup, but in a model where the attendee selected the seat themselves at purchase, which is inapplicable where an organizer allocates seats by rule.

Second, a **configurable participant-profile allocation gap** persists across all categories. Reviewed systems support guest preferences, VIP labels, groups and manual tagging, but none exposes a generalized rule layer in which an administrator configures hard constraints and weighted soft constraints over attributes such as contribution amount, activeness, tier and participation status. Congregation management systems hold these attributes without allocating on them; seating planners allocate without holding them.

Third, a **controlled reallocation gap** persists. Last-minute editing and manual adjustment are not equivalent to a workflow in which changed data is submitted, a repair is computed against the published plan under a movement-minimizing objective, a new version is produced with a movement summary, and only an approved version is published.

Fourth, and most decisively, **no reviewed system can express PJKIT's structural rules at all.** This is a categorical rather than a graded finding: a two-seat allocation unit that must occupy a valid within-row pair and must not span the centre aisle, a tier band whose row boundaries are derived from registration demand and may be shared between adjacent tiers, and a within-tier ordering guaranteeing that no higher-contributing participant sits behind a lower-contributing one of the same tier, are not configurable in any reviewed product.

The research gap is therefore a **combination gap** rather than a single missing feature. This project proposes a controlled seating allocation and reallocation workflow built on a configurable constraint model, not an improvement to seating-chart drawing.

## 2.6 Constraint Modelling and the Computational Character of the Problem

### 2.6.1 Constraint modelling and rule conversion

The proposed system requires human-readable event seating rules to be converted into a structured mathematical model before an optimization solver can process them, an activity known as constraint modelling or constraint formulation. Constraint modelling translates a real-world problem into formal components: decision variables, domains, constraints and an objective function (Rossi et al., 2006). Here the decision variables represent the unknown assignment — the seat assigned to an individual participant, or the seat *pair* assigned to an Emperor registration; the domain of each variable is the set of permissible seat identifiers or valid pairs; and the constraints encode both validity and preference.

The system distinguishes **hard constraints** — rules every valid plan must satisfy, comprising one allocation unit per participant, at most one occupant per seat, exclusion of structurally blocked seats, valid seat range, status eligibility, side-of-hall accessibility placement, valid Emperor pairing with no pair spanning the centre aisle, demand-derived tier-band placement ordered Emperor → Merit → Bodhi with a shareable boundary row, within-tier contribution ordering, and front-to-back packing with centre-out fill of the numbered section — from **soft constraints**, which are preferences satisfied so far as possible, comprising contribution-to-seat-priority alignment, activeness, category suitability, and movement minimization on reallocation. This distinction follows valued constraint satisfaction and constraint optimization, in which preferences, costs and priorities are represented and optimized rather than treated as pass-or-fail conditions (Schiex et al., 1995).

A weighted-sum aggregation of soft-constraint penalties is adopted rather than lexicographic or max-min aggregation, for three reasons. PJKIT's stakeholders described the trade-offs among soft factors as situational rather than strictly ranked, and stated that no single factor is always most important (Section 3.5, Appendix B, E16–E17), which rules out a lexicographic ordering. The relative weights are an organizer-configurable input to be calibrated with stakeholders during the requirement-validation cycle. And a single scalar objective is required by the solver.

Three modelling principles from the constraint-programming literature apply directly. **Linearization**, including Boolean linearization, expresses logical conditions using integer or Boolean variables, which is necessary because CP-SAT requires all constraints and objective coefficients to be integers (Google, n.d.-a); accordingly every penalty and weight in this project is defined on an integer scale, and any fractional cost is scaled to an integer before model construction. **Reification** links the truth of a condition to a Boolean variable — for example, an indicator recording whether a participant's assigned seat differs from their seat in the previous published plan, which is what allows movement to be counted and penalized. **Channeling** links layers of decision variables, connecting an assigned seat identifier to that seat's row, physical position, tier band and priority rank; OR-Tools documents channeling constraints as the standard mechanism for such relationships, implemented through implications or half-reified linear constraints (Google, n.d.-b).

A fourth, domain-specific modelling decision follows from the venue geometry: **physical seat position and seat priority rank are distinct attributes and must never be conflated.** Adjacency and aisle rules operate on physical position, whereas preference alignment operates on priority rank. The two differ because desirability at PJKIT increases toward the centre aisle rather than monotonically along a row (Appendix B, B6), so the most desirable positions are 8 and 9 while the pair structure forbids treating them as adjacent. The mathematical basis for treating the aisle as a structural break rather than an ordinary gap is Sun's (2020) model of aisle-interrupted row geometry.

### 2.6.2 Why the problem requires optimization rather than enumeration

Two distinct claims must be separated, because they are frequently conflated and only one of them establishes the need for a constraint solver.

The first concerns the **infeasibility of manual verification**. Even in the simplified case in which every participant occupies a single seat, assigning 122 participants among the venue's assignable seats admits on the order of 10²⁷¹ distinct ordered assignments. No human allocator can enumerate or verify such a space, and no allocator can demonstrate that a manually produced plan is the best available one under the community's own stated rules. This directly substantiates Problem Statement 1, and it is the correct use of the combinatorial count.

The second concerns **computational hardness**, and a large search space alone does not establish it. The classical linear assignment problem — assigning *n* individuals to *n* seats where the cost of each assignment is independent of all others — also admits *n*! candidate solutions, and is nonetheless solvable in polynomial time by the Hungarian algorithm (Kuhn, 1955). A factorial search space is therefore not by itself evidence that a general-purpose solver is required.

What makes the PJKIT problem computationally hard is its **structure**, which places it outside the linear-assignment class in four ways. An Emperor registration consumes an adjacent *pair* of seats subject to position-dependent validity, making the problem one of matching and packing rather than one-to-one assignment. Within-tier contribution ordering couples participants to one another, so the cost of an assignment is no longer separable per participant–seat pair, which is precisely the condition the Hungarian method requires. Tier-band boundaries are derived from registration demand and may be shared between adjacent tiers, so the band structure is itself decision-dependent rather than fixed input. And the front-to-back packing and centre-out fill rules impose global contiguity conditions rather than per-assignment costs.

Ipsen et al. (2026) establish the relevant complexity result for this class, observing that the seating allocation problem is a special case of the capacitated p-median problem, which is NP-hard (Mu & Tong, 2019). Consequently no exact polynomial-time algorithm is expected, and the practical alternatives are a heuristic without a quality guarantee or an exact solver capable of proving optimality on instances of this size. The latter is what this project adopts, and Section 2.7 compares the candidates.

## 2.7 Comparison of Seating Allocation Methods

| Method | How it works | Strength | Limitation | Suitability for this project |
|---|---|---|---|---|
| Manual assignment | The administrator assigns seats by judgement against a printed or spreadsheet layout. | Flexible; requires no tooling. | Slow, inconsistent between allocators, unverifiable against stated rules, and rework on every change. | Baseline for comparison only. |
| First-come-first-served | Seats assigned in registration order. | Trivial to implement. | Ignores tier, contribution, and seat suitability entirely. | Baseline only. |
| Random allocation | Seats assigned at random among eligible seats. | Useful as a lower bound in evaluation. | Observes no rule. | Weak baseline only. |
| Greedy priority-based | Participants sorted by contribution and each given the best remaining eligible seat. | Rule-aware; approximates current manual practice. | Locally good early decisions can force poor later ones; handles competing soft criteria badly; cannot recover from a dead end. | Baseline representing the current manual heuristic. |
| Region growing with local search (Muñoz et al., 2006) | Seeds each group at a seat and grows the block outward by annexing best-scoring neighbours; improves by local search. | Anytime behaviour; demonstrated at 50,000 seats. | No optimality or completeness guarantee; no solver status; rules embedded in the growth-scoring function rather than declared, so a rule change means an algorithm change. | Literature comparison point; not adopted. |
| Genetic algorithm | Evolves a population of candidate plans by selection, crossover and mutation. | Handles large spaces and complex scoring; used commercially in PerfectTablePlan (Oryx Digital Ltd., n.d.). | Cannot prove optimality; requires parameter tuning; provides no falsifiable status; results vary between runs, which conflicts with the reproducibility requirement (NFR8). | Literature benchmark and possible future comparison. |
| Integer linear / mixed-integer programming | Expresses the problem as linear constraints over integer variables with a linear objective. | Mature exact optimization with strong solvers (Williams, 2013); used for the seating sub-problems of Ipsen et al. (2026) and by Hales and García (2019). | Both ILP and CP-SAT require integer modelling, so that cost is common to either choice. The *differential* cost is that logical and conditional rules — pair validity, contiguity, conditional eligibility, ordering — must be compiled manually into linear form, typically through big-M constructions that are error-prone to author and weaken the relaxation the solver depends on for bounding. | Viable exact alternative; higher modelling effort and risk for this particular rule set. |
| Constraint programming with CP-SAT | Expresses the problem as integer variables with native logical constraints, Boolean indicators and an objective; solves by lazy clause generation with conflict-driven clause learning, linear-relaxation bounding and portfolio search (Stuckey, 2010; Perron & Didier, 2023). | Conditional and structural rules expressed natively through reification and channeling without big-M compilation; proves optimality and reports an explicit status (OPTIMAL, FEASIBLE, INFEASIBLE, MODEL_INVALID, UNKNOWN); deterministic and reproducible; production-grade and free. | Requires careful integer-only modelling; optimality may be claimed only when the status returned is OPTIMAL. | **Selected method.** |

**Selection rationale.** CP-SAT is not claimed to be universally superior to mixed-integer programming. Both are exact, both require integer modelling, and for a problem whose constraints were purely linear a well-formulated MIP model would be an equally defensible choice. CP-SAT is selected because of the particular character of the PJKIT rule set: pair validity, aisle exclusion, tier-band membership with a shareable boundary, within-tier precedence, contiguity of fill, and conditional accessibility placement are all logical rather than arithmetic conditions, and CP-SAT expresses them natively through reification and channeling rather than through hand-authored big-M linearizations that are both laborious to write correctly and detrimental to the bounding relaxation. Its lazy-clause-generation architecture, which combines constraint propagation with conflict-driven clause learning, linear-relaxation bounds and a portfolio of parallel search workers, is designed to prune search spaces of this character while retaining the ability to prove optimality (Stuckey, 2010; Perron & Didier, 2023).

Relative to the heuristic alternatives, CP-SAT provides two properties neither region growing nor a genetic algorithm can: a provable optimality claim, and an explicit falsifiable status that the system reports as part of allocation quality. Under this project's standing rule, a plan is never represented as optimal unless CP-SAT returns OPTIMAL; a FEASIBLE result reached at the time budget is reported as OPTIMAL_NOT_PROVEN (FR7). Determinism matters equally: NFR8 requires identical output for identical input, which a stochastic population-based method cannot guarantee. The greedy method is retained as an evaluation baseline representing current manual practice, and the genetic algorithm is noted as a benchmark and possible future comparison.

## 2.8 Literature Synthesis Against the Problem Statements

**Problem Statement 1.** Reviewed commercial systems offer guest management and visual seating but no configurable rule layer over PJKIT's participant attributes, and the reviewed academic studies offer exact methods only in bespoke, non-configurable formulations (Ipsen et al., 2026; Hales & García, 2019) or heuristic methods without quality guarantees (Muñoz et al., 2006). The proposed system is designed to address this through configurable hard and weighted soft constraints solved by a general-purpose exact solver, with the intention of making allocation consistent between allocators, repeatable across runs, and explainable through a per-constraint penalty breakdown.

**Problem Statement 2.** Manual editing and synchronization features do not constitute controlled reallocation. In this project, reallocation is defined as incremental repair of the published plan: unaffected assignments are locked, only affected assignments and a bounded surrounding neighbourhood are reconsidered, the number of unaffected participants moved is minimized ahead of movement distance, the result is stored as a new version, and publication requires explicit approval. This mechanism instantiates two established techniques — large neighbourhood search (Shaw, 1998) and minimal-perturbation repair (El Sakkout & Wallace, 2000) — with a movement-dominant objective whose structure corresponds to the switching-cost formulation of Hoang (2022). The intent is change *optimization* rather than change handling.

**Problem Statement 3.** Printed lists and organizer-driven distribution leave participants without assurance that they are reading the current plan. The proposed participant-facing lookup is designed to provide a route on which a participant sees only their own assignment, drawn only from the latest approved published version.

**Boundary of the contribution.** The academic contribution of this project lies in the first two objectives: the modelling of a real community assembly's seating rules — including multi-seat allocation units, demand-derived tier bands with shareable boundary rows, aisle-aware adjacency and within-tier precedence ordering — as a configurable constraint optimization problem, and the design of a stability-preserving incremental repair mechanism for plans that have already been published to the people they affect. The participant-facing lookup of Objective 3 is a necessary system module that closes the operational loop by ensuring participants read only approved current data; it resolves Problem Statement 3 and is not presented as an algorithmic contribution.

---

# Replacement paragraph for Section 1.2 (Background of Study)

Replace the sentence beginning *"The number of possible assignments grows explosively with scale…"* with the following. This removes the misleading inference while keeping the persuasive force of the number, and defers the formal hardness argument to Section 2.6.2.

> Each participant must be matched to exactly one seat within a limited seating layout, and every assignment must simultaneously satisfy a set of interrelated event-specific rules. The number of candidate arrangements is beyond human verification: even in the simplified case in which each of the 122 participants of the validated case-study scenario occupies a single seat, the venue's assignable seats admit on the order of 10²⁷¹ distinct ordered assignments. No allocator working by hand can survey such a space, and none can demonstrate that a manually produced plan is the best available arrangement under the community's own stated rules — which is the origin of the inconsistency and unjustifiability described later in this section. The seating allocation task is, moreover, computationally hard in its own right and not merely large: as established in Section 2.6.2, the structural rules that govern PJKIT seating — two-seat allocation units, contribution ordering within a tier, demand-derived tier bands, and contiguous row filling — place the problem outside the class of assignment problems solvable by classical polynomial-time methods (Ipsen et al., 2026; Mu & Tong, 2019).

**Also fix in the same paragraph:** change "150 participants" to the canonical figure used in NFR1 and NFR6 (122), and recompute the exponent if you prefer to state a different participant count. For 122 participants among 232 assignable seats the figure is approximately 10²⁷¹; for 150 it is approximately 8.75 × 10³²⁶ (the value currently printed, which is arithmetically correct for 150). State also how many seats fall in the numbered section as distinct from the free-seating section, since only the numbered section is solver-allocated.

---

# References to add

Add these to Section 5, in correct alphabetical position, and correct the existing entries noted in `Interim_Report_Rubric_Evaluation.md` §4.

```
Awadallah, M. A., Khader, A. T., Al-Betar, M. A., & Woon, P. C. (2012). Office-space-allocation
    problem using harmony search algorithm. In Proceedings of the International Conference on
    Neural Information Processing (pp. 365–374).

Barry, M., Gambella, C., Lorenzi, F., Sheehan, J., & Ploennigs, J. (2021). Optimal seat allocation
    under social distancing constraints. arXiv preprint arXiv:2105.05017.

El Sakkout, H., & Wallace, M. (2000). Probe backtrack search for minimal perturbation in dynamic
    scheduling. Constraints, 5(4), 359–388.

Google. (n.d.-a). CP-SAT solver. Google for Developers — OR-Tools. Retrieved June 2026, from
    https://developers.google.com/optimization/cp/cp_solver

Google. (n.d.-b). Channeling constraints. Google for Developers — OR-Tools. Retrieved June 2026,
    from https://developers.google.com/optimization/cp/channeling

Hales, R. O., & García, S. (2019). Congress seat allocation using mathematical optimization.
    TOP, 27(3), 426–455.

Hoang, K. D. (2022). Dynamic continuous distributed constraint optimization problems
    [Doctoral dissertation, Washington University in St. Louis].

Kuhn, H. W. (1955). The Hungarian method for the assignment problem. Naval Research Logistics
    Quarterly, 2(1–2), 83–97.

Mu, W., & Tong, D. (2019). On solving large p-median problems. Environment and Planning B:
    Urban Analytics and City Science, 47(6), 981–996.

Object Management Group. (2017). Unified Modeling Language (UML) specification, version 2.5.1.

Pisinger, D., & Ropke, S. (2010). Large neighborhood search. In M. Gendreau & J.-Y. Potvin (Eds.),
    Handbook of metaheuristics (2nd ed., pp. 399–419). Springer.

Schiex, T., Fargier, H., & Verfaillie, G. (1995). Valued constraint satisfaction problems: Hard and
    easy problems. In Proceedings of the 14th International Joint Conference on Artificial
    Intelligence (IJCAI-95) (pp. 631–639). Morgan Kaufmann.

Shaw, P. (1998). Using constraint programming and local search methods to solve vehicle routing
    problems. In Proceedings of the 4th International Conference on Principles and Practice of
    Constraint Programming (CP-98) (pp. 417–431). Springer.

Stoll, M. (2022). Solutions to the distance constrained cinema seating problem
    [Master's thesis, Utrecht University].

Ülker, O. (2013). Office space allocation by using mathematical programming and meta-heuristics
    [Doctoral dissertation, University of Nottingham].

Verfaillie, G., & Schiex, T. (1994). Solution reuse in dynamic constraint satisfaction problems.
    In Proceedings of the 12th National Conference on Artificial Intelligence (AAAI-94)
    (pp. 307–312).

Williams, H. P. (2013). Model building in mathematical programming (5th ed.). Wiley.
```

Also add the Müller / Rudová / Barták minimal-perturbation timetabling paper once you have selected and read a specific one from that series.

---

# Sources to obtain before submission

Of the works cited in this revision, the following **have been read in full** and the claims made about them are verified: **Ipsen et al. (2026)**, **Muñoz et al. (2006)**, **Sun (2020)** and **Hoang (2022)**. The CP-SAT architectural claims attributed to **Perron and Didier (2023)** and **Stuckey (2010)** are consistent with published summaries of those works but the papers themselves have not been read end to end.

The following are recommended **from domain knowledge and have not been retrieved or read**. Obtain and read each before citing, and confirm the exact author list, year, venue and page range — do not cite from another paper's bibliography:

| Source | Purpose in the revision | Status |
|---|---|---|
| Hales & García (2019) | Legislative-chamber seat allocation; §2.2 | Listed in Ipsen et al.'s bibliography; **not read** |
| Barry et al. (2021) | Distance-constrained venue seating; §2.2 | Listed in Ipsen et al.'s bibliography; **not read** |
| Stoll (2022) | Fixed-row cinema seating with adjacency; §2.2 | Listed in Ipsen et al.'s bibliography; **not read** |
| Mu & Tong (2019) | NP-hardness of p-median; §2.6.2 | Cited via Ipsen et al.; **not read** |
| Ülker (2013); Awadallah et al. (2012) | Office space allocation scope boundary; §2.2 | Listed in Ipsen et al.'s bibliography; **not read** |
| Shaw (1998); Pisinger & Ropke (2010) | Large neighbourhood search; §2.3 | **Not read** |
| El Sakkout & Wallace (2000) | Minimal perturbation in dynamic scheduling; §2.3 | **Not read** |
| Verfaillie & Schiex (1994) | Solution reuse in dynamic CSP; §2.3 | **Not read** |
| Müller / Rudová / Barták, minimal perturbation in course timetabling | Closest structural analogue for Objective 2; §2.3 | Specific paper **not yet selected or read** |
| Kuhn (1955) | Polynomial solvability of linear assignment; §2.6.2 | Standard result; primary source **not read** |

Two further verifications are needed regardless: confirm whether **Muñoz et al.** is 2005 or 2006 and whether the third author is López or Esteva (the retrieved copy lists Víctor Muñoz, Miquel Montaner and Beatriz López of Universitat de Girona), and confirm whether **Gay** is a listed author on the CP 2023 CP-SAT-LP paper.

Finally, the two claims about examination/classroom seating tools and congregation management systems in §2.4 are stated from general product knowledge and need a specific named product and documentation page each before they can stand as evidence in Table 2.1. Choose one representative product per category, inspect its documentation, and cite it as you have done for Cvent and PerfectTablePlan — otherwise soften both rows to "not documented."
