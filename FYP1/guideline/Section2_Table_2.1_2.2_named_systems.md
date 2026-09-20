# Section 2 — Named Systems for Table 2.1 and Table 2.2

**Replaces:** rows 7–10 of Table 2.1 and Table 2.2 in `FINAL_Section2_Literature_Review.md`, together with the surrounding prose in §2.4, §2.5 and §2.8 that refers to those categories.

**Why this was needed:** rows 7–10 previously named a *category* ("Examination and classroom seating tools") rather than a product. A category cannot be verified, and a capability claim about an unnamed category is not defensible in a viva. Each row now names one representative product whose capabilities and limitations were read from that vendor's own pages.

## Verification status

Unlike the academic sources recommended elsewhere, **these four products were inspected directly** during preparation of this revision. Each claim below traces to a page I read.

| Row | Product | Source inspected | Date |
|---|---|---|---|
| 7 | Eventbrite Reserved Seating | Product feature page and Help Centre article on managing a reserved seating event | July 2026 |
| 8 | Prismm (formerly AllSeated) | "Manage your guest list" solution page | July 2026 |
| 9 | Breeze ChMS | Product homepage and feature listing | July 2026 |
| 10 | Vidyalaya School Software, exam seating arrangement module | Vendor article on exam seating arrangement capabilities | July 2026 |

**One correction carried over.** A secondary source claimed that Prismm brought AllSeated and Social Tables together under one brand. Prismm's own pages reference only AllSeated and make no mention of Social Tables, so that claim is **not** repeated. Cvent's acquisition of Social Tables is separate and well documented, so row 3 remains "Cvent / Social Tables" unchanged.

---

# Replacement for Table 2.1 (rows 7–10)

Rows 1–6 are unchanged. Replace rows 7–10 with the following.

| No | Existing System | Category | Main Capability | Limitation |
|---|---|---|---|---|
| 7 | Eventbrite Reserved Seating (Eventbrite, n.d.-a, n.d.-b) | Reserved-seat ticketing and venue access | Creates a custom venue seat map through drag-and-drop design, and sells numbered seats through a clickable floor plan on which the attendee selects their own seat at the point of purchase. The seat label is carried on the attendee's ticket, for example "Balcony 1, Row AA, Seat 7". The event organizer can click a sold seat to view the attendee and order details, can create a manual order for chosen seats, and can transfer an attendee to a different seat. | Seat allocation is either self-selected by the attendee at purchase or assigned manually by the organizer, and no automatic or rule-based allocation driven by participant attributes is documented. There is no configurable constraint layer, no measurable optimization of the resulting arrangement, and no repair workflow that preserves the remainder of a published plan when one attendee changes. |
| 8 | Prismm, formerly AllSeated (Prismm, n.d.) | Banquet and table planning | Provides cloud-based floor plan design with 2D and 3D venue diagramming, guest list management, guest grouping and colour coding, and drag-and-drop placement of guests at tables within the designed floor plan. Captures guest requirements such as VIP placement requests and dietary needs. | Guests are assigned to tables rather than to numbered row and position seats, so the geometry that governs PJKIT seating is not represented. Placement is manual drag-and-drop and no automatic or optimized assignment is documented. Guest requirements are captured as annotations rather than as constraints that drive the allocation, and there is no guest-facing seat lookup. |
| 9 | Breeze ChMS (Breeze ChMS, n.d.) | Faith-based and non-profit congregation management | Maintains member records, tracks giving and generates contribution reports and year-end giving statements, records attendance through check-in, and provides event management with public-facing registration forms. | Maintains precisely the participant attributes that PJKIT allocates on, which are the contribution amount and the attendance history, but provides no seating allocation or seating chart function at all, so those attributes cannot be acted upon for seating. Room and resource assignment exists for event scheduling but not at seat level. |
| 10 | Vidyalaya School Software, exam seating arrangement module (Vidyalaya School Software, 2026) | Rule-based numbered-seat allocation in an adjacent domain | Automatically allocates students to numbered seats and examination halls from the roll numbers, the class and section details, the examination schedule, the room capacity and the seating pattern. Applies the constraint that students of the same class are not seated in the same hall, prevents duplicate seat allocation, supports real-time modification of student records and of the allocation, and can create a new seating plan when circumstances change. | Optimizes the separation of students rather than a priority or contribution ordering, and offers no participant-attribute weighting and no configurable soft constraints. Regeneration recreates the plan rather than repairing an already-published plan under a movement-minimizing objective, and no student-facing lookup of the allocated seat is documented on the reviewed page. |

## Replacement for the two observations following Table 2.1

> Two (2) observations follow from reviewing the existing systems across categories rather than within the event planning category alone.
>
> The first observation is that the individual capabilities which PJKIT requires all exist somewhere in the market, but each exists in a different product. Eventbrite Reserved Seating provides an attendee with the number of their own seat. Breeze ChMS holds the contribution amounts and the attendance history that PJKIT allocates on. The Vidyalaya exam seating module performs automatic rule-based allocation of numbered seats and can regenerate a plan after a change. Prismm and PerfectTablePlan perform guest placement, and PerfectTablePlan performs automated optimization of it.
>
> The second observation is that these capabilities exist in mutually exclusive products, and that none of the reviewed systems combines them. The two products that hold the right participant attributes perform no allocation, the product that performs rule-based allocation of numbered seats holds none of the attributes and optimizes separation rather than priority, and the products that optimize placement do so around tables rather than around a numbered row and position geometry. This strengthens rather than weakens the case for this project, because it locates the gap in the integration of these capabilities under a configurable rule layer rather than in the novelty of any single feature.

---

# Replacement for Table 2.2 (rows 7–10)

Rows 1–4 and the proposed system row are unchanged. Replace rows 7–10 with the following, keeping the same column order.

| Existing Method / System | Participant-Facing Seat Lookup After Admin Allocation | Configurable Participant-Profile-Based Allocation | Controlled Dynamic Reallocation | Constraint-Based Optimization | Supports PJKIT-Specific Structural Rules¹ |
|---|---|---|---|---|---|
| Eventbrite Reserved Seating | Partial, as the seat appears on the attendee's own ticket, but it is self-selected or manually assigned rather than produced by rule-based allocation | No | Partial, as the organizer can transfer an attendee to another seat manually, with no movement-minimizing repair | No | No |
| Prismm (formerly AllSeated) | No | Partial, as VIP and dietary requirements are captured as annotations rather than as allocation constraints | Manual adjustment | No, as placement is manual drag-and-drop with no automatic assignment documented | No |
| Breeze ChMS | No | Holds the contribution and attendance attributes but performs no allocation | No | No | No |
| Vidyalaya exam seating module | Not documented | Partial, as allocation is driven by roll number, class and section rather than by configurable participant attributes | Partial, as a plan can be regenerated after a change, but not repaired under a movement-minimizing objective | Partial, as allocation is rule-based and automatic, but with no weighted objective and no optimality or status reporting documented | No |

**Caption addition.** Extend the table caption or the introductory sentence to read:

> Table 2.2 White space analysis of the reviewed methods and systems. Every assessment is based on the publicly available product documentation, feature pages and help articles of each vendor, inspected in June and July 2026. A cell marked "Partial" denotes a capability that exists in some form but is not configurable over domain-specific participant attributes or is not exposed as a controlled workflow. A cell marked "Not documented" denotes a capability that is absent from the reviewed vendor documentation, which is distinguished from a capability verified to be absent.

## Replacement for the first and third white-space findings

The first finding and the third finding both refer to the newly named products and should be updated. The second and fourth findings are unchanged.

**First finding, revised:**

> First, there is a **participant-facing seat accessibility gap** within the event planning category. The existing planners allow seating charts to be printed, exported, shared or linked to tickets, which is not the same as an authenticated route on which a participant sees the seat that has been assigned to them from the latest seating map approved by the event administrator. Eventbrite Reserved Seating does place the seat label on the attendee's own ticket, which is the closest equivalent found in the review, but it does so in a model where the attendee selected that seat themselves at the point of purchase or where the organizer assigned it manually, rather than in a model where an administrator allocates seats by rule and then publishes an approved version. No reviewed system exposes a participant-facing route onto an administrator-published seating map.

**Third finding, revised:**

> Third, there is a **controlled dynamic reallocation gap**. Dynamic changes such as a participant absence or a last-minute substitution are typically handled by manual editing rather than by systematic reallocation. Eventbrite Reserved Seating allows an organizer to transfer an attendee to a different seat, and the Vidyalaya exam seating module allows a seating plan to be regenerated after a change, but neither treats the already-published plan as a baseline to be preserved. Manual transfer changes one record without regard to the rest of the plan, and regeneration recreates the plan without minimizing the disruption to participants who have already been informed of their seats. Neither is equivalent to a workflow in which the changed participant data is submitted, a repair is computed against the published seating map under a movement-minimizing objective, a new version is produced together with a movement summary, and only an approved version is published. Configurable constraint weights also receive little explicit support, which leaves the event administrator unable to formally adjust the relative importance of competing allocation criteria, and most systems offer no measurable quality metric by which to judge whether a generated seating map is balanced and defensible.

---

# Replacement for the combination-gap paragraph in §2.8

> **The nature of the gap and the boundary of the contribution.** The gap that this review establishes is a combination gap rather than a single missing feature. The individual capabilities exist separately across the market, since Eventbrite Reserved Seating gives an attendee the number of their own seat, Breeze ChMS holds the contribution amounts and the attendance history, the Vidyalaya exam seating module performs automatic rule-based allocation of numbered seats and can regenerate a plan after a change, and PerfectTablePlan performs automated optimization of guest placement. What no reviewed academic study or existing market system provides is the combination that the PJKIT use case requires, which is configurable participant-profile-based constraints, constraint-based optimization with falsifiable status reporting, controlled movement-minimizing repair of an already-published seating map, versioned publishing, and participant-facing lookup, all within a single workflow and over a venue whose structural rules include two-seat allocation units, demand-driven tier bands with shareable boundary rows, aisle-aware pairing and within-tier contribution ordering.

---

# Should you cite the official webpages in the table?

**Yes, but cite once per row rather than in every cell.** Three reasons, and three cautions.

## Why to cite

**The rubric asks for it directly.** The literature review criterion carrying the heaviest weight names *"proper cross referencing"* in its top-band descriptor. A comparison table whose judgments are unattributed reads as opinion, and this is the single easiest place in Chapter 2 to demonstrate referencing discipline.

**It is the question the examiner has already signalled.** Grilling question 3 in `Literature_Review_Comment.md` is literally *"How do you know Cvent does not support rule-based allocation? Did you verify from official documentation, product demo pages, or only marketing pages?"* An in-row citation answers that question before it is asked.

**Negative claims are the weakest cells and need the most support.** Table 2.2 is largely a grid of "No". A positive claim can be checked by anyone who opens the product; a negative claim asserts that something is absent, which is unfalsifiable unless you say where you looked. The citation is what converts "No" from an assertion into a checkable statement.

## How to cite

Put the citation in the **Existing System** column only, so the capability and limitation cells stay readable:

> | 7 | Eventbrite Reserved Seating (Eventbrite, n.d.-a, n.d.-b) | … |

Then state the inspection date once in the table caption, as in the caption addition above, and put the full URLs in the reference list. This gives full verifiability at the cost of one parenthesis per row.

## Three cautions

**These sources do not improve your reference-quality score.** Vendor feature pages and help articles are commercial documentation, not peer-reviewed literature, and the second literature-review criterion rewards *"references from published journal / conferences."* Adding five more vendor URLs while the academic base stays thin would move that criterion in the wrong direction. Cite them because the white-space claim genuinely requires them as evidence, and keep the academic additions from `revised_section2_literature_review.md` as the counterweight so that vendor sources do not come to dominate the list.

**Distinguish "No" from "Not documented".** Where you have read the documentation and the capability is clearly absent, "No" is honest. Where the documentation simply does not address the question, "Not documented" is the honest cell, and it is also the safer one, because an examiner who happens to know the product cannot catch you out on a feature buried in a release note. I have used "Not documented" for the Vidyalaya student lookup for exactly this reason, and you should apply the same test to the Cvent and PerfectTablePlan rows you wrote earlier.

**Record the retrieval date and expect the pages to move.** Vendor pages are unstable, product names change, and one of the products in this table has already been renamed once, since Prismm was formerly AllSeated. The retrieval date in the caption is what protects the claim if the page changes before your viva. It is also worth saving a PDF print of each page you cite into your project folder, so the evidence survives even if the page does not.

---

# Reference entries to add

```
Breeze ChMS. (n.d.). Church management software. Retrieved July 2026, from
    https://www.breezechms.com/

Eventbrite. (n.d.-a). Reserved seating: Your seating chart maker for events. Retrieved July
    2026, from https://www.eventbrite.com/organizer/features/reserved-seating/

Eventbrite. (n.d.-b). Manage your reserved seating event. Eventbrite Help Centre. Retrieved
    July 2026, from https://www.eventbrite.co.uk/help/en-gb/articles/216108/how-to-manage-
    your-reserved-seating-event/

Prismm. (n.d.). Manage your guest list. Retrieved July 2026, from
    https://www.prismm.com/solutions/event-design-software/manage-your-guest-list

Vidyalaya School Software. (2026, June). How is technology revolutionizing exam seating
    arrangement in educational institutions? Retrieved July 2026, from
    https://www.vidyalayaschoolsoftware.com/blog/2026/06/how-is-technology-revolutionizing-
    exam-seating-arrangement-in-educational-institutions/
```

**Note on the Vidyalaya entry.** This is a vendor article rather than a product feature page, which makes it the weakest of the five sources. If you would prefer a product documentation page for that row, OpenEduCat's exam management module and EasyEdmin's examination scheduling documentation are the two alternatives I saw during the search, and either would be a stronger citation if their documentation confirms the same capabilities. Check one of them before submission if you have time; otherwise the Vidyalaya article does support every claim made in the row, since automatic allocation, the same-class separation constraint, real-time modification and plan regeneration are all stated on it explicitly.

Sources consulted for this revision: [Eventbrite Reserved Seating](https://www.eventbrite.com/organizer/features/reserved-seating/), [Eventbrite Help Centre — manage your reserved seating event](https://www.eventbrite.co.uk/help/en-gb/articles/216108/how-to-manage-your-reserved-seating-event/), [Prismm — manage your guest list](https://www.prismm.com/solutions/event-design-software/manage-your-guest-list), [Breeze ChMS](https://www.breezechms.com/), [Vidyalaya School Software — exam seating arrangement](https://www.vidyalayaschoolsoftware.com/blog/2026/06/how-is-technology-revolutionizing-exam-seating-arrangement-in-educational-institutions/).
