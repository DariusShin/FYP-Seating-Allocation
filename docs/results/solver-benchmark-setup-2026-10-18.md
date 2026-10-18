# Solver-selection benchmark setup and development validation

Date: 18 October 2026, Asia/Kuala_Lumpur.

Status: **experiment setup implemented and development checks completed; main dissertation experiment not run**. Implementation and retained development evidence are grouped into separate conventional commits on `codex/experiment-workspace-setup`.

## How to run and find results

Use the [experiment README](../../research/experiments/solver_benchmark/README.md) for environment setup, optional preflight/pilot commands, the full `run` command and report regeneration. The [experiments index](../../research/experiments/README.md) distinguishes this solver study from the separate weighting study and the older sensitivity harness.

The first experiment compares the maintained CP-SAT builder, an independently formulated SCIP MIP, and deterministic constraint-aware greedy using shared inputs, compact current-ratio coefficients, placement validation and reference scoring. Its frozen workload is 156 primary five-second runs, 72 additional 30/60-second runs and four separate prototype checks, under a 90-minute overall runner ceiling. Full execution remains a deliberate later step; a previous pilot cannot bypass the main command's fresh gates.

For a main run, the chosen `--out` directory will contain `results.md`, `summary.json`, raw maps/measurements in `runs/`, five CSV tables in `tables/`, and four figures in `figures/`, each exported as PNG/PDF/SVG. Pilot diagnostic tables are under `pilot/` and are excluded from main analyses.

## Implementation checks

The implementation test command completed with **12 tests passed**, with three OR-Tools SWIG deprecation warnings. It covers:

- Exhaustive physical-assignment oracles: nine tiny cases × four preference configurations × three methods = 108 method checks, including 72 exact-solver checks. Both exact solvers must match the oracle objective or prove the deliberately infeasible cases infeasible.
- Feasibility witnesses and the complete deterministic 232-job schedule, including the registration-based 230-seat case.
- Shared weights, independent placement-audit rejection of tampered maps, greedy independence from exact solvers and correct failure semantics.
- Process-group watchdog/atomic records, frozen-input tampering detection, and report handling of missing pairs, unexecuted budgets and pilot-only diagnostics.
- PDF/SVG/PNG rendering on an explicitly unexecuted unit-test fixture, preserving missing observations rather than inventing measurements. This renderer fixture is not a main-study result figure.

The [retained input-certification bundle](solver-benchmark-plan-2026-10-18/manifest.json) completed in plan mode. It certified **13 events**, independently audited every feasibility witness and checked **32,456 legal-option score vectors** against the maintained production scorer. Its [inventory](solver-benchmark-plan-2026-10-18/inventory.json) records hashes and counts. Every main job is `not_started`; its generated [coverage report](solver-benchmark-plan-2026-10-18/results.md) contains no measured algorithm outcomes.

The Emperor-heavy event has **99 Emperor registrations, 19 Merit and 13 Bodhi**, totaling 131 registrations and **230 physical seats**. Emperor registrations are approximately 75.57% of registrations; their entitlement is two seats each. This is distinct from the three full 232-seat event patterns.

## Retained development pilots

Both pilots use separate development inputs and the predeclared 19-job development schedule: 18 comparative runs and one prototype check. They are excluded from H1/RQ1/H3 and cannot establish a main-study winner or attendee satisfaction.

| Pilot | Completed jobs | Comparative exact-solver valid maps | Greedy outcomes | Prototype | Actual runner elapsed | Conservative main-workload projection |
|---|---:|---:|---|---|---:|---:|
| [First pilot](solver-benchmark-development-2026-10-18/manifest.json) | 19/19 | 12/12 | 6 construction failures | Valid map | 250.94 s | 113.26 min; exceeds ceiling |
| [Updated pilot](solver-benchmark-development-2026-10-18-v2/manifest.json) | 19/19 | 12/12 | 6 construction failures | Valid map | 216.51 s | 88.08 min; within ceiling |

The first pilot's [projection](solver-benchmark-development-2026-10-18/pilot/projection.json) is retained unchanged. Development identified repeated policy-file reads during common preprocessing. The updated implementation compiles the same components using a pure Decimal reference formula, checks every compiled option against the production scorer during preflight, and rescores selected maps with both formulas. The new pilot also verifies input hashes, records per-trial memory and uses the source fixture's actual default prototype settings. Each pilot preserves its own source snapshot; the two are development iterations, not matched timing repetitions for estimating an algorithm speedup.

The updated pilot's [diagnostic report](solver-benchmark-development-2026-10-18-v2/pilot/results.md), [CSV table](solver-benchmark-development-2026-10-18-v2/pilot/tables/run-records.csv), [summary](solver-benchmark-development-2026-10-18-v2/pilot/summary.json) and [projection](solver-benchmark-development-2026-10-18-v2/pilot/projection.json) are generated from its saved JSON records. Thirteen of 19 jobs returned validated maps: 12 exact-solver comparative jobs and one separately configured prototype job. Greedy construction failures remain unsuccessful outcomes, with no invented objective score or infeasibility certificate.

In that updated pilot, the prototype retained its actual 60-second allowance, eight workers, seed `20260918` and canonicalization enabled. It returned a valid map in **60.90 seconds through parsed service output**, or **61.03 seconds including the separate research audit/persistence**. This verifies the measurement boundary and illustrates why a 60-second solving allowance does not promise a 60-second complete service response. It does not establish that 60 seconds is necessary or sufficient across the four main prototype cases.

The largest recorded trial-worker lifetime peak was **259.03 MiB**, including imports/model/audit. Prototype child memory is reported separately and is not added to the parent peak. These development observations do not establish full-machine memory sufficiency or final per-method resource rankings.

## Readiness and limitations

The updated standalone pilot projects approximately **88.08 minutes**, leaving limited room under the agreed 90-minute ceiling. Its estimate is a projection, not an observed complete-study duration. A full `run` includes certification of all 13 main events as well as its own correctness checks and fresh pilot; it must recompute fit on the actual machine before launching main runs. It preserves the declared workload and stops with diagnostics if the projection does not fit. No cases or budgets were removed to force this development pilot to pass.

Use the intended local M4/24 GB Mac with stable power settings and no competing heavy workloads for the main study. The recorded development environment is macOS/arm64, OR-Tools **9.15.6755**, SCIP **10.0.0**, SoPlex **8.0.0**. Hardware `sysctl` fields were unavailable inside the development sandbox and are explicitly marked unavailable in the manifests; M4/24 GB remains the user-supplied machine description. Actual package versions and sources are retained in each bundle.

No main-run result plots or hypothesis conclusions have been produced. The weighting runner and its 120-minute study remain separate future implementation/execution work. Production policy and solver code were not changed by this setup.
