# Production concurrent-edit alerts for the seating workspace

Status: proposed enhancement, documentation only. Prepared 2026-10-11.
Scope: production Seating Flow integration only; explicitly **outside the FYP dissertation scope**. No solver, policy, schema or persistence changes are proposed.

## Purpose and boundary

In the production integration, the Version control and the Local-history control will not be shown to staff. Versioning remains internal machinery. This proposal defines the cheapest correct behavior when two staff members edit the same event's seating draft concurrently, and what the second writer sees when a save or publication collides.

The concurrency core already exists and must not change:

- One shared working draft per event (`workspaces` keyed by `event`), storing `base`, a monotonic `revision`, the body and the last actor (services/seating/src/seat_solver/production/workspace.py).
- Every mutating command — `workspace_save`, `submit`, `approve`, `publish`, regeneration and absence repair — must echo the revision it observed; a mismatch is rejected as a stale write (workspace.py action revision check; `STALE_BASELINE` in service.py).
- Publication rechecks the workspace revision and the expected public pointer inside one transaction, and monotonic revisions prevent an old browser from recreating a consumed draft.

Because staff will no longer see version controls, the only required change is **presentation**: distinct alerts for the two stale cases, a reload action, and lightweight provenance text.

## Worked scenario

| Time | Staff A | Staff B | Server state after |
| --- | --- | --- | --- |
| 15:01 | Saves generated draft | — | rev 1 (A) |
| 15:03 | Editing (unsaved) | Opens the same event, sees rev 1 | rev 1 |
| 15:05 | Saves manual edits (echoes rev 1 → accepted) | — | rev 2 (A) |
| 15:06 | Publishes (echoes rev 2 → accepted) | — | published pointer set; workspace advanced |
| 15:07 | — | Saves manual edits (echoes rev 1 → **rejected, stale**) | unchanged |

Outcome rules, all already enforced by the backend:

1. **Last successful save wins.** There is no branch tree (15:01→15:05 vs 15:01→15:07); B's divergent write fails and is never merged.
2. **Re-entering `/seating` shows the latest saved server state**: A's 15:05 draft before publication; the published version afterwards. Unsaved browser edits are never merged and never silently dropped server-side — they simply never reach the server.
3. **Browser-local Dexie history stays a private recovery log.** In production it must not be offered as a restore path for shared drafts, since the local snapshot can contradict the shared server state.
4. **Publication requires the current revision.** A publishing at 15:06 succeeds because the workspace is at rev 2; anything echoing an older revision fails, including a save that races the publish.

## Proposed handling (minimal)

1. **Classify the stale case on the client.** When a save returns a stale/revision-mismatch error, the client re-opens the workspace (it already knows how to open a plan):
   - If the plan is now published → show the *published while editing* alert and land on the read-only published view.
   - Otherwise → show the *changed by another staff member* alert and offer **Reload latest**, which rebases the editor onto the current revision.
   This requires no backend change; the existing error code plus one re-open call is sufficient.
2. **Alert copy (both cases)** must state plainly that the conflicting change was not saved, who/when where known, and that reloading discards unsaved local edits after confirmation. Never auto-overwrite, never silently discard.
3. **Provenance line**: display "Last saved by {actor} · {saved_at}" beside the working draft. The data is already in the workspace response; no version UI is exposed.
4. **Optional, cheapest pre-warning**: check the revision when the seating route gains focus or before entering edit mode, so a long editing session learns about a colleague's save sooner. The save-time check remains the only authoritative gate. This item is optional and may be dropped without affecting correctness.

## Explicitly out of scope

- Merge tools, per-staff concurrent drafts or per-actor workspaces.
- Presence indicators, live collaboration, WebSocket/polling infrastructure.
- Restoring or displaying previous versions in the production UI.
- Any change to the solver, request schemas, SQLite persistence or publication semantics.

## Acceptance scenarios

- B saving on a stale revision receives a clear alert, the server state is unchanged, and Reload latest rebases onto the colleague's revision.
- B editing when the plan becomes published receives the published-while-editing alert and lands on the published view; a stale save cannot recreate or alter the published state.
- Two staff editing sequentially (no conflict) see exactly the same behavior as today.
- Re-entering the event always reflects the latest saved server draft or the published snapshot, never a local-only restore.
- Hiding the Version and Local-history controls does not remove any recovery or conflict protection; stale writes still cannot overwrite newer server state.

## Decisions to confirm before implementation

- Final alert wording and language (English/Chinese) for both cases.
- Whether Reload latest keeps a copy of the discarded local edits in Dexie for manual recovery (recommended yes; it is already how local history behaves).
- Whether the optional focus-time revision check ships in the first production release or is deferred.
