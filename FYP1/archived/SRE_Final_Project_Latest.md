# SRE Project Report

> Extracted from the source PDF. The cover page and non-text figures/images were omitted. Tables are preserved as preformatted text where automatic conversion to Markdown tables could reduce accuracy.

## Table of Contents

```text
          1. Project Title ................................................................................................................................. 4
          2. Project Vision .............................................................................................................................. 4
          3. Project problems and objectives ................................................................................................. 4
            3.1 Background of Study ............................................................................................................ 4
            3.2 Problem Statement ................................................................................................................ 7
            3.3 Objectives ............................................................................................................................. 8
          4. System Goal ................................................................................................................................ 9
            4.1 Goal Graph ............................................................................................................................ 9
            4.2 Goal Definition ..................................................................................................................... 9
            4.3 Goals Against Problems, Objectives, and Vision ................................................................ 10
          5. System Context ......................................................................................................................... 10
            5.1 Subject Facet ....................................................................................................................... 10
            5.2 Usage Facet ......................................................................................................................... 12
            5.3 IT System Facet .................................................................................................................. 12
            5.4 Development Context ......................................................................................................... 13
            5.5 Consolidated Functional Requirements .............................................................................. 14
            5.6 Consolidated Non-Functional Requirements ...................................................................... 15
          6. Requirement Engineering (RE) Analysis Modelling ................................................................ 17
            6.1 Use Case Diagram............................................................................................................... 17
            6.2 System Flowchart................................................................................................................ 19
            6.3 System State Machine Diagram .......................................................................................... 20
            6.4 Class Diagram ..................................................................................................................... 22
            6.5 Swimlane Diagram for Generate Seating Plan Use Case ................................................... 23
          7. Methodology ............................................................................................................................. 24
            7.1 Software Development Methodology: Agile SCRUM implementation with Netizen
            eXperience ................................................................................................................................ 24
            7.2 Software Architecture Diagram .......................................................................................... 25
            7.3 Methods and Technologies Adopted ................................................................................... 26
          8. Propose Interface design ........................................................................................................... 28
            8.1 Event Administrator Seating Allocation Dashboard ........................................................... 28
            8.2 Event Participant Seat Lookup Portal ................................................................................. 28
          9. Requirement Resources and elicitation requirements ............................................................... 29
            9.1 Literature Review................................................................................................................ 29
             9.1.1 Existing Seat and Space Allocation Systems ............................................................... 29
             9.1.2 White Space Analysis Table ......................................................................................... 30
            9.2 Elicitation Questionnaires ................................................................................................... 31
            9.3 Joint Application Development Workshop ......................................................................... 31
          10. Project Milestone .................................................................................................................... 34
            10.1 FYP 1 Gantt Chart ............................................................................................................. 34
            10.2 FYP 2 Gantt Chart ............................................................................................................. 34
          11. Overall finding and output ...................................................................................................... 35
            11.1 Preliminary Findings from Elicitation .............................................................................. 35
            11.2 Constraint Listing Output.................................................................................................. 36
          12. Conclusion .............................................................................................................................. 39
          13. References ............................................................................................................................... 40
          14. Appendices .............................................................................................................................. 41
            Appendix A: Elicitation Questionnaires ................................................................................... 41
            Appendix B: Requirement Traceability Matrix ........................................................................ 43
            Appendix C: Site Visit Evidence .............................................................................................. 43
```

# 1. Project Title

The project title of my Final Year Project (FYP) is titled as “Intelligent Automated Seating Allocation System for Large-Scale Assemblies Using Configurable Constraint Optimization”. This project collaborates with Netizen eXperience to solve the existing seating allocation problem on the Petaling Jaya Kwan Inn Teng (PJKIT)’s annual events.

# 2. Project Vision

The vision statement for this Final Year Project (FYP) is as below:

“To provide an intelligent and configurable seating allocation system that supports constraint- compliant seating arrangements for large scale assemblies, enabling event administrator to generate seating plans automatically by considering participant profiles, priority rules, and event- specific constraints, and to support ad hoc event handling for seating allocation on the event day.”

# 3. Project problems and objectives

## 3.1. Background of Study

Large-scale assembly events such as community gatherings, convocation, ceremonies, and religious assemblies frequently require event administrator to choose the seating for their event participants. Although the task of seating assignment for event participants appears to be an administrative task, it is a multi-criteria combinatorial assignment problem (Rossi et al., 2006; Ipsen et al., 2026). Each participant must be matched and assigned to exactly one seat in a limited seating layout, and each seating assignment must simultaneously adhere and satisfy a set of interrelated event-specific rules. For example, participants of specific categories may need to be placed in specific seating zones, participants with higher event priority or contribution may receive a more favorable seat, and certain seats may be blocked or reserved from event participants. The number of possible assignments grows explosively with scale, which even in the simplified case where each of the case study’s 150 participants assigned a single seat among a venue that can support up to 232 seats, the number of possible ordered seat assignments is denoted as 232!/(232−150)! approximately 8.75×10326 of possible combinations for the seating plan, which is infeasible to check manually by human and it is impractical for machine to enumerated it naively (Rossi et al. 2006).

The case-study organization of this project, which Petaling Jaya Kwan Inn Teng (PJKIT), organized large annual community events that consisted of 100 to 200 participants per event. These events are held in a hall that could be set up to 16 rows and 16 seats per row, which in total 232 assignable seats after structurally blocked divider in the center of the hall based on the given layout from previous events. The current seating assignments workflow implemented by PJKIT is a typical manual procedure across many event administrator, which participant records are first store in excel spreadsheets, then the event administrator create the seating plan by manually filling each participant’s name in a predefined excel spreadsheet template as shown in Figure 1 below, the created seating plan will then be will convert into PDF document that will be shared digitally with participants through WhatsApp and used to print out an A2 sized venue chart and .

The seating allocation decisions made by PJKIT event administrator are not arbitrary for every single event, instead they adhere to a set of event-specific rules that caused the seating allocation problem to be more complicated than general seat assignment that relies on selection and randomness. In the context of PJKIT annual event-specific rule, participants will be divided into three (3) contribution tiers, which the Emperor, Merit and Bodhi. The contribution tiering is used as the primary criteria to determine the precedence of the seating arrangements from the front of the hall, which each Emperor row should precede the first Merit Row, and every Merit row should precede the first Bodhi row. The seating boundaries for each tier are not a fixed zone, but it is determined by the demand. On the other hand, each tier seating row also has their allocation rule to determine which participant will be allocated toward a more favorable seat in each row. For example, the participant with high contribution should be seated in a higher favorable row compared to the less contributed participant within the same tiering. The event administrator from PJKIT have to hold many competing considerations in mind at once to balance these coupled allocation rules manually for over a hundred of participants every event, which contribute to the inefficiency as the seating map preparation usually consumed more than a week from the starting of manually assigning seat, validate until finalize the seating plan.

Commercial event-planning tools such as Cvent, PerfectTablePlan, WeddingWire, and Zola offer features including floor plan design, table arrangement, guest list management, drag- and-drop seating and printable seating charts. Whole WeddingWire and Zola offer similar features for creating floor plans, assigning guests, and exporting or sharing arrangements (WeddingWire, n.d.; Zola, n.d.), PerfectTablePlan, for example, manages guest details, preferences, manual drag- and-drop or automatic seat assignment, it also supports printable charts. However, these solutions prioritize visualization of seat allocation, guest arrangement, and manual planning support rather than explicit fairness-driven allocation controlled by customizable weighted constraint.

The consequences that will be faced by PJKIT of continuing their current manual seating allocation workflow are severe and compounding. First, the quality of seating allocation decline as scale of participants increases, two different event staff member allocating the same event would result in two different plans, and neither of them could be objectively justified against the community’s stated tier, pairing and priority rule, which causing the event administrator to be expose to the perceptions of unfairness. Then, the preparation of the seating map consumes an unreasonable amount of volunteer time in the weeks before the event. Any late change, such as an absence, a substitution, or a newly registered walk-in ad hoc participant, requires an error -prone rework on a nearly completed seating plan. Each manual revision and reallocation of participants seat may increase the risk of introducing duplicate seat assignments, or missing participants.

This final year project is carried out in collaboration with Netizen eXperience, a software company that provides end-to-end digital solutions in Southeast Asia, which operates a Corporate

Social Responsibility (CSR) event management platform currently used by PJKIT to manage events and participants registrations and historical record. Netizen eXperience has appointed a Tech Lead as the industry supervisor to provide technical advice and facilities development for the seating allocation system. The industry supervisor also acts as the intermediary for requirement gathering, validation and organizing the site visit for discussion with PJKIT stakeholders. The seating allocation system proposed in this project is designed to be integrate as an new system module into the staging environment for the existing event management platform of Netizen eXperience rather than a stand-alone academic prototype.

## 3.2. Problem Statement

This project addresses three (3) pain points that are identified from the background of study in Section 3.1 and validated against the current event seating map generation workflow of PJKIT.

### Problem Statement 1: Inconsistency and inefficiency in multi-criteria manual seating allocation workflow

The manual participant seating allocation workflow requires the event administrator to consider many participant profiles simultaneously, including participant’s contribution, tiering priority, activeness on participating in other events organized by PJKIT, and status of participation against a constrained seating layout with demand-driven tier groups. This process is slow and does not scale with the growth of participants number and seating layout expansion of the event. The quality of the produced seating plan is difficult to validate or justify against the administrator’s own stated event-specific rules, and different event administrators make different decisions on assigning seats to participants resulting in producing an inconsistent seating map.

### Problem Statement 2: High operational disruption and lack of controlled dynamic reallocation mechanisms

Manual workflows provide limited support for a controlled reallocation of seating maps following changes to participant data closely to end of event preparation, and on the event day due to ad hoc events such as participant absence or substitution of a participant. Once a plan has been published, such a change creates a fundamentally different problem from initial allocation, it is a repair problem, in which the assignment that are directly affected by the changes must be fixed while preserving the rest of the previously communicated plan, that includes participants who may already have been informed or seated at their locations. A late change that appears in the existing manual participant seating allocation workflows may force event administrator from PJKIT to revise the whole seating plan, which increases the risk of duplicate or outdated seat records, and re-incurs the full cost and inconsistency of manual allocation for every small change.

### Problem Statement 3: Communication bottlenecks and inefficiencies in participant seat retrieval

Participants from PJKIT events currently relies on several ways to retrieve their assigned seats details in an event including getting from the printed seating map that will be showing during the event day, seats listing PDF document that shared by PJKIT event administrator or by asking the event staff to check manually for them during the event day. This administrator-driven distribution of participants seating information creates queues at the event, and it didn’t provide assurance that participants are reading the latest approved plan and offers no-self-service channel for participants to check their assigned seat before or during the event.

## 3.3. Objectives

The objectives of this project derive directly from the three (3) problem statements and specify what the project aimed at developing, solve and achieve.

### Objective 1

To design and develop a configurable, constraint-based seating allocation engine that converts participant profiles, seating layouts and configurable event-specific rules into programmable constraints for automating the seating plan generation.

### Objective 2

To develop a controlled incremental dynamic seating reallocation mechanism that accommodates ad hoc participant data changes due to absence, substitutions of participant and late registration, including on the event day by treating the latest published plan as the baseline state and modifying only the affected seats.

### Objective 3

To develop a participant-facing seat lookup channel that allows participants to retrieve and view their assigned seat number and event seating map from the latest event administrator published seating map.

# 4. System Goal

This section defines the goal model under a single identifier scheme, which decomposes the single root goal derived from the vision statement in Section 2 into a goal tree that maps the three (3) problem statements and separating hard goals from soft goals in this project.

## 4.1. Goal Graph

## 4.2. Goal Definition

```text
  Goal ID Goal Description                                  Type
          The system shall enable event administrator to produce fair, rule-

          consistent seating plans for large-scale assemblies (validated baseline:
   MG1                                                      Root
          100–200 participants; 256-seat venue with 232 assignable seats) with
          reduced manual effort and controlled handling of ad-hoc changes.
          The system shall generate constraint-compliant seating plans
   G1                                                       Hard
          automatically.
          Event rules shall be modelled as computable hard constraints and
   G1.1                                                     Hard
          weighed soft constraints.
          Plans shall be generated from participant profiles, seating layout, and
   G1.2                                                     Hard
          constraint configuration.
          Every run shall report a verifiable solver status and reproducible quality
   G1.3                                                     Hard
          indicators.
          Published plans shall be reallocated under administrator control when
   G2                                                       Hard
          participant or event data changes.
          Reallocation shall repair incrementally, minimizing first the number of
   G2.1   unaffected participants moved and then total movement distance for the Hard
          latest published seating map.
```

```text
          Every generated or repaired result shall be a version requiring explicit
   G2.2                                                     Hard
          administrator approval before publication.
   G3     Participants shall retrieve their assigned seat themselves. Hard
   G3.1   Only the latest published plan shall ever be exposed to participants. Hard
          The system should improve fairness and consistency of seating map
   SG1                                                      Soft
          generation.
          The system should reduce the administrator's manual effort on seating
   SG2                                                      Soft
          map generation.
   SG3    The system should make allocation results explainable. Soft
          The system should be usable by administrators without optimization
   SG4                                                      Soft
          knowledge.
```

## 4.3. Goals Against Problems, Objectives, and Vision

```text
     Goal     Problem Statement    Objective     Vision Element
                                            Intelligent, configurable,

 G1 (G1.1–G1.3) Problem Statement 1 Objective 1 constraint-compliant automatic
                                            seating plan generation.
                                            Ad-hoc event handling seating
 G2 (G2.1–G2.2) Problem Statement 2 Objective 2
                                            map reallocation.
                                            Support for   large-scale
 G3 (G3.1)    Problem Statement 3 Objective 3 assemblies on a participant-
                                            facing scale.
              Quality dimension for all     Intelligent and configurable
 SG1–SG4                          All
              three (3) problem statement   system.
```

# 5. System Context

The system contexts in this project are validated during the requirement elicitation activities described in Section 9 and the contexts are categorized into the Subject Facet, Usage Facet, and IT Systems Facets along with the Development Context.

## 5.1. Subject Facet

```text
 Context Object   Explanation
                  The attributes for a participant in the existing event management

                  platform including contribution tier (Emperor / Bodhi / Merit),
                  contribution score (integer ringgit), activeness score, status
 Participant Profile
                  eligibility, participant category and special-need flags (elderly, monk,
                  accessibility requirement), adjacent-guest name for Emperor
                  registrations, and ad-hoc flag.
```

```text
                  The domain situation that requires seating allocation, which consist
 Event            of attributes such as date, status, time and the associated venue layout

                  and constraint configurations.

                  The physical environment of the event and constraints assignments
                  boundaries for the solver function. It is a 16 rows × 16 seats layout
 Venue Layout     with a center aisle between physical positions index 8 and index 9. It
                  also contains 24-seat structural seats, leaving 232 assignable seats for

                  the allocation.

                  The object with the physical position index, priority rank to satisfy
 Seat             preferred rules, spatial zone for category suitability, accessibility flag,
                  and blocked flag.

                  The continuous block of rows that a tier occupies. It ordered from the

                  front with the sequence of Emperor to Merit to Bodhi. The boundaries
 Tier Group       are derived from each event's tier demand, which is not fixed venue
                  zones. Also, each row is tier-exclusive, and group capacity is
                  validated before model construction.

                  The two-seat allocation unit assigned to an Emperor registration.
 Emperor Pair     Physical positions index 8 and index 9 will never form a pair due to
                  the center aisle existing in the venue layout.

 Constraint Rule  It defines the event-specific rules that must be satisfied during seating
                  allocation.

 Constraint Weight It is a number that defines the importance of soft constraints during
                  optimization.

 Seating Plan     Seating plan is the generated allocation output that maps participants
                  to seats.

                  A generated result with solver status, penalty breakdown, movement

 Seating Plan Version summary, and lifecycle state, each version referencing its
                  predecessor.

                  The change event for participant data including absence, substitution,
 Participant Status
                  or ad-hoc registration that triggers reallocation.
```

## 5.2. Usage Facet

```text
 Context Object   Explanation        Interaction
                                     Prepares data, configures constraints and

                  Primary user of the weights, generates and regenerates
 Event Administrator seating allocation system plans, reviews versions, approves and
                  to generate seating plan. publishes, exports.

                                     Retrieves their assigned seat and views
 Event Participant Direct actor      the seating map from the latest published
                                     plan (FR13).
                  Supports data preparation
                                     Updates participant records and statuses;
 Event Staff      and event-day operations
                                     uses the published plan.
                  Industry collaborator that
                                     Integrates the engine, relays PJKIT
                  operates the  CSR
 Netizen eXperience                  stakeholder feedback, maintains
                  platform
                                     platform-side components.
                  Existing external system
 Netizen eXperience used by PJKIT for events Sends participant, layout, and constraint
 event management and  participant data data to the engine, it also receives and
 platform         management.        store seating plan in JSON format.
```

## 5.3. IT System Facet

```text
 Context Object   Explanation
                  A solver function written Python 3 language. It is embedding Google

                  OR-Tools CP-SAT, and it will be deployed on AWS Lambda. The
 Seat Allocation Engine engine will run on demand and have an explicitly defined 60-second
                  solver budget. It will return the seating plan as JSON upon accepting
                  valid JSON payload input from the system.

                  Next.js / React application that written in TypeScript, it is currently

 Netizen eXperience hosting the admin module for event management operation in PJKIT,
 event management and it will be integrated with a new participant lookup route upon
 platform         project completion. It acts as the system to invoke the seat allocation
                  engine through the AWS SDK with JSON payloads as input.

 Seating Allocation A new route in the existing Netizen eXperience event management
 Dashboard        platform that will be used to perform seating plan generation,
```

```text
                  publication, and preview on the generated seating plans result from
                  seat allocation engine.

                  A new route in the existing Netizen eXperience event management
 Participant Seat Lookup
                  platform that will be used to by event participant to retrieve and check
 Interface
                  for the latest published seating map and their assigned seat details,
                  Structured JSON request and response payloads from AWS Lambda
 API Communication
                  to the Netizen eXperience event management platform.
```

## 5.4. Development Context

```text
 Context Object   Rationale for Inclusion            Source & Type

 Final Year Project The project must be completed within the FYP1 Project
 (FYP) Timeline   and FYP2 timeframe.                Constraint

 Final Year Project Provides academic guidance and validates the Academic
 (FYP) Supervisor project scope.                     Stakeholder

 Netizen eXperience Provides industry use case and platform context. Industry
 Industry Supervisor                                 Stakeholder

 PJ Kwan Inn Teng Site Monthly activity that are carried out to collect real Domain Source
 Visit            event context, historical seating references,
                  workflow and constraint details.

 Historical Event Seating The administrator’s actual seating chart, a 16 x 16 Domain artifact
 Plan (2023 & 2024) grid layout. Used as a reference for modelling the
                  venue layout and seat quality.

 Development Tools Required to build the solution which includes Technical
                  Python 3.11+, OR-Tools CP-SAT, Next.js, AWS Resource
                  (Lambda, DynamoDB, S3), SST, Visual Studio
                  Code, and GitHub.

 Data       Privacy Participant data may contain personal or sensitive Ethical / Data
 Considerations   attributes.                        Constraint

 Solver    Function Solver runtime may be affected by dataset size Technical
 Runtime Limits   and deployment environment. Explicitly defined Constraint
                  maximum time limit for the solver function as
                  budget.
```

## 5.5. Consolidated Functional Requirements

```text
                                                         Goal
 ID    Functional Requirement Description
                                                         Trace
       The system shall accept participant profile data from the existing web
 FR1                                                     G1.2
       platform as a structured JSON payload.
       The system shall accept seating layout data from the existing web platform
 FR2                                                     G1.2
       as a structured JSON payload.
       The system shall allow event organizers to configure the weights of the
 FR3                                                     G1.1
       supported soft constraints.
       The system shall map the configurable event rules into computable hard
 FR4                                                     G1.1
       constraints and weighted soft constraints.
       The system shall generate a seating allocation result based on participant
 FR5                                                     G1.2
       profiles, seating layout, and constraint configuration.
       The system shall return the generated seating allocation result in a frontend- G1.2,
 FR6
       consumable JSON format, including when the run fails. G1.3
       The system shall return the solver status of every allocation run
       (OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, or error) together
 FR7   with a clear status message when allocation succeeds, fails, or becomes G1.3
       infeasible; a FEASIBLE seating allocation result shall be reported as
       OPTIMAL_NOT_PROVEN when a proven optimum is required.

       The system shall calculate and return reproducible quality indicators for
       every generated plan including solver status, independent hard-constraint
                                                         G1.3,
 FR8   validation result, total weighted soft-constraint penalty with a per-
                                                         SG3
       constraint breakdown, movement count and distance where applicable, and
       runtime.
       The system shall perform dynamic reallocation as incremental repair of the
       published plan, modifying only the assignments affected by a change
                                                         G2.1,
 FR9   minimizing first the number of unaffected participants moved and shall
                                                         G2.2
       store the repaired result as a new plan version requiring organizer approval
       under FR14.
       The system shall allow event organizers to review generated seating plan
                                                         G2.2,
 FR10  versions, including the seating map and quality indicators, through the
                                                         SG3
       admin review page.
 FR11  The system shall allow seating results to be exported for event operation. G1.2
```

```text
       The system shall store and retrieve the persisted entities of the data model:
                                                         G1.2,
 FR12  events, participants, layouts, seats, constraint configurations, plan versions,
                                                         G2.2
       and assignments, with each plan version referencing its predecessor.
       The system shall allow a participant to retrieve their assigned seat and view
 FR13                                                    G3.1
       the seating map from the latest published seating plan.
       The system shall store every generated allocation result as a plan version,
                                                         G2.2,
 FR14  shall require explicit organizer approval before publication, and shall
                                                         G3.1
       expose only the latest published version to participants.
       The system shall validate every incoming payload against its schema and
                                                         G1.2,
 FR15  structural rules — including pre-model tier-capacity validation — and shall
                                                         G1.3
       return a structured, frontend-consumable error response for invalid input.
       The system shall re-check every generated seating plan against all hard
       constraints independently of the solver that produced it, including
 FR16                                                    G1.3
       reconstruction of the reported objective value, before the plan can be
       accepted.
       The system shall return a structured failure response containing the solver
       status and any determinable validation, capacity, or input failure reasons, G1.3,
 FR17
       shall prevent an unsuccessful result from being published, and shall allow G2.2
       the organizer to revise data, constraints, weights, or seat availability.
```

## 5.6. Consolidated Non-Functional Requirements

```text
                                                          Goal
 ID          Non-Functional Requirement Description
                                                          Trace
             The system shall return an OPTIMAL result within the configured
             60-second solver budget for the default dataset of 122 registrations
 NFR1:       and the 256-seat (232-assignable) case-study layout under the G1.3,
 Performance defined evaluation environment; when the budget expires before SG1

             optimality is proven, the system shall return the actual solver status
             and shall not represent the solution as optimal.

             The system shall enable an event administrator to generate and
 NFR2:
             publish a seating plan without assistance after a single briefing SG4
 Usability
             session (criterion subject to stakeholder validation).
             The system shall not publish a plan that fails input validation,
 NFR3:       solver processing, or independent post-solve validation, and shall G2.2,
 Reliability keep the previously published plan unchanged and accessible G3.1
             when such a failure occurs.
```

```text
             The system shall isolate the constraint configuration from the
 NFR4:
             solver logic such that a change to the constraint configuration G1.1
 Maintainability
             requires no modification of solver code.
             The system shall inherit administrative access from the host
             platform's authentication, shall restrict unpublished plan versions
 NFR5:
             to authorized administrators, shall allow each participant to view
 Security &                                               G3.1
             only their own assignment from the latest published version, shall
 Privacy
             use pseudonymous participant identifiers in the solver payload,
             and shall retain data in line with the event lifecycle.
             The system shall support the validated operational baseline of 122
 NFR6:       registrations and the 232-assignable-seat layout and shall treat
                                                          MG1
 Scalability larger datasets as exploratory scalability experiments paired with
             layouts of sufficient capacity.
             The participant seat lookup should remain available throughout the
 NFR7:       event window, the target availability level should be elicited and
                                                          G3
 Availability agreed with Netizen eXperience because the lookup depends on
             the host platform's availability characteristics.

             The system shall produce the same canonical allocation and
 NFR8:       quality indicators for identical normalized input data, constraint
                                                          SG1
 Reproducibility configuration, solver parameters, and deterministic seed, repeated
             executions .
```

# 6. Requirement Engineering (RE) Analysis Modelling

## 6.1. Use Case Diagram

### Primary use case description - Generate Seating Plan

```text
 Field         Description

 Use Case      Generate Seating Plan

 Primary Actor Event Administrator

 Supporting Actor Seat Allocation Solver Function

 Goal Trace    G1 (G1.1–G1.3)

 Precondition  The system should receive selected participant data, venue seating layout,
               and constraint configuration.
```

```text
 Trigger       Organizer clicks Generate Plan in the admin module.

               1. Platform packages participants, layout, configuration, and optional

               previous allocation into a JSON payload.
               2. Engine validates schema, derives the demand-driven tier bands, and
               checks band capacity.
               3. Engine builds the integer constraint model over eligible combinations
               only.
 Main Success
               4. CP-SAT solver function solves the seating allocation within the
 Scenario
               configured time budget.
               5. Engine extracts assignments and penalty breakdown.
               6. Independent validator rechecks all the hard constraints and the
               reconstructed objective.
               7. Result is stored as a new seating plan version.
               8. Organizer reviews the version and quality indicators.

               2a. Invalid payload return structured INVALID_INPUT error.

               2b. Capacity exceeded return a structured infeasibility explanation
               message without invoking the solver.
               4a. INFEASIBLE / UNKNOWN status and conflict hints returned, the
 Extensions    organizer relaxes rules or adjusts seat range.

               4b. FEASIBLE  with proven optimum required reported as
               OPTIMAL_NOT_PROVEN
               6a. Independent validation fails lead to result rejected, failure reported.

               A reviewable plan version exists; nothing is published without explicit
 Postcondition
               approval (UC6).
```

## 6.2. System Flowchart

## 6.3. System State Machine Diagram

The system state machine diagram above demonstrated the life of one seating allocation session in the seat allocation solver function. First, the serverless aspect of the engine is illustrated in the entry transitions, which a first invocation of the solver function requires to transition into a ColdStart state before starting to solve the seating allocation. The Solving State fork into two (2) different states, either ResultReady state when the solver returns the status of OPTIMAL or

FEASIBLE and generates a seating map solution, or the Failed state when the returned solver status is INFEASIBLE, INVALID or TIEMOUT. Also, moving the ResultReady to the UnderReview state, the system state can branch into two (2) different state, which either back to the Solving state when the event administrator choose to regenerate the seating plan again, or forward to the Published state when the event administrator approved the result and published the seating map to participant.

The most important part to be observed from the state machine diagram above is the seating map reallocation looping, where a Published seating plan can be Reloaded and fed back into the Solving state as reference, so that the incremental repair of the seating plan could minimize the movement of the participant. The session thus only will be terminated from the Published state, when the event administrator confirmed that the latest published seating plan is in the single stagble resting state of the system.

## 6.4. Class Diagram

The data modeling structure started from the Event class as the root, which an event may be registered by many Participants, and each event will only use one single venue layout. Every event is configured by one ConstraintConfig class, which consists of HardConstraint and SoftConstraint definition. Each event may produce many AllocationPlanVersion that represent the seat assignment results from the generation operation. There is also a self-reference relationship on the AllocationPlanVersion class, which lets the reallocation compare and measure the movement against the prior published seating plan. Each Seat class carries the physicalPosition and priorityRank as separated attributes to separate the aisle logic from the preference logic. The solver function engine-side SolverEngine and ConstraintModelBuilder are cleanly separated from the domain and artifact classes by implementing the Builder design pattern, so that the model’s builder operations are concrete realization of the constraint model, but not a property of the domain data.

## 6.5. Swimlane Diagram for Generate Seating Plan Use Case

# 7. Methodology

## 7.1. Software Development Methodology: Agile SCRUM implementation with Netizen eXperience

This final year project implemented the Agile software development methodology, specifically the SCRUM framework together with the Netizen eXperience assigned industry supervisor, Mr. Cheah Poh Xiang. Based on the Figure 8 above, each sprint in Agile SCRUM framework consists of four SCRUM ceremonies including the Sprint Planning for backlog brainstorming and task effort estimation, followed by Daily Standup Meeting for ongoing progress synchronization, and closed by a Sprint Review to demonstrate the developed increment of the intelligent seating allocation system, and Sprint Retrospective that discover the possible improvement steps derived from goods and bad practices observed during a sprint. All the ceremonies in Final Year Project 1 (FYP1) phase are held on Wednesday with the industry supervisor and the developer that are currently maintaining the Netizen eXperience Event Management platform for PJKIT. The project is implementing a two-week sprint setting, which Sprint Planning and the Stand-up meeting run weekly from 10:00am to 10:15am to set and update the sprint backlog status, while the more important Sprint Review and Retrospective run biweekly from 10:30am to 11:00am to demonstrate the increment developed in the sprint and reflect on the sprint.

## 7.2. Software Architecture Diagram

The proposed intelligent seating allocation system in this project adopts a four-layer architecture that separates the actors who use the system from the internal or external software that they interact with, a computation layer that focus on generating the seating plan at serverless compute side, and the storage that persists the required metadata for event, participant, and seating allocation result. Based on Figure 9 above, the first layer of the architecture model is the Users layer that holds the two primary actors of the system, which are the Event Administrator and the Event Participant. The second layer is Application Layer, which is the Netizen eXperience Event Management Platform, containing the Admin Seating Allocation Dashboard, a Next.js server component that will call the server actions that will interact with the deployed AWS resources via AWS SDK. The Application Layer also contains a Participant Seat Lookup Interface that will fetch and display the latest participant seating details on the latest published seating map retrieved from DynamoDB. The Compute Layer is focus on the AWS serverless, where an AWS Lambda function hosts the core seating allocation engine and its embedded Google OR-Tools CP-SAT solver function. The Data Layer is AWS storage, comprising Amazon DynamoDB to store event, participant, and allocation metadata, along with the latest-approved seat references. Amazon S3 is also being deployed to Data Layer to store the versioned seating-plan result JSON for seating plan generation record traceability and referencing the latest seating plan. The implementation of the layered architecture model ensures that each tier depends only on the one above it, so the application, the solver function, and the storage can be scale and modify independently. The primary flow begins with the Event Administrator. From the Admin Seating Allocation Dashboard, the organizer optionally configures the constraints and selects the range of participant data to be involved in the event seating allocation. Then, the Next.js server component transforms this data into a structure JSON file that will be used to invokes the Lambda function in the Compute Layer through the AWS SDK. The seating allocation engine builds and solves the model with CP- SAT and returns the optimal/feasible solution together with its solver status inside the Lambda function. The resulting seating-plan JSON will then send back as response to the server component that invoke the solver function, which triggers server actions to store the event and participant metadata in DynamoDB and the versioned seating-plan document in S3. When a change occurs after publication, the same path is used for reallocation where the server component re-invokes the Lambda function with the updated payload and the previous seating plan, so that the engine will perform repairs and minor adjustment on existing seating plan rather than regenerates the whole seating plan with all the same data payload. The Event Participant never reaches the compute tier, the Participant Seat Lookup Interface requests participant-specific seating details from the server component, which serves the latest published seating details read from DynamoDB, and the participant could view their seat. The takeaway is that computation is triggered only by the administrator and runs on demand, while the participant's path is a short, read-only lookup of already-approved data.

## 7.3. Methods and Technologies Adopted

```text
 Method / Technology      Role in the Project

 Constraint Programming (CP) with Core method used to model event seating rules as a

 hard and weighed soft constraints Constraint Optimization Problem.
```

```text
                          The library used to execute the constraint model and
 Google OR-Tools CP-SAT solver report explicit solver statuses (optimal, feasible,

                          infeasible, model invalid, unknown).

                          Programming language used for the implementation of
 Python 3
                          the seat allocation solver function.
                          An on demand serverless deployment of the engine,
 AWS Lambda
                          invoked with an explicit solver time budget.

 AWS SDK (from the Next.js Invocation channel for AWS infrastructure with JSON
 service component)       payloads and results.

                          Existing Netizen eXperience Event Management
                          platform that is currently hosting the admin module and
 Next.js / React (TypeScript)
                          integration with an participant lookup route as the
                          outcome of the project.

                          Persistence of allocation metadata and versioned plan
 Amazon DynamoDB & Amazon S3
                          JSON respectively.
                          Infrastructure-as-code framework used to provision the
 SST Framework
                          AWS resources.

                          Tracking all the backlog and task for the development of
 GitHub Issues & Projects intelligent allocation system in the Netizen eXperience
                          repository.
```

# 8. Propose Interface design

## 8.1. Event Administrator Seating Allocation Dashboard

## 8.2. Event Participant Seat Lookup Portal

# 9. Requirement Resources and elicitation requirements

## 9.1. Literature Review

### 9.1.1. Existing Seat and Space Allocation Systems

The table below listed the existing seat and space allocation systems used in event planning.

```text
 No Existing System Main Capability        Limitation

 1  Manual Excel / Allows organizers to manually No automated allocation, no
    Spreadsheet   record participant names, seat fairness metric, no

    Planning      numbers, groupings, and remarks. optimization, and difficulty

                                           handling dynamic changes.
 2  Manual Seating Allow organizers to manually Highly dependent on human

    Chart / Paper- place participants on a physical or judgment and difficult to scale
    Based Layout  digital seating layout.  for hundreds of participants.

 3  Cvent / Social Supports event management, Strong in event planning and

    Tables        event diagramming, collaboration, visualization but limited in
                  and floor planning.      explicit fairness-driven

                                           weighted constraint
                                           optimization.

 4  PerfectTablePlan Supports guest details, RSVPs, Provides useful automatic

                  preferences, automatic   seating support, but formal
                  assignment, drag-and-drop fairness metrics and

                  seating, last-minute changes, and configurable weighted
                  printed floor plans.     constraint optimization are not

                                           the focus.

 5  WeddingWire   Supports drag-and-drop seating Useful for event seating
    Seating Chart charts, RSVP tracking, table visualization but limited in

    Tool          shape customization, sharing, formal optimization and
                  printing, and exporting. fairness evaluation.

 6  Zola Seating  Supports table assignment, floor Useful for basic guest seating

    Chart Tool    plan customization, guest planning, but limited in
                                           constraint optimization,
```

```text
 No Existing System Main Capability        Limitation

                  grouping, printing, downloading, dynamic reallocation, and
                  and sharing.             fairness scoring.
```

### 9.1.2. White Space Analysis Table

```text
             Participant-Facing Configurable Controlled Constraint-
 Existing Method
             Seat Lookup After Participant-Profile- Dynamic Based
 / System
             Admin Allocation Based Allocation Reallocation Optimization
 Manual Excel /
             No           No            No            No
 Seating Chart
                                        Partial editing with
 Cvent       Partial      Partial / limited           No
                                        synchronization
                                                      Yes, Genetic
                          Partial, through
                                        Partial last-minute Algorithm-
 PerfectTablePlan No      guest proximity
                                        editing       based automatic
                          preferences
                                                      assignment
 WeddingWire /
             Sharable     Weak          Manual adjustment No
 Zola
 Proposed FYP
             Yes          Yes           Yes           Yes
 System
```

The white space analysis indicates that existing systems excel at visual event planning, guest list management, manual seat arrangement, drag-and-drop seating, and printable chart generation. When visualizing tables, chairs, or floor plans is the primary goal, these features are very helpful to organizers. WeddingWire and Zola also facilitate the creation of floor plans, guest placement, and the export or sharing of seating charts (WeddingWire, n.d.; Zola, n.d.). Additionally, comparison reveals several significant gaps. First, most tools do not support automated allocation based on comprehensive participant profiles; the organizer is typically responsible for managing attributes like priority, contribution level, organizational position, attendance history, group relationship, and event-specific rules. Second, rather than using systematic reallocation, dynamic changes like participant absence or last-minute substitute are typically handled by manual editing. Third, configurable constraint weights receive little explicit support, leaving organizers unable to formally adjust the relative importance of competing allocation criteria. Fourth, most systems offer no measurable fairness metric by which to judge whether a generated plan is balanced and defensible.

Among the researched commercial system, PerfectTablePlan is one of the more sophisticated, supporting automatic seating assignment and employing a genetic algorithm to search for strong layouts once the combinatorial space outgrows exhaustive search (Oryx Digital Ltd., n.d.-b). The automatic assignment does not deliver explicit fairness metrics, participant- profile-based constraint weighting, or dynamic weighted constraint optimization as the system’s central objective. A white space therefore persists in a system that unites automated seating allocation with configurable constraints and measurable fairness evaluation. The proposed Final Year Project (FYP) system addresses this gap with an intelligent seating allocation service that draws on participant profile data, predefined constraint templates, configurable soft-constraint weights, and fairness evaluation to generate seating plans. It is, in effect, not merely a visual seating chart tool but a decision-support system for fair, constraint-compliant allocation.

## 9.2. Elicitation Questionnaires

By utilizing the list of elicitation questionnaires in Appendix A, it provides the baseline information for the background of project study on the seating allocation problem happening in PJKIT, their current seating map generation workflow and the existing event-specific rules considered during the workflow which may ultimately derived into constraints that guide to solve the seating allocation problem in PJKIT. For example, answers to Part A contribute to the background of study of this project, the answers from Parts B to Part D became set of hard- constraint, Part E calibrated the soft-constraint weights and lastly the Part Of questions validated the reallocation stability expectation that produced Objective 2 and FR9/FR14.

## 9.3. Joint Application Development Workshop

A site visit to the PJKIT was conducted together with the industry supervisor from Netizen eXperience on 26th June 2026. The sire visit combined a semi-structured interview with PJKIT stakeholders, direct observation of the event venue physically. At the same day, a joint application development (JAD) workshop is carried out between the FYP student, Industry Supervisor - Mr. Cheah Poh Xiang and three (3) representatives including the head of administrator that handle on event seating allocation from PJKIT side to brainstorm, discuss and refine the requirement for the proposed intelligent seating allocation system. The result of the session is listing below:

```text
 Ref  Elicited Response for the Elicitation Questionnaires

      Exact attendance figures are not retained, but attendance across events in the past two
 A1
      years has consistently fallen within the 100–200 participant range.
      PJKIT holds one to two events per year that require a formal seating plan. The seating

 A2   rules are largely stable across events; only the preferred (soft) constraints vary between
      events.

      Seating preparation begins only about two weeks before the event and is carried out by
      a team of fewer than five senior volunteers who must personally know the participants
 A3
      and understand the significance of each placement; the task cannot be delegated to

      general staff.
      The hall comprises approximately sixteen rows of about sixteen seats, arranged concert

 B4   style, which a numbered seating section toward the front and a free-seating section
      toward the back of the venue.

      Certain seats are permanently unavailable owing to the building's structural elements;
 B5
      the affected rows simply lose a few seats.
      The most desirable seats are those of the east block near the center aisle, while the next
 B6
      most desirable are the west block (西單) seats nearest the aisle.

      Participants with limited mobility are seated at the side of the hall for ease of access, as
 B7
      standard practice.
      Placement is decided first by contribution tier, then by contribution amount, and
 C8
      thereafter by a combination of seniority and attendance at PJKIT events.

      Normally for events in PJKIT, three (3) contribution tiers are recognized, taken directly
      from the event registration form, which:
      1. Emperor tier required for participant to contribute at least RM5000 contribution
      amount in an event.
 C9
      2. Merit tier required participants to contribute at least RM3000 contribution amount in
      an event.
      3. Bodhi tier required participants to contribute at least RM2000 contribution amount in
      an event.

      The number of rows for each contribution tier occupies is not fixed. It depends on the
 C10  tier's registration count, so a larger Emperor turnout extends further toward the front.

      Tiers are seated in the order Emperor → Merit → Bodhi from the front, and a row may
```

```text
      be shared between two tiers when one tier's registrations end partway along a row, the

      next tier continues in the same row as to fill up the whole row.
      A registration normally occupies two adjacent seats by a married couple, which almost

 C11  always carry the same name. Registrations larger than two seats are extremely rare and

      are treated as exceptions.
      Within a tier, order is governed first by contribution amount; the remaining factors such

 D12  as seniority and previous event attendance are combined under weightings that have not
      yet been finalized from PJKIT side.

      Ties are understood to be resolved by registration order (first come, first served), to be
 D13
      confirmed with the client.
      Row filling follows the principle already described: rows are packed to capacity outward
 D14
      from the center aisle with no deliberately empty seats, in registration order.
      Special categories (monks/sifu, elderly participants, guests of honor) and accessibility
 D15
      needs are accommodated, but manually rather than by an explicit rule.

      No single factor is most important; conflicts are resolved pragmatically, tending to satisfy
 E16  participants more likely to complain. For planning, the model is directed to focus on

      contribution-to-seat matching and on participant activeness in previous PJKIT events.

 E17  A fixed ranking of the soft factors is not possible because the trade-off is situational.
      The weightings are not expected to change often, but the event administrator may adjust
 E18
      the emphasis of rules per event to loosen or tighten a given aspect.
      Walk-in or late registrations are uncommon because registration closes on a set date. The

 F19  change that does occur is the absence of a registered participant, sometimes with a

      replacement taking the vacated seat.
      The registration will close after a certain time, but participant absence can still occur

 F20  after finalization of the seating map generation. When the scenario happens, disruption
      to already-assigned participants must be kept minimal.

      When such a change occurs, the seating map is going to be revised to minimize the effect
 F21
      on already-assigned participants and avoid confusion at the venue.
      A plan or a revision is approved by the senior-volunteer working team together with the
 F22
      event administrator (sifu) before it is announced to participants.
```

# 10. Project Milestone

## 10.1. FYP 1 Gantt Chart

## 10.2. FYP 2 Gantt Chart

The 28-week schedule for the whole final year project distribute evenly for FYP1 (Weeks 1-14) and for FYP2 (Weeks 15-28), June to December 2026. Each sprint carries a goal and ends in a demonstrable increment reviewed at the biweekly demo, and requirements are refined continuously across sprints. This makes the milestone plan consistent with the Agile SCRUM methodology, while the two academic checkpoints FYP1 submission of Interim Report, FYP2 Completion of VIVA and submission of Dissertation remain as fixed milestones.

# 11. Overall finding and output

## 11.1. Preliminary Findings from Elicitation

The validated constraint and scenario base that underpin the entire requirement set were obtained via the elicitation processes (Section 9):

```text
 Preliminary Finding Description

 Validated event participant PJKIT’s event averagely includes 100 – 200 participant per event,
 scale and venue layout and the participants is allocating in a 16 rows × 16 seats venue

                    layout which in total of 256 numbered seats, where 232 assignable

                    after 24-seat is blocked by the building structure in the center of
                    the hall. Participants are arranged in a concert-style with a

                    numbered front section and a free-seating section at the back of
                    the venue.

 Existing workflow for PJKIT currently prepares all the seating maps for every event

 generating seating plan is manually by inserting participant name one-by-one into the
 conducted manually by predefined seating chart in an excel sheet. The seating map

 event administrator and generation procedure is carried out by a team of fewer than five
 volunteers.        senior volunteers who must personally know the participants and

                    understand the significance of each placement. The current

                    workflow takes up until two (2) weeks before the event day.
 Contribution tier structure Participants are first categorized by their contribution tier which

 as the first-order rule for either Emperor, Merit, or Bodhi tier. The seating allocation
 seating allocation ordered as the last row of Emperor tier should precede the first row

                    of the Merit tier, and the last row of Merit tier should precede the

                    first row of Bodhi tier. The seating row could be shred between
                    two different tiers to avoid empty seats in the numbered front row.

 Generic tools in the market The specific rules of PJKIT seating allocation for participants
 cannot be used to solve the increased the necessity to implement a customized solution that

 specific seating allocation could generate a seating map by satisfying all the structural rules

 problem in PJKIT   such as contribution tiering priority, side-of-hall placement of
```

```text
                    participants who need accessible seats and within-tier contribution

                    ordering.
 Dynamic participant data PJKIT will close the registration of the event on a set date, walk-

 change ad hoc event for in and late registration are uncommon scenario to occur in PJKIT

 PJKIT events       event. However, the primary ad hoc event case for PJKIT is the
                    absence of a registered participant, sometimes also with

                    replacement participant to take the vacated seat on the event day.
                    In every case the stakeholder expectation is that a published plan

                    is repaired with minimal disruption instead of regenerating the

                    whole seating map again.
 Constraint programming Every elicited structural rule for event seating allocation in PJKIT

 with CP-SAT is suitable for are expressible as a pure-integer that could be used by the CP-SAT
 creating the solver function model to solve the seating allocation problem and generate a

 to solve PJKIT seating seating plan result within the configured time budget, the

 allocation business case independently implemented validator confirms zero hard-
                    constraint violations and reconstructs the reported objective value

                    exactly, and repeated runs reproduce the identical canonical plan
```

## 11.2. Constraint Listing Output

```text
 Constraint Ref Rule (plain language)                  Classification

            Each participant is assigned exactly one allocation unit (one
 C1                                                      Hard
            seat; one valid seat pair for Emperor registrations).
            Each seat is occupied by at most one participant (both seats of
 C2                                                      Hard
            an assigned Emperor pair count as occupied).
 C3         Blocked or unavailable seats must not be assigned. Hard

            Assignments must fall within the valid seat range of the event
 C4                                                      Hard
            layout.
 C5         Only participants of eligible status may be seated. Hard

            Participants with higher contribution/priority scores should Soft
 C6
            receive seats of higher priority rank.      (weighted)
```

```text
            Participants with higher activeness scores should be favored Soft
 C7
            within their tier.                          (weighted)
            Participants should be seated in zones suitable for their Soft
 C8
            category (within-tier suitability preference). (weighted)

            Upon  reallocation, unaffected participants retain their
            previous seats by default; unavoidable movement is
                                                          Soft
 C9         minimized in number and then in distance (movement
                                                        (weighted)
            minimization; penalty is zero when no previous allocation
            exists).

            An Emperor registration occupies exactly two adjacent seats
            forming one of the venue's valid within-row pairs; when no
 C10                                                     Hard
            adjacent guest name is provided, both seats display the
            primary participant's name.

            No Emperor pair may straddle the center aisle: positions 8 and

 C11        9 never form a pair. Physical adjacency is determined by Hard
            physical seat position, never by priority rank.

            Tier-band placement: tiers occupy contiguous, demand-
            derived row bands ordered Emperor → Merit → Bodhi from

            the front of the hall; a boundary row may be shared between

 C12        two adjacent tiers (when one tier ends partway along a row, Hard
            the next continues in it) so the numbered section packs with

            no empty seat; band capacity (with Emperor units counting
            two seats) is validated before model construction.

            Within each tier, a participant with a higher contribution score

 C13        is never seated in a later row than a participant with a lower Hard
            score.

            Among plans of equal weighted penalty, a deterministic tie- Modelling
 C14        breaking rule selects a canonical plan; the tie-break term is rule

            scaled so it can never override any weighted penalty. (objective)
```

```text
            Front-to-back packing where the numbered section fills

 C15        seating from front to back with no empty seat (the remaining Hard
            assignable rows form the free-seating section).

            Centre-out fill where each side of a row fills outward from the

 C16        center aisle, so no gap appears between the aisle and an outer Hard
            occupied seat.

            A participant who requires an accessible seat is placed at a
 C17        side/edge seat of the hall (for an Emperor unit, a pair at the Hard

            side), for ease of access.
```

# 12. Conclusion

This report has presented the planning-phase work of a Final Year Project that addresses a genuine and recurring operational problem which the manual seating allocation for large-scale assembly events. The background established that seating allocation is a multi-criteria combinatorial problem whose solution space grows explosively with participant numbers, and that the case-study organization, PJ Kwan Inn Teng, currently manages events of 100 - 200 participants in a 256-seat venue (232 assignable after its structural blocked center block) governed by demand-derived tier bands, two-seat Emperor allocation units, an aisle that breaks adjacency, and contribution-ordering rules - using spreadsheets, printed charts, and PDF listings. Manual allocation is slow and inconsistent between allocators and cannot be objectively justified against the community's own priority rules; late data changes and ad-hoc registrations force disruptive, error-prone rework of nearly finished plans; and participants queue at the venue to retrieve seats from printed lists that may already be outdated. Without the research and development undertaken in this project, these consequences persist and worsen as event attendance grows.

The literature review demonstrated that neither commercial tooling nor the published seating-allocation literature offers this combination which related to a declaratively configurable, status-reporting, and stability-aware seating allocation engine. The contribution of this project is a to develop a configurable, constraint-based seating allocation system whose core is a solver engine that models real event rules formalized in Section 11.2 as a Constraint Optimization Problem that solved by Google OR-Tools CP-SAT solver and deployed as a Python script on AWS Lambda function that invoked with JSON payloads directed from the Netizen eXperience event management platform. The system provides organizer-controlled generation, versioned review and publishing, configurable rules over PJKIT's domain attributes, controlled dynamic reallocation that incrementally repairs the published plan for ad-hoc participants while leaving unaffected participants in their initial assigned seat. This project also aimed to develop participant-facing lookup interface for PJKIT participants to enable them to perform self-checking on the latest published seat from event administrator before or during the event day.

# 13. References

WeddingWire. (n.d.). Wedding seating chart tool. https://www.weddingwire.com/wedding- planning/wedding-seating-tables.html

Zola. (n.d.). Wedding seating chart: Seat all your guests in minutes. https://www.zola.com/wedding-planning/seating-chart

# 14. Appendices

## Appendix A: Elicitation Questionnaires

```text
 Part A: Event scale and context

 1. How many participants typically attend PJKIT annual assembly, and how does number of
 participants vary between events in PJKIT?

 2. How many events per year require a formal seating plan, and are the rules the same across

 them?
 3. How long before the event does seat preparation currently start (total days/week needed to

 generate a seating plan for each event), and how many PJKIT's human forces (staff + volunteer)
 are involved?

 Part B: Venue and layout structure

 4. How is the venue physically layout look like? How many rows in total, how many seats are
 allowed per row?

 5. Are there seats that must never be assigned (blocked, reserved, equipment, safety)?
 6. Which seats do you consider the "best" seats, and what makes one seat better than another

 (row, closeness to the center, closeness to the front stage)?
 7. Are there seats designated or preferred for participants with mobility difficulties or

 wheelchairs?

 Part C: Tiering (the first-order allocation factor)

 8. What is the first factor that decides where a participant will be seated — contribution tiering,
 contribution amount, participant role (normal public community, staff from PJKIT, monk/sifu

 from PJKIT, volunteer), seniority, or something else?

 9. How are the contribution tiers defined, and what are the boundaries between them such as
 contribution amount thresholds?

 10. Are the number of rows assigned to each contribution tier fixed for every event in PJKIT, or
 does the number of rows depend on how many people register in each tier? In what order are

 the tiers seated from the front of the hall, and can a tier's rows ever be shared with the next tier?

 11. Do any registrations occupy more than one seat? If so, must the two seats be adjacent, and
 may they be split across an aisle?
```

```text
 Part D: Ordering, filling, and special placement within the same tier
 12. Within the same tier, what decides who sits in front of whom — exact contribution amount,

 activeness or participation history for event in PJKIT, seniority, or registration order?

 13. If two participants have identical standing, how do you break the tie today?
 14. When a tier's rows are not completely full, where do the empty seats end up — the back

 rows of the tier, the outer edges of rows, or spread evenly? Do you fill each row outward from
 the center aisle?

 15. Are there participant categories with special placement expectations (monks, elderly

 participants, guests of honor), or participants who require an accessible seat?

 Part E: Relative importance of the soft factors (weighting)
 16. Among the factors just mentioned — contribution-to-seat matching, activeness, category-to-

 zone suitability — which is the most important to satisfy when they conflict?

 17. Could you rank these factors, or say which factor you would sacrifice first if not all can be
 satisfied?

 18. Would you want the ability to change these priorities per event, and who should be allowed
 to change them?

 Part F: Ad-hoc events and dynamic changes
 19. What last-minute changes have you experienced in past events (withdrawals, substitutions,

 walk-in registrations), and how frequently do they happen on the event day itself?
 20. When a change happens after the plan is finalized, how much of the existing plan are you

 willing to change and which participants must not be moved?
 21. How is a revised plan being prepared with the current workflow is the mentioned ad hoc

 event above what happens, and what problems has that caused the event?

 22. Who has the authority to approve or revise the seating plan before it is announced to
 participants?
```

## Appendix B: Requirement Traceability Matrix

```text
 Goal                 Realized by (FR)      Constrained by (NFR)

 G1.1 Model rules as
                      FR3, FR4              NFR4
 constraints
                      FR1, FR2, FR5, FR6, FR11,
 G1.2 Generate plans                        NFR1, NFR6, NFR8
                      FR12, FR15
 G1.3 Verifiable status & FR6, FR7, FR8, FR15, FR16,
                                            NFR1, NFR3
 indicators           FR17
 G2.1 Incremental, movement-
                      FR9                   NFR1, NFR8
 minimizing repair

 G2.2 Versioning, approval, FR9, FR10, FR12, FR14,
                                            NFR3
 publishing           FR17
 G3.1 Latest-published-only
                      FR13, FR14            NFR5, NFR7
 participant access
 SG1 Fairness & consistency FR5, FR8        NFR1, NFR8

 SG2 Reduced manual effort FR5, FR9, FR13   NFR2
 SG3 Explainability   FR7, FR8, FR10        —

 SG4 Usability        FR10, FR13            NFR2
```
