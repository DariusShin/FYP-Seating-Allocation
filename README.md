# PJ Kwan Inn Teng — CP-SAT Seat Allocation Prototype

A Python prototype that uses Google OR-Tools CP-SAT to generate an optimized,
constraint-compliant seating allocation for the PJ Kwan Inn Teng FYP case
study: 100 primary participants (8 Emperor × 2 seats, 32 Bodhi, 60 Merit)
allocated onto a 10-row × 12-seat hall with a centre aisle, tier row zones,
contribution ordering, accessibility, and four weighted soft constraints.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -e .
```

Generate the deterministic dataset (seed `20260707`):

```bash
python -m seat_solver.data_generator --count 100 --seed 20260707 --output data/mock_participants.json
python -m seat_solver.floor_plan_generator --rows 10 --seats-per-row 12 --output data/floor_plan.json
```

Solve, validate, and benchmark:

```bash
python -m seat_solver.cli solve \
  --participants data/mock_participants.json \
  --floor-plan data/floor_plan.json \
  --previous-allocation data/previous_allocation.json \
  --config config/solver_config.json \
  --output output/seat_allocation_result.json

python -m seat_solver.cli validate \
  --result output/seat_allocation_result.json \
  --output output/validation_report.json

python -m seat_solver.benchmark \
  --participants data/mock_participants.json \
  --floor-plan data/floor_plan.json \
  --config config/solver_config.json \
  --previous-allocation data/previous_allocation.json \
  --runs 10 \
  --output output/performance_report.json
```

Run the tests:

```bash
pytest -q
```

## Layout

| Path | Purpose |
|---|---|
| `docs/mathematical_model.json` | Full mathematical model: sets, variables, hard/soft constraints, objective, tie-break dominance proof |
| `docs/code_overview.md` | Per-module code walkthrough with Mermaid execution-flow diagrams and the module dependency graph |
| `config/solver_config.json` | Tier boundaries, weights, category-zone cost matrix, movement costs, solver parameters |
| `schemas/` | JSON Schemas for participants, floor plan, config, and result documents |
| `src/seat_solver/` | Solver package: generators, preprocessing, cost matrices, CP-SAT model, solving, formatting, validation, benchmark, CLI |
| `tests/` | pytest suite covering data generation, floor plan, hard/soft constraints, statuses, schemas, regeneration |
| `output/` | Result, validation report, and performance report (generated) |

## Design notes

- **Integer-only model (HC12):** every CP-SAT variable, cost, weight, and
  objective coefficient is an integer; money is integer ringgit.
- **Emperor pairs:** each Emperor registration is one two-seat allocation
  unit assigned to a predefined valid adjacent pair (`y[e,k]` variables);
  positions 6–7 never pair because of the centre aisle.
- **Structural hard constraints:** tier row zones, accessibility, and
  blocked seats are enforced by never creating ineligible variables.
- **Contribution ordering (HC5):** linear boundary-variable encoding between
  consecutive contribution levels inside each tier.
- **Front-fill rows (HC13):** inside each tier zone every seat of row r
  outranks every seat of row r+1, so rows fill front to back and empty seats
  are pinned to the last occupied row of each zone (configurable via
  `constraints.enforce_front_fill`).
- **Penalty normalization:** raw component costs have incomparable scales
  (movement reaches 139 while priority mismatch tops out at 11), so each
  component is rescaled to 0–100 integers by its theoretical maximum before
  weighting (`constraints.normalize_penalties`); the weights then compare
  like for like. Results report unweighted, normalized, and weighted layers.
- **Deterministic tie-break:** the objective is
  `1_000_000 × MainPenalty + TieBreak`, where the tie-break is strictly
  dominated by any main-penalty difference (proof in
  `docs/mathematical_model.json`) and makes the optimum a unique canonical
  layout.
- **Success = proven optimal:** a run is reported as success only when
  CP-SAT returns `OPTIMAL`; everything else becomes a structured JSON error
  (`OPTIMAL_NOT_PROVEN`, `INFEASIBLE`, `TIER_CAPACITY_EXCEEDED`, …).
- **Independent validation:** after extraction the result document itself is
  re-audited (duplicates, adjacency, aisle, tier zones, ordering,
  accessibility, blocked seats, penalty totals, objective reconstruction,
  JSON Schema) before it is accepted.

The output JSON is designed to be renderable by the Buddy seat-map prototype
(`https://buddy-prototype-three.vercel.app/seat`) without a runtime dependency
on it.

## Frontend visualization

`frontend/` contains a Next.js 16 + Tailwind CSS v4 + shadcn/ui prototype that
renders `output/seat_allocation_result.json` in the style of the Buddy seat
page: altar/stage marker, 10 × 12 seat grid with the centre aisle, gold /
silver / bronze tier colours, elderly (★), monastic (☸), accessible (♿) and
moved (↻) markers, per-seat penalty tooltips, distribution and solver stats
sidebars, and a filterable assignments table.

It also supports **in-browser regeneration**: the "Reallocation weights" panel
exposes the four soft-constraint weights as sliders and a "Regenerate seating
plan" button. The button POSTs to `/api/solve`, which runs the Python CP-SAT
solver with the adjusted weights and the *currently displayed plan as the
previous allocation* — raising the movement weight therefore reallocates with
minimal participant movement.

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000/seat
```

The `/seat` page reads `../output/seat_allocation_result.json` at request
time when it exists (re-running the solver refreshes the page) and falls back
to the bundled snapshot in `frontend/src/data/`. Environment overrides:
`SEAT_RESULT_PATH` (result file), `SEAT_SOLVER_ROOT` (repo root used by
`/api/solve`), and `SEAT_SOLVER_PYTHON` (Python executable; defaults to the
repo's `.venv`).
