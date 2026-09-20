# v2 requirement traceability and report amendments

Source: signed interim report, Table 3.4 C1–C17 and Appendices A/B/E; adopted `production-implementation-plan-v2.md`; stakeholder confirmations in the implementation conversation. The signed PDF is preserved under FYP1; it is not rewritten.

| Requirement | Implementation | Verification |
|---|---|---|
| C1/C2 | production.py exact-one option / physical at-most-one; production_validator exact ID multiset | duplicates, sizes, missing IDs, tampered maps |
| C3/C4 | policy.py coordinates and types; production_scoring legal options | geometry, blocked cells, malformed values |
| C5 | policy.ELIGIBLE and status/replacement validation | excluded/empty event, unknown statuses, replacements |
| C6/C7/C8 | production_scoring.candidate_cost; ranked-v1 mapper | 16 profiles, independent tiny objective oracle |
| C9 | production.py repair scopes and staged count/distance objectives | absence/replacement, stale baseline, no public change |
| C10/C11 | approved physical pairs and formatter | Emperor allocation and aisle checks |
| C12/C13 | ordered row boundary groups; shared rows | E/M/B shared row; no upper-tier inference |
| C14 | proven sequential canonical passes | repeated/reordered input, completion flag |
| C15/C16 | initial exact row targets and centre-out prefixes; repair inversions | initial gaps invalid, repair vacancy allowed |
| C17 | side singles 1,2,15,16; side pairs (1,2),(15,16) | accessible full row; strict tiny infeasibility |
| FR1–6, FR15 | production_request schema, CLI solve, service adapter | strict JSON/input tests |
| FR7/8 | actual status, stage bounds/gaps, reconstructed penalties, movement/timing | forced unfinished proof, strict benchmark |
| FR9/12/14/17 | transactional PlanStore, explicit transitions, published baseline | stale publish, failure preservation, review/approval |
| FR10/11 | existing editor + server validation + plan actions/print | frontend editor tests and manual/API verification |
| FR13, NFR5 | signed host identity and participant-scoped public response | unpublished state and privacy tests |
| FR16 | production_validator against source inputs before draft/approve/publish | objective and representation tampering |
| NFR1/6/8 | evaluation runner, seeded scenarios, canonicalization | core/profile/random suites; report-baseline split pending |

## Explicit amendments

- 2026 production capacity is 240, with 16 blocked seats. Historical report capacity 232 remains in `data/historical/report-232.json`.
- Shared-row centre preference is soft under v2. Accessibility stays hard; initial packing stays strict. Both policy defaults and the average physical-rank scorer were confirmed before implementation.
- Tier minimums are validated; the registration's explicit tier is authoritative even above another tier minimum.
- Packing is mode-dependent. Repair may preserve vacancies to avoid moving published registrations.
- Production accepts independently valid FEASIBLE. Strict research mode can require proven business optimality.
- FR3 is implemented by ranking/enabling three ordinary preferences. Movement is protected repair policy.
- Manual editing never preserves a current-plan optimality claim; publication requires a newly validated exact revision.
- The default synthetic example is **96 units / 152 occupied seats (56 E, 24 M, 16 B)**, not the report's 94-unit/150-person baseline. The report's 38-single Merit/Bodhi split is unconfirmed and is not invented as report evidence.

## External acceptance gates

The SQLite store and signed-cookie adapter provide a runnable local reference integration. Host identity issuance, host status mapping, DynamoDB/S3 persistence and AWS Lambda deployment/cold-warm measurements require the host deployment environment. They are not claimed as deployed or benchmarked here. Platform-specific status mapping rejects unknown values. Single-companion Emperor absence and registration-order business tie-break remain unconfirmed; no implicit policy is introduced.
