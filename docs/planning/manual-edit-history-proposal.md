# Local manual-edit history proposal

Status: implemented on `codex/manual-edit-history` (2026-10-01).

## Implemented behavior

The dashboard and verification screen share a Dexie-backed history controller. Accepted edits contain full before/after registration items; compound Emperor-pair ↔ two-Merit rearrangements are previewed and recorded atomically. Undo/redo append journal entries, and new edits abandon only the active redo path. The Local history panel exposes saved snapshots, retained incompatible branches, active edits, the complete session journal, comparison, restoration as a new draft edit, and explicit scoped deletion. Nothing is automatically pruned.

Saved snapshots are immutable and parent-linked. The session keeps its original baseline and active edit chain across saves, updating its parent snapshot and server revision, so attribution survives editing/review transitions. A pending-save receipt captures the submitted state before the network call; reload can reconcile a successful server save whose local finalization failed. IndexedDB writes are serialized with transaction-level generation checks to reject competing tabs. Storage failures leave the current state usable in memory and display a recovery warning.

`workspace_check` accepts optional `history_context` (`schema_version`, `baseline`, ordered active `edits`). The server validates history continuity, registration inputs, placements and the final state. The shared rule detector evaluates docked historical states without relaxing review-entry seating requirements. Each current finding is attributed to its latest absent-to-present transition; pre-existing findings stay unattributed. `attribution.groups` contains operation IDs, changes, registration IDs, finding IDs and current focus seats. Attribution is response-only and is never saved in review acknowledgements or publication audit data.

Review defaults to changed-registration highlights and one card per introducing edit. Underlying findings remain expandable and individually acknowledgeable. Correction candidates are highlighted only on request. Position restoration preserves current names/notes, checks current placements and destination availability, and requires a read-only full check to remove all linked findings without introducing any finding, including advisories. An intervening change invalidates the preview; Apply records a new undoable edit.

Follow-up correction (2026-10-02): a standalone `Dock → seat` event has no original seated destination. Restoration now traces its active history to the nearest complete placement, includes connected swaps/current destination occupants and the former occupant named in a linked violation when filling vacated seats. This reconstructs both a direct exchange and an Emperor moved to empty seats followed by two Merit placements. The preview lists every affected registration and connected placement edit. All affected allocations are cleared only in a cloned in-memory candidate before their complete bundles are restored; only the fully validated result can be applied, as one undoable edit. Current names, notes and unrelated placements are retained. If the original location predates available history, the UI explains that limitation instead of inventing a destination.

Review borders, spotlights, candidate locations and selection now resolve registration IDs against the current working state, so they follow moves immediately while awaiting verification. Physical gap markers remain attached to empty locations and disappear when filled. Edit-mode selection also follows the selected registration through swap, undo/redo and docking.

History analysis is bounded to 500 active edits per request; longer branches retain every local record and display an explicit fallback to ordinary verification. Missing, invalid or incompatible history also falls back without suppressing any safeguard. Browser-local history is not a shared audit trail. Regeneration replay and solver changes are excluded.

Validation includes the row-2/row-7 compound exchange, repeated edits, undo branches, baseline findings, dock states, recovery, failed-save reconciliation, storage failures and stale tabs. Production-sized attribution with 96 registrations and 20 edits measured approximately 0.07–0.12 seconds locally. An isolated browser walkthrough verified compound preview, focused edit cards, reload recovery, restoration and undo.

The original design rationale follows.

For ordered registration-ID replay after regeneration, see the [manual swap preservation plan](manual-swap-replay-after-regeneration.md). That enhancement extends this history model with portable intent and recommends an application-owned shared store for multi-staff use.

## Current behavior

`SeatDashboard` loads the saved workspace and keeps up to 50 undo states in React memory. Moves, swaps and docking use this timeline; refreshing loses it. `workspace_save` updates the server working state and increments its revision. `workspace_versions` retains a working state per generated plan, not an immutable snapshot of every manual save. A server revision is therefore not yet a independently restorable draft version.

## Recommended storage

Use Dexie.js over browser IndexedDB, with an immutable saved snapshot plus an ordered edit log. Dexie provides asynchronous storage, indexes and transactions: https://dexie.org/docs/Dexie/Dexie and https://dexie.org/docs/Dexie/Dexie.transaction(). No extra React state library is necessary.

Scope all records by authenticated user, event and base plan version. Use three tables:

- `versions`: UUID, scope, parent version UUID, server revision, saved timestamp, full `WorkingState`, schema version and layout fingerprint.
- `sessions`: UUID, scope, parent version UUID, base server revision, current state, undo cursor, last sequence and updated timestamp.
- `edits`: session UUID + sequence, operation UUID, timestamp, operation type and an array of `{ participantId, before: WorkingItem, after: WorkingItem }` changes.

One swap is one atomic edit containing both registrations; a move, docking operation or multi-registration rearrangement follows the same structure. Record only successful changes, exclude no-ops, and retain all edits even when the in-memory undo window is capped. Include detail edits in the same history path. Log undo/redo as explicit operations referencing their original edit; clear only the active redo branch after a new edit, preserving the original log for inspection.

## Load → edit → save as new version

1. Load the server workspace and matching local saved snapshot on screen entry. Resume a local session only if its scope, base revision and layout fingerprint match. If they differ, retain the local branch and offer comparison instead of silently overwriting either state.
2. Start editing from that snapshot. Persist each accepted edit and the updated session state together in one IndexedDB transaction. Serialize writes so rapid swaps cannot be persisted out of order. Report write failures and retain unsaved state in memory.
3. On Save, capture the state and last sequence. Submit that state using the existing server revision check. Keep network calls outside the IndexedDB transaction.
4. After server success, atomically create a new immutable local version linked to its parent and close the saved portion of the session. Store the returned server revision. Future edits start a child session; earlier versions remain selectable.
5. If the request fails, keep the session unsaved. If the server saved but local finalization failed, reconcile against the returned revision/state on reload rather than reapplying moves. A server-supported idempotency key would make retry recovery more robust.

This gives a readable history of n edits involving m registrations, independent of final placement. Store structured before/after values rather than only descriptions so undo and comparison do not depend on names or seat labels.

## Scope and acceptance checks

Browser history stays on that browser profile; it is not a shared staff audit trail. For cross-device history, persist the same immutable snapshots and edit batches in new server SQLite tables, in the same transaction as the workspace save. Do not label a browser-only version as a shared server plan version.

Verify refresh recovery; whole-pair swaps; repeated swaps involving the same registrations; undo followed by a new branch; reopening each saved version; switching event/user/plan; two-tab stale writes; failed save retries; browser storage failure; and layout changes. Store participant IDs and changed items only, scope access to the signed-in user, and provide local-history deletion/retention controls.
