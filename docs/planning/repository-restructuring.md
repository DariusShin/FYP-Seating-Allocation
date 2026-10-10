# Repository restructuring and scoped change management

Date: 11 October 2026 (Asia/Kuala_Lumpur).

Status: **stages 0–3 implemented on `restructure-project-folders`; stage 4 documentation regrouping implemented; cloud deployment remains out of scope**. The user confirmed `docs/results/` as the destination for experiment evidence, alongside the requested `docs/methodologies/`. §2's dependency inventory and the move inventory below are retained as the pre-migration record; current paths reflect the implemented layout.

## 1. Purpose and decisions

Keep one repository for the FYP research and its reference web application, with explicit boundaries between executable software, experimental code, explanatory documents and recorded evidence.

| Decision | Rationale | Status |
|---|---|---|
| Put methodology documents in `docs/methodologies/` | Make mathematical modeling and evaluation methods easy to locate | Requested |
| Put recorded experiment evidence in `docs/results/` | Keep results distinct from methods and application runtime state | Confirmed by user |
| Keep executable experiments under `research/experiments/` | Scripts have dependencies and execution instructions; they are not just documents | Proposed |
| Keep one maintained current solver, used by both experiments and the application | Avoid research and deployment implementations drifting apart | Proposed |
| Separate Next.js and Python service boundaries | Give each component clear dependency, testing and deployment ownership | Proposed |
| Migrate in independently reviewable stages | Preserve working commands, historical evidence and application behavior | Proposed |
| Use stable responsibility-based commit scopes | Make history searchable even after paths change | Proposed convention |

The restructuring does not include changing numerical preference weights, hard constraints, registration eligibility, movement priorities, database technology or API behavior. Those changes need their own rationale and validation in separate commits.

## 2. Current repository and dependencies

The present Python locations are `src/seat_solver/prototype/` and `src/seat_solver/production/`. Next.js lives separately in `frontend/`; it is not inside the Python production directory.

The local application calls `seat_solver.production.service` as a subprocess through `frontend/src/lib/production-service.ts`. Local server persistence uses SQLite; browser history uses Dexie/IndexedDB. The DynamoDB design in `docs/planning/table.md` describes future integration. A production-named directory does not establish that Lambda deployment is implemented or tested.

Dependencies that must be addressed before moving application code:

| Current dependency | Migration consequence |
|---|---|
| Production modules import `read_json`/`write_json` from `seat_solver.prototype.models` | Extract shared utilities before removing the prototype from the application package |
| `production-service.ts` derives the solver root from the parent of the working directory | Update process configuration and integration tests when moving the frontend |
| `policy.py` derives the root using `Path(__file__).resolve().parents[3]` | Replace repository-depth assumptions with explicit configuration or packaged resources |
| Experiment code derives the root by parent depth and modifies `sys.path` | Establish an installed solver dependency and a documented experiment entry point |
| Root `tests/conftest.py` imports historical prototype modules | Split historical fixtures from current application test fixtures |
| `production_data.py` contains synthetic generation and application-used name restoration | Separate responsibilities before moving the generator into research/test support |
| Evaluation code lives in the production package | Move research orchestration after extracting its required shared functionality |
| Recorded manifests contain source paths and SHA-256 hashes | Preserve original provenance and matching source before changing those files |

## 3. Proposed target structure

```text
FYP-Seating-Allocation/
├── apps/
│   └── web/                         # Current frontend/
│       ├── src/                     # Next.js routes, UI and browser history
│       ├── tests/
│       └── package.json
├── services/
│   └── seating/
│       ├── pyproject.toml
│       ├── src/seat_solver/
│       │   ├── core/                # Constraints, scoring, validation and repair
│       │   ├── application/         # Workspace and publication use cases
│       │   ├── adapters/            # Local process and persistence integrations
│       │   └── resources/           # Packaged policy/layout defaults
│       └── tests/
├── research/
│   ├── experiments/                 # Runners, sensitivity studies and analysis
│   ├── baselines/                   # Historical prototype; future comparators
│   ├── fixtures/                    # Synthetic generators and reusable datasets
│   └── archive/FYP1/                # Earlier reports, feedback, papers and diagrams
├── contracts/                       # Canonical request/result schemas
├── docs/
│   ├── methodologies/
│   ├── results/
│   ├── application/
│   ├── architecture/
│   └── planning/
├── output/                          # Local runtime state and disposable output
└── README.md
```

Create folders when they receive real content. Add an `infra/` directory only when implementing deployment configuration. Keep `seat_solver` as the Python import namespace where practical; folder relocation alone should not force callers to adopt unrelated API changes.

### Dependency and ownership rules

- Experiments import the maintained solver package. The deployed application must not import experimental algorithms, result archives or historical prototype code.
- The solver core receives validated inputs and performs allocation/scoring. Database access and transport concerns belong to adapters; application use cases coordinate them.
- Extract an interface at an actual boundary rather than creating speculative abstractions for every module.
- Keep one authoritative copy of each schema and policy. If contracts are bundled into a deployment artifact, generate that copy and check it against the canonical source; do not maintain it independently.
- Keep historical prototype rules explicitly separate from current PJKIT rules. The prototype is not automatically a fair comparator if its feasible set or objective differs.
- Production tests and research experiments may share synthetic fixture utilities, but a service deployment should not require the research toolchain. Decide the fixture package location after separating application-used functions from `production_data.py`.

## 4. Documentation and evidence move inventory

Paths below are repository-relative. Preserve filenames during the first relocation to reduce unnecessary link changes.

| Current source | Destination |
|---|---|
| `docs/maths-model-draft.md` | `docs/methodologies/maths-model-draft.md` |
| `docs/maths-model-review-2026-10-11.md` | `docs/methodologies/maths-model-review-2026-10-11.md` |
| `docs/seating-algorithm-research-2026-10-08.md` | `docs/methodologies/seating-algorithm-research-2026-10-08.md` |
| `docs/preference-parameter-study-2026-10-11.md` | `docs/methodologies/preference-parameter-study-2026-10-11.md` |
| `docs/preference-elicitation-template.md` | `docs/methodologies/preference-elicitation-template.md` |
| `docs/mathematical_model.md` and `.json` | Same filenames under `docs/methodologies/` |
| `docs/solver-mathematical-background.md` | `docs/methodologies/solver-mathematical-background.md` |
| `docs/evaluation.md` | `docs/methodologies/evaluation.md` |
| `docs/requirements-traceability.md` | `docs/methodologies/requirements-traceability.md` |
| Entire `experiments/results/preference-sensitivity-2026-10-11/` | `docs/results/preference-sensitivity-2026-10-11/` |
| Recorded `output/evaluation/*.json` | `docs/results/historical/evaluation/`, retaining original filenames |
| `experiments/preference_sensitivity.py`, `summarize_preference_sensitivity.py` and runner README | `research/experiments/` |
| `src/seat_solver/production/evaluation.py` | `research/experiments/`, after dependency cleanup |
| `src/seat_solver/prototype/` and associated historical tests/fixtures | `research/baselines/legacy_cp_sat/`, after dependency cleanup |
| `FYP1/` | `research/archive/FYP1/`, preserving its internal structure |

Inspect older `output/performance_report.json`, `output/validation_report.json` and associated allocation/input files before archiving them. Keep related evidence together, identify its policy/schema version, and record missing provenance honestly. A filename containing `v2` is not sufficient evidence of the exact model used.

Keep the draft, reviewed model and implemented formulation labelled by status. Use one canonical current formulation and link to it from application guides rather than maintaining competing copies.

Application guides such as integration, UI, verification, manual history, absence workflow and code overview should ultimately move to `docs/application/`. Architecture documentation should distinguish current local SQLite/browser persistence from proposed DynamoDB deployment. Move `docs/planning/table.md` only with its links and proposed-status label updated.

### Results bundle preservation

The 11 October preference study currently contains 40 evidence files and a manifest referencing 15 source files. Confirm these counts again at migration time rather than treating them as permanent invariants.

For every recorded run:

1. Preserve original inputs, per-run records, summaries and manifests byte-for-byte during relocation.
2. Verify source hashes before editing or moving the recorded source. Record a recoverable Git revision only if it actually contains all matching source; untracked experiment files cannot be recovered from an earlier commit.
3. Where necessary, save an immutable `source_snapshot/` with the original relative paths and verify it against the manifest. This is an evidence snapshot, not another actively maintained solver.
4. Add a separate relocation note/path map. Do not rewrite original paths or hashes to imply that the old experiment used the new implementation.
5. Update documentation links outside immutable records. If a recorded report needs a navigational replacement, provide a wrapper/index or an explicitly labelled corrected edition.
6. Run any reproduction check into a new directory. Explain differences in machine, dependencies, source revision or time budget.

Keep live SQLite databases, backups, participant-specific operational data and browser storage outside `docs/results/`. Retain the existing runtime database location through the initial migration so a new empty database is not accidentally mistaken for the saved application state.

## 5. Staged migration and acceptance gates

All implementation stages below are pending. Each stage should produce a reviewable change that leaves the repository usable.

### Stage 0 — Record the baseline

- Inventory tracked and untracked files; preserve existing work without blanket staging or cleanup.
- Capture current setup commands, relevant test outcomes, representative synthetic solve/validation output and experiment provenance.
- Record the local database configuration without copying operational data into research evidence.
- Establish a baseline before changing paths, so pre-existing failures are distinguishable from migration regressions.

### Stage 1 — Organize methodology and results

- Create `docs/methodologies/` and `docs/results/`, and perform the inventory moves above.
- Preserve source snapshots/provenance before changing experiment runner defaults.
- Add destination indexes and update root/documentation links, including references in command examples.
- Update default output locations for future recorded experiments to `docs/results/<study-id>/`; retain an explicit output argument for temporary runs.

Acceptance: moved evidence hashes match, local documentation links resolve, provenance remains inspectable, and a small experiment can write to a fresh directory. A documentation-only move does not require rerunning the full 306-solve study.

### Stage 2 — Separate research from application dependencies

- Extract shared JSON utilities from the prototype package without changing serialization behavior.
- Split synthetic generation from application-required name restoration.
- Relocate experiment orchestration and historical prototype code; update CLI imports and compatibility entry points where needed.
- Separate prototype fixtures/tests from current service tests, including root `conftest.py` behavior.
- Replace experimental `sys.path` edits with a documented dependency/install arrangement.

Acceptance: current service imports succeed without importing the historical prototype or experiment modules; current and legacy tests can be collected separately; a synthetic research run uses the maintained solver package.

### Stage 3 — Move web and Python service roots

- Move `frontend/` to `apps/web/` with its package configuration, tests and applicable `AGENTS.md`/`CLAUDE.md` instructions.
- Move the Python package/build configuration to `services/seating/`; update installation instructions and test discovery.
- Update the subprocess bridge, environment-variable defaults and integration tests together.
- Replace parent-depth resource lookup with explicit resource/configuration handling. Bundle required policy, layout and schema resources into the installable/deployable artifact.
- Separate core, application and adapter responsibilities in small follow-up changes rather than combining every module redesign with the root move.

Acceptance: documented clean setup works; the service loads resources outside the repository working directory; a complete synthetic solve passes validation; relevant backend tests, frontend tests, type checking, lint and build pass; event/workspace/publication integration remains functional using isolated test state.

### Stage 4 — Consolidate documentation and future deployment ownership

- Relocate remaining application/architecture documentation and academic archives with link updates.
- Document SQLite ownership, browser-local history and the proposed cloud persistence boundary.
- Add Lambda handlers/build configuration and infrastructure only as separately scoped deployment work when required.

Acceptance: implemented and proposed designs remain distinguishable, entry-point documentation is current, and any future deployment artifact excludes research/results unless explicitly required. Cloud acceptance requires its own tests; a successful local restructure is insufficient.

## 6. Conventional commit convention

Use the [Conventional Commits 1.0.0 specification](https://www.conventionalcommits.org/en/v1.0.0/) as the syntax reference. It defines optional scopes and breaking-change notation; it does not prescribe this repository's scope vocabulary. The following scope and type choices are **proposed project rules**, not installed enforcement or an automatic release policy.

```text
type(scope): concise description

Optional body explaining the reason, affected boundary and validation.

Optional footer(s).
```

Use lowercase scopes, a concrete description and one primary responsibility per commit. Prefer a scope that survives relocation: `web` is more durable than `frontend`, and `solver` is more informative than `src`. Do not rewrite old commits to adopt the new vocabulary; existing `seating`, `venue` and `FYP1` history remains valid historical context.

### Scope vocabulary and target paths

| Scope | Responsibility / current location | Target location |
|---|---|---|
| `web` | Next.js UI, routes, browser history; `frontend/` | `apps/web/` |
| `solver` | Allocation constraints, scoring, validation and absence repair | `services/seating/src/seat_solver/core/` |
| `service` | Application commands, workspace/publication orchestration and transport wiring | Service `application/` and transport adapters |
| `storage` | Persistence implementation, schema evolution and database design | Persistence adapters and relevant architecture documents |
| `contracts` | Request/result schemas and compatibility | `contracts/` and generated/bundled consumers |
| `research` | Experiment scripts, comparator implementations and synthetic fixtures | `research/experiments/`, `baselines/`, `fixtures/` |
| `methodology` | Modeling, literature and evaluation-method explanations | `docs/methodologies/` |
| `results` | Recorded measurements, evidence bundles and results indexes | `docs/results/` |
| `planning` | Proposals and migration plans | `docs/planning/` |
| `archive` | Historical academic records and references | `research/archive/` |
| `repo` | Changes spanning repository structure, shared setup or tooling | Root configuration and coordinated cross-boundary moves |
| `infra` | Future deployment/build infrastructure | Deployment configuration when introduced |

Scopes describe the purpose of a change, not exclusive ownership of every touched file. A solver fix may include solver tests and its methodology correction. A database-design document can use `docs(storage)` even though its path begins with `docs/`. A publication operation belongs to `service`; a SQL transaction correction belongs to `storage`.

### Project type choices and examples

| Type | Project usage | Example |
|---|---|---|
| `docs` | Explanations, plans and documentation organization | `docs(methodology): group mathematical model and evaluation guides` |
| `chore` | Evidence management or routine repository maintenance | `chore(results): archive preference sensitivity evidence with provenance` |
| `refactor` | Code organization preserving intended observable behavior | `refactor(solver): extract JSON utilities from prototype dependencies` |
| `fix` | Correct an implementation defect | `fix(storage): reject publication from a stale workspace revision` |
| `feat` | Introduce a capability | `feat(research): add a greedy allocation comparator` |
| `test` | Add or improve verification | `test(service): cover solver resource loading outside the repository` |
| `build` | Dependency or artifact packaging changes | `build(service): package policy and layout resources` |
| `ci` | Automated checks | `ci(repo): validate scoped pull request titles` |
| `perf` | Performance improvements supported by measurements | `perf(solver): reduce equivalent candidate domains` |

Use `docs(results)` for a written discussion of existing measurements and `chore(results)` for adding or relocating raw evidence. Separate a scoring-policy change from a folder migration; a changed objective is not a behavior-preserving refactor. An unchanged numerical result is not required from every timed-out search after a performance change, but any behavioral equivalence claim needs appropriate evidence.

### Commit boundaries during this migration

Recommended sequence; these are examples, not commands already executed:

```text
docs(planning): document repository restructuring and commit scopes
chore(results): preserve source snapshots for recorded experiments
docs(methodology): relocate modeling and evaluation documents
chore(results): relocate recorded experiment bundles
refactor(service): remove imports from prototype utilities
refactor(research): separate experiment runners and legacy fixtures
refactor(web): move Next.js application to apps/web
refactor(repo): relocate the seating service and update its callers
build(service): bundle runtime policy and schema resources
docs(repo): update setup and component ownership guides
```

Keep dependent moves and the path/import/configuration repairs needed to make them work in the same commit. Separate unrelated semantic changes. Use `repo` for an inseparable cross-component migration; otherwise split independent work rather than listing several scopes in one title. Every commit should have a coherent purpose and a usable resulting state.

For a move, avoid opportunistic formatting or renaming that obscures the diff. Git detects renames from content; use `git mv` for tracked files where convenient, and explicitly add newly created/untracked files. Before committing, inspect `git diff --cached --stat` and `git diff --cached`. Avoid blanket `git add .` when unrelated research drafts or results are present.

### Breaking changes and scope limitations

A directory move is not automatically a breaking API change. If it removes a supported import path, CLI command, request field or integration contract without compatibility, identify that break and give migration instructions. For example, only if an old public entry point is actually removed:

```text
refactor(service)!: replace the legacy service entry point

BREAKING CHANGE: Callers must replace seat_solver.production.service with
the new documented entry point. Update the host process configuration.
```

A commit scope does not enforce file access, determine which tests are sufficient, or create a deployment boundary. Base test selection and future CI path filters on actual dependencies. In particular, solver/contracts changes may require web integration checks, while methodology changes usually need link/content checks.

### Optional enforcement later

Start with this documented convention. If enforcement becomes useful, introduce commitlint or equivalent validation in a separate tooling change, with a small explicit scope allowlist. Decide whether validation targets individual commits or squash-merge PR titles. Do not infer component version releases from scopes unless a release policy is separately defined.

## 7. Change targeting and review record

Before starting a migration change, record:

```text
Stage:
Primary scope:
Purpose:
Paths moving (old -> new):
Dependent imports, links, commands and environment settings:
Expected behavior changes (normally none for relocation):
Evidence/provenance handling:
Validation performed and outcomes:
Compatibility or rollback instructions:
```

Prefer a focused branch such as `codex/repository-methodology-organization` for the first stage. If a merged migration needs reversal, revert the relevant commit(s) and account for later dependent changes. Do not use destructive working-tree resets to undo a restructuring around ongoing user work.

## 8. Remaining implementation decisions

- ~~Exact extraction boundaries for currently mixed production modules and shared fixture utilities.~~ **Resolved:** `seat_solver.jsonio` carries the shared JSON utilities; `research/fixtures/synthetic_participants.py` carries `generate()`, while the application keeps only the deterministic name primitives and workspace restoration.
- ~~Whether legacy CLI paths receive temporary compatibility wrappers, and their documented support period.~~ **Resolved:** no shim; the full historical CLI (including `legacy-solve` and v1 validation) lives at `research/baselines/legacy_cp_sat/cli.py`, and the maintained `seat_solver.cli` serves production `solve`/`validate` only.
- Packaging/build mechanism for consuming canonical contracts without relying on a repository checkout. **Still open;** runtime policy/request schemas currently sit beside the service under `services/seating/`, and the standalone layout contract moved to `contracts/`.
- Whether and when the broader application relocation is worthwhile relative to the FYP submission schedule. **Partially resolved:** the web move and service move are implemented; deeper core/application/adapter splitting inside `seat_solver` remains follow-up work.
- Cloud handler, infrastructure and persistence implementation details, to be decided as deployment work.

Implementation notes: the `FYP1/` archive relocation was **deferred by user decision** — it stays at the repository root. Recorded evidence bundles keep their pre-relocation `manifest.json` paths and hashes, with relocation notes and a `source_snapshot/` preserved beside them.

## 9. Supporting references

- [Current documentation index](../README.md) and [current project setup](../../README.md).
- [Current integration guide](../application/integration.md) and [proposed DynamoDB design](table.md).
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/): message syntax and compatibility signals.
- [Python package resources](https://docs.python.org/3/library/importlib.resources.html): accessing packaged resources without repository-depth assumptions.
- [AWS Python Lambda packaging](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html): handler and dependency packaging for future deployment.

Update this document's status and indexes as stages are completed. Once migration is complete, retain the durable ownership/commit rules in contributor documentation and clearly mark this migration plan completed or superseded.
