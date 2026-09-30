> Archived historical guidance. For the current workflow and setup, see the [project README](../../../README.md) and [frontend README](../../../frontend/README.md).

# Seating dashboard redesign: flow and implementation backlog

Status: historical redesign plan. The September 22 scope change below supersedes the safeguard requirements and implementation claims in this document.

## Current branch scope — September 22

The safeguard implementation and its tests are preserved on `codex/seating-safeguards` (initial snapshot `ff9e5a7`). They have been removed from `codex/seating-dashboard-redesign`: no Submit/check command, C13/packing findings, advisory acknowledgements or review gate at working-draft publication. B07 and the safeguard portions of B08 belong to the separate branch. Save, stale-write protection, snapshot publication, venue display and printing remain.

Current path: **Save draft → Finish editing → Continue to publication → Publish seating plan**. This is staff confirmation, not an automated safeguard check. The solver's own constraints and output validator remain intact.

See [flow audit and C13 reproduction](../../seating-safeguard-separation.md). The sections below record the earlier plan and are not the current branch's acceptance criteria.

Branch: `codex/seating-dashboard-redesign`, created from fetched `origin/main`.

## Confirmed scope

- The user reviewed this flow and authorized P0 implementation before P1 work.
- Focus on frontend interaction and workflow, retaining the CP-SAT solver and its allocation logic. Supporting persistence, validation and publication integration changes are identified explicitly below.
- Venue remains 256 physical positions: 240 assignable seats and 16 structurally blocked positions. The user's confirmation supersedes the older 232-seat values in the attached documents.
- English controls initially, Traditional Chinese participant names and hall landmarks. Per subsequent user direction, retain main’s neutral minimalist component styling and accent colours. Use fictional names in demo fixtures.
- First generation → admin inspection/manual editing → admin review → Submit → safeguards → fix findings or acknowledge permitted alerts → publication → venue display.
- Holding dock sits beside the map in this phase and supports dragging allocation cards in both directions. A floating dock is deferred.
- Figma work continues separately. The supplied Figma file is a future visual handoff, not a dependency for this proposal; its contents were not inspected for this audit.
- Attached DESIGN.md and refactor brief are requirement references. Their instructions to build Figma deliverables or immediately implement do not supersede the user's review-first request.

## Proposed user flow

| Step | Staff experience | State and next action |
| --- | --- | --- |
| 1. Generate | Recognizable empty hall, readiness summary and Generate draft. Settings stay secondary. Real generation progress; recoverable error on failure. | Solver creates a private draft. Nothing becomes public. |
| 2. Inspect | Draft opens in Read mode. Search Chinese names; select seats or checklist rows to inspect the same allocation. | Edit plan deliberately enables mutations. |
| 3. Edit | Move, swap, update displayed names, check names/attendance/seats, lock and annotate. A pair remains one allocation spanning two seats. | Save working changes independently of submission checks. Undo/redo covers operations and metadata. |
| 4. Use dock | Side panel shows docked individuals/pairs with names, previous location and reason. Drag map → dock or dock → map; equivalent buttons are available. | No registration is deleted. Dock count stays visible. Unresolved dock items block publication, but not saving work. |
| 5. Review | Finish editing opens a read-only summary of changes, exclusions, unchecked records and dock items. Selecting an item returns to its location. | Admin presses Submit when ready; this starts safeguard checking, not publication. |
| 6. Check | Check the exact saved revision server-side. Show actionable findings beside the map, with affected names and locations. Always check front-to-back and centre-out packing, including repair-derived drafts. | Fix required issues or acknowledge only findings explicitly permitted by policy. |
| 7. Resolve | Fix in Edit mode, or choose Continue without changes for acknowledgeable alerts. This means accepting a finding, not discarding edits or deleting a participant. | Acknowledgements record actor, revision, finding and reason where required. Any edit invalidates previous checks/acknowledgements as appropriate. Re-submit after fixes. |
| 8. Publish | Show final summary and explicit Publish seating plan confirmation. Staff know that the previous public version remains visible until success. | Revalidate the exact revision and atomically publish. Failure preserves the prior public version. |
| 9. Display | Open venue display showing only the published map, Chinese names, hall landmarks and optional publication time. | Full-screen/print controls available outside the normal map-only presentation. Later edits use a separate draft. |

The current backend has DRAFT → UNDER_REVIEW → APPROVED → PUBLISHED transitions. Preserve these internal boundaries while presenting the simpler admin flow above. Do not introduce a new reviewer role or auto-publish simply because a check passes. The same authorized admin may complete review and publication using existing permissions.

## Safeguard policy

Temporary packing gaps are allowed while rearranging the working draft. Strict checks run on Submit and again at publication. Findings name the actual empty location and affected occupied location, rather than only displaying C15/C16.

| Finding | Proposed behavior |
| --- | --- |
| Duplicate assignment, blocked seat, invalid pair, aisle crossing, missing eligible allocation or unresolved dock item | Must fix; no Continue without changes action. |
| Existing hard eligibility, accessibility, tier and contribution rules | Preserve server enforcement; must fix. |
| C15 front-to-back or C16 centre-out gap | Must fix before publication, including after releasing an absent partner’s seat. |
| Valid but unusual placement or optional priority warning | May acknowledge and continue without changes. |
| Unchecked name/attendance/seat-review markers | Show readiness counts; exact blocking policy should be confirmed before implementation. Proposed default: advisory unless the business rules require completion. |
| Unsaved changes, stale revision, failed save or unavailable validation | Publication unavailable until safely saved and freshly checked. |

Submission without changes is limited to advisory alerts. The staff-authorized partner-absence exception changes Emperor allocation size only; it does not override packing, accessibility, tier order or other mandatory checks.

## Workspace layout

- Compact header: event, Participants, Settings, Details, Versions, Venue display.
- Context bar: Draft/Published, Read/Edit/Review, accurate save/connection state and next action.
- Main canvas: 三寶佛 / FRONT at the top, 西單 left, 東單 right, centre aisle, row labels 1–16, actual structural blocks and ENTRANCE / BACK. Read names before secondary status markers.
- Edit mode: dock beside the map, initially about 280–320 px wide. Detail/checklist panels share a secondary panel region rather than stacking permanent sidebars. Keep dock drop targets reachable during moves.
- Search: registered and displayed names, result navigation, centring, dimming unrelated allocations and persistent selection.
- Counts: registrations, represented people, occupied seats, empty assignable seats, blocked positions and dock items use explicit units.
- Fit/zoom and internal panel scrolling keep core operations usable at 1366×768 and 1920×1080 without page-level vertical scrolling.

## Current implementation audit

| Area | Existing baseline | Required change |
| --- | --- | --- |
| Dashboard | `seat-dashboard.tsx` has placement state, undo, participant/statistics panels and permanent configuration | Explicit modes, map-first shell, checklist, dock and recovery state. |
| Manual operations | `seat-editor.ts` already moves/swaps whole allocations, checks physical pair destinations and returns displaced unassigned registrations to the list | Extend transactions with dock provenance, locks, metadata, previews, redo and equivalent non-drag controls. |
| Map/search | `seat-map.tsx` supports drag, selection, focus scrolling and dimming | Paper landmarks, name-first styling, view controls and mode-safe interactions. |
| Save | `plan-actions.tsx` calls manual edit; `PlanStore.edit` validates every edit before saving a new version | Persist incomplete working drafts separately from validated results; never label unsaved/local work as server-saved. |
| Workflow | `/api/plans` permits manual/submit/approve/publish/reject/get; store checks revisions and publication pointer | Structured preflight findings and revision-bound acknowledgements; keep final server authority. |
| Packing | `production_validator.py` checks C15/C16 only outside REPAIR_PUBLISHED | Submission/publication-specific strict packing checks, leaving solver generation/repair objectives unchanged. |
| Public route | Header calls `/my-seat` “Guest view”; this is a participant lookup route | Add dedicated venue presentation using a deliberately scoped published-only response. Preserve participant lookup behavior. |
| Protection | Store already protects exact revisions, transitions and stale publication pointers | Extend stale-write protection to mutable working drafts; do not assume current protection covers the new dock/metadata. |

## Ordered implementation backlog

| ID | Priority | Deliverable and acceptance | Dependencies |
| --- | --- | --- | --- |
| B01 | P0 | Record approved flow and safeguard policy; reconcile document capacity references with confirmed production layout. Inventory UI/API contracts and keep solver payload compatibility. | User review |
| B02 | P0 | Working-draft model for allocation placements, dock entries, two display occupants, verification markers, locks, notes and exclusions. Separate registered/display names. Derive counts from canonical venue and registration data. | B01 |
| B03 | P0 | Supporting persistence/API: save incomplete working state, restore it after refresh, reject stale writes and expose accurate save errors. Keep working drafts separate from validated/published snapshots. | B02 |
| B04 | P0 | Map-first shell with Read/Edit/Review modes, paper landmarks, actual 16 blocked positions, name-first cards, status/readiness bar and secondary settings/details. | B02 |
| B05 | P0 | Safe moves/swaps, side dock drag/drop, destination previews, pair atomicity, locks, non-drag alternatives and undo/redo. All involved people remain accounted for. | B02–B04 |
| B06 | P0 | Display-name editing including spouse name, name/attendance/seat-review markers, notes, absence/replacement actions and synchronized searchable checklist. Absence does not delete registration data. | B03–B05 |
| B07 | P0 | Review summary and Submit-triggered safeguard panel. Check strict packing and other rules on the server; navigate findings to the map. Implement only approved acknowledgement policy. | B01, B03, B05–B06 |
| B08 | P0 | Final confirmation and publication integration with exact-revision checks, fresh validation, audit records and preserved public snapshot on failure. | B07 |
| B09 | P0 | Dedicated published-only venue display with full hall at 1920×1080, no admin controls in presentation, correct landmarks and print fallback. | B04, B08 |
| B11 | P1 | Revision/regeneration impact preview, preservation of manual metadata and version history polish. Generating a revision never changes the public plan. | B03, B08 |
| B12 | P1 | Accessibility and viewport verification: keyboard operation, labels, focus, non-colour status cues, long Chinese names, compact laptop and venue sizing. | Throughout B04–B11 |
| B13 | Deferred | Floating dock, optional presentation search, first-use guidance and visual alignment with completed Figma handoff. | Core flow accepted |

Implementation checkpoints: (1) persisted Read/Edit map and dock; (2) checklist and manual review; (3) safeguards and publication; (4) venue display and reliability. Review each checkpoint using a realistic fictional event dataset.

## Verification plan

- Unit: move/swap/pair/dock transactions, no loss or duplicates, lock behavior, metadata undo/redo, explicit count derivation and strict C15/C16 checks including repair-derived input.
- Integration: Read mode cannot mutate; incomplete draft can save/restore; stale saves fail safely; registered names remain unchanged by display edits; warnings are revision-bound; direct API publication cannot bypass approved safeguards.
- Workflow: generate → inspect → move through dock → swap → review → Submit → fix a packing gap → acknowledge an advisory alert → Publish → venue display.
- Failure: save/network/publication failure, refresh with docked items, two concurrent editors and revision changes after checking. Prior public content remains unchanged.
- UI: drag and button paths produce equivalent results; selection stays synchronized; names and hall fit intended laptop/TV viewports; print output excludes admin controls.
- Run relevant Python and frontend tests, frontend typecheck/lint and production build when implementation is ready. Read the repository's installed Next.js documentation before coding, as required by `frontend/AGENTS.md`.

## Approved safeguard interpretation

Continue without changes applies to advisory alerts only. Packing violations remain blocking. The separately approved partner-absence exception releases a seat and does not exempt any resulting vacancy from packing checks.

## Implementation update — P0

The user approved implementation and added partner absence to P0. The user explicitly chose to **release** an absent Emperor partner's seat for reassignment. The contributor remains Emperor, with unchanged registered identity, contribution and priority. A recorded reason authorizes a one-seat operational allocation; restoring the pair returns it to the dock for two-seat placement. The solver still generates pairs. Released vacancies receive normal strict packing checks; they are not reserved or exempted.

P0 implementation delivered on this branch:

- B01: approved workflow and 240/16 production geometry retained.
- B02–B03: revision-checked SQLite working drafts, incomplete/docked state persistence, distinct registered/display names and separate saved/public states.
- B04: viewport-contained paper hall, Read/Edit/Review modes, Chinese names/landmarks, accurate counts, selection, search and zoom.
- B05: adjacent dock, drag and button move/swap previews, atomic pair operations, lock enforcement and undo/redo.
- B06: editable occupant names, three verification markers, notes, absence/restoration, linked replacement registrations and synchronized searchable checklist. Companion unlink/relink is included as P0.
- B07: Submit-triggered server safeguards, strict C15/C16 including repair drafts, blocking findings, priority/verification/partner-absence alerts and explicit acknowledgements.
- B08: exact-revision publication, acknowledgement audit records, fresh independent validation and atomic public-pointer update. The old publication endpoint cannot bypass an active working-draft review.
- B09: staff-launched `/venue`, latest-published-only geometry/names, full-screen mode and print/save-PDF styling. Participant lookup remains independently scoped.

Synthetic names: the production fixture, fixture generator and frontend editor fixture now use reproducibly shuffled fictional Traditional Chinese names; some Emperor pairs have distinct partner names. Display edits never rewrite authoritative registered names.

Checks performed: Python regression and operational lifecycle tests; frontend editor/workspace tests; TypeScript; ESLint; Ruff for touched Python files; production build. The build emits a pre-existing-style dynamic filesystem tracing warning in the production service integration. Browser-based visual/interaction checks were not completed because launching the automated browser was declined. Consequently, laptop/TV visual acceptance, actual drag gestures and printed output still require manual review; these are not claimed as verified.

P1/P2 remain separate: floating dock, full regeneration impact comparison/adoption UI, deeper version comparison, richer recovery/reconciliation, final Figma alignment and guided onboarding. Existing generated version history is inspectable, but a newly generated plan does not silently replace an already saved working draft.

## Visual correction — main branch styling retained

The user supplied a minimalist screenshot and explicitly requested preservation of main's card backgrounds, borders, sizing and accent colours. The implementation therefore reuses the existing design tokens and seat-card classes: 56px cards, existing rounded border/padding, neutral occupied/empty surfaces, ring selection and unchanged tier-dot palette. The hall uses the existing 1000–1400px canvas width; fit-to-view scales the whole hall. Shared UI primitives and global accent tokens are unchanged. Custom green/cream surfaces introduced during the first pass were removed.

Latest verification: 111 Python tests passed. After the visual correction, all 15 frontend tests, frontend typecheck/lint and the production build passed. Automated browser execution remains unapproved, so rendered laptop/TV/print checks are still pending.

## Pair display and synthetic-name update

Emperor pairs now render as one card spanning their two physical seat tracks, with the contributor’s Chinese display name. A persisted `partner_name_edited` flag switches the pair to two named cells only after staff edit the partner name. Both states share one group selection outline. Partner absence remains a single seat and the other position remains available. Venue snapshots carry only the display flag and primary name, not private notes. Synthetic fixtures now default to unnamed partners; the explicit fixture migration updates recognized placeholder names in the current private working draft while retaining staff edits and published snapshots.

## Seat interaction update

Occupied-seat clicks open a details/action modal in Read or Edit mode. The side panel is reserved for the holding dock and does not open just because a seat is selected or Edit mode starts. Dragging an allocation outside the venue reveals the dock; dropping outside docks it atomically. Cancelled drags preserve placements. Sending an allocation to the dock closes its modal and reveals the panel. The dock can be closed/reopened, and dock cards support drag-back or modal move/swap actions. Review/safeguard findings now use a modal as well, preserving the dock-only side-panel behavior.

## Readability and pair re-merging

Page typography is larger; seat display names use 12–16px responsive sizing instead of 10px, while existing card dimensions and colour tokens remain unchanged. Previously split Emperor pairs merge automatically when contributor and partner display names match after removing whitespace (including tabs, newlines, non-breaking/ideographic spaces and zero-width spacing). Comparison preserves letter case and entered names. Empty names do not count as a match. The edit-history flag remains recorded, so different names split the pair again; published venue display uses the same rule.

## Venue presentation scope correction

B10 is removed from scope: no offline read-only mode, unsaved-navigation guard or conflict-recovery controls. B03 save errors, dirty-state checks and server-enforced stale-write protection remain. The venue requires an online connection and clears the map when its publication request fails.

Venue cards show published Chinese occupant names only, without identifiers, seat indices or PAIR labels. Printing uses the reference’s landscape arrangement, Chinese landmarks, compact white bordered cells and a dummy Chinese event title. Existing published placeholder names are hidden; staff must publish corrected Chinese names to fill those cells.
