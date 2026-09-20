# Interim Report — Targeted Revisions

**Target document:** `Draft_Interim_Report_To_GPT` (your current submission draft)
**Basis:** `Interim_Report_Rubric_Evaluation.md`, `Literature_Review_Response_Roadmap.md`, `Literature_Review_Comment.md`, `revised_section2_literature_review.md`
**Approach:** Sentence-level and paragraph-level replacements only, preserving your original wording and register wherever the original is defensible. Whole paragraphs are replaced only where the paragraph does not currently exist (Scope of Study, Future Work, §3.4) or where the roadmap requires new material (Literature Review additions).

**Abstract is deliberately excluded** — to be drafted after you confirm the sections below.

### Confirmed scenario used throughout

| Quantity | Value |
|---|---|
| Participants (people) | **150** |
| Emperor | 112 participants, attending as couples, forming **56** two-seat registrations → 112 seats |
| Merit | 22 participants → 22 seats |
| Bodhi | 16 participants → 16 seats |
| Allocation units (solver decision units) | **94** (56 Emperor pairs + 22 Merit + 16 Bodhi) |
| Occupied seats | **150** |
| Venue | 16 rows × 16 seats = 256; 8 seats per side of the centre aisle (aisle between positions 8 and 9); **232** assignable after the 24-seat structural block |
| Empty assignable seats | **82** (rows 11–16 remainder, forming the free-seating section) |
| Tier band order | **Emperor → Merit → Bodhi** from the front; boundary rows may be shared |
| Computed bands for this scenario | Emperor rows 1–9, Merit rows 9–10, Bodhi rows 10–11 (rows 9 and 10 shared) |

Your report's existing figure of **150 participants** in §1.2 and §2.3 is therefore correct and stays. It is **NFR1 and NFR6** that carry the stale figure of 122 and need updating (see §1.6 below). `CLAUDE.md` has been updated to match this scenario.

---

# Section 1.2 — Background of Study

## Revision 1.2-A — the combinatorial claim (the misleading sentence)

**Reason:** A large search space does not by itself establish computational hardness — the classical linear assignment problem also admits a factorial number of candidates and is still solvable in polynomial time by the Hungarian algorithm. As written, the sentence only establishes that naive enumeration is impractical, which no method proposes, so it does not justify the need for a constraint solver. The revision keeps your number and your point about manual infeasibility, and adds the structural argument that does carry the claim.

**Original:**

> The number of possible assignments grows explosively with scale, which even in the simplified case where each of the case study's 150 participants assigned a single seat among a venue that can support up to 232 seats, the number of possible ordered seat assignments is denoted as 232!/(232 - 150)! approximately 8.75 × 10^326 of possible combinations for the seating plan, which is infeasible to check manually by human and it is impractical for machine to enumerated it naively (Rossi et al., 2006).

**Revised:**

> The number of possible assignments grows explosively with scale. Even in the simplified case where each of the case study's 150 participants is assigned a single seat among a venue that can support up to 232 seats, the number of possible ordered seat assignments is denoted as 232!/(232 − 150)!, which is approximately 8.75 × 10^326 possible combinations for the seating plan. No event administrator working by hand can survey a space of this size, and none can demonstrate that a manually produced seating map is the best available arrangement under the community's own stated rules (Rossi et al., 2006). The seating allocation task is also computationally hard in its own right, and not merely large. As discussed in Section 2.6, the structural rules that govern PJKIT seating, which are the two-seat Emperor allocation units, the contribution ordering within each tier, the demand-driven tier bands and the contiguous filling of rows, place this problem outside the class of assignment problems that classical polynomial-time methods can solve (Ipsen et al., 2026; Mu & Tong, 2019).

## Revision 1.2-B — add the Emperor pairing rule to the tier description

**Reason:** Emperor two-seat pairing is the most distinctive rule in the case study and the one no reviewed commercial tool can express, yet the Background never mentions it. It is currently introduced for the first time in Section 3.5.3. One sentence inserted into your existing tier paragraph closes this.

**Insert after your existing sentence** *"…and every Merit row should precede the first Bodhi row."*:

> A further characteristic of PJKIT registration is that Emperor participants attend as couples, so one Emperor registration occupies two adjacent seats rather than one. In the validated scenario of 150 participants, the 112 Emperor participants therefore form 56 two-seat registrations, and the seating map carries only 56 Emperor names across 112 occupied seats. Together with the 22 Merit and 16 Bodhi participants, the event administrator is in effect allocating 94 allocation units into 150 seats of the numbered section, and the two seats of an Emperor registration must be adjacent within the same row and must never be separated by the centre aisle that divides the eight seats on each side of the hall.

## Revision 1.2-C — language corrections (no content change)

| Original | Revised |
|---|---|
| "PJKIT), organized large annual community events that consisted of 100 to 200 participants" | "PJKIT), organizes large annual community events that consist of 100 to 200 participants" |
| "participant records are first store in excel spreadsheets" | "participant records are first stored in Excel spreadsheets" |
| "the created seating plan will then be will convert into PDF document" | "the created seating plan will then be converted into a PDF document" |
| "**Figure 1 PJKIT''s annual event venue layout**" | "**Figure 1 PJKIT's annual event venue layout**" |
| "The seating boundaries for each tier are not a fixed zone, but it is determined by the demand." | "The seating boundaries for each tier are not fixed zones, but are determined by the demand." |
| "Whole WeddingWire and Zola offer similar features" | "While WeddingWire and Zola offer similar features" |
| "requires an error -prone rework on a nearly completed seating plan" | "requires an error-prone rework on a nearly completed seating plan" |
| "the seating row could be shred between two different tiers" (§3.5.2 table) | "the seating row could be shared between two different tiers" |

---

# Section 1.3 — Problem Statement

## Revision 1.3-A — broken cross-reference

**Original:** "…identified from the background of study in Section 3.1 and validated against the current event seating map generation workflow of PJKIT."

**Revised:** "…identified from the background of study in Section 1.2 and validated against the current event seating map generation workflow of PJKIT."

---

# Section 1.4 — Objectives

## Revision 1.4-A — add justification and feasibility

**Reason:** The rubric awards the top band for objectives *"clearly stated and justified towards answering the problem statement, and achievable within the time frame."* Your three objectives are clear and map cleanly onto the three problem statements, but nothing states how each will be judged, and the measurable criteria you already hold in Section 1.5.4 are not visible from here.

**Insert as a closing paragraph after Objective 3:**

> Each objective is measurable against a criterion defined in Section 1.5.4 and is scoped to the project timeline in Section 3.7. Objective 1 is judged by whether the solver function returns an OPTIMAL result within the configured solver budget for the validated 150-participant scenario, with an independent validator confirming zero hard-constraint violations (NFR1, FR16). Objective 2 is judged by whether an ad hoc participant change is accommodated while minimizing first the number of unaffected participants moved and then the total movement distance, measured against the latest published seating map (G2.1, FR9). Objective 3 is judged by whether a participant retrieves the correct assigned seat from the latest published version only, with unpublished versions never exposed (G3.1, FR14). All three objectives are confined to the seating allocation module of the existing Netizen eXperience event management platform rather than to a new platform, which is what makes them achievable within the twenty-eight-week schedule.

---

# Section 1.5 — Scope of Study (NEW SECTION)

**Insert as a new Section 1.5, and renumber the current Section 1.5 "System Goal and Requirements" to Section 1.6** (updating its internal references 1.5.1 → 1.6.1, 1.5.2 → 1.6.2, 1.5.3 → 1.6.3, 1.5.4 → 1.6.4, and every cross-reference to them elsewhere in the report).

**Reason:** The rubric carries a dedicated criterion, "Scope of Study, including relevancy and feasibility," which the report currently has no section answering. The five modules are adapted from the project scope definition, and the exclusions are stated explicitly because deliberate bounding is what the criterion rewards.

## 1.5 Scope of Study

The scope of this project consists of five (5) modules, of which the first, the design and development of the seat allocation solver function, is the principal technical and research contribution. The scope defined below represents the workload to be completed by December 2026.

**1.5.1 Seat Allocation Engine and Solver Function Development.** The primary scope is the design and development of the seat allocation engine. The engine receives structured input, which are the participant profiles, the seating layout, the constraint configuration, and the previously published allocation where one exists, and it generates a seating allocation result. The event-specific rules of PJKIT are modelled as programmable constraint expressions, where hard constraints represent the mandatory rules that every valid seating map must satisfy and weighted soft constraints represent the preferences to be optimized. The output of the engine includes the participant-to-seat assignments together with the quality indicators, which are the solver status, the independent hard-constraint validation result, the total weighted soft-constraint penalty with a per-constraint breakdown, the movement count and distance where applicable, and the runtime. This module is the core research contribution of the project because it determines how a seating map can be generated systematically from participant profiles and modelled event rules, including the modelling of the two-seat Emperor allocation units, the aisle-aware adjacency, the demand-driven tier bands ordered Emperor → Merit → Bodhi with shareable boundary rows, and the within-tier contribution ordering.

**1.5.2 Event Administrator Seat Allocation Management Module.** The system includes an administrator-side management module through which the event administrator operates the engine, which covers preparing or selecting the participant data, configuring the seating-related settings and soft-constraint weights, generating the seating map, reviewing the generated result and its quality indicators, regenerating where necessary, and approving or publishing a selected version. Versioning and publishing are part of this module, where every generated result is treated as a version that the event administrator may compare and review, and only the approved or latest published version is made available to participants. This module is included in the scope because seating allocation must remain under the control of the event administrator, as the system is intended to support the decision rather than to replace the human review that PJKIT's senior volunteers currently perform.

**1.5.3 Event Participant Seat Lookup.** The system supports a participant-facing seat lookup based on the latest approved allocation, through which a participant can view their assigned seat number and refer to the event seating map after the event administrator has published the plan. This module addresses the current dependence on printed seating maps, PDF listings shared through WhatsApp, and asking event staff to check manually. The detailed authentication implementation is treated as a supporting function inherited from the host platform rather than as a research focus of this project.

**1.5.4 Configurable Constraint-Based Allocation.** The system supports configurable constraint-based allocation, in which the event-specific seating rules are represented as hard constraints and weighted soft constraints before being processed by the engine. The hard constraints include one allocation unit per participant, at most one occupant per seat, exclusion of the structurally blocked seats in the centre of the hall, valid event seat range, participant status eligibility, side-of-hall placement for participants who require an accessible seat, demand-driven tier-band placement ordered Emperor → Merit → Bodhi with a boundary row shareable between two adjacent tiers, Emperor two-seat pairing restricted to the valid within-row pairs and never straddling the centre aisle between positions 8 and 9, within-tier contribution ordering, and the front-to-back packing and centre-out fill of the numbered section. The soft constraints include contribution-to-seat-priority alignment, activeness score, category suitability, and movement minimization upon reallocation, together with a deterministic tie-breaking term scaled so that it can never override any weighted penalty. The soft-constraint weights carry no fixed ranking and are configurable per event, which reflects the situational trade-offs described by the PJKIT stakeholders during elicitation. This module ensures that the system generates rule-consistent and priority-aware seating maps rather than random or merely sequential assignments. The full constraint listing is given in Section 3.5.3.

**1.5.5 Dynamic Reallocation upon Participant Data Changes.** The system supports dynamic reallocation as the controlled incremental repair of an already-published seating map following participant data changes, which for PJKIT are principally the absence of a registered participant and the substitution of that participant on the event day. Dynamic reallocation is deliberately distinguished from the initial plan generation in Section 1.5.1. Where generation solves a global problem over every participant and every seat before any seating map exists, reallocation treats the published seating map as the baseline state and processes only the change. The system classifies participants as affected, which covers the absent participant, the replacement participant and any occupant of a candidate seat drawn into the repair, or as unaffected, whose assignments are preserved. The repair follows an escalation hierarchy in which a direct substitution into the released seat is attempted first, a reduced repair model over the affected participants and a bounded neighbourhood of candidate seats is solved next, and the neighbourhood is expanded progressively only when the smaller repair proves infeasible. A complete regeneration of the seating map remains available but only as a final fallback that the event administrator must explicitly invoke, so that the system never silently triggers a whole-plan change during an event. Every repaired result is stored as a new version with a movement summary and requires review before approval and publication.

**1.5.6 Out of Scope.** The following are explicitly excluded from this project. The implementation of authentication and user account management is inherited from the host platform and is not developed here. The construction of a venue layout drawing or floor-plan editing tool is excluded, as the layout is supplied as structured data. Generalization of the constraint configuration to organizers other than PJKIT is not attempted within the FYP timeline, although the constraint configuration is deliberately isolated from the solver logic (NFR4) so that such generalization remains possible afterwards. The implementation and tuning of a genetic algorithm is excluded and is retained only as a literature benchmark for comparison, as discussed in Section 2.7. Finally, the free-seating section at the back of the hall is outside the allocation scope, because PJKIT does not assign numbered seats there.

**1.5.7 Feasibility.** The scope is feasible within the twenty-eight-week schedule in Section 3.7 for three reasons. First, the solver function is a self-contained component with a JSON input and output contract, so it can be developed and evaluated independently of the host platform and integrated afterwards. Second, the case study is bounded and already validated, at 150 participants and a 232-seat assignable layout, which is small enough for an exact solver to prove optimality within the configured budget and therefore does not require the project to also solve a scalability problem. Third, the collaboration with Netizen eXperience provides existing platform infrastructure, so the project does not need to build event management, participant registration or data persistence from the beginning.

---

# Section 1.6 — System Goal and Requirements (renumbered from 1.5)

## Revision 1.6-A — broken cross-reference

**Original:** "…decomposes the single root goal derived from the vision statement in Section 2 into a goal tree…"

**Revised:** "…decomposes the single root goal derived from the vision statement in Section 1.1 into a goal tree…"

## Revision 1.6-B — NFR1, align with the confirmed scenario

**Original:** "The system shall return an OPTIMAL result within the configured 60-second solver budget for the default dataset of 122 registrations and the 256-seat (232-assignable) case-study layout under the defined evaluation environment…"

**Revised:** "The system shall return an OPTIMAL result within the configured 60-second solver budget for the default dataset of 150 participants, which comprises 94 allocation units after the 112 Emperor participants are paired into 56 two-seat registrations, on the 256-seat (232-assignable) case-study layout under the defined evaluation environment…"

## Revision 1.6-C — NFR6, align with the confirmed scenario

**Original:** "The system shall support the validated operational baseline of 122 registrations and the 232-assignable-seat layout and shall treat larger datasets as exploratory scalability experiments paired with layouts of sufficient capacity."

**Revised:** "The system shall support the validated operational baseline of 150 participants (94 allocation units, 150 occupied seats) on the 232-assignable-seat layout and shall treat larger datasets as exploratory scalability experiments paired with layouts of sufficient capacity."

## Revision 1.6-D — MG1, state the default scenario

**Original:** "…(validated baseline: 100-200 participants; 256-seat venue with 232 assignable seats)…"

**Revised:** "…(validated baseline: 100–200 participants, with a default evaluation scenario of 150 participants; 256-seat venue with 232 assignable seats)…"

---

# Section 2 — Literature Review

The literature review is revised in four ways: two new subsections are added (§2.1 search strategy and §2.3 reallocation literature), the current opening paragraph is expanded into a proper subsection with per-study critical analysis and an explicit gap statement, the complexity argument is corrected, and a number of targeted sentence fixes are applied. Your existing §2.1 (existing systems) and §2.2 (white space analysis) prose is retained, with additions rather than rewrites.

**Resulting structure** (renumbering your current subsections):

| New | Content |
|---|---|
| 2.1 | Literature Search Strategy — **NEW** |
| 2.2 | Academic Studies on Seating and Space Allocation — expanded from your current opening paragraph |
| 2.3 | Stability-Preserving Reallocation and Repair-Based Optimization — **NEW** |
| 2.4 | Existing Seat and Space Allocation Systems — your current 2.1, table expanded |
| 2.5 | White Space Analysis — your current 2.2, one column added |
| 2.6 | Constraint Modelling and the Computational Character of the Problem — your current 2.3, corrected |
| 2.7 | Comparison of Seating Allocation Methods — your current 2.4, one cell revised |
| 2.8 | Literature Synthesis Against Problem Statements — your current 2.5, with contribution boundary added |

The full replacement text for all eight subsections is in **`revised_section2_literature_review.md`**. The items below are the specific reasons each change is made, so you can decide what to accept.

## Revision 2-A — the gap sentence in the opening paragraph

**Reason:** This is the single most attackable sentence in Section 2. It does not parse, it states the gap in absolute form (which the examiner comment explicitly warned against), and it never says what the reviewed works fail to do, so the claim rests on nothing.

**Original:**

> By combines a general-purpose constraint solver, a provable optimality guarantee, and a stability-preserving reallocation mechanism in one system that this project delivers using Google OR-Tools CP-SAT (CP-SAT Solver, n.d.; Perron et al., 2023), a solver built on the lazy clause generation paradigm (Stuckey, 2010) that natively expresses PJKIT's tier, pairing, and ordering rules as integer and Boolean constraints without hand-compiled linearization.

**Revised:**

> None of the reviewed studies provides the combined capability that the PJKIT case requires. Ipsen et al. (2026) and Hales and García (2019) achieve exact optimization, but through bespoke formulations built for one venue and one rule set, with no configurable rule layer and no mechanism for repairing a seating map that has already been published. Muñoz et al. (2006) achieve scale and anytime behaviour, but with no optimality guarantee and no explicit solver status. Sun (2020) models venue geometry but does not address allocation. None of the reviewed works models a multi-seat allocation unit, a demand-driven tier band with a shareable boundary row, or a contribution ordering among individuals within a tier. This project therefore intends to combine a general-purpose constraint solver, a provable optimality claim with explicit status reporting, and a stability-preserving reallocation mechanism in one system, using Google OR-Tools CP-SAT (Google, n.d.-a; Perron & Didier, 2023), a solver built on the lazy clause generation paradigm (Stuckey, 2010) that natively expresses PJKIT's tier, pairing and ordering rules as integer and Boolean constraints without hand-compiled linearization.

Note the hedge: **"none of the reviewed studies"** rather than "none exists." This is the defensible form of the claim, and it is what your literature review actually demonstrates.

## Revision 2-B — the complexity paragraph in your current §2.3

**Reason:** Same defect as Revision 1.2-A, in the same words. The revision separates the two claims that are currently conflated.

**Original:**

> Modelling matters because the problem is combinatorial: even ignoring Emperor pairing, assigning 150 participants into the PJKIT layout's 232 assignable seats admits 232!/(232-150)! ordered assignments, a scale at which exhaustive checking is impractical and at which nested-loop, if-else programming becomes difficult to maintain, slow to search, and weak at arbitrating conflicting preferences.

**Revised:**

> Modelling matters for two separate reasons that should not be conflated. The first is the size of the space. Even ignoring Emperor pairing, assigning 150 participants into the PJKIT layout's 232 assignable seats admits 232!/(232 − 150)! ordered assignments, a scale at which exhaustive checking is impractical and at which nested-loop, if-else programming becomes difficult to maintain, slow to search, and weak at arbitrating conflicting preferences. The second, and the one that determines the choice of solving method, is that the problem is computationally hard and not merely large. A large search space alone does not establish hardness, because the classical linear assignment problem also admits a factorial number of candidate assignments and is nonetheless solvable in polynomial time by the Hungarian algorithm (Kuhn, 1955). What places the PJKIT problem outside that class is its structure. An Emperor registration consumes an adjacent pair of seats subject to position-dependent validity, which makes the problem one of matching and packing rather than one-to-one assignment. The within-tier contribution ordering couples participants to one another, so the cost of an assignment is no longer separable per participant-seat pair, which is the condition the Hungarian method requires. The tier-band boundaries are derived from registration demand and may be shared between adjacent tiers, so the band structure is itself decision-dependent rather than fixed input. Ipsen et al. (2026) establish the relevant result for this class, observing that the seating allocation problem is a special case of the capacitated p-median problem, which is NP-hard (Mu & Tong, 2019). No exact polynomial-time algorithm is therefore expected, and the practical alternatives are a heuristic without a quality guarantee or an exact solver able to prove optimality on instances of this size.

## Revision 2-C — the ILP/MIP limitation cell in the comparison table

**Reason:** The cell currently ends by conceding that "both ILP and CP-SAT require integer modelling, so this cost is not avoided by CP-SAT's alternative," which blunts the differentiator inside the very table meant to establish it. The revision keeps the honesty but separates the shared cost from the differential one.

**Original limitation cell:** "Logical and conditional rules (pairing, adjacency, if-then eligibility) must be manually compiled into linear form, typically via big-M constructions that are error-prone and weaken relaxations; no native reification or channeling; both ILP and CP-SAT require integer modelling, so this cost is not avoided by CP-SAT's alternative."

**Revised limitation cell:** "Both ILP and CP-SAT require integer modelling, so that cost is common to either choice. The differential cost is that logical and conditional rules, which for PJKIT are the pair validity, the aisle exclusion, the contiguous filling and the conditional eligibility, must be compiled manually into linear form, typically through big-M constructions that are error-prone to author and that weaken the relaxation the solver relies on for bounding. There is no native reification or channeling."

## Revision 2-D — the selection rationale, and a stray artifact

**Reason:** Two fixes. The rationale should state plainly that CP-SAT is not claimed to be universally better, which is the answer to the most likely viva question on this point. There is also a stray fragment in the text.

**Original contains:** "Relative to the published seating 5 / 20 heuristics - region growing and GA - CP-SAT provides…"

The fragment **"5 / 20"** is a stray artifact and must be deleted.

**Insert at the start of the selection rationale paragraph:**

> CP-SAT is not claimed to be universally superior to mixed-integer programming. Both are exact, both require integer modelling, and for a problem whose constraints were purely linear a well-formulated MIP model would be an equally defensible choice. CP-SAT is selected because of the particular character of the PJKIT rule set, in which the pair validity, the aisle exclusion, the tier-band membership with a shareable boundary, the within-tier precedence and the contiguity of filling are all logical rather than arithmetic conditions.

**Also update the citation key** "(Google, n.d.-a)" at the end of that paragraph so that it matches a reference list entry — see the reference corrections at the end of this document.

## Revision 2-E — reframe the superseded Muñoz rules

**Reason:** If it is unclear what the literature contributed after two of its rules were discarded, an examiner will ask. The reframing shows the literature supplied the constraint *category* while your validation against the historical charts determined its *content*, which is evidence-based elicitation and a methodological strength.

Where you discuss Muñoz et al.'s optional rules, use:

> Their optional rules identified a class of constraint that had not been considered during the initial elicitation for PJKIT, which is the class of rules governing row-level packing and the distribution of vacant seats. Comparison against PJKIT's historical 2023 and 2024 seating charts then determined the specific form this class takes at PJKIT. Rather than avoiding isolated seats and edge gaps, PJKIT packs each row outward from the centre aisle and fills the numbered section from front to back with no vacant seat, which is recorded as constraints C15 and C16 in Section 3.5.3. The literature therefore supplied the constraint category and the empirical validation determined its content.

## Revision 2-F — contribution boundary in the synthesis

**Reason:** The examiner's likely question is why a participant lookup belongs in an optimization FYP. State the boundary rather than defending the lookup as a research contribution.

**Append to the end of your current §2.5:**

> The academic contribution of this project lies in the first two objectives, which are the modelling of a real community assembly's seating rules as a configurable constraint optimization problem, including the multi-seat allocation units, the demand-driven tier bands with shareable boundary rows, the aisle-aware adjacency and the within-tier contribution ordering, and the design of a stability-preserving incremental repair mechanism for seating maps that have already been published to the participants they affect. The participant-facing seat lookup in Objective 3 is a necessary system module that closes the operational loop by ensuring that participants read only approved and current seating information. It resolves Problem Statement 3 and is not presented as an algorithmic contribution.

## Revision 2-G — citation consistency

| Issue | Fix |
|---|---|
| "Muñoz et al. (2006)" in the opening paragraph and Conclusion, "Muñoz et al. (2005)" in §2.5 | Use one year throughout, matching the reference list entry, after verifying which version you hold |
| "Perron et al., 2023" and "Perron & Didier, 2023" both used | Use one form throughout |
| "(CP-SAT Solver, n.d.)" used for both the CP-SAT page and the channeling page | Split into "(Google, n.d.-a)" for the solver page and "(Google, n.d.-b)" for channeling |
| "(Google, n.d.-a)" cited but no matching list entry | Resolved by the reference list corrections below |

---

# Section 3 — Methodology

## Revision 3-A — broken figure references

| Location | Original | Revised |
|---|---|---|
| §3.1 | "Based on the Figure 8 above, each sprint in Agile SCRUM framework…" | "Based on Figure 3 above, each sprint in the Agile SCRUM framework…" |
| §3.2.4 | "Based on Figure 9 above, the first layer of the architecture model…" | "Based on Figure 7 above, the first layer of the architecture model…" |
| §3.6.1 | "**Figure 3** Event Administrator Seating Allocation Dashboard" | "**Figure 10** Event Administrator Seating Allocation Dashboard" |
| §3.6.2 | "**Figure 4** Event Participant Seat Lookup Interface" | "**Figure 11** Event Participant Seat Lookup Interface" |

After these changes, verify the whole document runs Figure 1 to Figure 11 with no duplicates: Figure 1 venue layout, Figure 2 goal tree, Figure 3 SCRUM sprint, Figure 4 use case, Figure 5 system flowchart, Figure 6 state machine, Figure 7 architecture, Figure 8 class diagram, Figure 9 swimlane, Figure 10 admin dashboard, Figure 11 participant lookup. If the §3.4 lifecycle diagram is also numbered, insert it in sequence and renumber the rest.

## Revision 3-B — typographical corrections

| Location | Original | Revised |
|---|---|---|
| §3.2.3 | "the returned solver status is INFEASIBLE, INVALID or TIEMOUT" | "…INFEASIBLE, INVALID or TIMEOUT" |
| §3.2.3 | "is in the single stagble resting state of the system" | "is in the single stable resting state of the system" |
| §3.2.6 caption | "Activity Diagram of the Generate Seating Plan use case in the propsoed system" | "…in the proposed system" |
| §3.5.1 | "The sire visit combined a semi-structured interview" | "The site visit combined a semi-structured interview" |
| §3.5.2 | "were obtained via the elicitation processes (Section 9)" | "…(Section 3.5.1)" |

## Revision 3-C — Section 3.4, the unfilled placeholder

**Reason:** Section 3.4 currently contains only the text "Write the explantion". An unfilled placeholder in a submitted document is damaging out of proportion to its length. The lifecycle below is written to match the stages already described in the use case main success scenario in Section 3.2.2, so it should be consistent with whatever diagram you have placed there.

**Replace "Write the explantion" with:**

The seating allocation optimization lifecycle describes how a plain-language seating rule from PJKIT becomes a validated seating map, and it is the process that the solver function implements. The lifecycle has seven (7) stages, and each stage is a distinct transformation with its own output artifact.

The first stage is **rule elicitation**, where the seating rules are gathered from the PJKIT stakeholders through the interview, the joint application development workshop and the direct observation described in Section 3.5.1, and are recorded in plain language.

The second stage is **constraint classification**, where each elicited rule is classified either as a hard constraint that every valid seating map must satisfy, or as a weighted soft constraint that represents a preference to be optimized. The output of this stage is the constraint listing in Section 3.5.3.

The third stage is **mathematical formulation**, where each classified rule is expressed as a mathematical statement over decision variables, using the linearization, reification and channeling principles described in Section 2.6. The output is the constraint optimization problem formulation in Section 3.5.4.

The fourth stage is **pre-model validation**, where the incoming payload is checked against its schema, the tier bands are derived from the registration demand of the event, and the capacity of each band is verified before any model is constructed. A failure at this stage returns a structured error without invoking the solver, which is what FR15 requires.

The fifth stage is **model construction**, where the decision variables are created only for eligible combinations, that is, only for participant-seat combinations permitted by the participant's tier band and only for the venue's valid Emperor pairs. The hard constraints are then added and the weighted soft-constraint penalties are assembled into a single integer objective together with the deterministic tie-breaking term.

The sixth stage is **solving and extraction**, where the CP-SAT solver function searches within the configured time budget and returns both a solution and an explicit solver status. The assignments and the per-constraint penalty breakdown are extracted from the solution, and the status is preserved so that a FEASIBLE result is never reported as optimal.

The seventh stage is **independent validation and result formatting**, where the extracted seating map is re-checked against every hard constraint by a validator implemented independently of the solver, including a reconstruction of the reported objective value, before the result is serialized into the frontend-consumable JSON structure and stored as a new plan version. This separation is deliberate, because a solver that is trusted to check its own output provides no assurance that the model expressed the intended rules.

The lifecycle is iterative rather than linear. When a demonstration to the PJKIT stakeholders reveals that a modelled constraint behaves differently from the community's intent, the affected rule returns to the second and third stages for reclassification or reformulation, which is the mechanism by which the constraint listing is refined across sprints.

## Revision 3-D — Section 3.5.4, preliminary mathematical formulation (NEW)

**Reason:** Section 2.6 discusses constraint modelling theory and the Conclusion refers to rules "formalized in Section 11.2", a section that does not exist. The report never formalizes the model, even though the modelling is the claimed contribution. The sketch below closes that gap and gives Section 3.4 and the Conclusion something real to reference. Add it as a new subsection at the end of Section 3.5.

### 3.5.4 Preliminary Constraint Optimization Problem Formulation

The formulation below is the preliminary output of the third stage of the lifecycle in Section 3.4. It is stated here to demonstrate that the elicited rules in Section 3.5.3 are expressible as a pure-integer model, and it will be elaborated into the complete model during FYP 2.

**Sets and parameters.** Let *U* be the set of allocation units, partitioned by tier into the Emperor units *U*(E), the Merit units *U*(M) and the Bodhi units *U*(B). In the validated scenario, the 112 Emperor participants form 56 Emperor units, and with the 22 Merit and 16 Bodhi participants there are 94 allocation units in total. Let *S* be the set of assignable seats, where each seat *s* carries a row *r*(*s*) from 1 to 16, a physical position *p*(*s*) from 1 to 16, a priority rank, and a blocked flag. Let *Q* be the set of valid Emperor pairs, which are the within-row adjacent position pairs (1,2), (3,4), (5,6), (7,8), (9,10), (11,12), (13,14) and (15,16); the pair (8,9) is structurally excluded because the centre aisle separates the eight seats on each side of the hall. Each unit *u* carries a contribution amount *c*(*u*), an activeness score, an eligibility status and an accessibility flag, and where a previously published seating map exists, a previous seat.

**Decision variables.** Variables are created only for eligible combinations, which encodes several hard constraints by construction:

- *x*(*u*,*s*) is a binary variable defined for each Merit or Bodhi unit *u* and each non-blocked seat *s* whose row lies in *u*'s tier band, and equals 1 if and only if *u* is assigned seat *s*.
- *y*(*u*,*q*) is a binary variable defined for each Emperor unit *u* and each valid pair *q* in *Q* whose two seats are non-blocked and lie in the Emperor band, and equals 1 if and only if *u* is assigned the pair *q*.

Because no variable exists for a blocked seat, for an out-of-band placement, for an ineligible participant or for an aisle-straddling pair, none of these can appear in any solution.

**Hard constraints.**

- (H1) Each Merit or Bodhi unit occupies exactly one seat: the sum of *x*(*u*,*s*) over all *s* equals 1.
- (H2) Each Emperor unit occupies exactly one valid pair: the sum of *y*(*u*,*q*) over all *q* equals 1.
- (H3) Each seat has at most one occupant, counting both seats of every assigned pair.
- (H4) Within-tier contribution ordering: for every two units *u* and *u*′ of the same tier where *c*(*u*) is greater than *c*(*u*′), the assigned row of *u* is not later than the assigned row of *u*′.
- (H5) A unit with the accessibility flag is assigned a side or edge seat of the hall, and for an Emperor unit a pair at the side.
- (H6) The numbered section fills from front to back with no vacant seat, and each side of a row fills outward from the centre aisle.
- (H0) Before the model is constructed, the tier bands are derived from the tier demand of the event and each band's capacity is validated, with Emperor units counted as two seats. For the validated scenario this yields Emperor rows 1 to 9, Merit rows 9 to 10 and Bodhi rows 10 to 11, where rows 9 and 10 are shared boundary rows and the remaining 82 assignable seats form the free-seating section. A capacity violation is returned as a structured infeasibility explanation without invoking the solver.

**Objective.** The objective minimizes a weighted sum of integer soft-constraint penalties, comprising the mismatch between a unit's contribution rank and the priority rank of its assigned seat, the activeness penalty, the category suitability penalty, the movement penalty on reallocation, and a deterministic tie-breaking term. The movement penalty is counted through reified indicators that record whether a unit's assigned seat differs from its seat in the previously published map, and is identically zero when no previous map exists. Upon reallocation the movement term dominates, minimizing first the number of unaffected participants moved and then the total movement distance, so that no unaffected participant is displaced merely to improve another participant's seat preference marginally. Every weight, penalty coefficient and tie-break term is an integer, as CP-SAT requires, and the tie-break coefficient is scaled so that the largest possible tie-break contribution remains smaller than one unit of the smallest weighted penalty.

## Revision 3-E — Section 3.7, Gantt charts

Your `academic/diagrams/` folder currently contains a single `Darius_FYP_Gantt_Chart.xlsx`. The rubric requires the project timeline **for both semesters**, so confirm that Section 3.7.1 and Section 3.7.2 each carry an exported and embedded chart image that is legible at print size, and that the two fixed academic milestones, which are the FYP 1 interim report submission and the FYP 2 viva and dissertation submission, are visible on them. A missing FYP 2 chart drops this criterion to the lowest band.

---

# Section 4 — Conclusion

## Revision 4-A — Section 4.1, two corrections

| Original | Revised |
|---|---|
| "The contribution of this project is a to develop a configurable, constraint-based seating allocation system…" | "The contribution of this project is to develop a configurable, constraint-based seating allocation system…" |
| "…models real event rules formalized in Section 11.2 as a Constraint Optimization Problem…" | "…models real event rules formalized in Section 3.5.4 as a Constraint Optimization Problem…" |

Also align the participant figures in Section 4.1 with the confirmed scenario, and hedge the gap claim in the same way as Revision 2-A: "neither commercial tooling … nor the published seating-allocation literature" becomes "neither the reviewed commercial tooling … nor the reviewed seating-allocation literature".

## Revision 4-B — Section 4.2 Future Work Recommendation (NEW)

**Reason:** Section 4.2 currently reads "Next module or things to do in FYP2….". The Conclusion criterion is doubly weighted and explicitly includes future work, whose lowest descriptor is "No future work recommended." Written in the first person as requested.

**Replace with:**

## 4.2 Future Work Recommendation

The work that follows this report is organized around the FYP 2 schedule in Section 3.7.2, and I have grouped it into five (5) areas.

First, I will complete the constraint optimization problem modelling for the seating allocation. The preliminary formulation in Section 3.5.4 covers only the core hard constraints and the shape of the objective, so I will extend it into the complete mathematical model, which includes formalizing the demand-driven tier-band derivation with its shareable boundary rows, the front-to-back packing and centre-out fill rules, the side-of-hall accessibility placement, and the movement-minimizing objective used during incremental repair. I will document the finished model as a machine-readable model specification so that every constraint in the listing in Section 3.5.3 can be traced to the mathematical statement that implements it, and so that the independent validator in FR16 can be written against the same specification rather than against the solver code.

Second, I will develop the solver function itself. This begins with implementing the hard constraints and the weighted soft constraints in Python 3 with Google OR-Tools CP-SAT, adding the deterministic tie-breaking, and confirming that the default 150-participant scenario returns an OPTIMAL result within the configured solver budget. I will then implement the incremental reallocation mechanism described in Section 1.5.5, which is the escalation hierarchy that attempts a direct substitution first, then a reduced repair model over a bounded neighbourhood, and then a progressively expanded neighbourhood, with a complete regeneration retained only as a fallback that the event administrator must explicitly invoke. After that I will deploy the solver function to AWS Lambda and measure the cold-start behaviour, because the OR-Tools library adds a large deployment artifact and the on-event-day repair case is the most time-sensitive use of the system.

Third, I will continue refining the requirements and the constraints with PJKIT. I will conduct a monthly site visit to PJKIT together with the industry supervisor, in which I will showcase the current progress of the seating allocation system and walk the stakeholders through the behaviour of each newly modelled constraint against their own historical seating maps. The purpose of these visits is to validate that each modelled rule matches the community's intent rather than only my interpretation of it, and to settle the items that elicitation left open, which are the weightings between contribution, seniority and previous event attendance recorded as unfinished in Appendix B D12, the tie-breaking rule recorded as needing confirmation in D13, the usability criterion in NFR2, and the availability target in NFR7. Any correction arising from a visit returns to the constraint classification and mathematical formulation stages of the lifecycle in Section 3.4.

Fourth, I will keep participating in the Agile SCRUM ceremonies with the industry supervisor from Netizen eXperience, following the two-week sprint arrangement described in Section 3.1, so that each increment of the solver function is demonstrated and reviewed rather than developed in isolation. Alongside this, I will begin reviewing the current codebase of the Netizen eXperience event management platform, focusing on the Next.js server components and server actions, the existing participant and event data model, and the AWS resource definitions provisioned through the SST framework. The purpose of this review is to identify the integration points for the administrator seating allocation dashboard and the participant seat lookup route before the integration phase begins in the second half of FYP 2, so that integration is not delayed by unfamiliarity with the existing platform.

Fifth, I will carry out the evaluation of the system. I will implement the random, first-come-first-served and greedy priority-based baselines identified in Section 2.7, define the change scenarios for reallocation from the ad hoc cases that PJKIT reported, which are participant absence and substitution, and compare the seating maps produced by the engine against those baselines on the quality indicators in FR8. For Objective 2 I will measure the number of unaffected participants moved, the total movement distance and the repair runtime, and compare the incremental repair against a full regeneration with a movement penalty, so that the benefit of repairing locally is measured rather than assumed. I will then validate the system on real PJKIT event data obtained through the industry supervisor.

Beyond the FYP timeline, I would recommend three extensions. The constraint configuration could be generalized so that other organizers on the Netizen eXperience platform can define their own tiers and rules without modification to the solver logic, which the isolation required by NFR4 is intended to make possible. The engine could be compared against a genetic algorithm implementation, which is the approach taken by PerfectTablePlan, in order to quantify the trade-off between provable optimality and search flexibility. Finally, the venue model could be extended beyond the single rectangular hall of the case study to layouts with multiple blocks and irregular row lengths.

---

# Section 5 — References

## Corrections to existing entries

| Entry | Correction |
|---|---|
| CP-SAT Solver. (n.d.) | Re-author as "Google. (n.d.-a). *CP-SAT solver*. Google for Developers — OR-Tools." and add the URL and retrieval date. Google is an identifiable corporate author, so filing the entry under its title is not correct APA. |
| Channeling constraints | Missing entirely. Add "Google. (n.d.-b). *Channeling constraints*. Google for Developers — OR-Tools." — Section 2.6 cites the channeling documentation, which is a different page from the CP-SAT solver page. |
| Ipsen et al. (2026) | Remove "Open MIND", which is a reference-manager artifact. It is an arXiv preprint; cite it as such. |
| Muñoz Solà, V., Montaner, M., & Esteva, P. (2006) | Verify the third author. The retrieved copy of this paper lists **Víctor Muñoz, Miquel Montaner and Beatriz López** of Universitat de Girona. Also settle the year, since the in-text citations alternate between 2005 and 2006. |
| Perron, L., Didier, F., & Gay, S. (2023) | Verify whether Gay is a listed author, and make the in-text form consistent with whatever the entry says. |
| Peter J. Stuckey. 2010. | Reformat to APA and file under S: "Stuckey, P. J. (2010). Lazy clause generation…" |
| Oryx Digital Ltd. (n.d.) | Remove the stray "c" before the URL. |
| Pohl, K. & Rupp, C. (2016) | Cited nowhere in the text. Either cite it in the methodology, where requirements engineering practice is discussed, or remove it. |
| Whole list | Re-sort alphabetically. Current out-of-order entries: "Invoke" should precede "Ipsen"; Stuckey is filed under "Peter"; Muñoz appears after Rossi; "What is AWS Lambda" appears before Schwaber. |

## Entries cited in the text but missing from the list

Add: **Hoang (2022)** (cited in §2.5), **Schiex et al. (1995)** (cited in §2.6), **Williams (2013)** (cited in the comparison table), **Object Management Group (2017)** (cited in §3.2.1 and §3.2.3).

## New entries required by the revisions

Full APA-formatted entries for Awadallah et al. (2012), Barry et al. (2021), El Sakkout & Wallace (2000), Google (n.d.-a and n.d.-b), Hales & García (2019), Kuhn (1955), Mu & Tong (2019), Pisinger & Ropke (2010), Shaw (1998), Stoll (2022), Ülker (2013) and Verfaillie & Schiex (1994) are provided in the "References to add" block of `revised_section2_literature_review.md`.

**Before citing any of these, read the source.** Of the works recommended in the revised literature review, only Ipsen et al. (2026), Muñoz et al., Sun (2020) and Hoang (2022) have been read in full in preparing this material. The remainder are recommended from domain knowledge or were located in Ipsen et al.'s bibliography, and each must be obtained, read, and its author list, year, venue and pagination confirmed before it appears in your reference list. The full status table is at the end of `revised_section2_literature_review.md`.

---

# Order of work

| Step | Task | Depends on |
|---|---|---|
| 1 | Apply the Section 1 revisions, including the new Scope of Study, and renumber 1.5 to 1.6 | — |
| 2 | Apply the Section 3 and Section 4 revisions, including §3.4, §3.5.4 and §4.2 | — |
| 3 | Obtain and read the new literature sources | — |
| 4 | Apply the Section 2 revisions from `revised_section2_literature_review.md` | Step 3 |
| 5 | Correct and complete the reference list; fix all cross-references and figure numbers | Steps 1–4 |
| 6 | Export and embed both Gantt charts | — |
| 7 | Draft the Abstract | Steps 1–6 confirmed |
| 8 | Full language proofread; confirm the `Ã` and `â` sequences are extraction artifacts and not present in the source document | Step 7 |
