# Mathematical Model of the Seat Allocation Solver Engine

**Implementation reference:** `src/seat_solver/` (CP-SAT prototype, schema version `1.0.0`)
**Case study:** PJ Kwan Inn Teng (PJKIT) — 16 × 16 hall, 256 seats, centre aisle after position 8.
**Engine:** Google OR-Tools CP-SAT (pure integer constraint programming).

> Note: this document formalises the **solver engine prototype** in `src/seat_solver/`. The companion
> [mathematical_model.md](mathematical_model.md) describes the separate `pjkit-v2` production policy.

This document gives an academic formalisation of every set, parameter, variable, hard constraint, soft constraint, and objective term implemented in the engine, cross-referenced to the implementing module and function.

---

## 1. Sets and Indices

| Symbol | Definition                                                                                                                                          | Source                                 |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| $P$    | Set of primary participants (allocation demand units), $\lvert P \rvert = 150$ in the default scenario                                              | `models.Participant`                   |
| $S$    | Set of physical seats, $\lvert S \rvert = R \times C = 16 \times 16 = 256$                                                                          | `models.Seat`, `FloorPlan`             |
| $K$    | Set of valid adjacent Emperor seat pairs $k = (s_a, s_b)$: same row, $pos(s_b) - pos(s_a) = 1$ with $pos(s_a)$ odd, never spanning the centre aisle | `preprocessing.build_valid_pairs`      |
| $U$    | Set of allocation units, $U = U^{\text{single}} \cup U^{\text{pair}}$; Emperor participants form two-seat units, Merit/Bodhi form one-seat units    | `preprocessing.build_allocation_units` |
| $T$    | Tier set in precedence order $T = (\text{EMPEROR}, \text{BODHI}, \text{MERIT})$                                                                     | `models.TIER_NAMES`                    |
| $Z$    | Zone set $\{\text{LEFT\_OUTER}, \text{LEFT\_CENTER}, \text{RIGHT\_CENTER}, \text{RIGHT\_OUTER}\}$                                                   | `models.ZONE_NAMES`                    |
| $O_u$  | Eligible option set of unit $u$: eligible seats (singles) or eligible valid pairs (Emperors)                                                        | `preprocessing`                        |
| $B_t$  | Demand-derived row band of tier $t$ (§3)                                                                                                            | `preprocessing.compute_tier_bands`     |

### Seat attributes

Each seat $s \in S$ carries:

- $row(s) \in \{1,\dots,16\}$ — one-based row number (internal index $row\_idx = row - 1$)
- $pos(s) \in \{1,\dots,16\}$ — the **physical position**, used exclusively for adjacency
- $\rho(s) \in \{1,\dots,16\}$ — the **priority rank** (1 = best), used exclusively for desirability
- $side(s) \in \{\text{LEFT}, \text{RIGHT}\}$, $zone(s) \in Z$, $acc(s) \in \{0,1\}$ (accessible), $blk(s) \in \{0,1\}$ (blocked)

$\rho$ and $pos$ are never interchangeable (project gotcha: adjacency must use `physical_position`).

### Priority-rank pattern

Mirrored around the aisle (`floor_plan_generator.priority_rank_for_position`), with $a = 8$:

$$
\rho(s) =
\begin{cases}
2\,\big(pos(s) - a - 1\big) + 1, & pos(s) > a \quad \text{(right of aisle: odd ranks } 1,3,5,\dots)\\[4pt]
2\,\big(a - pos(s)\big) + 2, & pos(s) \le a \quad \text{(left of aisle: even ranks } 2,4,6,\dots)
\end{cases}
$$

so the right-of-aisle seat always outranks its mirrored left seat.

### Structural blocked block

Observed identically in the real 2023/2024 PJKIT layouts (`floor_plan_generator.DEFAULT_BLOCKED_PATTERN`):

$$
blk(s) = 1 \iff
\begin{cases}
row(s) \in \{6, 8\} \ \wedge\ 5 \le pos(s) \le 12 \\[2pt]
row(s) \in \{7, 9\} \ \wedge\ pos(s) \in \{5, 6, 11, 12\}
\end{cases}
$$

Assignable capacity: $\lvert S \rvert - \sum_s blk(s) = 256 - 24 = 232$ seats.

---

## 2. Parameters

All quantities are integers — no floating-point value ever enters the CP-SAT model (HC12).

| Symbol                                                            | Meaning                                                                                             | Config key (`config/solver_config.json`)                                               |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| $w_1, w_2, w_3, w_4$                                              | Weights of SC1–SC4                                                                                  | `priority_seat_weight`, `category_zone_weight`, `movement_weight`, `activeness_weight` |
| $r^{\text{acc}}, r^{\text{monk}}, r^{\text{eld}}, r^{\text{def}}$ | Desired priority ranks for accessibility, monk, elderly, default                                    | `desired_priority_rules`                                                               |
| $z_{cat,\,zone}$                                                  | Category–zone cost matrix                                                                           | `category_zone_costs`                                                                  |
| $\pi^{\text{fix}}, \pi^{\text{row}}, \pi^{\text{col}}$            | Movement: fixed penalty, row-distance, column-distance weights                                      | `movement`                                                                             |
| $\Pi_k$                                                           | Priority of Emperor pair $k$ (centre-out, east side first: positions 9–10 → 1, 7–8 → 2, …, 1–2 → 8) | `emperor_pair_priorities`                                                              |
| $M$                                                               | Main objective scale (tie-break dominance bound)                                                    | `tie_break.main_objective_scale`                                                       |
| $t_{\max}, W, \text{seed}$                                        | Solver time limit, worker count, random seed                                                        | `solver`                                                                               |

### Seat demand

Each participant $p$ has integer contribution $c_p$ (RM), tier $t(p) \in T$, and seat footprint $\sigma_p = 2$ if $t(p) = \text{EMPEROR}$, else $\sigma_p = 1$. Total seat demand:

$$
D \;=\; \sum_{p \in P} \sigma_p \;=\; 2\,\lvert P^{\text{EMP}} \rvert + \lvert P^{\text{BOD}} \rvert + \lvert P^{\text{MER}} \rvert
$$

Default scenario: $D = 2(56) + 16 + 22 = 150$ occupied seats of 232 assignable; 82 assignable seats remain empty. Three counts are distinguished and never conflated: participants ($150$), allocation units ($56 + 16 + 22 = 94$), and occupied seats ($150$).

---

## 3. Preprocessing: Demand-Derived Tier Bands (HC4)

Tiers are **not** fixed venue zones. Their row bands are derived by front-to-back packing _before_ model construction (`preprocessing.compute_tier_bands`), so band ordering and tier-exclusive rows are enforced structurally.

### Per-row capacities

With $K_r$ the valid pairs of row $r$ and $S_r$ the non-blocked seats of row $r$:

$$
\kappa^{\text{pair}}_r = \lvert K_r \rvert, \qquad
\kappa^{\text{seat}}_r = \big\lvert \{ s \in S_r : blk(s) = 0 \} \big\rvert
$$

### Band derivation

Rows are consumed in order $r = 1, 2, \dots$ by tiers in precedence order. For tier $t$ with unit demand $n_t$ ($n_{\text{EMP}}$ = number of Emperor units; $n_t = \lvert P^t \rvert$ otherwise), with remaining demand $n^{\text{rem}}_t$:

$$
\text{take}_{t,r} = \min\!\big(n^{\text{rem}}_t,\ \kappa_t(r)\big),
\qquad
n^{\text{rem}}_t \leftarrow n^{\text{rem}}_t - \text{take}_{t,r}
$$

where $\kappa_t = \kappa^{\text{pair}}$ for EMPEROR and $\kappa^{\text{seat}}$ otherwise. The band and per-row unit target are:

$$
B_t = \{ r : \text{take}_{t,r} > 0 \}, \qquad q_{t,r} = \text{take}_{t,r}
$$

A tier's last row may be only partially used but still belongs exclusively to that tier; rows behind the Merit band belong to no tier (free-seating section).

### Feasibility gates (run before model construction)

1. **Total capacity** (`check_total_capacity`): if $D > 232$, reject with structured error `CAPACITY_EXCEEDED`.
2. **Band packing** (`compute_tier_bands`): if any tier's demand exceeds $\sum_r \kappa_t(r)$, reject with `TIER_CAPACITY_EXCEEDED`.
3. **Per-band accessibility** (`check_capacity`): each tier's accessible demand must be met by accessible supply _inside its own band_.

For the default 112/22/16 scenario the computed bands are: EMPEROR rows 1–9, BODHI rows 9–10, MERIT rows 10–11; rows 12–16 remain unassigned.

---

## 4. Contribution-Level Domain Reduction (HC5 / HC13)

`preprocessing.compute_allowed_rows` performs a pure domain reduction: it removes only combinations the hard constraints already exclude, but shrinks the CP-SAT model dramatically for demand-heavy tiers.

Within tier $t$, group units by contribution level $g$ and sort levels descending $g_1 > g_2 > \dots$. Level $g_i$ occupies the packing positions

$$
\Big[\, 1 + \textstyle\sum_{j < i} \lvert G_{g_j} \rvert,\ \ \textstyle\sum_{j \le i} \lvert G_{g_j} \rvert \,\Big]
$$

With cumulative row target $Q_r = \sum_{r' \le r,\ r' \in B_t} q_{t,r'}$, row $r$ is _allowed_ for level $g_i$ iff its position interval intersects the level's block:

$$
Q_{r-1} < last_i \ \wedge\ Q_r \ge first_i
$$

---

## 5. Decision Variables

| Symbol                              | Domain                                      | Meaning                     | Code                         |
| ----------------------------------- | ------------------------------------------- | --------------------------- | ---------------------------- |
| $x_{u,s} \in \{0,1\}$               | $u \in U^{\text{single}},\ s \in O_u$       | Single-seat assignment      | `single_vars`                |
| $y_{u,k} \in \{0,1\}$               | $u \in U^{\text{pair}},\ k \in O_u$         | Emperor pair assignment     | `pair_vars`                  |
| $b_{t,i} \in \mathbb{Z}_{[0,\,15]}$ | consecutive contribution levels of tier $t$ | Row boundary between levels | `_add_contribution_ordering` |

Variables are created **only** for eligible combinations: band rows (HC4), accessibility (HC8), non-blocked seats (HC9). Ineligibility is enforced structurally — there is no constraint to violate, simply no variable.

### Derived expressions

Because exactly one option variable of each unit equals 1, the assigned row is the linear expression

$$
row(u) \;=\; \sum_{s \in O_u} row(s)\, x_{u,s}
\qquad\text{or}\qquad
row(u) \;=\; \sum_{k \in O_u} row(k)\, y_{u,k}
$$

and the occupancy of seat $s$ is

$$
occ(s) \;=\; \sum_{u \,:\, s \in O_u} \!\! var_{u,s} \;\in\; \{0, 1\} \quad \text{(by HC3)}
$$

---

## 6. Hard Constraints

| ID   | Statement                                               | Formalisation                                                                                              | Implementation               |
| ---- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------- |
| HC1  | Every single unit gets exactly one seat                 | $\sum_{s \in O_u} x_{u,s} = 1 \quad \forall u \in U^{\text{single}}$                                       | `AddExactlyOne`              |
| HC2  | Every Emperor unit gets exactly one valid pair          | $\sum_{k \in O_u} y_{u,k} = 1 \quad \forall u \in U^{\text{pair}}$                                         | `AddExactlyOne`              |
| HC3  | At most one occupant per physical seat                  | $\sum_{u : s \in O_u} var_{u,s} \le 1 \quad \forall s \in S$                                               | `AddAtMostOne`               |
| HC4  | Tier bands demand-derived, ordered, tier-exclusive      | $B_{\text{EMP}} \prec B_{\text{BOD}} \prec B_{\text{MER}}$ front-to-back; $O_u \subseteq B_{t(u)}$         | `compute_tier_bands`         |
| HC5  | Higher contribution ⇒ equal-or-earlier row              | $\forall t,\ \forall i, j \in t:\ c_i > c_j \Rightarrow row(i) \le row(j)$                                 | boundary encoding (below)    |
| HC6  | Emperor pairs adjacent, same row                        | $k = (s_a, s_b):\ row(s_a) = row(s_b),\ pos(s_b) - pos(s_a) = 1,\ pos(s_a)$ odd                            | `build_valid_pairs`          |
| HC7  | No pair crosses the centre aisle                        | $(pos(s_a), pos(s_b)) \ne (a,\, a+1)$                                                                      | rejected at pair enumeration |
| HC8  | Accessibility                                           | accessible singles → $acc(s) = 1$; accessible pairs → $\exists\, s \in k : acc(s) = 1$                     | eligibility filter           |
| HC9  | Blocked seats never assigned                            | $blk(s) = 1 \Rightarrow s \notin O_u\ \ \forall u$                                                         | eligibility filter           |
| HC11 | Capacity feasibility                                    | $D \le 232$; per-band and per-band-accessible checks                                                       | `check_capacity`             |
| HC12 | Pure integer model                                      | all coefficients, costs, weights $\in \mathbb{Z}$                                                          | whole pipeline               |
| HC13 | Front fill: rows fill front to back                     | $\sum_{u} var_{u,\,\cdot \in r} = q_{t,r} \quad \forall r \in B_t$                                         | `_add_front_fill`            |
| HC14 | Middle fill: each row side fills outward from the aisle | $occ(s_{\text{outer}}) \le occ(s_{\text{inner}})$ for consecutive seats ordered by distance from the aisle | `_add_middle_fill`           |

### HC5 boundary encoding

Sort a tier's distinct contributions descending $g_1 > g_2 > \dots$. Between consecutive levels $g_i, g_{i+1}$ introduce an integer boundary variable $b_{t,i} \in [0, R-1]$ with

$$
row(u) \le b_{t,i} \quad \forall u \in G_{g_i},
\qquad
b_{t,i} \le row(u) \quad \forall u \in G_{g_{i+1}}
$$

Transitivity over the chain of boundaries yields $row(i) \le row(j)$ for every strictly-greater contribution pair, while units with equal contribution remain mutually unordered.

### HC14 correctness

Ordering each row side's non-blocked seats outward from the aisle and chaining $occ(\text{outer}) \le occ(\text{inner})$ forces the occupied seats of each side to form one contiguous block starting at the aisle — patterns such as $[\text{aisle}][X][\ ][X]$ are impossible. The ordering uses $pos(s)$, never $\rho(s)$.

---

## 7. Soft Constraints and Cost Model

All costs are precomputed, non-negative integers (`cost_calculator`), so the objective stays purely integer.

### Normalisation

With `normalize_penalties` enabled, each raw component $c$ is rescaled by its theoretical maximum $\mu_c$ onto $[0, 100]$ using integer round-half-up (`PenaltyScaler.normalized`):

$$
\tilde{c} \;=\; \left\lfloor \frac{2 \cdot 100 \cdot c + \mu_c}{2\,\mu_c} \right\rfloor
\;=\; \operatorname{round}\!\left( \frac{100\,c}{\mu_c} \right)
$$

The closed form $(2nc + d) \,\//\, (2d)$ implements $\operatorname{round}(n/d)$ half-up without floating point.

### SC1 — Priority-seat mismatch

Desired rank of participant $p$ (the best applicable rule wins):

$$
r^{\text{des}}_p = \min\Big( \{r^{\text{def}}\} \cup \{r^{\text{acc}} \mid acc_p\} \cup \{r^{\text{monk}} \mid monk_p\} \cup \{r^{\text{eld}} \mid eld_p\} \Big)
$$

$$
c^{\text{prio}}_{u,o} =
\begin{cases}
\big\lvert r^{\text{des}}_p - \rho(s) \big\rvert & \text{singles} \\[3pt]
\big\lvert r^{\text{des}}_p - \Pi_k \big\rvert & \text{Emperor pairs}
\end{cases}
$$

### SC2 — Category–zone mismatch

$$
c^{\text{zone}}_{u,o} =
\begin{cases}
z_{cat(p),\, zone(s)} & \text{singles} \\[3pt]
z_{cat(p),\, zone(s_a)} + z_{cat(p),\, zone(s_b)} & \text{pairs}
\end{cases}
$$

### SC3 — Movement (regeneration)

Zero when no previous allocation exists or the seat/pair is retained; otherwise:

$$
c^{\text{mov}}_{\text{single}} = \pi^{\text{fix}} + \pi^{\text{row}} \big\lvert row(s) - row(s^{\text{prev}}) \big\rvert + \pi^{\text{col}} \big\lvert pos(s) - pos(s^{\text{prev}}) \big\rvert
$$

$$
c^{\text{mov}}_{\text{pair}} = \pi^{\text{fix}} + \pi^{\text{row}} \big\lvert row(k) - row(k^{\text{prev}}) \big\rvert + \pi^{\text{col}} \big\lvert pos^{\text{first}}(k) - pos^{\text{first}}(k^{\text{prev}}) \big\rvert
$$

With no previous-allocation input, every movement cost is exactly zero.

### SC4 — Activeness mismatch

Target rank from event count $e_p$, normalised over $[e^{\min}, e^{\max}]$ onto $[1, 16]$ (integer round-half-up):

$$
r^{\text{act}}_p = 1 + \left\lfloor \frac{2\,(15)\,\big(e^{\max} - e_p\big) + \Delta}{2\,\Delta} \right\rfloor,
\qquad
\Delta = \max\big(1,\ e^{\max} - e^{\min}\big)
$$

$$
c^{\text{act}}_{u,o} = \big\lvert r^{\text{act}}_p - \rho(\cdot) \big\rvert
$$

### Component maxima (normalisation denominators)

$$
\mu_{\text{prio}} = \max\Big( \rho^{\max} - \min_t r^t,\ \max_t r^t - \min_k \Pi_k \Big),
\qquad
\mu_{\text{zone}} = 2 \max_{cat,\,zone} z_{cat,\,zone}
$$

$$
\mu_{\text{mov}} = \pi^{\text{fix}} + \pi^{\text{row}} (R - 1) + \pi^{\text{col}} (C - 1),
\qquad
\mu_{\text{act}} = \rho^{\max} - 1
$$

### Weighted penalty of a candidate option

$$
\mathrm{Pen}(u, o) \;=\; \sum_{c \,\in\, \{\text{prio},\, \text{zone},\, \text{mov},\, \text{act}\}} w_c \cdot \tilde{c}_{u,o}
$$

---

## 8. Objective Function

$$
\min \; Z \;=\;
\underbrace{M \sum_{u \in U} \mathrm{Pen}\big(u,\, o^*_u\big)}_{\text{main penalty}}
\;+\;
\underbrace{\sum_{u \in U} \tau\big(u,\, o^*_u\big)}_{\text{tie-break}}
$$

where $o^*_u$ is the selected option of unit $u$ and the tie-break term is

$$
\tau(u, o) = \operatorname{rank}(u) \cdot \operatorname{index}(o)
$$

with $\operatorname{rank}(u)$ the 1-based position of $u$ in participant-id order and $\operatorname{index}(o)$ the deterministic global seat index (singles) or pair index (Emperors).

### Symmetry breaking

Swapping two equal-cost units $p, q$ between options $a, b$ changes the tie-break sum by

$$
\big(\operatorname{rank}_p - \operatorname{rank}_q\big)\big(\operatorname{index}_a - \operatorname{index}_b\big) \ne 0
$$

so the optimum is a single canonical layout — deterministic across runs with identical inputs.

### Dominance guarantee

The maximum achievable tie-break total is

$$
\tau^{\max} = \sum_{u \in U} \max_{o \in O_u} \tau(u, o)
$$

and model construction **fails fast** unless $M > \tau^{\max}$ (`_add_objective` raises `ValueError`). Consequently a one-unit main-penalty improvement always outweighs the entire tie-break term: the tie-break can never override the weighted soft constraints, and soft weights can never override hard constraints.

---

## 9. Solution Extraction and Independent Validation

CP-SAT must return status `OPTIMAL`. Any other status yields a structured error document; in particular `FEASIBLE` maps to `OPTIMAL_NOT_PROVEN` (a feasible result is never reported as optimal).

1. **Extraction** (`solver._extract_assignments`): read the $x, y$ variables with value 1.
2. **Objective reconstruction audit:**

$$
\hat{Z} \;=\; M \sum_{u} \mathrm{Pen}(u, o^*_u) + \sum_{u} \tau(u, o^*_u) \;\stackrel{!}{=}\; Z_{\text{solver}}
$$

A mismatch aborts with `OUTPUT_VALIDATION_FAILED`. 3. **Independent validation** (`validator.compute_hard_constraint_validation`): every hard constraint is re-counted purely from the serialized result JSON — duplicate seats, unassigned units, tier-band membership, contribution ordering, Emperor adjacency, aisle crossing, accessibility, blocked seats, front fill, middle fill. All counters must be zero. 4. **Schema validation** (`validator.validate_against_schema`): the result document must conform to `schemas/solver_result.schema.json` (JSON Schema Draft 2020-12).

---

## 10. Benchmark Metrics

`benchmark.run_benchmark` executes the full pipeline $N$ times on freshly loaded inputs and reports per-run and aggregated (min / max / mean / median / p95) statistics:

$$
T_{\text{wall}} = t_{\text{end}} - t_{\text{start}} \quad (\texttt{time.perf\_counter}),
\qquad
\text{gap} = Z - Z^{\text{bound}}
$$

plus CP-SAT statistics (conflicts, branches, variable and constraint counts) and peak RSS via optional `psutil`. No metric is estimated or reused between runs.

---

## 11. Summary of the Complete Model

$$
\boxed{
\begin{aligned}
\min_{x,\, y,\, b} \quad
& M \sum_{u \in U} \sum_{c} w_c\, \tilde{c}_{u,\, o^*_u} \;+\; \sum_{u \in U} \tau(u, o^*_u) \\[4pt]
\text{s.t.} \quad
& \sum_{o \in O_u} var_{u,o} = 1 && \forall u \in U && \text{(HC1, HC2)} \\
& \sum_{u \,:\, s \in O_u} var_{u,s} \le 1 && \forall s \in S && \text{(HC3)} \\
& O_u \subseteq B_{t(u)},\ \ acc/blk \text{ filters} && \forall u \in U && \text{(HC4, HC8, HC9)} \\
& row(i) \le b_{t,i} \le row(j) && \text{consecutive levels} && \text{(HC5)} \\
& \sum_{u} var_{u,\, \cdot \in r} = q_{t,r} && \forall r \in B_t && \text{(HC13)} \\
& occ(s_{\text{outer}}) \le occ(s_{\text{inner}}) && \text{per side, per row} && \text{(HC14)} \\
& var_{u,o} \in \{0,1\},\ \ b_{t,i} \in \mathbb{Z}_{[0,15]} &&
\end{aligned}
}
$$

with the valid-pair set $K$ encoding HC6/HC7 structurally, the capacity gates of §3 rejecting infeasible demand before model construction, and $M > \tau^{\max}$ guaranteeing tie-break dominance.
