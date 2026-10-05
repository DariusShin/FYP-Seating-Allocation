# Current production requirement traceability

This mapping describes the `pjkit-v4` implementation. Academic source requirements remain in the signed report under `FYP1/`; they are not automatically current runtime requirements. Numbering below retains applicable rule IDs without introducing a placeholder objective for a retired requirement.

| Rule or capability | Implementation | Verification evidence |
| --- | --- | --- |
| C1/C2: complete allocations and unique occupancy | `production.py`, `production_validator.py`, `workspace.py` | Exact eligible-ID multiset, sizes, duplicate/overlap and missing allocation tests |
| C3/C4: valid geometry and blocked-seat exclusion | `policy.py`, `production_scoring.py` | Coordinates, unique IDs, strict types and blocked-seat tests |
| C5: confirmed paid eligibility | `policy.py`, `workspace.py` | Eligibility and immutable registration-input tests; attendance does not release seats |
| C6/C7/C8: contribution, activeness and category-zone costs | `production_scoring.py`, ranked-v1 mapper | Effective preference profiles, reconstructed costs and tiny optimum oracle |
| C10/C11: approved Emperor pairs | Legal options, formatter and workspace validation | Two-seat cardinality, adjacency and aisle-boundary tests |
| C12/C13: tier seat precedence and within-tier contribution row order | `production.py`, validator and `verification.py` | Shared boundary rows, same-row priority and ordering finding tests |
| C14: deterministic canonical selection | Sequential option-index minimization after proven weighted objective | Reordered/repeated inputs and canonical completion metadata |
| C15/C16: front-packed rows and east-first available-seat prefixes | Solver/validator packing and review gap detector | Gap, blocked-position, all-off and accessibility-conflict tests |
| C17: accessibility | Legal options and workspace integrity checks | Accessibility for singles/pairs and both registrations in a swap |
| Draft generation and explicit publication | `service.py`, `plan_store.py`, `workspace.py` | Private draft isolation, revision checks and transactional pointer switching |
| Staff editing and history | `SeatDashboard`, `manual-history.ts` | Atomic swaps, docking, detail edits, local snapshots, recovery and stale tabs |
| Explainable manual review | `VerificationEntry`, `VerificationScreen`, `verification.py` | Route entry, checks, attribution, overrides/revocation and publish-time revalidation |
| Identity and public privacy | `production-service.ts`, API guards, participant/venue projections | Signed-session scope, cross-event rejection and public-data filtering |

## Current policy boundaries

The active 16 × 16 layout has 24 blocked and 232 assignable seats. Emperor → Merit → Bodhi precedence includes within-row physical priority; tiers may share boundary rows. Minimum contributions are RM5,000/RM3,000/RM2,000, with explicit registration tiers and no inferred exclusive upper bounds.

Generation modes `INITIAL` and `REGENERATE_DRAFT` use the same complete hard-constrained model. Preferences contain exactly `contribution_seat`, `activeness` and `category_zone`. New output is a private draft; manual editing and publication are application operations.

Solver ordering/packing are hard requirements. Manual publication enforces complete structural validity and review policy: OPEN C12/C13 findings block unless explicitly overridden, while C15/C16 are advisory. Overrides are recorded, not proofs of solver feasibility. See [verification flow](verification-flow.md).

The example request is synthetic: 56 Emperor + 24 Merit + 16 Bodhi registrations consume 152 seats. The report's 94-unit/150-seat tier split is not established by this example. Deployment integration and formal research measurements remain separate acceptance work in [evaluation](evaluation.md) and [integration](integration.md).
