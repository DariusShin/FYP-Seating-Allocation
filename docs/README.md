# Documentation index

Current documentation is organized by responsibility. The local application as of 2026-10-05 uses the `pjkit-v4` policy, the `desirability-v2` scorer, a Python CP-SAT solver, a Next.js staff interface, SQLite workspaces and browser-local Dexie history.

| Area | Contents |
| --- | --- |
| [Application guides](application/README.md) | Implemented behavior: solver/service/UI code overview, verification, absence workflow, manual history and integration |
| [Methodologies](methodologies/README.md) | Modeling, literature and evaluation-method explanations, including the current mathematical model |
| [Planning](planning/README.md) | Confirmed experiment hypotheses, solver/weighting protocols, execution and dissertation figures; repository restructuring and unimplemented application proposals |
| Results | [Preference sensitivity](results/preference-sensitivity-2026-10-11/) and [expanded attempt 3 Study A figures](results/solver-selection-v4-attempt3-figures-2026-10-23/README.md), with manifests and source snapshots. The [production Study B plan](planning/solver-selection-production-follow-up.md) is separate and has no measured results yet |
| [Solver benchmark setup](results/solver-benchmark-setup-2026-10-18.md) | Implementation validation and development pilots; links to executable commands, raw data and diagnostic tables; main-study execution pending |

Start with the [project README](../README.md) for setup and the [web app README](../apps/web/README.md) for a local walkthrough. Component boundaries are described in the [seat component guide](../apps/web/src/components/seat/README.md).

Superseded implementation guides, completed plans and redundant replacement pages have been deleted. Prior revisions remain in Git history. Academic reports and feedback under `FYP1/` are research records, not current implementation instructions. The planning index retains proposed enhancements and experiment protocols with explicit implementation/execution status.
