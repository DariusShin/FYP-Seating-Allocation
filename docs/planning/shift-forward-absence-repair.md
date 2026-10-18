# Shift-forward absence repair (deterministic fast path)

Status: proposed, unimplemented. This plan documents the implementation details for a deterministic, solver-free repair of seating gaps left by absences, with the existing CP-SAT absence repair retained as an automatic fallback.

## Scope

- Applies only to the **Repair gaps after absence** operation (`generation_mode: REPAIR_ABSENCE`), i.e. gap repair after staff mark registration units absent.
- Replaces the CP-SAT search with an O(seats) deterministic forward-compaction pass **when the gap shape admits it**, and falls back to `absence_repair.repair()` otherwise.
- Preference re-ranking regeneration (`Generate new draft`) is explicitly out of scope; it remains a full solve and its retry behaviour is unchanged.

## Motivation

The current repair (`services/seating/src/seat_solver/production/absence_repair.py`) is already a scoped neighbourhood repair, not a full regeneration, but it still runs staged CP-SAT searches with the request time budget (60 s in `services/seating/data/production_request.json`). Failures surface as `REPAIR_TIMEOUT`, `REPAIR_NO_SOLUTION` and `REPAIR_INFEASIBLE`, which staff experience as the retry dialog in `apps/web/src/components/seat/map-loading-overlay.tsx`. For the dominant scenario — one or more registration units absent from the middle of a packed row — the correct answer is a forward shift that can be computed deterministically in milliseconds with feasibility by construction. The fast path removes the wait and makes that scenario always succeed.

## Correction to the originally proposed example

The sketch that motivated this plan pulled the front participant of the next row into the vacated row tail. That variant is rejected because it violates the absence movement priority (minimise moved registration units first, then distance, then preferences):

```
before:    pos 1..8  = 16 15 14 13 12 11 10  9 | aisle | 1  2  3 (4) 5  6  7  8
rejected:  pos 1..8  = [1 from row 4] 16 15 14 13 12 11 10 | 1 2 4 5 6 7 8 9
selected:  pos 1..8  = (empty) 16 15 14 13 12 11 10 | 1 2 3 5 6 7 8 9
```

- The rejected variant gives the promoted unit the row's worst seat (priority 16), a large preference downgrade, and forces a second repair cascade inside the donor row.
- The selected variant moves only the suffix behind the gap in packing order (ranks 5–16 here, 12 registration units) and parks the gap at the row tail. Filling a middle gap from another row always opens a second mid-row gap, so this is the minimum-moved-units repair for the common case.
- Cross-row movement is therefore not part of the fast path; it remains available to the CP-SAT fallback when compaction is illegal.

## Mechanism

### Packing-order model

Seats are ordered by the existing rank rule (`policy.py:147-155`): east side from the aisle (physical position 16 → rank 1 … 9 → rank 8), then west side (8 → rank 9 … 1 → rank 16). Rows are traversed front to back. The packing order is a list of **slots** where an Emperor registration occupies two consecutive approved-pair positions and a single registration occupies one position.

### Eligibility pre-checks (fast path conditions)

Run on the saved baseline before compaction. All must hold, otherwise fall back:

1. Every absent registration unit's previous seats are inside one row (no cross-row gap bundle).
2. The row's present occupants, read in packing order, form a contiguous suffix-aligned sequence: the gap consists of the absent unit's slots only; there is no pre-existing mid-row gap or temporary-dock hole in the affected span.
3. Shifting the suffix forward by one slot per unit keeps every Emperor registration on an approved-pair alignment (see pair handling below).
4. No registration unit lands on, or is shifted out of, an accessible position (`accessible_positions: [1, 2, 15, 16]`) contrary to its accessibility requirement.
5. All moved units stay inside their row: no tier-boundary interaction (C12/C13 are row-aligned, so within-row shifts are safe by construction).

### Compaction algorithm

1. Remove the absent units' slots from the row's packing-order sequence.
2. Walk the remaining present units from the first gap forward; each unit moves to the immediately preceding free slot in packing order. Emperor units move as a two-seat bundle onto the nearest legal approved-pair position; if a bundle cannot land legally, abort the fast path.
3. The trailing free slots (row tail) remain empty — the gap terminates at the least desirable seats of the row, matching front-fill packing demand targets.
4. Compute the change list (registration unit, from-seat bundle, to-seat bundle, doubled centroid distance) with the same `movement()` metric as the CP-SAT repair.

### Validation and fallback

- The compacted placement is audited with the existing independent `validate_placements` audit before acceptance. Any failure aborts the fast path and dispatches `absence_repair.repair()` with the same saved baseline, preferences and time budget — no user-visible difference except latency.
- A fast-path result records `repair_summary.engine = "shift-forward compaction"`, `optimality_scope: "repair_neighbourhood"`, `optimality_proven: true` for the movement stage (minimum-moved-units is proven by the gap argument above), and the preference-cost delta versus baseline so staff retain the option to run a full repair.
- Zero-move retention is unchanged: a map already satisfying all rules after the absence is kept as-is without any computation.

### Integration points

- `service.py` dispatch: attempt the fast path inside (or before) the `REPAIR_ABSENCE` branch; the request/response contract and workspace guard are unchanged, so `apps/web` needs no workflow change beyond displaying the engine label.
- `absence_repair.py` gains a shared helper for the packing-order slot model so both paths interpret rows identically.
- Attendance, persistence, versioning, review and publication behaviour in `docs/application/absence-reallocation.md` are untouched.

## Fit with the dynamic reallocation objective

- **Minimum movement first**: compaction is the provably minimum-moved-units repair for eligible gap shapes; preferences cannot outweigh movement in repair, so ignoring preference cost is consistent with the strict ordering.
- **Waiting time**: milliseconds of in-process computation instead of a staged CP-SAT search bounded by the 60 s request budget (host watchdog 330 s).
- **Success consistency**: feasibility by construction for eligible cases eliminates `REPAIR_TIMEOUT`/`REPAIR_NO_SOLUTION` retries for the dominant scenario; the fallback path preserves today's completeness for hard cases (Emperor straddles, accessibility, multi-row gaps, tier edges).

## Dependencies

- Existing hard-rule model and audit (`production.build`, `production_validator.validate_placements`).
- Existing repair dispatch and workspace guards (`service.py`, `production-service.ts`).
- No schema or persistence changes.

## Acceptance checks

1. Single mid-row absence in a fully packed row with no Emperor pair or accessibility involvement: fast path returns the suffix compaction with the minimum number of moved units; the CP-SAT repair on the same input returns the same moved-unit count.
2. Emperor pair inside the shifted suffix: pair moves as a bundle onto a legal approved-pair position, or the fast path aborts and the CP-SAT fallback produces a valid plan.
3. Accessible-need unit adjacent to the gap: compaction either keeps it on accessible positions or aborts to fallback; independent audit passes in both outcomes.
4. Multiple absences, pre-existing gaps, docked present units, and cross-row bundles: fast path declines and behaviour matches today's repair exactly.
5. Fast-path results pass `validate_placements`; repair summaries record engine, scope and preference delta; failed/stale candidates never switch the published pointer.
6. End-to-end latency of the fast path is below one second including validation, versus the current search-bound latency.

## Unresolved decisions

- Whether the fast path should also cover gaps in **partially filled rows** (packing demand targets already tolerate tail gaps; eligibility check 2 may be relaxed safely) or start strict and widen later.
- Whether the UI should offer an explicit "keep original seats" review affordance when the preference delta of the compaction is large, or rely on the existing review-then-publish flow.
- Whether preference-delta reporting on fast-path results is displayed in the repair toast/summary or only in the version record.
