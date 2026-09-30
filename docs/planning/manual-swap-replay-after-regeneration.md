# Preserve manual swaps after regeneration

Status: proposed enhancement, documentation only. Prepared 2026-10-01.
Suggested implementation branch: `codex/preserve-manual-swaps` (not created by this planning task).

## Purpose and boundary

Preserve staff decisions as an ordered, durable series of swaps between registration IDs. When new participant data or preference priorities produce a fresh solver map, replay those decisions in the application layer and save the resulting private draft as a new version.

The solver function, Lambda solver payload, constraints and optimization objective remain unchanged. The application owns the manual-decision store, asynchronous-result correlation, replay, conflict handling and derived draft. Replay must not write modified assignments back into the immutable raw solver response or claim its optimality/metrics describe the edited map. Publishing remains a separate explicit action.

This extends the [local history proposal](manual-edit-history-proposal.md). That proposal records actual before/after edits for undo and recovery; this enhancement additionally records portable swap intent. A placement diff alone cannot reconstruct the intended sequence reliably.

## Current integration points

Observed in this repository when planning:

- `frontend/src/lib/workspace.ts`: `move` exchanges whole equal-size registrations, moves to empty seats, and rejects incompatible destinations. `dock` temporarily removes an allocation. Neither persists a replayable sequence.
- `frontend/src/components/seat/seat-dashboard.tsx`: keeps an in-memory undo timeline and saves working state through `/api/workspace`. The regeneration `onResult` callback opens the returned `plan_version_id` and resets the timeline.
- `frontend/src/components/seat/weight-controls.tsx`: submits preference-based `REGENERATE_DRAFT`, remembers a successful result if opening fails, and retries opening without solving again.
- `frontend/src/app/api/solve/route.ts` and `frontend/src/lib/production-service.ts`: await a local Python process, not a deployed asynchronous Lambda job pipeline. Registration import/update and cloud job orchestration remain integration work.
- `src/seat_solver/production/workspace.py`: revision-checked working state and per-base saved workspaces; these are not a complete immutable manual-edit ledger.

The future integration point is between successful generated-result retrieval and adoption of a new working draft. Do not first replace the current workspace and only then discover that replay failed. Preserve the current workspace until the candidate can be adopted atomically.

## Meaning of “lock participant IDs”

Recommended interpretation: retain the identities and order of manual decisions, not fixed seat coordinates and not a solver constraint. Name changes and seat-number changes do not alter identity. `participant_id` must identify the same event registration across imports and generations; never regenerate IDs from input ordering or match by display name. An Emperor payer/companion allocation is one registration unit, not two replay IDs.

For an intent `SWAP(A, B)`, resolve A's and B's **current allocations in the replay candidate**, then exchange both allocations atomically. Resolve again before every later operation. Recorded original seat IDs are audit evidence only.

Example using single-seat registrations:

| Stage | A | B | C |
| --- | --- | --- | --- |
| New solver result | R1-S1 | R2-S1 | R3-S1 |
| Replay sequence 1: A ↔ B | R2-S1 | R1-S1 | R3-S1 |
| Replay sequence 2: B ↔ C | R2-S1 | R3-S1 | R1-S1 |

Sequence is material: reversing the operations gives a different result. A can appear in many operations; locking it after its first swap would be incorrect. Two intentionally recorded A ↔ B swaps cancel in final placement but remain two distinct audit events.

This preserves the **swap relationship**, not “A must remain in row 1”, “A must be ahead of B”, or a guaranteed preferred seat. If the new solver has already reversed A and B, replay will exchange them again. Coordinate pinning or relative-order rules would require separate intent types and product decisions; do not silently substitute those meanings. Confirm this semantic distinction before implementing the branch.

## Store design

Use an application-owned manual-decision repository with a storage adapter. For a local, single-browser first release, extend the proposed IndexedDB/Dexie history store. For decisions shared by multiple staff, the application backend must be authoritative, with browser storage serving as an unsaved recovery cache. The existing SQLite service can host that repository locally; the [DynamoDB proposal](dynamodb-seating-schema.md) is a future deployment mapping, not an implemented dependency.

Do not make browser-local data the sole shared store: another staff device or a completion processed after the browser closes must be able to load the same saved decisions. Actor identity is audit metadata; saved shared intent is scoped to event and draft lineage, while private unsaved sessions are also scoped to the user.

Proposed logical records (names are not existing APIs/tables):

| Record | Essential fields |
| --- | --- |
| Intent event | `operationId`, `eventId`, `lineageId`, monotonic `sequence`, `kind`, `registrationIds: [A,B]`, `actorId`, `createdAt`, `sourceDraftVersionId`, `sourceRevision`, original before/after seat bundles, schema version |
| Intent-set snapshot | `intentSetId`, `revision`, parent reference, ordered active operation IDs, content hash, capture timestamp; immutable once referenced by a generation |
| Draft version | immutable `draftVersionId`, parent draft, raw solver plan ID, final working-state reference/hash, participant-input revision, layout/policy versions, intent-set reference and replay-run reference |
| Generation context | `generationRequestId`, event/lineage, source draft/revision, frozen intent-set reference/hash, participant-input/layout/preference revisions or hashes, request status, expected adoption revision |
| Replay run | `replayRunId`, unique replay key, generated plan ID/hash, intent-set hash, replay-engine version, outcome, ordered per-operation outcomes, candidate reference/hash, conflict details |

Append the edit's actual before/after values and its portable intent in the same application-store transaction as the new working revision. An operation ID is generated once and reused on transport retry. Allocate sequence under a revision check, not with timestamps or browser counters alone. Never deduplicate by participant IDs: repeated swaps can be deliberate.

The intent set is an immutable ordered view of active decisions, not every event ever recorded. Undo/redo and disabling preservation append audit events and produce a new intent-set revision. An undone swap is excluded from the active set; do not replay both the swap and an inverse just to emulate undo, since intermediate validity may have changed. Redo restores its order on the current history branch. New edits after undo create a branch and invalidate that branch's redo path. Non-tail removal creates a new intent-set revision and requires a complete fresh replay; later decisions may depend on it.

Existing saved drafts without a ledger have an empty portable intent set. Do not infer historical swaps from their final seat differences. Explain that automatic preservation starts with newly recorded decisions.

## Which edits are portable in the first release

| Edit | History | Automatic regeneration replay |
| --- | --- | --- |
| Occupied A ↔ occupied B, equal-size complete units | Record full edit and IDs | Yes, when still valid |
| Single or Emperor pair moved into empty space | Record | No; there is no second registration ID identifying the destination |
| Dock/undock or replacing an occupant from the dock | Record | No; not a two-seated-registration swap |
| Name/note change | Record | Separate metadata merge by ID; never overwrite refreshed authoritative registration data |
| Mixed-size/multi-registration rearrangement | Record | Deferred explicit compound intent; do not guess decomposition into pairwise swaps |
| No-op or rejected edit | Optional diagnostic only | No portable swap |

Include direct editing and review-screen edits in capture if they meet the same two-registration swap contract. Replay itself must not append new user intents, otherwise every regeneration duplicates history.

When non-portable edits exist, list them before regeneration and retain them in the old draft. Do not advertise that all manual placements are automatically preserved. The first release guarantees attempted preservation of recorded compatible swaps, with explicit conflict reporting for the rest.

## Regeneration and asynchronous adoption

Proposed application workflow:

1. Load the chosen saved draft and its intent-set reference. Enter edit mode; accepted swaps update the working state and journal together. Before regeneration, flush and save the current edits, or stop with a recoverable save error. Never launch using an unsaved in-memory-only sequence.
2. Capture an immutable generation context at one source revision, including the ordered intent set and the exact authoritative participant/layout/preference snapshot references. New participants keep stable IDs. Changed input requires a new context rather than modifying an in-flight one.
3. Submit the ordinary solver request through the application job adapter. Store replay context beside the job; do not add manual locks or history to the solver request. Show generation progress. Recommended first release: keep the source map viewable but disable edits while its generation is pending; other tabs/users still require revision checks.
4. On completion, resolve the exact job/request and its immutable raw result. Verify event, request/input references and successful solver-output acceptance before replay. Completion does not imply adoption. Failed, cancelled or obsolete work leaves the current draft intact.
5. Clone the raw result into a candidate. Replay the frozen active intents in ascending sequence. Always start from raw generated assignments, including when retrying. Keep an operation-by-operation report and perform final structural/entitlement validation.
6. If replay succeeds, stage an immutable derived draft and atomically adopt it only when the source workspace revision and current generation token still match. Store candidate, lineage, intent-set reference and replay result together. Use fresh verification for the derived map under the application's applicable policy.
7. If the source changed, retain the candidate as unadopted history and require reconciliation with the current draft. An old completion must never silently replace newer edits or a newer selected generation. If replay conflicts, enter resolution without changing the current saved draft.
8. On reload, query the persisted generation/replay status rather than starting another solve or replaying on top of an edited workspace. Once adopted, normal manual editing creates new operations for the next intent-set revision.

The application adapter may use polling or completion notifications. Its contract must support duplicate, delayed and out-of-order completion without relying on a single mounted React component. This plan does not select or implement the Lambda transport.

Use a unique replay key containing event, raw generated-plan ID/hash, intent-set hash and replay-engine version. Repeated delivery returns the existing replay run/derived version. A new raw plan gets a new run with the same intent set. Atomic adoption is a conditional store operation, not a UI-only flag.

Example across generations: G1 + [swap 1, swap 2] produces D1. G2 starts from its own raw map and replays [1,2] exactly once. If D1 added swap 3, G2 uses [1,2,3]. Never take D1's already-replayed map and apply [1,2] again. Branches inherit the selected parent's intent set only; they do not combine every event's historical swaps.

## Replay validation and conflicts

For each swap, verify distinct IDs, both present and currently eligible, both fully seated, equal current entitlement, and legal destination bundles for both registrations. Preserve complete Emperor pairs, actual layout-approved adjacency, accessibility and non-overlap. A pair changing from two seats to one is a conflict rather than an automatic resize. The current `move` behavior can return a displaced registration to the dock when the source is unseated; the replay contract must reject that case explicitly.

Use current generated registration requirements and layout, not old metadata copied from the journal. Reuse/extract the application validation rules in the future branch without changing solver code. Old seat audit references changing alone do not cause a conflict; identity/entitlement/destination compatibility does.

Recommended first-release policy: stop at the first conflict and retain the successful prefix only for diagnosis. Mark the remaining suffix `NOT_ATTEMPTED`. Do not adopt a partially replayed candidate or automatically skip the failed decision: later swaps may depend on it.

Conflict records identify the operation, registrations, reason, original audit locations, current candidate locations and proposed resolution choices. Staff may disable that intent for a new child intent set and rerun from raw output, replace it with an explicitly recorded decision, or cancel adoption and keep the previous draft. Resolution changes are attributed and revisioned. Missing registrations are never recreated, and a new participant is never substituted merely because it occupies an old seat.

Distinguish physical replay validity from business-rule review. A structurally valid replay can worsen priorities or introduce contribution-order/packing findings. Preserve raw solver metrics only as baseline metrics, label the derived map manually modified, and run the current application review/publication requirements against the exact derived revision. If policy prevents publication, report that conflict; do not promise unconditional preservation of all staff choices.

## Proposed branch work packages

1. Agree the identity-to-identity semantics, portable edit scope, shared-store requirement and conflict policy. Establish stable imported registration IDs and an input revision contract.
2. Add repository records and storage adapters for journal, intent sets and immutable derived drafts. Integrate capture, save, undo/redo and lineage without changing solver inputs.
3. Build a pure deterministic replay function taking raw assignments, current requirements/layout and a frozen intent set. Separate replay receipts from user edit capture.
4. Add application generation-context capture, durable status, retry/idempotency and conditional adoption. Exercise with the existing local solve adapter before connecting the future async transport.
5. Add progress, restored-swap counts, conflict resolution and version provenance to the staff workflow. Keep the old draft available throughout.
6. Validate acceptance scenarios, then enable the feature for new ledger-backed drafts. Keep the existing solver and publication regression suite passing unchanged.

Future code areas: dashboard/weight controls, a new replay library and manual-decision repository, workspace APIs/service, and the application job adapter. Excluded: optimization model, Lambda solver function internals, solver request schema, policy tuning and automatic publication.

## Acceptance scenarios

- A ↔ B followed by B ↔ C matches sequential replay on a newly generated map; swapping twice intentionally is distinguished from retrying one operation twice.
- Whole Emperor-pair swaps preserve four unique occupied seats; single/pair mismatches and inaccessible return destinations report conflicts without partial mutation.
- Added registrations retain the solver's placements unless explicitly referenced by a later staff decision. Renamed registrations resolve by stable ID. Removed/cancelled or resized registrations produce actionable conflicts.
- Preference reorder produces new baseline assignments, then applies the same frozen ID sequence; no old seat coordinates or solver objective values are treated as final truth.
- Save/reload/undo/redo/new history branch reconstruct the same active intent set. Old versions remain reproducible and independently selectable.
- G1, G2 and G3 each replay inherited decisions once from their raw result. Replay receipts never multiply the decision log.
- Duplicate response, callback retry, browser restart and adoption retry create one derived version for a replay key.
- J2 finishing before J1, concurrent staff saves and event/version switching never allow stale adoption.
- A failed operation halts the suffix; resolution reruns the complete revised intent set from raw output. The old draft and public map remain intact.
- Journal-write failure prevents a false “saved” state. Solver failure or replay persistence failure preserves recoverable job/source records.
- Published output contains every eligible registration's full entitlement and is reviewed under the existing applicable policy; generation/replay alone never changes publication.

## Decisions to confirm before implementation

Recommended defaults above make this plan actionable, but these product decisions remain explicit: swaps mean ID-to-ID exchange rather than fixed seats; the shared application store is authoritative for multi-staff use; first-conflict replay is all-or-nothing for adoption; only occupied equal-size swaps are portable initially; saving precedes generation and the initiating editor is frozen until completion. Additional intent types and seamless editing during in-flight generation should be separate follow-ups.
