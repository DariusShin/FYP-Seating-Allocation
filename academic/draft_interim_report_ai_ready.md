---
source_pdf: Draft_Interim_Report_To_GPT.pdf
extracted_on: 2026-07-28 14:52:30
page_count: 46
extraction_method: pdftotext -layout + embedded image extraction
---

# Draft Interim Report - Extracted Markdown

> AI-agent-ready extraction from the uploaded PDF. The original wording, page order, captions, and table-like spacing are preserved as closely as possible. Embedded figures/screenshots are extracted into the `draft_interim_report_extracted_assets/` folder and referenced near their original PDF pages.


<!-- Page 1 -->

<!-- Extracted image(s) from PDF page 1: -->
![Extracted image from page 1](draft_interim_report_extracted_assets/page_01_image_01.png)

                     UNIVERSITI TEKNOLOGI PETRONAS

                                Department of Computing


                                    Interim Report


 Project title: Intelligent Automated Seating Allocation System for Large-Scale
             Assemblies Using Configurable Constraint Optimization


                           Supervisor: Ts. Dr. Ooi Boon Yaik


              Name                  Student ID                   Course

         Darius Lee Shin                22003269   Bachelor of Computer Science (Hons)


<!-- Page 2 -->

# Table of Contents
1. Introduction ................................................................................................................................. 4
   1.1 Project Vision ........................................................................................................................ 4

   1.2 Background of Study ............................................................................................................ 4

   1.3 Problem Statement ................................................................................................................ 7

   1.4 Objectives ............................................................................................................................. 8

   1.5 System Goal and Requirements ............................................................................................ 8

       1.5.1 Goal Tree ........................................................................................................................ 9
       1.5.2 Goal Definition .............................................................................................................. 9
       1.5.3 Consolidated Functional Requirements ....................................................................... 10
       1.5.4 Consolidated Non-Functional Requirements ................................................................11
2. Literature Review...................................................................................................................... 13
   2.1 Existing Seat and Space Allocation Systems ...................................................................... 13

   2.2 White Space Analysis ......................................................................................................... 14

   2.3 Constraint Modelling and Rule Conversion in Seating Allocation ..................................... 16

   2.4 Comparison of Seating Allocation Methods ....................................................................... 17

   2.5 Literature Synthesis Against Problem Statements .............................................................. 19

3. Methodology ............................................................................................................................. 20
   3.1 Software Development Methodology: Agile SCRUM ....................................................... 20

   3.2 Software Design and Architecture ...................................................................................... 21

       3.2.1 Use Case Diagram........................................................................................................ 21
       3.2.2 System Flowchart......................................................................................................... 23
       3.2.3 System State Machine Diagram ................................................................................... 24
       3.2.4 System Architecture Diagram ...................................................................................... 26
       3.2.5 Class Diagram .............................................................................................................. 28
       3.2.6 Swimlane Diagram for Generate Seating Plan Use Case ............................................ 29
   3.3 Methods and Technologies Adopted ................................................................................... 30


<!-- Page 3 -->

   3.4 Seating Allocation Optimization Lifecycle ......................................................................... 31

   3.5 Preliminary Works .............................................................................................................. 31

       3.5.1 Interview and Joint Application Development Workshop ........................................... 31
       3.5.2 Preliminary Findings from Elicitation ......................................................................... 32
       3.5.3 Constraint Listing Output ............................................................................................ 33
   3.6 Proposed System Interfaces ................................................................................................ 35

       3.6.1 Event Administrator Seating Allocation Dashboard .................................................... 35
       3.6.2 Event Participant Seat Lookup Portal .......................................................................... 36
   3.7 Project Timeline .................................................................................................................. 36

       3.7.1 FYP 1 Gantt Chart........................................................................................................ 36
       3.7.2 FYP 2 Gantt Chart........................................................................................................ 37
4. Conclusion ................................................................................................................................ 38
   4.1 Summary of Project Progress.............................................................................................. 38

   4.2 Future Work Recommendation ........................................................................................... 39

5. References ................................................................................................................................. 40
6. Appendices ................................................................................................................................ 42
   Appendix A: Elicitation Questionnaires ................................................................................... 42

   Appendix B: Interview Result and Finding .............................................................................. 44


<!-- Page 4 -->

# 1. Introduction
The project title of my Final Year Project (FYP) is titled as "Intelligent Automated Seating
Allocation System for Large-Scale Assemblies Using Configurable Constraint Optimization".
This project collaborates with Netizen eXperience to solve the existing seating allocation problem
on the Petaling Jaya Kwan Inn Teng (PJKIT)'s annual events.

## 1.1 Project Vision
The vision statement for this Final Year Project (FYP) is as below:

"To provide an intelligent and configurable seating allocation system that supports constraint-
compliant seating arrangements for large scale assemblies, enabling event administrator to
generate seating plans automatically by considering participant profiles, priority rules, and event-
specific constraints, and to support ad hoc event handling for seating allocation on the event day."

## 1.2 Background of Study
Large-scale assembly events such as community gatherings, convocation, ceremonies, and
religious assemblies frequently require event administrator to choose the seating for their event
participants. Although the task of seating assignment for event participants appears to be an
administrative task, it is a multi-criteria combinatorial assignment problem (Rossi et al., 2006;
Ipsen et al., 2026). Each participant must be matched and assigned to exactly one seat in a limited
seating layout, and each seating assignment must simultaneously adhere and satisfy a set of
interrelated event-specific rules. For example, participants of specific categories may need to be
placed in specific seating zones, participants with higher event priority or contribution may receive
a more favorable seat, and certain seats may be blocked or reserved from event participants. The
number of possible assignments grows explosively with scale, which even in the simplified case
where each of the case study's 150 participants assigned a single seat among a venue that can
support up to 232 seats, the number of possible ordered seat assignments is denoted as
232!/(232 - 150)! approximately 8.75 × 10326 of possible combinations for the seating plan,
which is infeasible to check manually by human and it is impractical for machine to enumerated it
naively (Rossi et al., 2006).

       The case-study organization of this project, which Petaling Jaya Kwan Inn Teng (PJKIT),
organized large annual community events that consisted of 100 to 200 participants per event. These


<!-- Page 5 -->

<!-- Extracted image(s) from PDF page 5: -->
![Extracted image from page 5](draft_interim_report_extracted_assets/page_05_image_01.png)

events are held in a hall that could be set up to 16 rows and 16 seats per row, which in total 232
assignable seats after structurally blocked divider in the center of the hall based on the given layout
from previous events. The current seating assignments workflow implemented by PJKIT is a
typical manual procedure across many event administrator, which participant records are first store
in excel spreadsheets, then the event administrator create the seating plan by manually filling each
participant's name in a predefined excel spreadsheet template as shown in Figure 1 below, the
created seating plan will then be will convert into PDF document that will be shared digitally with
participants through WhatsApp and used to print out an A2 sized venue chart.


**Figure 1 PJKIT''s annual event venue layout**

       The seating allocation decisions made by PJKIT event administrator are not arbitrary for
every single event, instead they adhere to a set of event-specific rules that caused the seating
allocation problem to be more complicated than general seat assignment that relies on selection
and randomness. In the context of PJKIT annual event-specific rule, participants will be divided
into three (3) contribution tiers, which the Emperor, Merit and Bodhi. The contribution tiering is
used as the primary criteria to determine the precedence of the seating arrangements from the front
of the hall, which each Emperor row should precede the first Merit Row, and every Merit row
should precede the first Bodhi row. The seating boundaries for each tier are not a fixed zone, but


<!-- Page 6 -->

it is determined by the demand. On the other hand, each tier seating row also has their allocation
rule to determine which participant will be allocated toward a more favorable seat in each row. For
example, the participant with high contribution should be seated in a higher favorable row
compared to the less contributed participant within the same tiering. The event administrator from
PJKIT have to hold many competing considerations in mind at once to balance these coupled
allocation rules manually for over a hundred of participants every event, which contribute to the
inefficiency as the seating map preparation usually consumed more than a week from the starting
of manually assigning seat, validate until finalize the seating plan.

       Commercial event-planning tools such as Cvent, PerfectTablePlan, WeddingWire, and
Zola offer features including floor plan design, table arrangement, guest list management, drag-
and-drop seating and printable seating charts. Whole WeddingWire and Zola offer similar features
for creating floor plans, assigning guests, and exporting or sharing arrangements (WeddingWire,
n.d.; Zola, n.d.), PerfectTablePlan, for example, manages guest details, preferences, manual drag-
and-drop or automatic seat assignment, it also supports printable charts (Oryx Digital Ltd., n.d.).
However, these solutions prioritize visualization of seat allocation, guest arrangement, and manual
planning support rather than explicit fairness-driven allocation controlled by customizable
weighted constraint.

       The consequences that will be faced by PJKIT of continuing their current manual seating
allocation workflow are severe and compounding. First, the quality of seating allocation decline
as scale of participants increases, two different event staff member allocating the same event would
result in two different plans, and neither of them could be objectively justified against the
community's stated tier, pairing and priority rule, which causing the event administrator to be
expose to the perceptions of unfairness. Then, the preparation of the seating map consumes an
unreasonable amount of volunteer time in the weeks before the event. Any late change, such as an
absence, a substitution, or a newly registered walk-in ad hoc participant, requires an error -prone
rework on a nearly completed seating plan. Each manual revision and reallocation of participants
seat may increase the risk of introducing duplicate seat assignments, or missing participants.

       This final year project is carried out in collaboration with Netizen eXperience, a software
company that provides end-to-end digital solutions in Southeast Asia, which operates a Corporate
Social Responsibility (CSR) event management platform currently used by PJKIT to manage


<!-- Page 7 -->

events and participants registrations and historical record. Netizen eXperience has appointed a
Tech Lead as the industry supervisor to provide technical advice and facilities development for the
seating allocation system. The industry supervisor also acts as the intermediary for requirement
gathering, validation and organizing the site visit for discussion with PJKIT stakeholders. The
seating allocation system proposed in this project is designed to be integrated as a new system
module into the staging environment for the existing event management platform of Netizen
eXperience rather than a stand-alone academic prototype.

## 1.3 Problem Statement
This project addresses three (3) pain points that are identified from the background of study in
Section 3.1 and validated against the current event seating map generation workflow of PJKIT.

#### Problem Statement 1: Inconsistency and inefficiency in multi-criteria manual seating
allocation workflow
The manual participant seating allocation workflow requires the event administrator to consider
many participant profiles simultaneously, including participant's contribution, tiering priority,
activeness on participating in other events organized by PJKIT, and status of participation against
a constrained seating layout with demand-driven tier groups. This process is slow and does not
scale with the growth of participants number and seating layout expansion of the event. The quality
of the produced seating plan is difficult to validate or justify against the administrator's own stated
event-specific rules, and different event administrators make different decisions on assigning seats
to participants resulting in producing an inconsistent seating map.

#### Problem Statement 2: High operational disruption and lack of controlled dynamic
reallocation mechanisms
Manual workflows provide limited support for a controlled reallocation of seating maps following
changes to participant data closely to end of event preparation, and on the event day due to ad hoc
events such as participant absence or substitution of a participant. Once a plan has been published,
such a change creates a fundamentally different problem from initial allocation, it is a repair
problem, in which the assignment that are directly affected by the changes must be fixed while
preserving the rest of the previously communicated plan, that includes participants who may
already have been informed or seated at their locations. A late change that appears in the existing
manual participant seating allocation workflows may force event administrator from PJKIT to


<!-- Page 8 -->

revise the whole seating plan, which increases the risk of duplicate or outdated seat records, and
re-incurs the full cost and inconsistency of manual allocation for every small change.

#### Problem Statement 3: Communication bottlenecks and inefficiencies in participant seat
retrieval
Participants from PJKIT events currently relies on several ways to retrieve their assigned seats
details in an event including getting from the printed seating map that will be showing during the
event day, seats listing PDF document that shared by PJKIT event administrator or by asking the
event staff to check manually for them during the event day. This administrator-driven distribution
of participants seating information creates queues at the event, and it didn't provide assurance that
participants are reading the latest approved plan and offers no-self-service channel for participants
to check their assigned seat before or during the event.

## 1.4 Objectives
The objectives of this project derive directly from the three (3) problem statements and specify
what the project aimed at developing, solve and achieve.

#### Objective 1: To design and develop a configurable, constraint-based seating allocation engine
that converts participant profiles, seating layouts and configurable event-specific rules into
programmable constraints for automating the seating plan generation.

#### Objective 2: To develop a controlled incremental dynamic seating reallocation mechanism
that accommodates ad hoc participant data changes due to absence, substitutions of participant and
late registration, including on the event day by treating the latest published plan as the baseline
state and modifying only the affected seats.

#### Objective 3: To develop a participant-facing seat lookup channel that allows participants to
retrieve and view their assigned seat number and event seating map from the latest event
administrator published seating map.

## 1.5 System Goal and Requirements
This section defines the goal model under a single identifier scheme, which decomposes the single
root goal derived from the vision statement in Section 2 into a goal tree that maps the three (3)
problem statements and separating hard goals from soft goals in this project.


<!-- Page 9 -->

<!-- Extracted image(s) from PDF page 9: -->
![Extracted image from page 9](draft_interim_report_extracted_assets/page_09_image_01.png)

### 1.5.1 Goal Tree


**Figure 2 Goal Tree for Proposed Intelligent Seating Allocation System**

### 1.5.2 Goal Definition
  Goal ID    Goal Description                                                             Type
             The system shall enable event administrator to produce fair, rule-
             consistent seating plans for large-scale assemblies (validated baseline:
   MG1                                                                                    Root
             100-200 participants; 256-seat venue with 232 assignable seats) with
             reduced manual effort and controlled handling of ad-hoc changes.
             The system shall generate constraint-compliant seating plans
    G1                                                                                    Hard
             automatically.
             Event rules shall be modelled as computable hard constraints and
   G1.1                                                                                   Hard
             weighed soft constraints.
             Plans shall be generated from participant profiles, seating layout, and
   G1.2                                                                                   Hard
             constraint configuration.
             Every run shall report a verifiable solver status and reproducible quality
   G1.3                                                                                   Hard
             indicators.
             Published plans shall be reallocated under administrator control when
    G2                                                                                    Hard
             participant or event data changes.
             Reallocation shall repair incrementally, minimizing first the number of
   G2.1      unaffected participants moved and then total movement distance for the       Hard
             latest published seating map.
             Every generated or repaired result shall be a version requiring explicit
   G2.2                                                                                   Hard
             administrator approval before publication.
    G3       Participants shall retrieve their assigned seat themselves.                  Hard
   G3.1      Only the latest published plan shall ever be exposed to participants.        Hard
             The system should improve fairness and consistency of seating map
    SG1                                                                                   Soft
             generation.


<!-- Page 10 -->

                The system should reduce the administrator's manual effort on seating
      SG2                                                                                     Soft
                map generation.
      SG3       The system should make allocation results explainable.                        Soft
                The system should be usable by administrators without optimization
      SG4                                                                                     Soft
                knowledge.

### 1.5.3 Consolidated Functional Requirements
                                                                                          Goal
 ID         Functional Requirement Description
                                                                                          Trace
            The system shall accept participant profile data from the existing web
 FR1                                                                               G1.2
            platform as a structured JSON payload.

            The system shall accept seating layout data from the existing web platform
 FR2                                                                                   G1.2
            as a structured JSON payload.

            The system shall allow event organizers to configure the weights of the
 FR3                                                                                G1.1
            supported soft constraints.

            The system shall map the configurable event rules into computable hard
 FR4                                                                               G1.1
            constraints and weighted soft constraints.

            The system shall generate a seating allocation result based on participant
 FR5                                                                                   G1.2
            profiles, seating layout, and constraint configuration.

            The system shall return the generated seating allocation result in a frontend- G1.2,
 FR6
            consumable JSON format, including when the run fails.                          G1.3

            The system shall return the solver status of every allocation run
            (OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, or error) together
 FR7        with a clear status message when allocation succeeds, fails, or becomes G1.3
            infeasible; a FEASIBLE seating allocation result shall be reported as
            OPTIMAL_NOT_PROVEN when a proven optimum is required.

            The system shall calculate and return reproducible quality indicators for
            every generated plan including solver status, independent hard-constraint
                                                                                      G1.3,
 FR8        validation result, total weighted soft-constraint penalty with a per-
                                                                                      SG3
            constraint breakdown, movement count and distance where applicable, and
            runtime.

            The system shall perform dynamic reallocation as incremental repair of the
            published plan, modifying only the assignments affected by a change
                                                                                         G2.1,
 FR9        minimizing first the number of unaffected participants moved and shall
                                                                                         G2.2
            store the repaired result as a new plan version requiring organizer approval
            under FR14.


<!-- Page 11 -->

         The system shall allow event organizers to review generated seating plan
                                                                                  G2.2,
 FR10    versions, including the seating map and quality indicators, through the
                                                                                  SG3
         admin review page.

 FR11    The system shall allow seating results to be exported for event operation.     G1.2

         The system shall store and retrieve the persisted entities of the data model:
                                                                                         G1.2,
 FR12    events, participants, layouts, seats, constraint configurations, plan versions,
                                                                                         G2.2
         and assignments, with each plan version referencing its predecessor.

         The system shall allow a participant to retrieve their assigned seat and view
 FR13                                                                                  G3.1
         the seating map from the latest published seating plan.

         The system shall store every generated allocation result as a plan version,
                                                                                     G2.2,
 FR14    shall require explicit organizer approval before publication, and shall
                                                                                     G3.1
         expose only the latest published version to participants.

         The system shall validate every incoming payload against its schema and
                                                                                     G1.2,
 FR15    structural rules - including pre-model tier-capacity validation - and shall
                                                                                     G1.3
         return a structured, frontend-consumable error response for invalid input.

         The system shall re-check every generated seating plan against all hard
         constraints independently of the solver that produced it, including
 FR16                                                                            G1.3
         reconstruction of the reported objective value, before the plan can be
         accepted.

         The system shall return a structured failure response containing the solver
         status and any determinable validation, capacity, or input failure reasons, G1.3,
 FR17
         shall prevent an unsuccessful result from being published, and shall allow G2.2
         the organizer to revise data, constraints, weights, or seat availability.

### 1.5.4 Consolidated Non-Functional Requirements
                                                                                        Goal
 ID               Non-Functional Requirement Description
                                                                                        Trace
                  The system shall return an OPTIMAL result within the configured
                  60-second solver budget for the default dataset of 122 registrations
 NFR1:            and the 256-seat (232-assignable) case-study layout under the G1.3,
 Performance      defined evaluation environment; when the budget expires before SG1
                  optimality is proven, the system shall return the actual solver status
                  and shall not represent the solution as optimal.

                  The system shall enable an event administrator to generate and
 NFR2:
                  publish a seating plan without assistance after a single briefing SG4
 Usability
                  session (criterion subject to stakeholder validation).


<!-- Page 12 -->

                   The system shall not publish a plan that fails input validation,
 NFR3:             solver processing, or independent post-solve validation, and shall G2.2,
 Reliability       keep the previously published plan unchanged and accessible G3.1
                   when such a failure occurs.

                   The system shall isolate the constraint configuration from the
 NFR4:
                   solver logic such that a change to the constraint configuration G1.1
 Maintainability
                   requires no modification of solver code.

                   The system shall inherit administrative access from the host
                   platform's authentication, shall restrict unpublished plan versions
 NFR5:
                   to authorized administrators, shall allow each participant to view
 Security &                                                                            G3.1
                   only their own assignment from the latest published version, shall
 Privacy
                   use pseudonymous participant identifiers in the solver payload,
                   and shall retain data in line with the event lifecycle.

                   The system shall support the validated operational baseline of 122
 NFR6:             registrations and the 232-assignable-seat layout and shall treat
                                                                                      MG1
 Scalability       larger datasets as exploratory scalability experiments paired with
                   layouts of sufficient capacity.

                   The participant seat lookup should remain available throughout the
 NFR7:             event window, the target availability level should be elicited and
                                                                                      G3
 Availability      agreed with Netizen eXperience because the lookup depends on
                   the host platform's availability characteristics.

                 The system shall produce the same canonical allocation and
 NFR8:           quality indicators for identical normalized input data, constraint
                                                                                    SG1
 Reproducibility configuration, solver parameters, and deterministic seed, repeated
                 executions.


<!-- Page 13 -->

# 2. Literature Review
Beyond commercial event-planning software, a series of academic literature and study addresses
seating and spectator allocation as a combinatorial optimization problem. Ipsen et al. (2026)
formalize the Hierarchical Seating Allocation Problem for organizational office seating,
decomposing the seating assignment into per-level sub-problems and showing that a warm-started
local search which repairs only the seat near an existing incumbent is a practical mechanism for
keeping successive office setting plans stable, which similar to the movement-minimizing
reallocation that objective (Objective 2) follows. Muñoz et al. (2006) address ticket-to-seat
allocation for a Formula 1 Grand Prix using a region-growing heuristic and an explicit split
between mandatory and optional distribution rules, a hard/soft rule structure that independently
mirrors the constraint classification adopted in this project (Section 11.2). Sun (2020) contributes
a combinatorial model of aisle-interrupted row geometry that corroborates, from a distinct
mathematical angle, this project's treatment of the center aisle as a structural break in physical seat
adjacency rather than an ordinary seat gap. By combines a general-purpose constraint solver, a
provable optimality guarantee, and a stability-preserving reallocation mechanism in one system
that this project delivers using Google OR-Tools CP-SAT (CP-SAT Solver, n.d.; Perron et al.,
2023), a solver built on the lazy clause generation paradigm (Stuckey, 2010) that natively expresses
PJKIT's tier, pairing, and ordering rules as integer and Boolean constraints without hand-compiled
linearization.

## 2.1 Existing Seat and Space Allocation Systems
The table below listed the existing seat and space allocation systems used in event planning.
 No Existing System          Main Capability                        Limitation
 1     Manual Excel /        Allows organizers to manually          No automated allocation, no
       Spreadsheet           record participant names, seat         fairness metric, no
       Planning              numbers, groupings, and remarks.       optimization, and difficulty
                                                                    handling dynamic changes.
 2     Manual Seating        Allow organizers to manually           Highly dependent on human
       Chart / Paper-        place participants on a physical or    judgment and difficult to scale
       Based Layout          digital seating layout.                for hundreds of participants.


<!-- Page 14 -->

 No Existing System          Main Capability                            Limitation
 3    Cvent / Social         Supports event management,                 Strong in event planning and
      Tables                 event diagramming, collaboration,          visualization but limited in
                             and floor planning.                        explicit fairness-driven
                                                                        weighted constraint
                                                                        optimization.
 4    PerfectTablePlan       Supports guest details, RSVPs,             Provides useful automatic
                             preferences, automatic                     seating support, but formal
                             assignment, drag-and-drop                  fairness metrics and
                             seating, last-minute changes, and          configurable weighted
                             printed floor plans.                       constraint optimization are not
                                                                        the focus.
 5    WeddingWire            Supports drag-and-drop seating             Useful for event seating
      Seating Chart          charts, RSVP tracking, table               visualization but limited in
      Tool                   shape customization, sharing,              formal optimization and
                             printing, and exporting.                   fairness evaluation.
 6    Zola Seating           Supports table assignment, floor           Useful for basic guest seating
      Chart Tool             plan customization, guest                  planning, but limited in
                             grouping, printing, downloading,           constraint optimization,
                             and sharing.                               dynamic reallocation, and
                                                                        fairness scoring.

## 2.2 White Space Analysis
The table below lists the existing seat and space allocation system used in event planning, based
on each system vendor's publicly available product documentation and about product pages (Cvent,
n.d.; Oryx Digital Ltd., n.d.; WeddingWire, n.d.; Zola, n.d.).

                   Participant-Facing       Configurable           Controlled             Constraint-
 Existing Method
                   Seat Lookup After        Participant-Profile-   Dynamic                Based
 / System
                   Admin Allocation         Based Allocation       Reallocation           Optimization
 Manual Excel /
                   No                       No                     No                     No
 Seating Chart
                                                                   Partial editing with
 Cvent             Partial                  Partial / limited                             No
                                                                   synchronization


<!-- Page 15 -->

                                                                                     Yes, Genetic
                                          Partial, through
                                                               Partial last-minute   Algorithm-
 PerfectTablePlan No                      guest proximity
                                                               editing               based automatic
                                          preferences
                                                                                     assignment
 WeddingWire /
                    Sharable              Weak                 Manual adjustment     No
 Zola
 Proposed FYP
                    Yes                   Yes                  Yes                   Yes
 System

The white space analysis indicates that existing systems excel at visual event planning, guest list
management, manual seat arrangement, drag-and-drop seating, and printable chart generation.
When visualizing tables, chairs, or floor plans is the primary goal, these features are very helpful
to organizers. WeddingWire and Zola also facilitate the creation of floor plans, guest placement,
and the export or sharing of seating charts (WeddingWire, n.d.; Zola, n.d.).
       Additionally, comparison reveals several significant gaps. First, most tools do not support
automated allocation based on comprehensive participant profiles; the organizer is typically
responsible for managing attributes like priority, contribution level, organizational position,
attendance history, group relationship, and event-specific rules. Second, rather than using
systematic reallocation, dynamic changes like participant absence or last-minute substitute are
typically handled by manual editing. Third, configurable constraint weights receive little explicit
support, leaving organizers unable to formally adjust the relative importance of competing
allocation criteria. Fourth, most systems offer no measurable fairness metric by which to judge
whether a generated plan is balanced and defensible.
       Among the researched commercial system, PerfectTablePlan is one of the more
sophisticated, supporting automatic seating assignment and employing a genetic algorithm to
search for strong layouts once the combinatorial space outgrows exhaustive search (Oryx Digital
Ltd., n.d.). The automatic assignment does not deliver explicit fairness metrics, participant-profile-
based constraint weighting, or dynamic weighted constraint optimization as the system's central
objective. A white space therefore persists in a system that unites automated seating allocation with
configurable constraints and measurable fairness evaluation. The proposed Final Year Project
(FYP) system addresses this gap with an intelligent seating allocation service that draws on
participant profile data, predefined constraint templates, configurable soft-constraint weights, and
fairness evaluation to generate seating plans. It is, in effect, not merely a visual seating chart tool
but a decision-support system for fair, constraint-compliant allocation.


<!-- Page 16 -->

## 2.3 Constraint Modelling and Rule Conversion in Seating Allocation
The proposed system requires human-readable event seating rules to be converted into a structured
mathematical model before an optimization solver can process them, an activity known as
constraint modelling or constraint formulation. Constraint modelling translates a real-world
problem into formal components: decision variables, domains, constraints, and an objective
function (Rossi et al., 2006). In this project, the real-world problem is the assignment of event
participants to available seats under participant-profile and event-specific rules. The decision
variables represent the unknown assignment - for example, the seat assigned to a specific
participant, or the seat pair assigned to an Emperor registration; the domain of each variable is the
set of permissible seat identifiers (or valid pairs); and the constraints encode validity and
preference - each participant receives exactly one seat, each seat serves at most one occupant,
unavailable seats are excluded, Emperor pairs never straddle the center aisle, tier bands and
contribution ordering are respected, and high-priority participants occupy more suitable seats.
       Modelling matters because the problem is combinatorial: even ignoring Emperor pairing,
assigning 150 participants into the PJKIT layout's 232 assignable seats admits 232!/(232-150)!
ordered assignments, a scale at which exhaustive checking is impractical and at which nested-loop,
if-else programming becomes difficult to maintain, slow to search, and weak at arbitrating
conflicting preferences. The proposed system distinguishes hard constraints - mandatory rules a
valid plan must satisfy, such as one allocation unit per participant, at most one occupant per seat,
unavailable-seat exclusion, valid seat range, status eligibility, side-of-hall accessibility placement,
tier-band placement (ordered Emperor → Merit → Bodhi, with shared boundary rows), valid
Emperor pairing, and within-tier contribution ordering - from soft constraints - preferences
satisfied as far as possible, such as priority-score alignment, activeness score, category-to-zone
suitability, and movement minimization. This distinction follows valued constraint satisfaction and
constraint optimization approaches, in which preferences, costs, and priorities are represented and
optimized rather than treated as strict pass-or-fail conditions (Schiex et al., 1995). A weighted-sum
aggregation of the soft-constraint penalties is adopted (rather than lexicographic or max-min
aggregation) because PJKIT's rules express graded trade-offs between preferences of different
kinds, the relative weights are an organizer-configurable input validated with stakeholders, and a
single scalar objective is required by the solver; the weight-calibration procedure is part of the
requirement-validation cycle described in Section 3.5.


<!-- Page 17 -->

       Three modelling principles from the constraint-programming literature are directly
relevant. Linearization, including Boolean linearization, expresses complex logical conditions
using integer or Boolean variables - essential for CP-SAT, which requires all constraints and
objective coefficients to be integers (CP-SAT Solver, n.d.); accordingly, all penalty values and
weights in this project are defined on integer scales, and any fractional cost is scaled to an integer
before model construction. Reification links the truth value of a logical condition to a Boolean
variable; for example, a Boolean indicator represents whether a participant has moved from their
previous seat after reallocation, enabling movement to be counted and penalized in the objective.
Channeling links different layers of decision variables - for instance, connecting a participant's
assigned seat identifier to that seat's row, physical position, zone, and priority rank; Google's OR-
Tools documentation describes channeling constraints as the standard mechanism for representing
such relationships, commonly implemented through implications or half-reified linear constraints
(CP-SAT Solver, n.d.). A fourth, domain-specific modelling decision follows from the venue
geometry: physical seat position and seat priority rank are distinct attributes and must never be
conflated - adjacency and aisle rules operate on physical position, while preference alignment
operates on priority rank - a separation whose mathematical basis is the treatment of aisles as
structural breaks in row geometry (Sun, 2020).

## 2.4 Comparison of Seating Allocation Methods
Based on the research study, multiple algorithmic approaches could be implemented for the
creation of the seating allocation solver function. Table below compares the reviewed seating
allocation method from previous studies.
     Method        How It Works               Strength                      Limitation
 Greedy priority   Participants are sorted by More       rule-aware   than Early locally good decisions
      based        priority and assigned the random or first come-first- can       force     poor     later
                   best available seat one by served.                       assignments;     weak     with
                   one.                                                     competing constraints.
     Genetic       Evolves a population of Flexible for large search Typically,            cannot    prove
 Algorithm (GA)    seating     plans    via spaces        and      complex mathematical       optimality;
                   selection, crossover, and scoring; used in seating requires             tuning;      no
                   mutation                   tools         such        as falsifiable status reporting.


<!-- Page 18 -->

                                                   PerfectTablePlan          (Oryx
                                                   Digital Ltd., n.d.).
  Integer Linear   Represents the problem Mature exact optimization Logical                      and     conditional
  Programming /    with linear equations, with strong solvers when the rules (pairing, adjacency, if-
  Mixed-Integer    integer variables, and model is linear (Williams, then eligibility) must be
  Programming      objective function.             2013); used for the seating manually              compiled     into
    (ILP/MIP)                                      sub-problems of Ipsen et al. linear form, typically via
                                                   (2026).                            big-M constructions that are
                                                                                      error-prone      and   weaken
                                                                                      relaxations;      no      native
                                                                                      reification or channeling;
                                                                                      both   ILP      and    CP-SAT
                                                                                      require integer modelling,
                                                                                      so this cost is not avoided by
                                                                                      CP-SAT's alternative.
 Constraint        Represents the problem Native              reification      and Requires careful integer-
 Programming - with integer variables, channeling for if-then rules; based modelling; optimality
 Satisfiability    native              logical no        big-M      compilation; is claimed only when status
 (CP-SAT)          constraints,       Boolean proven          optimality      with is OPTIMAL
                   indicators,      and       an explicit     status      reporting
                   objective; solves via lazy (OPTIMAL / FEASIBLE /
                   clause generation with INFEASIBLE                              /
                   CDCL        learning,     LP- MODEL_INVALID                    /
                   relaxation bounds, and UNKNOWN); production-
                   portfolio               search grade and free
                   (Stuckey, 2010; Perron
                   & Didier, 2023).

CP-SAT, implemented through Google OR-Tools, is selected because the proposed system must
do more than assign seats: it must enforce hard structural rules (two-seat pairs, aisle breaks, tier
bands, ordering), optimize weighted preferences, preserve reallocation stability, and report
measurable allocation quality. Relative to ILP/MIP - the closest exact alternative - CP-SAT
expresses PJKIT's conditional and structural rules natively through reification and channeling
rather than through hand-compiled big-M linearizations, while retaining exactness; its lazy-clause-


<!-- Page 19 -->

generation architecture with conflict learning, LP bounding, and parallel portfolio search is
specifically designed to prune search spaces of this problem's scale (Perron & Didier, 2023;
Stuckey, 2010). Relative to the published seating 5 / 20 heuristics - region growing and GA -
CP-SAT provides what neither can: a provable optimality claim and an explicit, falsifiable solver
status that the system surfaces as part of allocation quality, under the project's standing rule that a
solution is never reported optimal unless CP-SAT returns OPTIMAL (Google, n.d.-a). The greedy
method is retained as an evaluation baseline, and the genetic algorithm is noted as a literature
benchmark and possible future alternative.

## 2.5 Literature Synthesis Against Problem Statements
By synthesizing the reviewed systems and literature against the problem statements, it can confirm
that the project's positioning in the correct area. Regarding Problem Statement 1, existing
commercial systems provide varying levels of guest management and visual seating, but none
supplies a configurable rule layer over PJKIT's domain attributes, and the academic literature
supplies exact methods only in bespoke, non-configurable forms (Ipsen et al., 2026) or heuristic
methods without guarantees (Muñoz et al., 2005); the proposed system addresses this with
configurable hard and weighted soft constraints solved by a general-purpose exact solver, making
allocation consistent, repeatable, and explainable. Regarding Problem Statement 2, manual edits,
last-minute changes, and synchronization features do not constitute controlled dynamic
reallocation; in this project, reallocation means incrementally repairing the published plan after a
data change - modifying only the affected assignments and a bounded surrounding area, with
particular emphasis on ad-hoc participants and on-event-day changes - storing the repaired result
as a new version, penalizing movement with formal precedent in switching-cost constraint
optimization (Hoang, 2022), and publishing only after review, thereby delivering change
optimization rather than mere change handling. Regarding Problem Statement 3, printed lists and
organizer-driven sharing leave a communication gap; the proposed participant-facing lookup
provides an authenticated route through which participants view the latest published seat number
and seating map, directly addressing fragmented seating communication.


<!-- Page 20 -->

<!-- Extracted image(s) from PDF page 20: -->
![Extracted image from page 20](draft_interim_report_extracted_assets/page_20_image_01.png)

# 3. Methodology
## 3.1 Software Development Methodology: Agile SCRUM


**Figure 3 Agile SCRUM Two-Week Sprint with Netizen eXperience**

This final year's project implemented the Agile software development methodology, specifically
the SCRUM framework (Schwaber & Sutherland, 2020) together with the Netizen eXperience
assigned industry supervisor, Mr. Cheah Poh Xiang. Based on the Figure 8 above, each sprint in
Agile SCRUM framework consists of four SCRUM ceremonies as defined in the official SCRUM
Guide (Schwaber & Sutherland, 2020), which including the Sprint Planning for backlog
brainstorming and task effort estimation, followed by Daily Standup Meeting for ongoing progress
synchronization, and closed by a Sprint Review to demonstrate the developed increment of the
intelligent seating allocation system, and Sprint Retrospective that discover       the possible
improvement steps derived from goods and bad practices observed during a sprint. All the
ceremonies in Final Year Project 1 (FYP1) phase are held on Wednesday with the industry
supervisor and the developer that are currently maintaining the Netizen eXperience Event
Management platform for PJKIT. The project is implementing a two-week sprint setting, which
Sprint Planning and the Stand-up meeting run weekly from 10:00am to 10:15am to set and update
the sprint backlog status, while the more important Sprint Review and Retrospective run biweekly
from 10:30am to 11:00am to demonstrate the increment developed in the sprint and reflect on the
sprint.


<!-- Page 21 -->

<!-- Extracted image(s) from PDF page 21: -->
![Extracted image from page 21](draft_interim_report_extracted_assets/page_21_image_01.png)

## 3.2 Software Design and Architecture
### 3.2.1 Use Case Diagram
The use-case diagram below follows Unified Modelling Language use case notation (Object
Management Group [OMG], 2017), used to identify the Event Administrator and Event Participant
as the primary actors of the intelligent seating allocation system and a series of what are the
activities that could perform within the system boundary.


**Figure 4 System Use Case Diagram of the Intelligent Seating Allocation System**


<!-- Page 22 -->

#### Primary use case description - Generate Seating Plan

 Field               Description
 Use Case            Generate Seating Plan

 Primary Actor       Event Administrator

 Supporting Actor    Seat Allocation Solver Function

 Goal Trace          G1 (G1.1-G1.3)

 Precondition        The system should receive selected participant data, venue seating layout,
                     and constraint configuration.

 Trigger             Organizer clicks Generate Plan in the admin module.

# 1. Platform packages participants, layout, configuration, and optional
                     previous allocation into a JSON payload.
# 2. Engine validates schema, derives the demand-driven tier bands, and
                     checks band capacity.
# 3. Engine builds the integer constraint model over eligible combinations
                     only.
 Main Success        4. CP-SAT solver function solves the seating allocation within the
 Scenario            configured time budget.
# 5. Engine extracts assignments and penalty breakdown.
# 6. Independent validator rechecks all the hard constraints and the
                     reconstructed objective.
# 7. Result is stored as a new seating plan version.
# 8. Organizer reviews the version and quality indicators.

                     2a. Invalid payload return structured INVALID_INPUT error.
                     2b. Capacity exceeded return a structured infeasibility explanation
                     message without invoking the solver.
                     4a. INFEASIBLE / UNKNOWN status and conflict hints returned, the
 Extensions          organizer relaxes rules or adjusts seat range.
                     4b. FEASIBLE with proven optimum required reported as
                     OPTIMAL_NOT_PROVEN
                     6a. Independent validation fails lead to result rejected, failure reported.

                     A reviewable plan version exists; nothing is published without explicit
 Postcondition
                     approval (UC6).


<!-- Page 23 -->

<!-- Extracted image(s) from PDF page 23: -->
![Extracted image from page 23](draft_interim_report_extracted_assets/page_23_image_01.png)

### 3.2.2 System Flowchart


**Figure 5 System Flowchart for event administrator user flow**


<!-- Page 24 -->

<!-- Extracted image(s) from PDF page 24: -->
![Extracted image from page 24](draft_interim_report_extracted_assets/page_24_image_01.png)

### 3.2.3 System State Machine Diagram


**Figure 6 System State Machine Diagram for Seating Allocation Engine**

The system state machine diagram above, drawn using UML state machine notation (OMG, 2017),
demonstrated the life of one seating allocation session in the seat allocation solver function. First,
the serverless aspect of the engine is illustrated in the entry transitions, which a first invocation of
the solver function requires to transition into a ColdStart state before starting to solve the seating
allocation. The Solving State fork into two (2) different states, either ResultReady state when the


<!-- Page 25 -->

solver returns the status of OPTIMAL or FEASIBLE and generates a seating map solution, or the
Failed state when the returned solver status is INFEASIBLE, INVALID or TIEMOUT. Also,
moving the ResultReady to the UnderReview state, the system state can branch into two (2)
different state, which either back to the Solving state when the event administrator choose to
regenerate the seating plan again, or forward to the Published state when the event administrator
approved the result and published the seating map to participant.

       The most important part to be observed from the state machine diagram above is the seating
map reallocation looping, where a Published seating plan can be Reloaded and fed back into the
Solving state as reference, so that the incremental repair of the seating plan could minimize the
movement of the participant. The session thus only will be terminated from the Published state,
when the event administrator confirmed that the latest published seating plan is in the single stagble
resting state of the system.


<!-- Page 26 -->

<!-- Extracted image(s) from PDF page 26: -->
![Extracted image from page 26](draft_interim_report_extracted_assets/page_26_image_01.png)

### 3.2.4 System Architecture Diagram


**Figure 7 System Architecture Diagram for Proposed Intelligent Seating Allocation System**

The proposed intelligent seating allocation system in this project adopts a four-layer architecture
model that consists of the layered architecture pattern commonly used to separate presentation,
application, compute, and data concerns in distributed systems. The architecture model separates
the actors who use the system from the internal or external software that they interact with, a
computation layer that focuses on generating the seating plan at serverless compute side, and the
storage that persists the required metadata for event, participant, and seating allocation result.
       Based on Figure 9 above, the first layer of the architecture model is the Users layer that
holds the two primary actors of the system, which are the Event Administrator and the Event
Participant. The second layer is Application Layer, which is the Netizen eXperience Event
Management Platform, containing the Admin Seating Allocation Dashboard, a Next.js server
component that will call the server actions that will interact with the deployed AWS resources via
AWS SDK. The Application Layer also contains a Participant Seat Lookup Interface that will fetch


<!-- Page 27 -->

and display the latest participant seating details on the latest published seating map retrieved from
DynamoDB. The Compute Layer is focused on the AWS serverless, where an AWS Lambda
function hosts the core seating allocation engine and its embedded Google OR-Tools CP-SAT
solver function (What is AWS Lambda? - AWS Lambda., n.d.; CP-SAT Solver, n.d.). The Data
Layer is AWS storage, comprising Amazon DynamoDB to store event, participant, and allocation
metadata, along with the latest-approved seat references. Amazon S3 is also being deployed to
Data Layer to store the versioned seating-plan result JSON for seating plan generation record
traceability and referencing the latest seating plan. The implementation of the layered architecture
model ensures that each tier depends only on the one above it, so the application, the solver
function, and the storage can be scaled and modified independently.
         The primary flow begins with the Event Administrator. From the Admin Seating Allocation
Dashboard, the organizer optionally configures the constraints and selects the range of participant
data to be involved in the event seating allocation. Then, the Next.js server component transforms
this data into a structure JSON file that will be used to invokes the Lambda function in the Compute
Layer through the AWS SDK (Invoke - AWS Lambda., n.d.). The seating allocation engine builds
and solves the model with CP-SAT and returns the optimal/feasible solution together with its solver
status inside the Lambda function. The resulting seating-plan JSON will then send back as
response to the server component that invoke the solver function, which triggers server actions to
store the event and participant metadata in DynamoDB and the versioned seating-plan document
in S3.
         When a change occurs after publication, the same path is used for reallocation where the
server component re-invokes the Lambda function with the updated payload and the previous
seating plan, so that the engine will perform repairs and minor adjustment on existing seating plan
rather than regenerates the whole seating plan with all the same data payload. The Event Participant
never reaches the compute tier, the Participant Seat Lookup Interface requests participant-specific
seating details from the server component, which serves the latest published seating details read
from DynamoDB, and the participant could view their seat. The takeaway is that computation is
triggered only by the administrator and runs on demand, while the participant's path is a short,
read-only lookup of already-approved data.


<!-- Page 28 -->

<!-- Extracted image(s) from PDF page 28: -->
![Extracted image from page 28](draft_interim_report_extracted_assets/page_28_image_01.png)

### 3.2.5 Class Diagram


**Figure 8 Class Diagram of the Intelligent Seating Allocation System**

The data modeling structure started from the Event class as the root, which an event may be
registered by many Participants, and each event will only use one single venue layout. Every event
is configured by one ConstraintConfig class, which consists of HardConstraint and SoftConstraint
definition. Each event may produce many AllocationPlanVersion that represent the seat assignment
results from the generation operation. There is also a self-reference relationship on the
AllocationPlanVersion class, which lets the reallocation compare and measure the movement
against the prior published seating plan. Each Seat class carries the physicalPosition and
priorityRank as separated attributes to separate the aisle logic from the preference logic. The solver
function engine-side SolverEngine and ConstraintModelBuilder are cleanly separated from the


<!-- Page 29 -->

<!-- Extracted image(s) from PDF page 29: -->
![Extracted image from page 29](draft_interim_report_extracted_assets/page_29_image_01.png)

domain and artifact classes by implementing the Builder design pattern, so that the model's builder
operations are concrete realization of the constraint model, but not a property of the domain data.

### 3.2.6 Swimlane Diagram for Generate Seating Plan Use Case


**Figure 9 Activity Diagram of the Generate Seating Plan use case in the propsoed system**


<!-- Page 30 -->

## 3.3 Methods and Technologies Adopted
 Method / Technology                    Role in the Project

 Constraint Programming (CP) with       Core method used to model event seating rules as a
 hard and weighed soft constraints      Constraint Optimization Problem.
                                        The library used to execute the constraint model and
 Google OR-Tools CP-SAT solver          report explicit solver statuses (optimal, feasible,
                                        infeasible, model invalid, unknown).
                                        Programming language used for the implementation of
 Python 3                               the seat allocation solver function.
                                        An on demand serverless deployment of the engine,
 AWS Lambda                             invoked with an explicit solver time budget.

 AWS SDK (from the Next.js              Invocation channel for AWS infrastructure with JSON
 service component)                     payloads and results.
                                        Existing Netizen eXperience Event Management
                                        platform that is currently hosting the admin module and
 Next.js / React (TypeScript)           integration with a participant lookup route as the outcome
                                        of the project.
                             Persistence of allocation metadata and versioned plan
 Amazon DynamoDB & Amazon S3 JSON respectively.

                                        Infrastructure-as-code framework used to provision the
 SST Framework
                                        AWS resources.
                                        Tracking all the backlog and task for the development of
 GitHub Issues & Projects               intelligent allocation system in the Netizen eXperience
                                        repository.

Google OR-Tools CP-SAT solver is selected as the solving engine in this project for the seating
allocation problem in Section 2.4 because it accepts integer decision variables, Boolean indicators,
and conditional constraints through reification and channeling, and reports explicit solver statuses
that this project surfaces as part of allocation quality (CP-SAT Solver, n.d.). This selection is
further grounded in the primary technical literature describing CP-SAT's lazy-clause-generation
architecture, which combines SAT-style conflict-driven clause learning (Stuckey, 2010) with
linear-programming relaxation bounds and portfolio parallel search (Perron et al., 2023) an
architecture specifically designed to prune search spaces of this project's scale while still proving
optimality, a guarantee bespoke greedy or metaheuristic approaches cannot offer.


<!-- Page 31 -->

<!-- Extracted image(s) from PDF page 31: -->
![Extracted image from page 31](draft_interim_report_extracted_assets/page_31_image_01.png)
![Extracted image from page 31](draft_interim_report_extracted_assets/page_31_image_02.jpeg)
![Extracted image from page 31](draft_interim_report_extracted_assets/page_31_image_03.jpeg)

## 3.4 Seating Allocation Optimization Lifecycle


Write the explantion


## 3.5 Preliminary Works
### 3.5.1 Interview and Joint Application Development Workshop


A site visit to the PJKIT was conducted together with the industry supervisor from Netizen
eXperience on 26th June 2026. The sire visit combined a semi-structured interview with PJKIT
stakeholders with the elicitation questionnaires in Appendix A, and direct observation of the event
venue physically. At the same day, a joint application development (JAD) workshop is carried out
between the FYP student, Industry Supervisor - Mr. Cheah Poh Xiang and three (3) representatives
including the head of administrator that handle on event seating allocation from PJKIT side to
brainstorm, discuss and refine the requirement for the proposed intelligent seating allocation
system. The result of this elicitation activity is located at Appendix B.


<!-- Page 32 -->

### 3.5.2 Preliminary Findings from Elicitation
The validated constraint and scenario base that underpin the entire requirement set were obtained
via the elicitation processes (Section 9):

 Preliminary Finding            Description
 Validated event participant PJKIT's event averagely includes 100 - 200 participant per event,
 scale and venue layout         and the participants is allocating in a 16 rows × 16 seats venue
                                layout which in total of 256 numbered seats, where 232 assignable
                                after 24-seat is blocked by the building structure in the center of
                                the hall. Participants are arranged in a concert-style with a
                                numbered front section and a free-seating section at the back of
                                the venue.
 Existing      workflow    for PJKIT currently prepares all the seating maps for every event
 generating seating plan is manually by inserting participant name one-by-one into the
 conducted      manually   by predefined seating chart in an excel sheet. The seating map
 event administrator and generation procedure is carried out by a team of fewer than five
 volunteers.                    senior volunteers who must personally know the participants and
                                understand the significance of each placement. The current
                                workflow takes up until two (2) weeks before the event day.
 Contribution tier structure Participants are first categorized by their contribution tier which
 as the first-order rule for either Emperor, Merit, or Bodhi tier. The seating allocation
 seating allocation             ordered as the last row of Emperor tier should precede the first row
                                of the Merit tier, and the last row of Merit tier should precede the
                                first row of Bodhi tier. The seating row could be shred between
                                two different tiers to avoid empty seats in the numbered front row.
 Generic tools in the market The specific rules of PJKIT seating allocation for participants
 cannot be used to solve the increased the necessity to implement a customized solution that
 specific seating allocation could generate a seating map by satisfying all the structural rules
 problem in PJKIT               such as contribution tiering priority, side-of-hall placement of
                                participants who need accessible seats and within-tier contribution
                                ordering.


<!-- Page 33 -->

 Dynamic participant data PJKIT will close the registration of the event on a set date, walk-
 change ad hoc event for in and late registration are uncommon scenario to occur in PJKIT
 PJKIT events                   event. However, the primary ad hoc event case for PJKIT is the
                                absence of a registered participant, sometimes also with
                                replacement participant to take the vacated seat on the event day.
                                In every case the stakeholder expectation is that a published plan
                                is repaired with minimal disruption instead of regenerating the
                                whole seating map again.
 Constraint     programming Every elicited structural rule for event seating allocation in PJKIT
 with CP-SAT is suitable for are expressible as a pure-integer model natively supported by CP-
 creating the solver function SAT's lazy-clause-generation architecture (Perron et al., 2023;
 to solve PJKIT seating Stuckey, 2010), which solves the seating allocation problem and
 allocation business case       generate a seating plan result within the configured time budget,
                                the independently implemented validator confirms zero hard-
                                constraint violations and reconstructs the reported objective value
                                exactly, and repeated runs reproduce the identical canonical plan

### 3.5.3 Constraint Listing Output
 Constraint Ref    Rule (plain language)                                             Classification
                   Each participant is assigned exactly one allocation unit (one
 C1                                                                                      Hard
                   seat; one valid seat pair for Emperor registrations).
                   Each seat is occupied by at most one participant (both seats of
 C2                                                                                      Hard
                   an assigned Emperor pair count as occupied).
 C3                Blocked or unavailable seats must not be assigned.                    Hard
                   Assignments must fall within the valid seat range of the event
 C4                                                                                      Hard
                   layout.
 C5                Only participants of eligible status may be seated.                   Hard
                   Participants with higher contribution/priority scores should          Soft
 C6
                   receive seats of higher priority rank.                             (weighted)
                   Participants with higher activeness scores should be favored          Soft
 C7
                   within their tier.                                                 (weighted)


<!-- Page 34 -->

                 Participants should be seated in zones suitable for their             Soft
 C8
                 category (within-tier suitability preference).                     (weighted)
                 Upon reallocation, unaffected participants retain their
                 previous seats by default; unavoidable movement is
                                                                                       Soft
 C9              minimized in number and then in distance (movement
                                                                                    (weighted)
                 minimization; penalty is zero when no previous allocation
                 exists).
                 An Emperor registration occupies exactly two adjacent seats
                 forming one of the venue's valid within-row pairs; when no
 C10                                                                                  Hard
                 adjacent guest name is provided, both seats display the
                 primary participant's name.
                 No Emperor pair may straddle the center aisle: positions 8 and
 C11             9 never form a pair. Physical adjacency is determined by             Hard
                 physical seat position, never by priority rank.
                 Tier-band placement: tiers occupy contiguous, demand-
                 derived row bands ordered Emperor → Merit → Bodhi from
                 the front of the hall; a boundary row may be shared between
 C12             two adjacent tiers (when one tier ends partway along a row,          Hard
                 the next continues in it) so the numbered section packs with
                 no empty seat; band capacity (with Emperor units counting
                 two seats) is validated before model construction.
                 Within each tier, a participant with a higher contribution score
 C13             is never seated in a later row than a participant with a lower       Hard
                 score.
                 Among plans of equal weighted penalty, a deterministic tie-        Modelling
 C14             breaking rule selects a canonical plan; the tie-break term is         rule
                 scaled so it can never override any weighted penalty.              (objective)
                 Front-to-back packing where the numbered section fills
 C15             seating from front to back with no empty seat (the remaining         Hard
                 assignable rows form the free-seating section).


<!-- Page 35 -->

<!-- Extracted image(s) from PDF page 35: -->
![Extracted image from page 35](draft_interim_report_extracted_assets/page_35_image_01.png)

                 Centre-out fill where each side of a row fills outward from the
 C16             center aisle, so no gap appears between the aisle and an outer    Hard
                 occupied seat.
                 A participant who requires an accessible seat is placed at a
 C17             side/edge seat of the hall (for an Emperor unit, a pair at the    Hard
                 side), for ease of access.


## 3.6 Proposed System Interfaces
### 3.6.1 Event Administrator Seating Allocation Dashboard


**Figure 3 Event Administrator Seating Allocation Dashboard**


<!-- Page 36 -->

<!-- Extracted image(s) from PDF page 36: -->
![Extracted image from page 36](draft_interim_report_extracted_assets/page_36_image_01.png)
![Extracted image from page 36](draft_interim_report_extracted_assets/page_36_image_02.png)

### 3.6.2 Event Participant Seat Lookup Portal


**Figure 4 Event Participant Seat Lookup Interface**

## 3.7 Project Timeline
### 3.7.1 FYP 1 Gantt Chart


<!-- Page 37 -->

<!-- Extracted image(s) from PDF page 37: -->
![Extracted image from page 37](draft_interim_report_extracted_assets/page_37_image_01.png)

### 3.7.2 FYP 2 Gantt Chart


The 28-week schedule for the whole final year project distribute evenly for FYP1 (Weeks 1-14)
and for FYP2 (Weeks 15-28), which maps to the time frame of June 2026 to December 2026. Each
sprint carries a goal and ends in a demonstrable increment reviewed at the biweekly demo, and
requirements are refined continuously across sprints. This makes the milestone plan consistent
with the Agile SCRUM methodology, while the two academic checkpoints FYP1 submission of
Interim Report, FYP2 Completion of VIVA and submission of Dissertation remain as fixed
milestones.


<!-- Page 38 -->

# 4. Conclusion
## 4.1 Summary of Project Progress
This report has presented the planning-phase work of a Final Year Project that addresses a genuine
and recurring operational problem which the manual seating allocation for large-scale assembly
events. The background established that seating allocation is a multi-criteria combinatorial
problem whose solution space grows explosively with participant numbers, and that the case-study
organization, PJ Kwan Inn Teng, currently manages events of 100 - 200 participants in a 256-seat
venue (232 assignable after its structural blocked center block) governed by demand-derived tier
bands, two-seat Emperor allocation units, an aisle that breaks adjacency, and contribution-ordering
rules - using spreadsheets, printed charts, and PDF listings. Manual allocation is slow and
inconsistent between allocators and cannot be objectively justified against the community's own
priority rules; late data changes and ad-hoc registrations force disruptive, error-prone rework of
nearly finished plans; and participants queue at the venue to retrieve seats from printed lists that
may already be outdated. Without the research and development undertaken in this project, these
consequences persist and worsen as event attendance grows.

       The literature review demonstrated that neither commercial tooling (Cvent, n.d.; Oryx
Digital Ltd., n.d.; WeddingWire, n.d.; Zola, n.d.) nor the published seating-allocation literature
(Ipsen et al., 2026; Muñoz et al., 2006; Sun, 2020) offers this combination which is a declaratively
configurable, status-reporting, and stability-aware seating allocation engine. The contribution of
this project is a to develop a configurable, constraint-based seating allocation system whose core
is a solver engine that models real event rules formalized in Section 11.2 as a Constraint
Optimization Problem that solved by Google OR-Tools CP-SAT solver and deployed as a Python
script on AWS Lambda function that invoked with JSON payloads directed from the Netizen
eXperience event management platform. The system provides organizer-controlled generation,
versioned review and publishing, configurable rules over PJKIT's domain attributes, controlled
dynamic reallocation that incrementally repairs the published plan for ad-hoc participants while
leaving unaffected participants in their initial assigned seat. This project also aimed to develop
participant-facing lookup interface for PJKIT participants to enable them to perform self-checking
on the latest published seat from event administrator before or during the event day.


<!-- Page 39 -->

## 4.2 Future Work Recommendation
Next module or things to do in FYP2….


<!-- Page 40 -->

# 5. References
CP-SAT Solver. (n.d.). Google for Developers.

Cvent. (n.d.). Event diagramming and seating. Retrieved June 2026,
       from https://www.cvent.com

Ipsen, A., Cashmore, M., Fielding, K., Marchesotti, N., Zehtabi, P., Magazzeni, D., & Veloso, M.
       (2026). Beyond manual planning: seating allocation for large organizations. Open MIND.
       https://doi.org/10.48550/arxiv.2602.05875

Invoke - AWS Lambda. (n.d.). https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html

Perron, L., Didier, F., & Gay, S. (2023). The CP-SAT-LP solver (Invited talk). In R. H. C. Yap
       (Ed.), 29th International Conference on Principles and Practice of Constraint
       Programming (CP 2023) (Leibniz International Proceedings in Informatics, Vol. 280, pp.
       3:1-3:2). Schloss Dagstuhl - Leibniz-Zentrum für Informatik.
       https://doi.org/10.4230/LIPIcs.CP.2023.3

Peter J. Stuckey. 2010. Lazy clause generation: combining the power of SAT and CP (and MIP?)
       solving. In Proceedings of the 7th international conference on Integration of AI and OR
       Techniques in Constraint Programming for Combinatorial Optimization Problems
       (CPAIOR'10). Springer-Verlag, Berlin, Heidelberg, 5-9. https://doi.org/10.1007/978-3-
       642-13520-0_3

Rossi, F., Van Beek, P., & Walsh, T. (2006). Handbook of Constraint Programming (Foundations
       of Artificial Intelligence). In Elsevier eBooks. http://dl.acm.org/citation.cfm?id=1207782

Muñoz Solà, Víctor & Montaner, Miquel & Esteva, Peplluis. (2006). Seat allocation for massive
       events based on region growing techniques. 179-186.

Oryx Digital Ltd. (n.d.). Using a genetic algorithm for table seating. PerfectTablePlan.
       c https://www.perfecttableplan.com

Pohl, K. & Rupp, C. (2016). Requirements engineering fundamentals: a study guide for the
       certified professional for requirements engineering exam-foundation level-IREB
       compliant. Rocky Nook, Inc.


<!-- Page 41 -->

What is AWS Lambda? - AWS Lambda. (n.d.).
       https://docs.aws.amazon.com/lambda/latest/dg/welcome.html

Schwaber, K. and Sutherland, J. (2020) The Scrum Guide: The Definitive Guide to Scrum: The
       Rules of the Game. Scrum.org & Scrum Inc.

Sun, S. (2020). Mathematical model of seat arrangement in large gymnasium. IOP Conference
       Series Materials Science and Engineering, 806(1), 012013. https://doi.org/10.1088/1757-
       899x/806/1/012013

WeddingWire. (n.d.). Wedding seating chart tool. https://www.weddingwire.com/wedding-
       planning/wedding-seating-tables.html

Zola. (n.d.). Wedding seating chart: Seat all your guests in minutes. Retrieved June 2026,
       https://www.zola.com/wedding-planning/seating-chart


<!-- Page 42 -->

# 6. Appendices
## Appendix A: Elicitation Questionnaires
### Part A: Event scale and context
# 1. How many participants typically attend PJKIT annual assembly, and how does number of
 participants vary between events in PJKIT?
# 2. How many events per year require a formal seating plan, and are the rules the same across
 them?
# 3. How long before the event does seat preparation currently start (total days/week needed to
 generate a seating plan for each event), and how many PJKIT's human forces (staff + volunteer)
 are involved?
### Part B: Venue and layout structure
# 4. How is the venue physically layout look like? How many rows in total, how many seats are
 allowed per row?
# 5. Are there seats that must never be assigned (blocked, reserved, equipment, safety)?
# 6. Which seats do you consider the "best" seats, and what makes one seat better than another
 (row, closeness to the center, closeness to the front stage)?
# 7. Are there seats designated or preferred for participants with mobility difficulties or
 wheelchairs?
### Part C: Tiering (the first-order allocation factor)
# 8. What is the first factor that decides where a participant will be seated - contribution tiering,
 contribution amount, participant role (normal public community, staff from PJKIT, monk/sifu
 from PJKIT, volunteer), seniority, or something else?
# 9. How are the contribution tiers defined, and what are the boundaries between them such as
 contribution amount thresholds?
# 10. Are the number of rows assigned to each contribution tier fixed for every event in PJKIT, or
 does the number of rows depend on how many people register in each tier? In what order are
 the tiers seated from the front of the hall, and can a tier's rows ever be shared with the next tier?
# 11. Do any registrations occupy more than one seat? If so, must the two seats be adjacent, and
 may they be split across an aisle?


<!-- Page 43 -->

### Part D: Ordering, filling, and special placement within the same tier
# 12. Within the same tier, what decides who sits in front of whom - exact contribution amount,
 activeness or participation history for event in PJKIT, seniority, or registration order?
# 13. If two participants have identical standing, how do you break the tie today?
# 14. When a tier's rows are not completely full, where do the empty seats end up - the back
 rows of the tier, the outer edges of rows, or spread evenly? Do you fill each row outward from
 the center aisle?
# 15. Are there participant categories with special placement expectations (monks, elderly
 participants, guests of honor), or participants who require an accessible seat?


### Part E: Relative importance of the soft factors (weighting)
# 16. Among the factors just mentioned - contribution-to-seat matching, activeness, category-to-
 zone suitability - which is the most important to satisfy when they conflict?
# 17. Could you rank these factors, or say which factor you would sacrifice first if not all can be
 satisfied?
# 18. Would you want the ability to change these priorities per event, and who should be allowed
 to change them?


### Part F: Ad-hoc events and dynamic changes
# 19. What last-minute changes have you experienced in past events (withdrawals, substitutions,
 walk-in registrations), and how frequently do they happen on the event day itself?
# 20. When a change happens after the plan is finalized, how much of the existing plan are you
 willing to change and which participants must not be moved?
# 21. How is a revised plan being prepared with the current workflow is the mentioned ad hoc
 event above what happens, and what problems has that caused the event?
# 22. Who has the authority to approve or revise the seating plan before it is announced to
 participants?


<!-- Page 44 -->

## Appendix B: Interview Result and Finding
 Ref   Elicited Response for the Elicitation Questionnaires
       Exact attendance figures are not retained, but attendance across events in the past two
 A1
       years has consistently fallen within the 100-200 participant range.
       PJKIT holds one to two events per year that require a formal seating plan. The seating
 A2    rules are largely stable across events; only the preferred (soft) constraints vary between
       events.
       Seating preparation begins only about two weeks before the event and is carried out by
       a team of fewer than five senior volunteers who must personally know the participants
 A3
       and understand the significance of each placement; the task cannot be delegated to
       general staff.
       The hall comprises approximately sixteen rows of about sixteen seats, arranged concert
 B4    style, which a numbered seating section toward the front and a free-seating section
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
# 1. Emperor tier required for participant to contribute at least RM5000 contribution
 C9    amount in an event.
# 2. Merit tier required participants to contribute at least RM3000 contribution amount in
       an event.
# 3. Bodhi tier required participants to contribute at least RM2000 contribution amount in
       an event.
       The number of rows for each contribution tier occupies is not fixed. It depends on the
 C10
       tier's registration count, so a larger Emperor turnout extends further toward the front.


<!-- Page 45 -->

       Tiers are seated in the order Emperor → Merit → Bodhi from the front, and a row may
       be shared between two tiers when one tier's registrations end partway along a row, the
       next tier continues in the same row as to fill up the whole row.
       A registration normally occupies two adjacent seats by a married couple, which almost
 C11   always carry the same name. Registrations larger than two seats are extremely rare and
       are treated as exceptions.
       Within a tier, order is governed first by contribution amount; the remaining factors such
 D12   as seniority and previous event attendance are combined under weightings that have not
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
 E16   participants more likely to complain. For planning, the model is directed to focus on
       contribution-to-seat matching and on participant activeness in previous PJKIT events.
 E17   A fixed ranking of the soft factors is not possible because the trade-off is situational.
       The weightings are not expected to change often, but the event administrator may adjust
 E18
       the emphasis of rules per event to loosen or tighten a given aspect.
       Walk-in or late registrations are uncommon because registration closes on a set date. The
 F19   change that does occur is the absence of a registered participant, sometimes with a
       replacement taking the vacated seat.
       The registration will close after a certain time, but participant absence can still occur
 F20   after finalization of the seating map generation. When the scenario happens, disruption
       to already-assigned participants must be kept minimal.
       When such a change occurs, the seating map is going to be revised to minimize the effect
 F21
       on already-assigned participants and avoid confusion at the venue.


<!-- Page 46 -->

       A plan or a revision is approved by the senior-volunteer working team together with the
 F22
       event administrator (sifu) before it is announced to participants.
