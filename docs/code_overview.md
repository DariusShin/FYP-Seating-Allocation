# Production code overview

| Module | Responsibility |
|---|---|
| policy.py | Strict JSON schema and semantic validation, eligible statuses, version lookup, host status mapper, ranked preference coefficients |
| production_scoring.py | Legal physical options, comparable mean-rank costs, repair change set, movement/local-gap and quality reconstruction |
| production.py | CP-SAT exactly-one/occupancy/ordering/packing model, sound initial row pruning, staged solve/scope logic, canonicalization, serialization |
| production_validator.py | Solver-independent assignment and result audit against original inputs, including metric and objective reconstruction |
| plan_store.py | SQLite immutable snapshots, transactional states, publication pointer, approval hash and participant-scoped rendering |
| service.py | JSON application adapter; server-resolved baseline and event-scoped lifecycle commands |
| cli.py | Production solve/audit and explicit legacy-solve entry point |
| production_data.py | Parameterized seeded synthetic requests; does not invent a report-baseline tier split |
| evaluation.py | Core/profile/random/saturation experiments and labelled status/runtime/quality results |
| frontend production-service.ts | Python bridge, signed host identity, same-origin mutation guard |
| /api/solve | Ranked preference requests produce drafts; raw weights/client seat maps rejected |
| /api/plans | Manual validation/save, review, approval, publication, rejection and history |
| /api/allocation | Only the published pointer and participant-scoped assignment/anonymous geometry |
| WeightControls / PlanActions / RegistrationEditor | Ranked preferences; review/publication; absence/replacement/registration changes |
| Existing seat editor/map | Local moves/swaps/pair presentation, with backend audit required to save |

Request → validation → eligible domains → CP-SAT → independent audit → immutable draft → manual revalidation → review/approval → atomic publication. Public lookup and repair both resolve the explicit published pointer.

The old cp_sat_model.py/preprocessing.py/cost_calculator.py/solver.py/validator.py remain v1 reproduction APIs. They are not imported by the production service. Their fixtures and the old numeric-weight schema are clearly separate from schemas/production_request.schema.json and the v2 model document.
