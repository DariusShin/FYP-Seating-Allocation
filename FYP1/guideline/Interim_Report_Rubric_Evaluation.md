# Interim Report Evaluation Against UTP FORM 08 Rubric

**Evaluated artifact:** `draft_interim_report_ai_ready.md` (extraction of `Draft_Interim_Report_To_GPT.pdf`, 46 pages)
**Rubric:** UTP-ACA-PROG-FYP-01.08a/b, Appendix 3-8 FORM 08, FYP I Interim Report (Total 85 marks)
**Also considered:** `Literature_Review_Comment.md`, `Literature_Review_Response_Roadmap.md`, elicitation results in Appendix B

**Confirmed ground truth used throughout this evaluation** (per your instruction and Appendix B):
- Venue is 16 rows × 16 seats = 256 seats; 8 seats per side of the centre aisle, so the aisle falls between positions 8 and 9; 232 seats assignable after the 24-seat structural block.
- Contribution tier order is **fixed** as Emperor → Merit → Bodhi from the front of the hall.
- A boundary row **may** be shared between two adjacent tiers (elicitation A-C10).

---

## 1. Headline findings

Three findings dominate everything else, and all three are about **missing or unwritten content rather than wrong content**:

1. **There is no Abstract.** The rubric allocates a dedicated criterion to it (×1, 5 marks) and names four required elements: problem statement, objective, methodology, future work. An absent abstract scores "Very Weak (1)" — costing roughly 4 marks for perhaps 250 words of writing. This is the cheapest mark recovery available to you.

2. **There is no Scope of Study section.** The rubric has a dedicated criterion, "Scope of Study, including relevancy and feasibility" (×1, 5 marks). Section 1.5 (System Goal and Requirements) is excellent content but answers a *different* question — it specifies requirements, not scope boundaries and feasibility. The five-module scope from `fyp_interim-report-refined.md` §1.4 was dropped in this draft and needs restoring.

3. **Section 4.2 Future Work is unwritten** — it currently reads "Next module or things to do in FYP2….". The Conclusion criterion is ×2 (10 marks) and is explicitly *"Summary of project progress **and future work**"*; the "Very Weak" descriptor is literally "No future work recommended." Section 3.4 is likewise an unfilled placeholder reading "Write the explantion".

Beyond these, the two content-quality issues that will cost the most marks are the **literature review's compression** (the per-study critical analysis that existed in the refined report was collapsed into a single paragraph — and this is the largest single criterion at ×4 = 20 marks) and the **broken cross-references and citation errors** throughout, which the ×4 criterion explicitly names ("with proper cross referencing").

---

## 2. Your specific question: is the combinatorial/space-complexity claim misleading?

**Yes — the interpretation is wrong, though the arithmetic is right.** This is worth understanding precisely, because it is the justification for your entire method choice.

### What the draft currently says (§1.2, repeated in §2.3)

> "…even in the simplified case where each of the case study's 150 participants assigned a single seat among a venue that can support up to 232 seats, the number of possible ordered seat assignments is denoted as 232!/(232 − 150)! approximately 8.75 × 10³²⁶ … which is infeasible to check manually by human and it is impractical for machine to enumerated it naively (Rossi et al., 2006)."

### Why this is a problem

The arithmetic checks out — 232!/82! is indeed approximately 8 × 10³²⁶, so that figure is fine. The problem is the inference drawn from it.

**A large search space does not imply computational hardness.** The counter-example is the classical **linear assignment problem**: assigning *n* agents to *n* tasks with additive costs also admits *n*! candidate solutions, and yet it is solved in **polynomial time**, O(n³), by the Hungarian algorithm (Kuhn, 1955). If a factorial search space were sufficient evidence of intractability, the Hungarian algorithm could not exist. So as written, the paragraph proves only that *naive enumeration* is impractical — and nobody proposes naive enumeration. An examiner who knows this can say, in one sentence, *"your own argument does not rule out a polynomial-time assignment algorithm; why do you need a constraint solver at all?"* — and the current text gives you no answer.

The clause **"impractical for machine to enumerate it naively"** is the specific phrase that makes this a strawman. It defeats an approach no one would use, while leaving the real question untouched.

### What actually makes the PJKIT problem hard

The hardness comes from **structure, not size** — specifically from the constraints that take the problem outside the linear-assignment class:

| Structural feature | Why it breaks linear assignment |
|---|---|
| Emperor two-seat units (C10, C11) | An allocation unit consumes an adjacent *pair*, making this a matching/packing problem rather than a one-to-one assignment. Pair validity is also position-dependent (never straddling positions 8/9). |
| Within-tier contribution ordering (C13) | Introduces precedence coupling *between* participants; cost is no longer separable per participant–seat pair, which is the precondition for the Hungarian method. |
| Demand-derived tier bands with shared boundary rows (C12) | The band boundaries are themselves decision-dependent rather than fixed input — arguably the most interesting feature of your problem, and currently the least emphasized. |
| Front-to-back packing and centre-out fill (C15, C16) | Contiguity/no-gap requirements, which are global structural constraints, not per-assignment costs. |
| Weighted multi-criteria objective (C6–C9) | Competing soft terms requiring simultaneous arbitration. |

### Recommended replacement argument

Keep the factorial, but **repurpose it** — it is a perfectly good illustration of why *a human allocator* cannot exhaustively verify a plan by hand, which directly supports Problem Statement 1. Then add a separate, correctly-framed hardness sentence. The citation path is already inside a source you cite: **Ipsen et al. (2026) state that the seating allocation problem is a special case of the capacitated p-median problem, which is NP-hard**, citing Mu & Tong (2019). Replacement wording is supplied in the companion file `revised_section2_literature_review.md` (see §2.6 there and the §1.2 replacement paragraph at the end of that file).

The corrected version is *stronger*, not weaker: it converts a claim an examiner can dismantle into one that positions your structural constraints as the actual research interest.

### Two accompanying number problems in the same paragraph

- **150 vs 122.** Section 1.2 and §2.3 use **150 participants**; NFR1 and NFR6 use **122 registrations**; MG1, §3.5.2, and the Conclusion say **100–200**. Pick one canonical validated figure and use it everywhere. If you switch to 122, the factorial becomes 232!/110! ≈ 10²⁷¹, not 10³²⁶ — so the number must be recomputed, not just carried over.
- **The numbered-vs-free-seating section is never quantified.** Elicitation B4 and constraint C15 establish that only a *numbered front section* is solver-allocated, with a free-seating section behind it. The solver's seat pool is therefore **smaller than 232**, and the report never says how much smaller. This affects the complexity statement, the tier-band capacity validation (FR15), and NFR6's scalability baseline. Determine and state the numbered-section size.

---

## 3. Is the literature review sufficient?

**It is passable but currently under-performing relative to the marks at stake.** At ×4 (20 marks) it is the single largest criterion on the form, and the draft has *regressed* from the refined report in the way that matters most to that criterion.

### What was lost in compression

In `fyp_interim-report-refined.md`, §2.1 gave each academic work its own paragraph with an explicit "relevance to this project" analysis, and closed with a dedicated **"Gap identified"** paragraph deriving the research gap from the reviewed works. In this submission draft, all four academic works are compressed into **one opening paragraph of Section 2**, with no subsection heading of their own, no critique of each work's limitations, and no derivation of the gap.

The rubric's "Very Good (5)" descriptor asks for work that *"critically analyse previous work relevant to current studies, with proper cross referencing. Clearly established the importance of the current work."* One descriptive paragraph does not read as critical analysis, and the gap is now **asserted rather than derived** — in a sentence that is also grammatically broken:

> "By combines a general-purpose constraint solver, a provable optimality guarantee, and a stability-preserving reallocation mechanism in one system that this project delivers using Google OR-Tools CP-SAT…"

This sentence simultaneously (a) does not parse, (b) states the gap claim in unhedged absolute form — exactly what `Literature_Review_Comment.md` warned against — and (c) never says what the reviewed works *fail* to do, so the claim rests on nothing. Fixing this one sentence is high-value.

### Recentness is a scoring risk

The criterion is explicitly named *"…and **recentness** of literature."* Current academic sources: Muñoz et al. (2006), Rossi et al. (2006), Schiex et al. (1995, missing from the reference list), Stuckey (2010), Sun (2020), Perron et al. (2023), Ipsen et al. (2026). Only **two** sources are from the last five years, and Ipsen et al. is an **arXiv preprint, not peer-reviewed** — which also affects the "Quality of references" criterion. The remedy identified in the roadmap still applies and is cheap: mine Ipsen et al.'s own reference list for **Hales & García (2019)** on legislative-chamber seat allocation (peer-reviewed, in *TOP*, and contextually the closest published analogue to a community assembly), **Barry et al. (2021)** on social-distancing seat allocation, and **Stoll (2022)** on distance-constrained cinema seating.

### Objective 2's literature support remains the thinnest

Objective 2 is now well-defined operationally (PS2 correctly frames it as a *repair* problem; FR9 and G2.1 are precise). But its literature support is still one paragraph of Ipsen et al. plus Hoang (2022) — and **Hoang (2022) is cited in §2.5 and does not appear in the reference list at all.** As the roadmap set out, your incremental-repair-with-progressive-expansion mechanism *is* two named techniques with established literature: **Large Neighbourhood Search** (Shaw, 1998) and the **Minimal Perturbation Problem** (El Sakkout & Wallace, 2000; and the course-timetabling line of work by Müller, Rudová & Barták, which is a near-exact structural analogue — a published timetable absorbing a late change with minimum disruption). Naming them converts your escalation ladder from something invented into something principled, and it is the most substantive improvement available to Section 2.

### Verdict

Sufficient to pass; not yet scoring in the top band. A revised Section 2 implementing the roadmap is provided in `revised_section2_literature_review.md`, structured as eight subsections rather than five, with the academic analysis restored, the search strategy added, the gap hedged and derived, the complexity argument corrected, and the system review broadened by category.

---

## 4. Citation and cross-reference defects

These matter twice — the ×4 criterion names "proper cross referencing," and the ×2 criterion assesses reference quality directly.

### Cited in text but absent from the reference list

| Citation | Where cited |
|---|---|
| Hoang (2022) | §2.5 |
| Schiex et al. (1995) | §2.3 |
| Williams (2013) | §2.4, ILP/MIP table row |
| OMG (2017) | §3.2.1, §3.2.3 |
| Google, n.d.-a | §2.4 selection rationale — key matches no list entry |

### In the reference list but never cited

- **Pohl & Rupp (2016)** — appears in the list, cited nowhere in the text.

### Incorrect or garbled reference details

- **Ipsen et al. (2026)** is listed with the journal *"Open MIND"* and an arXiv DOI. It is an arXiv preprint; "Open MIND" appears to be a reference-manager artifact. Also state it is a preprint.
- **Muñoz et al.** — the list gives the third author as *"Esteva, Peplluis"*. The retrieved paper's authors are **Víctor Muñoz, Miquel Montaner and Beatriz López** (Universitat de Girona). Verify which version you are citing and correct the author list.
- **Muñoz year is inconsistent:** cited as 2006 in the Section 2 opening and the Conclusion, but 2005 in §2.5; the list says 2006.
- **Perron et al. (2023)** — in-text alternates between "Perron et al., 2023" and "Perron & Didier, 2023". Fix to one form and verify whether Gay is a listed author on the CP 2023 paper.
- **"CP-SAT Solver. (n.d.)"** has no URL, and is used for two distinct Google pages — the CP-SAT solver page *and* the channeling-constraints page (§2.3). The channeling source was lost when merging from the refined report; restore it as a separate entry.
- **Oryx Digital Ltd. (n.d.)** entry contains a stray "c" before the URL.
- **Reference list is not alphabetical** (APA 7 requires it): "Invoke" is filed after "Ipsen" (should precede it), Stuckey is filed under "Peter", Muñoz appears after Rossi, and "What is AWS Lambda" appears before Schwaber.

### Broken internal cross-references

| Says | Should be |
|---|---|
| §1.3: "background of study in Section 3.1" | Section 1.2 |
| §1.5: "vision statement in Section 2" | Section 1.1 |
| §2 opening and §4.1: "Section 11.2" | Does not exist — the Conclusion promises rules "formalized in Section 11.2" that the report never formalizes anywhere |
| §2.3: "requirement-validation cycle described in Section 3.5" | Verify — §3.5 is Preliminary Works |
| §3.1: "Based on the Figure 8 above" | Figure 3 |
| §3.2.4: "Based on Figure 9 above" | Figure 7 |
| §3.5.2: "(Section 9)" | Does not exist |
| §3.6.1 "Figure 3", §3.6.2 "Figure 4" | Duplicate numbers already used for the SCRUM and use-case figures — renumber all figures sequentially |

---

## 5. Section-by-section comments against each rubric criterion

### 5.1 ABSTRACT — ×1 (5 marks)

**Absent.** Write approximately 200–300 words covering the four named elements in order: the problem (manual multi-criteria seating allocation at PJKIT, 100–200 participants, 256-seat venue, tier and pairing rules, disruptive late changes, printed-list seat retrieval); the objectives (configurable constraint-based engine; incremental repair mechanism; participant lookup); the methodology (COP modelling with hard and weighted soft constraints, CP-SAT on AWS Lambda, Agile SCRUM with Netizen eXperience, elicitation via interview and JAD workshop); and future work (FYP 2 development, integration, evaluation against baselines). Add 5–6 keywords.

### 5.2 INTRODUCTION — Background of Study and Problem Statement — ×2 (10 marks)

**Estimated: Good (4).** The content is genuinely strong — the PJKIT context is concrete, the tier structure and manual workflow are described from real observation, and the three problem statements are clearly delineated and non-overlapping. PS2's framing of reallocation as a *repair* problem rather than a regeneration problem is a real improvement over the earlier draft.

Holding it back from "Very Good (5)", which requires *"well written, articulate and concise"*:

- **The complexity claim** (§2 above) sits in the opening paragraph and is the first substantive technical assertion an examiner reads.
- **The 150 vs 122 inconsistency.**
- **Language errors** at a density that will be noticed. In the extraction I count: "organized large annual community events that consisted of" (tense), "participant records are first store" (stored), "the created seating plan will then be will convert into PDF" (double auxiliary), "Whole WeddingWire and Zola offer" (While), "impractical for machine to enumerated it" (to enumerate), "PJKIT''s annual event venue layout" (double apostrophe, in a figure caption), "error -prone" (stray space), "the seating row could be shred between two different tiers" (shared), "sire visit" (site visit), "single stagble resting state" (stable), "TIEMOUT" (TIMEOUT), "propsoed" (proposed), "is a to develop" (§4.1). Several `Ã`/`â` sequences appear where `×`, `→` and `ñ` should be — verify whether these are PDF-extraction artifacts or present in your source document; if the latter, they are a serious presentation problem.
- **§1.2's commercial-tool paragraph pre-empts Chapter 2.** Consider trimming it to one sentence and letting the literature review carry it.

### 5.3 INTRODUCTION — Objective — ×2 (10 marks)

**Estimated: Good (4).** Three objectives, clearly stated, each mapping cleanly onto one problem statement — the traceability is explicit and correct. Objective 2's wording ("treating the latest published plan as the baseline state and modifying only the affected seats") is precise and now properly distinct from Objective 1.

To reach the top band, the rubric additionally requires objectives *"justified towards answering the problem statement, and achievable within the time frame"*:

- Add one sentence per objective, or a short paragraph after the three, stating the measurable criterion by which each will be judged and cross-referencing NFR1 (the 60-second OPTIMAL criterion) and G2.1. You already have these criteria — they are simply not visible from the objectives.
- Add an explicit feasibility sentence tying the objectives to the 28-week schedule in §3.7, since "achievable within the time frame" is named in the descriptor.
- Objective 1 currently omits any mention of the solution method and of the measurable outputs (solver status, penalty breakdown). Naming the COP formulation and CP-SAT would strengthen the justification.

### 5.4 INTRODUCTION — Scope of Study, relevancy and feasibility — ×1 (5 marks)

**Absent as a distinct section.** §1.5's goal tree and requirements are strong content but answer a different rubric line, and the rubric criterion here is specifically about scope, relevancy and feasibility. Restore a Scope of Study subsection covering the five modules (solver engine; admin management with versioned publishing; participant lookup; configurable constraint allocation; incremental dynamic reallocation), state explicitly what is **out of scope** (authentication implementation, venue-layout drawing tools, generalization to other organizers, GA benchmarking), and close with a feasibility paragraph. Explicit exclusions score well against "relevancy and feasibility" because they demonstrate deliberate bounding.

### 5.5 LITERATURE REVIEW — Critical analysis, relevancy and recentness — ×4 (20 marks)

**Estimated: Fair to Good (3–4).** Assessed in detail in §3 above. The white-space analysis (§2.2) and the method comparison (§2.4) are comparative and analytical and read well. The weaknesses are the compression of the academic literature into one paragraph, the absent gap derivation, the unhedged and ungrammatical gap sentence, thin recentness, and the broken cross-references the descriptor explicitly names. Use `revised_section2_literature_review.md`.

### 5.6 LITERATURE REVIEW — Quality of references — ×2 (10 marks)

**Estimated: Fair (3).** The descriptor for the top band is *"Sufficient references all are relevant, and almost all from published journal / references."* Currently, of 15 listed references, roughly 6 are vendor product pages or AWS documentation, one key academic source is an unrefereed preprint, four cited works are missing from the list entirely, one listed work is never cited, and there are author, venue and alphabetization errors (§4 above). Fixing the missing and garbled entries and adding 3–5 peer-reviewed sources should move this to Good or Very Good — this is a mechanical fix worth several marks.

### 5.7 METHODOLOGY — Research methodology and Project Activities — ×2 (10 marks)

**Estimated: Good (4).** This is the strongest chapter in the draft. §3.1's SCRUM description is concrete and credible — named industry supervisor, actual ceremony days and times, two-week sprint cadence, and correct grounding in Schwaber & Sutherland (2020). §3.2's design suite is comprehensive (use case plus a full use-case description table with main success scenario and extensions, flowchart, UML state machine, layered architecture, class diagram, swimlane). §3.5's preliminary works are genuinely evidential: a dated site visit (26 June 2026), a JAD workshop with three PJKIT representatives, elicitation questionnaires in Appendix A and results in Appendix B, and a 17-rule constraint listing. **The elicitation evidence is the single most persuasive material in the report** — an examiner reading Appendix B can see the requirements came from real stakeholders.

Gaps preventing the top band:

- **§3.4 "Seating Allocation Optimization Lifecycle" reads "Write the explantion."** An unfilled placeholder in a submitted document is damaging out of proportion to its size.
- **No evaluation or testing methodology.** The refined report's evaluation section (datasets, baselines, metrics, 10-run protocol, per-objective success criteria, threats to validity) is absent. The rubric asks whether activities are *"relevant to achieving the objectives"* — without an evaluation design there is no stated means of demonstrating achievement. Given that greedy, random and FCFS baselines are already named in §2.4, and that `refine-objective2.md` §14 already specifies Objective 2 metrics (affected-participant accommodation rate, unaffected participants moved, movement distance, full-regeneration avoidance rate), this section can be assembled quickly from material you already have.
- **No mathematical formulation.** §2.3 discusses constraint modelling theory but the report never formalizes the model, while §4.1 refers to rules "formalized in Section 11.2" — promising a formalization that does not exist. Even a half-page sketch of decision variables, hard constraints and the objective would close this, and it is the core of your claimed contribution.
- Deployment-risk analysis (Lambda time budget, cold start with the OR-Tools binary, payload limits) and the PDPA/data-protection paragraph were both dropped. NFR5 gestures at privacy; the methodology does not support it.

### 5.8 METHODOLOGY — Project milestone and timeline (Gantt chart, both semesters) — ×1 (5 marks)

**Cannot fully verify — likely Good (4), at risk.** The descriptor requires charts *"for both semesters."* §3.7.1 (FYP 1) appears to have an embedded chart; §3.7.2 (FYP 2) has a heading and explanatory prose, but I cannot confirm a second chart image is present. **Verify before submission that both charts are embedded and legible at print size**, that the two fixed academic milestones (interim report submission; viva and dissertation) are marked, and that sprint boundaries are visible so the chart is consistent with the SCRUM methodology described in §3.1. A missing FYP 2 chart drops this criterion to "Weak" or "Very Weak."

### 5.9 CONCLUSION — Summary of project progress and future work — ×2 (10 marks)

**Estimated: Weak to Fair (2–3), entirely because of §4.2.** §4.1 is a competent summary that recaps the problem, the venue and rule structure, the literature position and the contribution. Two defects: "The contribution of this project is a to develop a configurable…" does not parse, and the reference to "Section 11.2" is broken.

**§4.2 must be written.** It currently reads "Next module or things to do in FYP2….". Draw on material you already have: completion of the COP formulation and the full constraint model; the incremental repair mechanism with progressive neighbourhood expansion per `refine-objective2.md`; Lambda deployment with cold-start benchmarking; platform integration (admin dashboard and participant lookup); execution of the evaluation plan with baseline comparison; validation on real PJKIT event data; and beyond-FYP extensions (GA benchmark, richer layouts, generalization to other organizers on the platform). This is roughly 250 words for approximately 4 marks.

---

## 6. Estimated score and recovery

| Rubric criterion | Mult. | Max | Current estimate | After recommended fixes |
|---|---:|---:|---:|---:|
| Abstract | ×1 | 5 | 1 (absent) | 4–5 |
| Background of study and problem statement | ×2 | 10 | 8 | 10 |
| Objective | ×2 | 10 | 8 | 10 |
| Scope of study, relevancy and feasibility | ×1 | 5 | 1–2 (absent) | 4–5 |
| Literature review — critical analysis, relevancy, recentness | ×4 | 20 | 12–16 | 16–20 |
| Literature review — quality of references | ×2 | 10 | 6 | 8–10 |
| Methodology — research methodology and project activities | ×2 | 10 | 8 | 10 |
| Project milestone and timeline (Gantt, both semesters) | ×1 | 5 | 4 (verify) | 5 |
| Conclusion — summary of progress and future work | ×2 | 10 | 4–6 | 8–10 |
| **Total** | | **85** | **≈ 52–61** | **≈ 75–82** |

Examiner judgment varies, so treat these as indicative. The pattern is what matters: **roughly 20 of the recoverable marks sit in content that is missing or unwritten rather than content that is wrong.** An abstract, a scope section, a future-work section, and filling §3.4 together account for about 15 marks and require no new research.

## 7. Prioritized action list

| Priority | Action | Marks at stake | Effort |
|---|---|---|---|
| 1 | Write the Abstract (four named elements) | ~4 | 1 hour |
| 2 | Write §4.2 Future Work; fill §3.4 | ~5 | 2 hours |
| 3 | Restore a Scope of Study section with explicit exclusions and feasibility | ~3 | 2 hours |
| 4 | Replace Section 2 with the revised version; fix the complexity claim in §1.2 | ~4–8 | 3–4 hours |
| 5 | Fix all missing/garbled references and alphabetize; fix all broken cross-references and figure numbering | ~3 | 2 hours |
| 6 | Add an evaluation methodology subsection and a half-page COP formulation | ~2 | 3 hours |
| 7 | Reconcile 150 vs 122; quantify the numbered vs free-seating section | correctness | 30 min |
| 8 | Confirm both Gantt charts are embedded and legible | ~2 if missing | 15 min |
| 9 | Full language proofread; verify the `Ã`/`â` artifacts are not in the source PDF | ~2 across criteria | 2 hours |

## 8. One project-level warning outside the rubric

`CLAUDE.md` — the specification your solver will be built from — currently states the tier order as **Emperor → Bodhi → Merit** and asserts that *"rows are tier-exclusive: a tier band's partially used last row stays otherwise empty and is never shared with the next tier."*

Both statements now **contradict your elicited ground truth**. Appendix B (A-C10) and your own instruction confirm the order is **Emperor → Merit → Bodhi**, and that a boundary row **may** be shared between adjacent tiers so the numbered section packs with no empty seat — which is also what constraints C12 and C15 in the report's own listing say.

The report is right and the specification is stale. Update `CLAUDE.md` before implementation begins, or the solver will be built to enforce a hard constraint that the stakeholders explicitly contradicted. This is a correctness risk, not a marks risk, but it is the most consequential item in this document.
