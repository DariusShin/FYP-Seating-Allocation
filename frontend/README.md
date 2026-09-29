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
