# PJKIT solver and application production implementation plan — v2

Prepared: 2026-09-18  
Status: Planning only. This document defines the implementation direction; it does **not** implement the changes.

## 0. Purpose of this revision

This v2 plan refines the previous production implementation plan against:

- the signed FYP Interim Report as the approved academic baseline;
- later stakeholder/layout decisions;
- the production-behaviour decisions made after the interim report;
- the final ranked soft-preference configuration model;
- the current public GitHub PoC on `main`;
- the revised testing/evaluation direction for FYP2.

The most important v2 changes are:

1. **Do not expose raw percentage sliders in production.** Event administrators rank and enable/disable plain-language soft preferences; the backend maps the order to versioned integer coefficients.
2. **Movement preservation is not an ordinary configurable soft preference during published-plan repair.** It is a protected repair objective: first minimize unaffected allocation units moved, then movement distance.
3. **The current production UI has three ordinary configurable preferences:** contribution-to-seat matching, activeness, and category suitability. The generic mapper can retain `40/30/20/10`, but current production modes normally expose at most three ranked items.
4. **Shared-row higher-tier centre placement remains a strong soft preference unless PJKIT explicitly confirms it as mandatory.** Cross-row tier precedence remains hard; accessibility remains hard.
5. **Contribution tier is an explicit registration attribute.** Validate its minimum contribution threshold, but do not infer an exclusive tier solely from the contribution amount unless PJKIT confirms exclusive upper bounds.
6. **`FEASIBLE` is a valid reviewable production result after independent validation.** It is not `OPTIMAL`, and proof metadata must remain visible.
7. **Manual assignment/swapping is a supported draft workflow.** Revalidate all hard constraints and recompute quality metrics before approval/publication.
8. **Testing is separated into correctness, optimization quality, robustness, reproducibility, repair quality, performance, and deployment performance.**

---

## 1. Sources and decision precedence

Use the following precedence when implementation details conflict:

1. **Explicit later stakeholder decisions that are documented and approved for the production event.**
2. **Signed FYP Interim Report** — approved project scope, requirements, C1–C17, FR1–FR17, NFR1–NFR8, and elicitation evidence.
3. **Adopted production-behaviour decisions** — lifecycle, FEASIBLE handling, manual editing, registration eligibility, published-plan repair, and ranked preference configuration.
4. **Current public PoC code** — implementation reference only; it is not a business-requirement source.
5. **Legacy mock data/configuration** — development fixtures only.

Do not edit the signed PDF. Record later refinements in the final dissertation, implementation documentation, and a requirements/traceability amendment.

### Public repository baseline checked for this plan

Repository:

```text
DariusShin/FYP-Seating-Allocation
```

Public `main` checked on 2026-09-18. The latest public commit visible during this review is:

```text
c6258ec4e637c8b8bc00fe9921f6373a761a88c7
```

The public PoC still contains the older assumptions:

- 10 × 12 prototype layout in README;
- Emperor → Bodhi → Merit terminology in `CONTEXT.md`;
- old contribution thresholds in `config/solver_config.json`;
- four raw numeric weights;
- `OPTIMAL`-only success handling;
- `/api/solve` accepting client-supplied raw weights and previous allocation;
- successful solve writing directly to `live_allocation_result.json`;
- the public view selecting the newest solver output rather than an explicitly published version.

If local uncommitted manual-editor work exists, preserve and audit it before changing related frontend files. Public GitHub cannot verify uncommitted local changes.

---

## 2. Confirmed production baseline

| Topic | v2 implementation decision |
|---|---|
| Venue | Current 2026 production target: 16 rows × 16 physical positions = 256 physical seats |
| Sides | West/西单 positions 1–8; East/东单 positions 9–16 |
| Aisle | Between physical positions 8 and 9 |
| 2026 obstacles | Rows 6 and 8, positions 5–12 inclusive; row 7 fully available |
| 2026 assignable capacity | 240 assignable seats / 16 blocked seats under the later 2026 layout decision |
| Historical report fixture | Preserve the interim-report 232-assignable-seat layout as a separate historical/reproducibility fixture; do not silently rewrite it as 240 |
| Tier precedence | Emperor → Merit → Bodhi |
| Tier source | Tier comes from the event registration record/form, not from automatic amount classification alone |
| Contribution minimums | Emperor ≥ RM5,000; Merit ≥ RM3,000; Bodhi ≥ RM2,000 |
| Upper contribution bounds | **Not assumed in v2.** Do not reject a registration merely because its contribution exceeds another tier’s minimum; confirm exclusive ranges with PJKIT before enforcing them |
| Pair allocation | Emperor registration = one allocation unit consuming two approved physical seats |
| Accessibility | Hard rule. Singles: positions 1, 2, 15, 16. Emperor accessible pairs: (1,2), (15,16), subject to final stakeholder confirmation/versioned policy |
| Shared tier boundary row | Adjacent tiers may share a row. Tier row precedence is hard; higher-tier preference for better positions inside the shared row is soft unless later confirmed mandatory |
| Within-tier contribution | Higher contribution must never be in a later row than lower contribution; within-row seat desirability remains soft |
| Solver eligibility | `CONFIRMED` and `REPLACEMENT_CONFIRMED` consume demand; other statuses do not |
| Initial generation | No previous allocation; movement = 0; global front-to-back and centre-out packing apply |
| Draft regeneration | Normally no previous-allocation baseline; freely re-optimize the draft |
| Published repair | Latest published version is authoritative baseline; preserve unaffected assignments before repacking; gaps may remain |
| Production solver result | Independently valid `OPTIMAL` or `FEASIBLE` may become a reviewable draft |
| Publication | Separate explicit approval/publication action; generation never directly updates participant-facing data |
| Manual edits | Allowed on drafts; authoritative revalidation/rescoring required before approval/publication |
| User soft-preference UI | Ordered enabled/disabled preference list, not numeric sliders |
| Repair movement | Protected system objective, not a draggable/disableable ordinary preference |
| Current ordinary configurable preferences | Contribution-seat matching, activeness, category suitability |

### Important academic traceability note

The 240-seat 2026 production layout is a **later refinement** from the signed report’s 232-assignable-seat baseline. Preserve both fixtures and state the difference explicitly in the final dissertation.

---

## 3. Rule categories: never mix these in the UI

Production behaviour must clearly separate three classes of rules.

### 3.1 Hard constraints

Hard constraints determine whether a plan is valid and publishable.

Examples:

- exactly one allocation unit per eligible registration;
- physical seat used at most once;
- blocked seats unavailable;
- valid Emperor pair;
- no aisle-straddling Emperor pair;
- tier row precedence;
- within-tier contribution row ordering;
- accessibility;
- initial-generation packing rules where applicable.

The user cannot disable a hard constraint with a preference control.

### 3.2 Protected lifecycle objectives

These are not ordinary administrator-configurable preferences.

For `REPAIR_PUBLISHED`:

1. minimize the number of unaffected allocation units moved;
2. minimize total movement distance;
3. optionally minimize local packing disruption as a lower protected stage.

The UI may explain these policies but must not expose them as percentage sliders.

### 3.3 Ordinary configurable soft preferences

Current production set:

1. `contribution_seat` — give higher-contribution registrations more desirable seats within the legal tier/row context;
2. `activeness` — favour participants with stronger PJKIT participation history;
3. `category_zone` — prefer seating zones suitable for participant category.

These are the only items currently intended for user ranking/enabling in production.

---

## 4. Priority and contradiction register

| Priority | Current conflict | v2 required resolution |
|---|---|---|
| P0 | Solve route writes successful generation directly to a guest-visible file | Generation creates/stores a draft only; publication is explicit |
| P0 | Public allocation loader uses newest file/mtime as authority | Public lookup resolves only the event’s explicit published-version pointer |
| P0 | Raw slider weights are trusted from the browser | Browser sends ordered enabled preference keys; backend derives effective coefficients |
| P0 | Client sends arbitrary `previous_allocation` | Server resolves authoritative published baseline for repair |
| P0 | Solver/frontend rely on incomplete validation | Validate original inputs and independently validate the complete proposed plan |
| P0 | Old layout/tier/order/config remain in code/docs | Introduce versioned production policy/layout and retain legacy fixtures only for historical tests |
| P0 | Tier-exclusive rows conflict with shared-boundary requirement | Implement shared boundary-row membership/occupancy |
| P1 | Every regeneration uses displayed plan as movement baseline | Explicit `generation_mode`; ordinary draft regeneration has no published baseline |
| P1 | Movement is one of four freely adjustable weights | Remove it from ordinary production ranking during repair; protect count-first/distance-second |
| P1 | `FEASIBLE` is discarded | Preserve incumbent, independently validate it, and return reviewable proof metadata |
| P1 | Existing `priority_seat` PoC cost is not cleanly contribution-derived | Define an auditable contribution-to-seat soft cost and avoid double counting |
| P1 | Shared-row centre precedence is treated as potentially hard | Keep it soft unless PJKIT explicitly confirms mandatory within-row superiority |
| P1 | Tier is inferred with exclusive min/max ranges | Treat tier as explicit input; validate confirmed minimum threshold only unless upper bounds are approved |
| P1 | Manual editor lacks authoritative save/revalidate/publish path | Add backend validation, rescoring, draft persistence, provenance, and publish gate |
| P2 | Existing additive tie-break is described as proving unique canonical output under all timed runs | Canonicalize only when higher objectives are sufficiently fixed/proven; report completion honestly |
| P2 | Existing tests/docs encode fixed mock counts and old layout | Generalize tests and split historical vs current production fixtures |

---

# 5. Implementation sequence

## Step 0 — Establish one executable, versioned policy contract

**Dependencies:** none  
**Priority:** P0

Create versioned policy and layout contracts before changing solver logic.

Required work:

1. Version policy separately from layout:
   - `policy_version_id`
   - `layout_version_id`
2. Map report C1–C17 to:
   - model rule;
   - independent validation rule;
   - applicable generation modes;
   - behavioural tests.
3. Use report IDs in structured validation/error details.
4. Define modes explicitly:

```text
INITIAL
REGENERATE_DRAFT
REPAIR_PUBLISHED
FULL_REGENERATION
```

5. Define the mode matrix:
   - hard rules that always apply;
   - initial-only packing;
   - repair relaxations;
   - protected repair objectives;
   - ordinary configurable preferences.
6. Define contribution tiers as registration attributes with minimum validation:
   - Emperor minimum RM5,000;
   - Merit minimum RM3,000;
   - Bodhi minimum RM2,000.
7. Do **not** encode exclusive upper ranges without a confirmed stakeholder rule.
8. Keep:
   - cross-row tier precedence = hard;
   - within-tier contribution row ordering = hard;
   - within-row contribution/seat desirability = soft.
9. Shared boundary row:
   - allow adjacent tiers in the same row;
   - represent higher-tier better-seat placement as a soft preference;
   - exempt/appropriately treat accessibility-constrained units;
   - do not let a UI weight change tier row legality.
10. Record the later 2026 240-seat layout as an amendment from the signed report baseline.

**Deliverables**

- policy schema;
- layout schema;
- rule/mode matrix;
- requirement-to-code traceability table;
- modelling-decision register;
- report amendment note.

**Acceptance**

Every rule has an unambiguous source, mode applicability, model implementation, validator implementation, and test.

---

## Step 1 — Remove generation-to-publication coupling

**Dependencies:** Step 0  
**Priority:** P0

Current public PoC behaviour to replace:

- `/api/solve` writes `output/live_allocation_result.json` after success;
- public loader picks the newest output file;
- public endpoint serves that output;
- UI language implies regeneration/publication coupling.

Required work:

1. A solve creates a **draft plan version** only.
2. Separate:
   - admin draft reader;
   - published participant reader.
3. Introduce an explicit published-version pointer per event.
4. No file mtime may define publication authority.
5. A failed:
   - solve;
   - validation;
   - save;
   - approval;
   - publication
   must leave the existing published pointer unchanged.
6. Handle the case where an event has no published plan.
7. Do not silently import a legacy output as published. Require an import/review path with layout/policy provenance.

**Acceptance**

While an admin generates/regenerates a draft, a participant reading the event still receives the previously published plan.

---

## Step 2 — Refactor request/data schemas and strict input validation

**Dependencies:** Step 0  
**Priority:** P0

Primary areas:

- `models.py`
- `preprocessing.py`
- CLI/request adapters
- JSON Schemas
- frontend allocation/request types

### Participant/status changes

Add:

```json
{
  "registration_status": "CONFIRMED",
  "replacement_for_participant_id": null
}
```

Canonical solver-facing statuses:

```text
CONFIRMED                 eligible
REPLACEMENT_CONFIRMED     eligible
PENDING                   excluded
WAITLISTED                excluded
CANCELLED                 excluded
ABSENT                    excluded
REPLACED                  excluded
```

Host-platform statuses must be mapped through an adapter. Unknown host statuses fail validation.

### Event/operation metadata

Add:

```text
event_id
generation_mode
layout_version_id
policy_version_id
baseline_plan_version_id
preference_profile_version
```

### Ranked preference request

The browser sends order/enabled state, not arbitrary production weights:

```json
{
  "preference_profile_version": "ranked-v1",
  "preferences": [
    { "key": "contribution_seat", "enabled": true },
    { "key": "activeness", "enabled": true },
    { "key": "category_zone", "enabled": false }
  ]
}
```

Array order is authoritative.

### Validation

Before dataclass conversion/model construction:

- validate actual JSON types;
- reject string booleans;
- reject duplicate participant/seat IDs;
- reject invalid/missing fields;
- reject malformed coordinates;
- validate row/position bounds;
- validate `row_index`;
- validate pair definitions;
- validate status;
- validate replacement lineage;
- validate tier minimum;
- validate baseline compatibility;
- validate preference keys/order/profile version.

Do not silently default an unknown preference/status.

### Repair baseline trust boundary

For `REPAIR_PUBLISHED`:

- client sends `event_id` and optionally expected `baseline_plan_version_id`;
- server resolves the actual latest published version;
- stale/mismatched baseline request is rejected or returned as a concurrency conflict;
- client-supplied assignments never become authoritative publication history.

### Count reporting

Return separately:

- submitted registration count;
- eligible registration count;
- excluded registration count;
- allocation-unit count;
- physical-person count where needed;
- required-seat count;
- assignable-seat capacity.

**Acceptance**

Invalid raw data fails before model construction. Every status/profile has a tested deterministic outcome.

---

## Step 3 — Implement versioned 2026 physical layout and accessible domains

**Dependencies:** Step 2  
**Priority:** P0

Current 2026 target:

- 16 rows;
- 16 physical positions per row;
- aisle between 8 and 9;
- block:
  - R06-S05 … R06-S12;
  - R08-S05 … R08-S12;
- row 7 fully available;
- 16 blocked / 240 assignable.

Required work:

1. Create a named/versioned 2026 layout fixture.
2. Preserve a historical 232-assignable-seat fixture from the signed report.
3. Accessible single positions:
   - 1;
   - 2;
   - 15;
   - 16.
4. Accessible Emperor pairs:
   - (1,2);
   - (15,16).
5. Enumerate approved Emperor physical pairs from layout policy.
6. Never infer adjacency from seat priority rank.
7. Keep:
   - physical position;
   - side;
   - desirability/priority;
   - accessibility;
   - blocked state
   as separate concepts.
8. Pair capacity calculations must use valid non-overlapping approved pairs.

**Acceptance**

Exact blocked-set comparison, capacity assertions, aisle/pair assertions, accessibility-domain assertions, and versioned historical/current fixtures all pass.

---

## Step 4 — Rebuild initial-generation shared tier boundaries and packing

**Dependencies:** Steps 2–3  
**Priority:** P0

Required work:

1. Use tier order:

```text
Emperor → Merit → Bodhi
```

2. Build eligible allocation units:
   - Emperor pair units;
   - Merit/Bodhi single-seat units.
3. Replace tier-exclusive row bands with shared boundary-row occupancy/membership.
4. Allow one row to contain adjacent tiers when a higher tier ends partway through it.
5. Derive numbered-section demand from physical seat requirements.
6. Respect Emperor pair capacity while deriving boundary occupancy.
7. Enforce hard row precedence:

```text
higher tier row <= lower tier row
```

with equality allowed on a shared boundary row.

8. Retain hard within-tier contribution row ordering:

```text
contribution[i] > contribution[j]
=> row[i] <= row[j]
```

9. Initial generation / draft regeneration:
   - enforce front-to-back numbered-section packing;
   - enforce centre-out filling according to the final policy;
   - derive the remaining free-seating area.
10. Do **not** encode “higher tier must always occupy the better centre position in a shared row” as a hard rule in v2.
11. Instead, expose shared-boundary desirability to the scorer as a soft component or as part of the contribution/tier desirability cost, without double counting.
12. Accessibility remains hard and can therefore legitimately produce an outer/edge placement even when centre placement would otherwise be preferred.
13. Compare Emperor pairs and single seats using a documented common desirability scale.
14. Re-derive any allowed-row pruning from the new formulation and verify it on tiny exhaustive cases before enabling aggressive pruning.

**Acceptance**

Tests cover:

- Emperor/Merit shared row;
- Merit/Bodhi shared row;
- accessibility on shared row;
- pair/single common desirability;
- no earlier-row packing gaps in initial generation;
- hard tier order;
- soft within-row placement trade-offs;
- mixed-tier row rendering.

---

## Step 5 — Build one authoritative validator and scorer for every proposed plan

**Dependencies:** Steps 2–4  
**Priority:** P0

The validator must be solver-independent.

Input:

```text
normalized participants
+ layout
+ policy
+ generation mode
+ authoritative baseline when applicable
+ proposed assignment
```

Required checks:

1. Exact eligible-ID multiset.
2. No extra/ineligible assignment.
3. Exactly one allocation unit per eligible registration.
4. Correct allocation-unit size.
5. Seat IDs exist.
6. No duplicate physical occupancy.
7. Emperor pair legal.
8. No aisle crossing.
9. Blocked seats unused.
10. Accessibility satisfied.
11. Tier row precedence.
12. Within-tier contribution row ordering.
13. Packing rules only where applicable by mode.
14. Baseline/movement semantics in repair.
15. Consistency among:
    - assignments;
    - occupancy map;
    - row summaries;
    - display representation.
16. Recompute:
    - raw soft components;
    - normalized components;
    - effective mapped coefficients;
    - weighted preference total;
    - movement count/distance;
    - objective stages;
    - tie/canonical metadata.

### Important v2 rule

A shared-boundary centre-preference violation is **not a hard validation failure** unless a future approved policy promotes it to hard. It should appear in the soft quality breakdown.

### Manual edits

Use this same validator/scorer:

- after solver extraction;
- after manual assignment/swap;
- immediately before publication.

Soft degradation may warn the admin but does not by itself block publication.

**Acceptance**

Tampered assignments, duplicate IDs/seats, altered metrics, invalid accessibility, invalid pairings, invalid tier order, and invalid packing are caught independently of solver-reported status.

---

## Step 6 — Implement ranked ordinary preferences, proof metadata, and FEASIBLE handling

**Dependencies:** Steps 4–5  
**Priority:** P1

This step replaces the current raw percentage/slider contract.

### 6.1 Production ordinary preference keys

Use:

```text
contribution_seat
activeness
category_zone
```

Do not expose `movement` as an ordinary ranked preference during `REPAIR_PUBLISHED`.

### 6.2 Versioned rank-to-coefficient mapper

Generic `ranked-v1` mapping:

| Active rank | Integer coefficient |
|---|---:|
| P1 | 40 |
| P2 | 30 |
| P3 | 20 |
| P4 | 10 |
| Disabled / inapplicable | 0 |

These are **relative integer coefficients, not percentages**.

Current production modes expose at most three ordinary preferences, so P4 normally remains unused. Keep the generic mapper versioned rather than inventing a fourth preference solely to consume P4.

Disabled semantics:

1. preserve the saved full preference order;
2. filter disabled/inapplicable items;
3. compact enabled ranks;
4. assign 40, 30, 20, 10 in active order.

Examples:

```text
3 active -> 40 / 30 / 20
2 active -> 40 / 30
1 active -> 40
0 active -> no ordinary preference contribution
```

Do not renormalize to “100%”.

### 6.3 Normalization before weighting

Each ordinary component must be normalized to a documented comparable integer scale before rank coefficients are applied.

Example target:

```text
0..100 normalized penalty per component
```

The mapper does not fix incompatible raw scales by itself.

Persist:

```text
preference_profile_version
full preference order
enabled state
effective weights
normalization_version
policy_version
```

### 6.4 Initial and draft-regeneration objective

Movement is not applicable:

```text
movement = 0
baseline = null
```

Minimize one ordinary weighted preference stage:

```text
WeightedPreference =
  W_contribution * P_contribution_norm
+ W_activeness   * P_activeness_norm
+ W_category     * P_category_norm
```

Then apply deterministic canonicalization/tie handling.

### 6.5 Published-repair objective

Use protected lexicographic intent:

```text
Stage R1: minimize unaffected allocation units moved
Stage R2: minimize movement distance
Stage R3: minimize local packing disruption, if retained by policy
Stage R4: minimize ranked ordinary weighted preference score
Stage R5: deterministic canonicalization
```

The user cannot disable R1/R2.

Do not mislabel the ordinary 40/30/20 mapping as lexicographic priority: lower-ranked preferences may collectively outweigh one unit of a higher-ranked preference. That is intentional for ordinary soft preferences.

### 6.6 FEASIBLE production handling

Production:

```text
OPTIMAL  -> valid reviewable draft if independent validation passes
FEASIBLE -> valid reviewable draft if independent validation passes
```

A `FEASIBLE` result must include:

- actual solver status;
- incumbent objective/stage values;
- best bound where meaningful;
- optimality gap where meaningful;
- elapsed time;
- which stage/proof remains unproven.

For a multi-stage repair:

- only fix/proceed from a stage when the required stage optimum has been proven;
- if the time budget expires with a valid FEASIBLE incumbent in an unfinished higher-priority stage, return that incumbent as reviewable but state that minimal movement/optimality is **not proven**;
- do not claim later stages were optimized if they were never legitimately reached.

### 6.7 Strict benchmark mode

Retain a separate research/benchmark policy such as:

```text
PROVEN_OPTIMAL_ONLY
```

instead of forcing the production UI to discard valid FEASIBLE plans.

### 6.8 Shared total solve budget

Use one configured end-to-end optimization budget. Do not secretly allocate the full 60 seconds to every lexicographic stage/scope.

### 6.9 Canonicalization

Canonicalization is technical reproducibility machinery, not an ordinary business preference.

Only claim canonical completion when higher objectives are sufficiently fixed/proven and the canonical pass completes.

**Acceptance**

- every production ordering maps deterministically;
- disabled items compact correctly;
- raw weight overrides are rejected by production request validation;
- `FEASIBLE` is reviewable in production;
- strict benchmark remains strict;
- repair movement cannot be disabled;
- all-off ordinary preferences remains valid;
- ordinary reordering never changes hard-constraint applicability.

---

## Step 7 — Implement published-plan incremental repair

**Dependencies:** Steps 1–6 plus authoritative published-plan storage  
**Priority:** P1

Required work:

1. Resolve authoritative published baseline by event/version.
2. Compare updated normalized event data with baseline.
3. Derive change set:
   - absence;
   - confirmed replacement;
   - accessibility change;
   - contribution/tier correction;
   - seat becomes unavailable;
   - accepted exceptional late registration.
4. Keep hard:
   - eligibility;
   - exactly-one/uniqueness;
   - valid seats;
   - pair rules;
   - accessibility;
   - tier row precedence;
   - within-tier contribution row ordering.
5. Relax unconditional global front-fill/centre-out packing during repair.
6. Permit a vacancy when preserving the published plan is operationally preferable.
7. Candidate scope sequence:

```text
S0 directly affected/vacated allocation
S1 same row
S2 same tier/boundary region
S3 neighbouring boundary row(s)
S4 whole numbered section
```

8. Freeze unaffected assignments outside the active scope.
9. Expand only when the restricted scope is **proven infeasible**.
10. `UNKNOWN` is inconclusive; do not treat it as proof that a scope is infeasible.
11. Within a chosen scope, apply protected repair objective order from Step 6.
12. Replacement participants must satisfy their own:
    - tier;
    - accessibility;
    - allocation-unit size;
    - pair requirements.
13. Full regeneration is an explicit admin action, never an automatic repair fallback.
14. Store:
    - scope;
    - changed units;
    - frozen units;
    - moved unaffected units;
    - movement distance;
    - vacancy reasons;
    - proof status.

### Interpretation rule

`OPTIMAL` for a restricted repair scope means optimal **within that restricted model**, not globally optimal over every possible wider repair.

**Acceptance**

- simple absence may leave a gap with zero unaffected movement;
- legal replacement can reuse a vacated seat/pair;
- illegal replacement does not inherit an unsuitable seat;
- repair failure does not change the published plan;
- FEASIBLE repair can be reviewed with honest proof metadata.

---

## Step 8 — Complete immutable plan versioning and explicit publication

**Dependencies:** Steps 1–2, 5–7  
**Priority:** P1

Plan-version metadata should include:

```text
plan_version_id
event_id
predecessor_plan_version_id
generation_mode
policy_version_id
layout_version_id
preference_profile_version
normalization_version
effective_weights
solver_status_at_generation
objective/proof metadata
manually_modified
validation_revision/hash
publication_status
created_at/by
approved_at/by
published_at/by
```

Publication states:

```text
DRAFT
UNDER_REVIEW
APPROVED
PUBLISHED
SUPERSEDED
REJECTED
```

Rules:

1. Editing an approved draft invalidates prior approval.
2. A manually edited plan must be freshly validated/rescored.
3. Publication atomically:
   - verifies exact approved revision;
   - revalidates;
   - updates published pointer;
   - supersedes prior published version.
4. Stale/concurrent publication attempts fail safely.
5. Participants only see the latest `PUBLISHED` version.
6. Repair baseline resolves only from published history.
7. Participant-facing output excludes private administrative profile/score/audit fields.

**Acceptance**

No draft/manual edit/failed solve can accidentally become participant-visible.

---

## Step 9 — Integrate frontend review, ranked preferences, manual editor, and publication

**Dependencies:** Steps 3–8  
**Priority:** P1

### 9.1 Layout

Render:

- 16 × 16 physical grid;
- west/east labels;
- centre aisle;
- confirmed obstacles;
- mixed-tier shared rows;
- free-seating area;
- repair vacancies;
- accessible indicators;
- Emperor pair presentation without losing physical seat identity.

### 9.2 Replace slider UI

Remove production raw percentage sliders.

Use one ordered preference component:

```text
Seating preferences

1. Give higher contributors more desirable seats      [ON]
2. Favour participants who attend more PJKIT events   [ON]
3. Match seats to participant categories              [ON]
```

Controls:

- enable/disable switch;
- move up/down;
- keyboard/touch accessible reordering;
- optional drag-and-drop enhancement.

Do not display “40% / 30% / 20%” as user-entered percentages.

Helper copy:

> Higher preferences receive more emphasis during optimization. Compulsory seating rules always apply.

### 9.3 Mode-aware controls

`INITIAL`, `REGENERATE_DRAFT`, `FULL_REGENERATION`:

- show three ordinary preferences;
- movement is hidden/not applicable.

`REPAIR_PUBLISHED`:

```text
Repair policy
✓ Preserve published assignments where possible [system controlled]

Additional seating preferences
1. ...
2. ...
3. ...
```

Movement preservation cannot be disabled.

### 9.4 Generation actions

Replace ambiguous “Regenerate and publish” with:

```text
Generate draft
Regenerate draft
Repair published plan
Full regenerate
Validate edits
Submit for review
Publish
```

Only show actions valid for the lifecycle state.

### 9.5 Manual editing

Preserve/extend existing local manual-editor work if present.

Supported operations:

- assign unassigned eligible registration;
- move;
- swap;
- edit an Emperor pair as one allocation unit where appropriate.

After edit:

1. send complete proposed plan to authoritative backend validator/scorer;
2. show exact hard-rule failures;
3. show soft-score changes;
4. mark plan `manually_modified=true`;
5. remove current-plan `OPTIMAL` claim even if the generating solve was optimal.

Display:

```text
Solver result at generation: OPTIMAL
Current plan: Manually modified
Current hard validation: PASSED
Current preference score: ...
```

Soft-worse but valid edits may be published after approval.

### 9.6 Review UX

Show separately:

- lifecycle state;
- current validity;
- generating solver status;
- optimality/proof details;
- manual-modification state;
- objective component breakdown;
- repair movement summary;
- draft vs published comparison.

### 9.7 Participant view

Guest polling/refresh only observes explicit publication changes.

**Acceptance**

Non-technical staff can configure preference order without numeric optimization knowledge; invalid manual changes cannot be published; guest data changes only after publication.

---

# 6. Preference profile specification

## 6.1 Production request

```json
{
  "preference_profile_version": "ranked-v1",
  "preferences": [
    { "key": "contribution_seat", "enabled": true },
    { "key": "activeness", "enabled": true },
    { "key": "category_zone", "enabled": false }
  ]
}
```

The complete known preference set must be present unless the schema explicitly versions an alternative representation.

## 6.2 Backend mapper

```text
RANK_WEIGHTS_ranked_v1 = [40, 30, 20, 10]
```

Algorithm:

1. validate unique known keys;
2. validate actual booleans;
3. preserve submitted full order;
4. remove mode-inapplicable items;
5. remove disabled items;
6. compact active rank positions;
7. assign rank coefficients;
8. normalize component costs;
9. construct the ordinary weighted objective.

The client cannot submit trusted effective numeric weights in the production API.

## 6.3 Disabled and re-enabled semantics

Persist the **full order**, including disabled items.

Example saved order:

```text
Contribution ON
Category OFF
Activeness ON
```

Active compact mapping:

```text
Contribution -> 40
Activeness   -> 30
Category     -> 0
```

If Category is re-enabled without reordering:

```text
Contribution -> 40
Category     -> 30
Activeness   -> 20
```

This makes re-enabling predictable.

## 6.4 All optional preferences disabled

Valid configuration.

Initial generation then uses:

```text
hard constraints
+ technical canonicalization
```

Repair uses:

```text
hard constraints
+ protected movement stages
+ local packing stage if retained
+ technical canonicalization
```

Do not disable hard C13 row ordering or C17 accessibility just because a related ordinary preference is off.

## 6.5 Comparison caveat

Do not compare total weighted objective values across different:

- enabled sets;
- ordering;
- mapper versions;
- normalization versions

as if they represented the same objective.

For cross-profile analysis, compare normalized component penalties separately.

---

# 7. Production status and error UX

## `OPTIMAL`

User message:

> Valid seating plan generated. The configured objective has been proven optimal for this solve/model.

Admin may:

- review;
- manually edit;
- reject;
- regenerate;
- approve/publish.

## `FEASIBLE`

User message:

> Valid seating plan generated. All compulsory seating rules are satisfied, but the solver did not prove that this is the best possible arrangement within the available solve time.

Admin may:

- review;
- manually edit;
- reject;
- retry/try to improve;
- approve/publish.

## `INFEASIBLE`

Do not show only raw CP-SAT terminology.

Return actionable domain reason where determinable, for example:

```text
Accessible-seat capacity conflict
Emperor-pair capacity conflict
Tier/boundary capacity conflict
No plan satisfies the current compulsory rules
```

Never invent a minimal unsatisfiable core unless actually computed.

## Capacity/pre-model errors

Return before solver invocation where provable:

```text
CAPACITY_EXCEEDED
TIER_CAPACITY_EXCEEDED
INVALID_INPUT
INVALID_REPLACEMENT
STALE_BASELINE
```

---

# 8. Testing and evaluation plan to implement alongside the code

Testing is continuous across Steps 0–9; this section defines the formal FYP2 evaluation suite.

## 8.1 Evaluation dimensions

| Dimension | Main measures |
|---|---|
| Correctness | independent hard-constraint validation, tiny-instance oracle agreement |
| Optimization quality | solver status, normalized component penalties, objective value within same profile, best bound, optimality gap |
| Suitability | contribution/seat concordance or rank-based suitability metrics, stakeholder/historical comparison |
| Robustness | ranked-preference profile testing, disabled preferences, randomized instances, invalid/adversarial inputs |
| Reproducibility | same normalized input/profile/seed -> same completed canonical result where canonicalization completes |
| Repair quality | unaffected movement rate, moved allocation-unit count, movement distance, repair scope, quality loss vs full regeneration |
| Performance | preprocessing time, model-build time, solver wall time, end-to-end function time, memory, branches/conflicts |
| Deployment | AWS Lambda cold/warm latency and artifact/runtime behaviour |

## 8.2 Layout fixtures

Maintain at least:

```text
historical_report_layout
    232 assignable seats

production_2026_layout
    240 assignable seats
```

Do not mix results from them without labelling the layout version.

## 8.3 Deterministic core dataset suite

Recommended minimum: 20 deterministic scenarios.

Suggested categories:

- DS-01–04: tiny known-optimum cases for exhaustive enumeration;
- DS-05–09: realistic PJKIT loads around 100–200 participants;
- DS-10–12: high physical-seat demand / saturation;
- DS-13–14: Emperor-pair, shared-boundary, accessibility, obstacle stress;
- DS-15–16: published absence/substitution repair;
- DS-17: empty event;
- DS-18: overall capacity exceeded;
- DS-19: structural accessibility/pair infeasibility;
- DS-20: malformed/contradictory input.

Do not introduce generic “groups of 8–12” unless group registration becomes a confirmed PJKIT requirement.

## 8.4 Report baseline benchmark

Retain the report’s 150-person / 94-allocation-unit scenario:

```text
112 physical people represented by 56 Emperor registrations
+ 38 single-seat registrations
= 94 allocation units
= 150 occupied physical seats
```

Do not invent a Merit/Bodhi split unless confirmed by a source/fixture.

## 8.5 Ranked-preference configuration testing

Current production has three ordinary preferences.

The complete ordered-enabled profile space is:

```text
k=0: 1
k=1: 3
k=2: 6
k=3: 6
total = 16 profiles
```

This gives a clean exhaustive production-profile test.

For each profile verify:

- hard feasible region unchanged by ordinary preference settings;
- disabled components contribute zero weighted cost;
- effective rank mapping is correct;
- normalized component trade-offs are recorded;
- no preference setting makes a hard rule disappear.

Do not require the geometric plan to change for every reordering.

## 8.6 Randomized-instance robustness

Generate at least 100 reproducible randomized participant sets around a fixed operating load.

Record seed and vary:

- tier composition;
- contribution amounts;
- activeness;
- categories;
- accessibility demand;
- Emperor proportion.

Report:

- median runtime;
- IQR;
- p95 runtime;
- minimum/maximum;
- OPTIMAL rate;
- FEASIBLE reviewable-result rate;
- invalid/infeasible rate by intended scenario class.

## 8.7 Saturation/performance curve

Vary:

- required physical seats;
- allocation-unit count;
- Emperor proportion.

Do not use participant count alone as the complexity axis.

Interpret the curve as an **empirical difficulty region**, not an exact mathematical “combinatorial explosion tipping point”.

## 8.8 Small-instance oracle verification

For tiny cases, enumerate all legal assignments independently.

Require:

```text
CP-SAT optimum == independent enumerator optimum
```

for the same policy/profile.

This validates formulation correctness more strongly than trusting solver status alone.

## 8.9 Repair evaluation

For each published baseline inject:

- absence;
- replacement;
- accessibility change;
- seat blockage;
- multiple absences.

Measure:

```text
unaffected movement rate
moved allocation-unit count
physical seats/people moved
total movement distance
repair scope
repair runtime
ordinary preference score
quality difference vs explicit full regeneration
```

When comparing repair vs global full regeneration, clearly separate:

- stability objective;
- ordinary seating quality.

## 8.10 Runtime measurement

Record separately:

```text
input/schema validation
preprocessing
model construction
CP-SAT wall time
extraction
independent validation/rescoring
serialization
end-to-end latency
```

After Lambda deployment also record:

```text
cold invocation latency
warm invocation latency
```

## 8.11 Visualizations

Recommended primary plots:

1. runtime vs physical-seat demand/allocation-unit count;
2. optimality gap/best bound vs solve time for difficult cases;
3. normalized soft-component trade-offs across ranked profiles;
4. runtime distribution by dataset class;
5. repair movement vs ordinary-quality trade-off.

Dolan–Moré performance profiles are optional and should only be used when comparing multiple solver configurations/budgets/workers over a common suite.

---

# 9. Documentation updates required with implementation

Update together with code; do not leave the README describing the retired prototype behaviour.

## Repository documentation

Update:

- `README.md`
- `CONTEXT.md`
- `GUIDE.md` / production guide
- `docs/mathematical_model.json`
- `docs/code_overview.md`
- CLI usage
- schemas
- frontend help text
- testing/evaluation documentation

### README must stop claiming

- 10 × 12 is the production layout;
- Emperor → Bodhi → Merit is the production tier order;
- every successful production run must be `OPTIMAL`;
- four raw sliders are the production configurator;
- the currently displayed plan is always the reallocation baseline;
- regeneration automatically publishes.

### CONTEXT.md must be corrected

Production terminology should reflect:

```text
Emperor → Merit → Bodhi
shared boundary rows
ranked ordinary preferences
protected published-plan repair
```

Keep legacy assumptions only in clearly named historical/prototype sections if needed.

## Final dissertation amendment areas

Do not retroactively alter the signed interim report. In the final dissertation update the implementation description for:

- admin configuration: “enable/disable and rank soft preferences” rather than “enter weights”;
- FR3 implementation interpretation;
- initial vs repair objective semantics;
- FEASIBLE production handling;
- manual review/edit/publish workflow;
- current 2026 layout amendment;
- shared-boundary implementation;
- status model;
- evaluation methodology.

---

# 10. Policy edge cases still requiring explicit confirmation

Do not silently resolve these in code.

1. **Centre-out packing vs accessibility in tiny/partial rows**  
   Both are currently hard in the report. Certain tiny cases can conflict. Decide whether accessibility creates an explicit packing exception or whether such an instance is intentionally infeasible.

2. **Exact shared-row desirability formula**  
   v2 treats higher-tier centre preference as soft. Define the common seat/pair desirability scale and whether accessibility-constrained units are exempt from pairwise inversion penalties.

3. **Local packing stage during repair**  
   Current recommendation: after movement distance, before ordinary preferences. Confirm if this should remain a protected repair objective.

4. **Tiny demand with all three tiers sharing one row**  
   Do not invent an at-most-two-tier cap unless PJKIT confirms one.

5. **Partial Emperor-pair absence**  
   Current status model operates at registration/allocation-unit level. If only the adjacent guest is absent while the primary participant attends, a separate occupant-level policy is required.

6. **Registration-order business tie-break**  
   Appendix E described first-come-first-served as provisional. Until confirmed, use stable technical canonicalization and do not present ID ordering as registration order.

7. **Tier contribution upper bounds**  
   v2 validates minimum contribution thresholds only. Confirm whether PJKIT wants exclusive numeric ranges or treats the selected tier field as authoritative regardless of higher contribution amount.

---

# 11. Suggested reviewable implementation batches

1. **Policy contract + draft/publication separation**
   - Steps 0–1

2. **Versioned request/status/preferences + strict validation**
   - Step 2

3. **2026 layout + shared-boundary initial model**
   - Steps 3–4

4. **Independent validator/scorer**
   - Step 5

5. **Ranked preference mapper + FEASIBLE production support**
   - Step 6

6. **Published incremental repair**
   - Step 7

7. **Version lifecycle + publication authority**
   - Step 8

8. **Frontend ranked preferences + manual review/edit**
   - Step 9

9. **Evaluation suite + docs + host-platform integration**
   - Sections 8–9

Each batch must include:

- behavioural tests;
- migration notes;
- schema/version impact;
- documentation updates;
- explicit acceptance criteria.

Passing old tests that encode retired PoC assumptions is **not** an acceptance criterion.

---

# 12. Final target behaviour

```text
NEW EVENT
=========
Load eligible registrations
      |
Validate input/layout/policy
      |
Derive shared tier boundaries
      |
Map ranked ordinary preferences
      |
Build + solve CP-SAT
      |
OPTIMAL or FEASIBLE
      |
Independent validation/rescoring
      |
Draft plan
      |
Admin review / manual edit / regenerate
      |
Fresh validation
      |
Explicit publish


PUBLISHED EVENT CHANGE
======================
Latest published plan
      +
Changed event/registration data
      |
Validate + derive repair change set
      |
Protected movement-minimizing repair
      |
Ordinary ranked preferences
      |
OPTIMAL or FEASIBLE
      |
Independent validation/rescoring
      |
New draft version
      |
Admin review / manual edit
      |
Fresh validation
      |
Explicit publish


PARTICIPANT VIEW
================
Event
  |
published_plan_version_id
  |
participant-scoped assignment
  |
latest approved seat/map only
```

Core production principle:

> **Before publication, optimize seating quality freely. After publication, preserve operational stability first, then optimize the remaining seating preferences.**

Core configuration principle:

> **Administrators express relative preference by ordering plain-language rules. The backend owns the mathematical mapping, normalization, validation, and lifecycle policy.**

## Implementation handoff

The repository implementation and verification mapping is recorded in [implementation-status.md](implementation-status.md). The executable formulation is documented in [mathematical_model.md](mathematical_model.md) and [mathematical_model.json](mathematical_model.json). Host deployment and the unconfirmed historical benchmark composition remain explicitly separate acceptance items.
