# Buddy UI reference and implementation

Reference inspected: `netizen-experience/buddy-prototype`, commit
`1fe3bbe6cc36ab079661b99bc66053d90e21cce7`, especially
[`app/seat/seat-allocation.tsx`](https://github.com/netizen-experience/buddy-prototype/blob/1fe3bbe6cc36ab079661b99bc66053d90e21cce7/app/seat/seat-allocation.tsx).

## Claude Code guidance found

The reference's `CLAUDE.md` describes Next.js 16 App Router, Tailwind v4 CSS
tokens, Lucide icons, and shadcn **Base UI** (`base-rhea`). Its two repository
skills live under `.agents/skills/`, not `.claude/skills/`:

- `frontend-design/SKILL.md`: deliberate visual direction, restrained decoration,
  clear product language, responsive layout, keyboard focus, reduced motion,
  and visual review.
- `shadcn/SKILL.md`: inspect installed components, consult component docs,
  compose existing primitives, use semantic tokens, and respect the different
  APIs of Base UI and Radix.

This application's shadcn configuration is **Radix** (`radix-nova`), so the
rebuild retains Radix and uses its `asChild` composition. It does not copy
Base UI's incompatible `render` APIs. No global Claude skill directory was
found under `~/.claude`; another local Buddy checkout also contains broader
React, Next.js and web design guidance.

## Adapted UI

- Compact workspace header, collapsible configuration sidebar, neutral seat
  tiles, tier dots, stage and entrance markers, and a horizontally scrollable
  map with readable seat widths.
- Pointer-based drag and drop (mouse and touch) moves registrations to empty seats or swaps occupied
  registrations. Both seats of an Emperor registration move together.
- The seat dialog offers a searchable participant dropdown, a preview, Apply,
  Cancel, and Remove assignment / Remove pair. Escape and closing the dialog
  discard a pending selection. Removal retains the registration for reassignment.
- Undo keeps the last 50 draft states; Discard changes restores the published
  plan and can itself be undone.
- Participant listing supports name/guest/ID search, tier filters and an
  unassigned filter. Guest lookup shares the searchable picker and provides
  Cancel selection and participant switching.

## Draft and solver boundary

Manual placements are held in the current browser tab. They do not overwrite
solver output, persist across reloads, or automatically change the guest view.
The editor rejects blocked seats, broken pairs, incompatible pair/single swaps,
and inaccessible destinations, including the returning participant in a swap.
It does **not** claim to validate contribution order, tier bands or hall packing.

Regeneration uses the current assigned registrations as a movement preference,
then publishes the solver's new result through the existing endpoint. Removed
registrations are still in the solver input and may be reassigned. When a draft
exists, the regeneration dialog explains this before proceeding. Statistics
remain explicitly tied to the last published solver run.

## Verification

From `frontend/`:

```sh
npm test
npm run typecheck
npm run lint
npm run build
```

The domain tests cover movement, swaps, pair integrity, accessibility on both
sides of a swap, blocked seats, removal/reassignment, replacement, preview
cancellation and aisle boundaries. Browser checks covered the rendered organizer
screen, participant-ID search, cancellation, pair removal, Undo, mouse-driven
pair swaps, guest selection and guest seat highlighting. Production
build passes; Next.js reports a file-tracing warning from the existing dynamic
allocation loader.
