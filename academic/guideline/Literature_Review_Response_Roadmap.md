# Response & Revision Roadmap — Section 2 (Literature Review)

**Reviewed artifact:** `academic/fyp_interim-report-refined.md`, Chapter 2 (§2.1–§2.5)
**Against:** `academic/guideline/Literature_Review_Comment.md` (examiner feedback)
**Also considered:** `academic/guideline/refine-objective2.md`, project spec (`CLAUDE.md`)
**Purpose:** Assess the examiner's feedback, record what the current draft already covers, and prioritize the remaining work. This is a review document, not a revised draft.

---

## 1. Assessment of the examiner's feedback

The feedback is well-calibrated and I agree with essentially all of it. Its rubric scores are fair, and two of its criticisms are the right ones to worry about: the **absolute gap claim** and the **narrowness of the existing-system review**. Neither is a research-design flaw — both are framing and coverage problems, which is the cheapest class of problem to fix.

Two qualifications, however:

**The examiner under-rates Objective 2's real weakness.** They score it "moderate to strong" and ask for "one or two sources" on rescheduling or minimal perturbation. That understates it. The report's incremental-repair mechanism with progressive neighbourhood expansion *is* a known, named technique with a canonical literature — **Large Neighbourhood Search** and the **Minimal Perturbation Problem** — and the draft currently reinvents it without naming either. This is not a gap of one or two supporting citations; it is a missing theoretical anchor for the project's second objective. See §3.2 below.

**The examiner missed the most attackable technical claim in the chapter.** Their review is rhetorical rather than technical, so it does not challenge the report's hardness argument, which is currently stated incorrectly. See §3.1 below. In a CS viva this is more dangerous than the wording of the gap claim, because it is a claim that is *wrong* rather than merely *overreaching*.

---

## 2. Point-by-point response to the examiner's items

| # | Examiner item | Status in current draft | Action required |
|---|---|---|---|
| E1 | "None existing solution/study" is too absolute; use combined-capability framing | **Partially addressed.** §2.2 already ends on the combination framing ("not a single missing feature but the missing combination"), and §2.1's gap paragraph opens "Across the reviewed literature…". But the same sentence then says "no published seating-allocation method combines…", which reads as universal, and the Abstract repeats the unhedged form. | Tighten three specific spots: the Abstract's gap sentence, §2.1 "Gap identified" opening clause, and §1.1's "Nor does the academic literature supply…". Use *"none of the reviewed…"* consistently. Low effort, high defensive value. |
| E2 | Add a literature search strategy paragraph (databases, keywords, date range, inclusion/exclusion) | **Missing entirely.** | Add as new §2.1 opening subsection. This is the single highest value-per-effort item. It also retroactively substantiates the existing claim that the seating literature is "thin," which is currently an unsupported empirical assertion. See §4 for a draft. |
| E3 | Existing-system review too narrow; add ≥3 more categories | **Valid.** Only 4 systems, and §2.2's selection rationale ("span the market spectrum") is asserted, not derived from criteria. | Expand Table 2.1 by category rather than by product count — one representative per category is enough. Categories: reserved-seat ticketing, banquet/table planning, faith-based/non-profit congregation management, exam/classroom seating. Note that the last is also an *academic* stream, not just a commercial one (see §3.3). |
| E4 | Add a "Supports PJKIT-specific rules" column to Table 2.1 | **Valid and cheap.** | Add it. This becomes the strongest column in the table because every commercial row is a factual "No" — two-seat allocation units, demand-derived tier bands, aisle-aware pairing, and within-tier contribution ordering are simply not expressible in any of these tools. Unlike "Partial/Weak" judgments, this cell is not contestable. |
| E5 | Strengthen Objective 2 with reassignment-stability / minimal-perturbation / repair literature | **Valid, and more serious than stated.** Objective 2 currently rests on Hoang (2022) — self-caveated as distributed and continuous — plus one paragraph of Ipsen et al. | Name and cite Large Neighbourhood Search and the Minimal Perturbation Problem. See §3.2 — this is the most substantive revision in the list. |
| E6 | Objective 3 is under-supported academically; don't oversell it | **Partially addressed.** §1.4.3 already demotes authentication to a platform concern, but Chapter 2 never states the contribution boundary, and §2.2 calls the lookup "a core feature." | Add one explicit sentence to §2.5: the lookup is a necessary system module that closes the operational loop, not part of the algorithmic contribution. **Do not manufacture citations for it.** Padding a weak objective with tangential HCI or self-service-information references would invite a worse question than the honest boundary statement does. |
| E7 | Avoid wording implying proven outcomes | **Valid.** Table 2.1's "Proposed FYP System / Yes / Yes / Yes / Yes" asserts capability for an unbuilt system; §2.5 says the system "addresses" rather than "is designed to address"; the Abstract says the combination "this project delivers." | Sweep Chapter 2 for the indicative mood on unbuilt capability. Mark the proposal row as "Yes (designed)" or "Target," and shift to "is intended to / is designed to / will be evaluated by." |

**Examiner grilling questions (their §"Examiner grilling questions"):** the draft already contains defensible answers to Q4 (PerfectTablePlan), Q5 (CP-SAT vs GA), Q6 (FEASIBLE ≠ OPTIMAL), Q8 (manual edit vs controlled reallocation), and Q9 (lookup scope). Q1–Q3 (coverage, search methodology, documentation of negative capability claims) are answered only once E2 and E3 are done. Q7 (PJKIT uniqueness) and Q10 (contribution claim) are answerable but are not stated compactly anywhere — consider a short explicit "contribution boundary" paragraph at the end of §2.5 that answers both in three sentences.

---

## 3. Findings the examiner did not raise

### 3.1 The hardness argument is stated incorrectly — highest technical risk

Both §1.1 and §2.3 justify computational difficulty by counting ordered assignments (`232!/(232−122)!`). A search-space count is **not** a complexity argument, and conflating the two is exactly the kind of imprecision a CS examiner will pick apart. The plain assignment problem — n agents, m tasks, linear costs — also has a factorially large search space and is nonetheless **solvable in polynomial time** by the Hungarian algorithm. Presenting the factorial as evidence of hardness therefore proves nothing, and a well-prepared examiner can say so in one sentence.

What actually makes the PJKIT problem hard is its *structure*, not its size: two-seat pairing units, within-tier ordering constraints, band capacity coupling, and adjacency/aisle restrictions take it outside the linear-assignment class. There is also a clean citation path available — the report's own primary source (Ipsen et al., 2026) notes that the seat allocation problem is a special case of the **capacitated p-median problem**, which is NP-hard, citing Mu & Tong (2019).

**Recommendation.** Keep the factorial only as an illustration of why *manual* enumeration is infeasible for a human allocator (which is a fair use of it, and directly supports Problem Statement 1). Add a separate, correctly-framed sentence establishing computational hardness via the CPMP/p-median reduction, and state explicitly that the structural constraints place the problem outside polynomially-solvable linear assignment. This converts the chapter's weakest technical claim into one of its stronger ones.

### 3.2 Objective 2's mechanism has a canonical name the report never uses

`refine-objective2.md` specifies: lock unaffected assignments, release affected seats, re-solve a bounded neighbourhood, progressively expand on infeasibility, full regeneration only as last resort. That is a textbook description of two established techniques, and the report presents both as if invented for this project:

- **Large Neighbourhood Search (LNS)** — re-optimizing a bounded neighbourhood around an incumbent solution while freezing the remainder, originating with Shaw (1998) in constraint-programming vehicle routing and surveyed since (Pisinger & Ropke, 2010). This is precisely the "reduced CP-SAT repair model with progressive neighbourhood expansion."
- **Minimal Perturbation Problem (MPP)** — given a solution to a CSP and a change to the problem, find a new solution minimizing the number of changed assignments. El Sakkout & Wallace (2000) formalized it for dynamic scheduling; the Müller / Rudová / Barták line of work applies it to **course timetabling**, where an already-published timetable must absorb a change with minimum disruption. That is a near-exact structural analogue of PJKIT: published plan + late change + preserve unaffected assignments.
- Also worth one line: **solution reuse in dynamic CSP** (Verfaillie & Schiex, 1994), the canonical reference for reusing a prior solution when constraints change.

Adding these does three things at once: it gives Objective 2 real literature (E5), it makes the escalation ladder look principled rather than ad hoc, and it lets the report drop the *defensive* framing around Hoang (2022) — instead of leaning on a distributed/continuous dissertation and apologizing for the mismatch, Hoang becomes a *supporting* citation for the switching-cost objective while LNS and MPP carry the mechanism.

Note also that Hoang's own reactive-vs-proactive distinction maps onto full-regeneration vs. incremental-repair, so the existing source can be worked harder than it currently is.

### 3.3 The report's own primary source is an uncited goldmine — fixes coverage and recency together

The examiner's rubric asks for *recent* literature, and Chapter 2's seating-specific academic base is currently two papers, one from 2005. Ipsen et al. (2026) — already cited — contains a reference list with several directly on-topic, peer-reviewed works the draft ignores:

| Candidate source | Why it matters here |
|---|---|
| **Hales & García (2019), "Congress seat allocation using mathematical optimization," *TOP* 27(3)** | Physical seat allocation in a **legislative assembly** — contextually far closer to a PJKIT community assembly than office floor plans. It is also the paper Ipsen et al. adapted their integer program from, so it is upstream of a source already central to the report. Arguably the most important single missing citation. |
| **Barry et al. (2021), "Optimal Seat Allocation Under Social Distancing Constraints"** | Recent, seating-specific, constraint-based, and includes floor-plan parsing. Directly answers the recency criterion. |
| **Stoll (2022), "Solutions to the Distance Constrained Cinema Seating Problem" (MSc, Utrecht)** | Fixed-row venue seating with adjacency/distance constraints — the closest published analogue to a rows-and-positions venue with adjacency rules, i.e. structurally close to Emperor pairing. |
| **Ülker (2013); Awadallah et al. (2012)** — office space allocation | Establishes the adjacent Office Space Allocation problem class, useful for scoping what this project is *not*. |
| **Mu & Tong (2019)** | The NP-hardness anchor needed for §3.1 above. |

Mining a key paper's reference list is legitimate **backward snowballing**, and describing it as such in the search-strategy paragraph (E2) turns this from opportunism into documented methodology. It is also the cheapest possible route to satisfying both the coverage and recency criticisms, since the sources are already identified.

A caution: **Serafini (2012)** also appears in Ipsen's list and is tempting, but it concerns *apportionment* of seat counts to EU member states rather than assigning individuals to physical seats. Cite it only if the distinction is stated, or leave it out.

### 3.4 Internal contradiction in the "Gap identified" paragraph

§2.1's gap paragraph states that "Ipsen et al. (2026) achieve exactness only through bespoke integer programs **without a reallocation objective**." But the same section, four paragraphs earlier, praises Ipsen's warm-started local search as "the closest published precedent for this project's incremental repair mechanism." The chapter therefore credits and denies the same property of the same paper.

The fix is also a sharper gap statement. Ipsen's local search is a **solution-improvement** step *within a single planning run* — it warm-starts from an incumbent to get a better plan, not to preserve an *already-communicated commitment* to participants. This project's repair mechanism is triggered by a *data change after publication*, and its stability objective exists because assignments have already been announced to people. That distinction — improvement-warm-start versus post-publication commitment-preserving repair — is defensible, precise, and is the actual gap. State it that way.

### 3.5 Stale and conflicting facts inside Chapter 2

These appear to be leftovers from the earlier draft revision and will read as carelessness if an examiner cross-checks them against Chapter 3:

1. **§2.1, Sun (2020) paragraph** describes the venue as "a fixed **12-seat** row with one central aisle," while §2.3 correctly uses the 232-assignable-seat, 16-seats-per-row layout. The same sentence correctly places the aisle between positions 8 and 9, which is only consistent with a 16-seat row — so the sentence contradicts itself.
2. **§2.3 states the tier band order as "Emperor → Merit → Bodhi"** and adds "with shared boundary rows." Both halves conflict with the project spec (`CLAUDE.md`), which specifies the order **Emperor → Bodhi → Merit** and states that rows are **tier-exclusive** — "a tier band's partially used last row stays otherwise empty and is never shared with the next tier." §2.1 similarly writes "Emperor/Merit/Bodhi."

I cannot tell which document is authoritative — the report may reflect a newer reading of the 2023/2024 charts, or the spec may be current and the report stale. **Reconcile these before submission**, because a hard constraint stated one way in the literature review and the opposite way in the methodology is the kind of inconsistency that costs disproportionate credibility.

### 3.6 A genuine strength currently buried

The Muñoz et al. discussion reports that two candidate soft rules drawn from the literature (no isolated seat, no row-edge gaps) were **superseded** after checking PJKIT's historical 2023/2024 charts, which showed centre-out packing and front-to-back fill instead. As written, this reads as "we borrowed from the literature and then discarded it," inviting the question *"so what did the literature contribute?"*

Reframe it as what it actually is: the literature supplied the *constraint class* (row-level packing and gap aesthetics as legitimate soft constraints), and empirical validation against real historical charts determined the *specific form* that class takes at PJKIT. That is evidence-based constraint elicitation — a methodological strength — and it currently sits in a subordinate clause.

### 3.7 Table 2.2's ILP cell partly refutes its own conclusion

The ILP limitation cell ends: "both ILP and CP-SAT require integer modelling, so this cost is not avoided by CP-SAT's alternative." That is honest, but placing it in the *limitation* column of the rejected alternative blunts the differentiator in the very table meant to establish it. Restructure so the shared cost (integer modelling) is acknowledged once, and the *differential* cost (big-M compilation of logical/conditional constraints, weakened relaxations, no native reification or channeling) is what the cell actually contrasts. Align the wording with the examiner's own expected answer to their Q on CP-SAT vs MIP — that CP-SAT is not claimed to be universally better, but is a better fit for *this* rule set.

---

## 4. Draft: literature search strategy paragraph (for E2)

Adapt and insert as the opening of §2.1, replacing placeholders with what you actually did. Do not overstate it — an honest narrative search is fully acceptable at interim stage; a fabricated systematic protocol is not.

> **Search strategy.** Literature was identified through a two-stage search. In the first stage, database searches were conducted on Google Scholar, IEEE Xplore, the ACM Digital Library, and Scopus using combinations of the keywords *seating allocation*, *seat assignment*, *spectator allocation*, *constraint optimization*, *constraint programming*, *CP-SAT*, *minimal perturbation*, *reallocation stability*, and *large neighbourhood search*, restricted to English-language publications. Works were included when they addressed the assignment of people to physical seats or presented constraint-optimization methods transferable to that problem, and excluded when they addressed seat-count apportionment rather than physical assignment, revenue-management or overbooking optimization, or pedestrian-flow and evacuation simulation. In the second stage, backward snowballing was applied to the reference lists of the most directly relevant works identified — in particular Ipsen et al. (2026) — to locate earlier seating-allocation studies not surfaced by keyword search. The search confirmed that literature addressing seating allocation *as an optimization problem* is limited relative to the general combinatorial-assignment literature, with contributions distributed across office space allocation, legislative seat allocation, and event/venue seating rather than forming a single coherent research stream.

That last sentence is what licenses the "thin literature" claim the chapter already makes.

---

## 5. Prioritized action list

| Priority | Action | Addresses | Effort |
|---|---|---|---|
| **1** | Fix the hardness argument: retain the factorial as a manual-infeasibility illustration; add a correct NP-hardness statement via the capacitated p-median reduction (Mu & Tong, 2019, via Ipsen et al.) | §3.1 — wrong claim | Low |
| **2** | Add LNS and Minimal Perturbation Problem literature as the theoretical anchor for Objective 2; demote Hoang to a supporting citation | E5, §3.2 | Medium |
| **3** | Add the search-strategy paragraph (§4 above) | E2, grilling Q2 | Low |
| **4** | Add Hales & García (2019), Barry et al. (2021), Stoll (2022) from Ipsen's reference list | E3 coverage, recency, §3.3 | Low–Medium |
| **5** | Expand Table 2.1 by category (ticketing, banquet, congregation management, exam seating) and add the "Supports PJKIT-specific rules" column | E3, E4, grilling Q1 | Medium |
| **6** | Reconcile the stale/conflicting facts: 12-seat vs 16-seat row; tier band order and row exclusivity vs `CLAUDE.md` | §3.5 | Low — but do it first if submitting soon |
| **7** | Hedge all absolute gap claims to "none of the reviewed…" in Abstract, §1.1, §2.1 | E1 | Low |
| **8** | Sweep for indicative-mood overclaims; mark the proposal row in Table 2.1 as designed/target | E7 | Low |
| **9** | Fix the Ipsen internal contradiction using the improvement-warm-start vs post-publication-repair distinction | §3.4 | Low |
| **10** | Add a three-sentence contribution-boundary paragraph closing §2.5 (answers grilling Q7, Q9, Q10; demotes Objective 3 honestly) | E6, Q10 | Low |
| **11** | Reframe the Muñoz superseded-rules passage as evidence-based elicitation | §3.6 | Low |
| **12** | Restructure Table 2.2's ILP limitation cell so the differentiator is unambiguous | §3.7 | Low |

Items 1, 2, and 6 are the ones that change the report's defensibility rather than its polish. Items 3–5 are what the examiner will check first.

---

## 6. Verification caveat

The sources recommended in §3.2 (Shaw, 1998; El Sakkout & Wallace, 2000; Verfaillie & Schiex, 1994; Müller/Rudová/Barták on minimal perturbation in course timetabling; Pisinger & Ropke, 2010) are recommended from domain knowledge and **have not been retrieved and read in preparing this review**. Locate and read each before citing, and confirm exact titles, venues, years, and page ranges. The sources in §3.3 are taken from the printed reference list of the retrieved Ipsen et al. preprint and should likewise be obtained and read rather than cited at second hand — citing a paper you have only seen in someone else's bibliography is precisely the practice the report's own reference-hygiene note warns against.
