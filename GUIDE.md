# PJ Kwan Inn Teng CP-SAT Seat Allocation Prototype Guide

## Goal

Build an executable Python prototype using Google OR-Tools CP-SAT to allocate participants to seats for the PJ Kwan Inn Teng Final Year Project case study.

The implementation must convert all seating rules into a mathematical model, generate deterministic mock data for 100 primary participants, create a 10-row by 12-seat floor plan, apply all listed hard and soft constraints, measure solver performance, and return the result as valid frontend-friendly JSON.

The frontend reference is:

`https://buddy-prototype-three.vercel.app/seat`

Use the page only as a visual and output-contract reference. Do not create a runtime dependency on it.

---

## 1. Required Technology

Use:

- Python 3.11 or newer
- Google OR-Tools CP-SAT
- Pydantic or Python dataclasses
- pytest
- `time.perf_counter` for elapsed-time measurement
- Optional `psutil` for process memory
- JSON and JSON Schema
- Type hints and docstrings
- Deterministic random seed `20260707`

All CP-SAT variables, coefficients, costs, and weights must be integers.

---

## 2. Recommended Project Structure

```text
seat-allocation-solver/
├── pyproject.toml
├── requirements.txt
├── README.md
├── CLAUDE.md
├── GUIDE.md
├── config/
│   └── solver_config.json
├── data/
│   ├── mock_participants.json
│   ├── floor_plan.json
│   └── previous_allocation.json
├── docs/
│   └── mathematical_model.json
├── schemas/
│   ├── participant.schema.json
│   ├── floor_plan.schema.json
│   ├── solver_config.schema.json
│   └── solver_result.schema.json
├── src/
│   └── seat_solver/
│       ├── __init__.py
│       ├── models.py
│       ├── data_generator.py
│       ├── floor_plan_generator.py
│       ├── preprocessing.py
│       ├── cost_calculator.py
│       ├── cp_sat_model.py
│       ├── solver.py
│       ├── result_formatter.py
│       ├── validator.py
│       ├── benchmark.py
│       └── cli.py
├── tests/
│   ├── test_data_generation.py
│   ├── test_floor_plan.py
│   ├── test_hard_constraints.py
│   ├── test_soft_constraints.py
│   ├── test_solver_status.py
│   ├── test_json_schema.py
│   └── test_regeneration.py
└── output/
    ├── seat_allocation_result.json
    ├── performance_report.json
    └── validation_report.json
```

The exact structure may be adapted to the repository, but the responsibilities must remain separated.

---

## 3. Contribution Tiers

The three contribution tiers are:

| Tier | Contribution | Seat Demand | Required Row Zone |
|---|---:|---:|---|
| Emperor | RM2,000 and above | 2 seats | Rows 1–2 |
| Bodhi | RM1,000–RM1,999 | 1 seat | Rows 3–5 |
| Merit | RM500–RM999 | 1 seat | Rows 6–10 |

Store the row boundaries in `solver_config.json`.

Use integer ringgit or integer sen values. Do not use floating-point values for money.

---

## 4. Mock Participant Data

Generate exactly 100 synthetic primary participant records:

- 8 Emperor
- 32 Bodhi
- 60 Merit

Seat demand:

- Emperor: `8 × 2 = 16`
- Bodhi: `32 × 1 = 32`
- Merit: `60 × 1 = 60`
- Total occupied seats: `108`
- Total empty seats: `12`

An Emperor adjacent guest does not count as an additional primary participant record.

Of the eight Emperor participants:

- Four contain a non-null `adjacent_person_name`.
- Four contain `adjacent_person_name: null`.
- When the adjacent name is null, both seats display the primary participant's name.
- When the adjacent name exists, one seat displays the primary participant and the second displays the adjacent guest.

Every primary participant record should include:

```json
{
  "participant_id": "P001",
  "full_name": "Synthetic Name",
  "is_synthetic": true,
  "contribution_amount_rm": 2500,
  "contribution_tier": "EMPEROR",
  "age": 68,
  "is_elderly": true,
  "is_monk": false,
  "requires_accessible_seat": false,
  "participant_category": "COMMITTEE",
  "category_importance": 3,
  "events_joined_last_2_years": 14,
  "adjacent_person_name": "Synthetic Guest Name",
  "previous_seat_ids": ["R01-S07", "R01-S08"]
}
```

Participant categories should include:

- `MONASTIC`
- `COMMITTEE`
- `VOLUNTEER`
- `GENERAL_DEVOTEE`

Dataset diversity requirements:

- At least 8 monks
- At least 20 elderly participants aged 60 or above
- At least 5 participants requiring accessible seating
- Event counts ranging from 0 to at least 20
- Approximately 70% of participants with valid previous assignments
- No duplicate physical seats in the previous assignment data

Use synthetic Malaysian-style names only.

---

## 5. Floor Plan

Create:

- 10 rows
- 12 physical seats per row
- 120 total seats
- One centre aisle between physical positions 6 and 7

Seat IDs:

```text
R01-S01
R01-S02
...
R10-S12
```

Every row uses the following left-to-right priority pattern:

```text
Physical position:
 1   2   3   4   5   6      7   8   9   10  11  12

Priority rank:
12  10   8   6   4   2      1   3   5    7   9  11
```

Priority rank 1 is the best seat.

Each seat should contain:

```json
{
  "seat_id": "R01-S07",
  "row_number": 1,
  "row_index": 0,
  "physical_position": 7,
  "priority_rank": 1,
  "side": "RIGHT",
  "zone": "RIGHT_CENTER",
  "tier_zone": "EMPEROR",
  "is_accessible": false,
  "is_blocked": false
}
```

Use spatial zones:

- `RIGHT_CENTER`
- `LEFT_CENTER`
- `RIGHT_OUTER`
- `LEFT_OUTER`

The right side is more important than the equivalent left-side position.

Support accessible and blocked seats.

---

## 6. Emperor Pair Rules

Every Emperor registration requires exactly two seats.

The only valid adjacent pairs are:

| Physical Positions | Pair Priority |
|---|---:|
| 1–2 | 6 |
| 3–4 | 4 |
| 5–6 | 2 |
| 7–8 | 1 |
| 9–10 | 3 |
| 11–12 | 5 |

Visual representation:

```text
[6][6] [4][4] [2][2]    [1][1] [3][3] [5][5]
```

Positions 6 and 7 must never form a pair because of the centre aisle.

Represent each Emperor registration as one two-seat allocation unit and use pair-assignment Boolean variables.

---

## 7. Mathematical Model

Create `docs/mathematical_model.json`.

The file must document:

- Sets
- Indices
- Input parameters
- Decision variables
- Hard constraints
- Soft constraints
- Objective function
- Assumptions
- Boundary conditions
- Integer scaling
- Expected solver statuses

Use these sets:

- `P`: single-seat participants, consisting of Bodhi and Merit participants
- `E`: Emperor allocation units
- `S`: physical seats
- `K`: valid Emperor pairs
- `R`: rows
- `T`: contribution tiers
- `Z`: seating zones

Decision variables:

```text
x[p,s] = 1 if single-seat participant p is assigned to seat s, otherwise 0

y[e,k] = 1 if Emperor allocation e is assigned to pair k, otherwise 0
```

Optional row expressions:

```text
row[p] = assigned row for single-seat participant p
row[e] = assigned row for Emperor allocation e
```

---

## 8. Hard Constraints

### HC1 — Every single-seat participant is assigned exactly once

For every `p ∈ P`:

```text
Σ(s ∈ EligibleSeats[p]) x[p,s] = 1
```

### HC2 — Every Emperor allocation is assigned exactly one valid pair

For every `e ∈ E`:

```text
Σ(k ∈ EligiblePairs[e]) y[e,k] = 1
```

### HC3 — Every physical seat has at most one occupant

For every seat `s`:

```text
Σ(p) x[p,s] + Σ(e,k where s belongs to k) y[e,k] ≤ 1
```

### HC4 — Tier row-zone eligibility

- Emperor variables are created only for rows 1–2.
- Bodhi variables are created only for rows 3–5.
- Merit variables are created only for rows 6–10.

Do not create invalid participant-seat variables.

### HC5 — Contribution ordering inside each tier

For participants or allocation units `i` and `j` in the same tier:

```text
If contribution[i] > contribution[j], then row[i] ≤ row[j]
```

Participants with equal contribution do not require ordering.

### HC6 — Emperor adjacency

Every Emperor allocation must use one predefined valid pair.

### HC7 — No centre-aisle crossing

Positions 6 and 7 must never form a pair.

### HC8 — Accessibility

A participant requiring accessibility must use an accessibility-compatible seat or pair.

### HC9 — Blocked seats

A blocked seat must never be assigned.

### HC10 — Unique primary allocation

A primary participant must not appear in more than one unrelated allocation unit.

### HC11 — Capacity validation

Before model construction:

```text
2 × Emperor count + Bodhi count + Merit count
≤ available seat count
```

Also validate each tier's row-zone capacity.

### HC12 — Integer-only model

All CP-SAT variables, costs, weights, and expressions must be integer-based.

---

## 9. Soft Constraints

All soft constraints must be represented as precomputed integer assignment costs.

Default weights:

```json
{
  "priority_seat_weight": 40,
  "category_zone_weight": 25,
  "movement_weight": 20,
  "activeness_weight": 15
}
```

Each weight must be an integer between 0 and 100.

### SC1 — Priority-seat mismatch

Suggested desired priority:

- Accessibility requirement: rank 1
- Monk: rank 1
- Elderly: rank 3
- General participant: rank 8

Where more than one rule applies, use the highest priority.

For a single seat:

```text
priority_cost[p,s]
= abs(desired_priority_rank[p] - priority_rank[s])
```

For an Emperor allocation, compare the participant's desired rank with pair priority.

### SC2 — Category-zone mismatch

Use a configurable cost matrix:

```json
{
  "MONASTIC": {
    "RIGHT_CENTER": 0,
    "LEFT_CENTER": 2,
    "RIGHT_OUTER": 4,
    "LEFT_OUTER": 8
  },
  "COMMITTEE": {
    "RIGHT_CENTER": 0,
    "LEFT_CENTER": 2,
    "RIGHT_OUTER": 3,
    "LEFT_OUTER": 6
  },
  "VOLUNTEER": {
    "RIGHT_CENTER": 1,
    "LEFT_CENTER": 2,
    "RIGHT_OUTER": 1,
    "LEFT_OUTER": 3
  },
  "GENERAL_DEVOTEE": {
    "RIGHT_CENTER": 2,
    "LEFT_CENTER": 2,
    "RIGHT_OUTER": 0,
    "LEFT_OUTER": 1
  }
}
```

Store the matrix in `solver_config.json`.

### SC3 — Movement after regeneration

For a participant with a previous seat:

```text
movement_cost[p,s] = 0
when s is the previous seat
```

Otherwise:

```text
movement_cost[p,s]
= fixed_move_penalty
+ row_distance_weight × abs(previous_row[p] - row[s])
+ column_distance_weight × abs(previous_position[p] - physical_position[s])
```

Suggested configuration:

```json
{
  "fixed_move_penalty": 20,
  "row_distance_weight": 12,
  "column_distance_weight": 1
}
```

For Emperor allocations:

- Same previous pair: zero cost
- Same row, different pair: moderate cost
- Different row: larger cost

When no previous assignment exists, movement cost is zero.

### SC4 — Activeness mismatch

Use `events_joined_last_2_years`.

Convert activeness into a target rank from 1 to 12:

```text
activity_target_rank[p]
= 1 + round(
    11 ×
    (max_activity - activity[p])
    / max(1, max_activity - min_activity)
  )
```

Then:

```text
activeness_cost[p,s]
= abs(activity_target_rank[p] - priority_rank[s])
```

For Emperor allocations, use pair priority.

---

## 10. Objective Function

Minimize:

```text
Priority-seat mismatch
+ Category-zone mismatch
+ Movement after regeneration
+ Activeness mismatch
```

Single-seat objective:

```text
Z_single =
Σ(p,s) x[p,s] × (
    W_priority × C_priority[p,s]
  + W_zone × C_zone[p,s]
  + W_movement × C_movement[p,s]
  + W_activeness × C_activeness[p,s]
)
```

Emperor objective:

```text
Z_emperor =
Σ(e,k) y[e,k] × (
    W_priority × C_priority_pair[e,k]
  + W_zone × C_zone_pair[e,k]
  + W_movement × C_movement_pair[e,k]
  + W_activeness × C_activeness_pair[e,k]
)
```

Total:

```text
Z = Z_single + Z_emperor + TieBreakPenalty
```

Use deterministic tie-breaking:

```text
FinalObjective =
MAIN_OBJECTIVE_SCALE × MainPenalty
+ TieBreakPenalty
```

Prove that the tie-break term cannot override a difference in the main penalty.

---

## 11. Solver Function

Create a reusable function similar to:

```python
def solve_seat_allocation(
    participants: list[Participant],
    floor_plan: FloorPlan,
    config: SolverConfig,
    previous_allocation: PreviousAllocation | None = None,
) -> SolverResult:
    ...
```

The function must:

1. Validate input.
2. Convert Emperor records into two-seat allocation units.
3. Precompute eligible single-seat assignments.
4. Precompute valid Emperor pairs.
5. Precompute integer cost matrices.
6. Create the CP-SAT model.
7. Add all hard constraints.
8. Add the weighted objective.
9. Configure and run `CpSolver`.
10. Check the status.
11. Accept a successful result only when the status is `OPTIMAL`.
12. Extract every assignment.
13. Calculate the penalty breakdown.
14. Independently validate the extracted solution.
15. Return a serializable result.

Suggested solver configuration:

```json
{
  "require_optimal": true,
  "max_time_seconds": 300,
  "num_search_workers": 8,
  "random_seed": 20260707,
  "log_search_progress": false
}
```

Status handling:

- `OPTIMAL`: write the successful result.
- `FEASIBLE`: do not report it as optimal.
- `FEASIBLE` with `require_optimal: true`: return `OPTIMAL_NOT_PROVEN`.
- `INFEASIBLE`: return a structured error.
- `MODEL_INVALID`: return a structured error.
- `UNKNOWN`: return a structured error.

The default dataset must be designed so that the prototype reaches `OPTIMAL`.

---

## 12. Main Output JSON

Write:

`output/seat_allocation_result.json`

Recommended structure:

```json
{
  "schema_version": "1.0.0",
  "run_id": "RUN-...",
  "generated_at": "ISO-8601 timestamp",
  "case_study": "PJ Kwan Inn Teng",
  "status": "success",
  "input_summary": {
    "primary_participant_count": 100,
    "emperor_count": 8,
    "bodhi_count": 32,
    "merit_count": 60,
    "required_seat_count": 108,
    "total_seat_count": 120,
    "empty_seat_count": 12
  },
  "weights": {
    "priority_seat_weight": 40,
    "category_zone_weight": 25,
    "movement_weight": 20,
    "activeness_weight": 15
  },
  "solver": {
    "engine": "Google OR-Tools CP-SAT",
    "status": "OPTIMAL",
    "objective_value": 0,
    "best_objective_bound": 0,
    "optimality_gap": 0,
    "wall_time_seconds": 0.0,
    "user_time_seconds": 0.0,
    "num_conflicts": 0,
    "num_branches": 0,
    "response_stats": ""
  },
  "penalty_summary": {
    "unweighted": {
      "priority_seat": 0,
      "category_zone": 0,
      "movement": 0,
      "activeness": 0
    },
    "weighted": {
      "priority_seat": 0,
      "category_zone": 0,
      "movement": 0,
      "activeness": 0,
      "tie_break": 0,
      "total": 0
    }
  },
  "floor_plan": {
    "row_count": 10,
    "seats_per_row": 12,
    "total_seats": 120,
    "aisle_after_position": 6,
    "rows": []
  },
  "assignments": [],
  "empty_seat_ids": [],
  "unassigned_participants": [],
  "hard_constraint_validation": {
    "all_constraints_satisfied": true,
    "duplicate_seat_count": 0,
    "unassigned_count": 0,
    "tier_zone_violation_count": 0,
    "contribution_order_violation_count": 0,
    "emperor_adjacency_violation_count": 0,
    "aisle_crossing_violation_count": 0,
    "accessibility_violation_count": 0,
    "blocked_seat_violation_count": 0
  }
}
```

Every numeric field must use the actual executed result.

Do not leave fake placeholder metrics.

---

## 13. Error JSON

Use structured errors:

```json
{
  "schema_version": "1.0.0",
  "status": "error",
  "error": {
    "code": "OPTIMAL_NOT_PROVEN",
    "message": "CP-SAT returned FEASIBLE, but require_optimal is enabled.",
    "solver_status": "FEASIBLE",
    "details": {}
  },
  "solver": {
    "wall_time_seconds": 300.0,
    "objective_value": 12345,
    "best_objective_bound": 12000
  }
}
```

Supported error codes:

- `INVALID_INPUT`
- `CAPACITY_EXCEEDED`
- `TIER_CAPACITY_EXCEEDED`
- `MODEL_INVALID`
- `INFEASIBLE`
- `OPTIMAL_NOT_PROVEN`
- `SOLVER_UNKNOWN`
- `OUTPUT_VALIDATION_FAILED`

---

## 14. Performance Tracking

Include in every result:

- Solver status
- Objective value
- Best objective bound
- Optimality gap
- Wall-clock time
- User time where available
- Conflicts
- Branches
- Solver response statistics
- Peak or approximate memory
- Boolean variable count
- Integer variable count
- Constraint count
- Eligible participant-seat combination count
- Eligible Emperor-pair combination count

Use `time.perf_counter()` for external elapsed time.

Create:

`output/performance_report.json`

Benchmark the deterministic scenario for ten runs and report:

- Successful optimal runs
- Failed runs
- Minimum time
- Maximum time
- Mean time
- Median time
- P95 time
- Objective values
- Best bounds
- Conflicts
- Branches
- Peak RSS memory
- Per-run statistics

---

## 15. Independent Validation

After result extraction, verify:

1. Exactly 100 primary participants were processed.
2. Exactly 108 physical seats are occupied.
3. Exactly 12 seats are empty.
4. No seat is duplicated.
5. Every Bodhi participant has one seat.
6. Every Merit participant has one seat.
7. Every Emperor allocation has exactly two seats.
8. Every Emperor pair is adjacent.
9. No Emperor pair crosses the aisle.
10. Emperor participants are in rows 1–2.
11. Bodhi participants are in rows 3–5.
12. Merit participants are in rows 6–10.
13. Contribution ordering is correct inside each tier.
14. Accessibility is satisfied.
15. Blocked seats are unused.
16. Penalty totals are correct.
17. The reconstructed weighted objective matches the solver objective.
18. The result conforms to `solver_result.schema.json`.
19. Solver status is `OPTIMAL`.
20. Optimality gap equals zero.

Write the report to:

`output/validation_report.json`

---

## 16. Required Tests

Implement at least the following tests:

1. Exactly 100 primary records are generated.
2. Tier distribution is 8 Emperor, 32 Bodhi, and 60 Merit.
3. Seat demand is 108.
4. The floor plan has 10 rows and 120 unique seats.
5. Every row uses `[12, 10, 8, 6, 4, 2, 1, 3, 5, 7, 9, 11]`.
6. The centre aisle is after physical position 6.
7. Every Emperor receives exactly two approved adjacent seats.
8. No Emperor pair uses positions 6 and 7.
9. No seat is duplicated.
10. All tier-zone constraints pass.
11. Contribution ordering passes.
12. Accessibility passes.
13. Zero soft weights do not break hard constraints.
14. Higher movement weight reduces or preserves movement.
15. Higher priority weight improves or preserves priority mismatch.
16. Identical regeneration input preserves previous seats where possible.
17. The default status is `OPTIMAL`.
18. The output passes JSON Schema validation.
19. Impossible tier capacity returns a structured error.
20. Emperor without an adjacent name displays the primary name on both seats.
21. Emperor with an adjacent name displays the two names correctly.

---

## 17. CLI Commands

Generate participants:

```bash
python -m seat_solver.data_generator   --count 100   --seed 20260707   --output data/mock_participants.json
```

Generate floor plan:

```bash
python -m seat_solver.floor_plan_generator   --rows 10   --seats-per-row 12   --output data/floor_plan.json
```

Run solver:

```bash
python -m seat_solver.cli solve   --participants data/mock_participants.json   --floor-plan data/floor_plan.json   --previous-allocation data/previous_allocation.json   --config config/solver_config.json   --output output/seat_allocation_result.json
```

Validate:

```bash
python -m seat_solver.cli validate   --result output/seat_allocation_result.json   --output output/validation_report.json
```

Benchmark:

```bash
python -m seat_solver.benchmark   --runs 10   --output output/performance_report.json
```

Run tests:

```bash
pytest -q
```

---

## 18. Implementation Order

1. Inspect the repository and the reference seat page where possible.
2. Create the project structure and dependency files.
3. Create `docs/mathematical_model.json`.
4. Create `solver_config.json` and JSON Schemas.
5. Implement the deterministic participant generator.
6. Implement the floor-plan generator.
7. Implement validation.
8. Implement Emperor allocation preprocessing.
9. Implement cost matrices.
10. Implement the CP-SAT model.
11. Implement result extraction.
12. Implement independent validation.
13. Run the solver and reach `OPTIMAL`.
14. Generate the main result JSON.
15. Run all tests and fix failures.
16. Run the ten-run benchmark.
17. Confirm all outputs are schema-valid and frontend-friendly.

Do not stop after writing code. Execute the prototype.

---

## 19. Acceptance Criteria

The prototype is complete only when:

- Exactly 100 primary participants exist.
- Exactly 120 unique physical seats exist.
- Exactly 108 seats are occupied.
- Exactly 12 seats are empty.
- Every hard constraint passes.
- The default run returns `OPTIMAL`.
- Optimality gap is zero.
- The output JSON is valid.
- Every assignment has a penalty breakdown.
- Every Emperor allocation has exactly two adjacent seats.
- The performance benchmark is executed.
- All tests pass.
- The output can be rendered by the target frontend.
- No unresolved placeholder, TODO, fake metric, or unexecuted code remains.

---

## 20. Final Claude Code Response

After implementation, Claude Code should return one valid JSON object only:

```json
{
  "status": "completed",
  "project_path": "relative/path",
  "files_created": [],
  "files_modified": [],
  "commands_executed": [],
  "solver_result": {
    "status": "OPTIMAL",
    "objective_value": 0,
    "best_objective_bound": 0,
    "optimality_gap": 0,
    "wall_time_seconds": 0.0
  },
  "dataset_summary": {
    "primary_participants": 100,
    "emperor": 8,
    "bodhi": 32,
    "merit": 60,
    "occupied_seats": 108,
    "empty_seats": 12
  },
  "test_summary": {
    "passed": 0,
    "failed": 0
  },
  "benchmark_summary": {
    "runs": 10,
    "optimal_runs": 10,
    "mean_wall_time_seconds": 0.0,
    "p95_wall_time_seconds": 0.0
  },
  "output_files": {
    "mathematical_model": "docs/mathematical_model.json",
    "participants": "data/mock_participants.json",
    "floor_plan": "data/floor_plan.json",
    "allocation_result": "output/seat_allocation_result.json",
    "validation_report": "output/validation_report.json",
    "performance_report": "output/performance_report.json"
  },
  "assumptions": [],
  "known_limitations": []
}
```

Replace every placeholder with the actual result.
