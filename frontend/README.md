This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Staff demo flow

Home opens `/event`. **Enter seating allocation** opens the event-scoped route
`/event/PJKIT-2026/seat` (the route is `/event/[eventId]/seat`). The event must
match the signed host session; `/seat` redirects to that session's event route.

When a plan exists, a dialog offers **Load latest draft** and **Generate new
draft** before any solver request is sent. Loading opens the latest saved plan
with its saved workspace edits. Generating creates a new private plan and opens
that exact version. When no plan exists, generation starts automatically.
Refreshing an existing event's seating page presents the choice again rather
than automatically creating another draft.

The hall stays dimmed and unavailable to mouse, touch, and keyboard interaction
until the selected workspace has loaded. A failed request offers retry. If the
solver already saved its result, retry only opens that plan and never solves
again. The populated map appears without a page reload.

`workspace_open` explicitly selects the active version. Switching archives the
previous saved workspace in `workspace_versions`, preserves edits when reopening
a version, and advances the revision so stale browser saves are rejected.
Published seating changes only through the existing publish action.

**Submit for review** saves outstanding edits and navigates to
`/events/[eventId]/seating-plans/[planId]/verification`. The route reads the exact
active workspace, checks staff access and event ownership, and returns 404 for
an inactive or missing plan instead of switching the event's workspace. Server
revision checks continue to reject stale saves, checks and publication requests.
**Back to editing** saves verification edits and opens
`/events/[eventId]/seating-plans/[planId]`, preserving the selected seat and local
history. Recovered browser edits are saved before the entry check runs; docked
paid registrations must be assigned before entering verification.

Successful publication opens `/events/[eventId]/venue`. `/venue` redirects to
the signed session's event display. Venue polling is scoped to that event and
shows only its published snapshot; seat controls remain disabled.

The seat component boundaries and removed legacy components are documented in
[`src/components/seat/README.md`](src/components/seat/README.md).

To rehearse with an isolated database, start the development server from this
directory with `SEAT_PLAN_DB=/tmp/seating-demo.sqlite3 npm run dev`.
Production requires the existing administrator host session; local development
retains the existing administrator fallback. The prototype still uses its single
configured event dataset; the nested route establishes event ownership without
adding a multi-event management backend.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Paid-seat retention demo (policy v4)

The default database is `output/paid-seats-v4.sqlite3`. The old `output/plans.sqlite3` and backups are preserved; no migration or reset is applied to them. Unset a previous `SEAT_PLAN_DB` override or point it explicitly at the v4 file. Starting this branch for the first time gives an empty event history and the normal initial-generation flow.

Paid registrations retain their name and allocation even when contributors do not attend. Emperor always retains two seats. Absence, replacement, attendance markers, name/seat checkboxes and location locks are removed from the production UI and stored workspace state.

Use **Edit plan** for manual moves/swaps and the holding dock. All paid registrations must be seated before publication. Seat details use **Edit → Save draft / Cancel** for display name and note; canceling does not change the workspace. Settings offers regeneration only after changing preference order or an enabled flag, and opens the new private draft for review.

To reset only the v4 demo store, stop the server and solver processes first, then run from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m seat_solver.production.reset_local
PYTHONPATH=src .venv/bin/python -m seat_solver.production.reset_local --apply
```

The first command reports counts; `--apply` creates an integrity-checked backup and clears the selected local state transactionally. Layout and registration fixtures are preserved. Do not point this command at the old history unless you explicitly intend to reset it.
