# Seating component structure

`SeatDashboard` owns the current draft, selection, accepted edits, saves and
generation lifecycle. Its view sections are separate components:

| Component | Responsibility |
| --- | --- |
| `WorkspaceHeader` | Search, workspace navigation and version/history actions |
| `WorkspaceToolbar` | Draft status, dock access, undo, save and review submission |
| `WorkspaceFooter` | Occupancy totals and undo/redo controls |
| `HoldingDock` | Temporary unseated registrations and dock drop target |
| `WorkspaceDialogs` | Details, settings, local/server versions and help dialogs |
| `ParticipantChecklist` | Searchable, filtered registration list with 10 per page and map highlighting |
| `MapLegend` | Tier colors and participant indicators |
| `HallMap` | Shared seating geometry for editing, verification and venue display |
| `VerificationEntry` | Route startup, history recovery, full-seating gate and navigation |
| `VerificationScreen` | Server checks, finding acknowledgements, corrections and publication |

`types.ts` provides shared component types and re-exports canonical domain types.
`helpers.ts` provides shared map projections, position labels, search and route
builders, and re-exports the existing pure editing and finding helpers. Keep
rule semantics in `lib/workspace.ts` and `lib/verification.ts` rather than
duplicating them in components.

`history-controller.ts` hands one controller between editing and verification
after pending local writes finish. Its in-memory handoff requires matching actor,
event, plan, revision, base inputs and saved state. It preserves undo and
attribution when IndexedDB is unavailable. Refreshes use normal Dexie recovery;
different browsers do not share history. `VerificationScreen` receives the server
snapshot separately from recovered local state so it can save recovered edits
before checking the new revision.

The old `AssignmentsTable`, `ParticipantDialog`, `ParticipantPicker`,
`PlanActions`, `SeatAssignmentDialog`, `SeatLegend`, `SeatMap`, `StatsSidebar`
and `useSeatDrag` had no callers in the current editing, verification, venue or
participant flow. They and their unused theme helpers were removed. The current
`AllocationDetails`, generation/loading components, `WeightControls` and
`LocalHistoryPanel` remain in use. `PublicSeatMap` continues to serve the
participant-facing published view separately.

Routes read the active workspace without calling `workspace_open`. An old review
link therefore cannot replace another staff member's active plan. Use the event
entry flow to explicitly open a different saved plan. Publishing still runs the
existing server validation and acknowledgement gates before navigating to the
event venue.

## Absence and incremental repair

The dashboard distinguishes temporary dock entries from absent registrations. `workspace.ts` owns atomic mark-absent and restore-and-place operations; the restore dialog changes nothing on Cancel. Emperor attendance applies to the entire pair. `WeightControls` exposes separate full generation and absence repair actions. The dashboard saves outstanding changes before requesting repair with the current plan ID/revision. `absence_repair.py` performs the reduced movement-first repair; `VerificationEntry` admits absent dock entries while blocking present dock entries. See [Objective 2](../../../../docs/absence-reallocation.md).
