# Local manual-edit history proposal

Status: recommendation only; persistence is not implemented by the interaction fix.

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
