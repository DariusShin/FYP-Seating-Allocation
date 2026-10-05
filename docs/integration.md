# Application integration

## Local service and solver contract

`PYTHONPATH=src .venv/bin/python -m seat_solver.production.service` accepts one JSON command on stdin and returns JSON on stdout. Next.js invokes this local process through `production-service.ts`. SQLite persistence defaults to `output/paid-seats-v4.sqlite3`; override with `SEAT_PLAN_DB` for isolated environments. `SEAT_SOLVER_ROOT`, `SEAT_SOLVER_PYTHON` and `SEAT_EVENT_REQUEST` configure the process and source request.

Generation accepts `INITIAL` or `REGENERATE_DRAFT`, policy/layout versions, confirmed paid registration inputs and the full ordered/enabled list of `contribution_seat`, `activeness`, `category_zone`. Enabled ranks map to 40/30/20. Cost calculation and result penalty summaries cover these three components only. Each solve uses the complete constrained model and saves a private draft.

The service uses saved event registrations for later drafts and can refresh configured geometry-compatible layout obstacles/ranks. The browser generation endpoint accepts preference changes, not attendance or registration edits. A host integration must supply authoritative registration data; local draft generation does not implement an import pipeline.

## Workspace commands

| Command | Contract |
| --- | --- |
| `workspace_load` | Read the event's active workspace |
| `workspace_open` | Explicitly open a saved plan; preserve saved workspaces and advance revisions on a switch |
| `workspace_save` | Persist valid working state using current plan ID/revision |
| `workspace_check` | Check saved state; an optional candidate state is read-only feedback after review entry |
| `workspace_ack` | Override/acknowledge or reopen a current finding with optional note |
| `workspace_publish` | Recheck saved placements and review policy; atomically publish if revision and public pointer still match |

Identity/event are assigned by the authenticated API adapter, not browser role/actor fields. Staff routes read the active plan without opening a different workspace. Complete paid allocations and valid pairs/accessibility cannot be overridden. See [verification flow](verification-flow.md) for statuses, finding severities and publication audit fields.

The versioned-plan `manual`/`submit`/`approve`/`publish` API remains separate from staff workspace review. Its validation revision and approval hash must not be confused with the workspace's monotonic `revision`.

## Host identity contract

In production, set `SEAT_HOST_SECRET` to a server-side secret shared with the trusted host identity issuer. The host issues the HttpOnly `seat_session` cookie:

    base64url(JSON payload) + "." + base64url(HMAC-SHA256(secret, encoded_payload))

Payload fields:

```json
{"actor":"host-user-id","role":"admin","event_id":"PJKIT-2026","exp":1900000000}
```

Participant sessions instead use role `participant` and include `participant_id`. The issuer authenticates/authorizes the host user first and sets Secure, HttpOnly, appropriate SameSite and expiry attributes. Never put the shared secret in a browser bundle or allow clients to self-issue sessions. The adapter verifies signature, expiry, role and event. Administrative writes also reject cross-origin browser requests.

With no configured secret, only non-production development runs use the explicit synthetic local administrator identity. A production build/runtime without a session denies access; it does not silently enable an admin demo. Platform login/logout, secret rotation and the actual identity issuer belong to the host integration and must be tested there.

## Publication and public projections

Generation and draft saves do not switch the public pointer. Workspace publication checks the saved active revision, requires prior review and no OPEN red findings, rejects a changed expected public pointer, and commits the snapshot/pointer/workspace atomically. Published snapshots include review audit data; venue and participant projections omit that data.

`venue` returns the authenticated event's published floor plan and display names. `public` returns only the selected registration's identity/names/seats plus anonymous occupancy for other registrations. `/events/[eventId]/venue` is staff-only; `/my-seat` uses participant identity from the signed session. Drafts, contributions, source requests and review notes are not participant-visible.

## Deployment acceptance

Provision the solver/config/layout files and Python environment explicitly. Platform authentication, authoritative registration imports, managed persistence and AWS execution remain host integration work. SQLite in this repository is a local reference, not a durable Lambda temporary-filesystem contract. See the [DynamoDB proposal](planning/dynamodb-seating-schema.md) for the target cloud architecture and [evaluation](evaluation.md) for deployment measurements.
