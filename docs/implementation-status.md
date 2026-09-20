# Production v2 implementation status

Implemented against `production-implementation-plan-v2.md`, with the user's explicit confirmation of strict initial centre-out packing, repair packing after movement distance, common average physical desirability for singles/pairs, and accessibility exemption from the shared-tier preference.

| Plan area | Implemented repository path |
|---|---|
| Versioned policy, strict contracts | `config/production_policy.json`, `schemas/production_*`, `policy.py` |
| 2026 geometry, accessible domains | `data/layouts/production_2026.json`, `production_scoring.options` |
| Shared rows, ordered tiers/contributions, initial packing | `production.py`, independent `production_validator.py` |
| Ranked preferences and normalized scoring | `production_scoring.py`, `weight-controls.tsx` |
| Protected staged repair, bounded scope expansion | `production.py`, `service.py` |
| Proof, FEASIBLE acceptance, canonicalization | `production.py`, review proof panel |
| Immutable versions, manual rescoring, review and publication | `plan_store.py`, `/api/plans`, `plan-actions.tsx` |
| Registration changes and participant publication view | `registration-editor.tsx`, `/api/allocation`, `published-seat.tsx` |
| Reproducible tests and evaluation | `tests/test_production.py`, `evaluation.py`, `output/evaluation/` |
| Mathematical model and traceability | `mathematical_model.json`, `mathematical_model.md`, `requirements-traceability.md` |

An edit creates a new draft and atomically supersedes its editable predecessor, invalidating predecessor approval. Published snapshots remain immutable. Repair drafts reference the current published version without superseding it until explicit publication. The review UI exposes history, current validity, solver provenance, stage proof and repair movement separately.

The implemented host is a runnable local Next.js/Python adapter with transactional SQLite storage. Production host identity is supplied through a verified signed session cookie; missing authentication fails closed outside development. Actual host account integration, managed database/object storage, cloud deployment and Lambda cold/warm measurements are deployment acceptance work, not claimed as completed by local tests. See `integration.md`.

The report's 94-registration/150-seat benchmark remains unconfirmed as to its exact tier split. The 96-registration/152-seat example is labelled synthetic and must not be presented as that report benchmark. The signed interim report is not rewritten; `requirements-traceability.md` records amendments. Historical 232-seat fixtures and v1 solver remain available for reproduction, while the production layout has 240 available seats.

## Verification recorded for this implementation

The deterministic core suite returned 17 OPTIMAL cases and three deliberate failures (capacity, structural infeasibility and invalid input). All 16 preference profiles, 98/100 randomized instances and all 21 saturation instances returned OPTIMAL; the other two randomized instances were INFEASIBLE. Every successful evaluation output passed independent validation. Reports include machine and OR-Tools versions, input hashes, statuses, proof, timings and movement. These observations are local measurements, not a production latency guarantee.

The frontend passes TypeScript, ESLint, its 10 editor tests, and the Next.js production build. The build downloads the project's configured Google fonts and therefore requires network access. Next.js reports a non-fatal broad file-tracing warning for the local Python bridge; deployment must provision the repository solver/config/data files and Python environment explicitly as documented.

Final automated regression result: **101 Python tests passed**, plus **10 frontend editor tests passed**. A production-mode HTTP check against an isolated SQLite database passed authentication/authorization, rejection of incomplete preference requests, private draft generation, submit/approve/publish transitions, participant identity scoping, public payload privacy, repair isolation and version history. It also verified the administrative page renders successfully with a saved production plan. The test used synthetic registrations and did not publish into the project's live database.
