# Solver benchmark runtime amendment: 20 October 2026

Status: **authorized after the completed Windows development pilot; implemented for the next main run**. This amends only the solver study's overall runner ceiling. The 20 October [scope amendment](solver-benchmark-scope-amendment-2026-10-20.md) remains the record of the 21-event design.

## Evidence and decision

The 28-job Windows pilot in [`docs/results/solver-selection-v3-21-events-windows-pilot-2026-10-20`](../results/solver-selection-v3-21-events-windows-pilot-2026-10-20/pilot/results.md) completed all 28 attempts. Correctness and input certification passed, no worker was interrupted, and no returned map failed external validation. The pilot's conservative [projection](../results/solver-selection-v3-21-events-windows-pilot-2026-10-20/pilot/projection.json) was 7,509.90 seconds (125.16 minutes), exceeding the former 7,200-second ceiling by 309.90 seconds. The user accepted this projected duration and authorized a recorded ceiling extension before the main experiment.

The new solver runner ceiling is **8,100 seconds (135 minutes)**. Measured-batch work stops by **7,800 seconds (130 minutes)**, retaining the final **300 seconds** for report generation. Relative to the completed pilot projection, this supplies 590.10 seconds (9.84 minutes) of projected headroom. The projection is an estimate, not a completion guarantee; the main run repeats correctness, input certification and a fresh 28-job pilot within its own clock. It proceeds to the main jobs only if that fresh projection fits the new ceiling.

## Frozen study design

This amendment does not change the 21 synthetic events, their generation seeds or retained input hashes; four preference configurations; CP-SAT, SCIP and greedy definitions; 252 primary five-second runs; 72 fresh 30/60-second runs on the four mixed events; four prototype checks; 28 pilot jobs; worker/canonicalization settings; independent audits; scoring; or figure and table definitions. The three methods retain identical per-case search allowances. The separate rank-weighting study retains its own 120-minute ceiling.

The earlier `solver-selection-v3-21-events-2026-10-20` pilot remains development evidence under the old 120-minute limit. The amended main run uses protocol `solver-selection-v4-21-events-135m-2026-10-20` and a new evidence directory. Do not combine the pilot records with main outcomes or overwrite either bundle. If the fresh main-run pilot projects beyond 135 minutes, the runner must stop before main measurements and preserve diagnostics; do not shrink the case set or extend the deadline silently.
