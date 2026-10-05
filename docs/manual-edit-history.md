# Browser-local manual-edit history

Status: implemented. `frontend/src/lib/manual-history.ts` owns Dexie persistence and restoration; `components/seat/history-controller.ts` coordinates editing/verification route handoff. Browser history is scoped to the signed actor, event and base plan, and is separate from shared SQLite workspaces and immutable published plans.

## Records and accepted edits

The `seating-manual-history-v1` IndexedDB database contains:

| Table | Contents |
| --- | --- |
| `versions` | Immutable saved snapshots with scope, parent, server revision, saved time, state and input/layout fingerprint |
| `sessions` | Baseline, active edits, undo cursor, current state, sequence, generation, revision and optional pending-save receipt |
| `edits` | Ordered journal keyed by session/sequence, operation IDs, before/after changes and undo/redo references |

Accepted moves, swaps, docking, detail edits and compound rearrangements record full before/after registration items. A swap or Emperor-pair ↔ two-Merit exchange is one atomic edit. No-ops do not create records. Undo/redo append journal entries; a new edit abandons the active redo path while retaining its original records. There is no 50-state cap or automatic pruning.

The Local history panel exposes saved snapshots, retained incompatible branches, active edits, the session journal, comparison, restoration as a new draft edit and explicit scoped deletion. Restoring a saved version never mutates that saved snapshot.

## Recovery and save lifecycle

1. Load the server workspace and scoped history. Recovery requires compatible scope, server revision, layout and authoritative registration inputs. Incompatible branches remain available for inspection instead of replacing current state.
2. Persist each accepted edit with session state. Writes are serialized and use transaction-level generation checks, so another tab cannot silently overwrite the local session.
3. Before the network save, persist a pending receipt capturing submitted state, sequence and revision. Edits accepted during the save remain in the active session.
4. On server success, add a parent-linked immutable local snapshot and advance the session's parent/revision. Keep the original baseline and active edit chain so attribution survives saves.
5. On refresh, reconcile a successful server save whose local finalization failed using its pending receipt and matching server state/revision. Do not replay already saved edits.

Storage failures retain usable in-memory state and show an explicit recovery warning. Browser refresh recovery requires functioning IndexedDB. Histories do not synchronize across browsers/devices, and are not a shared staff audit trail.

## Route handoff

Before navigating between editing and verification, flush pending writes and retain the controller. Reuse requires matching actor/event scope, plan/base input, revision, saved state and the controller's current revision. This preserves undo and attribution during client navigation even when IndexedDB is unavailable. Mismatched router snapshots receive a new controller; refreshes recover through normal history loading.

`VerificationEntry` passes recovered working state separately from the server snapshot. The review screen saves recovered edits before checking their new server revision. Returning to editing saves current corrections, retains history and restores selected-seat context.

## Verification attribution and connected restoration

The server can analyze up to 500 active edits supplied as optional `history_context`. The local journal retains every record even when the analysis limit is exceeded. Missing or invalid history falls back to ordinary verification and cannot weaken publication safeguards.

Findings are associated with their latest introducing edit; baseline findings remain unattributed. Connected restoration follows swaps, docking/reassignment and later occupants back to the nearest complete placement. It restores all affected seat bundles together while preserving current names/notes and unrelated edits. A read-only server check must remove all linked findings without adding any new finding. Apply creates one undoable edit; intervening changes invalidate the preview. See [verification flow](verification-flow.md).

## Coverage and future work

Frontend history tests cover refresh recovery, atomic compound edits, redo branches, immutable snapshots, edits during save, failed-save reconciliation, storage failure, stale tabs, incompatible inputs and connected restoration. Route tests cover scoped controller handoff and recovered edits saved before checking.

[Replay after regeneration](planning/manual-swap-replay-after-regeneration.md) remains proposed. Current history records actual before/after edits; it does not persist a shared portable swap-intent stream or automatically replay edits into new solver output.
