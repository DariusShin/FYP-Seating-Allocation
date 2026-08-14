# AI Agent Prompt Guideline for Amending the SRE Assignment 2 Report

## 1. Agent Role

You are acting as an experienced **Software Requirements Engineering reviewer and academic editor**.

Your task is to amend the existing Assignment 2 report for the Final Year Project titled:

> **Intelligent Automated Seating Allocation System for Large-Scale Assemblies Using Configurable Constraint Optimization**

---

## 2. Files and Source Hierarchy

Use the following files according to this strict hierarchy.

### 2.1 Primary Source of Truth

#### `fyp_interim-report-refined(1).md`

This file is the **sole source of truth** for the latest:

- Final Year Project scope;
- requirements;
- system behaviour;
- case-study information;
- technical design;
- constraint definitions;
- evaluation methodology;
- terminology;
- implementation direction;
- project progress.

Every statement describing the current or refined FYP must agree with this file.

### 2.2 Original Proposal Under Review

#### `SRE-Assignment1.md`

This file represents the **early-stage FYP1 proposal** that must be critically reviewed.

Use it to identify:

- incomplete requirements;
- inconsistent terminology;
- ambiguous statements;
- unverifiable requirements;
- missing requirements;
- early assumptions that were later refined.

Do not silently rewrite the original proposal as though it already contained the details from the refined interim report.

### 2.3 Assignment Instructions

#### `TFB3413_Software_Requirements_Engineering_Assignment_2.md`

Use this file to determine:

- required tasks;
- required report structure;
- expected page length;
- required quality characteristics;
- submission format.

### 2.4 Editable Assignment 2 Source

#### `SRE-Assignment2.md`

This is the document that must be amended directly.

### 2.5 Existing Rendered Report

#### `SRE-Assignment2-Report.pdf`

Use this file only to inspect:

- pagination;
- table readability;
- page breaks;
- cover-page formatting;
- table-of-contents formatting;
- overcrowded sections;
- layout problems.

---

## 3. Main Objective

Revise `SRE-Assignment2.md` so that the report:

1. uses a formal and academic tone;
2. provides a balanced critical review;
3. distinguishes clearly between the original FYP1 proposal and the refined interim report;
4. evaluates functional and non-functional requirements using valid Software Requirements Engineering principles;
5. contains no technical claims that conflict with the refined interim report;
6. follows the structure required by Assignment 2;
7. remains concise, precise, verifiable, and defensible during lecturer review.

---

## 4. General Editing Principles

### 4.1 Source Accuracy

Do not introduce new:

- requirements;
- metrics;
- constraints;
- system behaviours;
- solver outputs;
- evaluation thresholds;
- platform features;
- case-study details;

unless they are supported by the refined interim report.

### 4.2 Distinguish Proposal Weaknesses from Later Improvements

When describing a weakness in Assignment 1:

- state that it belonged to the early proposal;
- explain how it was later refined during the planning phase;
- do not make the original proposal appear more complete than it was.

### 4.3 Avoid Presenting Expected Benefits as Proven Results

Do not present intended benefits as completed findings.

For example, avoid:

> Plans are generated in minutes rather than days.

Use:

> The project is intended to reduce allocation time substantially, improve rule consistency, preserve seating stability during late changes, and provide participants with direct access to the latest published assignment.

### 4.4 Modal-Verb Convention

Use:

- **shall** for mandatory requirements;
- **should** for recommendations, desirable qualities, or items awaiting stakeholder validation;
- **may** for optional behaviour.

### 4.5 Balanced Critical Review

Retain the strengths of the original proposal, including:

- identification of relevant stakeholders;
- recognition of participant, venue, and constraint data;
- distinction between hard and soft goals;
- awareness of integration and deployment concerns;
- recognition of privacy and solver-runtime risks;
- identification of the main allocation pipeline.

---

## 5. Academic Tone Guidelines

Avoid overly absolute, rhetorical, or confrontational expressions.

| Avoid | Preferred academic wording |
|---|---|
| uniformly weak | exhibits recurring specification weaknesses |
| specifies nothing | does not define measurable acceptance criteria |
| root defect | most consequential recurring weakness |
| marketing language | insufficiently operationalised quality claim |
| more damaging than it first appears | has broader implications for traceability and completeness |
| the concepts that carried this review | the principal SRE concepts applied in this review |
| not so much wrong as early | represented an early requirements baseline that had not yet incorporated subsequent stakeholder-validation findings |

Do not weaken valid criticism. Express it neutrally and support it with evidence.

---

## 6. Mandatory Content Amendments

## 6.1 Participant-Facing Seat Lookup

Do not state that participant lookup was completely absent from Assignment 1.

Assignment 1 mentioned a participant seat-lookup page in NFR2. However:

- the participant was not defined consistently as a direct system actor;
- no participant-facing functional requirement was provided;
- no complete lookup workflow was defined;
- lookup was not connected to plan approval and publishing;
- participant access control was not specified.

Replace wording such as:

> An entire actor and use case were missing.

with:

> The proposal inconsistently acknowledged a participant seat-lookup page in NFR2, but it did not define the participant as a direct system actor or provide a corresponding functional requirement, use case, publishing dependency, or access-control requirement.

Apply this correction consistently in:

- Task 2.3;
- Task 3 completeness review;
- Task 3 discussion;
- Task 4 reflection;
- traceability discussion.

---

## 6.2 Performance Requirement

Remove any unsupported target such as:

> 200 participants within 30 seconds.

Use the performance criteria defined in the refined interim report:

- default dataset: 100 registrations;
- case-study layout: 120 physical seats;
- default occupancy: 108 physical seats;
- solver budget: 60 seconds;
- success criterion: `OPTIMAL` result within 60 seconds for the default scenario.

Use a requirement similar to:

> **NFR-PERF-01:** For the default dataset of 100 registrations and the 120-seat case-study layout, the allocation engine shall return an `OPTIMAL` result within the configured 60-second solver budget under the defined evaluation environment.

Also include:

> When the time budget expires before optimality is proven, the system shall return the actual solver status and shall not represent the solution as optimal.

Distinguish between:

- the broader event range of approximately 100–200 participants;
- the default 100-registration evaluation scenario;
- larger scalability experiments, which require a sufficiently large seating layout.

---

## 6.3 Fairness and Allocation-Quality Indicators

Remove references to a general fairness score unless it is operationally defined.

Do not include a proven optimality gap unless the refined interim report explicitly defines it as an output.

Use only supported indicators:

- solver status;
- independent hard-constraint validation result;
- total weighted soft-constraint penalty;
- per-constraint penalty breakdown;
- movement count;
- movement distance, where applicable;
- runtime;
- memory usage, where included;
- comparison against defined baselines.

Describe fairness as allocation quality measured through reconstructible and testable indicators.

---

## 6.4 Reliability and Reproducibility

Do not replace reliability with determinism.

Explain that:

- solver-status reporting is a functional behaviour;
- reliability and reproducibility are separate quality concerns.

Use separate proposed requirements.

### Reliability Example

> **NFR-REL-01:** A plan that fails input validation, solver processing, or independent post-solve validation shall not become publishable, and the previously published plan shall remain unchanged and accessible.

### Reproducibility Example

> **NFR-REP-01:** For identical normalized input data, constraint configuration, solver parameters, and deterministic seed, repeated executions shall produce the same canonical allocation and quality indicators.

---

## 6.5 Infeasibility Handling

Do not promise complete automatic diagnosis of every solver conflict unless this function is supported by the refined report.

Use:

> The system shall return a structured failure response containing the solver status and any determinable validation, capacity, or input failure reasons, and shall prevent an unsuccessful result from being published.

The current system may:

- identify known pre-model capacity failures;
- report invalid input;
- return `INFEASIBLE`;
- return `UNKNOWN`;
- preserve the currently published plan;
- allow organizers to revise data, constraints, weights, or seat availability.

Treat complete conflict-core diagnosis as future work unless it is explicitly included in the current scope.

---

## 6.6 Accessibility

Remove accessibility from descriptions of the confirmed PJKIT constraint set unless it is clearly labelled as a future configurable rule.

The confirmed current constraint areas include:

- contribution tier;
- contribution score;
- activeness;
- group relationship;
- participant status;
- tier-zone placement;
- Emperor two-seat pairing;
- centre-aisle integrity;
- contribution ordering;
- unavailable-seat exclusion;
- movement minimisation during reallocation.

---

## 6.7 Availability

Retain availability as a relevant missing quality concern, but do not invent a percentage or service-level target.

Use:

> An event-window availability requirement should be elicited and agreed with Netizen eXperience because the participant-facing lookup depends partly on the availability characteristics of the existing CSR platform.

Clearly label availability as:

- a recommendation;
- subject to stakeholder validation;
- partly dependent on the host platform.

---

## 6.8 Security and Privacy

Expand the critique of the original NFR5.

The refined quality requirements may include:

- administrative access inherited from the host CSR platform;
- unpublished plan versions restricted to authorised administrators;
- participants limited to viewing their own assignment;
- only the latest approved and published plan visible to participants;
- pseudonymous participant identifiers used in the solver payload;
- display names retained in the host platform where possible;
- participant data anonymised in testing and reporting;
- data retention aligned with the event lifecycle.

Do not imply that the allocation engine itself implements all authentication functions if these functions belong to the host platform.

---

## 6.9 Scalability

Remove the unsupported 400–800 participant figure as an operational requirement.

Use:

> The 400–800 participant estimate should be removed as an operational requirement because it was not validated. The current case-study baseline is the 100-registration, 120-seat scenario. Larger datasets should be treated as exploratory scalability experiments and paired with layouts of sufficient capacity.

---

## 6.10 Site-Visit and Stakeholder-Validation Wording

Do not attribute every refined detail to one site visit unless the source explicitly does so.

Prefer:

- stakeholder validation during the planning phase;
- the site visit and subsequent stakeholder discussions;
- the refined interim report adopts the validated range;
- the planning phase refined the venue, workflow, and constraint assumptions.

---

## 6.11 Existing-System Comparison

Avoid absolute wording such as:

> None of the reviewed tools supports profile-based allocation.

Use:

> None of the reviewed systems provides the required combination of configurable participant-profile-based constraints, constraint optimisation, controlled movement-minimising reallocation, versioned publishing, and participant-facing lookup within one workflow.

---

## 6.12 Anticipated Benefits

Replace statements that sound like completed experimental results.

Use:

> The project is intended to reduce allocation time substantially, improve rule consistency, preserve seating stability during late changes, and provide participants with direct access to the latest published assignment.

---

## 7. Task 2 Requirements Analysis Guidelines

## 7.1 Functional Requirements

List all twelve original functional requirements separately.

Do not combine:

- FR1 and FR2;
- FR3 and FR4;
- FR5 to FR8;
- FR10 and FR11.

For each requirement, include:

| Requirement ID | Requirement Description |
|---|---|

After the original functional-requirement table, evaluate:

- missing requirements;
- under-specified requirements;
- requirements needing improvement.

## 7.2 Non-Functional Requirements

List all six original NFRs individually.

For each NFR, identify:

- category;
- original wording;
- specification weakness;
- recommended measurable improvement.

---

## 8. Task 3 Critical Requirements Review Guidelines

Retain the five required quality characteristics:

1. completeness;
2. correctness;
3. consistency;
4. unambiguity;
5. verifiability.

Use the required table structure:

| Quality Characteristic | Findings | Evidence from Proposal | Recommendation |
|---|---|---|---|

### 8.1 Completeness

State that:

- participant lookup was acknowledged only indirectly in NFR2;
- no participant-facing FR existed;
- versioning, approval, and publishing were missing;
- movement-minimising repair was missing;
- input validation was missing;
- post-solve validation was missing;
- structured failure handling was missing;
- availability and reproducibility were not specified.

### 8.2 Correctness

Include:

- outdated 400–800 participant estimate;
- undefined fairness indicator;
- functional status reporting misclassified as reliability;
- technical and editorial errors;
- early assumptions later corrected through stakeholder validation.

Recommend:

- correcting the participant scale;
- replacing vague fairness with measurable indicators;
- separating functional status reporting, reliability, and reproducibility;
- systematic proofreading.

### 8.3 Consistency

Retain:

- MG1/HG1–HG5/SG1–SG5 versus undefined G1–G7;
- conflicting participant-scale figures;
- inconsistent shall/should usage;
- inconsistent deployment descriptions;
- participant described as indirect while lookup is mentioned.

### 8.4 Unambiguity

Evaluate terms such as:

- fair;
- intelligent;
- reduced manual effort;
- fairness-related indicators;
- predefined rules;
- acceptable processing time;
- clear and understandable;
- where necessary.

Recommend:

- operational definitions;
- measurable criteria;
- enumerated constraint templates;
- a project glossary.

### 8.5 Verifiability

Use verification criteria supported by the refined interim report:

- no duplicate seat assignments;
- valid seat range;
- blocked-seat exclusion;
- valid Emperor pair allocation;
- no pair across the centre aisle;
- correct tier-zone placement;
- contribution-order compliance;
- reconstructed weighted objective;
- penalty breakdown;
- actual solver status;
- movement summary for reallocation.

Do not include accessibility as a current validation rule unless it is explicitly identified as a future constraint.

---

## 9. Task 3 Discussion Guidelines

Discuss the interaction between findings.

Recommended themes:

### 9.1 Unquantified NFRs

Explain that vague NFRs affect:

- deployment decisions;
- testing;
- acceptance;
- system architecture;
- risk management.

### 9.2 Broken Traceability

Explain that incorrect identifiers prevent confirmation that:

- every goal is implemented;
- every requirement has justification;
- missing requirements can be detected;
- soft goals are operationalised.

### 9.3 Undefined Fairness

Explain that fairness must be replaced by measurable and reconstructible indicators.

### 9.4 Balance

Acknowledge strengths in:

- context analysis;
- early identification of stakeholders;
- recognition of hard and soft constraints;
- initial allocation pipeline;
- awareness of runtime and privacy risks.

---

## 10. Task 4 Reflection Guidelines

Use first-person writing because Task 4 is reflective, but maintain formal academic language.

The reflection should address:

1. major weaknesses discovered in the FYP1 proposal;
2. SRE concepts used during the review;
3. improvements to be completed before FYP2;
4. lessons learned from the assignment.

Discuss how the early proposal was useful as an initial baseline but did not yet include later stakeholder findings.

Replace:

> The proposal was not so much wrong as early.

with:

> The proposal represented an early requirements baseline that had not yet incorporated subsequent stakeholder-validation findings.

Explain how the refined planning phase changed:

- the participant role;
- participant lookup;
- publishing workflow;
- dynamic reallocation;
- movement minimisation;
- venue-specific constraints;
- evaluation criteria;
- error handling;
- plan validation;
- privacy requirements.

---

## 11. Report Structure and Formatting

The amended report must include:

1. Cover Page
2. Table of Contents
3. Task 1 — Project Summary
4. Task 2 — Requirements Analysis
5. Task 3 — Critical Requirements Review
6. Task 4 — Reflection and Improvement Plan
7. References

### Formatting Requirements

- Task 1 must fit within one page.
- The main report should remain approximately 7–9 pages where reasonably possible, excluding the cover page and references.
- List all twelve FRs individually.
- Avoid overcrowded tables.
- Move detailed argumentation from tables into prose where appropriate.
- Avoid awkward page breaks.
- Consolidate repeated arguments.
- Use no more than three numbered heading levels.
- Ensure every in-text citation appears in the references.
- Ensure every listed reference is cited in the report.

---

## 12. Required Agent Output

Produce all of the following.

## 12.1 Revised Report

Return a fully revised version of:

> `SRE-Assignment2.md`

Do not merely provide comments. Apply the amendments directly.

## 12.2 Amendment Log

Include a concise table:

| Section Changed | Original Issue | Amendment Made | Reason | Supporting Source |
|---|---|---|---|---|

## 12.3 Quality-Assurance Checklist

Confirm that:

- the refined interim report was used as the sole source of truth;
- all Assignment 2 tasks are completed;
- Task 1 fits within one page;
- all twelve original FRs are listed separately;
- participant lookup is described accurately;
- no unsupported 30-second target remains;
- no unsupported optimality-gap output remains;
- reliability and reproducibility are separate;
- accessibility is not presented as a confirmed current constraint;
- availability is labelled for stakeholder validation;
- the 400–800 figure is not treated as an operational requirement;
- all benefits are framed as expected outcomes unless already evaluated;
- the report uses formal academic language;
- citations and references were cross-checked;
- the report structure follows the assignment guideline.

---

# Final Copy-Ready Agent Instruction

```text
Amend SRE-Assignment2.md directly by following every instruction in this guideline.

Use fyp_interim-report-refined(1).md as the sole source of truth for the latest project scope, requirements, case-study details, system behaviour, evaluation criteria, and terminology.

Use SRE-Assignment1.md only as the original early-stage proposal being critically reviewed.

Use TFB3413_Software_Requirements_Engineering_Assignment_2.md to confirm the required report structure and tasks.

Use SRE-Assignment2-Report.pdf only to inspect formatting and pagination issues.

Return:
1. the complete revised SRE-Assignment2.md;
2. an amendment log;
3. a final quality-assurance checklist.

Do not introduce unsupported requirements, metrics, technical outputs, or case-study facts. Do not merely comment on the report. Apply all amendments directly.
```
