# Application planning

Plans describe unimplemented enhancements, not current runtime behavior. See the [documentation index](../README.md) for implemented features.

## Proposed enhancements

| Document | Status and scope |
| --- | --- |
| [Manual swap replay after regeneration](manual-swap-replay-after-regeneration.md) | Proposed. Portable ordered registration-ID decisions, shared storage, replay conflicts and atomic candidate adoption outside the solver |
| [DynamoDB seating schema](dynamodb-seating-schema.md) | Proposed target cloud architecture. Local persistence is SQLite; async jobs, imports and the independently versioned cloud verification facet are not implemented |

## Implemented features

| Current guide | Status |
| --- | --- |
| [Manual-edit history](../manual-edit-history.md) | Dexie journals, undo/redo, snapshots, recovery and route handoff implemented |
| [Verification flow](../verification-flow.md) | Findings, attribution, corrections, overrides and server publication gates implemented |

## Academic records

Superseded implementation plans have been deleted; earlier revisions remain in Git history. Academic materials remain under `FYP1/`:

- [Literature-review roadmap](../../FYP1/guideline/Literature_Review_Response_Roadmap.md)
- [Interim-report revisions](../../FYP1/guideline/interim_report_targeted_revisions.md)
- [Objective 2 refinement](../../FYP1/guideline/refine-objective2.md)
- [Assignment 2 amendments](../../FYP1/guideline/Assignment2-amendment.md)

New proposals should state status, scope, dependencies, unresolved decisions and acceptance checks. Implemented behavior belongs in a current guide; remove superseded plans once their useful details are documented there. Academic evidence does not define current runtime behavior.
