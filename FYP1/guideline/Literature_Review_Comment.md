## Verdict as an FYP examiner

Your Section 2 is **strong enough to support the direction of the project**, especially for a planning-phase interim report. It clearly connects seating allocation to constraint optimization, reviews several relevant academic works, compares commercial tools, explains constraint modelling, and justifies CP-SAT as the selected solver. The literature review also directly attempts to synthesize the findings against the three problem statements. 

However, I would **not yet accept the claim that “none of the current existing solution or study could resolve the PJKIT problem” in an absolute sense**. The safer and more defensible academic claim is:

> None of the **reviewed** academic studies and commercial systems provides the **combined capability** required by PJKIT: configurable participant-profile-based constraints, constraint optimization, controlled movement-minimizing reallocation, versioned publishing, and participant-facing lookup in one workflow.

That wording is much safer because your literature review proves a **reviewed-solution gap**, not a universal worldwide impossibility.

## Overall examiner score for Section 2

Based on the UTP evaluation expectation, literature review should be critical, relevant, recent, properly cross-referenced, and clearly establish the importance of the current work. 

My estimated examiner rating:

| Criterion                    |             Current Level | Examiner Comment                                                                                                                                                        |
| ---------------------------- | ------------------------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Relevance to project         |                    Strong | Most reviewed works are directly connected to seating, constraint optimization, solver selection, or reallocation.                                                      |
| Critical analysis            |            Good to strong | You compare methods, identify limitations, and link each study to PJKIT. This is better than simple summarization.                                                      |
| Coverage of existing systems |                  Moderate | The commercial review is useful but too narrow to support a very strong “market gap” claim.                                                                             |
| Support for Objective 1      |                    Strong | CP-SAT, hard/soft constraints, COP, and seating-allocation literature are well connected.                                                                               |
| Support for Objective 2      |        Moderate to strong | Incremental repair is promising, but the literature base is thinner and partly borrowed from dynamic constraint optimization rather than seating-specific reallocation. |
| Support for Objective 3      |          Weak to moderate | Participant-facing lookup is justified more by practical workflow pain than by academic literature.                                                                     |
| Reference quality            |        Moderate to strong | You have good academic sources, but commercial-source evidence needs stronger documentation and more competitor coverage.                                               |
| Defense readiness            | Good, but not bulletproof | You can defend the project, but a tough examiner can still attack the breadth of the existing-system review and the strength of the “none can solve it” claim.          |

My overall judgement: **Section 2 is sufficient for a good interim report, but not yet sufficient for a very strong dissertation-level claim unless you strengthen the existing-system review and narrow your gap statement.**

## Objective-by-objective grilling

### Objective 1: Seating allocation engine

Your literature review supports Objective 1 well. You review academic seating allocation, hard/soft constraint structures, CP-SAT, ILP/MIP, GA, greedy, manual, and region-growing approaches. You also explain that CP-SAT is selected because the project requires structural rules, weighted preferences, solver status, and exact reporting. 

As examiner, I would say this is the **strongest part** of your literature review. It backs the claim that seating allocation can be modelled as a COP and that CP-SAT is suitable for rule-heavy assignment problems.

But I would challenge you with this:

> You claim CP-SAT is selected because it supports hard constraints, soft penalties, if-then rules, and solver status. But how do you prove CP-SAT is better than a well-formulated MIP model for only 100–200 participants?

Your answer must be: CP-SAT is not claimed to be universally better. It is selected because the PJKIT rule set contains many logical, conditional, pairing, aisle, tier-band, and reallocation constraints that are more naturally expressed using reification and channeling. MIP is viable but requires more linearization effort.

### Objective 2: Controlled dynamic reallocation

This objective is supported, but less strongly than Objective 1.

You use Hoang’s switching-cost concept and connect it to movement minimization. You also use Ipsen et al.’s warm-start/local repair idea as a precedent for preserving stability near an incumbent solution.  Your report also defines incremental repair clearly: affected participants are repaired first, unaffected assignments remain fixed where possible, and local repair expands only when infeasible. 

That is good.

But as an examiner, I would attack this part:

> Your cited dynamic optimization source is not a seating-allocation paper, and it is distributed/continuous while your project is centralized/discrete. Are you overclaiming its relevance?

You already acknowledge that limitation, which is good. But to strengthen it further, you should add at least one or two sources on **rescheduling**, **assignment repair**, **minimal perturbation**, **dynamic vehicle routing**, **incremental constraint solving**, or **stable matching/reassignment**. The current support is conceptually valid, but still thin.

### Objective 3: Participant-facing seat lookup

This is the weakest literature-backed objective.

Your practical argument is strong: PJKIT participants currently depend on printed lists, PDFs, or staff assistance, creating queues and uncertainty about whether the latest plan is being viewed.  Your white-space table includes “participant-facing seat lookup after admin allocation,” which helps connect the feature to the market gap. 

But academically, this section is under-supported. It is currently justified mostly by **case-study workflow pain**, not by literature.

As examiner, I would ask:

> Why is participant-facing lookup part of a research contribution instead of just a basic CRUD/platform feature?

Your answer must be careful: participant lookup is **not the core research contribution**. The core contribution is the constraint-based allocation and controlled reallocation engine. The lookup is a necessary system module that closes the operational loop by exposing only the latest approved seating version to participants. It resolves Problem Statement 3 but should not be oversold as the main academic contribution.

## Major strength of your Section 2

Your strongest move is that you do not just say “manual seating is bad.” You show that the gap is a **combination gap**:

1. Existing systems may support visual seating charts.
2. Some tools may support automatic seating.
3. Some academic works may support optimization.
4. Some methods may support local repair or switching-cost ideas.
5. But the PJKIT use case requires all of these together: configurable rules, two-seat units, tier-band placement, aisle-aware adjacency, controlled repair, versioned publishing, and participant lookup.

That is the correct argument. Your white-space table makes this combination gap visible. 

## Major weakness: your existing-system review is too narrow

You reviewed:

* Manual Excel / seating chart
* Cvent
* PerfectTablePlan
* WeddingWire / Zola

That is acceptable for an interim report, but not enough if you want to strongly claim that existing solutions do not solve the PJKIT workflow.

A tough examiner could ask:

> Why only these four? What about Eventbrite reserved seating, Ticketmaster/SeatGeek venue seating, Allseated/Social Tables, church management systems, temple management systems, banquet table planners, school exam seating systems, and venue access-control tools?

Even if those systems still do not solve your problem, you need to show that you considered the broader solution space. Otherwise, your gap looks selective.

## Major weakness: “none existing solution or study” is too absolute

Do not say:

> None of the current existing solution or study could resolve PJKIT.

That is dangerous.

Say:

> None of the reviewed academic studies or commercial systems provides the required combination of configurable participant-profile-based allocation, constraint-based optimization, controlled movement-minimizing reallocation, versioned publishing, and participant-facing lookup within one PJKIT-specific workflow.

This is much more defensible. Your own earlier prompt guideline also warns against absolute wording and recommends this combined-capability framing. 

## Examiner grilling questions you must be ready for

### 1. Literature coverage

Why are four commercial systems enough to establish a white space? What criteria did you use to select Cvent, PerfectTablePlan, WeddingWire, and Zola?

### 2. Search methodology

Where did you search for academic papers? Google Scholar? IEEE Xplore? ACM Digital Library? Scopus? What keywords did you use? What inclusion and exclusion criteria did you apply?

### 3. Existing systems

How do you know Cvent does not support rule-based allocation? Did you verify from official documentation, product demo pages, or only marketing pages?

### 4. PerfectTablePlan

PerfectTablePlan already has automatic assignment using GA. Why is your project not just a smaller version of PerfectTablePlan?

Expected answer: because PJKIT needs profile-driven rule configuration, two-seat Emperor pairing, tier-band placement, controlled reallocation, versioned publishing, and participant-facing lookup, not only table guest preference optimization.

### 5. CP-SAT vs GA

Earlier research direction considered GA. Now your report selects CP-SAT. Why did the solver direction change?

Expected answer: GA is flexible but cannot prove optimality or provide explicit infeasibility/status reporting. CP-SAT better supports hard constraints, Boolean logic, reification, and status reporting, which are critical for a rule-heavy operational system.

### 6. CP-SAT feasibility

Can CP-SAT solve the problem within 60 seconds? What if it returns FEASIBLE but not OPTIMAL?

Expected answer: FEASIBLE is not reported as optimal. The system returns the actual solver status and only claims optimality when CP-SAT returns OPTIMAL.

### 7. PJKIT uniqueness

Are PJKIT rules truly unique, or are they just normal priority seating?

Expected answer: the uniqueness is not only priority seating; it is the combination of contribution tiers, demand-derived row bands, Emperor two-seat units, aisle-aware pairing, contribution ordering, dynamic repair, and participant lookup.

### 8. Dynamic reallocation

What is the theoretical difference between “editing a seat manually” and “controlled dynamic reallocation”?

Expected answer: manual editing changes records directly without optimization or stability guarantees. Controlled dynamic reallocation treats the published plan as a baseline, defines affected/unaffected participants, minimizes movement, creates a new plan version, and requires organizer approval.

### 9. Participant lookup

Why is participant lookup in an optimization FYP?

Expected answer: it is not the algorithmic contribution, but it resolves the third operational problem by ensuring participants access the latest published allocation instead of outdated printed/PDF lists.

### 10. Contribution claim

What exactly is your academic contribution?

Expected answer: the contribution is the applied modelling of a real PJKIT seating workflow as a configurable constraint optimization problem, including two-seat allocation units, tier-band rules, movement-minimizing reallocation, and measurable solver-status/penalty outputs.

## What you should improve before submission or defense

First, add a short **literature search strategy** paragraph. State databases, keywords, date range, and selection criteria. This makes your review look systematic rather than cherry-picked.

Second, expand the existing-system review by at least three more categories:

| Category                                          | Why add it                                                    |
| ------------------------------------------------- | ------------------------------------------------------------- |
| Venue/ticketing reserved-seat systems             | To show you considered seat lookup and ticket-linked seating. |
| Banquet/table planning systems                    | To compare against group and guest preference allocation.     |
| Church/temple/non-profit/event management systems | To show the PJKIT religious/community context was considered. |
| Exam/classroom seating systems                    | To compare rule-based seating under constraints.              |

Third, add a stronger column in Table 2.1:

> Supports PJKIT-specific rules: two-seat units, tier-band placement, aisle-aware pairing, contribution ordering

This would make the gap much clearer.

Fourth, strengthen Objective 2 with more literature on reassignment stability, repair-based optimization, minimal perturbation, or dynamic scheduling.

Fifth, avoid wording that makes the project sound like it has already proven outcomes. Say “is intended to,” “is expected to,” and “will be evaluated using,” unless you already have experimental results.

## Final examiner judgement

Your Section 2 is **good and defensible**, but it is not yet “examiner-proof.” It strongly supports Objective 1, reasonably supports Objective 2, and only practically supports Objective 3. The biggest risk is not the technical theory; it is the **breadth and defensibility of the existing-system gap claim**.

I would pass the literature review for an interim report, but during defense I would pressure you heavily on this point:

> You have shown that the reviewed solutions do not provide the required combined workflow. You have not proven that no existing solution in the world can solve it.

Fix that wording, expand the competitor categories, add a search strategy, and your literature review becomes much harder to attack.
