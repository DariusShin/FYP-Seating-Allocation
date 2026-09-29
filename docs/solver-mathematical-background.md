# Mathematical Model of the Seat Allocation Solver

This document explains, from start to end, the mathematics behind both solver
engines in this repository — the **prototype** (`src/seat_solver/prototype/`)
and the **production** engine (`src/seat_solver/production/`) — assuming only
ordinary mathematics (algebra, sums, inequalities). Every symbol is defined
before it is used.

---

## Part 0 — What problem are we solving?

A temple banquet hall has rows of seats. Participants register with a
**contribution** (money donated, in RM) that places them in one of three
**tiers**:

| Tier | Meaning | Seats needed |
|---|---|---|
| `EMPEROR` | highest donors | 2 (a pair of adjacent seats) |
| `MERIT` | middle donors | 1 |
| `BODHI` | lower donors / monks | 1 |

We must assign every participant to seat(s) so that:

1. **Hard constraints** (rules that must never break) hold — one occupant per
   seat, Emperor pairs adjacent, tiers in the right rows, higher contributors
   not behind lower ones, accessible seats to those who need them, etc.
2. **Soft preferences** (things we would like) are respected as much as
   possible — preferred seat ranks, category zones, minimal movement from a
   previous layout, activity-based row targets.

This is a **constrained optimization problem**: among all assignments that
satisfy every hard constraint, find one that minimizes the total soft
penalty.

We hand the problem to **CP-SAT** (Google OR-Tools), a solver that finds a
*provably best* solution, not just a good one.

---

> The prototype discussion below is historical. Part II and the [active model](mathematical_model.md) describe production v4, which has no attendance-driven changes.

## Part I — The prototype engine

Files, in the order the pipeline runs:
`models.py` → `preprocessing.py` → `cost_calculator.py` → `cp_sat_model.py`
→ `solver.py` → `validator.py` → `result_formatter.py`.

### 0.1 Symbols used throughout

| Symbol | Meaning |
|---|---|
| $P$ | set of participants, indexed $p$ |
| $S$ | set of physical seats, indexed $s$ |
| $R$ | number of rows; row numbers $1 \dots R$ |
| $t(p) \in \{\text{EMPEROR}, \text{MERIT}, \text{BODHI}\}$ | tier of participant $p$ |
| $c(p)$ | contribution of $p$ in RM (integer) |
| $U_E$ | Emperor **allocation units** (one unit = one participant needing a pair) |
| $U_1$ | single-seat allocation units (one unit = one MERIT or BODHI participant) |
| $K$ | set of valid adjacent seat pairs (odd position $j$ with $j+1$, never crossing the aisle) |
| $x_{p,s} \in \{0,1\}$ | 1 if single unit $p$ is assigned seat $s$ |
| $y_{u,k} \in \{0,1\}$ | 1 if Emperor unit $u$ is assigned pair $k$ |
| $w_1, w_2, w_3, w_4$ | weights of the four soft components |

### 0.2 Step 1 — From people to allocation units (`preprocessing.py`)

An Emperor participant occupies **two seats**, so the solver does not think in
people but in **allocation units**:

- Each Emperor participant becomes one unit that must take exactly one
  **valid pair** $k \in K$.
- Each MERIT/BODHI participant becomes one unit that must take exactly one
  **seat** $s \in S$.

A pair $k = (s_a, s_b)$ is *valid* when:

$$
\text{row}(s_a) = \text{row}(s_b), \quad
\text{pos}(s_b) = \text{pos}(s_a) + 1, \quad
\text{pos}(s_a) \text{ is odd}, \quad
\{s_a, s_b\} \cap \text{aisle-gap} = \emptyset, \quad
s_a, s_b \text{ not blocked}.
$$

The **aisle-gap** is the two positions straddling the centre aisle
(positions 8 and 9 in the 16-seat rows): a pair $(8, 9)$ would have its two
members separated by the aisle, so it is excluded.

### 0.3 Step 2 — Tier bands (HC4)

The hall is partitioned front-to-back into **bands**: contiguous blocks of
rows, one per tier, in the order

$$
\text{EMPEROR} \rightarrow \text{MERIT} \rightarrow \text{BODHI}.
$$

Band derivation is a greedy packing. Let

- $\text{pairCap}(r)$ = number of valid pairs in row $r$,
- $\text{seatCap}(r)$ = number of non-blocked seats in row $r$,
- $n_E, n_M, n_B$ = counts of Emperor, Merit, Bodhi **units**.

Walk rows $r = 1, 2, \dots$; the current tier consumes
$\min(\text{remaining}, \text{capacity}(r))$ units on row $r$ until its demand
is exhausted, then the next tier starts on the following row. Formally, for
tier $T$ with demand $n_T$ starting at row $r_T$:

$$
\text{target}_T(r) =
\begin{cases}
\min\big(n_T - \sum_{r' < r} \text{target}_T(r'),\ \text{cap}_T(r)\big) & r \ge r_T,\ \sum_{r' \le r} \text{target}_T(r') < n_T \\
0 & \text{otherwise}
\end{cases}
$$

where $\text{cap}_T = \text{pairCap}$ for EMPEROR and $\text{seatCap}$
otherwise. Rows are **tier-exclusive**: a row belongs to at most one tier, and
a tier's last row may be partially filled. Rows behind the last band are the
free-seating section.

*Example (default dataset: 86 Emperor, 24 Merit, 12 Bodhi on a 16×16 hall
with 24 blocked seats):* Emperor pairs fill rows 1–13 (row 13 only 2 pairs),
Merit takes rows 14–15 (16 + 8 units), Bodhi takes row 16 (12 units).

If the bands do not fit the hall, the input is rejected with a structured
error before any solving.

### 0.4 Step 3 — Domain pruning (`compute_allowed_rows`)

Within a tier, contribution ordering (HC5 below) forces each **contribution
level** (a group of units with equal $c(p)$) into a contiguous block of
packing positions. Sorting a tier's units by contribution descending, level
$g$ occupies positions $f_g \dots l_g$ where

$$
f_g = 1 + \sum_{g' < g} |G_{g'}|, \qquad
l_g = \sum_{g' \le g} |G_{g'}|.
$$

Row $r$ covers positions $\big(\sum_{r' < r} \text{target}(r'),\
\sum_{r' \le r} \text{target}(r')\big]$. Unit $p$ in level $g$ may only sit on
rows whose position interval intersects $[f_g, l_g]$:

$$
\text{allowed}(p) = \Big\{ r :\ \text{posStart}(r) < l_g \ \wedge\ \text{posEnd}(r) \ge f_g \Big\}.
$$

This is a *pure* reduction — it removes only combinations the hard
constraints already forbid — but it shrinks the CP-SAT model dramatically.

### 0.5 Step 4 — Integer cost tables (`cost_calculator.py`)

CP-SAT works only with **integers**, so every soft preference is pre-computed
as a non-negative integer penalty for each (unit, option) combination. There
are four components:

**SC1 — priority-seat mismatch.** Each participant has a *desired rank*
$d(p)$: the best (numerically lowest) rank among the rules that apply to them
(accessible → rank 1, monk → rank 1, elderly → rank 3, default → rank 10).
The penalty is the distance between the seat's actual rank and the desired
rank:

$$
\text{pen}_{1}(p, s) = |\,\text{rank}(s) - d(p)\,|.
$$

**SC2 — category-zone mismatch.** The hall's seats are grouped into zones
$Z$ (left/right × centre/outer). Each participant category $cat(p)$ has a
cost table $C_{cat}: Z \to \mathbb{Z}_{\ge 0}$:

$$
\text{pen}_{2}(p, s) = C_{cat(p)}\big(\text{zone}(s)\big).
$$

**SC3 — movement.** If a previous layout exists and participant $p$ sat at
seat set $A_p$ before, the movement penalty is 0 when they keep the same
seats and grows with the row distance otherwise:

$$
\text{pen}_{3}(p, s) =
\begin{cases}
0 & A_p = \{s\} \\
|\,\text{row}(s) - \text{row}(A_p)\,| \cdot \text{moveCost} & \text{otherwise}
\end{cases}
$$

where $\text{row}(A_p)$ is the row of the previous seat.

**SC4 — activeness mismatch.** Each participant has an activity score
$a(p)$ = events joined in the last two years. The tier's activity range
$[a_{\min}, a_{\max}]$ maps linearly onto seat ranks: very active
participants deserve front seats. The target rank is

$$
\text{target}(p) = 1 + \left\lfloor \frac{(R_{\max}-1)(a_{\max} - a(p)) + \max(1, a_{\max}-a_{\min})/2}{\max(1, a_{\max}-a_{\min})} \right\rfloor
$$

(integer round-half-up, no floating point), and the penalty is

$$
\text{pen}_{4}(p, s) = |\,\text{rank}(s) - \text{target}(p)\,|.
$$

**Normalization.** The raw scales differ wildly (movement can reach several
hundred on a 16×16 hall; priority mismatch tops out at 15). With
normalization enabled, each component is rescaled to $0 \dots 100$ by its
theoretical maximum $M_c$:

$$
\widetilde{\text{pen}}_c = \left\lfloor \frac{100 \cdot \text{pen}_c + M_c/2}{M_c} \right\rfloor
\quad \text{(integer round-half-up)}.
$$

The **weighted cost** of assigning unit $p$ to option $o$ is then

$$
\text{cost}(p, o) = \sum_{c \in \{1,2,3,4\}} w_c \cdot \widetilde{\text{pen}}_c(p, o).
$$

### 0.6 Step 5 — The CP-SAT model (`cp_sat_model.py`)

CP-SAT is a **constraint programming + SAT hybrid**: you declare Boolean
decision variables and linear constraints over them, plus one linear
objective to minimize. It searches for the assignment with the smallest
objective and *proves* nothing better exists.

**Decision variables.**

- $x_{p,s} \in \{0,1\}$ for every single unit $p$ and every *eligible* seat
  $s$ (eligibility = right band row, not blocked, accessible if required,
  inside the allowed-row set from §0.4).
- $y_{u,k} \in \{0,1\}$ for every Emperor unit $u$ and every eligible valid
  pair $k$.

Variables are created **only for eligible combinations** — infeasible choices
simply do not exist in the model. This is called *modeling by omission*, and
it enforces several hard constraints for free.

**Hard constraints.**

- **HC1 (exactly one seat per single unit):**
  $$\sum_{s \in \text{eligible}(p)} x_{p,s} = 1 \qquad \forall p \in U_1$$
- **HC2 (exactly one pair per Emperor unit):**
  $$\sum_{k \in \text{eligible}(u)} y_{u,k} = 1 \qquad \forall u \in U_E$$
- **HC3 (at most one occupant per seat):** for each seat $s$, let
  $V(s) = \{x_{p,s}\} \cup \{y_{u,k} : s \in k\}$; then
  $$\sum_{v \in V(s)} v \le 1.$$
- **HC5 (contribution ordering, per tier):** group units by contribution
  level; between consecutive levels $g$ (higher) and $g+1$ (lower) introduce
  an integer boundary variable $b_g \in [0, R-1]$ with
  $$\text{row}(i) \le b_g \quad \forall i \in G_g, \qquad
    b_g \le \text{row}(j) \quad \forall j \in G_{g+1}.$$
  Here $\text{row}(i)$ is the linear expression
  $\sum_o \text{rowIndex}(o) \cdot v_{i,o}$ — because exactly one $v$ is 1,
  the weighted sum equals the assigned row. Transitivity along the chain of
  boundaries gives $\text{row}(i) \le \text{row}(j)$ whenever
  $c(i) > c(j)$, while equal contributions stay unordered.
- **HC13 (front fill):** each band row's occupancy is fixed by the band
  derivation, so it becomes an equality:
  $$\sum_{k \in \text{pairs on row } r} y_{u,k} = \text{target}_E(r), \qquad
    \sum_{p \in T} x_{p,s} \big|_{\text{row}(s)=r} = \text{target}_T(r)$$
  for $T \in \{\text{MERIT}, \text{BODHI}\}$.
- **HC14 (middle fill):** on each side of each row, order the seats by
  distance from the aisle: $s_1$ (nearest) $\dots s_m$ (outermost). Require
  $$\text{occ}(s_{i+1}) \le \text{occ}(s_i) \quad \forall i$$
  where $\text{occ}(s) = \sum V(s)$. By transitivity the occupied seats form
  one contiguous block starting at the aisle — no gaps like `[X][ ][X]`.

**Objective.** Minimize

$$
\min \ \text{SCALE} \cdot \underbrace{\sum_{p \in U_1} \sum_{s} x_{p,s}\, \text{cost}(p,s)
+ \sum_{u \in U_E} \sum_{k} y_{u,k}\, \text{cost}(u,k)}_{\text{main penalty}}
\; + \; \underbrace{\sum v_{i,o} \cdot \tau(i,o)}_{\text{tie-break}}
$$

where $\text{SCALE}$ is a large constant (e.g. $10^5$) and
$\tau(i,o) = \text{rank}(i) \cdot \text{index}(o)$ is a tiny tie-break term
(unit's 1-based position in participant-id order × deterministic seat index).

*Why the tie-break?* Many assignments have identical cost (swapping two
equal-cost participants changes nothing). The tie-break breaks that symmetry
so the solver returns one **canonical** layout, making runs deterministic.
*Why it is safe:* the maximum possible tie-break total is computed and kept
strictly below $\text{SCALE}$, so a one-unit difference in the main penalty
always outweighs the entire tie-break term — the tie-break can never trade
solution quality for determinism.

### 0.7 Step 6 — Solving (`solver.py`)

`solve_seat_allocation` orchestrates: validate → preprocess → build model →
`solver.Solve(model)` → extract → audit. The solver returns a status:

| Status | Meaning | Action |
|---|---|---|
| `OPTIMAL` | best possible, proven | accept |
| `FEASIBLE` | valid but maybe not best | reject when `require_optimal` |
| `INFEASIBLE` | constraints contradict | structured error |
| `UNKNOWN` | time limit hit without proof | structured error |

Extraction: for each unit, the one variable with value 1 names its seat(s).

### 0.8 Step 7 — Independent audit (`validator.py`)

The extracted solution is re-checked **from the result JSON alone**, never
from solver internals: duplicate seats, adjacency, aisle crossing, tier
bands (C10), band ordering (C11), band recomputation (C12), contribution
ordering (C13), accessibility, blocked seats, middle fill, and an
**independent reconstruction of the objective value**. If any check fails,
the result is rejected — a solver or extraction bug can never silently
produce a bad seat map.

---

## Part II — The production engine (policy v4)

The complete current formulation is [mathematical_model.md](mathematical_model.md), with the machine-readable contract in [mathematical_model.json](mathematical_model.json).

Production uses confirmed paid registration units. Emperor always selects an approved adjacent pair and Merit/Bodhi select one seat. Attendance is not part of the input or eligibility calculation. All higher-tier physical seats precede lower-tier seats in row-major priority order. Within-tier contribution row ordering, accessibility, blocked-seat exclusion, front-fill and centre-out packing remain compulsory.

The objective combines three normalized integer costs: contribution-to-seat desirability, historical activeness and category-zone suitability. Enabled preferences are weighted 40/30/20 in priority order. Canonicalization follows the proven weighted objective under one shared deadline. Initial generation and regeneration use the same model; there are no repair scopes, previous-allocation inputs or movement objectives.

`production_validator.py` independently reconstructs solver rules and result metrics. `workspace.py` permits whole-registration manual moves and docking but enforces registration immutability, complete pair/seat cardinality, valid unique seats and accessibility; docking must be resolved before publication. Display names and notes are separate editable metadata. Publication switches the explicit public pointer atomically with revision checks.

The revised Objective 2 proposes explainable verification of every applicable business rule before manual publication, bound to the exact saved revision and content hash. This complete gate is planned; the current workspace does not yet enforce contribution order or packing after manual moves.

The local v4 store is `output/paid-seats-v4.sqlite3`. Earlier histories remain untouched. The prototype discussion above is historical and is not the production API.
