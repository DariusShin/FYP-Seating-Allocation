# Production code overview

## Python application

Modules below are under `src/seat_solver/production/`, except `cli.py`.

| Module | Responsibility |
| --- | --- |
| `policy.py` | Request schema/semantic validation, eligible statuses, policy lookup and ranked preference coefficients |
| `production_scoring.py` | Legal physical options, mean-rank costs, packing order and quality reconstruction |
| `production.py` | CP-SAT allocation, occupancy, ordering and packing constraints; weighted solve, row pruning, canonicalization and serialization |
| `production_validator.py` | Independent audit of placements, metrics, objective and serialized result against original inputs |
| `plan_store.py` | Immutable plan snapshots, versioned-plan lifecycle, publication pointer, approval hash and participant projections |
| `workspace.py` | Active draft and per-plan saved workspaces, structural validation, monotonic revisions, review persistence and atomic publication |
| `verification.py` | C12/C13/C15/C16 findings, resolution hints, acknowledgements and optional history attribution |
| `service.py` | Event-scoped JSON command adapter and local event data loading |
| `production_data.py` | Parameterized seeded synthetic requests |
| `evaluation.py` | Core, preference-profile, random and saturation experiments |
| `../cli.py` | Production solve and independent validation commands |

Generation follows request validation → legal options → CP-SAT → independent audit → immutable private draft. The staff workspace follows edit → save → safeguard review → explicit atomic publication. Attendance does not release paid seats. The versioned-plan approval API is a separate lifecycle from workspace review.

## Frontend and API

| Module or endpoint | Responsibility |
| --- | --- |
| `src/lib/production-service.ts` | Python bridge, signed host identity and same-origin mutation guard |
| `src/lib/seat-route-workspace.ts` | Read the exact active event/plan workspace without opening or replacing it |
| `/api/solve` | Generate private drafts from ranked preferences |
| `/api/workspace` | Load/open/save/check/acknowledge/publish the event workspace; identity and event are bound server-side |
| `/api/plans` | Versioned-plan actions and generated-plan history |
| `/api/venue` | Authenticated event's published venue snapshot; mismatched event query is rejected |
| `/api/allocation` | Participant-scoped published assignment and anonymous geometry |
| `SeatDashboard` | Draft state, accepted edits, selection, saves and generation lifecycle |
| `WorkspaceHeader`, `WorkspaceToolbar`, `WorkspaceFooter`, `WorkspaceDialogs` | Workspace view sections and actions |
| `HoldingDock`, `ParticipantChecklist`, `MapLegend`, `AllocationDetails` | Temporary docking, registration navigation, map help and buffered details |
| `WeightControls` | Ordered/enabled preference editing; calls the dashboard's generation handler |
| `HallMap` | Shared staff, verification and venue geometry |
| `VerificationEntry`, `VerificationScreen` | Local-history recovery, full-seating entry gate, review requests, corrections and navigation |
| `src/lib/manual-history.ts` | Dexie journals, undo/redo, saved snapshots, reconciliation and restoration |
| `components/seat/history-controller.ts` | Matching in-memory history handoff across edit/review routes |
| `components/seat/helpers.ts`, `types.ts` | Map projections, labels, search, encoded paths and shared domain types |
| `VenueDisplay`, `PublicSeatMap` | Staff venue display and separate participant published-seat presentation |

Staff routes are `/events/[eventId]/seating-plans/[planId]`, its `/verification` child, and `/events/[eventId]/venue`. Plan links require the current active workspace; an inactive plan returns 404. `/venue` redirects authenticated staff to their event venue. See [verification flow](verification-flow.md), [history](manual-edit-history.md) and the [component guide](../frontend/src/components/seat/README.md).
