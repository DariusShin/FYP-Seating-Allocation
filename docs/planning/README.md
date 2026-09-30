# Project planning documents

Central index for application enhancement plans, storage proposals and historical implementation plans. A document's status matters: placement in this folder does not mean its feature is implemented or approved. Runtime/setup documentation remains in `docs/` and the project READMEs; research and report-editing material remains under `FYP1/`.

## Current and branch-specific plans

| Document | Status and purpose |
| --- | --- |
| [Manual swap replay after regeneration](manual-swap-replay-after-regeneration.md) | Proposed; future `codex/preserve-manual-swaps` branch. Ordered registration-ID decisions replayed after generation, outside the solver. Includes data model, async lifecycle, conflicts and acceptance scenarios. |
| [Local manual-edit history](manual-edit-history-proposal.md) | Proposed foundation for per-version history, recovery and undo/redo. Read alongside the replay plan for shared-store and portable-intent requirements. |
| [DynamoDB seating schema](dynamodb-seating-schema.md) | Target cloud storage/integration architecture; local runtime still uses SQLite. The replay records are a proposed extension, not already included in this schema. |
| [Safeguard verification plan](safeguard-verification-plan.md) | Branch-specific plan and implementation notes. Consult its status and the [separation audit](../seating-safeguard-separation.md); do not treat historical statements as a guarantee of current runtime behavior. |

## Historical plans

These retain previous requirements and decisions. They are reference material, not instructions to restore superseded behavior.

| Document | Purpose |
| --- | --- |
| [Dashboard redesign](archived/seating-dashboard-redesign-plan.md) | Earlier staff workspace/UI redesign backlog. |
| [Production implementation plan](archived/production-implementation-plan.md) | Original production implementation direction. |
| [Production implementation plan v2](archived/production-implementation-plan-v2.md) | Revised historical policy and implementation plan. |
| [Production recommendations](archived/GUIDE-production-recommendations.md) | Earlier behavioral recommendations supporting those plans. |

Historical implementation evidence, traceability, integration notes and old guides remain in [docs/archived](../archived/README.md). Current model explanations and evaluations remain in `docs/`; they are not implementation plans.

## Academic planning references

Academic/report plans retain their `FYP1/` context and are indexed here rather than mixed into application implementation backlogs:

- [Literature-review response roadmap](../../FYP1/guideline/Literature_Review_Response_Roadmap.md).
- [Targeted interim-report revisions](../../FYP1/guideline/interim_report_targeted_revisions.md).
- [Objective 2 refinement](../../FYP1/guideline/refine-objective2.md).
- [Assignment 2 amendments](../../FYP1/guideline/Assignment2-amendment.md).

## Filing convention

Put new application proposals directly in this directory with a descriptive kebab-case filename. Include status, intended branch, scope, dependencies, unresolved decisions and acceptance checks. Move superseded/completed plans into `archived/` with their historical status preserved; link to their replacement. Keep a single canonical file and update this index and incoming links when moving it.

## Relocation record (2026-10-01)

| Previous path | Canonical path relative to this directory |
| --- | --- |
| `docs/manual-edit-history-proposal.md` | `manual-edit-history-proposal.md` |
| `docs/safeguard-verification-plan.md` | `safeguard-verification-plan.md` |
| `docs/dynamodb-seating-schema.md` | `dynamodb-seating-schema.md` |
| `docs/archived/seating-dashboard-redesign-plan.md` | `archived/seating-dashboard-redesign-plan.md` |
| `docs/archived/production-implementation-plan.md` | `archived/production-implementation-plan.md` |
| `docs/archived/production-implementation-plan-v2.md` | `archived/production-implementation-plan-v2.md` |
| `docs/archived/GUIDE-production-recommendations.md` | `archived/GUIDE-production-recommendations.md` |
