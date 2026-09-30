# Production code overview

| Module | Responsibility |
|---|---|
| policy.py | Strict JSON schema and semantic validation, eligible statuses, version lookup, host status mapper, ranked preference coefficients |
| production_scoring.py | Legal physical options, comparable mean-rank costs, packing and quality reconstruction |
| production.py | CP-SAT exactly-one/occupancy/ordering/packing model, sound initial row pruning, weighted solve, canonicalization, serialization |
| production_validator.py | Solver-independent assignment and result audit against original inputs, including metric and objective reconstruction |
| plan_store.py | SQLite immutable snapshots, transactional states, publication pointer, approval hash and participant-scoped rendering |
| service.py | JSON application adapter; event-scoped lifecycle commands, fresh v4 demo store |
| cli.py | Production solve/audit and explicit legacy-solve entry point |
| production_data.py | Parameterized seeded synthetic requests; does not invent a report-baseline tier split |
| evaluation.py | Core/profile/random/saturation experiments and labelled status/runtime/quality results |
| frontend production-service.ts | Python bridge, signed host identity, same-origin mutation guard |
| /api/solve | Ranked preference requests produce drafts; raw weights/client seat maps rejected |
| /api/plans | Manual validation/save, review, approval, publication, rejection and history |
| /api/allocation | Only the published pointer and participant-scoped assignment/anonymous geometry |
| WeightControls / AllocationDetails | Changed preferences enable regeneration; buffered details with Edit / Save / Cancel |
| Existing seat editor/map | Local moves/swaps/pair presentation, with backend audit required to save |

Request → validation → eligible domains → CP-SAT → independent audit → immutable draft → manual revalidation → review/approval → atomic publication. Public lookup resolves the explicit published pointer. Attendance has no seating operation.

The old cp_sat_model.py/preprocessing.py/cost_calculator.py/solver.py/validator.py remain v1 reproduction APIs. They are not imported by the production service. Their fixtures and the old numeric-weight schema are clearly separate from schemas/production_request.schema.json and the v4 model document.

Current staff flow is generate → save draft → review → publish. Whole-registration manual moves and the holding dock remain in edit mode. Paid-seat integrity, revision checks and atomic publication are enforced; a full explainable manual business-rule verification gate is planned for Objective 2.
