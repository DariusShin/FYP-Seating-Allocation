# Safeguard separation and seating flow audit

## Branches

- `codex/seating-safeguards`: preserves the full pre-separation implementation and its dependencies at `ff9e5a75430d1ee642889f05cbc91bf40a43a15a`. This includes the review UI, API command, finding generation, acknowledgements, publication checks and original tests. It is the starting point for safeguard redesign/debugging.
- `codex/seating-dashboard-redesign`: retains staff editing, saving and explicit publication, without the submission safeguard feature. No event data or published pointer was changed during this extraction.

The snapshot used a temporary Git index; the current branch and user's staging area were not switched or overwritten.

## Reproduced C13 issue

Read-only inspection of the saved `PJKIT-2026` workspace on September 22 produced:

| State | C13 | C15 | Verification alerts | Priority alerts |
| --- | ---: | ---: | ---: | ---: |
| Base plan placements | 0 | 4 | 94 | 22 |
| Saved edited placements | 51 | 4 | 94 | 29 |

This matches the screenshot's 55 required changes and 123 alerts. The 51 C13 findings involve 28 registrations; one registration appears in 26 conflicting pairs.

`production_validator.validate_placements` compares each pair within a contribution tier. A higher-contribution registration behind a lower-contribution registration violates C13. Manual moves can therefore generate many findings for one underlying move. The review layer renders every pair as the same generic “Contribution row ordering violated” message without names, amounts or rows. The repetition is not evidence that every generated plan fails C13: this base plan had no C13 findings.

The safeguard branch should add fixtures for these manual-move scenarios, group related findings, show both affected names/rows/contributions, and reconcile which ordering rules should block staff-authorized rearrangement. It should also reconcile repair-mode packing with final publication packing. Rule-policy changes are not part of this extraction.

## What was removed on the current branch

- `workspace_check`, finding generation and its frontend types/state/filter/navigation.
- Submit/check controls, rule findings and advisory acknowledgement UI.
- Saved-review revision tracking and publication requirements for checked revisions/acknowledgements.
- Workspace publication's business-rule revalidation and review audit records.
- The extra strict-packing flag used by the removed review workflow and its legacy publication guard.

The engine's existing C13 and other constraints, solver-output validation, and original versioned-plan API remain. Those are separate from the new working-draft review feature. The active dashboard publishes via `workspace_publish`.

Basic consistency checks remain: metadata shape, authoritative registration fields, known/unblocked seats, no overlapping assignments, exclusion of absent registrations, saved revisions, lock protection and stale public-pointer rejection. Docked work can be saved; attending registrations need seats to be serialized into a complete publication. Publication uses persisted state, never an unsaved browser payload, and commits the snapshot/pointer/revision atomically. Old databases may retain an unused nullable `checked_revision` column; no runtime review state depends on it.

## Flow audit against the requested sequence

| Step | Current behavior / remaining work |
| --- | --- |
| Empty hall and Generate draft | Implemented for events without a persisted plan. Existing events restore SQLite state; bundled result JSON is not loaded by `/seat`. Always starting empty needs an explicit event/new-draft lifecycle so existing work is not discarded. |
| Wait for allocation | Generate draft shows real pending/error states and explains the roughly one-minute wait. Current adapter invokes local Python. AWS Lambda/job orchestration remains a deployment task. |
| Populate generated result | First generation reloads the newly persisted plan. When an older working draft exists, regeneration does not adopt the new plan automatically; a revision adoption flow is still needed. |
| Edit assigned seats | Existing modal supports display names, absence, moves/swaps, drag/drop and locks. |
| Assign an empty seat using searchable participants | Empty-seat clicks currently depend on a selected participant. A dedicated searchable empty-seat picker matching the supplied reference is still needed. |
| Regenerate using locks and current edits | UI locks protect manual operations and saving. They are not wired into solver repair constraints; settings repair uses the published baseline. Repair of the current draft with pinned placements remains separate work. |
| Submit for safeguard review | Extracted to `codex/seating-safeguards` in this step. Current branch uses a staff review summary and explicit publication confirmation without automatic business-rule review. |
| Publish, venue and print | Preserved. Publication reads saved display names; venue continues to use the published snapshot and existing print layout. |

## Verification

Regression coverage includes direct publication without review, stale revisions, lock/overlap rejection, publication isolation, retired command rejection, legacy schema compatibility, and publication of a manual layout that the engine validator would flag for C13/packing. The latter verifies that the extracted review is not still running behind the new UI.

The saved event database was also copied to a temporary directory and its problematic workspace was published there. Publication succeeded and the venue response contained Chinese display names for all 148 assigned seats. No live event state was changed. Browser verification reached the publication confirmation from Finish editing with no findings or acknowledgement controls; the live Publish button was not pressed.

Checks passed: 120 Python tests, 27 frontend tests, TypeScript, ESLint, Ruff and production build. The build retains the existing dynamic filesystem tracing warning from the Python service adapter.
