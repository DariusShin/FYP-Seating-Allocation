# PJKIT v2 mathematical model

The machine-readable companion is [mathematical_model.json](mathematical_model.json). Its source of truth is the implemented `pjkit-v2` policy and `desirability-v1` scorer, rather than the retired PoC's HC numbering.

## Feasible assignments

Let P be eligible registration units and O_p their legal one-seat (Merit/Bodhi) or two-seat (Emperor) options. Define Boolean z[p,o]. Each registration selects exactly one option:

    sum(o in O_p) z[p,o] = 1

Each physical seat has at most one occupant, counting a chosen pair in both seat occupancies:

    occ[s] = sum(p,o containing s) z[p,o] <= 1

Blocked options and accessibility-incompatible options are removed. Pairs are approved disjoint physical-position pairs; no pair crosses the aisle. The 2026 layout blocks rows 6 and 8, positions 5–12, and rows 7 and 9, positions 5–6 and 11–12, leaving 232 assignable seats. The historical report layout remains a distinct 232-seat fixture.

Tier is explicit. Minimums are Emperor 5000, Merit 3000, Bodhi 2000 integer RM, with no inferred exclusive upper bounds. Tier row precedence is Emperor <= Merit <= Bodhi (equality permits shared rows). Within each tier, higher contributions cannot occupy later rows. Consecutive contribution-group row boundary variables implement all these ordering inequalities transitively.

Initial, draft-regeneration and explicit full-regeneration modes fix global row occupancy to front-packed physical demand and require each side's occupied available positions to form a centre-out prefix. Accessibility remains hard. An edge-only accessible registration in a tiny initial event may therefore make packing infeasible; the approved default is to report this conflict, not silently relax packing. Equal contribution groups' physical packing intervals permit sound initial-row pruning. Tiny oracle tests verify this formulation independently.

## Comparable seat and pair desirability

A pair uses the average physical seat rank, not the old incompatible pair-rank scale. Define doubled mean disadvantage:

    d(o) = 2 * mean(priority_rank(s) - 1, s in o)

For singles/pairs this is always integer. In a 16-wide row it ranges from 0 to 30. Scores are per registration, including category averages: two physical seats do not automatically double a registration's preference influence.

For each participant within their tier, contribution importance is 1..100, obtained by linearly scaling contribution above the tier's observed minimum. Equal contributions yield importance 1. Add a tier bonus 200/100/0 for Emperor/Merit/Bodhi, except accessible registrations receive no tier bonus. Raw contribution cost is `(importance + bonus) * d(o)` with maximum 9000. This incorporates shared-row higher-tier preference once. It is soft, not a ban on rank inversions; the bonus also influences preference in pure-tier partial rows.

Activeness importance is 0..100 using the tier's observed activity range; equal activity yields zero differential preference. Raw cost is `activity_importance * d(o)`, maximum 3000. Category cost is twice the mean of the seats' configured category-zone costs, maximum twice the largest entry.

Each raw component is normalized to 0..100 per registration by integer half-up rounding:

    normalized = (200 * raw + maximum) // (2 * maximum)

The ordinary objective is the sum of normalized costs multiplied by the backend's ranked-v1 coefficients. Filter disabled preferences and compact ranks to 40,30,20 (the generic fourth value 10 is reserved). The known keys are contribution_seat, activeness, category_zone. Coefficients need not sum to 100 and do not imply lexicographic preference: lower-ranked preferences can collectively outweigh a higher-ranked preference. All-off means zero ordinary cost, with hard rules unchanged.

## Published repair

The server resolves the latest published plan and checks expected version identity. Changed participants include status, tier, contribution, accessibility, category/activity, replacement changes, and occupants affected by unavailable/inaccessible old seats. Removed/absent registrations consume no new demand. Confirmed replacements must satisfy their own unit size and eligibility.

Unchanged assignments outside the repair scope are frozen. Scope expands from directly affected seats, to affected rows, tier rows, neighbouring rows, then the available hall (allowing the numbered boundary to expand). Only a proven INFEASIBLE restricted model triggers expansion. UNKNOWN is inconclusive and never treated as proof of infeasibility.

All structural, eligibility, accessibility and row ordering rules remain hard. Global front-fill/centre-out packing is relaxed. Objectives are optimized successively:

1. Number of unaffected surviving allocation units whose seat sets change.
2. Total doubled-centroid Manhattan distance for surviving previously seated units.
3. Same-side available-seat packing inversions: outer occupied and inner empty.
4. Ordinary ranked preference penalty.
5. Technical canonical selection.

Distance is `|2 mean(old row)-2 mean(new row)| + |2 mean(old position)-2 mean(new position)|`. Newly added/replacement IDs have no previous seat and contribute no distance. Changed surviving units still contribute distance but not unaffected-movement count. Physical seats moved are reported separately from units.

A stage is fixed only after proof of optimality. All stages/scopes share one deadline. FEASIBLE stops further optimization and preserves its audited incumbent; an unreached stage has no claimed bound or proof. An optimal restricted-scope repair is not a proof of global minimum movement over every scope.

## Canonicalization and validity

After all business objectives are proven and fixed, minimize each participant's option index in stable participant-ID order, fixing each proven minimum before the next. Options are sorted by stable seat-ID tuples. This gives a unique assignment vector when every pass completes; arbitrary boundary variable values do not change physical assignments. `canonicalization_complete=false` explicitly denotes a timed-out/incomplete pass. Business OPTIMAL and canonical completion are distinct metadata.

The independent validator never reads solver variables. It checks the exact eligible-ID multiset, physical occupancy, legal options, ordering, mode-dependent packing, reconstructed metrics, stage objective values and serialized floor-plan/assignment consistency. It validates a solution, not the solver's optimality certificate.

Manual changes are rescored against the saved input/profile/policy. Their current solver label becomes MANUALLY_MODIFIED; original generation status is retained. Only freshly validated, explicitly approved immutable versions can advance the published pointer.
