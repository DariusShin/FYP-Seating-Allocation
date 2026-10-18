# Repository and application planning

Plans describe proposed enhancements and retained experiment protocols; each entry records its implementation/execution status. See the [documentation index](../README.md) for implemented features.

## Proposed enhancements

| Document | Status and scope |
| --- | --- |
| [Experiment hypotheses, analysis and confirmed decisions](experiment-hypotheses-and-analysis.md) | Confirmed H1/RQ1 solver comparison, H2 weighting trade-offs, H3 budget comparisons and prototype timing verification; workload estimates, inference limits and Q1–Q13 decision audit. Current GrillMe interview closed; solver harness implemented, main experiments pending |
| [Benchmark result tables and dissertation figures](benchmark-results-visualization.md) | Confirmed Q10: five analytical figures across solver/budget/weighting studies plus a 230-seat illustration; sensitivity table substitution allowed, three main result tables and appendix records |
| [Experiment execution sequence and evidence recording](experiment-execution-sequence.md) | Execution guidance for both confirmed protocols: shared preparation/pilots, solver benchmark before weighting, local M4/24 GB primary environment, separate budgets and JSON evidence bundles |
| [Solver selection and supporting benchmark](solver-selection-benchmark.md) | Confirmed protocol; solver harness and development validation implemented, main execution pending. CP-SAT/greedy/SCIP: 13 events, 52 primary matched cases at five seconds; fixed 12-case subset at 30/60 seconds gives 228 comparative runs, plus four separate prototype checks; shared 90-minute runner ceiling |
| [Rank-weighting experiment protocol](rank-weighting-experiment.md) | Confirmed amended plan; implementation and execution pending. Four methods excluding equal weighting, 12 initial-allocation datasets, 840 searches at four seconds, 56 minutes allocated search within a two-hour runner cap; limited sensitivity/seed checks. Human verification deferred until post-project live deployment |
| [Repository restructuring and scoped change management](repository-restructuring.md) | Stages 0–4 of the research/application/evidence separation implemented on `restructure-project-folders`; retains the migration inventory, provenance rules, validation gates, conventional commit scopes and the remaining deployment decisions |
| [Manual swap replay after regeneration](manual-swap-replay-after-regeneration.md) | Proposed. Portable ordered registration-ID decisions, shared storage, replay conflicts and atomic candidate adoption outside the solver |
| [Production concurrent-edit alerts](concurrent-editing-production-ui.md) | Proposed, outside FYP scope. With Version/Local-history controls hidden, classify stale saves as draft-superseded or published-while-editing, alert with a Reload-latest action and show last-saved provenance; no backend concurrency change |
| [Seating table design](table.md) | Proposed. Canonical single-table `seating` design for the production DynamoDB integration, written in the Offerings `table.md` format: access patterns with table/key conditions/filter expressions and frequency, bare-event partition keys, flattened entities without SQL-style foreign keys, a versioned policy registry (seed/deploy-time; staff never edit policy), and the recorded key-shape decisions for the Plan/Layout/Policy sort keys (with no audit History entity — accountability rides on per-item audit metadata; the changeset log was rejected as an unused Offerings-pattern reuse). Supersedes the deleted DynamoDB seating schema and the lean CSV workbook (earlier revisions remain in Git history) |
| [Seating production table spec](production-table.md) | Proposed. Clean production-facing extraction of the seating table design in the host platform's house format (Type Enums → Entities → Facets → Secondary indexes → Access patterns), with the rationale and decision records left in [table.md](table.md) |

## Implemented features

| Current guide | Status |
| --- | --- |
| [Manual-edit history](../application/manual-edit-history.md) | Dexie journals, undo/redo, snapshots, recovery and route handoff implemented |
| [Verification flow](../application/verification-flow.md) | Findings, attribution, corrections, overrides and server publication gates implemented |

## Academic records

Superseded implementation plans have been deleted; earlier revisions remain in Git history. Academic materials remain under `FYP1/`:

- [Literature-review roadmap](../../FYP1/guideline/Literature_Review_Response_Roadmap.md)
- [Interim-report revisions](../../FYP1/guideline/interim_report_targeted_revisions.md)
- [Objective 2 refinement](../../FYP1/guideline/refine-objective2.md)
- [Assignment 2 amendments](../../FYP1/guideline/Assignment2-amendment.md)

New proposals should state status, scope, dependencies, unresolved decisions and acceptance checks. Implemented behavior belongs in a current guide; remove superseded plans once their useful details are documented there. Academic evidence does not define current runtime behavior.
