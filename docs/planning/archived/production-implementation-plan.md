# PJKIT solver and application implementation plan

Prepared: 2026-09-15. Planning only; this document does not implement the changes.

## Sources and decision precedence

- Latest stakeholder decisions in this conversation: obstacle coordinates, shared-row tier preference, and accessibility positions.
- [Production behaviour guide](GUIDE-production-recommendations.md), read in full (744 lines), including lifecycle, statuses, manual edits, eligibility, repair, scoring, metadata, and final decision summary.
- [Signed interim report](../../../FYP1/[Signed]DariusLeeShin_22003269_InterimReport.pdf): Table 3.4, printed pp. 39–41; FR1–FR17, pp. 48–49; NFR1–NFR8, pp. 50–51; Appendix E, pp. 55–57.
- [2026 venue reference](../../../FYP1/diagrams/2026_PJKIT_Event_Seating_Plan.png).
- Current Python and frontend code, including existing uncommitted manual-editor work. Preserve those changes during implementation.

Apply explicit later stakeholder decisions over earlier assumptions. Use the report as the baseline and the adopted production guide to define lifecycle-dependent refinements. Record departures from the report rather than claiming its original wording already contains them. Do not edit the signed PDF.

## Confirmed baseline

| Topic | Implementation decision |
|---|---|
| Venue | 16 rows × 16 physical positions, 256 seats |
| Sides | West/西单 positions 1–8 on the left; East/东单 positions 9–16 on the right |
| Aisle | Between positions 8 and 9 |
| Obstacles | Rows 6 and 8, positions 5–12 inclusive; row 7 fully available |
| Capacity | 16 blocked seats; 240 assignable seats |
| Tier precedence | Emperor → Merit → Bodhi |
| Contribution thresholds | Report minimums: Emperor RM5,000, Merit RM3,000, Bodhi RM2,000. Proposed exclusive integer-RM ranges: ≥5,000; 3,000–4,999; 2,000–2,999 |
| Pair allocation | Emperor registrations consume two seats in one approved physical pair; a merged display cell still represents two physical seats |
| Accessibility | Singles at positions 1, 2, 15, 16; Emperor pairs (1,2), (15,16). Centre-aisle seats are not accessible by this policy |
| Shared boundary | Adjacent tiers may share a row; higher-tier units receive centre precedence, with an accessibility exception |
| Within-tier contribution | Higher amount must never be in a later row; within-row contribution-to-seat matching remains soft |
| Eligibility | Only CONFIRMED and REPLACEMENT_CONFIRMED consume new demand |
| Initial/draft regeneration | No previous allocation; movement zero; global front and centre-out packing hard |
| Published repair | Published version is the baseline; preserve assignments before repacking; gaps are permitted; local packing becomes a preference |
| Production result | Independently valid OPTIMAL or FEASIBLE can be reviewed; publication is a separate explicit operation |
| Manual edits | Draft-only changes; validate and recompute metrics before acceptance/publication; retain generation provenance without claiming the edited plan is optimal |

Accessibility remains hard under report C17 and guide §4. The user's reference to accessibility priority is not permission for a low soft weight to allow inaccessible placements. Positions 2 and 15 are now explicitly eligible; do not retain the earlier outermost-only proposal.

## Priority and contradiction register

| Priority | Current conflict | Required resolution | References |
|---|---|---|---|
| P0 | Successful regeneration writes directly to a guest-visible file | Separate draft generation, approval, and publication; public lookup reads only an explicitly published version | FR9, FR13–14; guide §§1,10 |
| P0 | Frontend and solver trust incomplete validation | Validate original inputs and independently verify the complete proposed assignment; publication uses server-side validation | C1–5, C10–13, C17; FR15–16; guide §3 |
| P0 | Wrong obstacles, accessibility positions, tier order, and contribution ranges | Introduce versioned 2026 policy/layout and update physical domains | C3–4, C12, C17; Appendix E; latest decisions |
| P0 | Tier-exclusive bands leave empty earlier rows | Implement shared boundary rows and whole-section packing | C12, C15–16; guide §11.5 |
| P1 | Every regeneration uses the displayed plan as its previous allocation | Add explicit operation mode; only repair resolves the authoritative published baseline | C9; FR9; guide §§1,9,11.3 |
| P1 | Full repacking and weighted movement can displace unaffected people | Mode-aware constraints, controlled scopes, and count-before-distance repair | C9; FR9; guide §§6,8 |
| P1 | FEASIBLE discarded even when require_optimal=false | Extract and validate incumbent; distinguish validity from proof | FR7; guide §§2,11.1 |
| P1 | Contribution omitted from priority-seat cost; pair/activity ranks differ | Define integer, auditable contribution/activity/category preference costs without double counting | C6–8; guide §§7–8 |
| P1 | Existing editor has local checks but no authoritative validation/save/publication workflow | Extend current editor with server validation, rescoring, draft persistence and provenance | FR8, FR10, FR14–16; guide §3 |
| P2 | Additive tie-break does not prove a unique canonical layout | Canonicalization after fixing higher objectives; report completion honestly | C14; NFR8 |
| P2 | Fixed 122-registration tests and stale 10×12 documentation | Generalize production validation; introduce report-baseline and 2026-layout evaluation suites | NFR1, NFR4, NFR6 |

## Implementation sequence

### Step 0 — Establish one executable policy contract

Dependencies: none. Priority: P0.

1. Version the policy and layout separately from the solver package.
2. Map every report C1–C17 to a model rule, validation rule, and behavioural test. Retain report IDs in error details instead of relying on the unrelated existing HC numbering.
3. Specify applicability by mode: INITIAL, REGENERATE_DRAFT, REPAIR_PUBLISHED, FULL_REGENERATION.
4. Record the 2026 capacity change and the guide's repair exception to C12's compact packing/C15/C16. Hard tier precedence and within-tier contribution row ordering still apply during repair.
5. Treat the latest shared-row decision as stronger than guide §4's generic strong-soft recommendation: propose conditional hard centre precedence with a documented accessibility exception. Other weighted preferences cannot reverse this rule. Confirm its exact comparison/exemption semantics in the formulation before encoding; see the decision notes below.
6. Keep within-row contribution preference C6 separate from cross-tier precedence. Manual overrides of ordinary soft preferences remain allowed.

Deliverables: policy schema, traceability table, mode matrix, source-linked modelling decisions.

Acceptance: one example per mode has an unambiguous applicable rule set; no rule is silently relaxed by a UI weight or arbitrary config flag.

### Step 1 — Remove generation-to-publication coupling

Dependencies: Step 0. Priority: P0; implement this before integrating new solver outputs.

Current evidence: `frontend/src/app/api/solve/route.ts` writes `live_allocation_result.json` on success. `frontend/src/lib/allocation.ts` chooses the newest output by modification time; `api/allocation/route.ts` serves it to the public view. Weight controls say “Regenerate and publish.”

1. Make generation return/store a draft only.
2. Split admin draft loading from public published-plan loading. File modification time is not publication authority.
3. Do not automatically mark an existing legacy output as published or compliant with the new policy. Require an explicit import/review path with layout and policy provenance.
4. Remove automatic publication wording and actions. Until the full publication service exists, generation must have no public side effect.
5. Keep the current published pointer unchanged on solve, validation, persistence, or review failure. Handle “no published plan” explicitly.

Acceptance: regenerate a draft while a guest reads the published version; guest version stays unchanged. A failed solve cannot replace the public result.

### Step 2 — Refactor request/data schemas and strict input validation

Dependencies: Step 0. Priority: P0.

Primary files: `models.py`, `cli.py`, `preprocessing.py`, `schemas/`, frontend `allocation-types.ts` and solve request types.

1. Add registration_status and replacement_for_participant_id; keep original absent/replaced records for audit.
2. Introduce a host-status adapter. Unknown statuses fail validation; never silently become CONFIRMED.
3. Add event_id, generation_mode, layout_version_id, policy_version_id and baseline_plan_version_id.
4. Resolve a repair baseline on the server from the event's published version. Do not trust a client-supplied seat map as publication truth.
5. Validate raw JSON types before dataclass conversion; reject strings masquerading as booleans, truncated monetary values, invalid ages, duplicate IDs, missing required fields and malformed maps.
6. Check semantic invariants: unique row/position coordinates, valid bounds, row_index consistency, seat counts, valid non-crossing pairs, contribution/tier consistency, and baseline compatibility.
7. Check replacement links: valid original registration, same event, no self-links/cycles or duplicate active replacements. A replacement's own tier/accessibility/pair needs must be satisfied; it does not automatically inherit a legally unsuitable seat.
8. Return submitted, eligible, excluded, registration-unit, physical-seat-demand and capacity counts separately. Distinguish excluded registrations from erroneously unassigned eligible registrations.
9. Use a versioned adapter for legacy fixtures; do not weaken production validation to accept old shapes.

Acceptance: the earlier string-boolean/negative-age example fails before model construction; every status has a tested outcome; invalid replacements produce structured input errors.

### Step 3 — Implement the 2026 physical layout and accessible domains

Dependencies: Step 2. Priority: P0.

Primary files: `floor_plan_generator.py`, `data/floor_plan.json`, pair-domain construction, layout schema.

1. Block exactly R06-S05 through R06-S12 and R08-S05 through R08-S12.
2. Assert all 16 row-7 positions are available and total assignable capacity is 240.
3. Define accessible singles at 1,2,15,16 and accessible pairs at (1,2),(15,16).
4. Keep adjacency, desirability, side labels and display grouping separate. Never infer two-seat capacity from one displayed name cell.
5. Enumerate and validate approved pairs once from layout configuration. Capacity checks must count non-overlapping available pair capacity, not arbitrary overlapping candidate count.
6. Version old layouts so earlier published assignments can be interpreted without silently applying changed obstacles.

Acceptance: exact blocked-ID comparison; row 7 availability; 256 total/16 blocked/240 assignable; valid-pair and accessibility assertions.

### Step 4 — Rebuild initial-generation tier boundaries and packing

Dependencies: Steps 2–3. Priority: P0.

Primary files: `preprocessing.py`, `cp_sat_model.py`, `result_formatter.py`.

1. Use Emperor → Merit → Bodhi and report-based contribution thresholds.
2. Preserve Boolean registration-to-seat/pair assignment, exactly-one allocation and physical-seat at-most-one occupancy.
3. Replace exclusive bands with tier row membership and boundary-row occupancy counts. A row can contain more than one tier; result data must describe tier membership at assignment/seat level, with row summaries derived from occupants.
4. Derive sound occupancy targets from eligible physical-seat demand and layout capacity, carrying a partial tier into the same row as the next tier.
5. Retain pair feasibility when deriving Emperor targets. Do not count a free individual seat as available Emperor capacity.
6. Enforce hard cross-tier row precedence allowing equal rows at boundaries, and retain hard within-tier contribution row ordering.
7. Enforce global initial front-fill and per-side centre-out fill over available seats, with a partial last numbered row and an explicit remaining free-seating area.
8. Define shared-row centre precedence on a common physical desirability ordering, not by directly comparing pair ranks 1–8 to individual ranks 1–16. Define ties between mirrored sides consistently with east-first desirability.
9. Re-derive allowed-row pruning from the new constraints; prove it sound with tiny exhaustive instances rather than adapting the old exclusive-band pruning by guesswork.
10. Produce specific capacity/preprocessing errors where provable, leaving coupled feasibility to CP-SAT.

Acceptance: small E/M and M/B shared-row cases; no earlier available-row gaps in initial generation; no excluded eligible solution from pruning; accessible boundary exceptions; correct output tier colours on mixed rows.

### Step 5 — Build the authoritative validator and scorer for any proposed plan

Dependencies: Steps 2–4. Priority: P0. Develop its tests alongside Steps 3–4.

Primary files: `validator.py`, `cost_calculator.py`; proposed reusable validation/rescoring service.

1. Accept the original normalized participants, layout, policy, mode and baseline together with the proposed placements.
2. Verify the exact multiset of eligible participant IDs: no omitted, extra, duplicated or ineligible registration; exactly one unit of the correct size per eligible registration.
3. Recheck all applicable hard rules from physical assignments, independently of solver variables and declared success flags.
4. Verify seat_ids, embedded seats, occupancy maps, row summaries and display assignments agree; reject inconsistent representations.
5. Remove fixture-specific totals and success=OPTIMAL assumptions from validity checks.
6. Recompute raw component costs, normalization, weighted totals, movement metrics and objective stages from source inputs. Do not merely multiply reported costs by reported weights.
7. Return rule IDs, affected registrations/seats, and actionable details; do not claim a minimal unsatisfiable core unless actually derived.
8. Use this same backend service after solving, after manual edits, and immediately before publication. Client checks improve feedback but are not authoritative.

Acceptance: duplicate-ID tampering fails; contradictory assignment/seat maps fail; altered penalties fail; valid non-default dataset passes; initial gaps fail while permitted repair vacancies pass.

### Step 6 — Correct objectives, proof metadata and FEASIBLE handling

Dependencies: Steps 4–5. Priority: P1.

1. Define C6 as contribution-derived within-tier seat desirability, retaining documented personal-priority treatment where justified. Avoid adding a duplicate contribution penalty.
2. Define C7 activity relative to the relevant tier, and use compatible desirability scales for singles and pairs. Specify equal-score behaviour and rounding.
3. Keep C8 category suitability configurable; explicitly decide whether pair costs are per registration or per physical seat and normalize consistently.
4. Keep initial and draft-regeneration movement exactly zero. Report main preference penalty separately from solver encoding and canonicalization terms.
5. Implement lexicographic stages or rigorously bounded integer dominance. Prefer staged optimization where a combined coefficient risks overflow or loss of numeric precision in output consumers.
6. Fix an objective stage only when its optimum has been proven. If time expires with FEASIBLE, retain the valid incumbent and report which priorities remain unproven; do not assert exact lexicographic optimality.
7. Share one overall configured solve budget across optimization stages and later repair-scope attempts; do not allocate the full budget independently to each stage.
8. For require_optimal=false, extract and independently validate FEASIBLE assignments. For strict benchmarks, retain OPTIMAL_NOT_PROVEN handling.
9. After primary objectives are fixed, canonicalize assignments in stable normalized-ID/seat order using a deterministic method. Report canonicalization completion separately. FEASIBLE under a time limit does not guarantee the same canonical result across runs.
10. Record status, objective vector, bounds, absolute/relative gap where meaningful, scope, timing and generation provenance. Never label a manual edit OPTIMAL based on the generating solve.
11. Replace production-facing numeric weight configuration with ordered, enabled preference keys. Derive weights on the backend using the versioned mapper specified below. Keep this weighted preference stage distinct from mandatory constraints and lexicographic repair stages.

Acceptance: FEASIBLE can be reviewed in production; strict mode remains strict; lower priorities cannot override higher proven stages; canonical tests include equal-cost participants and reordered equivalent input.

### Step 7 — Implement published-plan incremental repair

Dependencies: Steps 2–6 and an authoritative baseline reader from Step 1/8. Priority: P1.

1. Compare normalized event data against the published version to derive changes and directly affected units: absence, replacement, changed accessibility/tier/contribution, new unavailability, accepted late registration.
2. Keep eligibility, pairing, uniqueness, valid seats, accessibility, cross-tier row order and within-tier contribution row order hard.
3. Disable unconditional global front-fill and centre-out constraints in repair; measure local packing as a lower-priority preference.
4. Do not recompute tightly packed initial bands and force everyone into them after an absence. Use baseline-aware candidate rows, preserve legal tier order and widen permitted boundaries as scope expands.
5. Try scopes: directly affected/vacated unit → same row → same tier band → neighbouring boundary rows → whole numbered section. Freeze unaffected assignments outside the active scope.
6. Expand on proven restricted-scope infeasibility. UNKNOWN means inconclusive, not proof that a scope cannot work; expose retry/budget exhaustion and any deliberate escalation reason.
7. Within the active scope, minimize unaffected moved registration units first, then total surviving-registration movement distance, then local packing, ordinary weighted preferences, and canonical tie-break. Report physical people/seats moved separately from allocation-unit count.
8. Give confirmed replacements legal opportunities to reuse vacated seats. Never force a single/pair or tier-incompatible replacement into them.
9. Store scope, frozen assignments, changed units, moved unaffected units, distances and vacancy reasons.
10. A full regeneration is an explicit administrator operation producing another draft; never silently use it as a repair fallback or publish it automatically.

Acceptance: an absence can leave a gap without moving unaffected registrations; legal replacement reuses seats; obstacles/accessibility changes trigger limited repair; all scope/budget failures preserve the published plan.

An OPTIMAL restricted repair is optimal for that restricted model. Stopping at the first feasible scope prioritizes locality and does not prove global movement optimality over all scopes. UI and research results must state that distinction.

### Step 8 — Complete draft/version persistence and explicit publication

Dependencies: Steps 1–2,5–6. Priority: P1. Backend work can precede completion of repair.

1. Introduce immutable plan-version snapshots, predecessor references, event identity, source-input/policy/layout versions, generation status, modification provenance and validation revision/hash.
2. Support DRAFT, UNDER_REVIEW, APPROVED, PUBLISHED, SUPERSEDED, REJECTED with explicit transitions.
3. Store manual changes as draft revisions; editing invalidates prior approval/validation until rechecked.
4. Publish only the exact approved and freshly validated revision. Atomically update the event's published-version pointer and supersede the previous version; reject stale concurrent publication attempts.
5. Resolve public lookup and repair baselines through that pointer. Prevent a draft, newest file, or bundled demo snapshot from being treated as published production data.
6. Use an adapter for host-platform identity/administrative authorization and persistence. A local development store may support tests, but production should use the report's host-platform integration and version storage, not arbitrary local output files.
7. Provide participant-scoped public responses rather than the complete administrative allocation payload, consistent with FR13/NFR5. Keep private profile, contribution, status, and audit data out of guest responses.

Acceptance: explicit approval required; failed/stale publication leaves the old version active; guest cannot read a draft; editing after approval requires reapproval; version history retains predecessor and policy context.

### Step 9 — Integrate frontend layout, editor and review operations

Dependencies: Steps 3–8. Priority: P1.

Primary files: `allocation-types.ts`, `allocation.ts`, both API routes, seat dashboard/map, weight controls, public view, `seat-editor.ts`, and existing editor tests.

1. Preserve and extend the existing drag/drop, participant picker, assignment dialog and local placement work; do not rebuild these blindly.
2. Render the corrected 2026 west/east labels, 16×16 physical grid, row-6/8 obstacles and fully available row 7. Group Emperor seats for presentation without losing individual physical IDs.
3. Derive tier colours per assignment; support mixed-tier rows, free seating, repair vacancies and blocked cells as distinct states.
4. Replace “Regenerate and publish” with mode-specific Generate draft, Regenerate draft, Repair published plan, Validate edits, Review and Publish actions.
5. Do not pass a current manual draft as the published movement baseline during ordinary regeneration. Explain that regeneration may discard manual placements unless explicit locks are introduced later.
6. Send complete proposed placements to backend validation/rescoring on manual save/validation; display exact hard-rule failures and soft-score changes.
7. Allow incomplete manual drafts to be saved as invalid/in-progress if needed, but never approve/publish them. Soft degradation alone does not block publication; mandatory tier/structural rules do.
8. Show separate lifecycle state, current validity, generation status, manual-modification state, proof/scope details and objective breakdown.
9. Make movement controls mode-appropriate: no misleading movement slider on initial generation, no ordinary slider that defeats count-first repair.
10. Guest polling observes publication changes only. Add draft-vs-published comparison and movement highlighting for admin review.
11. Include export of the approved/published layout with its version and appropriate participant data, matching the 2026 appearance (FR11).
12. Replace percentage sliders with one ordered list of plain-language preferences, each with an enable/disable switch and accessible move-up/move-down controls. Drag-and-drop is optional; percentages remain internal. Persist the ordered selection with the draft and show a review summary before generating.

Acceptance: an invalid drag/drop placement cannot be published; a valid soft-worse edit can; editing clears current-optimal claims; guest map changes only after explicit publish; layout screenshots match the confirmed physical coordinates.

### Preference-priority mapper — added stakeholder requirement

Implement the backend mapper in Step 6 and its frontend controls in Step 9. Define the request shape during Step 2. This is an adopted UI direction; repair movement exposure remains a policy decision because the existing guide gives it mandatory precedence.

**User-facing behaviour**

- Present preferences as statements rather than cost-function identifiers. Proposed labels: “Give higher contributors more desirable seats,” “Favour participants who attend more events,” “Match seats to participant categories,” and, only if policy permits ordinary weighting, “Keep participants close to their previous seats.”
- Each configurable preference has an enabled switch and one unique place in an ordered list. Show “Highest preference,” “Second preference,” etc. Do not describe these ranks as guaranteed satisfaction or strict lexicographic priority.
- Prefer an ordered list with move-up/move-down buttons (keyboard and touch supported); drag-and-drop can supplement it. If dropdowns are used instead, selecting an occupied rank swaps/reorders items atomically rather than permitting duplicate ranks.
- Disabled preferences remain visible, labelled “Not considered,” without an active rank. Preserve their relative location in the saved full ordering so re-enabling is predictable.
- Explain once: “Higher preferences receive more emphasis. Compulsory seating rules always apply.”
- Changing the controls changes draft configuration only. It neither reruns the solver nor publishes a plan automatically.

**Developer-controlled mapping**

| Enabled preference rank | Integer weight |
|---|---:|
| P1 | 40 |
| P2 | 30 |
| P3 | 20 |
| P4 | 10 |
| Disabled / not applicable in this mode | 0 |

Proposed disabled-item semantics: filter out disabled and mode-inapplicable preferences, preserve the remaining relative order, then assign the first k weights. Thus three active preferences receive 40/30/20, two receive 40/30, and one receives 40. Do not leave an empty priority slot or redistribute weights through rounded percentages. The sum need not equal 100: these are relative integer objective coefficients, not percentages of satisfaction. With all four active they happen to total 100.

If all optional preferences are disabled, allow the operation using the applicable hard constraints, protected repair/local-packing stages and technical canonicalization. Display that ordinary preferences are off. C13 contribution row ordering and C17 accessibility remain enforced even if their related soft preferences are disabled.

Normalize component costs on a documented comparable basis before applying the mapper. Keep pair-versus-single treatment explicit. A 40/30/20/10 mapping does not by itself make differently scaled costs comparable. Nor does 40 dominate the combined 30+20+10: lower preferences may collectively outweigh an improvement in P1. This trade-off is intentional in a weighted model; strict precedence belongs in a separate hard/lexicographic policy.

**Mode and protected-rule boundaries**

- INITIAL and REGENERATE_DRAFT: movement is not applicable, baseline is null, movement cost is zero. Show it as unavailable with a brief explanation or omit it from the active list; it must not consume a priority slot.
- REPAIR_PUBLISHED, recommended pending the stakeholder answer: preserve the guide's protected movement-count-first and movement-distance-second stages. Show “Preserve published seats” as a fixed repair policy, not a draggable/disableable item. Rank the ordinary contribution, activity and category preferences only after the protected stages.
- The current PoC has four cost components, but that does not establish four freely configurable preferences in every production mode. Do not invent a fourth ordinary preference merely to use P4.
- Shared-row higher-tier centre precedence, accessibility and all other mandatory rules remain outside this list. Local packing remains governed by the repair policy unless separately approved as an ordinary preference.
- If the stakeholder instead makes movement an ordinary optional preference, update the guide/traceability and repair objective explicitly; do not claim count-first movement minimization still holds.

**Request, storage and validation**

Example production request fragment (array order is authoritative):

```json
{
  "preference_profile_version": "ranked-v1",
  "preferences": [
    { "key": "priority_seat", "enabled": true },
    { "key": "activeness", "enabled": true },
    { "key": "category_zone", "enabled": false }
  ]
}
```

- Backend validates unique known keys, actual boolean types, the allowed mode-specific key set and supported profile version; missing required preference entries are rejected rather than silently changing defaults. Protected/inapplicable settings cannot be made active by modifying the request.
- Backend is the source of truth for effective weights. Browser requests contain ordering/enabled state, not arbitrary trusted numeric weights. A separate explicitly developmental benchmark path may accept raw weights without defining the production UI contract.
- Save the full preference ordering, enabled state, effective integer weights, mapper version, normalization version and applicable policy with each generated plan version. Replay uses that version's mapping rather than whatever defaults exist later.
- Use the same profile for solver scoring and authoritative manual-edit rescoring. Preserve raw component metrics for auditing even when a disabled component contributes zero to the weighted objective.
- Keep weighted quality values contextual to their policy/profile; do not compare totals across different enabled sets or mappings as if the scoring system were unchanged.

**Acceptance tests**

1. Every supported ordering maps to the intended unique weights; repeat requests produce identical mappings.
2. Disabling the first, middle or last item compacts active ranks correctly; re-enabling restores predictable ordering; all-off remains valid configuration.
3. Duplicate/unknown keys, string booleans, unsupported profiles and attempts to override protected policies fail validation.
4. Initial generation has zero movement cost regardless of stale client state; repair preservation cannot be disabled under the recommended policy.
5. Reordering/turning off a soft preference changes only the intended objective coefficients, never hard-constraint applicability.
6. Keyboard, pointer and dropdown paths (if provided) produce the same ordered request; saving/reloading retains settings.
7. Validation and manual rescoring reconstruct costs using the saved mapper/normalization versions; altering draft controls does not alter the published version.

### Step 10 — Evaluate, migrate and document

Dependencies: preceding steps. Priority: P2; tests are added continuously, not postponed until this step.

1. Parameterize the synthetic generator instead of fixing 122 records. Keep registrations, people, and occupied-seat demand distinct.
2. Retain the report's proposed 150-person benchmark: 56 Emperor registrations plus 38 single-seat registrations (94 units). Merit/Bodhi split remains unspecified by the production guide.
3. Use the confirmed 2026 layout with 240 assignable seats as the current target and explicitly label the change from the report's 232-seat baseline. Retain a separate historical layout fixture only for reproducible comparisons.
4. Test small exhaustive instances for feasibility/optimality against an independent enumerator; include mixed boundaries, accessibility/packing conflicts, statuses, replacement lineage and manual edits.
5. Exercise API lifecycle flows, publication failures/concurrency, repair scope/time limits and participant access boundaries.
6. Measure initial/draft/repair runs separately: valid-result rate, optimality proof rate, objective stages, scope, moved units/people, distance, runtime including preprocessing/validation, and correctly measured memory.
7. Record interpreter, OR-Tools version, platform, seed, worker count, input hashes and budget. Separate deterministic completed-optimum claims from timed FEASIBLE behaviour.
8. Update README, code overview, mathematical model, CLI documentation and UI copy to the same policy version. Add an amendment/traceability document for the report refinements; preserve the signed report.
9. Integrate/deploy through the host platform only after functional and performance acceptance. Read the installed Next.js local documentation before frontend implementation as required by frontend/AGENTS.md.

## Policy edge cases and remaining decisions

These should be tracked explicitly; do not repeat questions already resolved by the guide.

1. **Question 7 is not answered in the guide.** It contains no evaluation dataset or Merit/Bodhi split. Proposed planning baseline: 56 Emperor registrations + 38 singles, split pending; this does not block generalizing the solver.
2. **Shared-row precedence is stronger in the latest instruction than in guide §4.** Proposed rule: conditional hard higher-tier centre precedence with accessibility exceptions, keeping ordinary within-tier C6 soft. Formalize how a pair is compared with a single and when an accessibility exception applies. Document that an ordinary soft weight cannot reverse the confirmed cross-tier rule.
3. **Accessibility versus hard packing can be genuinely infeasible.** For example, a sole eligible participant requiring positions 1,2,15,16 cannot also satisfy a full centre-out chain with just one occupied seat. Do not silently call this valid. Return the conflict under the current policy; any initial-generation packing exception needs an explicit policy decision. Repair already has the guide's packing relaxation.
4. **Local packing placement in repair hierarchy:** guide §6 places it before ordinary preferences; §8 does not list it. The proposed hierarchy retains it after movement distance and before ordinary preferences.
5. **Scope-first repair versus global movement optimality:** apply the guide's scope-first strategy and describe proof relative to the chosen scope. A globally optimal movement benchmark must solve the unrestricted repair model separately.
6. **Tiny demand and multi-tier rows:** sequential packing can place all three tiers in one row when counts are small. The report/guide illustrates two adjacent tiers but does not define this degenerate case. Do not add an unexplained at-most-two-tiers cap that forces gaps; model ordered consecutive tiers unless a policy cap is approved.
7. **Partial Emperor absence:** the current registration-level status marks the whole pair. Preserve two-seat unit semantics; treating only one companion as absent or permitting a one-seat replacement into a pair requires explicit occupant-level policy/data rather than an implicit conversion.
8. **Registration order tie-breaking:** Appendix E D13 calls first-come-first-served provisional. Use stable normalized identifiers for technical canonicalization until a registration-order business preference is confirmed; do not present ID ordering as registration ordering.

## Suggested reviewable change batches

1. Policy/traceability plus draft-publication separation (Steps 0–1).
2. Versioned input contracts, strict validation and 2026 geometry (Steps 2–3).
3. Shared boundaries, initial packing and independent validation (Steps 4–5).
4. Preferences, FEASIBLE support and proof/canonical metadata (Step 6).
5. Published repair with baseline-aware domains and bounded scope (Step 7).
6. Version lifecycle, authoritative manual validation and frontend integration (Steps 8–9; foundational version storage can be introduced earlier for repair).
7. Report-baseline evaluation, documentation and host integration readiness (Step 10).

Each batch should include behavioural tests and an explicit migration path. Passing old tests that encode the wrong policy is not an acceptance criterion.
