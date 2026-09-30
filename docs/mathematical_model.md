# PJKIT v4 mathematical model

The machine-readable companion is [mathematical_model.json](mathematical_model.json). Its source of truth is the implemented `pjkit-v4` policy and `desirability-v2` scorer, rather than the retired PoC's HC numbering.

## Feasible assignments

Let P be eligible registration units and O_p their legal one-seat (Merit/Bodhi) or two-seat (Emperor) options. Define Boolean z[p,o]. Each registration selects exactly one option:

    sum(o in O_p) z[p,o] = 1

Each physical seat has at most one occupant, counting a chosen pair in both seat occupancies:

    occ[s] = sum(p,o containing s) z[p,o] <= 1

Blocked options and accessibility-incompatible options are removed. Pairs are approved disjoint physical-position pairs; no pair crosses the aisle. The 2026 layout blocks rows 6 and 8, positions 5–12, and rows 7 and 9, positions 5–6 and 11–12, leaving 232 assignable seats. The historical report layout remains a distinct 232-seat fixture.

Tier is explicit. Minimums are Emperor 5000, Merit 3000, Bodhi 2000 integer RM, with no inferred exclusive upper bounds. C12 orders ALL physical seats by `(row_number - 1) * seats_per_row + priority_rank`, with unique ranks per row and smaller values preferred. For each higher-tier p and lower-tier q, `worst_seat_order[p] < best_seat_order[q]`. Both Emperor seats count. Consecutive nonempty tier boundaries enforce all cross-tier comparisons, including Emperor → Bodhi when Merit is absent. Shared rows remain allowed, but same-row tier inversions do not.

C13 separately keeps higher contributions within the same tier from occupying later rows, using consecutive contribution-group row boundaries. Accessibility, pairs and packing remain compulsory: a conflict with strict tier priority is INFEASIBLE, never a hidden exemption. The stronger C12 implies the old row precedence, so the existing equal-size contribution-group row pruning remains sound; it only restricts candidate rows, not seat ranks.

Initial generation and preference-based regeneration fix global row occupancy to front-packed physical demand and require occupied available positions to form a prefix of the row order: 东单 (right) outward from the aisle, then 西单 (left) outward from the aisle. C16 requires every assignable east seat in a row to be occupied before any west seat in that row; blocked seats are skipped. The priority pattern at physical positions 1–16 is `16 15 14 13 12 11 10 9 | 1 2 3 4 5 6 7 8` (`pjkit-2026-v3`). This is compulsory even with all preferences disabled. Accessibility remains hard. An edge-only accessible registration in a tiny initial event may therefore make packing infeasible; the approved default is to report this conflict, not silently relax packing. Equal contribution groups' physical packing intervals permit sound initial-row pruning. Tiny oracle tests verify this formulation independently.

## Comparable seat and pair desirability

A pair uses the average physical seat rank, not the old incompatible pair-rank scale. Define doubled mean disadvantage:

    d(o) = 2 * mean(priority_rank(s) - 1, s in o)

For singles/pairs this is always integer. In a 16-wide row it ranges from 0 to 30. Scores are per registration, including category averages: two physical seats do not automatically double a registration's preference influence.

For each participant within their tier, contribution importance is 1..100, obtained by linearly scaling contribution above the tier's observed minimum. Equal contributions yield importance 1. Raw contribution cost is `importance * d(o)` with maximum 3000 in a 16-wide row. There is no tier bonus: hard C12 guarantees cross-tier priority regardless of which preferences are enabled or their weights. This scoring change is versioned as `desirability-v2`.

Activeness importance is 0..100 using the tier's observed activity range; equal activity yields zero differential preference. Raw cost is `activity_importance * d(o)`, maximum 3000. Category cost is twice the mean of the seats' configured category-zone costs, maximum twice the largest entry.

Each raw component is normalized to 0..100 per registration by integer half-up rounding:

    normalized = (200 * raw + maximum) // (2 * maximum)

The ordinary objective is the sum of normalized costs multiplied by the backend's ranked-v1 coefficients. Filter disabled preferences and compact ranks to 40,30,20 (the generic fourth value 10 is reserved). The known keys are contribution_seat, activeness, category_zone. Coefficients need not sum to 100 and do not imply lexicographic preference: lower-ranked preferences can collectively outweigh a higher-ranked preference. All-off means zero ordinary cost, with hard rules unchanged.

## Paid-seat retention and regeneration

P contains confirmed paid registration units. Attendance is not an input: a non-attending contributor retains the displayed name and the full paid allocation (two adjacent seats for Emperor, one for Merit/Bodhi). PENDING, WAITLISTED and CANCELLED describe upstream registration/payment eligibility only; the staff workspace cannot alter these records. There are no absence, replacement, single-seat Emperor, movement-cost or repair-scope states.

`INITIAL` and `REGENERATE_DRAFT` solve the same complete hard-constrained model. Settings enables regeneration only when the ordered preference list or an enabled flag differs from the current plan. The solver does not receive a previous allocation. New output is a private draft; the public pointer changes only on explicit publication. Previous versions remain history, not optimization inputs.

A working draft may temporarily dock a whole registration for manual moves/swaps. Server validation forbids registration additions/deletions/status changes, duplicate or blocked seats, invalid allocation sizes/pairs, and inaccessible placements. Publication requires every paid registration to be seated. Display-name corrections and notes are metadata; canceling detail edits has no storage effect.

The local v4 demo uses `output/paid-seats-v4.sqlite3`; old `output/plans.sqlite3` histories are preserved and not automatically migrated. Requests are tied to policy `pjkit-v4`.

## Objective 2: proposed server-side safeguard verification

The revised research objective is to develop and evaluate explainable, rule-based verification of generated and staff-edited plans against the exact saved revision before publication. For a candidate assignment A, the intended decision is `accept(A) = AND_h check_h(A, request, policy)`, with findings carrying rule ID, affected registrations/seats and corrective guidance. A verification result must bind to the input/policy version, saved revision and content hash; a subsequent edit invalidates it.

This is symbolic domain-rule reasoning, not a learned model or a new claim of optimality. Current code independently audits solver output and enforces draft integrity, paid-seat retention and stale-write/publication checks. A complete explainable business-rule gate for manually edited workspace publication remains planned; this requirement change does not silently restore the previously removed safeguard branch.

Proposed evaluation measures invalid-plan detection, false rejections of valid plans, rule/seat localization accuracy, latency, rejection of stale verified revisions and unchanged publication after a failed check. These are planned measurements, not collected results.

## Canonicalization and validity

After all business objectives are proven and fixed, minimize each participant's option index in stable participant-ID order, fixing each proven minimum before the next. Options are sorted by stable seat-ID tuples. This gives a unique assignment vector when every pass completes; arbitrary boundary variable values do not change physical assignments. `canonicalization_complete=false` explicitly denotes a timed-out/incomplete pass. Business OPTIMAL and canonical completion are distinct metadata.

The independent validator never reads solver variables. It checks the exact eligible-ID multiset, physical occupancy, legal options, ordering, front-fill and centre-out packing, reconstructed metrics, stage objective values and serialized floor-plan/assignment consistency. It validates a solution, not the solver's optimality certificate.

Manual changes are rescored against the saved input/profile/policy. Their current solver label becomes MANUALLY_MODIFIED; original generation status is retained. The versioned-plan approval API independently validates placements. The separate staff workspace publication flow retains its existing basic consistency checks and does not claim business-rule validation after manual edits; the removed safeguard workflow is not reintroduced by this solver fix.
