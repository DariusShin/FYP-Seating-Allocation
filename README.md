# PJKIT seating allocation — production v2

A Python OR-Tools CP-SAT solver and Next.js review application for versioned seating allocation. Current venue: **16 × 16**, **24 blocked**, **232 assignable**. Emperor → Merit → Bodhi can share boundary rows. Tiers come from registration records; minimum contributions are RM5,000 / RM3,000 / RM2,000, with no assumed upper bounds.

Production ordinary preferences are **contribution-to-seat matching, activeness and category suitability**. Administrators order and enable them; the backend maps enabled ranks to 40/30/20. These are relative coefficients, not percentages. Published repair separately protects movement count, then movement distance, then local packing.

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

Open `/seat`. With no saved plan, select **Generate draft**. Generation never publishes. Review the saved draft, validate/save manual edits if needed, then **Submit for review → Approve revision → Publish approved revision**. `/my-seat?participant=P001` is a local administrator preview; production participant identity is read from the host's signed session, not this query parameter.

A production solve may return OPTIMAL or FEASIBLE after independent validation. The latter is valid but has an incomplete optimality proof. Canonicalization completion is reported separately. A manual edit is labelled MANUALLY_MODIFIED while retaining generation provenance.

Draft regeneration has no movement baseline. **Repair published plan** uses the server's explicit published pointer, never client assignments. Absences may leave vacancies. Registration changes can be entered in the workspace and submitted into a new draft; previously published seats stay visible until explicit publication.

## Configuration and integration

- Request/schema: `data/production_request.json`, `schemas/production_request.schema.json`.
- Versioned policy: `config/production_policy.json` (`config/solver_config.json` contains the same v2 reference contract).
- Current layout: `data/layouts/production_2026.json`; historical report fixture: `data/historical/report-232.json`.
- Runtime local store: `output/plans.sqlite3` (override `SEAT_PLAN_DB`). SQLite transactions protect approval/publication and stale-pointer checks.
- Override server event input using `SEAT_EVENT_REQUEST`; later saved drafts retain their event participant data. Host deployments should supply their event-data adapter.
- `SEAT_SOLVER_ROOT` and `SEAT_SOLVER_PYTHON` locate the Python service.
- Production requires `SEAT_HOST_SECRET` and a host-issued signed HttpOnly `seat_session` cookie. No unauthenticated production admin fallback is enabled. See [integration](docs/integration.md).

The default example is synthetic: **56 Emperor + 24 Merit + 16 Bodhi registrations**, 96 units consuming 152 seats. This is not the report's unconfirmed 150-person benchmark split.

## Verification and evaluation

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite core --budget 3 --output output/evaluation/core-v2.json
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite profiles --budget 3 --output output/evaluation/profiles-v2.json
PYTHONPATH=src .venv/bin/python -m seat_solver.production.evaluation --suite random --runs 100 --budget 3 --output output/evaluation/random-v2.json
```

See [evaluation methodology](docs/evaluation.md), [mathematical model](docs/mathematical_model.md), [machine-readable formulation](docs/mathematical_model.json), [code overview](docs/code_overview.md), and [report amendments/traceability](docs/archived/requirements-traceability.md).

## Legacy reproduction

The older modules and their tests are retained as historical v1 reproduction, not the production API. `legacy-solve` accepts the old file flags, using `config/historical/solver_config.v1.json` and `data/historical/report-232.json`. Legacy mock data, old result files and bundled frontend snapshots are never automatically imported or published. Their 122-unit/208-seat scenario and exclusive-row assumptions do not define v2 behaviour.

AWS/host deployment is a separate environment-dependent acceptance gate; no Lambda latency or production cloud persistence is claimed by local tests.

## Redesigned staff workflow

On `codex/staff-seating-flow`, `/event` opens the staff event page and `/seat` redirects to the event-scoped seating route. Events without a plan automatically generate a draft; existing events offer **Load latest draft** or **Generate new draft**. Choose **Edit plan** for name changes, moves/swaps, attendance markers, locks, notes and the side holding dock. **Save draft → Finish editing → Continue to publication → Publish seating plan** publishes the saved revision. `/venue` shows the latest published names and full hall for staff, with full-screen and print/save-PDF controls. `/my-seat` retains its participant-scoped response.

The submission safeguard implementation is preserved on `codex/seating-safeguards` and removed from this branch. There is no automated contribution-order/packing review or advisory acknowledgement step in the working-draft publication flow. Solver constraints and independent solver-output validation remain unchanged. Basic draft integrity, exact-revision checks, publication-pointer checks and atomic publication remain in place.

Emperor partner absence releases the partner's seat after staff record a reason. The contributor retains Emperor priority and occupies one seat. Restoring a pair sends it to the dock for two adjacent seats. Every attending registration must have seats before it can be included in a published snapshot.

Working drafts use a separate SQLite table with monotonic revisions. Published snapshots retain display-name metadata and partner-absence reasons; registration names remain protected. Existing databases with the retired review column continue to load and save without migration or data loss.

See [safeguard separation and flow audit](docs/seating-safeguard-separation.md) for the historical C13 reproduction and safeguard scope. See [the frontend demo flow](frontend/README.md#staff-demo-flow) for current generation and version-opening behavior.
