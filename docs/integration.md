# Application integration and migration

## Local reference service

`PYTHONPATH=src .venv/bin/python -m seat_solver.service` accepts one JSON command on stdin and returns JSON on stdout. Next.js uses this process adapter. Local persistence is `output/plans.sqlite3`, override with `SEAT_PLAN_DB` for tests. This is not DynamoDB/S3 and is not claimed as a deployed Lambda implementation.

Commands: `solve`, `load`, `get`, `history`, `manual`, `submit`, `approve`, `publish`, `reject`, `public`. Lifecycle mutations include `plan_version_id` and `validation_revision`. Manual changes send the full list of `{participant_id, seat_ids}`. The immutable plan body and its hash identify the exact reviewed input/placement/profile. The server assigns event/actor from authenticated identity. Browser fields named actor/event/role are not trusted.

`solve` accepts the generation mode and complete ranked preference list. `REPAIR_PUBLISHED` resolves the baseline through the store, optionally checking a caller's expected version. Direct Python research use can pass a baseline to `production.solve`; this is a trusted application boundary, not a public client contract. HTTP requests cannot send previous assignments or raw weights. By default regeneration uses the latest saved event registrations (never its seats as a baseline). A host data adapter should resolve authoritative updated registrations and statuses from the event platform. The UI's registration panel supplies changes for a new draft.

`public` returns only the selected participant's identity/seat assignment and anonymous physical occupancy for other seats. No contributions, categories, source input, penalties, replacement records or audit history appear. HTTP scopes participant identity from the signed session; only administrators can preview a different ID.

## Host identity contract

In production, set `SEAT_HOST_SECRET` to a server-side secret shared with the trusted host identity issuer. The host issues the HttpOnly `seat_session` cookie:

    base64url(JSON payload) + "." + base64url(HMAC-SHA256(secret, encoded_payload))

Payload fields:

```json
{"actor":"host-user-id","role":"admin","event_id":"PJKIT-2026","exp":1900000000}
```

Participant sessions instead use role `participant` and include `participant_id`. The issuer authenticates/authorizes the host user first and sets Secure, HttpOnly, appropriate SameSite and expiry attributes. Never put the shared secret in a browser bundle or allow clients to self-issue sessions. The adapter verifies signature, expiry, role and event. Administrative writes also reject cross-origin browser requests.

With no configured secret, only non-production development runs use the explicit synthetic local administrator identity. A production build/runtime without a session denies access; it does not silently enable an admin demo. Platform login/logout, secret rotation and the actual identity issuer belong to the host integration and must be tested there.

## Publication correctness

Generation/save/review do not update the public pointer. Publishing requires APPROVED and the exact validation hash, re-audits the stored plan, checks the expected old published pointer, then supersedes/publishes in one SQLite transaction. Failed/stale operations roll back. Manual edits produce a new immutable draft and must be reviewed anew. Published snapshots are not edited in place.

## Migration

1. Preserve legacy outputs as historical artifacts; do not select files by modification time or auto-import old `success` results as published.
2. Generate/load a schema 2.0 production request, using explicit statuses, selected tiers meeting minimums and a versioned physical layout.
3. Use `data/historical/report-232.json` only for historical comparisons. Current `data/floor_plan.json` and `data/layouts/production_2026.json` describe the 240-seat target.
4. Review a new v2 draft; an old unpublished numeric-weight configuration is not an approved ranked-v1 profile.
5. Update host statuses through `policy.map_host_status`; unknown labels fail. Supply replacement links rather than overwriting original registrations.
6. Install host identity/persistence adapters before cloud production use. SQLite is the local reference contract; do not store a durable production publication pointer in a Lambda temporary filesystem.

The report's 94-unit/150-seat benchmark still needs a confirmed Merit/Bodhi split. `production_data --emperor 56 --merit M --bodhi B` can generate it once M+B=38 is agreed; no invented split is presented as the historical baseline.

Manual editing atomically supersedes its editable predecessor and clears predecessor approval when saving the replacement draft. A concurrent publication/edit causes the stale operation to fail rather than overwriting history. The origin guard compares the browser Origin host with the incoming Host header, since Next.js can normalize its internal request URL; production reverse proxies must preserve the external Host.

## Participant hall view

`/my-seat` displays the full hall and a participant details panel in a 4:1 desktop layout, stacked on smaller screens. Assigned seats always use green; the map contains physical position numbers rather than names. The details panel shows the registered name and each assigned seat's occupant name, including the companion for paired registrations. Only the selected registration's seat names are included in the public payload; the hall map remains anonymous. Seat coordinates explicitly identify 西单/东单, row and left-to-right physical position.

Optional `event_details` in the versioned request provides `name`, `date`, `time`, `timezone` and `venue`. Publish a newly reviewed version to update these details. Missing dates/times display “待公布 / To be announced”; allocation timestamps are never substituted for event times. The default request and synthetic generator use fictitious Chinese-character names. Existing immutable plans retain their original names; generate and publish a new version to use updated fixture data.
