# Current application documentation

These guides describe the implemented local application as of 2026-10-05. Production uses the `pjkit-v4` policy, the `desirability-v2` scorer, a Python CP-SAT solver, a Next.js staff interface, SQLite workspaces and browser-local Dexie history.

| Guide | Scope |
| --- | --- |
| [Code overview](code_overview.md) | Solver, persistence, API and frontend module responsibilities |
| [Staff UI](ui-reference.md) | Generation, editing, route navigation and published displays |
| [Absence reallocation](absence-reallocation.md) | Objective 2, incremental repair, movement priorities and shared attendance |
| [Verification flow](verification-flow.md) | Entry, findings, corrections, overrides and publication gates |
| [Manual-edit history](manual-edit-history.md) | Local journals, saved versions, recovery and route handoff |
| [Mathematical model](mathematical_model.md) | Current production constraints and objective |
| [Machine-readable model](mathematical_model.json) | Production formulation and lifecycle contract |
| [Mathematical background](solver-mathematical-background.md) | Plain-language explanation of the production model |
| [Integration](integration.md) | Service inputs, workspace commands, host identity and public projections |
| [Requirement traceability](requirements-traceability.md) | Applicable current rules and their implementation/test evidence |
| [Evaluation](evaluation.md) | Existing test coverage, experiment commands and remaining research measurements |
| [Planning](planning/README.md) | Unimplemented swap replay and cloud architecture proposals |

Start with the [project README](../README.md) for setup and the [frontend README](../frontend/README.md) for a local walkthrough. Component boundaries are described in the [seat component guide](../frontend/src/components/seat/README.md).

Superseded implementation guides, completed plans and redundant replacement pages have been deleted. Prior revisions remain in Git history. Academic reports and feedback under `FYP1/` are research records, not current implementation instructions. The planning index retains only explicitly unimplemented proposals.
