# Production solver mathematical background

The production solver assigns confirmed paid registration units to physical seats. Emperor needs an approved adjacent pair; Merit and Bodhi need one seat each. The current 16 × 16 layout has 24 blocked and 232 assignable seats. The default synthetic request has 56 Emperor, 24 Merit and 16 Bodhi registrations: 96 units requiring 152 seats.

## Decision variables and feasible assignments

For each registration `p`, compute legal options `O_p`: approved pairs or single seats that satisfy accessibility and blocked-seat rules. Boolean `z[p,o]` means option `o` is selected. Exactly one option must be chosen for each registration, and each physical seat may belong to at most one chosen option. Both cells of an Emperor pair count toward occupancy.

Tier order is Emperor → Merit → Bodhi. Seat order is row-major priority: `(row_number - 1) * seats_per_row + priority_rank`. Every higher-tier seat must precede every lower-tier seat, including both seats of each pair. Tiers may share rows when this order is preserved. Within a tier, a higher contribution may not be assigned to a later row than a lower contribution.

Rows fill front to back. Within a row, available east/right positions fill outward from the aisle before west/left positions fill outward. Blocked seats are skipped. These are hard solver requirements, including when every soft preference is disabled. If accessibility conflicts with required ordering/packing, the result may be INFEASIBLE.

## Soft costs

Each legal option has contribution, activeness and category-zone costs. Singles and pairs use comparable mean physical-seat rank, so a pair does not automatically receive twice a registration's preference influence. Components are normalized to integer 0..100 penalties.

Enabled preferences receive coefficients 40, 30 and 20 in their selected order. The weighted sum is minimized. These coefficients express relative weights, not percentages or a lexicographic guarantee. All-off gives zero ordinary preference cost while keeping every hard constraint.

See [the model](mathematical_model.md) for importance scaling, doubled mean disadvantage and integer rounding formulas.

## Solve, canonicalize and validate

CP-SAT may return OPTIMAL or FEASIBLE. OPTIMAL proves the business objective; FEASIBLE provides a valid solution without a completed optimum proof. After a proven objective is fixed, canonicalization minimizes option indices in stable registration-ID order under the shared deadline. Its completion flag is separate from optimization status.

The independent validator reconstructs rules, occupancy, costs and serialized results from original inputs and output, rather than trusting solver variables. It validates placement correctness, not the solver's optimality certificate.

Initial generation and preference regeneration use the same complete model over present registrations and produce private drafts. Objective 2 uses a separate incremental absence repair, with fixed outside placements and lexicographic movement objectives; see [absence reallocation](absence-reallocation.md). The objective contains contribution, activeness and category-zone costs; publication is a separate staff action.

## Manual edits and review

The staff workspace permits complete-registration moves and temporary docking while enforcing immutable registration records, valid pairs, accessibility and unique valid seats. Every paid allocation must be seated before review/publication.

Review recomputes C12/C13 ordering and C15/C16 packing findings. OPEN red ordering findings block publication unless explicitly overridden; yellow packing findings are advisories. This staff policy differs from the solver's compulsory generation constraints. Publication rechecks the persisted revision and records exceptions. See [verification flow](verification-flow.md).
