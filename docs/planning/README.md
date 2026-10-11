# Repository and application planning

Plans describe unimplemented enhancements, not current runtime behavior. See the [documentation index](../README.md) for implemented features.

## Proposed enhancements

| Document | Status and scope |
| --- | --- |
| [Repository restructuring and scoped change management](repository-restructuring.md) | Stages 0–4 of the research/application/evidence separation implemented on `restructure-project-folders`; retains the migration inventory, provenance rules, validation gates, conventional commit scopes and the remaining deployment decisions |
| [Manual swap replay after regeneration](manual-swap-replay-after-regeneration.md) | Proposed. Portable ordered registration-ID decisions, shared storage, replay conflicts and atomic candidate adoption outside the solver |
| [Production concurrent-edit alerts](concurrent-editing-production-ui.md) | Proposed, outside FYP scope. With Version/Local-history controls hidden, classify stale saves as draft-superseded or published-while-editing, alert with a Reload-latest action and show last-saved provenance; no backend concurrency change |
| [Seating table design](table.md) | Proposed. Canonical single-table `seating` design for the production DynamoDB integration, written in the Offerings `table.md` format: access patterns with table/key conditions/filter expressions and frequency, bare-event partition keys, flattened entities without SQL-style foreign keys, a versioned policy registry for the Settings dialog, and changeset-based history. Supersedes the deleted DynamoDB seating schema and the lean CSV workbook (earlier revisions remain in Git history) |

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
