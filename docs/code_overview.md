# `seat_solver` Code Overview

This document explains every module in [`src/seat_solver/`](../src/seat_solver/), shows each module's execution flow as a Mermaid diagram, and ends with a dependency graph linking all the files together.

## The big picture

The package implements one pipeline: load JSON inputs → validate them → convert participants into allocation units → precompute integer costs → build a CP-SAT model → solve to proven `OPTIMAL` → extract and re-audit the solution → emit frontend-friendly JSON. Each stage lives in its own module, and only `solver.py` knows about all of them.

```mermaid
flowchart LR
    A[data_generator.py<br/>mock participants] --> D[solver.py]
    B[floor_plan_generator.py<br/>10 x 12 hall] --> D
    C[config/solver_config.json] --> D
    D -->|"OPTIMAL + audited"| E[output/seat_allocation_result.json]
    E --> F[validator.py<br/>21-check report]
    E --> G[frontend /seat page]
```

---

## `__init__.py`

Package marker only. Declares `__version__ = "0.1.0"`; no logic.

---

## `models.py`

The typed data layer shared by every other module. Defines frozen dataclasses for all domain objects and the JSON load/save helpers, so file I/O and parsing never leak into the algorithmic modules.

Key contents:

| Item | Role |
|---|---|
| `Participant` | One primary registration record (tier, contribution, flags, previous seats). |
| `Seat` / `FloorPlan` | Physical seat (`physical_position` for adjacency, `priority_rank` for desirability — deliberately separate) and the seat collection with lookup helpers (`seat_by_id`, `seats_in_row`). |
| `TierConfig` / `SolverConfig` | Parsed `solver_config.json`: tier boundaries, weights, cost matrices, movement parameters, Emperor pair priorities, `enforce_front_fill`, `enforce_middle_fill`, `normalize_penalties`, tie-break scale, CP-SAT parameters. |
| `PreviousAllocation` | `participant_id → seat_ids` mapping from the previous event. |
| `read_json` / `write_json` / `load_*` | All file I/O for the package. |
| `InputDataError` | Raised when a JSON document cannot be parsed into a model. |

```mermaid
flowchart TD
    A[JSON file on disk] --> B["read_json()"]
    B --> C{document type}
    C -->|participants| D["Participant.from_dict() per record"]
    C -->|floor plan| E["FloorPlan.from_dict() -> Seat.from_dict() per seat"]
    C -->|config| F["SolverConfig.from_dict() -> TierConfig per tier"]
    C -->|previous allocation| G["PreviousAllocation.from_dict()"]
    D & E & F & G --> H[frozen dataclass instances]
    H --> I["to_dict() when serializing back to JSON"]
```

---

## `floor_plan_generator.py`

Deterministically generates the 10-row × 12-seat hall. Encodes the three spatial rules: the mirrored priority pattern `[12,10,8,6,4,2,1,3,5,7,9,11]` (right side outranks the mirrored left seat), the four zones (`LEFT_OUTER`, `LEFT_CENTER`, `RIGHT_CENTER`, `RIGHT_OUTER`), and the tier row zones (Emperor 1–2, Bodhi 3–5, Merit 6–10). Seats at positions 1, 6, 7, 12 are accessible; no seat is blocked by default.

```mermaid
flowchart TD
    A["main(): parse --rows / --seats-per-row / --output"] --> B["generate_floor_plan()"]
    B --> C{for each row 1..10}
    C --> D{for each position 1..12}
    D --> E["priority_rank_for_position()<br/>right: odd ranks 1,3,5... - left: even ranks 2,4,6..."]
    D --> F["zone_for_position()<br/>outer/center split per side"]
    D --> G["tier_zone_for_row()<br/>EMPEROR / BODHI / MERIT"]
    E & F & G --> H["Seat(seat_id=RxxSyy, accessible at 1/6/7/12)"]
    H --> I[FloorPlan with 120 seats]
    I --> J["write_json(data/floor_plan.json)"]
```

---

## `data_generator.py`

Generates the fixed 100-record synthetic dataset (8 Emperor, 32 Bodhi, 60 Merit → exactly 108 seats demanded) plus a consistent `previous_allocation.json`. All randomness flows through one seeded `random.Random(20260707)`, so output is byte-identical between runs.

The previous allocation is built to satisfy **every hard constraint** so a zero-movement regeneration is always feasible: seats fill in contribution order (which also satisfies front-fill), then a same-row repair pass swaps accessibility-requiring participants onto accessible seats (same-row swaps cannot break contribution ordering), and finally a deterministic ~70% subset keeps its seats.

```mermaid
flowchart TD
    A["main(): --count --seed --output"] --> B["generate_participants(seed)"]
    B --> B1[fixed tiers: 8 EMPEROR, 32 BODHI, 60 MERIT]
    B --> B2[seeded contributions, names, ages,<br/>8 monks, 24 elderly, 6 accessible, events 0..22]
    B --> B3[4 Emperors with guest name, 4 with null]
    A --> C["generate_floor_plan()"]
    B1 & B2 & B3 --> D["build_previous_allocation()"]
    C --> D
    D --> D1[fill pairs/seats in contribution order<br/>row by row, priority rank inside row]
    D1 --> D2[same-row accessibility repair swaps]
    D2 --> D3[keep deterministic 70% sample]
    D3 --> E[embed previous_seat_ids into participants]
    E --> F["write_json(mock_participants.json)"]
    D3 --> G["write_json(previous_allocation.json)"]
```

---

## `preprocessing.py`

Everything that must happen **before** the CP-SAT model exists: structural input validation, capacity checks, valid-pair enumeration, allocation-unit construction, and the front-fill row targets. Hard constraints HC4 (tier zones), HC8 (accessibility), and HC9 (blocked seats) are enforced *structurally* here — ineligible combinations simply never become variables.

Key contents:

- `validate_inputs()` — duplicate ids, tier/contribution consistency, unknown seats, previous-allocation seat reuse → `StructuredError("INVALID_INPUT")`.
- `build_valid_pairs()` — enumerates the pair set `K` from `emperor_pair_priorities` inside Emperor rows; refuses aisle-crossing pairs (HC7) and skips blocked seats.
- `check_capacity()` — HC11: total demand vs available seats, per-tier zone capacity, and accessible-seat/pair supply vs demand → `CAPACITY_EXCEEDED` / `TIER_CAPACITY_EXCEEDED`.
- `build_allocation_units()` — converts each participant into a `SingleUnit` (eligible seats) or `EmperorUnit` (eligible pairs).
- `compute_row_fill_targets()` — HC13: because tier demand is known up front, each zone row's occupancy is fully determined by filling rows front-to-back; returns `{tier: {row: required_count}}`.

```mermaid
flowchart TD
    A[participants + floor plan + config + previous] --> B["validate_inputs()"]
    B -->|problems| B1[StructuredError INVALID_INPUT]
    B -->|ok| C["build_valid_pairs()<br/>pairs K in Emperor rows, no aisle crossing"]
    C --> D["check_capacity()<br/>HC11 total + per-tier + accessible supply"]
    D -->|exceeded| D1[StructuredError CAPACITY_EXCEEDED /<br/>TIER_CAPACITY_EXCEEDED]
    D -->|ok| E["build_allocation_units()"]
    E --> E1["SingleUnit: eligible seats<br/>(tier zone, not blocked, accessible if required)"]
    E --> E2["EmperorUnit: eligible pairs<br/>(accessible pair if required)"]
    A --> F["compute_row_fill_targets()<br/>fill zone rows front to back"]
```

---

## `cost_calculator.py`

Precomputes the four soft-constraint costs as non-negative integers (HC12: nothing floating-point ever reaches the model) and implements **penalty normalization**.

- `desired_priority_rank()` — SC1 target: accessible/monk → 1, elderly → 3, general → 8; lowest applicable rank wins.
- `activity_target_rank()` — SC4: maps `events_joined_last_2_years` onto ranks 1..12 with integer round-half-up arithmetic.
- `movement_cost_single()` / `movement_cost_pair()` — SC3: zero for the previous seat/pair or when no previous allocation exists, otherwise `fixed + row_weight·Δrow + column_weight·Δcolumn`.
- `compute_component_maxima()` — theoretical maximum raw cost per component (priority 11, zone 16, movement 139, activeness 11 for the default scenario).
- `PenaltyScaler` — rescales each raw cost to `0..100` by its maximum (`(2·100·raw + max) // (2·max)`, round half up), so the four weights act on comparable quantities. Pass-through when `normalize_penalties` is off.
- `CostBreakdown` — raw components plus `normalized_components()`, `weighted_components()` (= weight × normalized), `weighted_total()`.
- `CostCalculator` — caches config/floor-plan/previous context and produces a `CostBreakdown` per eligible (unit, seat) or (unit, pair) candidate.

```mermaid
flowchart TD
    A["CostCalculator(participants, floor_plan, config, previous)"] --> B[min/max activity over dataset]
    A --> C["compute_component_maxima()"]
    C --> D["PenaltyScaler(normalize, maxima, scale=100)"]
    E["single_cost(unit, seat) / pair_cost(unit, pair)"] --> F["SC1 priority: abs(desired rank - seat rank/pair priority)"]
    E --> G["SC2 zone: category-zone matrix lookup<br/>(pair = sum of both seats)"]
    E --> H["SC3 movement: 0 if same seat/pair or no previous,<br/>else fixed + row and column distance"]
    E --> I["SC4 activeness: abs(activity target rank - rank)"]
    F & G & H & I --> J[CostBreakdown raw integers]
    J --> K["normalized_components(scaler): 0..100 each"]
    K --> L["weighted_components(config): weight x normalized"]
```

---

## `cp_sat_model.py`

Builds the pure-integer CP-SAT model from the preprocessed units and costs. Returns a `ModelBundle` carrying the model plus every lookup needed later for extraction and auditing (variables, cost breakdowns, tie-break terms, eligible counts).

Constraint encoding:

- **HC1/HC2** — `AddExactlyOne` over each unit's variables.
- **HC3** — `AddAtMostOne` over each seat's occupant variables (pair variables appear under both of their seats).
- **HC5** — contribution ordering via boundary variables: sort each tier's distinct contribution values descending; between consecutive levels add `row(higher) ≤ b ≤ row(lower)`; transitivity gives the full ordering without ordering equal contributors.
- **HC13** — front-fill: exact equalities `Σ assignment vars on zone row r == target(r)` from `compute_row_fill_targets()`.
- **Objective** — `Minimize(Σ var · (SCALE · weighted_cost + tie_break))` where `tie_break = unit_rank · option_index`. The builder computes the exact maximum achievable tie-break total and refuses to run if it reaches `main_objective_scale`, which proves the tie-break can never override a main-penalty difference (and makes the optimum a unique canonical layout).

```mermaid
flowchart TD
    A["build_model(singles, emperors, pairs, floor_plan, config, cost_calculator)"] --> B["create x[p,s] BoolVars for eligible seats<br/>+ AddExactlyOne per single (HC1)"]
    A --> C["create y[e,k] BoolVars for eligible pairs<br/>+ AddExactlyOne per Emperor (HC2, HC6, HC7)"]
    B & C --> D["AddAtMostOne per physical seat (HC3)"]
    B & C --> E["_add_contribution_ordering (HC5)<br/>row expressions + boundary IntVars per tier"]
    A --> F{enforce_front_fill?}
    F -->|yes| G["_add_front_fill (HC13)<br/>row occupancy equalities from targets"]
    F -->|no| H[skip]
    A --> M{enforce_middle_fill?}
    M -->|yes| N["_add_middle_fill (HC14)<br/>occ(outer) <= occ(inner) outward from the aisle"]
    M -->|no| O[skip]
    D & E & G & N --> I["_add_objective<br/>Minimize SCALE * (weight x normalized cost) + unit_rank * option_index"]
    I --> J{max tie-break >= scale?}
    J -->|yes| K[raise ValueError -> MODEL_INVALID]
    J -->|no| L[ModelBundle]
```

---

## `solver.py`

The orchestrator and single public entry point: `solve_seat_allocation(participants, floor_plan, config, previous_allocation=None) → dict`. It always returns a JSON-serializable document — success **only** when CP-SAT proves `OPTIMAL` *and* the extracted solution survives independent re-auditing and JSON Schema validation; every other outcome becomes a structured error (`INVALID_INPUT`, `CAPACITY_EXCEEDED`, `TIER_CAPACITY_EXCEEDED`, `OPTIMAL_NOT_PROVEN`, `INFEASIBLE`, `MODEL_INVALID`, `SOLVER_UNKNOWN`, `OUTPUT_VALIDATION_FAILED`).

Notable details:

- Status mapping: `FEASIBLE` is never accepted (returns `OPTIMAL_NOT_PROVEN`); only `OPTIMAL` proceeds.
- Objective audit: recomputes `SCALE · main_penalty + tie_break` from the extracted assignments and requires it to equal `solver.ObjectiveValue()`.
- Hard-constraint audit: rebuilds all violation counters **from the serialized result document itself** (via `validator.compute_hard_constraint_validation`) rather than trusting solver internals.
- Collects real solver statistics (wall/user time, conflicts, branches, variable and constraint counts, approximate peak RSS via optional `psutil`).

```mermaid
flowchart TD
    A["solve_seat_allocation()"] --> B["validate_inputs()"]
    B -->|error| Z[structured error JSON]
    B --> C["build_valid_pairs() + check_capacity()"]
    C -->|error| Z
    C --> D["build_allocation_units()<br/>any unit with zero options -> error"]
    D -->|error| Z
    D --> E["CostCalculator + build_model()"]
    E -->|ValueError| Z
    E --> F["CpSolver.Solve()<br/>time limit, workers, seed from config"]
    F --> G{status}
    G -->|FEASIBLE| Z1[OPTIMAL_NOT_PROVEN]
    G -->|INFEASIBLE / MODEL_INVALID / UNKNOWN| Z2[matching error code]
    G -->|OPTIMAL| H["_extract_assignments()<br/>chosen seat/pair per unit + costs + tie-break"]
    H --> I{"objective == SCALE * main + tie_break?"}
    I -->|no| Z3[OUTPUT_VALIDATION_FAILED]
    I -->|yes| J["build_success_result()"]
    J --> K["compute_hard_constraint_validation()<br/>re-audit from the result document"]
    K -->|violation| Z3
    K --> L["validate_against_schema()"]
    L -->|schema errors| Z3
    L -->|clean| M[success result dict]
```

---

## `result_formatter.py`

Turns extracted solutions into the frontend-friendly result document (and builds error documents). Contains no solver logic — only presentation:

- `ExtractedAssignment` — one solved unit (participant, seats, chosen pair, `CostBreakdown`, tie-break value, effective previous seats, derived `moved` flag).
- `_display_names()` — Emperor pairs show the primary participant on the better-ranked seat and the guest (or the primary name again when the guest is null) on the other seat.
- `build_success_result()` — assembles `input_summary`, `weights`, `constraint_config` (front-fill flag, normalization scale, component maxima), `solver` stats, the three-layer `penalty_summary` (unweighted / normalized / weighted + tie-break), the per-row floor-plan section with occupancy status, sorted per-assignment payloads with full penalty breakdowns, `empty_seat_ids`, and the hard-constraint block.
- `build_error_result()` — the structured error envelope that stays renderable by the frontend.

```mermaid
flowchart TD
    A["build_success_result(...)"] --> B["_display_names() per assignment<br/>guest on second seat of Emperor pair"]
    A --> C[accumulate totals per component:<br/>raw, normalized, weighted + tie-break]
    C --> D["assignment payloads (sorted by id)<br/>seats, pair priority, previous seats, moved,<br/>penalty: unweighted / normalized / weighted"]
    A --> E[floor plan rows with occupancy:<br/>OCCUPIED / EMPTY / BLOCKED + display names]
    E --> F[empty_seat_ids]
    B & D & F --> G[complete result dict:<br/>input_summary, weights, constraint_config,<br/>solver stats, penalty_summary, assignments,<br/>hard_constraint_validation]
    H["build_error_result(code, message, ...)"] --> I[error dict with solver timing fields]
```

---

## `validator.py`

Independent validation that works **purely from the serialized result dictionary** — never from solver internals — so the same code audits a fresh solve and powers `cli validate` on a file from disk.

- `validate_against_schema()` — JSON Schema validation against `schemas/` (locatable via the `SEAT_SOLVER_SCHEMA_DIR` env var).
- `compute_hard_constraint_validation()` — recounts duplicates, tier-zone, adjacency, aisle, accessibility, blocked-seat, contribution-ordering, and front-fill violations from the document.
- `count_front_fill_violations()` — HC13 audit: an earlier zone row with an empty available seat while a later row is occupied is a violation (returns 0 when the run had front-fill disabled, read from `constraint_config`).
- `count_middle_fill_violations()` — HC14 audit: walking outward from the centre aisle on each side of each row, an occupied seat found after an empty seat is a violation (returns 0 when the run had middle-fill disabled, read from `constraint_config`).
- `validate_result()` — the 21-check report (C01–C21): counts (100 processed / 108 occupied / 12 empty), uniqueness, per-tier seat counts, pair adjacency and aisle rules, tier zones, contribution ordering, accessibility, blocked seats, penalty-layer consistency (normalized values recomputed from `component_maxima`), objective reconstruction, schema conformance, `OPTIMAL` status, zero gap, and front-fill.

```mermaid
flowchart TD
    A["validate_result(result)"] --> B{status == success?}
    B -->|no| C[single failing C00 check -> report]
    B -->|yes| D[build seat lookup + tier rows from floor plan section]
    D --> E[C01..C03 counts: 100 processed,<br/>108 occupied, 12 empty]
    D --> F[C04..C07 uniqueness + per-tier seat counts]
    D --> G[C08..C09 pair adjacency + no aisle crossing]
    D --> H[C10..C12 tier row zones]
    D --> I[C13 contribution ordering]
    D --> J[C14..C15 accessibility + blocked seats]
    D --> K[C16 penalty layers: normalized recomputed<br/>from maxima, weighted = weight x normalized]
    K --> L[C17 objective == scale * main + tie-break]
    D --> M[C18 JSON Schema conformance]
    D --> N[C19 OPTIMAL + C20 zero gap]
    D --> O[C21 front-fill rows when enforced]
    E & F & G & H & I & J & L & M & N & O --> P["_report(): overall_passed + per-check details"]
```

---

## `cli.py`

The command-line interface with two subcommands. Expected failures (unreadable files, invalid input, solver failures) are written as structured JSON error documents and reported through the exit code — never as uncaught tracebacks.

- `solve` — loads participants, floor plan, config, and the optional previous allocation; runs `solve_seat_allocation`; writes the result; exit 0 only on success.
- `validate` — loads a result file, runs `validate_result`, writes the 21-check report; exit 0 only when every check passes.

```mermaid
flowchart TD
    A[python -m seat_solver.cli] --> B{subcommand}
    B -->|solve| C["load participants / floor plan / config / previous"]
    C -->|load failure| D[INVALID_INPUT error JSON + exit 1]
    C --> E["solve_seat_allocation()"]
    E --> F["write_json(--output)"]
    F --> G{status == success?}
    G -->|yes| H[print stats + exit 0]
    G -->|no| I[print error code + exit 1]
    B -->|validate| J["read_json(--result)"]
    J --> K["validate_result() -> 21 checks"]
    K --> L["write_json(validation report)"]
    L --> M{overall_passed?}
    M -->|yes| N[exit 0]
    M -->|no| O[exit 1]
```

---

## `benchmark.py`

Runs the complete solve pipeline N times (default 10) on freshly loaded inputs and writes `output/performance_report.json`. Timing uses `time.perf_counter` around each whole run; per-run CP-SAT statistics come from that run's actual solver response — nothing is estimated or reused. Aggregates min/max/mean/median/p95 wall time, objective values, bounds, conflicts, branches, and approximate peak RSS, and fails (exit 1) if any run is not `OPTIMAL`.

```mermaid
flowchart TD
    A["main(): --runs --output ..."] --> B["run_benchmark()"]
    B --> C{"for run 1..N"}
    C --> D[reload participants, floor plan,<br/>config, previous allocation]
    D --> E["perf_counter start -> solve_seat_allocation() -> stop"]
    E --> F{success?}
    F -->|yes| G[record wall time, objective, bound,<br/>conflicts, branches, variables, RSS]
    F -->|no| H[record error code + message]
    G & H --> C
    C -->|done| I["aggregate: min / max / mean / median / _p95()"]
    I --> J["write_json(performance_report.json)"]
    J --> K{failed runs?}
    K -->|0| L[exit 0]
    K -->|>0| M[exit 1]
```

---

## Module dependency graph

Arrows point from the importing module to the module it imports. `models.py` is the shared foundation; `solver.py` is the only module that composes the whole pipeline; `ortools` and `jsonschema` are the only third-party dependencies and are isolated to three files.

```mermaid
flowchart BT
    subgraph external [Third-party]
        ORTOOLS[(ortools.sat<br/>CP-SAT)]
        JSONSCHEMA[(jsonschema)]
    end

    MODELS[models.py]

    FLOORGEN[floor_plan_generator.py] --> MODELS
    DATAGEN[data_generator.py] --> MODELS
    DATAGEN --> FLOORGEN

    PREP[preprocessing.py] --> MODELS
    COST[cost_calculator.py] --> MODELS
    COST --> PREP

    CPMODEL[cp_sat_model.py] --> COST
    CPMODEL --> PREP
    CPMODEL --> MODELS
    CPMODEL --> ORTOOLS

    FORMATTER[result_formatter.py] --> COST
    FORMATTER --> PREP
    FORMATTER --> MODELS

    VALIDATOR[validator.py] --> MODELS
    VALIDATOR --> JSONSCHEMA

    SOLVER[solver.py] --> PREP
    SOLVER --> COST
    SOLVER --> CPMODEL
    SOLVER --> FORMATTER
    SOLVER --> VALIDATOR
    SOLVER --> MODELS
    SOLVER --> ORTOOLS

    CLI[cli.py] --> SOLVER
    CLI --> VALIDATOR
    CLI --> FORMATTER
    CLI --> MODELS

    BENCH[benchmark.py] --> SOLVER
    BENCH --> MODELS
```

Reading the graph bottom-up: the generators produce input data; `preprocessing` and `cost_calculator` prepare validated units and integer costs from `models` objects; `cp_sat_model` turns them into a CP-SAT model; `solver` orchestrates everything and hands results to `result_formatter` and `validator`; `cli` and `benchmark` are the two entry points on top.
