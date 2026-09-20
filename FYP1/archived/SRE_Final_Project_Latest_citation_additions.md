# Citation Additions for SRE_Final_Project_Latest.docx

Prepared as an editing checklist: each entry gives the section number, the current text (or insertion point), and the revised text with an APA 7 in-text citation added. Apply directly to the `.docx`. The compiled reference list to paste into Section 13 is at the end.

Legend: ✅ = source already verified/used elsewhere in this project (safe to reuse as-is). ⚠ = well-established, real source, but **you should verify the exact edition/URL/access date yourself** before submission, per your own project's existing citation-verification practice.

---

## Part 1 — Urgent integrity fixes (orphaned / inconsistent citations)

### 1.1 Section 3.1 — orphaned citations already in the text

**Current (line ~73):**
> "...it is a multi-criteria combinatorial assignment problem (Rossi et al., 2006; Ipsen et al., 2026)."
> "...it is infeasible to check manually by human and it is impractical for machine to enumerated it naively (Rossi et al. 2006)."

**Problem:** Rossi et al. (2006) and Ipsen et al. (2026) are cited in-text but **do not appear in your Section 13 reference list at all**. Also note the missing comma in the second instance — APA 7 requires "(Rossi et al., 2006)", not "(Rossi et al. 2006)".

**Fix:** Correct the comma, and add both full references to Section 13 (see Part 3 below).
> "...it is infeasible to check manually by human and it is impractical for a machine to enumerate it naively (Rossi et al., 2006)."

### 1.2 Section 9.1.2 — inconsistent Oryx citation label

**Current:**
> "...supporting automatic seating assignment and employing a genetic algorithm to search for strong layouts once the combinatorial space outgrows exhaustive search (Oryx Digital Ltd., n.d.-b)."

**Problem:** The "-b" suffix implies a companion "Oryx Digital Ltd. (n.d.-a)" reference exists, but it doesn't — your reference list has no Oryx entry at all, lettered or otherwise, and no other Oryx citation appears anywhere in the document.

**Fix (simplest):** Drop the suffix since only one Oryx source is used:
> "...employing a genetic algorithm to search for strong layouts once the combinatorial space outgrows exhaustive search (Oryx Digital Ltd., n.d.)."

Then add one **Oryx Digital Ltd. (n.d.)** entry to Section 13.

### 1.3 Section 9.1.1 — Cvent and PerfectTablePlan rows have no citation anywhere

**Current:** The comparison table lists Cvent, PerfectTablePlan, WeddingWire, and Zola as existing systems, but only WeddingWire and Zola ever receive an in-text citation (in the 9.1.2 narrative). Cvent is never cited at all.

**Fix:** Add one sentence immediately after the table intro line in 9.1.1:
> "The table below listed the existing seat and space allocation systems used in event planning, based on each vendor's publicly available product documentation and feature pages (Cvent, n.d.; Oryx Digital Ltd., n.d.; WeddingWire, n.d.; Zola, n.d.)."

---

## Part 2 — Section-by-section additions (novelty and credibility)

### Section 3.1 (Background of Study)

**Current (line ~79, tail):**
> "However, these solutions prioritize visualization of seat allocation, guest arrangement, and manual planning support rather than explicit fairness-driven allocation controlled by customizable weighted constraint."

**Revised:**
> "However, these solutions prioritize visualization of seat allocation, guest arrangement, and manual planning support rather than explicit fairness-driven allocation controlled by customizable weighted constraints — the kind of preference-cost representation formalized as *valued constraint satisfaction* by Schiex et al. (1995)."

*Why:* "customizable weighted constraint" is precisely the valued-CSP concept from Schiex, Fargier, and Verfaillie (1995) ✅, already used correctly in your own interim report. Citing it here shows the fairness claim is grounded in an established formalism, not an invented term.

---

### Section 4 (System Goal)

**Current:**
> "This section defines the goal model under a single identifier scheme, which decomposes the single root goal derived from the vision statement in Section 2 into a goal tree that maps the three (3) problem statements and separating hard goals from soft goals in this project."

**Revised:**
> "This section defines the goal model under a single identifier scheme, which decomposes the single root goal derived from the vision statement in Section 2 into a goal tree that maps the three (3) problem statements, following the goal-oriented requirements engineering approach of van Lamsweerde (2001), and separating hard goals from soft goals in the tradition of the Non-Functional Requirements (NFR) Framework (Chung et al., 2000)."

*Why:* Section 4.1 is literally titled "Goal Graph" and Section 4.2 splits goals into Hard/Soft — this is precisely van Lamsweerde's (2001) ⚠ KAOS goal-decomposition technique and Chung, Nixon, Yu, and Mylopoulos's (2000) ⚠ NFR Framework soft-goal model. Right now the report presents this structure as if it were invented for this project.

---

### Section 5 (System Context)

**Current:**
> "The system contexts in this project are validated during the requirement elicitation activities described in Section 9 and the contexts are categorized into the Subject Facet, Usage Facet, and IT Systems Facets along with the Development Context."

**Revised:**
> "The system contexts in this project are validated during the requirement elicitation activities described in Section 9 and the contexts are categorized into the Subject Facet, Usage Facet, and IT System Facet — the context-facet model of requirements engineering (Pohl & Rupp, 2015) — along with the Development Context."

*Why:* "Subject / Usage / IT System" facets is verbatim terminology from Pohl and Rupp's *Requirements Engineering Fundamentals* (2015) ✅ — already an established reference in your Assignment 2. This is the single highest-value fix in Section 5, since the facet names are quoted directly from that source.

---

### Section 5.5 (Consolidated Functional Requirements)

**Insertion** (one sentence before the FR table):
> "Each functional requirement below follows the mandatory *shall* / recommended *should* / optional *may* modal-verb convention prescribed for requirements specifications by ISO/IEC/IEEE 29148:2018 (ISO/IEC/IEEE, 2018), and is traced to the goal(s) it operationalizes."

### Section 5.6 (Consolidated Non-Functional Requirements)

**Insertion** (one sentence before the NFR table):
> "The non-functional requirements below follow the verifiable, fit-criterion structure for quality requirements recommended by Wiegers and Beatty (2013), under the same modal-verb discipline of ISO/IEC/IEEE 29148:2018 (ISO/IEC/IEEE, 2018)."

*Why:* ISO/IEC/IEEE 29148:2018 ✅ and Wiegers & Beatty (2013) ✅ are both already-used references from your Assignment 2 — reintroduce them here since this report reuses their exact requirement-writing conventions without saying so.

---

### Section 6 (RE Analysis Modelling)

**6.1 Use Case Diagram — insertion before the diagram description:**
> "The use case diagram (Figure 5) follows Unified Modeling Language use case notation (Object Management Group [OMG], 2017), identifying the Event Administrator and Event Participant as the primary actors of the intelligent seating allocation system."

**6.3 System State Machine Diagram — current opening:**
> "The system state machine diagram above demonstrated the life of one seating allocation session in the seat allocation solver function."

**Revised:**
> "The system state machine diagram above, drawn using UML state machine notation (OMG, 2017), demonstrated the life of one seating allocation session in the seat allocation solver function."

**6.4 Class Diagram — current (tail):**
> "The solver function engine-side SolverEngine and ConstraintModelBuilder are cleanly separated from the domain and artifact classes by implementing the Builder design pattern, so that the model's builder operations are concrete realization of the constraint model, but not a property of the domain data."

**Revised:**
> "The solver function engine-side SolverEngine and ConstraintModelBuilder are cleanly separated from the domain and artifact classes by implementing the Builder design pattern (Gamma, Helm, Johnson, & Vlissides, 1994), so that the model's builder operations are a concrete realization of the constraint model rather than a property of the domain data."

*Why this one matters most in Section 6:* you **explicitly name** "the Builder design pattern" — a specific, well-known software-engineering pattern with one canonical source (Gamma, Helm, Johnson, & Vlissides, 1994 — the "Gang of Four" *Design Patterns* book) ⚠. Naming a named pattern without citing its source is one of the clearest plagiarism-adjacent gaps in the whole report.

**6.5 Swimlane Diagram — this subsection currently has a heading but no descriptive paragraph. Suggested insertion:**
> "The swimlane diagram (Figure 7) adopts the swimlane / cross-functional flowchart notation originally proposed by Rummler and Brache (1990) to allocate each activity in the Generate Seating Plan use case to its responsible lane — the Event Administrator, the Event Management Platform, and the Seat Allocation Engine — making explicit which actor or component owns each step of plan generation."

*Why:* Rummler and Brache (1990) ⚠ are the originating source for the swimlane/"white space on the organization chart" technique.

---

### Section 7.1 (Agile SCRUM)

**Current:**
> "This final year project implemented the Agile software development methodology, specifically the SCRUM framework together with the Netizen eXperience assigned industry supervisor, Mr. Cheah Poh Xiang. Based on the Figure 8 above, each sprint in Agile SCRUM framework consists of four SCRUM ceremonies including the Sprint Planning for backlog brainstorming and task effort estimation, followed by Daily Standup Meeting for ongoing progress synchronization, and closed by a Sprint Review to demonstrate the developed increment..."

**Revised:**
> "This final year project implemented the Agile software development methodology, specifically the SCRUM framework (Schwaber & Sutherland, 2020), together with the Netizen eXperience assigned industry supervisor, Mr. Cheah Poh Xiang. Based on the Figure 8 above, each sprint in the Agile SCRUM framework consists of four SCRUM ceremonies as defined in the official Scrum Guide (Schwaber & Sutherland, 2020) — Sprint Planning for backlog brainstorming and task effort estimation, followed by the Daily Standup Meeting for ongoing progress synchronization, and closed by a Sprint Review to demonstrate the developed increment..."

*Why this is the single highest-priority fix in the whole report:* SCRUM is a **named, trademarked methodology** (the ceremonies, cadence, and roles you describe in detail are defined verbatim in Schwaber & Sutherland's official Scrum Guide, 2020 ✅ — already used correctly in your interim report), and right now it carries **zero citation** anywhere in this section.

---

### Section 7.2 (Software Architecture Diagram)

**Current opening:**
> "The proposed intelligent seating allocation system in this project adopts a four-layer architecture that separates the actors who use the system from the internal or external software that they interact with..."

**Revised:**
> "The proposed intelligent seating allocation system in this project adopts a four-layer architecture — consistent with the layered architecture pattern commonly used to separate presentation, application, compute, and data concerns in distributed systems (Richards, 2015) — that separates the actors who use the system from the internal or external software that they interact with..."

**Later in the same paragraph (AWS services):**
> "...an AWS Lambda function hosts the core seating allocation engine and its embedded Google OR-Tools CP-SAT solver function (Amazon Web Services, n.d.-a; Google, n.d.)... comprising Amazon DynamoDB to store event, participant, and allocation metadata... Amazon S3 is also being deployed to Data Layer to store the versioned seating-plan result JSON (Amazon Web Services, n.d.-b)..."

*Why:* Amazon Web Services (n.d.-a/-b) ✅ and Google (n.d.) ✅ are already-established citations from your interim report; Richards (2015) ⚠ is the standard reference for the layered-architecture pattern by name.

---

### Section 7.3 (Methods and Technologies Adopted)

**Insertion** (a narrative paragraph after the table — currently this section is only a bare table with no supporting text):
> "Google OR-Tools CP-SAT is selected as the solving engine because it accepts integer decision variables, Boolean indicators, and conditional constraints through reification and channeling, and reports explicit solver statuses that this project surfaces as part of allocation quality (Google, n.d.). This selection is further grounded in the primary technical literature describing CP-SAT's lazy-clause-generation architecture, which combines SAT-style conflict-driven clause learning (Stuckey, 2010) with linear-programming relaxation bounds and portfolio parallel search (Perron & Didier, 2023) — an architecture specifically designed to prune search spaces of this project's scale while still proving optimality, a guarantee bespoke greedy or metaheuristic approaches cannot offer."

*Why:* Google (n.d.) ✅, Stuckey (2010) ✅, and Perron & Didier (2023) ✅ are all sources this project already downloaded and verified (see `academic/research-papers/` and `literature_review_seating_allocation.md`). Right now Section 7.3 states a technology choice with zero justification or citation — the single biggest missed opportunity to demonstrate technical credibility.

---

### Section 9.1 (Literature Review) — the biggest content gap

Your Section 9.1 is titled "Literature Review" but currently contains **only a commercial-tool comparison table** — no academic paper is cited anywhere in it. This is the strongest opportunity to raise the report's novelty claim, since your own project already has four downloaded, relevant academic papers sitting unused (`academic/research-papers/`).

**Suggested insertion — a new paragraph at the very start of Section 9.1, before the 9.1.1 heading:**
> "Beyond commercial event-planning software, a thin but directly relevant body of academic literature addresses seating and spectator allocation as a combinatorial optimization problem. Ipsen et al. (2026) formalize the Hierarchical Seating Allocation Problem for organizational office seating, decomposing the assignment into per-level sub-problems and showing that a warm-started local search which repairs only the seats near an existing incumbent is a practical mechanism for keeping successive plans stable — a precedent this project's own movement-minimizing reallocation objective (Objective 2) follows. Muñoz et al. (2005) address ticket-to-seat allocation for a Formula 1 Grand Prix using a region-growing heuristic and an explicit split between mandatory and optional distribution rules, a hard/soft rule structure that independently mirrors the constraint classification adopted in this project (Section 11.2). Sun (2020) contributes a combinatorial model of aisle-interrupted row geometry that corroborates, from a distinct mathematical angle, this project's treatment of the centre aisle as a structural break in physical seat adjacency rather than an ordinary seat gap. None of these three works, however, combines a general-purpose constraint solver, a provable optimality guarantee, and a stability-preserving reallocation mechanism in one system — the combination this project delivers using Google OR-Tools CP-SAT (Google, n.d.; Perron & Didier, 2023), a solver built on the lazy clause generation paradigm (Stuckey, 2010) that natively expresses PJKIT's tier, pairing, and ordering rules as integer and Boolean constraints without hand-compiled linearization."

*Why:* Ipsen et al. (2026) ✅, Muñoz et al. (2005) ✅, and Sun (2020) ✅ are the exact three seating-allocation papers whose PDFs already sit in `academic/research-papers/` and whose annotated summaries already exist in `academic/literature_review_seating_allocation.md`. This single paragraph converts your "Literature Review" section from a commercial-tool table into an actual academic literature review, which is what raises the novelty argument the most.

---

### Section 9.3 (Joint Application Development Workshop)

**Current:**
> "At the same day, a joint application development (JAD) workshop is carried out between the FYP student, Industry Supervisor - Mr. Cheah Poh Xiang and three (3) representatives including the head of administrator that handle on event seating allocation from PJKIT side to brainstorm, discuss and refine the requirement for the proposed intelligent seating allocation system."

**Revised:**
> "At the same day, a Joint Application Development (JAD) workshop (Wood & Silver, 1995) is carried out between the FYP student, Industry Supervisor — Mr. Cheah Poh Xiang — and three (3) representatives, including the head of administrator that handles event seating allocation from the PJKIT side, to brainstorm, discuss, and refine the requirements for the proposed intelligent seating allocation system."

*Why:* JAD is a specifically named, formal elicitation technique with a canonical source (Wood & Silver, 1995) ⚠. Naming it without a citation understates that you applied a recognized RE method rather than an ad hoc meeting.

---

### Section 11.1 (Preliminary Findings — CP-SAT suitability row)

**Current (tail of the last table row):**
> "...are expressible as a pure-integer that could be used by the CP-SAT model to solve the seating allocation problem and generate a seating plan result within the configured time budget, the independently implemented validator confirms zero hard-constraint violations and reconstructs the reported objective value exactly, and repeated runs reproduce the identical canonical plan"

**Revised:**
> "...are expressible as a pure-integer model natively supported by CP-SAT's lazy-clause-generation architecture (Perron & Didier, 2023; Stuckey, 2010), which solves the seating allocation problem and generates a seating plan result within the configured time budget; the independently implemented validator confirms zero hard-constraint violations and reconstructs the reported objective value exactly, and repeated runs reproduce the identical canonical plan."

---

### Section 12 (Conclusion) — optional but recommended

**Current:**
> "The literature review demonstrated that neither commercial tooling nor the published seating-allocation literature offers this combination which related to a declaratively configurable, status-reporting, and stability-aware seating allocation engine."

**Revised:**
> "The literature review demonstrated that neither commercial tooling (Cvent, n.d.; Oryx Digital Ltd., n.d.; WeddingWire, n.d.; Zola, n.d.) nor the published academic seating-allocation literature (Ipsen et al., 2026; Muñoz et al., 2005; Sun, 2020) offers this combination, which is a declaratively configurable, status-reporting, and stability-aware seating allocation engine."

*Why:* your novelty claim in the conclusion is currently unsupported by any citation — this is where the "gap in the literature" argument is supposed to land, and right now it lands with nothing behind it.

---

## Part 3 — Compiled Reference List (paste into Section 13, replacing the current two-entry list)

Sorted alphabetically, APA 7. ✅ = already verified/used in this project's earlier reports; ⚠ = real, well-established source, but confirm the exact edition, DOI, and access date yourself before submission (the same discipline your interim report already applies to its own reference list).

Amazon Web Services. (n.d.-a). *What is AWS Lambda?* AWS Documentation. Retrieved June 2026, from https://docs.aws.amazon.com/lambda/latest/dg/welcome.html ✅

Amazon Web Services. (n.d.-b). *Invoke — AWS Lambda API reference*. AWS Documentation. Retrieved June 2026, from https://docs.aws.amazon.com/lambda/latest/api/API_Invoke.html ✅

Chung, L., Nixon, B. A., Yu, E., & Mylopoulos, J. (2000). *Non-functional requirements in software engineering*. Springer. ⚠

Cvent. (n.d.). *Event diagramming and seating*. Retrieved June 2026, from https://www.cvent.com ✅

Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley. ⚠

Google. (n.d.). *CP-SAT solver*. Google for Developers — OR-Tools. https://developers.google.com/optimization/cp/cp_solver ✅

Ipsen, A., Cashmore, M., Fielding, K., Marchesotti, N., Zehtabi, P., Magazzeni, D., & Veloso, M. (2026). *Beyond manual planning: Seating allocation for large organizations*. arXiv:2602.05875. https://arxiv.org/abs/2602.05875 ✅

ISO/IEC/IEEE. (2018). *Systems and software engineering: Life cycle processes. Requirements engineering* (ISO/IEC/IEEE 29148:2018). International Organization for Standardization. ✅

Muñoz, V., Montaner, M., & López, B. (2005). *Seat allocation for massive events based on region growing techniques*. Universitat de Girona. ✅

Object Management Group. (2017). *OMG Unified Modeling Language (OMG UML), version 2.5.1*. https://www.omg.org/spec/UML/2.5.1/ ⚠

Oryx Digital Ltd. (n.d.). *Using a genetic algorithm for table seating*. PerfectTablePlan. Retrieved June 2026, from https://www.perfecttableplan.com ✅

Perron, L., & Didier, F. (2023). The CP-SAT-LP solver (invited talk). In *Proceedings of the 29th International Conference on Principles and Practice of Constraint Programming (CP 2023)* (Article 3). Schloss Dagstuhl – Leibniz-Zentrum für Informatik. https://doi.org/10.4230/LIPIcs.CP.2023.3 ✅

Pohl, K., & Rupp, C. (2015). *Requirements engineering fundamentals* (2nd ed.). Rocky Nook. ✅

Richards, M. (2015). *Software architecture patterns*. O'Reilly Media. ⚠

Rossi, F., van Beek, P., & Walsh, T. (Eds.). (2006). *Handbook of constraint programming*. Elsevier. ✅

Rummler, G. A., & Brache, A. P. (1990). *Improving performance: How to manage the white space on the organization chart*. Jossey-Bass. ⚠

Schiex, T., Fargier, H., & Verfaillie, G. (1995). Valued constraint satisfaction problems: Hard and easy problems. In *Proceedings of the 14th International Joint Conference on Artificial Intelligence (IJCAI-95)* (pp. 631–639). Morgan Kaufmann. ✅

Schwaber, K., & Sutherland, J. (2020). *The Scrum guide: The definitive guide to Scrum — The rules of the game*. Scrum.org. https://scrumguides.org ✅

Stuckey, P. J. (2010). Lazy clause generation: Combining the power of SAT and CP (and MIP?) solving. In A. Lodi, M. Milano, & P. Toth (Eds.), *Integration of AI and OR techniques in constraint programming for combinatorial optimization problems* (CPAIOR 2010, LNCS 6140, pp. 5–9). Springer. https://doi.org/10.1007/978-3-642-13520-0_3 ✅

Sun, S. (2020). Mathematical model of seat arrangement in large gymnasium. *IOP Conference Series: Materials Science and Engineering*, *806*, 012013. https://doi.org/10.1088/1757-899X/806/1/012013 ✅

van Lamsweerde, A. (2001). Goal-oriented requirements engineering: A guided tour. In *Proceedings of the Fifth IEEE International Symposium on Requirements Engineering (RE'01)* (pp. 249–262). IEEE. https://doi.org/10.1109/ISRE.2001.948567 ⚠

WeddingWire. (n.d.). *Wedding seating chart tool*. https://www.weddingwire.com/wedding-planning/wedding-seating-tables.html ✅ (already present)

Wiegers, K., & Beatty, J. (2013). *Software requirements* (3rd ed.). Microsoft Press. ✅

Wood, J., & Silver, D. (1995). *Joint application development* (2nd ed.). John Wiley & Sons. ⚠

Zola. (n.d.). *Wedding seating chart: Seat all your guests in minutes*. https://www.zola.com/wedding-planning/seating-chart ✅ (already present)

> **Note (matching the disclaimer style your own interim report already uses):** Verify each URL, edition, and access date against the source you actually consult before submission. Items marked ⚠ are real, well-established, commonly cited works, but were not re-fetched or re-verified during this editing pass — confirm exact publication details before the final submission. The Ipsen et al. (2026) arXiv identifier reflects the metadata on the PDF already stored in this project's `academic/research-papers/` folder.

---

## Priority order if you have limited time

1. **Must fix (integrity risk):** Part 1 — orphaned Rossi/Ipsen/Oryx citations, missing Cvent citation.
2. **High value, low effort:** SCRUM citation (7.1), Builder pattern citation (6.4), context-facets citation (5).
3. **Highest novelty payoff:** the Section 9.1 literature paragraph (Ipsen/Muñoz/Sun/CP-SAT) — this single paragraph does the most to demonstrate research grounding.
4. **Polish:** goal-model citations (Section 4), UML/JAD/swimlane citations (Section 6, 9.3), architecture citations (7.2/7.3).
