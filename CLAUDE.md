# Project Overview

A Python prototype that uses Google OR-Tools CP-SAT to generate an optimized, constraint-compliant seating allocation for the PJ Kwan Inn Teng FYP case study.

# Tech Stack

- **Language:** Python 3.11+
- **Optimization Engine:** Google OR-Tools CP-SAT
- **Validation and Models:** Pydantic or Python dataclasses
- **Testing:** pytest
- **Performance Tracking:** `time.perf_counter`, OR-Tools solver statistics, and optional `psutil`
- **Data Exchange:** JSON and JSON Schema
- **Documentation:** Markdown and JSON-based mathematical model documentation
- **Frontend Integration Target:** JSON output compatible with the Buddy seat-map prototype
- **Package Management:** `pip`, `venv`, and optionally `pyproject.toml`

# Key Commands

Create and activate the virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate deterministic mock participants:

```bash
python -m seat_solver.data_generator \
  --count 150 \
  --seed 20260707 \
  --output data/mock_participants.json
```

Generate the 16-row, 16-seat floor plan (includes the structural blocked centre block):

```bash
python -m seat_solver.floor_plan_generator \
  --rows 16 \
  --seats-per-row 16 \
  --output data/floor_plan.json
```

Run the solver:

```bash
python -m seat_solver.cli solve \
  --participants data/mock_participants.json \
  --floor-plan data/floor_plan.json \
  --previous-allocation data/previous_allocation.json \
  --config config/solver_config.json \
  --output output/seat_allocation_result.json
```

Validate the generated solution:

```bash
python -m seat_solver.cli validate \
  --result output/seat_allocation_result.json \
  --output output/validation_report.json
```

Run the benchmark:

```bash
python -m seat_solver.benchmark \
  --participants data/mock_participants.json \
  --floor-plan data/floor_plan.json \
  --config config/solver_config.json \
  --runs 10 \
  --output output/performance_report.json
```

Run all tests:

```bash
pytest -q
```

Run one test module:

```bash
pytest -q tests/test_hard_constraints.py
```

Run formatting and linting when configured:

```bash
ruff check .
ruff format --check .
```

Apply formatting:

```bash
ruff format .
```

# Code Conventions

- Use Python 3.11 or newer and add type hints to all public functions and data models.
- Keep CP-SAT variables, coefficients, penalty values, weights, and objective terms as integers.
- Do not pass floating-point values into the CP-SAT model.
- Name Python modules and functions in `snake_case`.
- Name classes and Pydantic models in `PascalCase`.
- Name constants in `UPPER_SNAKE_CASE`.
- Use descriptive identifiers such as `participant_id`, `seat_id`, `row_number`, and `priority_rank`.
- Keep physical seat position separate from seat-priority rank.
- Use zero-based indexes internally and one-based row and seat numbers in user-facing JSON.
- Represent Emperor registrations as two-seat allocation units using valid pair variables.
- Do not model Emperor seats as two unrelated single-seat assignments.
- Create CP-SAT variables only for eligible participant-seat or Emperor-pair combinations.
- Keep validation, preprocessing, cost calculation, model construction, solving, result formatting, and benchmarking in separate modules.
- Store configurable tier boundaries, weights, category-zone costs, movement costs, and solver parameters in `solver_config.json`.
- Use deterministic seeds for mock data and solver runs.
- Return structured JSON errors rather than uncaught exceptions for expected invalid-input and solver-status cases.
- Never report a solution as optimal unless CP-SAT returns `OPTIMAL`.
- Independently validate the extracted solution after solving.
- Include a penalty breakdown for every allocation and a total penalty summary.
- Ensure every output file conforms to its JSON Schema before it is accepted.
- Add or update tests whenever a constraint, objective term, schema, or result field changes.
- Keep functions focused and avoid creating one large function that performs validation, modelling, solving, and output formatting together.
- Add docstrings that explain the mathematical meaning of non-obvious solver functions.

# Gotchas

- CP-SAT does not accept floating-point objective coefficients. Scale or convert every cost to an integer before model creation.
- Physical adjacency must use `physical_position`, not `priority_rank`.
- The hall is 16 rows × 16 seats (256 seats). Positions 8 and 9 are separated by the centre aisle and must never form an Emperor pair.
- The hall carries a structural blocked centre block (24 seats, from the real 2023/2024 PJKIT layouts): rows 6 and 8 block positions 5–12; rows 7 and 9 block positions 5–6 and 11–12. Assignable capacity is 232 seats.
- Pair seating is exclusive to the Emperor tier. The valid Emperor pair priorities (centre-out, east side first) are:
  - Positions 9–10: priority 1
  - Positions 7–8: priority 2
  - Positions 11–12: priority 3
  - Positions 5–6: priority 4
  - Positions 13–14: priority 5
  - Positions 3–4: priority 6
  - Positions 15–16: priority 7
  - Positions 1–2: priority 8
- The default scenario contains exactly 150 participants: 112 Emperor, 22 Merit, and 16 Bodhi.
- Emperor participants attend as couples, so the 112 Emperor participants form 56 two-seat registrations. The model therefore has 94 allocation units in total (56 Emperor pairs + 22 Merit + 16 Bodhi), and only 56 Emperor names appear on the seat map even though 112 Emperor seats are occupied.
- With 112 Emperor (56 pairs), 22 Merit, and 16 Bodhi participants, the expected occupied-seat count is 150 and the empty (assignable) seat count is 82.
- Distinguish three counts and never conflate them: participants (150 people), allocation units (94 solver decision units), and occupied seats (150).
- An Emperor adjacent guest is not counted as another primary participant record.
- When an Emperor participant has no adjacent guest name, both assigned seats display the primary participant's name (the merged-cell convention of the real layouts); a provided guest name appears on the second seat of the pair.
- Tier bands are demand-derived, NOT fixed venue zones: tiers occupy contiguous row blocks ordered Emperor → Merit → Bodhi from the front of the hall, with boundaries computed from each event's tier demand before model construction. The order follows the contribution thresholds elicited from PJKIT (Emperor from RM5000, Merit from RM3000, Bodhi from RM2000).
- A boundary row MAY be shared between two adjacent tiers: when one tier's demand ends partway along a row, the next tier continues in the same row so that the numbered section packs with no empty seat. Rows are NOT tier-exclusive.
- For the default 112/22/16 scenario the computed bands are: Emperor rows 1–9 (4 of row 9's 12 assignable seats), Merit rows 9–10 (14 of row 10), Bodhi rows 10–11 (14 of row 11). Rows 9 and 10 are shared boundary rows. The 82 remaining assignable seats across rows 11–16 form the free-seating section and are not solver-allocated.
- The hall is divided into a numbered section, which the solver allocates, and a free-seating section at the back, which it does not. The numbered section is exactly as large as total seat demand, because the numbered section packs with no empty seat.
- Numbered seats fill front to back with no empty seat, and each side of a row fills outward from the centre aisle, so no gap may appear between the aisle and an outer occupied seat.
- A participant requiring an accessible seat is placed at a side/edge seat of the hall; for an Emperor unit, this means a pair at the side.
- Band packing feasibility (and per-band accessible capacity) must be checked before model construction.
- Higher contribution within the same tier must not be assigned to a later row than a lower contribution.
- Soft-constraint weights must never override hard constraints.
- Movement penalties should be zero when no previous allocation is available.
- A `FEASIBLE` result is not the same as `OPTIMAL`. When `require_optimal` is enabled, return `OPTIMAL_NOT_PROVEN` instead of accepting it.
- Deterministic tie-breaking is required to reduce unnecessary layout changes between equivalent solutions.
- The tie-break term must be scaled so that it cannot overpower the main weighted penalty.
- Do not leave placeholder metrics in JSON output. Every metric must come from the actual executed solver or benchmark.
- Do not serialize OR-Tools objects, sets, tuples, or enums directly into JSON.
- The output JSON must remain frontend-friendly even when the solver returns an error.
- Always independently verify duplicate seats, adjacency, aisle crossing, tier placement, contribution ordering, accessibility, blocked seats, and reconstructed objective value.

# Current Focus

Prioritize building and validating the first executable CP-SAT prototype for the default 150-participant scenario (112 Emperor forming 56 pairs / 22 Merit / 16 Bodhi, giving 94 allocation units and 150 occupied seats).

The immediate work order is:

1. Create `docs/mathematical_model.json`.
2. Create `config/solver_config.json` and the required JSON Schemas.
3. Generate exactly 150 deterministic synthetic participant profiles (112 Emperor / 22 Merit / 16 Bodhi), pairing the Emperor records into 56 two-seat registrations.
4. Generate the 16 × 16 floor plan with the required priority pattern and blocked centre block.
5. Implement input validation and tier-capacity validation.
6. Convert Emperor records into two-seat allocation units.
7. Implement all hard constraints.
8. Implement the four weighted soft constraints.
9. Add deterministic tie-breaking.
10. Solve the default dataset and require an `OPTIMAL` result.
11. Generate frontend-ready JSON output.
12. Independently validate the extracted solution.
13. Run the full pytest suite.
14. Execute the ten-run benchmark and save the performance report.

Do not prioritize frontend development, visual redesign, authentication, database integration, cloud deployment, or unrelated application modules until the solver prototype, tests, validation report, and benchmark are complete.
