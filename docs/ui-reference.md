# Staff seating UI

The current interface uses Next.js App Router, Tailwind semantic tokens, Lucide icons and Radix-based shared UI primitives. `SeatDashboard` composes workspace sections; `HallMap` is shared with verification and the staff venue display. See the [component guide](../frontend/src/components/seat/README.md) for ownership boundaries.

## Generate and open a draft

`/event` opens the seating entry flow. Events without a plan show an empty hall and Generate draft. Generation invokes the local Python service and opens the exact returned `plan_version_id` as a private working draft.

Settings enables Generate new draft when preference ordering, enabled flags or attendance differ from the current plan. `WeightControls` supplies preferences to `SeatDashboard`; the dashboard owns solve/open requests, loading phases and retry state. A successful solve followed by failed workspace opening retries the opening without running a second solve. Generation blocks editing until the new workspace is ready.

`INITIAL` and `REGENERATE_DRAFT` use the complete solver model with absent registrations excluded. Settings also offers a separate absence repair using the saved map, local expansion and movement-first objectives; see [absence reallocation](absence-reallocation.md). Manual history is not replayed into a regenerated map. Regeneration never changes the published pointer. Saved-plan selection explicitly uses `workspace_open`; ordinary plan/review links only load the active workspace.

## Edit the working draft

Edit mode supports whole-registration moves, equal-size swaps and temporary docking. Emperor allocations retain both approved adjacent seats. Blocked, overlapping, inaccessible and incomplete pair destinations are rejected. Mixed-size rearrangements use a compound preview when possible; otherwise staff can use the holding dock. Every present eligible paid registration must be seated before verification. Mark absent docks the whole registration (both Emperor occupants), with a distinct absent card. Assignment requires confirmation to restore attendance; cancellation changes nothing.

The workspace provides search by name, guest/display name or registration ID, registration filters, participant navigation, map legend, local history and generated-plan versions. Details buffer display-name and note changes until Save draft succeeds; Cancel discards those buffered changes. Authoritative registration fields and payment status are not editable.

The header's Participants button opens a searchable, filtered dialog with 10 registrations per page. Changing the search or filter returns to the first page. Selecting a participant closes the list and highlights that registration's seats on the map; clicking an occupied map seat opens allocation details.

Accepted changes enter a persistent browser-local journal. Undo/redo and saved-version restoration are recoverable after refresh when the signed actor/event/plan, server revision and input fingerprint still match. A new edit abandons the active redo path while retaining journal records. Local versions and server plan versions are separate. See [manual-edit history](manual-edit-history.md).

## Review and publish

Submit for review saves outstanding edits and navigates to `/events/[eventId]/seating-plans/[planId]/verification`. The route checks staff access, event ownership and the active plan. It returns 404 for inactive or missing plans rather than replacing the active workspace.

Review restores matching local history and saves recovered changes before the entry check. The map and issue cards support corrections, undo/redo, finding attribution, optional restoration previews and per-finding overrides/acknowledgements. Back to editing saves corrections, retains history and returns to the plan route with the selected seat in the query string. See [verification flow](verification-flow.md) for the authoritative gates.

After confirmed publication, navigation opens `/events/[eventId]/venue`. `/venue` redirects to the signed session's event. Venue polling reads only that event's published snapshot and renders disabled seat controls. Draft saves and regeneration do not alter this display. `/my-seat` remains the participant-scoped published lookup.

Print / Save PDF uses A3 landscape with 10 mm page margins. Printed rows match the width of the 三寶佛 bar, with separate 20 mm side-label gutters and a 10 mm central aisle. Rows use 8 mm seat cells and 6 mm vertical gaps. Longer names shrink to fit the narrowed physical tracks. Controls, side headings and the entrance banner are hidden in print. Keep the browser's print paper size/orientation aligned with A3 landscape and disable browser headers/footers.

## Validation

From `frontend/`, run `npm test`, `npm run typecheck`, `npm run lint` and `npm run build`. Tests cover editing, pairs, details, generation retries, route access, exact-plan loading, history handoff and recovered edits saved before review. Test coverage is not a claim that every touch/browser configuration has been visually verified.
