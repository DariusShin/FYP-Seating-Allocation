# TFB3413 Software Requirements Engineering

## Assignment 2 (Individual)

### Critical Review of the FYP1 Proposal Using Software Requirements Engineering Principles

**University:** Universiti Teknologi PETRONAS
**Project Title:** Intelligent Automated Seating Allocation System for Large-Scale Assemblies Using Configurable Constraint Optimization
**Course:** TFB3413 Software Requirements Engineering
**Lecturer:** Ts. Dr. Shuib bin Basri
**Student:** Darius Lee Shin (22003269)
**Date:** July 2026

---

## Table of Contents

1. Task 1: Project Summary
   - 1.1 Project Title
   - 1.2 Problem Statement
   - 1.3 Project Objectives
   - 1.4 Target Users
   - 1.5 Proposed Solution
2. Task 2: Requirements Analysis
   - 2.1 Functional requirements identified in the proposal
   - 2.2 Non-functional requirements identified in the proposal
   - 2.3 Missing functional requirements
   - 2.4 Missing non-functional requirements
   - 2.5 Requirements that need improvement
3. Task 3: Critical Requirements Review
   - 3.1 Quality review table
   - 3.2 Discussion and justification
4. Task 4: Reflection and Improvement Plan
5. References

---

## Task 1: Project Summary

### 1.1 Project Title

*Intelligent Automated Seating Allocation System for Large-Scale Assemblies Using Configurable Constraint Optimization* — a Final Year Project with Petaling Jaya Kwan Inn Teng (PJKIT) as the case-study organization and Netizen eXperience as the industry collaborator.

### 1.2 Problem Statement

PJKIT organizes community events of approximately 100 to 200 participants in a 120-seat venue and currently prepares seating by hand, using spreadsheets, printed charts, and PDF name lists. The underlying problem is combinatorial: each participant must be matched to a suitable seat while contribution tier and score, activeness, group relationship, participant status, and venue restrictions are weighed simultaneously, and constraint programming has long been used to formalize assignment problems of this kind (Rossi et al., 2006). The PJKIT case adds structural rules: three contribution tiers map to reserved row zones, an Emperor registration occupies two adjacent seats that must form a valid within-row pair and never straddle the centre aisle, and seating order within each tier must respect contribution ranking. Manual allocation scales poorly: preparation is slow, two allocators given the same rules produce different plans, and a late absence or substitution forces disruptive rework that risks duplicate seats or broken Emperor pairs. Left unaddressed, these costs mean continued volunteer strain and reputational risk for PJKIT, and a forgone reusable allocation capability for Netizen eXperience's Corporate Social Responsibility (CSR) platform.

### 1.3 Project Objectives

The refined project pursues three objectives.

1. An allocation engine that models seating as a Constraint Optimization Problem, combining mandatory hard constraints with weighted soft constraints in the tradition of valued constraint satisfaction (Schiex et al., 1995), solved with the Google OR-Tools CP-SAT solver (Google, n.d.).
2. Controlled dynamic reallocation as incremental repair of the published plan: only the assignments affected by a change are modified, unaffected participants keep their published seats wherever possible, and every repaired result becomes a new version requiring organizer approval.
3. A participant-facing lookup channel through which a participant retrieves their assigned seat from the latest published plan.

### 1.4 Target Users

The primary user is the event organizer, who configures constraints, generates and reviews plan versions, and publishes an approved version. Secretariat staff, participants, Netizen eXperience, and system administrators are secondary users and beneficiaries.

### 1.5 Proposed Solution

The engine is a Python 3 function on AWS Lambda that embeds CP-SAT: it accepts participant profiles, the seating layout, the constraint configuration, and any previously published allocation as JSON, and returns the participant-to-seat mapping with quality indicators (solver status, independently validated hard-constraint satisfaction, per-constraint soft-penalty breakdown, movement count, and runtime). The existing Next.js CSR platform hosts the admin module and the participant lookup, with persistence in Amazon DynamoDB and Amazon S3. Commercial tools reviewed in the proposal (Cvent, PerfectTablePlan, WeddingWire, and Zola) each address fragments of the problem; none combines configurable profile-based constraints, constraint-based optimization, movement-minimizing reallocation, versioned publishing, and participant lookup in one workflow.

---

## Task 2: Requirements Analysis

### 2.1 Functional requirements identified in the proposal

Section 4.5 of the proposal states twelve functional requirements, each traced to a goal. Table 1 lists all twelve individually, quoted verbatim from the proposal so that the review can refer to their exact wording; the analysis in the remainder of this report is written independently.

*Table 1. Functional requirements as stated in the FYP1 proposal (Section 4.5)*

| Requirement ID | Requirement Description (quoted from the proposal) |
|---|---|
| FR1 | The system shall allow the existing web platform to send participant profile data to the seat allocation service. |
| FR2 | The system shall allow the existing web platform to send seating layout data to the seat allocation service. |
| FR3 | The system shall allow event organizers to configure predefined constraint weights for the allocation process. |
| FR4 | The system shall map predefined human-readable event rules into computable hard constraints and weighted soft constraints. |
| FR5 | The system shall generate a seating allocation result based on participant profiles, seating layout, and constraint configuration. |
| FR6 | The system shall return the generated seating allocation result in JSON format. |
| FR7 | The system should provide solver status such as optimal, feasible, infeasible, unknown, or error status. |
| FR8 | The system shall calculate and return fairness-related indicators for the generated seating plan. |
| FR9 | The system shall allow dynamic reallocation by processing updated participant or event data. |
| FR10 | The system shall allow event organizers to review the generated seating map through the admin review page. |
| FR11 | The system shall allow seating results to be exported for event operation. |
| FR12 | The system shall store or retrieve relevant events, participant, constraint, and seating result data from the database where necessary. |

Read together, the requirements cover input flow (FR1, FR2), configuration (FR3, FR4), allocation and output (FR5 to FR8), reallocation (FR9), review and export (FR10, FR11), and persistence (FR12). They form a coherent pipeline consistent with the system vision, although Task 3 shows that the goal identifiers they trace to are undefined.

### 2.2 Non-functional requirements identified in the proposal

Table 2 below lists all the non-functional requirements identified in the FYP1 proposal, quoted verbatim from Section 4.6.

*Table 2. Quality requirements as stated in the FYP1 proposal (Section 4.6)*

| Requirement ID | Quality Requirement (quoted from the proposal) |
|---|---|
| NFR1: Performance | The system should generate a seating allocation result within an acceptable processing time for approximately 100 to 200 participants. |
| NFR2: Usability | The admin seating plan review page and participant seat lookup page should be clear and understandable. |
| NFR3: Reliability | The system should return clear status messages when allocation succeeds, fails, or becomes infeasible. |
| NFR4: Maintainability | The constraint configuration and seat allocation solver logic should be modular and low coupling to one another. |
| NFR5: Security and Privacy | Real participant data should be protected and anonymized where necessary during testing and reporting. |
| NFR6: Scalability | The system design should allow future extension to larger datasets or other event types. |

Read together, the six statements cover the principal quality categories relevant to the system: solver processing time, usability of the review and lookup pages, status reporting on success and failure, modularity between configuration and solver logic, protection of participant data, and future extension to larger scales. They complement the functional pipeline of Section 2.1; their specification quality is assessed in Section 2.5.

### 2.3 Missing functional requirements

Comparing the proposal against the requirements validated with stakeholders during the planning phase exposes six functional requirements that the proposal did not state. Table 3 below lists them in the same format as the proposal's own requirement table, continuing the identifier sequence from FR13.

*Table 3. Missing functional requirements identified by this review*

| Requirement ID | Requirement Description |
|---|---|
| FR13: Participant seat lookup | The system shall allow a participant to retrieve their assigned seat from the latest published seating plan. |
| FR14: Plan versioning, approval, and publishing | The system shall store every generated allocation result as a plan version, shall require explicit organizer approval before publication, and shall expose only the latest published version to participants. |
| FR15: Stability-preserving reallocation | The system shall perform dynamic reallocation as incremental repair of the published plan, modifying only the assignments affected by a change and, where necessary, a bounded surrounding seating area, while minimizing first the number of unaffected participants moved and then total movement distance. |
| FR16: Input validation and structured errors | The system shall validate every incoming payload against its schema and structural rules and shall return a structured, frontend-consumable error response for invalid input. |
| FR17: Independent solution validation | The system shall re-check every generated seating plan against all hard constraints independently of the solver that produced it before the plan can be accepted. |
| FR18: Structured failure handling | The system shall return a structured failure response containing the solver status and any determinable validation, capacity, or input failure reasons, shall prevent an unsuccessful result from being published, and shall allow the organizer to revise data, constraints, weights, or seat availability. |

Each gap traces to evidence in the proposal. The participant lookup (FR13) was acknowledged only indirectly: NFR2 refers to a participant seat-lookup page while the usage facet classifies the participant as an indirect stakeholder who "does not directly operate the allocation service", and no functional requirement, use case, publishing dependency, or access-control requirement supports the page; in the refined project this lookup is Objective 3. FR14 and FR15 are absent because FR10 lets the organizer review the seating map but nothing requires generated results to be versioned, approved explicitly, or withheld from participants until published, and FR9 makes reallocation possible without protecting the published plan during it. FR16 to FR18 close robustness gaps: nothing in the proposal obliges the service to validate incoming payloads, to re-check a generated plan independently of the solver that produced it, or to define what follows an infeasible result, so a modelling error would pass unnoticed. Complete diagnosis of every conflicting rule combination remains future work.

### 2.4 Missing non-functional requirements

Beyond the weaknesses of the stated quality requirements examined in Section 2.5, two quality requirements are absent from the proposal altogether (Wiegers & Beatty, 2013). Table 4 below states them in the same format as the proposal's quality-requirement table, continuing the identifier sequence from NFR7.

*Table 4. Missing non-functional requirements identified by this review*

| Requirement ID | Quality Requirement |
|---|---|
| NFR7: Availability | The participant seat lookup should remain available throughout the event window. The target availability level should be elicited and agreed with Netizen eXperience, because the lookup depends partly on the availability characteristics of the existing CSR platform; no numeric target is proposed until that validation occurs. |
| NFR8: Reproducibility | For identical normalized input data, constraint configuration, solver parameters, and deterministic seed, repeated executions shall produce the same canonical allocation and quality indicators. |

NFR7 matters because the participant lookup delivers most of its value in the hours around the event, yet the proposal states no availability expectation; it is worded with "should" because it remains a recommendation subject to stakeholder validation. NFR8 is stated as mandatory because the refined design already commits to determinism: without it, regeneration causes gratuitous seat changes between equivalent solutions and benchmark comparisons cannot be repeated.

### 2.5 Requirements that need improvement

Because the proposal's requirements were written before the stakeholder validation completed during the planning phase, the recommended improvements are not limited to rewording: where validation showed a statement to be unverifiable, unsupported, or overlapping another requirement, the recommendation alters it, combines it with another requirement, or removes it in favour of a new improved requirement. Table 5 below records the functional requirements whose current form weakens the specification, with the recommended action and improved requirement for each.

*Table 5. Functional requirements needing improvement, with the identified weakness, the recommended action, and the improved requirement*

| Requirement | Weakness | Recommended action | Improved requirement |
|---|---|---|---|
| FR4 | "Predefined human-readable event rules" is never enumerated, so the requirement's scope is unknowable. | **Alter.** Enumerating the constraint areas confirmed during planning fixes the requirement's scope. | The system shall map the following configurable rule areas into computable hard constraints and weighted soft constraints: contribution tier and score, activeness, group relationship, participant status, tier-zone placement, Emperor two-seat pairing, centre-aisle integrity, within-tier contribution ordering, unavailable-seat exclusion, and movement minimization during reallocation. |
| FR7 | Uses "should" although status reporting is mandatory for the review workflow; every other FR uses "shall". | **Alter and combine with NFR3.** Reword to "shall", absorb the status-message behaviour of NFR3 so that status reporting is specified once as functional behaviour, and adopt a fixed modal-verb convention: shall for mandatory requirements, should for recommendations or items awaiting stakeholder validation, may for optional behaviour. | The system shall return the solver status of every allocation run (optimal, feasible, infeasible, unknown, or error) together with a clear status message when allocation succeeds, fails, or becomes infeasible. |
| FR8 | "Fairness-related indicators" has no formula, scale, or threshold, so the requirement is unverifiable as written. | **Alter.** Replace the undefined fairness indicators with indicators the system can compute and an independent validator can recompute. | The system shall calculate and return reconstructible quality indicators for every generated seating plan: solver status, independent hard-constraint validation result, total weighted soft-constraint penalty with a per-constraint breakdown, movement count and movement distance where applicable, and runtime, compared against defined baselines. |
| FR9 | Silent on stability, versioning, and organizer review of regenerated plans; written before the stability expectation was validated with stakeholders. | **Alter and combine with FR15.** Reallocation must repair the published plan rather than regenerate it, and its output must re-enter the approval workflow of FR14. | The system shall perform dynamic reallocation as incremental repair of the published plan, minimizing first the number of unaffected participants moved and then total movement distance, and shall store the repaired result as a new plan version requiring organizer approval under FR14. |
| FR12 | "Where necessary" delegates the storage decision to the implementer and is untestable. | **Alter.** Naming the persisted entities of the refined data model removes the undefined qualifier. | The system shall store and retrieve the following persisted entities: events, participants, layouts, seats, constraint configurations, plan versions, and assignments, with each plan version referencing its predecessor. |

The six quality requirements of Table 2 need improvement as a group. One pattern is visible across all six: every statement uses "should" rather than "shall", and each rests on a subjective qualifier, so none carries a fit criterion that a test could pass or fail (Pohl & Rupp, 2015). None of the six is traced to a goal, so the soft goals SG1 to SG5 have no explicit realization path. Table 6 records the specification weakness this review identifies in each quality requirement, with the recommended action and an improved requirement grounded in the refined interim report.

*Table 6. Quality requirements needing improvement, with the identified weakness, the recommended action, and the improved requirement*

| ID and category | Specification weakness | Recommended action | Improved requirement |
|---|---|---|---|
| NFR1: Performance | "Acceptable processing time" is unverifiable; no bound, dataset, or environment is stated. | **Alter.** Replace the subjective qualifier with an explicit bound, dataset, and evaluation environment. | The system shall return an OPTIMAL result within the configured 60-second solver budget for the default dataset of 100 registrations and the 120-seat case-study layout under the defined evaluation environment; when the budget expires before optimality is proven, the system shall return the actual solver status and shall not represent the solution as optimal. |
| NFR2: Usability | "Clear and understandable" is subjective. The statement also acknowledges a participant lookup page although the usage facet treats the participant as an indirect stakeholder and no functional requirement supports the page. | **Alter.** Refine into a task-based criterion, subject to stakeholder validation; the lookup page it presupposes becomes FR13. | The system shall enable an event organizer to generate and publish a seating plan without assistance after a single briefing session; the criterion remains subject to stakeholder validation. |
| NFR3: Reliability | Status reporting is observable functional behaviour that overlaps FR7; reliability as a quality attribute is left unspecified. | **Remove and combine into FR7.** Move the status-message behaviour into FR7 as functional behaviour, and specify reliability as a new quality requirement in its place. | The system shall not publish a plan that fails input validation, solver processing, or independent post-solve validation, and shall keep the previously published plan unchanged and accessible when such a failure occurs. |
| NFR4: Maintainability | "Modular and low coupling" names no verification method. | **Alter.** Restate with an observable criterion consistent with the refined design's separation of validation, preprocessing, model construction, solving, and result formatting. | The system shall isolate the constraint configuration from the solver logic such that a change to the constraint configuration requires no modification of solver code. |
| NFR5: Security and Privacy | "Where necessary" is undefined, and the statement covers only testing and reporting; operational access control is unaddressed. | **Alter.** Extend beyond testing and reporting to operational access control and data retention as specified in the refined design. | The system shall inherit administrative access from the host platform's authentication, shall restrict unpublished plan versions to authorized administrators, shall allow each participant to view only their own assignment from the latest published version, shall use pseudonymous participant identifiers in the solver payload, and shall retain data in line with the event lifecycle. |
| NFR6: Scalability | No target scale is named, and the 400 to 800 participant figure stated elsewhere in the proposal was never validated with stakeholders. | **Alter.** Anchor scalability to the validated baseline instead of the unvalidated 400 to 800 figure. | The system shall support the validated operational baseline of 100 registrations and 120 seats, and shall treat larger datasets as exploratory scalability experiments paired with seating layouts of sufficient capacity. |

---

## Task 3: Critical Requirements Review

### 3.1 Quality review table

Table 7 evaluates the proposal against five quality characteristics of good requirements specifications: completeness, correctness, consistency, unambiguity, and verifiability (ISO/IEC/IEEE, 2018; Sommerville, 2016). Each finding cites the section of the proposal that evidences it.

*Table 7. Quality review of the FYP1 proposal*

| Quality Characteristic | Findings | Evidence from Proposal | Recommendation |
|---|---|---|---|
| Completeness | Participant lookup is acknowledged only indirectly in NFR2; no participant-facing functional requirement, use case, publishing dependency, or access-control requirement exists. Versioning, approval, and publishing are missing, as are movement-minimizing repair, input validation, independent post-solve validation, and structured failure handling. Availability and reproducibility are not specified. | Section 4.2 describes the participant as an indirect stakeholder who "does not directly operate the allocation service", while NFR2 (Section 4.6) refers to a "participant seat lookup page" with no supporting FR. No FR mentions versions, approval, or publishing. Section 4.6 contains no availability or reproducibility requirement and no goal traces. | Add FRs for participant lookup tied to the publishing workflow, plan versioning and approval, incremental movement-minimizing reallocation, input validation, independent post-solve validation, and structured failure handling. Add the availability recommendation and the reproducibility requirement of Section 2.4, and extend traceability to the NFRs. |
| Correctness | Several statements pre-date stakeholder validation, and editorial errors alter meaning. The 400 to 800 participant estimate conflicts with the 100 to 200 scale validated during the planning phase. Fairness is asserted to be measurable but never defined. NFR3 places functional status reporting under a quality heading. | Section 4.4: "approximately 400 to 800 participants", repeated in Section 6.4; the refined interim report adopts the validated 100 to 200 range with a 100-registration default evaluation scenario. Meaning-distorting typographical errors: "Large-sale assembly" and "group tires" (Section 1.3), "automating the set allocation" (Section 1.2). | Correct the scale to the validated range. Replace the fairness claim with the measurable indicators listed in Section 2.5. Separate functional status reporting (FR7), reliability, and reproducibility into distinct requirements. Proofread systematically, since errors in a requirements document propagate into design. |
| Consistency | Goals are defined as MG1, HG1 to HG5, and SG1 to SG5, but every trace references G1 to G7, identifiers that are never defined, so all traceability links are broken. The participant scale contradicts itself, modal verbs vary, the deployment platform is stated differently in three places, and the participant is described as indirect while NFR2 refers to a participant lookup page. | Section 3.2 maps vision elements to "G1, G2, G3, G7"; FR5 traces to "G1, G2, G3". Sections 4.4 and 6.4 say 400 to 800 while NFR1 says 100 to 200. HG5 says "should" yet is classified a hard goal; FR7 uses "should" among eleven "shall" FRs. Section 4.3 says "AWS Lambda or a compute instance", Section 6.3 proposes an EC2 instance, and Section 6.6 defers the choice again. Section 4.2 conflicts with Section 4.6 on the participant's role. | Adopt one identifier scheme and regenerate the traceability matrix so every FR and NFR resolves to a defined goal. Reconcile the participant figures on the validated baseline. Fix the modal-verb convention (shall, should, may) and apply it uniformly. Record the deployment decision once, with rationale and fallback condition. Align the participant's actor classification with the lookup capability. |
| Unambiguity | Terms that drive acceptance are undefined: "fair", "intelligent", "reduced manual effort", "fairness-related indicators", "predefined rules", "acceptable processing time", "clear and understandable", and "where necessary". Two readers could not agree on whether the delivered system satisfies them. | Section 2.1: "intelligent and configurable", with no criterion for "intelligent". SG2: "reduce manual effort", with no baseline or measurement protocol. FR8: indicators unspecified. FR4: rules "predefined" but never listed. FR12 and NFR5: "where necessary". NFR1 and NFR2: "acceptable processing time", "clear and understandable". | Provide operational definitions and measurable criteria for each term, enumerate the constraint templates with their hard or soft classification and default weights, and add a project glossary covering both constraint-programming and PJKIT domain terms. |
| Verifiability | Most soft goals, several FRs, and all six NFRs lack acceptance criteria, so no test could establish whether they are met. Nothing bounds solver runtime, nothing defines the fairness indicators, and manual-effort reduction has no measurement design. | SG1 ("improve fairness") and SG2 ("reduce manual effort") carry no thresholds or measurement methods. FR8 is unverifiable without a defined indicator. NFR1 sets no bound although Section 6.6 acknowledges runtime risk. NFR4 ("modular and low coupling") and NFR6 ("allow future extension") name no verification method. | Attach a fit criterion to every requirement, and verify each published plan against the checks defined in the refined design: no duplicate seat assignments, valid seat range, blocked-seat exclusion, valid Emperor pairs that never cross the centre aisle, correct tier-zone placement, contribution-order compliance, a reconstructed weighted objective with per-constraint penalty breakdown, the actual solver status, and a movement summary for reallocation. |

### 3.2 Discussion and justification

The three most consequential findings interact. First, the quality requirements are unquantified: all six use "should" with a subjective qualifier, so none is testable, and because non-functional requirements are architecturally decisive (Sommerville, 2016), the missing processing-time bound in NFR1 is exactly the number that determines whether AWS Lambda, with its bounded execution model, is a viable deployment target — which is why the proposal leaves the deployment platform unresolved in three separate sections. Second, traceability is broken: every functional requirement traces to identifiers G1 to G7 that are defined nowhere, so a reviewer cannot confirm that every goal is operationalized or detect missing requirements (Pohl & Rupp, 2015); a correct matrix would have exposed the incompletely specified participant lookup, which NFR2 presupposes while no goal or functional requirement supports it. Third, the central novelty claim of fairness-driven allocation is never operationalized: the proposal cites Jain et al. (1998) for the principle that fairness can be quantified, but gives no formula, inputs, or threshold, leaving its headline capability unverifiable.

The recommendation across all three findings is the same discipline: attach a verifiable criterion to every statement and reconnect the traceability chain. Concretely, restate the six quality requirements in the measurable forms of Table 6, including the explicit 60-second solver budget that settles the Lambda deployment question; regenerate the traceability matrix under a single identifier scheme so every requirement resolves to a defined goal; and replace the undefined fairness score with the reconstructible quality indicators of Table 5, which the system can compute and an independent validator can recompute. In fairness to the proposal, its analysis layer is sound: it identifies the relevant stakeholders early, recognizes participant, venue, and constraint data as the core of the subject domain, distinguishes hard goals from soft goals with a satisfaction rationale for each, describes the allocation pipeline from input to export, and shows awareness of integration, privacy, and solver-runtime risks. The weaknesses concentrate in the specification layer — the precision, measurability, and internal consistency of the requirements themselves — which is exactly the layer the improvements of Sections 2.3 to 2.5 repair.

---

## Task 4: Reflection and Improvement Plan

### 4.1 What are the major weaknesses I discovered in my FYP1 proposal?

The major weaknesses lie in the correctness and validity of both the functional and non-functional requirements, and in the goal traceability that should have held them together. The FYP1 proposal was written before the site visit to PJKIT and before the negotiation sessions that produced the validated requirements of the planning phase, so several of its statements captured early assumptions rather than validated stakeholder needs: the 400 to 800 participant estimate is roughly four times the validated 100 to 200 scale, the participant was classified as an indirect stakeholder even though NFR2 already presupposed a participant lookup page, and all six quality requirements rest on subjective qualifiers such as "acceptable processing time" that no test could pass or fail. The goal-to-requirement traceability is equally weak: every functional requirement traces to identifiers G1 to G7 that are defined nowhere in the document, and some goals are only loosely related to the requirements that claim to realize them, so the goal model could not perform its diagnostic function — it neither helped to identify the missing requirements later exposed in Sections 2.3 and 2.4 nor confirmed that each stated requirement was actually justified by a goal.

### 4.2 Which Software Requirements Engineering concepts helped me during this review?

In my view, the concept that helped most was scenarios, one of the core activities of requirements engineering alongside goals (Pohl & Rupp, 2015). By stating a concrete scenario, I could reason about whether a goal is sufficient and accurately formulated for my FYP: a scenario that illustrates a case successfully fulfilling a goal confirms that the goal is operationalized by the existing requirements, while a scenario in which the goal fails to be fulfilled exposes a gap and leads to the creation of a new sub-goal and, subsequently, new requirements. Walking through the late-change scenario — a participant cancels shortly before the event after the plan has been published — showed that FR9's bare "dynamic reallocation" fails the stability expectation the organizer actually holds, which surfaced the sub-goals of protecting the published plan and controlling movement, and from them the versioning, publishing, and stability-preserving reallocation requirements (FR14 and FR15) of Section 2.3; the participant-lookup scenario similarly exposed FR13. Used this way, scenarios strengthened both the structure and the completeness of the FYP requirements in exactly the places where re-reading the proposal as prose had revealed nothing.

### 4.3 What improvements will I make before continuing to FYP2?

Before FYP2 I will revise the goal model first, because every other correction depends on it. I will identify the correct root goal and separate the hard goals from the soft goals, then draw a goal graph or tree whose decomposition makes the priority and hierarchy of the goals explicit, so that it is clear which goals are mandatory, which are aspirations, and in what order they must be satisfied. With that clear goal list in place, I will regenerate the connection from goals to the revised functional and non-functional requirements that incorporate the improvements stated in Section 2.5 — the altered, combined, and replacement requirements of Tables 5 and 6 together with the missing requirements FR13 to FR18 and NFR7 to NFR8 — under a single identifier scheme, so that every requirement resolves to a defined goal and every goal is operationalized. The main purpose of this reconnection is to anchor each non-functional requirement to a measurable and quantifiable metric, such as the 60-second solver budget for performance and the validated 100-registration, 120-seat scenario as the scalability baseline, so that the quality requirements constrain the FYP2 design instead of remaining directions that no test can fail.

### 4.4 What lessons have I learned from this assignment?

The lasting lesson is that requirements engineering is a step-by-step process that requires true understanding of the case study, built through its own principles such as goals and scenarios rather than through assumptions written from a distance. It is essential to carry out activities such as the site visit, direct observation, and interview sessions with the stakeholders, because these are what validate the requirements, the objectives, the quality expectations, the constraints, and the existing system workflow from the business side: every major correction recorded in this review — the participant scale, the participant's actor role, the stability expectation during reallocation, and the venue-specific seating rules — originated from those activities at PJKIT rather than from desk work. My FYP1 proposal represented an early requirements baseline that had not yet incorporated these validation findings, and the discipline this assignment taught me is to detect where such a baseline has fallen behind the validated understanding and to correct it before design and implementation begin, so that FYP2 proceeds from requirements that are complete, consistent, unambiguous, and verifiable.

---

## References

Google. (n.d.). *CP-SAT solver*. Google OR-Tools. https://developers.google.com/optimization/cp/cp_solver

ISO/IEC/IEEE. (2018). *Systems and software engineering: Life cycle processes. Requirements engineering* (ISO/IEC/IEEE 29148:2018). International Organization for Standardization.

Jain, R., Chiu, D. M., & Hawe, W. R. (1998). *A quantitative measure of fairness and discrimination for resource allocation in shared computer systems* (cs.NI/9809099). arXiv. https://arxiv.org/abs/cs/9809099

Pohl, K., & Rupp, C. (2015). *Requirements engineering fundamentals* (2nd ed.). Rocky Nook.

Rossi, F., van Beek, P., & Walsh, T. (Eds.). (2006). *Handbook of constraint programming*. Elsevier.

Schiex, T., Fargier, H., & Verfaillie, G. (1995). Valued constraint satisfaction problems: Hard and easy problems. In *Proceedings of the 14th International Joint Conference on Artificial Intelligence (IJCAI-95)* (pp. 631-639). Morgan Kaufmann.

Sommerville, I. (2016). *Software engineering* (10th ed.). Pearson.

Wiegers, K., & Beatty, J. (2013). *Software requirements* (3rd ed.). Microsoft Press.
