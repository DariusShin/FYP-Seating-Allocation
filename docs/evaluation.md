# Production v4 evaluation

Run `PYTHONPATH=src .venv/bin/python -m pytest -q` for the repository test suite, including production requirement tests. Production tests cover the full 16 effective ordered/enabled preference profiles, strict types, paid-entitlement validation, shared rows, exact ID multiset, accessibility/packing conflict, objective/representation tampering, canonical input order, independent tiny optimum enumeration, FEASIBLE handling, manual rescoring, paid-seat retention and transactional lifecycle/privacy.

Use `seat_solver.production.evaluation --suite core|profiles|random|saturation --budget SECONDS --output FILE`. Random uses `--runs 100` by default. Every record includes seed, input hash, layout version, registration count, physical demand, status, independent validity, component penalties, stage proof and timing where applicable. Stats include median, IQR, p95, extremes and status counts/rates over all runs, including intended failures. Recorded RSS is measured process peak, not mislabelled current RSS. Suite runs use canonicalize=false to measure optimization separately; canonical repeatability is tested with completion enabled.

The core suite has 20 deterministic scenarios: tiny assignments, realistic synthetic loads, saturation, pair/mixed-boundary/accessibility cases, additional seeded mixed-tier cases, empty event, over-capacity, structural infeasibility and malformed input. The default synthetic example is 96 units/152 seats, explicitly distinct from the report benchmark. Historical and current venue capacities must never be pooled without version labels.

The profile suite evaluates all 16 effective preference orders/enabled sets; six full permutations, six ordered pairs, three individual preferences, all-off. Disabled full-order permutations that produce the same active ordering are not distinct objectives. A geometric change is not required for every preference reorder.

The random suite generates 100 seeded approximately fixed-registration-load instances, varying Emperor proportion, contribution, category, activity and accessibility. Genuine accessibility/packing conflicts are expected in some cases and must be reported as infeasible, not hidden. Saturation varies physical demand and pair/unit composition rather than using registration count alone.

For difficult cases, use multiple budgets/workers and inspect proof stage, bounds/gaps and normalized component trade-offs. Do not compare weighted totals across different profiles as if the objective were unchanged.

Generated JSON reports in `output/evaluation/` document local runs. Timings are machine-specific observations, not guaranteed service latency. Additional host deployment acceptance must measure Lambda cold/warm invocation latency, serialization/storage/auth integration, and target-environment performance. This repository does not fabricate those measurements.

## Implemented verification and history coverage

`tests/test_verification.py` covers review entry, overrides and revocation, persistence, atomic publication, read-only feedback, stale/publication rechecks, hint integrity, privacy and local history attribution. `tests/test_workspace.py` covers complete present paid allocations, draft/save/open behavior, immutable snapshots, revision/public-pointer rejection and review-gated publication.

Local latency tests assert that a production-sized check and bounded history attribution complete within their test budgets. These are machine-specific regression assertions, not measured HTTP/Lambda service guarantees or a formal detection benchmark.

Frontend tests cover whole-registration moves, pair/compound swaps, docking, detail saves, generation retries, immutable local history, refresh recovery, incompatible branches, pending-save reconciliation and stale tabs. Route tests cover staff/event/active-plan access, encoded route segments, in-memory handoff during storage failure and saving recovered edits before review checks.

## Test validity audit — 2026-10-06

Reviewed the test targets, fixtures and assertions against the retained modules and current production paths. All 213 Python cases and 74 frontend cases pass. Their scope differs:

| Scope | Cases | Result and applicability |
| --- | ---: | --- |
| Production Python | 155 | Pass; current v4 solver, service, persistence, workspace and verification contracts |
| Historical prototype Python | 58 | Pass; retained `seat_solver.prototype` and v1 fixtures, not v4 acceptance |
| Current frontend | 64 | Pass; current workspace, dashboard, history, routes, grouping, verification and Python bridge |
| Legacy frontend editor | 10 | Pass; retained `src/lib/seat-editor.ts` and static result fixture; no current application module imports this editor |

Production Python coverage was checked by file:

| Test file | Cases | Current behavior covered |
| --- | ---: | --- |
| `test_production.py` | 40 | Production layout, 16 preference profiles, request validation, shared tier rows, audits, tiny optimum oracle, canonicalization, FEASIBLE handling, plan lifecycle and privacy |
| `test_east_island_priority.py` | 24 | Current physical priorities, east-first packing, blocked seats, pair packing and accessibility conflicts |
| `test_tier_precedence.py` | 34 | Emperor → Merit → Bodhi ordering across preferences and generation modes, independent ordering checks and validator failures |
| `test_paid_seat_retention.py` | 23 | Paid names and entitlements, rejection of retired attendance/replacement fields; independent attendance_status is supported, complete pairs, regeneration and publication isolation |
| `test_workspace.py` | 20 | Names, docking, saved revisions, version switching, immutable publication, review gates and synthetic fixture name restoration |
| `test_verification.py` | 11 | Findings, overrides/revocation, publication rechecks, resolution hints, untrusted history attribution and local latency budgets |
| `test_reset_local.py` | 3 | Dry-run reset, restorable backups, unknown-table rejection and missing-database behavior |

The separate versioned-plan submit/approve/publish tests remain valid: `service.dispatch` still exposes those actions through `PlanStore`. They cover that API lifecycle; workspace tests cover the staff UI's save/review/publish flow. Tests rejecting removed statuses, generation modes and workspace fields remain current regression guards.

The seven prototype files are marked `prototype`: `test_data_generation.py`, `test_floor_plan.py`, `test_hard_constraints.py`, `test_json_schema.py`, `test_regeneration.py`, `test_soft_constraints.py` and `test_solver_status.py`. Their historical registration counts, tier-exclusive rows, interleaved seat ranks, tier contribution ranges, movement objective and v1 result schema must not be used as current production requirements. They are retained because the historical solver and `legacy-solve` command still exist.

The old frontend editor tests now live in `frontend/tests/legacy/seat-editor.test.mjs`. Current editing is covered by `workspace.test.mjs`, `seat-dashboard.test.mjs`, `manual-history.test.mjs` and the review/route tests. The legacy tests remain module regressions and are included in the complete suite.

```bash
# Current application
PYTHONPATH=src .venv/bin/python -m pytest -q -m 'not prototype'
npm --prefix frontend run test:current

# Historical modules
PYTHONPATH=src .venv/bin/python -m pytest -q -m prototype
npm --prefix frontend run test:legacy

# Everything
PYTHONPATH=src .venv/bin/python -m pytest -q
npm --prefix frontend test
```

The prior baseline TypeScript and ESLint checks passed. Updated absence-feature checks are recorded below. These results validate the asserted local contracts; the frontend harnesses transpile modules and mock React/router/server dependencies, with a real Python invocation in the bridge test. They do not establish a full browser walkthrough, production build or deployed host/cloud acceptance. These counts describe the pre-absence baseline; the attendance contract and corresponding tests have since changed.

## Objective 2 evaluation and supporting verification

Objective 2 research evaluation should compare absence repair with full regeneration with/without movement penalties using identical saved baselines. Measure moved registrations and physical seats, centroid distance, preserved placements, preference cost, runtime, scope expansion and independent hard-rule satisfaction. Tiny exhaustive optimality and lifecycle tests are implemented; broader performance experiments remain work. Safeguard verification separately needs fault-injection detection/localization and deployment evaluation.

The local gate is implemented. A separately versioned content-hash-bound cloud verification facet, deployment latency and integration/concurrency acceptance remain proposed. Older version-specific measurements in `output/evaluation/` are historical artifacts and must not be presented as current-policy acceptance evidence.

## Absence feature verification — 2026-10-07

Before the feasible-repair acceptance correction, the production suite passed **166 tests** (`pytest -q -m 'not prototype'`), including 11 absence-repair cases. That frontend suite passed **72 tests** (`npm run test:current`). TypeScript and ESLint checks pass. Coverage includes the exhaustive tiny lexicographic movement oracle, progressive expansion/frozen placements, paired absence, shared attendance, absence-aware publication, legacy publication attendance guards, stale candidates, no-solution repair isolation, restore cancellation, distinct dock styling and save-before-repair. Historical prototype/editor suites were not rerun for this change.

A live browser walkthrough was attempted with an isolated temporary database, but a second Next.js development server could not start while the project already had a development server running. Browser interaction and deployment performance are not claimed by these results.

## Feasible repair acceptance correction — 2026-10-07

Interactive absence repair accepts independently validated FEASIBLE incumbents without requiring proof of minimum movement or distance. A later timeout or UNKNOWN status retains the earlier valid incumbent; only proven stages are fixed before further optimization. Regression tests cover FEASIBLE returns at each objective, later UNKNOWN, deadline exhaustion after a solution, no-solution rejection and rendering an unproven repair.

A read-only replay of the local 96-registration saved map with one absence returned a valid FEASIBLE repair moving 13 registrations, with doubled centroid distance 160. The distance stage used the remaining time budget; optimality was not claimed. No application draft or public pointer was changed by this replay. These are observations for that local snapshot, not a broader performance benchmark.

After this correction: **172 production Python tests**, **73 current frontend tests**, TypeScript and ESLint pass. The historical suites were not rerun.
