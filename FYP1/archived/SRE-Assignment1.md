<!-- Page 1 -->

# UNIVERSITI TEKNOLOGI PETRONAS

## Department of Computing



### TFB3413/TEB3413: Software Requirement Engineering
### Assignment 1 Report



## Intelligent Automated Seating Allocation for Large-Scale Assemblies Using Dynamic Weighted Constraint Optimization to Maximize Allocation Fairness



**Lecturer: Ts. Dr. Shuib bin Basri**



    Name                    Student ID                     Email

    Darius Lee Shin              22003269            darius_22003269@utp.edu.my

---

<!-- Page 2 -->

# Table of Contents
# 1.0 Project Background and Problem Statement ............................................................................ 4

## 1.1 Project Background ............................................................................................................... 4

## 1.2 Current Situation and Existing Process................................................................................. 5

## 1.3 Problem Statement ................................................................................................................ 6

## 1.4 Overview of Proposed Solution ............................................................................................ 6

# 2.0 System Vision ........................................................................................................................... 7

## 2.1 Vision Statement ................................................................................................................... 7

## 2.2 Importance of the Vision in Requirement Engineering ........................................................ 7

# 3.0 System Goals ............................................................................................................................ 8

## 3.1 Relationship Between Goals and Problem Statement ........................................................... 8

## 3.2 Relationship Between Vision and Goals ............................................................................. 10

# 4.0 Requirements Engineering Context Analysis ......................................................................... 10

## 4.1 Subject Facet ....................................................................................................................... 10

## 4.2 Usage Facet ..........................................................................................................................11

## 4.3 IT System Facet .................................................................................................................. 12

## 4.4 Development Context ......................................................................................................... 13

## 4.5 Functional Requirements .................................................................................................... 14

## 4.6 Quality Requirements ......................................................................................................... 15

## 4.7 Impact of System Context ................................................................................................... 16

# 5.0 Originality and Novelty of the Proposed System ................................................................... 17

## 5.1 Existing Seat and Space Allocation Systems ...................................................................... 17

## 5.2 White Space Analysis Table ................................................................................................ 18

## 5.3 Interpretation of White Space Analysis .............................................................................. 19

## 5.4 Conclusion of White Space Analysis .................................................................................. 20

---

<!-- Page 3 -->

# 6.0 Realistic Implementation and Expected Output ..................................................................... 21

## 6.1 Expected System Output ..................................................................................................... 21

## 6.2 Expected Users or Beneficiaries ......................................................................................... 21

## 6.3 Proposed Technologies ....................................................................................................... 22

## 6.4 Project Scope Suitability ..................................................................................................... 22

## 6.5 Algorithm Development Direction ..................................................................................... 23

## 6.6 Practical Implementation Considerations ........................................................................... 25

# 7.0 Conclusion .............................................................................................................................. 26

References ..................................................................................................................................... 27

---

<!-- Page 4 -->

# 1.0 Project Background and Problem Statement
## 1.1 Project Background
In large-scale assemblies, formal events, banquets, conferences, ceremonies, and other
organizational gatherings, seat allocation for participants is a recurring operational responsibility
for event organizers. In most of the real-world scenarios, event organizers must assign each
participant a suitable seat while weighing and considering several conflicting factors such as
participant priority, contribution to the event, organizational position, attendance history, group
relationship, accessibility requirements, and event-specific rules.

Seating allocation can be viewed computationally as a constraint satisfaction problem
(CSP), where a set of participants must be mapped onto a limited number of seats while adhering
to specific rules and predefined restrictions. Constraint programming and constraint satisfaction
have been used to represent such problems for a long time, where variables must take values under
a specified set of constraints (Rossi et al., 2006). Participants, seating zones, and event rules
translate into list of variables, domains and constraints within the seating domain. Event organizers
usually rely on manual tools such as Microsoft Excel, printed seating charts, or paper-based layouts.
These approaches are still capable for handling small events effectively, since participants can be
manually arranged into tables, rows, or seating zones by human manual effort. However, as the
number of participants and seats to be allocated increases, the number of possible seating
combinations expands rapidly, making full manual review by humans unfeasible for large-scale
events.

Manual seat allocation becomes vulnerable to duplicate assignments, overlooked
participant profiles, uneven priority handling, and conflict when last-minutes changes occur after
an event involve hundreds and more of participants. The event organizer often has to perform
manual review and frequent changes on several sections of the seating plan in an event where a
participant is absent, substituted, or moved to a different group. This increases operational
workload and affects the consistency of seating allocation for participants.

Commercial event-planning tools such as Cvent, PerfectTablePlan, WeddingWire, and
Zola offer features including floor plan design, table arrangement, guest list management, drag-
and-drop seating and printable seating charts. Whole WeddingWire and Zola offer similar features

---

<!-- Page 5 -->

for creating floor plans, assigning guests, and exporting or sharing arrangements (WeddingWire,
n.d.; Zola, n.d.), PerfectTablePlan, for example, manages guest details, preferences, manual drag-
and-drop or automatic seat assignment, it also supports printable charts. However, these solutions
prioritize visualization of seat allocation, guest arrangement, and manual planning support rather
than explicit fairness-driven allocation controlled by customizable weighted constraint.

Against this backdrop, the proposed Final Year Project sets out to develop an intelligent
automated seating allocation service that helps organizers of large-scale events produce fair,
constraint-compliant seating plans. Implementation and user testing draw on the PJ Kwan Inn Teng
event use case under the collaborator which Netizen eXperience Corporate Social Responsibility
(CSR) temple management platform. The underlying algorithmic approach and system design are
nevertheless kept deliberately general, so that the service can later be adapted to other large-scale
settings such as company gala dinners, annual dinners, conferences, or formal assemblies.

## 1.2 Current Situation and Existing Process
Across most event guest management settings, the current approach to seating allocation can be
characterized as the following:

    Existing Process          Description                           Limitation
    Manual     Excel    / Organizers manually prepare               This approach is adaptable and
    Spreadsheet Planning participant lists and assign seat          flexible, but when there are many
    numbers     using    spreadsheet          participants, it is time-consuming
    columns and tables.                       and is prone to mistakes.
Manual Seating Chart / Organizers need to manually place This method mainly relies on
    Paper-Based Layout     names or groups onto a printed or human judgment, and it became
    digital layout.                   difficult to update during last-
minute changes.
    Visual Event Planning Organizers use these platforms for        These platforms are helpful in
    Platforms             floor plan creation, guest list           visualization       on     seating
    management,         drag-and-drop         management, while still having
    seating, table arrangement and            limitations in automating the set
    printable layout.                         allocation to participant based on
their profiles.
    Human      Rule-Based Organizers use experience to This approach may produce
    Allocation            decide priority seating, group inconsistent results because rules

---

<!-- Page 6 -->

    Existing Process          Description                             Limitation
    placement,         and       special and priorities are not always
    arrangements.                        formally measured.

## 1.3 Problem Statement
Large-sale assembly seating allocation operations are commonly handled through manual planning,
spreadsheet-based arrangements, paper-based seating charts, or visual seating management
technologies. Although these methods can support basic need of seating allocation on small-scale
events, they become inefficient and inconsistent when the event organizers must consider and take
in account multiple criteria such as participant priority, contribution level, organizational position,
attendance history, group tires, and event-specific constraints.
The problem becomes more significant because seating allocation is not merely a visual
arrangement task. It can involve many possible participant-to-seat combinations, and the allocation
decision must satisfy both mandatory rules and preferred conditions. Constraint programming is
suitable for this type of problem because it allows real-world rules to be represented as constraints
over variables and domains (Rossi et al., 2006). Weighted or valued constraint satisfaction extends
this idea by allowing soft constraints to be assigned violation costs or preference values, which is
suitable when not all preferences can be fully satisfied at the same time (Schiex et al., 1995).
Current systems provide limited support for automated participant profile-based allocation,
configurable constraint weights, and measurable fairness evaluation. Dynamic changes in ad hoc
events, such as absent participants, last-minute participant substitution, or group replacement, are
also difficult to handle through manual or template-based methods. Therefore, there is a need for
an intelligent and configurable seating allocation service that can generate fair and constraint-
compliant seating plans for large-scale assemblies by applying dynamic weighted constraint
optimization.

## 1.4 Overview of Proposed Solution
In order to produce an optimal seating allocation outcome, the suggested system is an automated
seating allocation service that analyzes participant profiles, seating layout information, and event-
specific constraint configurations. The system will be separated into two parts, which the seat
allocation core algorithm will be built as an API endpoint-exposing backend microservice
integrated with a frontend admin dashboard for previewing the seat allocation result, edit the
weightage of the constraints and exporting the seating plan into PDF format.

---

<!-- Page 7 -->

    Component                          Description

    Participant Profile Input          Contains participant attributes such as priority, contribution
level, organizational position, attendance history, group
relationship, and participation status.

    Seating Layout Input               Contains seat-related information such as seat ID, row,
column, zone, availability, and seat quality score.

    Constraint Configuration           Contains predefined hard constraints and weighted soft
constraints used to guide the allocation process.

    Seat Allocation API Service        Processes input data and generate an optimized seating
allocation result.

    Optimization Solver                Solves the formulated constraint-based optimization model.

Admin Seating Plan Review Allows event organizers to view the generated seating plan
    Page                      and export the seating layout.

Dynamic Reallocation Function Allow the platform to call the allocation service again when
participant or event data changes.




# 2.0 System Vision
## 2.1 Vision Statement
To provide an intelligent and configurable seating allocation service that supports constraint-
compliant seating arrangements for large-scale assemblies that enabling event organizers to
generate seating plans automatically by considering participant profiles, priority rules, and event-
specific constraints.

## 2.2 Importance of the Vision in Requirement Engineering
The system vision articulates the change that the proposed system is intended to bring to the
existing seating allocation process. By stating the system’s overall purpose, it anchors the
subsequent identification of goals, requirements, stakeholders, system context, and expected
outputs.
This vision statement matters in Requirements Engineering because it keeps the project
oriented toward its central problem. The aim here is neither to build a complete event management
system nor to invent a new optimization algorithm. Rather, the project sets out to deliver a

---

<!-- Page 8 -->

configurable seating allocation service that strengthens manual seating workflows through
automated allocation, constraint handling, and fairness evaluation.




# 3.0 System Goals
## 3.1 Relationship Between Goals and Problem Statement
A goal in requirements engineering is a high-level objective that one or more stakeholders have
for the system that is being developed. Goals have a practical purpose: they provide a basis from
which needs, scenarios, and design choices that may be made, and translate the system vision into
more tangible goals. This project's main objective is G1 since it encapsulates the main objective
of the suggested system, which is to allow event planners to create seating arrangements for sizable
gatherings. To support clearer goal modelling, this principal goal is refined as follows:

**Main Goal (MG1): The system shall support event organizers in generating fair and constraint-**
compliant seating plans for large-scale assemblies with reduced manual effort.

This principal goal brings together the project’s essential intentions: automated generation
of seating plans, fairness, constraint compliance, and a lighter manual workload. The remaining
system goals are then sorted into hard goals and soft goals. Hard goals are those whose satisfaction
can be unambiguously confirmed or denied through system functions, whereas soft goals are
quality-oriented and lack a single absolute satisfaction condition; they are instead judged through
indicators such as usability, fairness score, performance, consistency, or stakeholder satisfaction.

    Goal ID     Goal Description                         Goal Type     Rationale
    MG1         The system shall support event Main Goal               This is the root goal because it
    organizers in generating fair and                      summarizes        the    central
    constraint-compliant seating plans for                 purpose of the proposed
    large-scale assemblies with reduced                    system.
manual effort.
    HG1         The system shall generate seating Hard Goal            This goal can be objectively
    plans based on participant profiles                    checked by verifying whether
    and seating layout data.                               the      system     produces
participant-to-seat
assignments.

---

<!-- Page 9 -->

    Goal ID   Goal Description                       Goal Type    Rationale
    HG2       The system shall consider event- Hard Goal          This goal can be checked by
    specific rules and constraints during               verifying     whether     the
    seat allocation.                                    allocation result follows the
    configured      rules     and
constraints.
    HG3       The system shall allow organizers to Hard Goal      This goal can be checked by
    configure predefined      constraint                verifying whether users can
    weights.                                            adjust the weight values for
supported constraint types.
    HG4       The system shall support dynamic Hard Goal          This goal can be checked by
    reallocation when participant or event              testing whether the system can
    data changes.                                       regenerate seating results after
    participant           absence,
    substitution,     or     group
changes.
    HG5       The system should provide seating Hard Goal         This goal can be checked by
    allocation results in a reviewable and              verifying     whether       the
    exportable format.                                  generated seating result can be
displayed and exported.
    SG1       The system should improve fairness Soft Goal        Fairness is quality-oriented
    in seating allocation.                              and must be evaluated using
fairness indicators, priority-
seat suitability, or constraint
satisfaction scores.
    SG2       The system should reduce manual Soft Goal           Manual effort reduction can
    effort for event organizers.                        be     evaluated      through
comparison with existing
manual workflow, but it is not
a simple yes/no condition.
    SG3       The     system     should     improve Soft Goal     Consistency depends on
    consistency of seating decisions.                   whether the same rules and
weights produce systematic
allocation results.
    SG4       The     system      should      provide Soft Goal   Explainability  can   be
    explainable allocation results.                     supported through solver

---

<!-- Page 10 -->

    Goal ID     Goal Description                         Goal Type    Rationale
status, fairness score, and
constraint satisfaction reports.
    SG5         The system should be usable by event Soft Goal        Usability is a quality goal that
    organizers    without      requiring                  depends on interface clarity
    knowledge      of       optimization                  and user understanding.
algorithms.

## 3.2 Relationship Between Vision and Goals
    Vision Element                                                    Related Goals

    Intelligent seating allocation service                            G1, G2, G3, G7

    Configurable seating allocation service                           G4

    Fair seating arrangement                                          G3, G7

    Constraint-compliant seating arrangement                          G2, G4, G7

    Support for large-scale assemblies                                G1, G5, G6

    Automatic generation based on participant profiles                G1, G2, G3




# 4.0 Requirements Engineering Context Analysis
Requirements Engineering context analysis identifies the objects, stakeholders, data, and technical
environments that shape a system’s requirements. Here the system context is organized into three
facets—Subject, Usage, and IT System—supplemented by a Development Context, since the
system is built within an academic Final Year Project (FYP) timeline and an industry collaboration
arrangement.

## 4.1 Subject Facet
The Subject Facet covers the information, entities, and domain concepts that the system represents
or that shape how its information is represented.

    System Context Object             Explanation

    Participant Profile               Participant profile is represented as system data and directly
influences allocation decisions.

---

<!-- Page 11 -->

    System Context Object             Explanation

    Event / Assembly                  The event provides the domain situation that requires seating
allocation.

    Venue Layout                      Venue layout defines the physical seating environment and
constrains possible assignments.

    Seat                              Seat is the resource assigned to a participant and contains
attributes used in the allocation model.

    Seating Zone                      Seating zones influence seat quality, priority matching, and
constraint modelling.

    Family / Organization Group       Group data is used to support group adjacency or group-based
seating rules.

    VIP / Priority Category           Priority category is part of participant classification and affects
seat suitability.

    Constraint Rule                   Constraint rules define what must or should be satisfied during
seating allocation.

    Constraint Weight                 Constraint weight defines the importance of soft constraints
during optimization.

    Fairness Score                    Fairness score represents how well the generated seating plan
satisfies fairness criteria.

    Seating Plan                      Seating plan is the generated allocation output that maps
participants to seats.

    Participant Status                Participant status affects dynamic reallocation              when
participants are absent, substituted, or changed.

## 4.2 Usage Facet
The Usage Facet covers the users, stakeholders, and external systems that interact with the
proposed system, whether directly or indirectly, or that derive benefits from its use.

    System Context Object            Explanation                        Interaction with the Existing
System

    Event Organizer / Admin          The event organizer is the Configure event rules, triggers
main user who needs to allocation, reviews seating
generate and review seating map, and exports results.
plans.

---

<!-- Page 12 -->

    System Context Object         Explanation                      Interaction with the Existing
System

    Secretariat Staff             Secretariat   staff   support Updates participant records,
participant data preparation verifies participant status, and
    and event-day operations.     uses the generated seating
plan.

    System Administrator          System          administrators Ensure system availability,
maintain technical access and access control, and integration
    platform operation.            readiness.

    Netizen eXperience            The collaborator’s technical Connects the platform to the
team supports integration with seat allocation API and
    the existing CSR platform.     maintains      platform-side
integration.

    Event Participant             Participant is an indirect Does not directly operate the
stakeholder affected by the allocation service but receives
    seating decision.           an assigned seat.

    Existing CSR Web Platform     The platform acts as an          Sends participant, layout, and
    external system that interacts   constraint data to the service
    with      seat      allocation   and receives seating plan
    microservice.                    JSON.

Final Year Project (FYP) Academic stakeholders who Do not use the system
    Supervisor / Examiner    evaluate the project direction operationally, but influence
    and outcome.                   scope,     evaluation,   and
documentation.

## 4.3 IT System Facet
The IT System Facet covers the technical and operational environment within which the system
will be deployed or integrated.

    System Context Object         Explanation

    Existing CSR Web Portal       The existing Netizen eXperience CSR Next.js web application
will call the seat allocation service and display the seating map
review page.

    Seat Allocation API Service   The proposed backend microservice is the main technical
component that processes allocation requests.

    Database                      AWS DynamoDB is considered for storing participant data,
event data, seating layout, constraint configuration, and
generated allocation results.

---

<!-- Page 13 -->

    System Context Object            Explanation

    Optimization Solver              OR-Tools CP-SAT is used as the proof-of-concept solver for
solving the constraint-based optimization model.

    Hosting   and         Compute AWS Lambda or a compute instance may be used to deploy
    Environment                   and execute the service depending on runtime requirements.

Frontend Seating Plan Review The existing web platform will include a new admin page to
    Page                         display generated seating plans.

    API Communication                The web platform and allocation service will communicate
through structured JSON requests and response payloads.

    Export Module                    The system will provide exportable seating results for event
operation and reporting.

## 4.4 Development Context
The Development Context covers the objects and constraints that shape how the system is
developed.

    Development           Rationale for Inclusion    Source &     Explanation of Source
    Context Object                                   Type

    Final Year Project The project must be Project                Limits the project scope and
    (FYP) Timeline     completed within the Constraint            affects       implementation
    FYP1       and  FYP2                       priorities.
timeframe.

    Final Year Project Provides        academic Academic          Advises on research direction,
    (FYP) Supervisor guidance and validates Stakeholder           methodology,              and
    the project scope.                         documentation quality.

    Netizen            Provides industry use Industry             Supports          requirement
    eXperience         case     and  platform Stakeholder         elicitation, case study data
    Supervisor       / context.                                   collection, and integration
    Collaborator                                                  understanding.

    PJ Kwan Inn Teng Needed to collect real Domain                Supports requirement gathering
    Site Visit       event context, historical Source             and validation of the event use
    seating references, and                      case.
constraint examples.

    Historical   Event Used for testing         and Data Source Expected     size   of    the
    Dataset            validation.                              participants is approximately
400 to 800 participants. The

---

<!-- Page 14 -->

    Development         Rationale for Inclusion      Source &       Explanation of Source
    Context Object                                   Type

data will be collected and
validated during site visit.

    Existing   Seating Used as a reference for Domain               Help define seat rows, zones,
    Map                modelling the venue Artifact                 labels,    and      allocation
    layout and seat quality.                     assumptions.

    SRS and SDD Required to translate Documentat                    Supports system architecture,
    Documents   requirements     into ion Artifact                  use case modelling, and
    software design.                                    implementation planning.

    Development         Required to build the Technical             Includes Python, Next.js, OR-
    Tools               prototype.            Resource              Tools     CP-SAT,        AWS
DynamoDB, and AWS Lambda
or compute instance.

    Privacy             Participant data may Ethical        / Data should be anonymized or
    Considerations      contain     personal  or Data         simulated where necessary.
    sensitive attributes.    Constraint

    Hardware       and Solver runtime may be Technical              Influences solver configuration,
    Runtime            affected by dataset size Constraint          performance      testing,   and
    Limitations        and          deployment                      scalability assumptions.
environment.

## 4.5 Functional Requirements
The functional requirements set out the services the system is expected to provide.

    Requirement ID     Functional Requirement                                        Related Goal

    FR1                The system shall allow the existing web platform to send G1, G2
participant profile data to the seat allocation service.

    FR2                The system shall allow the existing web platform to send G1, G2
seating layout data to the seat allocation service.

    FR3                The system shall allow event organizers to configure G4
predefined constraint weights for the allocation process.

    FR4                The system shall map predefined human-readable event G2, G4
rules into computable hard constraints and weighted soft
constraints.

---

<!-- Page 15 -->

    Requirement ID     Functional Requirement                                       Related Goal

    FR5                The system shall generate a seating allocation result based G1, G2, G3
on participant profiles, seating layout, and constraint
configuration.

    FR6                The system shall return the generated seating allocation G6
result in JSON format.

    FR7                The system should provide solver status such as optimal, G7
feasible, infeasible, unknown, or error status.

    FR8                The system shall calculate and return fairness-related G3, G7
indicators for the generated seating plan.

    FR9                The system shall allow dynamic reallocation by processing G5
updated participant or event data.

    FR10               The system shall allow event organizers to review the G6
generated seating map through the admin review page.

    FR11               The system shall allow seating results to be exported for G6
event operation.

    FR12               The system shall store or retrieve relevant events, G1, G6
participant, constraint, and seating result data from the
database where necessary.

## 4.6 Quality Requirements

The quality requirements describe the expected quality characteristics of the proposed system.

| Requirement ID | Quality Requirement |
|---|---|
| **NFR1: Performance** | The system should generate a seating allocation result within an acceptable processing time for approximately 100 to 200 participants. |
| **NFR2: Usability** | The admin seating plan review page and participant seat lookup page should be clear and understandable. |
| **NFR3: Reliability** | The system should return clear status messages when allocation succeeds, fails, or becomes infeasible. |
| **NFR4: Maintainability** | The constraint configuration and seat allocation solver logic should be modular and low coupling to one another. |
| **NFR5: Security and Privacy** | Real participant data should be protected and anonymized where necessary during testing and reporting. |
| **NFR6: Scalability** | The system design should allow future extension to larger datasets or other event types. |

## 4.7 Impact of System Context
The system context shapes both the requirements and the development decisions of this project.
The subject Facet mainly includes the characteristics of the event participant profile, seating zone,
venue layout, event specific constraint rule, group relationship, and participant status that define
the information to be represented in a system. The system requires data structures that can store
and process these attributes because seating allocation decisions are based on participant priority,
contribution level, organizational position, attendance history, and group relationships.
Additionally, because allocation is dependent on the physical layout of the venue, it must represent
seats, rows, zones, and seat quality in an organized manner.

From the perspective of the Usage Facet, it provides the needs of event organizers,
secretariat staff, system administrators, and the existing web platform drive the system’s functional
and usability requirements. Since the event organizers are the primary users who review allocation
results, the system must support an intelligible seating plan review interface and exportable output.

---

<!-- Page 17 -->

It must also support dynamic reallocation following participant absence, substitution, or other data
changes, because secretariat staff may update participant status during event preparation. The
system needs to expose a clear API request-and-response structure, so that the existing CSR web
platform could interact with the intelligent seat allocation service.

From the IT System Facet, the chosen technologies and operating environment shape
architectural and implementation decisions. Implementing the allocation logic as a standalone
backend microservice commits the system to JSON-based API communication. Adopting OR-
Tools CP-SAT requires the allocation model to be expressed through integer variables, constraints,
and an optimization objective. The prospective use of AWS Lambda or a compute instance, in turn,
conditions runtime expectations, deployment strategy, and performance testing—and should
solver runtime prove too long for serverless execution, a compute instance becomes the more
appropriate choice.

The Development Context further bounds the project’s scope. As a Final Year Project with
a fixed timeline, the system must remain realistic and manageable; accordingly, it concentrates on
predefined constraint templates, configurable weights, API-based allocation, an admin review UI,
and dynamic reallocation through repeated service calls. Taken as a whole, the system context
clarifies what the system should do, what data it must process, who uses or benefits from it, and
which technical decisions remain feasible within the Final Year Project (FYP) timeline. In short,
the system context clarifies what the system needs to accomplish, what data it must process, who
uses or benefits from it, and which technical choices are still possible within the Final Year Project
(FYP) timeframe.




# 5.0 Originality and Novelty of the Proposed System
## 5.1 Existing Seat and Space Allocation Systems
This section sets the proposed system against existing seat and space allocation systems used in
real-world event planning.

---

<!-- Page 18 -->

    No Existing System          Main Capability                     Limitation

    1    Manual Excel         / Allows organizers to manually       No automated allocation, no
    Spreadsheet            record participant names, seat      fairness      metric,     no
    Planning               numbers,     groupings,   and       optimization, and difficulty
    remarks.                            handling dynamic changes.

    2    Manual      Seating Allow organizers to manually Highly dependent on human
Chart / Paper-Based place participants on a physical judgment and difficult to scale
    Layout              or digital seating layout.       for hundreds of participants.

    3    Cvent    /     Social Supports event management, Strong in event planning and
    Tables                event               diagramming, visualization but limited in
    collaboration, and floor planning. explicit      fairness-driven
    weighted           constraint
optimization.

    4    PerfectTablePlan       Supports guest details, RSVPs,      Provides useful automatic
    preferences,            automatic   seating support, but formal
    assignment,         drag-and-drop   fairness      metrics       and
    seating, last-minute changes, and   configurable          weighted
    printed floor plans.                constraint optimization are not
the focus.

    5    WeddingWire            Supports drag-and-drop seating      Useful for event seating
    Seating Chart Tool     charts, RSVP tracking, table        visualization but limited in
    shape customization, sharing,       formal      optimization and
    printing, and exporting.            fairness evaluation.

    6    Zola Seating Chart Supports table assignment, floor        Useful for basic guest seating
    Tool               plan     customization,    guest        planning, but limited in
    grouping, printing, downloading,        constraint        optimization,
    and sharing.                            dynamic reallocation, and
fairness scoring.


## 5.2 White Space Analysis Table
    Existing Method /    Automated     Dynamic         VIP /        Configurable     Constraint-
    System               Allocation    Reallocation    Priority     Constraints      Based
    Based on      After           Handling     and Weights      Optimization
Changes

---

<!-- Page 19 -->

Participant
Profile
    Manual Excel /       No              No              Manual       No               No
Spreadsheet
    Manual Seating       No              No              Manual       No               No
Chart / Paper
Layout
    Cvent / Social       Partial         Partial         Partial      Limited          Limited /
    Tables                                                                             Unclear
    PerfectTablePlan     Partial         Partial         Partial      Limited          Partial
    WeddingWire /        Partial         Partial         Partial      Limited          Limited
Zola
    Proposed Final       Yes             Yes             Yes          Yes              Yes
Year Project
(FYP) System


## 5.3 Interpretation of White Space Analysis
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

---

<!-- Page 20 -->

allocation criteria. Fourth, most systems offer no measurable fairness metric by which to judge
whether a generated plan is balanced and defensible.

Among commercial offerings, PerfectTablePlan is one of the more sophisticated,
supporting automatic seating assignment and employing a genetic algorithm to search for strong
layouts once the combinatorial space outgrows exhaustive search (Oryx Digital Ltd., n.d.-b). The
automatic assignment does not deliver explicit fairness metrics, participant-profile-based
constraint weighting, or dynamic weighted constraint optimization as the system’s central
objective. A white space therefore persists in a system that unites automated seating allocation with
configurable constraints and measurable fairness evaluation.

The proposed Final Year Project (FYP) system addresses this gap with an intelligent seating
allocation service that draws on participant profile data, predefined constraint templates,
configurable soft-constraint weights, and fairness evaluation to generate seating plans. It is, in
effect, not merely a visual seating chart tool but a decision-support system for fair, constraint-
compliant allocation.

## 5.4 Conclusion of White Space Analysis
The white space analysis substantiates the originality and novelty of the proposed system through
its emphasis on fairness-driven automated allocation. Where existing systems concentrate on
manual planning, visual arrangement, guest list management, or rudimentary automatic seating
assistance, the proposed Final Year Project (FYP) system targets automated participant-profile-
based allocation, dynamic reallocation after event changes, VIP and priority handling, configurable
constraints and weights, constraint-based optimization, and measurable fairness evaluation. In
short, the proposed system offers practical value by reducing the manual workload and improving
the consistency of seat allocation for participant in a large-scale event.

---

<!-- Page 21 -->

# 6.0 Realistic Implementation and Expected Output
## 6.1 Expected System Output
    Expected Output                  Description

    Seat Allocation API Endpoint     A deployed backend service that receives participant data,
seating layout, and constraint configuration.

    JSON Seating Allocation Result   The service returns participant-to-seat mapping in
structured JSON format.

    Solver Status                    The service returns whether the result is optimal, feasible,
infeasible, unknown, or error status.

    Fairness Score                   The system calculates an allocation fairness score based on
the generated result.

    Constraint Satisfaction Report   The system reports whether hard constraints are satisfied
and how much soft-constraint penalty remains.

    Admin Seating Plan Review        The existing web platform displays a generated seating
    Page                             map for event organizer review.

    Exportable Seating Layout        The seating plan can be exported for operational use.

    Dynamic Reallocation Result      The service can be called again when participants are
absent, substituted, or changed.

## 6.2 Expected Users or Beneficiaries
    User / Beneficiary               Expected Benefit

    Event Organizer / Admin          Reduces manual effort in preparing seating plans and
supports more consistent decision-making.

    Secretariat Staff                Help staff manage event-day participant changes and refer
to a structured seating plan.

    Event Participant                Benefits indirectly from a more organized and fair seating
arrangement.

Netizen eXperience Developer / Gains a reusable allocation service that can be integrated
    Admin                          into the existing CSR web platform.

    System Administrator             Benefits from clearer system boundaries,                 API
communication, and manageable deployment.

---

<!-- Page 22 -->

    User / Beneficiary                   Expected Benefit

Future Event Management Use The service may be adapted to other events such as company
    Cases                       gala dinners, annual dinners, conferences, and formal
assemblies.

## 6.3 Proposed Technologies
    Layer          Proposed Technology / Explanation
Platform
    Backend        Python / Next.js API Python is suitable for the allocation service because
    route                 OR-Tools has Python support. A Next.js API route
may be used for platform-side integration if needed.
    Solver         OR-Tools CP-SAT               Used as the proof-of-concept solver for modelling
and solving the constraint-based optimization
problem.
    Database       AWS DynamoDB                  Used to store event data, participant data, seating
layout, constraint configuration, and allocation result
where applicable.
    Frontend       Existing        Netizen Used to provide the admin seating plan review page
eXperience CSR Next.js and call the allocation service.
Web Application
    Deployment AWS EC2 Instance                  AWS EC2 instance may be used depending on solver
runtime and deployment requirements.
    Data Format JSON                             Used for API request and response payloads between
the existing platform and the allocation service.

## 6.4 Project Scope Suitability
This Final Year Project is a system development-based project with an algorithmic research
component. The primary focus is to design and develop a seating allocation service that can be
integrated into an existing web platform. The research does not seek to develop an entirely
innovative optimization algorithm for the field of Constraint Optimization Problem (COP), but the
algorithmic component assists the modeling, selection, and assessment of the approach to achieve
the project vision on developing an intelligent seating allocation system that enabling event
organizers to generate seating plans automatically by considering participant profiles, priority rules,
and event-specific constraints.

---

<!-- Page 23 -->

    Scope Coverage                Description

    Requirement Gathering         Conduct site visit and discussion with collaborator to collect
event use case, seating layout, existing seating map, participant
attributes, and constraint list.

    Requirements                  Convert gathered requirements into SRS and SDD artefacts.
Documentation

    System Design                 Prepare system architecture diagram, use case diagram, process
flowchart, and sequence diagram.

    Literature Review             Review CSP, COP, weighted constraint optimization, constraint
mapping, fairness evaluation, and relevant allocation approaches.

    Backend API Service           Develop a seat allocation microservice using Python and OR-
Tools CP-SAT.

    Integration Flow              Allow the existing web platform to call the allocation service and
receive JSON seating results.

    Admin Review UI               Develop a seating plan review page in the existing Next.js web
application.

    Exportable Seating Layout     Allow generated seating results to be exported for event
operation.

    Dynamic Reallocation          Support reallocation by calling the service again after participant
status or event data changes.

    System Evaluation             Evaluate the system using a case-study dataset of approximately
400 to 800 participants, focusing on fairness score, constraint
satisfaction, and runtime practicality.



## 6.5 Algorithm Development Direction
The seating allocation problem will be formulated as a Dynamic Weighted Constraint Optimization
Problem. In this formulation, participants, seats, venue layout, and event rules will be represented
as computable data objects. Human-readable event rules will be mapped into predefined constraint
templates, including hard constraints and weighted soft constraints.

A basic Constraint Satisfaction Problem involves assigning values to variables from
defined domains while satisfying a set of constraints (Rossi et al., 2006). In the proposed system,
participants and seats can be represented as decision variables and domains, while event rules such
as “one participant can only occupy one seat” or “one seat cannot be assigned to more than one

---

<!-- Page 24 -->

participant” can be represented as hard constraints. However, seating allocation often includes
preferences that may not all be fully satisfied at the same time. Therefore, weighted or valued
constraint satisfaction is important because it enables the system to compute and cost minimized
and high-quality seat allocation solution by assigning costs or preferences to the soft constraints
(Schiex et al., 1995).

Hard constraints, such as assigning each participant to only one seat and preventing two
participants from occupying the same seat are the necessary and mandatory rules that must not be
violated. Soft constraints, such as VIP or priority handling, group adjacency, participant profile-
seat suitability, and event-specific preferences represent preferred rules that may be assigned
different weights on the cost calculation. The primary solver for the system implementation will
be the OR-Tools CP-SAT from Google. CP-SAT is the suitable model because it supports integer
decision variables, constraints, optimization objectives, and solver status reporting such as
“optimal”, “feasible”, “infeasible”, “model invalid”, or “unknown” (CP-SAT Solver, n.d.). After
receiving the modelled variables, restrictions, and goal function, the solver will try to generate an
ideal or workable seating allocation outcome.

The dynamic aspect of the project refers to two main capabilities. First, organizers may
adjust predefined constraint weights to reflect different event priorities. Second, the system may
generate a revised seating plan after participant or event changes, such as absence, substitution, or
group replacement. This interpretation of “dynamic” is feasible for the Final Year Project (FYP)
scope because it avoids unrestricted natural-language rule generation while still supporting
practical event changes.

Fairness will be included in two stages. During optimization, fairness will be represented
as part of the objective function, such as minimizing mismatch between participant priority and
seat suitability. After solving, fairness will also be evaluated through external calculation, such as
a fairness score or constraint satisfaction indicator. Jain et al. (1998) proposed a quantitative
fairness index for resource allocation, which supports the idea that fairness can be measured
instead of described only qualitatively. In this project, fairness measurement will be adapted to the
seating allocation context to support objective evaluation of generated seating plans.

---

<!-- Page 25 -->

## 6.6 Practical Implementation Considerations
    Consideration                   Explanation

    Dataset Availability            Historical participant data and existing seating maps are required
to create realistic test cases. These will be collected and validated
during the site visit.

    Data Privacy                    Participant data should be anonymized or simulated when used for
testing, reporting, or demonstration.

    Solver Runtime                  The optimization model may become computationally expensive
as the number of participants and seats increases.

    Constraint Complexity           Only predefined constraint templates should be supported to
prevent scope creep.

    Platform Integration            The backend service should return clean JSON responses that can
be consumed by the existing platform.

    Deployment Limitation           AWS Lambda may have runtime limitations, so a compute
instance may be considered if the solver requires longer execution
time.

    User Understanding              The seating plan review page should present results clearly so that
organizers can understand and use the generated plan.

    Future Manual Override          Drag-and-drop manual override is useful but should be placed as
future work to avoid increasing the implementation scope.


The implementation is planned carefully to ensure that the project remains realistic within the Final
Year Project 1 & 2 timeline. The first development priority should be the constraint modelling
logic and the seating allocation API service. After the backend service is functional, the project
can proceed to integration with the existing web platform and development of the admin seating
plan review page. Dynamic reallocation should be implemented by allowing the platform to call
the allocation service again with updated participant data, rather than attempting to build a fully
real-time optimization system.

---

<!-- Page 26 -->

# 7.0 Conclusion
This proposal described a system development-based Final Year Project that carries an algorithmic
research component. It responds to a genuine operational gap in large-scale seating allocation by
building an intelligent, configurable service spanning participant-profile-based allocation,
dynamic reallocation, priority handling, configurable constraint weights, constraint-based
optimization, and fairness evaluation.

The anticipated deliverable is a working prototype comprising a seating allocation API service,
integration with the existing CSR web platform, an admin seating plan review page, an exportable
seating layout, and measurable allocation indicators. Its scope is realistic for the Final Year Project
(FYP) timeline precisely because it targets a focused allocation service rather than a complete
event management platform or a newly invented optimization algorithm.

In sum, the proposed system delivers practical value to event organizers—reducing manual effort
and improving consistency—while contributing academic value through the application of
dynamic weighted constraint optimization to a real-world seating allocation problem.

---

<!-- Page 27 -->

# References
CP-SAT Solver. (n.d.). Google for Developers.
https://developers.google.com/optimization/cp/cp_solver

Jain, Raj & Chiu, Dah Ming & WR, Hawe. (1998). A Quantitative Measure Of Fairness And
Discrimination For Resource Allocation In Shared Computer Systems. CoRR.
cs.NI/9809099.

Rossi, F., Beek, P.V., & Walsh, T. (2006). Handbook of Constraint Programming.

Schiex, T., Fargier, H., & Verfaillie, G. (1995). Valued Constraint Satisfaction Problems: Hard
and Easy Problems. International Joint Conference on Artificial Intelligence.

WeddingWire. (n.d.). Wedding seating chart tool. https://www.weddingwire.com/wedding-
planning/wedding-seating-tables.html

Zola. (n.d.). Wedding seating chart: Seat all your guests in minutes.
https://www.zola.com/wedding-planning/seating-chart

