# Solver benchmark scope amendment: 20 October 2026

Status: **confirmed by the user through Q6 A; executable amendment implemented and implementation tests passed on Windows 11; fresh pilot and main execution pending**. This closes the occupancy-extension GrillMe session. Question numbers below belong to this session, separately from the earlier Q1–Q13 solver-design audit.

The executable harness implemented the target below under protocol `solver-selection-v3-21-events-2026-10-20`. Its completed Windows pilot led to a separate [runtime amendment](solver-benchmark-runtime-amendment-2026-10-20.md), which supersedes the 120-minute ceiling below with 135 minutes for the next main run. The 18 October bundle remains historical evidence. Every run must use a new output directory; implementation checks do not establish performance or completion within a ceiling.

## Dataset selection

Keep the original controlled synthetic generator, its scoring interpretation and all original 13 inputs. Do not adopt the separately prepared 13 spreadsheet-derived controlled candidates. The masked 2021–2026 history, six yearly requests, 2026 prototype demonstration and candidate files remain separate; exclusion from the benchmark does not authorize deleting them.

The [source-informed bundle](../../research/fixtures/pjkit-sample-2026-10-20/README.md) uses full-history registration frequency in the existing two-year-named input field, following the user's explicit instruction. That semantic override does not transfer to this benchmark. The benchmark retains its original synthetic activity-generation rules. Historical data supplies business context, not empirical calibration or validation of these controlled profiles. The four prototype timing checks below also use benchmark events, rather than the separate 60-registration demonstration request.

## Confirmed case inventory

One Emperor registration requires two physical seats; Merit and Bodhi require one. Registration count N = E + M + B; seat demand D = 2E + M + B. Capacity is 232 physical seats.

| Family | Emperor | Merit | Bodhi | Registrations | Seat demand | Occupancy | Patterns / events |
|---|---:|---:|---:|---:|---:|---:|---|
| Small, retained | 8 | 8 | 8 | 24 | 32 | 13.8% | All four / 4 |
| Typical, retained | 56 | 24 | 16 | 96 | 152 | 65.5% | All four / 4 |
| High occupancy, added | 62 | 31 | 24 | 117 | 179 | 77.2% | All four / 4 |
| Near capacity, added | 73 | 37 | 29 | 139 | 212 | 91.4% | All four / 4 |
| Full capacity, retained | 80 | 40 | 32 | 152 | 232 | 100% | All four / 4 |
| Emperor-heavy, retained | 99 | 19 | 13 | 131 | 230 | 99.1% | Mixed only / 1 |

All four means mixed profiles, contribution/activity conflict, tied contributions with varying activity, and a witness-compatible accessibility derivative of mixed. The new tier counts scale the full-capacity composition approximately while meeting the exact seat demands. They are not copies of yearly historical cohorts. The resulting inventory has 21 events, including five related accessibility derivatives.

## Batches and runtime

| Batch | Coverage | Jobs | Nominal allowance |
|---|---|---:|---:|
| Primary | 21 events × four existing configurations × three methods × 5 s | 252 | 1,260 s / 21 min |
| Budget sensitivity | Four selected events × three active configurations × three methods × 30/60 s | 72 | 3,240 s / 54 min |
| Prototype verification | Same four events × current configuration × actual prototype settings, configured 60 s | 4 | 240 s / 4 min, plus service overhead |
| Separate pilot | Coverage specified below | 28 | 600 s / 10 min |

There are 324 comparative runs plus four separate prototype checks: **328 main jobs**, before pilot and correctness work. Comparative search allocations total 75 minutes; adding prototype allowances gives 79 minutes. Including nominal pilot allocations gives 89 minutes before other work. These are scheduling allocations, not measured completion forecasts. Early completion may shorten runs, and prototype return time may exceed its configured allowance.

The overall solver-study ceiling is **120 minutes**, including preparation, certification, correctness, pilot, construction, search, validation, persistence and reporting. End measured-batch work by minute 115 and reserve the final five minutes for reports. A fresh pilot projection must pass before main runs; do not silently drop cases, shorten declared budgets or extend the deadline to force completion. Preserve interrupted, not-started and validation-pending records.

The separate rank-weighting study is unchanged: 12 events, 840 searches, four-second limits, 56 minutes allocated search and its own 120-minute ceiling. Combined permitted sequential runner execution is at most 240 minutes, excluding development and later dissertation writing. No concurrent execution is included.

### Fixed longer-budget and prototype subset

Use high-occupancy mixed, near-capacity mixed, full-capacity mixed and Emperor-heavy mixed. Cross them with the three existing active configurations for the longer-budget comparisons; reuse their primary five-second endpoints. Use current/default preference order and the actual prototype configuration for the four separate timing checks, currently 60 seconds, eight workers and canonicalization enabled, with isolated research stores.

This replaces the previous subset of full-mixed, full-conflict, full-tied and Emperor-heavy mixed before observing main outcomes. Full-conflict and full-tied remain primary cases. Conflict, tied-contribution and accessibility scenarios receive five-second comparisons only. Longer-budget claims concern these four mixed-profile events; they do not establish longer-budget behavior under the other patterns.

### Confirmed 28-job pilot

Use the existing separate development seed, with current/default preferences:

- Six mixed families × three methods × five seconds: 18 jobs, 90 s allocated.
- Emperor-heavy mixed × three methods × 30/60 seconds: six jobs, 270 s allocated.
- Four selected events through the actual prototype path: four jobs, 240 s configured.

Set the default and maximum pilot allowance to **900 seconds / 15 minutes**, nested inside the 120-minute total. The pilot checks correctness and runtime feasibility, not dissertation hypotheses. High/near-capacity 30/60-second comparative behavior is measured in the main batch; the pilot checks their short-run and prototype paths. An unsuccessful completion projection prevents main execution and requires a recorded amendment rather than result-dependent scope reduction.

## Analysis and figure implications

Keep H1, RQ1, H3 and the prototype verification question, with the existing matched objectives and separate validity, coverage, cost/components, runtime and proof reporting. H2 remains the separate weighting study. No combined accuracy, satisfaction or overall winner score is added.

- Primary denominator: 84 matched cases per method, 21 per preference configuration. Each H1 cost panel has at most 21 both-valid pairs; show exclusions and coverage. All-disabled cases remain 21 feasibility controls per method.
- Budget denominator: 12 matched cases per method per budget, four per active configuration, with the revised mixed-event membership. Do not compare that rate directly with the full 84-case primary rate.
- Retain the existing five analytical figure families across both studies and the 230-seat Emperor-heavy illustration. Figure 1 expands to 21 event rows; Figure 2 gains the new paired cases; Figure 3 uses the revised subset. Weighting figures and their data remain unchanged. No extra main-chapter figure is required.
- Optional runtime-versus-demand plots may show demands 32, 152, 179, 212, 230 and 232, labelled with registration counts and patterns. Profile composition and demand vary together: this is a scenario comparison, not a causal occupancy experiment or empirical complexity law.
- Retain one run per method/case/budget and fixed seeds. Related scenarios are not independent population samples, and the extension adds no repeated-trial runtime variance or significance claims.

## Implementation acceptance checks

These are implementation/preflight acceptance checks. The runner and implementation tests cover items 1–4; fresh pilot evidence remains pending:

1. Extend inventory, scheduling and reporting consistently to 21 events and 328 main jobs; do not only add family counts to a pilot loop. Preserve original request IDs, counts, seeds and derivation rules. Verify original 13 input hashes against retained evidence. Record the amended shuffled schedule; extending the job set can change execution order without changing inputs.
2. Implement the revised four-event subset and 28-job pilot. Derive projections from the schedule: 4,500 comparative search seconds, 108 comparative jobs per method, and four prototype allowances. Remove assumptions tied to the old 4,020 seconds / 76 jobs per method.
3. Implement the 7,200-second total deadline, 6,900-second measured-work cutoff, 300-second report reserve and 900-second pilot default/maximum. Keep single-worker comparative controls, scorer equivalence, no hints and independent audits intact.
4. Certify all amended inputs and compiled score vectors; preserve separate tiny-oracle and deliberately infeasible correctness checks. Add appropriate schedule, boundary and original-input-preservation verification. These checks are not main benchmark observations.
5. Run and retain a fresh development pilot, then use a new main evidence bundle if its gates pass. Keep all 18 October snapshots/reports unchanged as historical development evidence. They do not validate completion of the expanded workload.

## Decision audit and closure

| Session question | User answer | Settled decision |
|---|---|---|
| Q1 | A | 179 and 212 count physical seats, not registrations |
| Q2 | A, with expanded ceiling | Add both complete four-pattern families; allow 120 minutes overall |
| Q3 | A | Use the specified full-capacity-anchored tier counts |
| Q4 | B | Reselect the four mixed events for longer budgets and prototype checks |
| Q5 | A | Adopt the proportionate 28-job pilot, capped at 15 minutes |
| Q6 | A | Shared understanding confirmed; this GrillMe session is closed |

No research-design question remains open in this session. Implementation checks are not evidence of solver performance or industry-supervisor approval of the source-derived data.
