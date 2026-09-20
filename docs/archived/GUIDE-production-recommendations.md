# FYP Seating Allocation — Production Behaviour and Constraint Decisions Guide

## Purpose

This guide records the recommended production behaviour for the PJKIT Intelligent Automated Seating Allocation System and resolves several modelling questions that arise when moving the current proof-of-concept (PoC) into the production event-management workflow.

The **signed FYP Interim Report is the source of truth for business requirements and approved project scope**. The current GitHub PoC is treated as an implementation prototype and may be changed where its assumptions conflict with the approved report or later stakeholder validation.

The production design should preserve the following principles:

1. The solver is a **decision-support system**, not an autonomous replacement for the PJKIT event administrator.
2. **Hard constraints determine validity**. A plan that violates a hard constraint cannot be published.
3. **Soft constraints determine preference/quality**. They may be traded off, reweighted, or manually overridden by an administrator.
4. Before publication, the system may freely optimize a draft.
5. After publication, **stability takes precedence over cosmetic repacking**: the latest published plan becomes the baseline for incremental repair.
6. A `FEASIBLE` CP-SAT result is a valid reviewable plan even when optimality has not been proven.
7. Manual seat assignment and swapping are allowed before publication, but every edited plan must be revalidated.

---

# 1. Production Plan Lifecycle

The production system should distinguish three solver operations.

## 1.1 Initial Generation

Used when no published seating plan exists for the event.

```text
Participants
+ Venue layout
+ Constraint configuration
+ previousAllocation = null
            |
            v
Full CP-SAT optimization
            |
            v
Draft plan version
            |
            v
Admin review / manual edit / regenerate
            |
            v
Publish
```

Characteristics:

- Movement penalty is zero.
- Global front-to-back and centre-out packing rules apply.
- The solver is free to choose the best seating arrangement under the current rules.
- The result is a **draft** until explicitly approved and published.

## 1.2 Draft Regeneration

Used when the administrator does not like a generated draft but no version has yet been published.

Examples:

- Change soft-constraint weights.
- Change participant selection.
- Correct participant data.
- Change blocked-seat configuration.

Default behaviour:

```text
previousAllocation = null
```

The draft should normally be re-optimized freely because no participant has yet been promised a seat.

## 1.3 Post-Publication Ad Hoc Reallocation

Used when a published plan already exists and participant/event data changes.

Examples:

- Registered participant becomes absent.
- A confirmed replacement takes the place of an absent participant.
- Accessibility information changes.
- A seat becomes unavailable.
- An exceptional late registration is accepted.

```text
Latest published plan
+ Changed participant/event data
            |
            v
Controlled incremental repair
            |
            v
Movement-minimizing draft
            |
            v
Admin review / manual adjustment
            |
            v
Publish new version
```

The latest published plan must remain active until the repaired version is explicitly approved.

---

# 2. CP-SAT Status Handling for Production

The current PoC is intentionally strict and only accepts `OPTIMAL` as a successful result. For production, the system should distinguish mathematical optimality from operational validity.

| CP-SAT Status | Production Meaning | User Experience |
|---|---|---|
| `OPTIMAL` | Valid plan and CP-SAT proved that no better plan exists for the current objective | Show as a reviewable draft with “Optimal solution proven” |
| `FEASIBLE` | Valid plan satisfies all hard constraints, but optimality was not proven within the solver budget | Show as a reviewable draft with “Valid solution found; optimization not yet proven” |
| `INFEASIBLE` | No plan satisfies the current hard constraints | Explain the conflicting capacity/rule condition and provide corrective actions |
| `UNKNOWN` | No valid result was established within the current solve limits | Offer retry / longer solve / review configuration |
| `MODEL_INVALID` | The mathematical model or configuration is invalid | Block generation and surface a technical/configuration issue |
| `INVALID_INPUT` | Input payload or data is invalid | Show the specific data problem |

A `FEASIBLE` plan must **not** be labelled `OPTIMAL`, but it may be reviewed, manually edited, approved, and published if all independent hard-constraint checks pass.

Suggested admin message:

> **Valid seating plan generated.** All compulsory seating rules are satisfied. The solver found a valid plan within the available time but has not yet proven that this is the mathematically best arrangement. You may review, edit, regenerate, or publish the plan.

---

# 3. Manual Assignment and Seat Swapping

Manual assignment and swapping should be supported because the system is designed to assist rather than replace the PJKIT administrator.

Recommended flow:

```text
Generated draft
      |
      v
Admin manually assigns / swaps seats
      |
      v
Independent hard-constraint validator
      |
      +---- FAIL ---> explain violation; block publication
      |
      v
Recalculate soft penalties and quality indicators
      |
      v
Admin review
      |
      v
Publish
```

## 3.1 Hard-Constraint Violation

A manual change that violates a mandatory rule must not be publishable.

Examples:

- Duplicate seat assignment.
- Emperor pair split or crossing the centre aisle.
- Participant moved outside an allowed tier band.
- Accessible participant moved to an invalid position.
- Blocked seat assigned.
- Contribution row-ordering rule violated.

## 3.2 Soft-Constraint Degradation

A manual edit may worsen a soft preference. The system should warn the administrator but allow the edit.

## 3.3 Plan Status after Manual Modification

A plan originally generated as `OPTIMAL` is no longer guaranteed to be mathematically optimal after a manual edit.

Recommended metadata:

```json
{
  "solver_status_at_generation": "OPTIMAL",
  "manually_modified": true,
  "current_hard_constraint_validation": "PASSED",
  "current_objective_value": 2860
}
```

The UI should display:

```text
Initial solver result: OPTIMAL
Current plan: Manually modified
Hard-constraint validation: PASSED
```

Do not continue displaying the current edited plan as `OPTIMAL`.

---

# 4. Decision 1 — Tier Boundaries Within a Shared Row

## Problem

The approved PJKIT requirement allows a boundary row to be shared between adjacent contribution tiers when the higher tier finishes partway through a row.

Examples:

```text
Emperor | Merit
Merit   | Bodhi
```

The unresolved question is whether the higher tier must always receive the best centre seats in the shared row.

## Recommendation

Use the following precedence:

```text
1. Hard structural / safety constraints
2. Accessibility hard constraint
3. Tier-band membership and tier order
4. Shared-row higher-tier seat preference
5. Other weighted soft preferences
```

### Recommended modelling choice

**Do not make “higher tier must receive every better seat in a shared row” a hard constraint unless PJKIT explicitly confirms that rule.**

Instead:

- The shared boundary row itself is valid for both adjacent tiers.
- The higher tier receives a **strong soft preference** for the better seat-priority positions within that row.
- Accessibility remains hard and may place a higher-tier participant at an outer/side seat.
- Other weighted preferences may influence the remaining seat choices.

### Important production rule

The **tier order across rows remains hard**.

If Emperor and Merit share Row 9:

- no Merit unit may appear in a row before the Emperor band;
- Row 9 may contain both;
- within Row 9, Emperor should normally receive the better available positions;
- accessibility or other mandatory rules may override that preference.

---

# 5. Decision 2 — Eligible Registration Statuses

## Problem

The approved report contains the hard rule:

> Only participants of eligible status may be seated.

However, the current participant model has no explicit status field.

## Recommendation

Add an explicit registration/allocation status to the solver input.

Suggested field:

```json
{
  "registration_status": "CONFIRMED"
}
```

Recommended canonical statuses:

| Status | Solver Eligibility | Meaning |
|---|---:|---|
| `CONFIRMED` | Yes | Participant is registered and should be allocated |
| `REPLACEMENT_CONFIRMED` | Yes | Confirmed replacement participant should be allocated |
| `PENDING` | No | Registration is not finalized |
| `WAITLISTED` | No | Not yet admitted into the numbered seating allocation |
| `CANCELLED` | No | Registration cancelled |
| `ABSENT` | No | Participant will not attend |
| `REPLACED` | No | Original registration has been superseded by a replacement |

If the host Netizen eXperience platform uses different registration labels, create a **mapping layer** from platform statuses to these solver-facing canonical statuses rather than coupling the solver to application-specific strings.

## Absence representation

```json
{
  "participant_id": "P078",
  "registration_status": "ABSENT"
}
```

The record remains available for audit/history but is excluded from the new allocation.

## Replacement representation

Replacement participant:

```json
{
  "participant_id": "P205",
  "registration_status": "REPLACEMENT_CONFIRMED",
  "replacement_for_participant_id": "P078"
}
```

Original participant:

```json
{
  "participant_id": "P078",
  "registration_status": "REPLACED"
}
```

This preserves traceability instead of overwriting the original record.

---

# 6. Decision 3 — Reallocation Versus Packing

## Problem

The initial-generation rules require front-to-back packing and centre-out filling. After publication, an absence may create a vacancy. Enforcing strict global packing could move many participants merely to remove one empty seat.

That behaviour conflicts with the approved objective of controlled incremental repair.

## Recommendation

Use **mode-specific packing semantics**.

### Initial Generation

Packing rules are hard:

```text
front_to_back = HARD
centre_out = HARD
movement = not applicable
```

### Pre-Publication Regeneration

Packing remains hard:

```text
front_to_back = HARD
centre_out = HARD
movement = normally zero / ignored
```

### Post-Publication Reallocation

Published-plan stability takes precedence over global repacking.

Recommended priority:

```text
1. Safety / eligibility / uniqueness / pairing / tier legality
2. Preserve unaffected published assignments
3. Satisfy the changed participant(s)
4. Minimize number of unaffected participants moved
5. Minimize movement distance
6. Restore local packing where possible
7. Optimize ordinary soft preferences
```

Global packing should therefore **not remain an unconditional hard constraint during repair**.

Recommended implementation:

```text
generation_mode = INITIAL
    enforce_global_packing = true

generation_mode = REPAIR
    enforce_global_packing = false
    local_packing_penalty = enabled
    movement_minimization = dominant
```

A vacated seat may legitimately remain empty after an absence if filling it would require unnecessary displacement of already-published participants.

## Repair-scope expansion

Recommended repair strategy:

```text
Scope 0: vacated seat / directly affected allocation unit
Scope 1: same row
Scope 2: same tier band
Scope 3: neighbouring boundary row(s)
Scope 4: whole numbered seating section
Fallback: explicit full regeneration
```

The system should expand the repair scope only when the smaller scope cannot produce a valid repair.

---

# 7. Decision 4 — Within-Row Contribution Preference

## Problem

The approved report distinguishes:

- **hard row ordering**: a participant with higher contribution must not be placed in a later row than a participant with lower contribution within the same tier;
- **soft seat-priority preference**: higher priority/contribution should generally receive more desirable seat ranks.

The unresolved question is whether contribution order within the same row should also be hard.

## Recommendation

Keep **within-row contribution placement soft**.

This is consistent with the approved distinction between mandatory row ordering and weighted seat-rank preference.

### Hard rule

For two participants `i` and `j` in the same tier:

```text
if contribution[i] > contribution[j]
then row[i] <= row[j]
```

### Soft rule within the same row

If both participants are already in the same row:

```text
higher contribution should prefer better priority_rank
```

but this may be traded against:

- accessibility;
- participant category;
- activeness;
- other configured soft preferences.

### Avoid double counting

The production model should clearly define whether the existing `priority_seat` soft cost already includes contribution rank.

If it does, do not add a second independent “within-row contribution” cost that counts the same preference twice.

Recommended formulation:

```text
C6 / priority-seat mismatch
    = contribution-derived seat desirability preference
      within the participant's valid tier / row context
```

---

# 8. Recommended Objective Hierarchy

The system should distinguish **validity**, **stability**, and **preference quality**.

## Initial Generation

```text
Hard constraints
    must all pass

then minimize:
    priority-seat mismatch
  + activeness mismatch
  + category-zone mismatch
  + shared-boundary tier preference
  + deterministic tie-break
```

Movement cost:

```text
0
```

## Post-Publication Repair

Recommended lexicographic intent:

```text
Priority 1:
Minimize number of unaffected participants moved

Priority 2:
Minimize total movement distance

Priority 3:
Minimize ordinary weighted preference penalties

Priority 4:
Deterministic tie-break
```

If implemented as one integer objective, coefficients must be scaled so that a lower-priority objective can never outweigh one unit of a higher-priority objective.

---

# 9. Recommended Input Additions

Suggested participant fields:

```json
{
  "participant_id": "P001",
  "registration_status": "CONFIRMED",
  "replacement_for_participant_id": null,
  "contribution_amount_rm": 5000,
  "contribution_tier": "EMPEROR",
  "requires_accessible_seat": false,
  "participant_category": "GENERAL_DEVOTEE",
  "events_joined_last_2_years": 8
}
```

Suggested solve request metadata:

```json
{
  "generation_mode": "INITIAL",
  "baseline_plan_version_id": null
}
```

or:

```json
{
  "generation_mode": "REPAIR_PUBLISHED",
  "baseline_plan_version_id": "PLAN-V7"
}
```

Recommended enum:

```text
INITIAL
REGENERATE_DRAFT
REPAIR_PUBLISHED
FULL_REGENERATION
```

---

# 10. Recommended Plan Version Metadata

```json
{
  "plan_version_id": "PLAN-V8",
  "event_id": "EVENT-2026-01",
  "generation_mode": "REPAIR_PUBLISHED",
  "predecessor_plan_version_id": "PLAN-V7",
  "solver_status_at_generation": "FEASIBLE",
  "manually_modified": true,
  "hard_constraint_validation": "PASSED",
  "publication_status": "UNDER_REVIEW"
}
```

Recommended publication states:

```text
DRAFT
UNDER_REVIEW
APPROVED
PUBLISHED
SUPERSEDED
REJECTED
```

Only `PUBLISHED` may be exposed to participants.

---

# 11. Required PoC Changes Before Production Integration

## 11.1 Accept FEASIBLE as a reviewable result

Current PoC behaviour:

```text
OPTIMAL -> success
FEASIBLE -> OPTIMAL_NOT_PROVEN error
```

Recommended production behaviour:

```text
OPTIMAL -> reviewable plan
FEASIBLE -> reviewable plan with warning / optimality gap
```

Benchmark mode may retain `require_optimal = true`.

Production mode should allow `require_optimal = false` without discarding the feasible assignment.

## 11.2 Add solver-facing registration status

Update the participant model and schema with:

```text
registration_status
replacement_for_participant_id
```

Exclude ineligible records during preprocessing.

## 11.3 Separate generation mode from previous allocation

Do not infer the business operation only from whether `previous_allocation` exists.

Pass an explicit mode:

```text
INITIAL
REGENERATE_DRAFT
REPAIR_PUBLISHED
FULL_REGENERATION
```

## 11.4 Make packing mode-aware

Initial generation:

```text
global packing = hard
```

Repair:

```text
global packing = relaxed
movement preservation = dominant
local packing = soft
```

## 11.5 Support shared boundary rows

The approved report permits a row to be shared between adjacent tiers.

The final production tier-band derivation must therefore support:

```text
Emperor -> Merit -> Bodhi
```

with shared boundary rows when one tier ends partway through a row.

The PoC must not assume tier-exclusive boundary rows if that contradicts the approved requirement.

## 11.6 Support post-generation manual editing

Add:

```text
manual assignment
seat swap
hard-constraint revalidation
objective reconstruction
plan-version audit metadata
```

A manually modified plan may be published only if all hard constraints pass.

---

# 12. Final Behaviour Summary

```text
NEW EVENT
=========
Validate
  |
Full optimization
  |
OPTIMAL / FEASIBLE
  |
Independent validation
  |
Draft
  |
Admin review / edit / regenerate
  |
Revalidate
  |
Publish


PUBLISHED EVENT CHANGE
=====================
Latest published plan
  +
Participant/event change
  |
Incremental repair
  |
Preserve unaffected assignments first
  |
OPTIMAL / FEASIBLE
  |
Independent validation
  |
New draft version
  |
Admin review / edit
  |
Revalidate
  |
Publish new version


INFEASIBLE
==========
Do not show only a technical error.

Explain:
- what rule/capacity condition failed;
- which participants/seats are involved where determinable;
- what the administrator can change.

Keep the previously published plan unchanged.
```

---

# 13. Decision Summary

| Question | Recommended Decision |
|---|---|
| Shared boundary row | Higher tier gets a strong preference for better positions, but accessibility/hard rules override; do not make exact within-row tier superiority hard unless PJKIT confirms it |
| Eligible statuses | Add explicit solver-facing statuses; allocate only confirmed/confirmed-replacement records |
| Vacancy after absence | Preserve published assignments; global packing becomes secondary during repair |
| Within-row contribution | Keep soft; row-level contribution ordering remains hard |
| FEASIBLE status | Show as a valid reviewable plan, clearly labelled “optimality not proven” |
| INFEASIBLE status | Explain the actual conflict and offer corrective actions |
| Manual edits | Allow before publication; revalidate all hard constraints and recompute quality metrics |
| Manually edited OPTIMAL plan | Do not continue claiming the edited plan itself is optimal |
