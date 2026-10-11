# PJKIT seating allocation — production v4

A Python OR-Tools CP-SAT solver and Next.js review application for versioned seating allocation. Current venue: **16 × 16**, **24 blocked**, **232 assignable**. Emperor → Merit → Bodhi can share boundary rows. Tiers come from registration records; minimum contributions are RM5,000 / RM3,000 / RM2,000, with no assumed upper bounds.

Each row fills 东单 (right) completely before 西单 (left), skipping blocked seats. Physical positions 1–16 have priority ranks `16 15 14 13 12 11 10 9 | 1 2 3 4 5 6 7 8`. This is a hard solver rule for initial generation and regeneration.

Production preferences are contribution-to-seat matching, activeness and category suitability. Staff order and enable them; the backend maps enabled ranks to 40/30/20. These are relative coefficients, not percentages. Registration records and names are preserved. Staff may mark an entire registration absent, releasing its seats into a distinct holding-dock state; Emperor pairs remain one unit.

## Repository layout

| Path | Responsibility |
| --- | --- |
| `apps/web/` | Next.js staff interface, browser-local history and the Python subprocess bridge |
| `services/seating/` | Maintained `seat_solver` Python package, runtime resources and service tests |
| `research/experiments/` | Experiment runners and study tooling |
| `research/fixtures/` | Synthetic generators shared by tests and experiments |
| `research/baselines/legacy_cp_sat/` | Historical v1 prototype retained for reproduction and comparison |
| `contracts/` | Standalone canonical schemas |
| `docs/` | Application guides, methodologies, planning proposals and recorded results |
| `output/` | Local runtime state and disposable output |
| `FYP1/` | Earlier academic records, retained in place |

## Run locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e 'services/seating[dev]'
.venv/bin/python -m seat_solver.cli solve --request services/seating/data/production_request.json --output /tmp/pjkit-draft.json
.venv/bin/python -m seat_solver.cli validate --result /tmp/pjkit-draft.json --output /tmp/pjkit-audit.json
cd apps/web
npm install
npm run dev
```

Open `/event` and enter the seating workspace. With no saved plan, a private draft is generated. Use Edit plan for manual moves and the dock, then Save draft → Submit for review → resolve or override blocking findings → Publish seating plan. Participant lookup reads only the published version.

A production solve may return OPTIMAL or FEASIBLE after independent validation. The latter is valid but has an incomplete optimality proof. Canonicalization completion is reported separately. A manual edit is labelled MANUALLY_MODIFIED while retaining generation provenance.

Settings offers preference-based full regeneration and a separate **Repair gaps after absence** action. Outstanding edits are saved first. Absent registrations are excluded from seating demand. Repair starts locally, freezes outside placements and expands only on infeasibility, prioritizing fewest moved registrations, then distance, then preferences. Neither action publishes automatically. See [absence reallocation](docs/application/absence-reallocation.md).

## Configuration and integration

- Request/schema: `services/seating/data/production_request.json`, `services/seating/schemas/production_request.schema.json`; the standalone layout contract lives in `contracts/production_layout.schema.json`.
- Versioned policy: `services/seating/config/production_policy.json` (`config/solver_config.json` contains the same v4 reference contract).
- Current layout: `data/layouts/production_2026.json`; historical report fixture: `data/historical/report-232.json`.
- Runtime local store: `output/paid-seats-v4.sqlite3` (override `SEAT_PLAN_DB`). SQLite transactions protect approval/publication and stale-pointer checks.
- Override server event input using `SEAT_EVENT_REQUEST`; later saved drafts retain their event participant data. Host deployments should supply their event-data adapter.
- `SEAT_SOLVER_ROOT`, `SEAT_SOLVER_PYTHON` and `SEAT_SOLVER_RESOURCES` locate the repository root, the Python interpreter and the service runtime resources.
- Production requires `SEAT_HOST_SECRET` and a host-issued signed HttpOnly `seat_session` cookie. No unauthenticated production admin fallback is enabled. See [integration](docs/application/integration.md).

The default example is synthetic: **56 Emperor + 24 Merit + 16 Bodhi registrations**, 96 units consuming 152 seats. This is not the report's unconfirmed 150-person benchmark split.

## Verification and evaluation

```bash
.venv/bin/python -m pytest services/seating -q
.venv/bin/python -m pytest research/baselines/legacy_cp_sat -q
npm --prefix apps/web test
npm --prefix apps/web run test:current
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run build
.venv/bin/python -m research.experiments.evaluation --suite core --budget 3 --output output/evaluation/core-v4.json
.venv/bin/python -m research.experiments.evaluation --suite profiles --budget 3 --output output/evaluation/profiles-v4.json
.venv/bin/python -m research.experiments.evaluation --suite random --runs 100 --budget 3 --output output/evaluation/random-v4.json
```

See [evaluation methodology](docs/methodologies/evaluation.md), [mathematical model](docs/methodologies/mathematical_model.md), [machine-readable formulation](docs/methodologies/mathematical_model.json), [code overview](docs/application/code_overview.md), and [report amendments/traceability](docs/methodologies/requirements-traceability.md).

AWS/host deployment is a separate environment-dependent acceptance gate; local tests do not establish Lambda latency or cloud persistence.

## Staff workflow

`/event` opens the event-scoped seating flow. Edit mode enables whole-registration moves/swaps and temporary docking. Seat details offer Edit → Save draft / Cancel for display-name corrections and staff notes; Cancel discards only those local detail edits. `/venue` redirects staff to `/events/[eventId]/venue`, which shows the published hall and `/my-seat` provides participant-scoped lookup.

The [verification flow](docs/application/verification-flow.md) checks C12/C13 ordering and C15/C16 packing. OPEN red findings block publication unless explicitly overridden with a recorded staff decision; yellow findings are advisory. Structural validity and complete allocations for present paid registrations cannot be overridden. Publication rechecks saved placements, the active plan/revision and the expected public pointer transactionally.

Every present confirmed paid registration must have its full allocation before publication: two adjacent seats for Emperor, one for Merit/Bodhi. Marked-absent units remain docked and excluded from demand; attendance never changes registration records or names. Registration IDs, payment status and authoritative names cannot be changed in the seating workspace.

Working drafts retain monotonic revisions and immutable published snapshots. The default store is `output/paid-seats-v4.sqlite3` (override with `SEAT_PLAN_DB`). Browser-local history stores immutable manual-save snapshots separately in IndexedDB.

See [verification flow](docs/application/verification-flow.md) for review routes and publication policy, and [manual-edit history](docs/application/manual-edit-history.md) for recovery and undo/redo. See [the frontend demo flow](apps/web/README.md#staff-demo-flow) for current generation and version-opening behavior.

## Objective 2

Controlled absence-driven dynamic allocation minimizes registration movement from the latest saved working map through incremental repair. Attendance is saved in SQLite and shared when opening event plans. Safeguard verification supports this workflow. See [absence reallocation](docs/application/absence-reallocation.md) and [the active mathematical model](docs/methodologies/mathematical_model.md).

## Planning

See the [documentation index](docs/README.md) for current behavior and the [planning index](docs/planning/README.md) for proposals, including [preserving manual swaps after regeneration](docs/planning/manual-swap-replay-after-regeneration.md). The proposals describe future work and do not change solver behavior.
