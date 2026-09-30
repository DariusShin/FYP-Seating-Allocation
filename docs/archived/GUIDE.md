> Archived historical guidance. For the current workflow and setup, see the [project README](../../README.md) and [frontend README](../../frontend/README.md).

# Production v2 developer and operator guide

The implemented policy is described in [the mathematical model](../mathematical_model.md), [traceability](requirements-traceability.md), and [integration contract](integration.md). The full implementation direction remains [plan v2](../planning/archived/production-implementation-plan-v2.md).

## Administrator workflow

1. Load confirmed event registrations (or the synthetic development input).
2. Order/enable contribution-seat, activity and category preferences. No percentages are entered.
3. Generate a draft. Review validity, actual solver status and version.
4. Move/swap registrations in the existing editor; Emperor units remain paired. Validate and save edits to get an authoritative score and a new draft version. Invalid changes are explained and cannot advance to publication.
5. Submit for review, approve the exact revision, and explicitly publish. Soft preference degradation alone is not a publication failure.
6. After publication, mark absence/replacement or other participant changes and choose Repair published plan. The latest published plan remains visible until the replacement draft is approved/published.
7. Full regeneration is explicit; it may rearrange all seats and still produces only a draft.

## Status interpretation

OPTIMAL proves the configured business objectives for the current model/scope. FEASIBLE is a valid audited incumbent whose optimality is unproven. Canonicalization completion is a separate field. A manually changed plan is not still OPTIMAL; its generation provenance is retained. UNKNOWN is not proof of infeasibility and does not trigger scope expansion.

## Inputs and repair

Only CONFIRMED/REPLACEMENT_CONFIRMED allocate seats. ABSENT/REPLACED records remain for audit. A replacement references the original REPLACED record and satisfies its own tier, size and accessibility. Unknown host statuses need an explicit mapping.

Strict initial centre-out packing may conflict with tiny edge-accessibility demand. Return infeasibility rather than violating a compulsory rule. Published repair permits vacancies and minimizes unaffected moved units, doubled-centroid movement distance, local gaps, then ordinary preference cost. Smallest feasible scope is preferred; its optimum is not claimed as global across all scopes.

## CLI and evaluation

Use `seat_solver.cli solve --request ... --output ...` for an unpersisted initial/draft solve. Use `seat_solver.production.service` JSON stdin for versioned workflow operations. Use `seat_solver.production.production_data` for parameterized synthetic requests. See README for executable commands and docs/evaluation.md for research measurements.

Historical v1 generation/validation/config modules exist only for reproduction. New production callers must not use the old raw-weight or client-supplied-baseline API.
