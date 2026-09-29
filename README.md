# PJKIT seating allocation — production v4

A Python OR-Tools CP-SAT solver and Next.js review application for versioned seating allocation. Current venue: **16 × 16**, **24 blocked**, **232 assignable**. Emperor → Merit → Bodhi can share boundary rows. Tiers come from registration records; minimum contributions are RM5,000 / RM3,000 / RM2,000, with no assumed upper bounds.

Production preferences are contribution-to-seat matching, activeness and category suitability. Staff order and enable them; the backend maps enabled ranks to 40/30/20. These are relative coefficients, not percentages. Paid registrations retain their name and complete seat entitlement regardless of attendance.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
PYTHONPATH=src .venv/bin/python -m seat_solver.cli solve --request data/production_request.json --output /tmp/pjkit-draft.json
PYTHONPATH=src .venv/bin/python -m seat_solver.cli validate --result /tmp/pjkit-draft.json --output /tmp/pjkit-audit.json
cd frontend
npm install
npm run dev
```

Open `/event` and enter the seating workspace. With no saved plan, a private draft is generated. Use Edit plan for manual moves and the dock, then Save draft → Finish editing → Continue to publication → Publish seating plan. Participant lookup reads only the published version.

A production solve may return OPTIMAL or FEASIBLE after independent validation. The latter is valid but has an incomplete optimality proof. Canonicalization completion is reported separately. A manual edit is labelled MANUALLY_MODIFIED while retaining generation provenance.

Settings offers only preference-based regeneration. Generate new draft is enabled when a priority or enabled flag differs from the current plan. Regeneration uses the complete model and never publishes automatically. There is no absence/replacement workflow or attendance-driven seat release.

## Configuration and integration

- Request/schema: `data/production_request.json`, `schemas/production_request.schema.json`.
- Versioned policy: `config/production_policy.json` (`config/solver_config.json` contains the same v4 reference contract).
- Current layout: `data/layouts/production_2026.json`; historical report fixture: `data/historical/report-232.json`.
- Runtime local store: `output/paid-seats-v4.sqlite3` (override `SEAT_PLAN_DB`). SQLite transactions protect approval/publication and stale-pointer checks.
- Override server event input using `SEAT_EVENT_REQUEST`; later saved drafts retain their event participant data. Host deployments should supply their event-data adapter.
- `SEAT_SOLVER_ROOT` and `SEAT_SOLVER_PYTHON` locate the Python service.
- Production requires `SEAT_HOST_SECRET` and a host-issued signed HttpOnly `seat_session` cookie. No unauthenticated production admin fallback is enabled. See [integration](docs/archived/integration.md).

The default example is synthetic: **56 Emperor + 24 Merit + 16 Bodhi registrations**, 96 units consuming 152 seats. This is not the report's unconfirmed 150-person benchmark split.

## Verification and evaluation

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite core --budget 3 --output output/evaluation/core-v4.json
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite profiles --budget 3 --output output/evaluation/profiles-v4.json
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite random --runs 100 --budget 3 --output output/evaluation/random-v4.json
```

See [evaluation methodology](docs/evaluation.md), [mathematical model](docs/mathematical_model.md), [machine-readable formulation](docs/mathematical_model.json), [code overview](docs/code_overview.md), and [report amendments/traceability](docs/archived/requirements-traceability.md).

## Legacy reproduction

The older modules and their tests are retained as historical v1 reproduction, not the production API. `legacy-solve` accepts the old file flags, using `config/historical/solver_config.v1.json` and `data/historical/report-232.json`. Legacy mock data, old result files and bundled frontend snapshots are never automatically imported or published. Their 122-unit/208-seat scenario and exclusive-row assumptions do not define v4 behaviour.

AWS/host deployment is a separate environment-dependent acceptance gate; no Lambda latency or production cloud persistence is claimed by local tests.

## Redesigned staff workflow

On `codex/paid-seat-retention`, `/event` opens the event-scoped seating flow. Edit mode enables whole-registration moves/swaps and temporary docking. Seat details offer Edit → Save draft / Cancel for display-name corrections and staff notes; Cancel discards only those local detail edits. Removed staff checkboxes and allocation locks are not stored. `/venue` shows the published hall and `/my-seat` provides participant-scoped lookup.

The submission safeguard implementation is preserved on `codex/seating-safeguards` and removed from this branch. There is no automated contribution-order/packing review or advisory acknowledgement step in the working-draft publication flow. Solver constraints and independent solver-output validation remain unchanged. Basic draft integrity, exact-revision checks, publication-pointer checks and atomic publication remain in place.

Every confirmed paid registration must have its full allocation before publication: two adjacent seats for Emperor, one for Merit/Bodhi. Attendance does not change names or demand. Registration IDs, payment status and authoritative names cannot be changed in the seating workspace.

Working drafts retain monotonic revisions and immutable published snapshots. The fresh default store is `output/paid-seats-v4.sqlite3`; the old `output/plans.sqlite3` and its backups remain untouched. Unset an old `SEAT_PLAN_DB` override when using the fresh demo. No old absence/replacement histories are migrated.

See [safeguard separation and flow audit](docs/seating-safeguard-separation.md) for the historical C13 reproduction and safeguard scope. See [the frontend demo flow](frontend/README.md#staff-demo-flow) for current generation and version-opening behavior.

## Revised Objective 2

The current FYP report proposes explainable server-side safeguard verification of the exact saved revision, with rule/seat findings and stale-verification rejection. Solver-output auditing and basic workspace integrity are implemented; the full manual business-rule verification gate remains planned. See [the active mathematical model](docs/mathematical_model.md).
