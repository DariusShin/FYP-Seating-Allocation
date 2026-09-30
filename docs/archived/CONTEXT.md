> Archived historical guidance. For the current workflow and setup, see the [project README](../../README.md) and [frontend README](../../frontend/README.md).

# Active implementation context

Production specification: `docs/planning/archived/production-implementation-plan-v2.md`. Later confirmed edge-case defaults are recorded in `docs/requirements-traceability.md`.

- 16×16 physical venue, blocked rows 6/8 positions 5–12, 240 assignable; row 7 available.
- Explicit registration tiers Emperor → Merit → Bodhi, minimums 5000/3000/2000, no automatic exclusive amount classification.
- Shared boundary rows, hard tier/contribution row ordering, soft within-row desirability.
- Side accessibility is hard; initial centre-out/front packing is strict. Repair permits gaps.
- Three ranked ordinary preferences: contribution_seat, activeness, category_zone. Backend ranked-v1 mapper 40/30/20; disabled ranks compact. Movement is protected repair policy.
- INITIAL / REGENERATE_DRAFT / FULL_REGENERATION have no baseline. REPAIR_PUBLISHED resolves published history on the server.
- OPTIMAL and FEASIBLE can be reviewed after audit. Manual edits are rescored and lose current optimality claims.
- Generate → draft → review → approve → publish. Public lookup never reads newest output files.
- Local persistence: SQLite immutable plan snapshots and transactional published pointer. Host integration: signed session cookie, production auth required.
- Python production modules: policy, production, production_scoring, production_validator, plan_store, service, production_data, evaluation.
- Legacy v1 modules remain for reproducibility only. Do not copy their assumptions into production changes.

Run Python tests with `PYTHONPATH=src .venv/bin/python -m pytest`. Frontend checks: test, typecheck, lint, build. Read frontend/AGENTS.md and installed Next.js docs before frontend changes. Preserve unrelated working-tree changes and signed academic artifacts.
