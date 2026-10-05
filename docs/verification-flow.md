# Safeguard verification flow

Status: implemented in the local application. Review runs in `src/seat_solver/production/verification.py` and `workspace.py`, exposed through `/api/workspace`. It does not invoke CP-SAT. `VerificationEntry` owns route startup and navigation; `VerificationScreen` owns corrections and serialized review requests.

## Routes and entry

1. In the editor, Submit for review saves outstanding changes with the current plan ID and revision. Eligible paid registrations in the holding dock disable submission.
2. Navigate to `/events/[eventId]/seating-plans/[planId]/verification`. The server admits signed admin/staff users for their own event. `seatRouteWorkspace` loads the active workspace and returns 404 for missing, cross-event or inactive plans; it never calls `workspace_open`.
3. `VerificationEntry` opens matching browser history. A recovered state with docked paid registrations requires returning to editing.
4. `VerificationScreen` receives the server snapshot separately from recovered state. It saves recovered edits first, then checks the resulting saved revision. A fresh persisted check records `IN_PROGRESS` even when there are no findings.

Entry checks run again on route entry/resume. A stale save/check fails instead of silently adopting another staff member's state. A dashboard opened with an in-progress review offers resume; the plan editing route starts directly in edit mode.

## Rules and publication policy

| Check | Review behavior | Publication behavior |
| --- | --- | --- |
| Registration immutability, valid unique/unblocked seats, accessibility, complete approved pair/seat allocation | Invalid state is rejected by server validation | Cannot be overridden |
| Every eligible paid registration seated | Required for review entry | Required for publication |
| C12: all higher-tier physical seats precede lower-tier seats | RED finding, including same-row priority inversions | Each OPEN finding blocks; staff may explicitly override it |
| C13: higher contribution within a tier must not occupy a later row | RED finding | Each OPEN finding blocks; staff may explicitly override it |
| C15: available empty seat before an occupied later row | YELLOW advisory | Does not block |
| C16: occupied later seat with an earlier available packing seat empty, east/right outward then west/left outward | YELLOW advisory | Does not block |

Solver generation enforces ordering and packing as hard constraints. Staff publication uses the review policy above: an acknowledged exception is not a proof that every solver constraint is satisfied. Attendance does not bypass paid-seat requirements.

## Checks, saves and acknowledgements

All mutations carry `plan_version_id` and the current `revision`; identity and event are bound by the authenticated API adapter. SQLite serializes revision checks, state changes and publication.

| Command | Behavior |
| --- | --- |
| `workspace_check` without `state` | Validate and check persisted state; save findings, seen IDs, review status and checked revision |
| `workspace_check` with `state` | Read-only candidate feedback after review entry; does not save the candidate or replace the persisted review |
| `workspace_ack` | Set a current finding to `ACKED` or `OPEN`, with optional note; persists actor/time and recomputed review |
| `workspace_save` | Validate and persist working state; advance revision and invalidate checked revision; a save after `PASSED` starts `NOT_CHECKED` with fresh acknowledgements |
| `workspace_publish` | Recheck saved state, require prior review and zero OPEN red findings, verify expected published pointer, and atomically publish |

Current findings have `OPEN` or `ACKED` status. Resolved findings disappear from the current list and contribute to the resolved count through saved seen IDs. Finding IDs include the rule, sorted registration IDs and any gap seat IDs. A new pair or gap is not automatically acknowledged. Acknowledgements can survive fixes/rechecks within an in-progress review and can be revoked. Notes are optional; they are not mandatory approval reasons.

The frontend queues saves/checks/acknowledgements on one revision stream. Ordinary corrections debounce for 900 ms, then save before checking the persisted revision. Obsolete queued states/responses do not replace newer findings. Read-only checks are also used to validate restoration candidates. Initial entry and publication use loading states; ordinary checks update the issue panel.

## Findings, history and corrections

Finding payloads contain rule ID, severity, participants with names/contributions/rows/seats, involved seat IDs, a resolution hint and current acknowledgement status. Hints suggest forward moves or candidate swaps evaluated against ordering rules; they are guidance, not a guarantee that every unrelated finding disappears.

Optional `history_context` contains schema version, baseline and ordered active edits. The server validates continuity, registration inputs, placements and the final state, then attributes each current finding to its latest absent-to-present transition. Findings already present at the baseline remain unattributed. Missing/incompatible history or more than 500 active edits falls back to ordinary findings without suppressing any check. Attribution is response-only; it is not persisted as an audit trail.

The issue panel groups attributed findings by introducing edit, with underlying findings expandable and individually actionable. Changed-registration highlights follow current placements. Gap markers remain attached to empty locations; candidate highlighting is requested separately. Normal moves apply directly; mixed-size chain changes use a preview or offer return to the holding dock in editing.

Restoration traces connected placement edits to a complete earlier allocation, including occupants needed for an atomic exchange. It preserves current names, notes and unrelated placements. A candidate must remove every linked finding without introducing any new finding, including advisories, as confirmed by a read-only server check. The preview binds to state/revision and becomes invalid after an intervening change. Apply records one new undoable edit; unavailable original positions are explained rather than invented. See [history](manual-edit-history.md).

## Exit and publication

Back to editing saves the latest corrections, flushes/retains the matching history controller, and navigates to `/events/[eventId]/seating-plans/[planId]?seat=...` when a seat was selected.

Publish saves the latest state and requests `workspace_publish`. The server recomputes findings against persisted placements, rejects unreviewed state or OPEN red findings, and rejects a changed public pointer. Successful publication records `PASSED`, captures `safeguard_review` in the immutable snapshot, and updates the public pointer and workspace transactionally. The audit includes acknowledgement actor/time/notes; public projections omit review data. The UI then opens `/events/[eventId]/venue`.

Publication trusts neither a browser-supplied placement payload nor UI readiness alone. The implementation uses saved plan/revision checks and publish-time recomputation; it does not provide the proposed independently versioned, content-hash-bound cloud `VERIFICATION` facet.

## Coverage and limits

`tests/test_verification.py` and `tests/test_workspace.py` cover entry/publication gates, overrides/revocation, stale revisions, fresh checks, privacy, hints, history attribution and local latency assertions. Frontend tests cover route guards, compound moves, history handoff and recovered-state save-before-check ordering. Formal detection/localization experiments and target-environment performance remain work described in [evaluation](evaluation.md).
