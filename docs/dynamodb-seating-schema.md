# Event seating allocation — DynamoDB schema proposal

This proposal adds seating allocation to the main application's event domain. It follows the reference workbook's **Facet → Attribute → Type → Sub-attribute → Remarks → Example** representation. It describes infrastructure to create and integration work to implement; the repository currently uses SQLite and a Python process adapter, not a deployed DynamoDB/Lambda service.

## 1. Use cases

| ID | Actor and use case | Data required | Storage facets | Access pattern |
|---|---|---|---|---|
| UC01 | Administrator enables seating for an event | Existing event, offering-event mapping, seating configuration | Events metadata; Seating configuration | Get event by its existing key; get configuration |
| UC02 | Staff imports or updates seating registrations | Selected contribution bundle, registered person, status, category, accessibility, activity, age | Registration; contribution link | Query registrations for event; get/update one registration; exact source lookup |
| UC03 | Staff records cancellation, absence, or replacement | Original registration and replacement link | Registration; audit | Transactionally update affected registrations and input revision |
| UC04 | Administrator defines the hall | Dimensions, physical seats, blocked positions, pairs, accessibility | Layout object | Get immutable layout by event and version |
| UC05 | Administrator orders/enables solver preferences | Ordered preferences, policy version, solver settings | Configuration; policy | Read/update configuration with revision check |
| UC06 | Administrator generates or regenerates a draft | Consistent registration/layout/configuration snapshot | Request object; job; idempotency record | Commit request; insert queued job; trigger Lambda |
| UC07 | Staff polls a solve or retries a failed infrastructure attempt | Job status, lease, attempt, error, resulting plan | Job | Exact get by event and job; conditional state changes |
| UC08 | Staff loads a generated draft and views its diagnostics | Assignments, quality, solver proof/status, source request | Plan; result object; assignment | Get plan/result; query assignments |
| UC09 | Staff saves manual moves, names, locks, attendance or dock state | Complete working state, base plan and monotonic revision | Workspace object; configuration; audit | Stage immutable state, conditionally advance workspace pointer |
| UC10 | Staff publishes the exact saved revision | Completed result, expected published pointer, workspace revision | Plan; configuration; assignment; audit | Small transaction switches pointers after all content exists |
| UC11 | Participant views their own published seat | Signed identity, event registration mapping, published pointer | Identity link; configuration; assignment | Exact key reads; no participant/contribution table scan |
| UC12 | Staff displays or prints the published hall | Published result with seat/display metadata | Configuration; plan; result object | Resolve pointer and load immutable result |
| UC13 | Administrator repairs the published allocation | Frozen new request and authoritative published baseline | Request object; job; plan; result object | Capture/check published version; load its full result |
| UC14 | Staff reviews plan history and audit trail | Plan summaries; actor/time/action and references | Plan; audit | Query event prefixes with pagination |

## 2. Physical tables and existing-system boundaries

**Create one new physical table: `Seating`.** Logical facets below are item types in this table, not separate tables. Keep `Auth`, `Offerings`, and `Events` as the existing logical table names from the workbook; map these names to actual deployed names in infrastructure configuration.

| Table | Partition key | Sort key | Action | Index decision |
|---|---|---|---|---|
| Auth | `pk` String | `sk` String | Retain identity and role ownership | Keep existing `GSI1PK`/`GSI1SK` index |
| Offerings | `pk` String | `sk` String | Retain contribution/invoice ownership | Reuse existing `eventId`/`serialNo` GSI for import discovery |
| Events | `pk` String, existing event ID | `sk` String | Add optional seating integration attributes on `meta` | Retain existing event `type`/`pk` and `status`/`pk` GSIs |
| **Seating** | **`pk` String** | **`sk` String** | **New table for every seating facet** | **No GSI or LSI required initially** |

Use on-demand capacity initially, point-in-time recovery, and DynamoDB Streams `NEW_IMAGE` on Seating. These are proposed deployment settings, not observations of existing infrastructure. Deploy the transactional workflow in one AWS account and Region.

### 2.1 Workbook compatibility and unresolved source conventions

The workbook's `Events v2` sheet uses the raw event ID as `pk`, `meta` as its metadata `sk`, and event type/status GSIs. Its locale definition says `locale#[locale]`, while the example uses `lang#en`; statistics similarly show both `statistics` and `statistics#events`. Resolve the deployed convention in the adapter before import. Do not silently migrate these unrelated keys.

Offerings identifies an event with a code such as `202507LH`, whereas Events uses an opaque ID. Add `offeringEventId` to Events metadata to make the relationship explicit. An invoice can contain multiple bundles and names; **invoice, payer, Auth user, seating registration, and companion are not interchangeable identities**. A seating registration is one allocation unit: normally two seats for Emperor and one for Merit/Bodhi. Explicitly identify its source bundle and registered person.

The workbook does not define seating registration status, accessibility needs, participant category, activity count, age or companion name. Collect/verify these through registration or staff entry. A paid invoice alone does not establish attendance, and an offering dedication name does not establish the attending person's identity.

### 2.2 Additions to Events metadata — UC01

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Metadata | pk | String (S) | — | Existing PK; unchanged | `evt_2026_01` |
| Metadata | sk | String (S) | — | Existing SK; unchanged | `meta` |
| Metadata | seatingEnabled | Boolean (BOOL) | — | Optional addition; absence means disabled | `true` |
| Metadata | offeringEventId | String (S) | — | Required when importing legacy Offerings event records | `202507LH` |
| Metadata | seatingSchemaVersion | Number (N), integer | — | Storage contract version, distinct from solver schema | `1` |

Event `status="published"` means the event is published. It never publishes a seating plan. Seating publication is controlled exclusively by `publishedPlanVersionId` in Seating configuration.

## 3. Key conventions and complete facet map

Keys are case-sensitive. Reserve `#` as a delimiter and encode external identifiers before constructing keys. Examples use readable IDs; use generated stable IDs in production. A plan ID is a time-sortable ULID, so history ordering follows creation time without an index. Do not reuse IDs for different content.

`E` below means `EVENT#<eventId>`. Every event-owned item also carries `eventId` as a String. `objectId` values include a kind prefix, e.g. `REQUEST#req_01`, `LAYOUT#layout_v1`, `RESULT#plan_01`, `WORKSPACE#ws_01`. Object IDs identify immutable content, not a mutable revision number.

| Facet | pk value | sk value | Cardinality / purpose | Use cases |
|---|---|---|---|---|
| Configuration | `E` | `CONFIG` | One per event; active pointers and revisions | UC01, UC05–06, UC09–13 |
| Registration | `E` | `REG#<participantId>` | One per allocation unit | UC02–03, UC06 |
| Contribution link | `E` | `SOURCE#<sourceKeyHash>` | One per contributing bundle/unit; import deduplication | UC02 |
| Identity link | `USER#<authUserId>` | `EVENT#<eventId>#REG#<participantId>` | One per authorized user-registration relationship | UC11 |
| Policy | `POLICY#<policyVersionId>` | `META` | Immutable policy registry; shared across events | UC05–06, UC13 |
| Object manifest | `EVENT#<eventId>#OBJECT#<objectId>` | `META` | One manifest per layout, request, result or workspace | UC04, UC06, UC08–13 |
| Object part | Same object PK | `PART#000000`, `PART#000001`, … | Ordered bounded content chunks | Same as manifest |
| Job | `E` | `JOB#<jobId>` | One requested solve; mutable execution state | UC06–08, UC13 |
| Idempotency | `E` | `IDEMP#<tokenHash>` | One client submission token | UC06–07 |
| Plan | `E` | `PLAN#<planVersionId>` | Immutable content reference plus publication metadata | UC08, UC10–14 |
| Assignment | `EVENT#<eventId>#PLAN#<planVersionId>` | `REG#<participantId>` | One eligible registration's query projection | UC08, UC10–12 |
| Audit | `E` | `AUDIT#<13-digit-epoch-ms>#<auditId>` | Append-only action; ID prevents timestamp collision | UC02–03, UC09–10, UC14 |

Separate object and plan partitions keep large payloads out of routine event queries. This does not eliminate the potential for a very busy event partition to become hot; measure before adding shards. The current hall is 16 × 16, with 24 blocked positions and 232 assignable seats.

### 3.1 Shared type and timestamp rules

`S` = String; `N` = Number; `BOOL` = Boolean; `M` = Map; `L` = List; `B` = Binary; `NULL` = explicit null. Optional attributes are omitted unless null is part of their contract. Key attributes are always nonempty Strings. JSON arrays use ordered Lists, not sets. Attributes described as integers must be validated as integers by the application.

Host metadata `createdAt`, `updatedAt`, `publishedAt`, and `leaseUntil` use **epoch milliseconds** as Numbers, matching the workbook examples. Solver payload timestamps retain their existing ISO 8601 Strings. Any future DynamoDB TTL attribute must use epoch **seconds**, not milliseconds. No TTL is required for durable registrations, plans, source snapshots, or publication pointers.

All newly written event-owned facet items include `entityType` (String, e.g. `SOLVER_JOB`) and `eventId` (String). These are ordinary attributes, not GSI keys. Metadata timestamps and actor IDs below are set by the authenticated server.

## 4. Attribute definitions

### 4.1 Configuration — UC01, UC05–06, UC09–13

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Configuration | pk / sk | S / S | — | PK / SK | `EVENT#evt_2026_01` / `CONFIG` |
| Configuration | entityType | S | — | Fixed discriminator | `SEATING_CONFIG` |
| Configuration | eventId | S | — | Existing Events ID | `evt_2026_01` |
| Configuration | inputRevision | N, integer | — | Increment with every registration/configuration change affecting a solve | `12` |
| Configuration | stateRevision | N, integer | — | Optimistic concurrency for pointers/configuration | `20` |
| Configuration | activeLayoutObjectId | S | — | Committed immutable layout | `LAYOUT#layout_v1` |
| Configuration | policyVersionId | S | — | Current code supports this policy only | `pjkit-v3` |
| Configuration | preferenceProfileVersion | S | — | Current supported mapping | `ranked-v1` |
| Configuration | preferences | L of M | `key:S`, `enabled:BOOL` | Exactly three unique keys; list order defines priority | `[{"key":"contribution_seat","enabled":true},{"key":"activeness","enabled":true},{"key":"category_zone","enabled":false}]` |
| Configuration | solverSettings | M | See solver contract below | Versioned server-approved settings | `{"max_time_seconds":60,"num_search_workers":8,"random_seed":42,"require_optimal":false,"canonicalize":true}` |
| Configuration | eventDetails | M, optional | See event_details below | Event display snapshot, updated through revision protocol | `{"name":"Dharma Assembly","date":null,"time":null,"timezone":"Asia/Kuala_Lumpur","venue":"Main Hall"}` |
| Configuration | latestPlanVersionId | S or NULL | — | Latest explicitly attached completed draft/plan | `01JPLANEXAMPLE` |
| Configuration | publishedPlanVersionId | S or NULL | — | Sole current public-plan pointer | `null` |
| Configuration | workspaceObjectId | S or NULL | — | Saved immutable working state | `WORKSPACE#ws_01` |
| Configuration | workspaceBasePlanVersionId | S or NULL | — | Plan on which current edits are based | `01JPLANEXAMPLE` |
| Configuration | workspaceRevision | N, integer | — | Monotonic; increment on save and publication | `4` |
| Configuration | updatedAt / updatedBy | N / S | — | Epoch ms / Auth user ID | `1790640000000` / `usr_staff_01` |

Initialize revisions to zero and nullable pointers to null. A newly completed background job must not automatically replace a workspace that staff have edited meanwhile; attaching a draft checks the revisions captured at submission.

### 4.2 Registration and contribution link — UC02–03, UC06

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Registration | pk / sk | S / S | — | Event PK; stable participant SK | `EVENT#evt_2026_01` / `REG#P001` |
| Registration | entityType / eventId | S / S | — | Discriminator / owner | `REGISTRATION` / `evt_2026_01` |
| Registration | participant | M | Full participant contract in §5 | Contains only solver participant fields | `{"participant_id":"P001", ...}` |
| Registration | source | M | `table:S`, `pk:S`, `sk:S`, `bundleId:S`, `unitId:S` | Authoritative invoice/bundle reference; omit for authorized manual registration | `{"table":"Offerings","pk":"payer-example","sk":"A00001","bundleId":"bundle_01","unitId":"1"}` |
| Registration | sourceVersion | S, optional | — | Source revision or canonical relevant-content hash for reconciliation | `sha256:<64-hex-digits>` |
| Registration | revision | N, integer | — | Conditional update version | `3` |
| Registration | createdAt / createdBy | N / S | — | Creation metadata | `1790640000000` / `usr_staff_01` |
| Registration | updatedAt / updatedBy | N / S | — | Last edit metadata | `1790640000000` / `usr_staff_01` |
| Contribution link | pk / sk | S / S | — | Hash canonical JSON tuple `[table,pk,sk,bundleId,unitId]` | `EVENT#evt_2026_01` / `SOURCE#<sha256>` |
| Contribution link | entityType / eventId | S / S | — | Standard ownership | `CONTRIBUTION_LINK` / `evt_2026_01` |
| Contribution link | participantId | S | — | Stable imported registration | `P001` |
| Contribution link | source | M | Same source fields above | Verify tuple against hash; do not expose to participant | `{"table":"Offerings", ...}` |
| Contribution link | createdAt / createdBy | N / S | — | Import provenance | `1790640000000` / `usr_staff_01` |

Create registration + unique source link + increment `inputRevision` in one transaction. On repeated import, resolve the link and update the existing registration conditionally. Never silently create a second allocation for the same bundle/unit. Retain cancelled/replaced records instead of deleting them, so replacement references remain resolvable.

Map Offerings bundle tiers `emperor`, `merit`, `bodhi` to solver enums `EMPEROR`, `MERIT`, `BODHI`. Use the registered tier; do not infer tier solely from payment amount. Current minimums are RM5,000 / RM3,000 / RM2,000 respectively. `contribution_amount_rm` currently accepts whole-ringgit integers: reject fractional amounts pending an explicit host rule or solver-contract change, rather than silently rounding. Define host invoice-to-registration eligibility as a separate business rule.

### 4.3 Identity link — UC11

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Identity link | pk | S | — | PK from verified Auth user ID | `USER#usr_01` |
| Identity link | sk | S | — | SK permits several authorized registrations per user/event | `EVENT#evt_2026_01#REG#P001` |
| Identity link | entityType | S | — | Fixed | `IDENTITY_LINK` |
| Identity link | eventId / participantId | S / S | — | Server-approved relationship | `evt_2026_01` / `P001` |
| Identity link | createdAt / createdBy | N / S | — | Relationship provenance | `1790640000000` / `usr_staff_01` |

Query the authenticated user's PK with the event prefix, then validate any selected participant against these records. Guests can have registrations without an Auth link. Do not authorize by shared phone number or payer name. A signed session already containing a trusted participant ID can use that verified mapping directly.

### 4.4 Immutable objects: layout, request, result and workspace

The solver returns repeated layout, source-request and baseline data plus diagnostics. Store complete JSON without assuming it fits in one item. Use the same bounded object representation for all four large document kinds. This keeps every required durable payload in DynamoDB, with no required S3 dependency.

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Object manifest | pk / sk | S / S | — | Object-specific PK / fixed SK | `EVENT#evt_2026_01#OBJECT#REQUEST#req_01` / `META` |
| Object manifest | entityType / eventId | S / S | — | Standard ownership | `OBJECT_MANIFEST` / `evt_2026_01` |
| Object manifest | objectId | S | — | Immutable ID | `REQUEST#req_01` |
| Object manifest | objectKind | S | — | `LAYOUT`, `REQUEST`, `RESULT`, `WORKSPACE` | `REQUEST` |
| Object manifest | storageState | S | — | `STAGING` → `COMMITTED`; never back | `COMMITTED` |
| Object manifest | payloadSchemaVersion | S | — | Solver version or workspace storage version | `2.0.0` |
| Object manifest | contentEncoding | S | — | Canonical UTF-8 JSON; no compression initially | `json-utf8` |
| Object manifest | partCount | N, integer | — | Exact number of parts required | `3` |
| Object manifest | byteLength | N, integer | — | Total raw JSON UTF-8 bytes | `300000` |
| Object manifest | sha256 | S | — | Hash of concatenated bytes | `<64-hex-digits>` |
| Object manifest | createdAt / createdBy | N / S | — | Creation provenance | `1790640000000` / `usr_staff_01` |
| Object part | pk / sk | S / S | — | Same PK; zero-padded part index | Same PK / `PART#000000` |
| Object part | entityType / eventId | S / S | — | Standard ownership | `OBJECT_PART` / `evt_2026_01` |
| Object part | partIndex | N, integer | — | Starts at zero | `0` |
| Object part | data | Binary (B) | — | Up to 128 KiB raw UTF-8 bytes; SDK encodes on wire | `<binary JSON fragment>` |
| Object part | sha256 | S | — | Hash of this part's bytes | `<64-hex-digits>` |

Canonicalize with sorted object keys, compact separators, UTF-8, ordered arrays, and no NaN/Infinity; define number normalization once in the adapter. Split bytes, not independent JSON objects. Concatenate all parts before decoding UTF-8 because a multibyte character can cross a boundary. DynamoDB's 400 KB item limit includes attribute names and values; enforce an encoded-item size check as well as the conservative 128 KiB part bound. [AWS item limits](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html)

Writer protocol: create unique STAGING manifest → conditionally write immutable parts → retry unprocessed writes if using a batch path → strongly read/verify exact part sequence, lengths and hashes → conditionally set COMMITTED. Readers reject STAGING objects. Never overwrite committed parts; enforce this through the persistence API and IAM boundary. Clean up abandoned staging objects separately after a safe retention period.

| Object kind | Decoded JSON payload | Reason to preserve |
|---|---|---|
| LAYOUT | Full production `layout` object, including every physical seat | Stable geometry, blocked/accessibility state and pair rules |
| REQUEST | Exact complete production request passed to `solve()` | Reproducible input, including all statuses and event display details |
| RESULT | Full generated/manual result plus plan provenance required by the adapter | Complete diagnostics and repair baseline; no lost output fields |
| WORKSPACE | `{"participants":[...],"items":{"P001":{...}}}` | Exact current staff editing state, including unassigned/docked entries |

The request intentionally embeds its layout and participants even though current registrations/layout also exist. Current records are editable; submitted input must remain frozen. The result retains the solver's own `source_request` and `baseline_snapshot`. These duplicates are deliberate historical snapshots.

### 4.5 Policy registry — UC05–06, UC13

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Policy | pk / sk | S / S | — | Policy version / metadata | `POLICY#pjkit-v3` / `META` |
| Policy | entityType | S | — | Fixed | `SOLVER_POLICY` |
| Policy | policyVersionId | S | — | Immutable version ID | `pjkit-v3` |
| Policy | document | M | Exact policy JSON, see §5 | Copy of validated deployed policy | `{"policy_version_id":"pjkit-v3", ...}` |
| Policy | sha256 | S | — | Canonical policy hash | `<64-hex-digits>` |
| Policy | solverBuildId | S | — | Immutable deployment artifact/version | `git:<commit-sha>` |
| Policy | createdAt / createdBy | N / S | — | Registry provenance | `1790640000000` / `usr_staff_01` |

Current `policy()` reads `config/production_policy.json` from the deployed package. A database policy row does **not** override that code. Initially seed the registry from the deployed file and compare its version/hash before running. A different policy needs a compatible deployment or a deliberate policy-loading refactor. Preference ranks map to enabled weights 40/30/20; these are relative coefficients, not percentages or arbitrary client weights.

### 4.6 Solver job and idempotency — UC06–08, UC13

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Job | pk / sk | S / S | — | Event / job | `EVENT#evt_2026_01` / `JOB#job_01` |
| Job | entityType / eventId | S / S | — | Stream filter discriminator / owner | `SOLVER_JOB` / `evt_2026_01` |
| Job | jobId | S | — | Stable server-generated ID | `job_01` |
| Job | jobStatus | S | — | `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED` | `QUEUED` |
| Job | requestObjectId | S | — | Must refer to a COMMITTED request | `REQUEST#req_01` |
| Job | requestHash | S | — | Must match request manifest | `<64-hex-digits>` |
| Job | generationMode | S | — | Copy of request mode for status display | `REPAIR_PUBLISHED` |
| Job | inputRevision | N, integer | — | Revision frozen at submission | `12` |
| Job | expectedStateRevision / expectedWorkspaceRevision | N / N, integers | — | Guard eventual draft attachment | `20` / `4` |
| Job | expectedPublishedPlanVersionId | S or NULL | — | Pointer at submission, including non-repair jobs | `01JOLDPLAN` |
| Job | baselinePlanVersionId | S or NULL | — | Same pointer for repair; null for other modes | `01JOLDPLAN` |
| Job | solverBuildId / policyHash | S / S | — | Reproducibility and deployed compatibility | `git:<commit-sha>` / `<64-hex-digits>` |
| Job | attempt | N, integer | — | Increment on lease acquisition | `1` |
| Job | leaseToken | S, optional | — | Fences timed-out/stale workers | `lease_01` |
| Job | leaseUntil | N, optional | — | Epoch ms; execution ownership expiry, not TTL | `1790640300000` |
| Job | resultPlanVersionId | S, optional | — | Winning completed output | `01JNEWPLAN` |
| Job | error | M, optional | `code:S`, `message:S`, `details:M`, `solver_status:S or NULL` | Bounded failure summary; overflow in error result object | `{"code":"INVALID_INPUT","message":"...","details":{},"solver_status":null}` |
| Job | errorObjectId | S, optional | — | Full bounded-object error payload if needed | `RESULT#error_job_01` |
| Job | createdAt / createdBy | N / S | — | Submission provenance | `1790640000000` / `usr_staff_01` |
| Job | startedAt / completedAt | N, optional | — | Epoch ms | `1790640001000` |
| Idempotency | pk / sk | S / S | — | Event / hash of actor + client token | `EVENT#evt_2026_01` / `IDEMP#<sha256>` |
| Idempotency | entityType / eventId | S / S | — | Standard ownership | `IDEMPOTENCY` / `evt_2026_01` |
| Idempotency | submissionHash | S | — | Hash of normalized command and expected revisions | `<64-hex-digits>` |
| Idempotency | jobId | S | — | Repeated command returns this job | `job_01` |
| Idempotency | createdAt / createdBy | N / S | — | Submission provenance | `1790640000000` / `usr_staff_01` |

Create queued job and idempotency item in one transaction, conditionally absent, while checking input/configuration revisions. Same token + same submission returns the existing job; same token + different submission is a conflict. A deliberate new solve uses a new token. Infrastructure retries reuse the existing job and immutable request.

### 4.7 Plan and assignment projection — UC08, UC10–14

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Plan | pk / sk | S / S | — | Event / time-sortable plan ID | `EVENT#evt_2026_01` / `PLAN#01JNEWPLAN` |
| Plan | entityType / eventId | S / S | — | Standard ownership | `SEATING_PLAN` / `evt_2026_01` |
| Plan | planVersionId | S | — | Never reused | `01JNEWPLAN` |
| Plan | resultObjectId | S | — | Full COMMITTED result | `RESULT#01JNEWPLAN` |
| Plan | requestObjectId | S | — | Exact source request; manual changes get a new request snapshot | `REQUEST#req_01` |
| Plan | contentHash | S | — | Immutable result hash; adapter validation revision | `<64-hex-digits>` |
| Plan | publicationStatus | S | — | `DRAFT`, `PUBLISHED`, `SUPERSEDED` for current workspace flow | `DRAFT` |
| Plan | projectionState | S | — | `STAGING` or `COMPLETE`; COMPLETE only after assignment verification | `COMPLETE` |
| Plan | assignmentCount | N, integer | — | Number of registration projection records, not seat count | `96` |
| Plan | jobId | S, optional | — | Generated plan provenance | `job_01` |
| Plan | predecessorPlanVersionId / baselinePlanVersionId | S or NULL | — | Editing predecessor / repair baseline | `01JOLDPLAN` / `null` |
| Plan | expectedPublishedPlanVersionId | S or NULL | — | Publication compare-and-swap expectation | `01JOLDPLAN` |
| Plan | inputRevision | N, integer | — | Captured source input revision | `12` |
| Plan | workingRevision | N, integer, optional | — | Workspace revision, if manually published | `4` |
| Plan | solverStatusAtGeneration | S | — | Preserve original OPTIMAL/FEASIBLE provenance | `FEASIBLE` |
| Plan | manuallyModified | BOOL | — | Manual editing must not claim original proof still holds | `true` |
| Plan | createdAt / createdBy | N / S | — | Creation metadata | `1790640000000` / `usr_staff_01` |
| Plan | publishedAt / publishedBy | N / S, optional | — | Set only on explicit publication | `1790640060000` / `usr_staff_01` |
| Assignment | pk / sk | S / S | — | Event+plan / participant | `EVENT#evt_2026_01#PLAN#01JNEWPLAN` / `REG#P001` |
| Assignment | entityType / eventId | S / S | — | Standard ownership | `SEAT_ASSIGNMENT` / `evt_2026_01` |
| Assignment | planVersionId / participantId | S / S | — | Projection identity | `01JNEWPLAN` / `P001` |
| Assignment | registeredName | S | — | Source registration name | `Example Participant` |
| Assignment | allocationType | S | — | `EMPEROR_PAIR` or `SINGLE` | `EMPEROR_PAIR` |
| Assignment | seatIds | L of S | — | Ordered occupant seat IDs | `["R01-S07","R01-S08"]` |
| Assignment | seats | L of M | `seat_id:S`, `row_number:N`, `physical_position:N`, `priority_rank:N`, `zone:S`, `display_name:S` | Exact public seat details projected from completed result | `[{"seat_id":"R01-S07", ...}]` |

The complete result object is canonical; assignment records are an intentional read projection for UC11. Store no financial amounts, categories, activity measures, notes or diagnostic penalties in this projection. Authenticate before returning it. Empty/noneligible registrations have no assignment item; return a generic no-published-assignment response rather than leaking their status.

Stage the result and all assignment records before setting `projectionState=COMPLETE`. Verify exact participant IDs, assignment count, unique valid seat IDs and projection equality with the canonical result. Publication requires both COMMITTED content and COMPLETE projections. Published content/projections are immutable; only lifecycle metadata can change. A repair reads the full result, not the reduced assignment projection.

### 4.8 Workspace payload and audit — UC09–10, UC14

Workspace objects hold the exact `WorkspaceStore` state. The configuration row holds its active pointer, base-plan ID and revision.

| Facet | Attribute / JSON path | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Workspace payload | participants | L of M | Full participant contract | Preserves registration records, including excluded ones | `[{"participant_id":"P001", ...}]` |
| Workspace payload | items | M | Keys are participant IDs | Exactly one entry per participant | `{"P001":{...}}` |
| Workspace item | seat_ids | L of S | — | Empty means dock/unassigned | `["R01-S07","R01-S08"]` |
| Workspace item | display_names | L of S | — | Current normalization repeats payer display name for a pair; registered name unchanged | `["Example Participant","Example Participant"]` |
| Workspace item | name_checked / attendance_confirmed / seat_reviewed / locked | BOOL each | — | Staff markers; locked protects manual movement | `false` |
| Workspace item | companion_absent | BOOL | — | Only Emperor; reason required when true | `true` |
| Workspace item | note / absence_reason / dock_reason | S each | — | Each max 2,000 characters under current validator | `Partner not attending` |
| Workspace item | previous_seat_ids | L of S | — | Prior location for staff state | `["R02-S07","R02-S08"]` |
| Workspace item | changed_at | S or NULL | — | ISO timestamp, if present | `2026-09-29T00:00:00Z` |
| Audit | pk / sk | S / S | — | Event / time + unique ID | `EVENT#evt_2026_01` / `AUDIT#1790640000000#audit_01` |
| Audit | entityType / eventId | S / S | — | Standard ownership | `SEATING_AUDIT` / `evt_2026_01` |
| Audit | action | S | — | e.g. REGISTERED, REGISTRATION_UPDATED, JOB_QUEUED, WORKSPACE_SAVED, PUBLISHED | `PUBLISHED` |
| Audit | actorId / createdAt | S / N | — | Auth identity / epoch ms | `usr_staff_01` / `1790640000000` |
| Audit | planVersionId / jobId / participantId | S, optional each | — | Related entities where applicable | `01JNEWPLAN` |
| Audit | previousObjectId / newObjectId | S, optional each | — | Reference large changes instead of embedding them | `WORKSPACE#ws_01` / `WORKSPACE#ws_02` |
| Audit | revision | N, optional | — | Relevant workspace/input revision | `5` |
| Audit | changes | M, optional | — | Bounded summary only | `{"publishedPlanVersionId":{"from":null,"to":"01JNEWPLAN"}}` |

The current solver request has no `locked` or `companion_absent` fields. They belong to workspace state and published `operations`, not to participant input. Current automatic solving still derives pair demand from tier. Persisting these fields does not make regeneration honor locks or single-seat Emperor attendance; that requires an explicit solver/workspace integration change. Current workspace publication performs basic integrity checks but does not claim a full solver hard-constraint audit for manually edited output.

## 5. Exact nested solver data contract

The following attribute dictionaries use the current `production_request.schema.json` and policy file. Within a JSON payload, `object`, `array`, `string`, `integer`, `number`, `boolean`, and `null` are JSON types; if stored natively they correspond to M, L, S, N, N, BOOL and NULL. The object storage format preserves these types through JSON serialization. All fields marked required must be emitted; nullable required fields must be explicitly null when empty. The request forbids unknown properties.

### 5.1 Request envelope — REQUEST object

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `schema_version` | string | Yes | Fixed `2.0.0` | `"2.0.0"` |
| `event_id` | string | Yes | minLength: 1; Equals the existing Events ID; never a job ID | `"evt_2026_01"` |
| `generation_mode` | string | Yes | `INITIAL`, `REGENERATE_DRAFT`, `REPAIR_PUBLISHED`, `FULL_REGENERATION`; All four values are implemented; mode is chosen by the trusted application | `"INITIAL"` |
| `layout_version_id` | string | Yes | minLength: 1 | `"demo-layout-v1"` |
| `policy_version_id` | string | Yes | Fixed `pjkit-v3` | `"pjkit-v3"` |
| `baseline_plan_version_id` | string or null | Yes | Required null outside REPAIR_PUBLISHED | `null` |
| `preference_profile_version` | string | Yes | Fixed `ranked-v1` | `"ranked-v1"` |
| `preferences` | array of object | Yes | minItems: 3; maxItems: 3; Exactly one of each preference key, in priority order | `[{"key":"contribution_seat","enabled":true},{"key":"activeness","enabled":true},{"key":"category_zone","enabled":true}]` |
| `participants` | array of object | Yes | Include excluded statuses to preserve replacement semantics | `[{"participant_id":"P001","full_name":"Example Participant","registration_status":"CONFIRMED","replacement_for_participant_id":null,"contribution_tier":"MERIT","contribution_amount_rm":3000,"requires_…` |
| `layout` | object | Yes | Full embedded layout, not just its database pointer | `{"layout_version_id":"demo-layout-v1", …}` |
| `solver` | object | Yes | — | `{"max_time_seconds":60, …}` |
| `event_details` | object | No | Optional display snapshot; do not derive event time from solve time | `{"name":"Example Assembly", …}` |

### 5.2 Participant — Registration.participant and request.participants[]

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `participant_id` | string | Yes | minLength: 1; Allocation-unit ID, scoped to event; stable across versions | `"P001"` |
| `full_name` | string | Yes | minLength: 1 | `"Example Participant"` |
| `registration_status` | string | Yes | `CONFIRMED`, `REPLACEMENT_CONFIRMED`, `PENDING`, `WAITLISTED`, `CANCELLED`, `ABSENT`, `REPLACED`; Only CONFIRMED and REPLACEMENT_CONFIRMED receive seats | `"CONFIRMED"` |
| `replacement_for_participant_id` | string or null | Yes | A confirmed replacement uniquely references an original REPLACED record in this event | `null` |
| `contribution_tier` | string | Yes | `EMPEROR`, `MERIT`, `BODHI`; Registered bundle tier; Emperor normally consumes two adjacent approved seats | `"MERIT"` |
| `contribution_amount_rm` | integer | Yes | minimum: 0; Whole RM, meets registered tier minimum; no assumed upper bound | `3000` |
| `requires_accessible_seat` | boolean | Yes | Explicit requirement; do not infer solely from age | `false` |
| `participant_category` | string | Yes | `MONASTIC`, `COMMITTEE`, `VOLUNTEER`, `GENERAL_DEVOTEE` | `"GENERAL_DEVOTEE"` |
| `events_joined_last_2_years` | integer | Yes | minimum: 0; Authoritative as-of snapshot, not a live aggregate queried by solver | `0` |
| `age` | integer | Yes | minimum: 0; maximum: 120; Age at the agreed event/reference date; captured explicitly | `30` |
| `adjacent_person_name` | string or null | Yes | Nullable companion display data, not a second registration | `null` |

### 5.3 Layout — LAYOUT object and request.layout

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `layout_version_id` | string | Yes | minLength: 1; Must equal envelope layout_version_id | `"demo-layout-v1"` |
| `row_count` | integer | Yes | minimum: 1; maximum: 64 | `1` |
| `seats_per_row` | integer | Yes | minimum: 2; maximum: 32 | `4` |
| `aisle_after_position` | integer | Yes | minimum: 1 | `2` |
| `accessible_positions` | array of integer | Yes | Current validator requires positions 1, 2, width−1, width | `[1,2,3,4]` |
| `approved_pairs` | array of array | Yes | Disjoint adjacent physical-position pairs on one side of aisle; reused per row | `[[1,2],[3,4]]` |
| `seats` | array of object | Yes | Every physical position including blocked seats; count equals row_count × seats_per_row | `[{"seat_id":"R01-S01","row_number":1,"row_index":0,"physical_position":1,"priority_rank":4,"side":"LEFT","zone":"LEFT_OUTER","is_accessible":true,"is_blocked":false},{"seat_id":"R01-S02","row_number":…` |

### 5.4 Physical seat — layout.seats[]

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `seat_id` | string | Yes | minLength: 1; Unique and stable within layout lineage | `"R01-S01"` |
| `row_number` | integer | Yes | minimum: 1 | `1` |
| `row_index` | integer | Yes | minimum: 0; Exactly row_number − 1 | `0` |
| `physical_position` | integer | Yes | minimum: 1 | `1` |
| `priority_rank` | integer | Yes | minimum: 1; Relative priority within row; validated between 1 and seats_per_row | `4` |
| `side` | string | Yes | `LEFT`, `RIGHT` | `"LEFT"` |
| `zone` | string | Yes | `LEFT_OUTER`, `LEFT_CENTER`, `RIGHT_CENTER`, `RIGHT_OUTER` | `"LEFT_OUTER"` |
| `is_accessible` | boolean | Yes | — | `true` |
| `is_blocked` | boolean | Yes | Blocked positions remain in geometry and are never assignable | `false` |

### 5.5 Ordered preference — preferences[]

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `key` | string | Yes | `contribution_seat`, `activeness`, `category_zone` | `"contribution_seat"` |
| `enabled` | boolean | Yes | — | `true` |

### 5.6 Solver settings — solver

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `max_time_seconds` | number | Yes | Greater than 0; maximum: 300 | `60` |
| `num_search_workers` | integer | Yes | minimum: 1; maximum: 16 | `8` |
| `random_seed` | integer | Yes | minimum: 0 | `42` |
| `require_optimal` | boolean | Yes | — | `false` |
| `canonicalize` | boolean | Yes | — | `true` |

### 5.7 Event display details — event_details

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `name` | string | Yes | minLength: 1 | `"Example Assembly"` |
| `date` | string or null | Yes | — | `null` |
| `time` | string or null | Yes | — | `null` |
| `timezone` | string | Yes | minLength: 1 | `"Asia/Kuala_Lumpur"` |
| `venue` | string or null | Yes | — | `"Example Hall"` |

### 5.8 Policy document — Policy.document

The current policy schema fixes the entire document with `const`; the fields below are not independently editable settings under the same version ID.

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `policy_version_id` | string | Yes | — | `"pjkit-v3"` |
| `normalization_version` | string | Yes | — | `"desirability-v2"` |
| `tier_order` | array of string | Yes | — | `["EMPEROR","MERIT","BODHI"]` |
| `tier_minimums` | object | Yes | — | `{"EMPEROR":5000,"MERIT":3000,"BODHI":2000}` |
| `rank_weights` | array of number | Yes | Current three ordinary preferences use the first three enabled ranks | `[40,30,20,10]` |
| `initial_packing` | string | Yes | — | `"STRICT"` |
| `repair_local_packing` | boolean | Yes | — | `true` |
| `tier_seat_precedence` | string | Yes | — | `"HARD_ALL_PHYSICAL_SEATS"` |
| `category_zone_costs` | object | Yes | Map category → zone → numeric penalty; copy the entire versioned matrix | `{"MONASTIC":{"RIGHT_CENTER":0,"LEFT_CENTER":2,"RIGHT_OUTER":4,"LEFT_OUTER":8},"COMMITTEE":{"RIGHT_CENTER":0,"LEFT_CENTER":2,"RIGHT_OUTER":3,"LEFT_OUTER":6},"VOLUNTEER":{"RIGHT_CENTER":1,"LEFT_CENTER":…` |

### 5.9 Full result payload — RESULT object

Preserve every key returned by `production.format_result()` and persistence/workspace additions. The following dictionary covers the top-level production output; nested diagnostics are retained losslessly rather than flattened into mutable columns. Exact assignment maps retain all participant fields from §5.2 in addition to the fields below.

| Attribute | JSON type | Remarks | Example |
|---|---|---|---|
| schema_version / status | string each | Result contract / success discriminator | `2.0.0` / `success` |
| run_id / generated_at | string each | Solver run UUID / ISO timestamp | `run-uuid` / `2026-09-29T00:00:00+00:00` |
| event_id / generation_mode | string each | Input provenance | `evt_2026_01` / `INITIAL` |
| policy_version_id / layout_version_id | string each | Exact applied versions | `pjkit-v3` / `demo-layout-v1` |
| preference_profile_version / normalization_version | string each | Preference/scoring versions | `ranked-v1` / `desirability-v2` |
| preferences | array of object | Original ordered preference list | `[{"key":"activeness","enabled":true}, …]` |
| effective_weights | object of numbers | Derived enabled coefficients by preference | `{"contribution_seat":40,"activeness":30,"category_zone":20}` |
| source_request | object | Complete §5.1 request | `{"schema_version":"2.0.0", …}` |
| baseline_snapshot | object or null | plan_version_id, event_id, policy_version_id, source_request and assignments of repair baseline | `null` |
| manually_modified | boolean | True only for manually edited output | `false` |
| publication_status | string | Adapter overlays current lifecycle state from plan metadata | `DRAFT` |
| solver_status_at_generation | string | Retain original solver provenance after edits | `OPTIMAL` |
| solver | object | Status, timings, search statistics, proof and canonicalization flag | `{"status":"FEASIBLE", …}` |
| quality | object | Complete computed penalties and quality diagnostics | `{"penalties":{"P001":{…}}, …}` |
| input_summary | object of integer counts | Submitted/eligible/excluded registrations, units, primary participants, tier counts, required/total/available/blocked/empty seats | `{"required_seat_count":1, …}` |
| weights | object of numbers | Legacy-compatible priority_seat_weight, activeness_weight, category_zone_weight, movement_weight | `{"priority_seat_weight":40,"activeness_weight":30,"category_zone_weight":20,"movement_weight":0}` |
| constraint_config | object | enforce_front_fill, enforce_middle_fill, normalize_penalties booleans; normalization_scale number | `{"enforce_front_fill":true,"enforce_middle_fill":true,"normalize_penalties":true,"normalization_scale":100}` |
| penalty_summary | object | unweighted, normalized and weighted maps | `{"weighted":{"total":0, …}, …}` |
| tier_bands | object of integer arrays | Rows used by each tier, including shared boundary rows | `{"EMPEROR":[],"MERIT":[1],"BODHI":[]}` |
| floor_plan | object | row_count, seats_per_row, aisle_after_position, total_seats and rows[] | `{"row_count":1,"total_seats":4, …}` |
| floor_plan.rows[].seats[] | object | Physical seat fields plus occupancy_status, participant_id, display_name, tier and section | `{"seat_id":"R01-S01","occupancy_status":"EMPTY", …}` |
| assignments | array of object | Full participant fields; is_monk/is_elderly booleans; allocation_type string; seat_ids string array; seats object array; pair_priority number/null; previous_seat_ids string array; moved boolean/null; penalty object | `[{"participant_id":"P001","seat_ids":["R01-S03"], …}]` |
| empty_seat_ids | array of string | Assignable vacant positions | `["R01-S01","R01-S02","R01-S04"]` |
| excluded_participants | array of object | participant_id and reason strings | `[{"participant_id":"P002","reason":"ABSENT"}]` |
| unassigned_participants | array | Empty for a successful complete solve | `[]` |
| hard_constraint_validation | object | Solver: all_constraints_satisfied BOOL, duplicate_seat_count N, unassigned_count N; current manual flow: checked BOOL=false | `{"all_constraints_satisfied":true,"duplicate_seat_count":0,"unassigned_count":0}` |
| plan_version_id / predecessor_plan_version_id | string / string or null | Added by persistence; identity / lineage | `01JNEWPLAN` / `null` |
| expected_published_version_id | string or null | Added by persistence; stale publication check | `null` |
| created_at | string | Persistence ISO timestamp | `2026-09-29T00:00:00+00:00` |
| operations | object, optional | Published workspace items keyed by participant ID; §4.8 | `{"P001":{"locked":true, …}}` |
| working_revision | integer, optional | Exact published staff revision | `4` |

Map plan metadata to API fields `validation_revision`, `created_by`, `published_by`, `published_at` and current `publication_status` when loading. Convert host epoch timestamps to the expected ISO strings. This avoids modifying hashed historical JSON when its lifecycle changes. Older approval API fields may be returned as null unless that workflow is deliberately restored. Errors use `{"schema_version":"2.0.0","status":"error","error":{"code":string,"message":string,"details":object,"solver_status":string|null}}`.


### 5.10 Complete example passed to Python

This is a small, fictitious one-row example to demonstrate every field. It is not the production hall. The stored REQUEST object decodes to exactly this shape, without DynamoDB keys or job fields.

```json
{
  "schema_version": "2.0.0",
  "event_id": "evt_2026_01",
  "generation_mode": "INITIAL",
  "layout_version_id": "demo-layout-v1",
  "policy_version_id": "pjkit-v3",
  "baseline_plan_version_id": null,
  "preference_profile_version": "ranked-v1",
  "preferences": [
    {
      "key": "contribution_seat",
      "enabled": true
    },
    {
      "key": "activeness",
      "enabled": true
    },
    {
      "key": "category_zone",
      "enabled": true
    }
  ],
  "participants": [
    {
      "participant_id": "P001",
      "full_name": "Example Participant",
      "registration_status": "CONFIRMED",
      "replacement_for_participant_id": null,
      "contribution_tier": "MERIT",
      "contribution_amount_rm": 3000,
      "requires_accessible_seat": false,
      "participant_category": "GENERAL_DEVOTEE",
      "events_joined_last_2_years": 0,
      "age": 30,
      "adjacent_person_name": null
    }
  ],
  "layout": {
    "layout_version_id": "demo-layout-v1",
    "row_count": 1,
    "seats_per_row": 4,
    "aisle_after_position": 2,
    "accessible_positions": [
      1,
      2,
      3,
      4
    ],
    "approved_pairs": [
      [
        1,
        2
      ],
      [
        3,
        4
      ]
    ],
    "seats": [
      {
        "seat_id": "R01-S01",
        "row_number": 1,
        "row_index": 0,
        "physical_position": 1,
        "priority_rank": 4,
        "side": "LEFT",
        "zone": "LEFT_OUTER",
        "is_accessible": true,
        "is_blocked": false
      },
      {
        "seat_id": "R01-S02",
        "row_number": 1,
        "row_index": 0,
        "physical_position": 2,
        "priority_rank": 2,
        "side": "LEFT",
        "zone": "LEFT_CENTER",
        "is_accessible": true,
        "is_blocked": false
      },
      {
        "seat_id": "R01-S03",
        "row_number": 1,
        "row_index": 0,
        "physical_position": 3,
        "priority_rank": 1,
        "side": "RIGHT",
        "zone": "RIGHT_CENTER",
        "is_accessible": true,
        "is_blocked": false
      },
      {
        "seat_id": "R01-S04",
        "row_number": 1,
        "row_index": 0,
        "physical_position": 4,
        "priority_rank": 3,
        "side": "RIGHT",
        "zone": "RIGHT_OUTER",
        "is_accessible": true,
        "is_blocked": false
      }
    ]
  },
  "solver": {
    "max_time_seconds": 60,
    "num_search_workers": 8,
    "random_seed": 42,
    "require_optimal": false,
    "canonicalize": true
  },
  "event_details": {
    "name": "Example Assembly",
    "date": null,
    "time": null,
    "timezone": "Asia/Kuala_Lumpur",
    "venue": "Example Hall"
  }
}
```

## 6. Access patterns and GSI justification

| Use case | DynamoDB operation / key condition | Index required? |
|---|---|---|
| Load event | Events GetItem: `pk=eventId AND sk=meta` | No |
| Load configuration | Seating GetItem: `pk=E AND sk=CONFIG` | No |
| List event registrations | Query: `pk=E AND begins_with(sk,'REG#')` | No |
| Resolve imported bundle | GetItem: `pk=E AND sk=SOURCE#hash` | No |
| Find contributions to import | Offerings Query existing GSI: `eventId=:sourceEventId`, ordered by `serialNo` | Existing index only; base key is payer/invoice and cannot query by event |
| Find my registrations | Query: `pk=USER#verifiedUser AND begins_with(sk,'EVENT#eventId#REG#')` | No; explicit relationship records |
| Load layout/request/result/workspace | Get manifest; Query object PK with `begins_with(sk,'PART#')` | No |
| Poll job | GetItem: `pk=E AND sk=JOB#jobId` | No |
| List jobs for this event | Query: `pk=E AND begins_with(sk,'JOB#')`; sort bounded results by createdAt if needed | No chronological job-list index promised |
| List plan history | Query: `pk=E AND begins_with(sk,'PLAN#')`, `ScanIndexForward=false` | No; time-sortable plan IDs |
| Read my published seats | Get CONFIG → Get PLAN metadata → Get assignment by event+plan+participant | No |
| Load staff hall | Get CONFIG → PLAN → RESULT manifest/parts | No |
| Read audit history | Query: `pk=E AND begins_with(sk,'AUDIT#')`, descending | No |

**No new GSI is justified by UC01–UC14.** Do not add a `status` GSI merely because a status attribute exists. Do not use the existing Events status GSI to track solver jobs. This separate table avoids accidentally populating the workbook's Events type/status indexes with job or plan rows.

Use strongly consistent base-table reads for publication pointers, manifests, snapshot capture and immediate status checks. Existing Offerings GSI import discovery is eventually consistent: reconcile from authoritative source keys and explicit import completion before allowing a solve; a GSI query alone cannot certify a complete latest registration snapshot. [AWS read consistency](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)

Paginate every Query until `LastEvaluatedKey` is absent, including object parts and registrations. A Query page is at most 1 MB. [AWS pagination](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html)

**Future index only if a new requirement appears:** a global operations dashboard/reaper that discovers overdue jobs across all events could justify a sparse `JobsDue` GSI with String PK `JOBDUE#<bucket>` and Number SK `nextCheckAt` in epoch ms; project base keys, eventId, jobId and jobStatus. Only QUEUED/RUNNING jobs carry these attributes; remove them on completion. Query every configured bucket up to the current time and recheck the base job conditionally because GSI reads can lag. This is not required for event-scoped polling or configured stream retry/on-failure recovery and is not part of the initial table definition.

## 7. Consistent snapshots, Lambda trigger and persistence

### 7.1 Capture the exact input

1. Authorize the administrator for the existing event. Read CONFIG strongly, recording input/state/workspace revisions and the current published pointer.
2. Query all event registrations strongly and load the committed layout and compatible policy. Every registration write and every configuration change affecting solver input must increment `inputRevision` in the same transaction as that change. This includes updates to snapshotted event display details. Copy source Events changes through this controlled adapter; do not read mutable Events fields halfway through building a request.
3. Read CONFIG again. If `inputRevision` changed, discard the mixed snapshot and retry. Strong individual reads alone do not provide a multi-item snapshot. Include all registration statuses, not only eligible people; replacement validation needs original REPLACED records.
4. Construct and validate the request, stage/commit its immutable object, then transact: condition-check unchanged input/state/workspace revisions and expected published pointer; put absent idempotency row; put absent QUEUED job; append audit. A failed condition leaves an unreferenced object, never a submitted mixed-version request.
5. For repair, capture the server's published pointer as `baseline_plan_version_id`; reject repair without a published plan. For INITIAL, REGENERATE_DRAFT and FULL_REGENERATION set it to null. Validate the same event, compatible policy and geometry before solving.

### 7.2 Trigger only explicit job submission

Configure a Lambda event-source mapping on Seating Streams with `NEW_IMAGE`, filtering **INSERT** records whose `entityType` is `SOLVER_JOB` and `jobStatus` is `QUEUED`. Store result/part/configuration changes without triggering another solve. Example filter pattern:

```json
{
  "eventName": ["INSERT"],
  "dynamodb": {
    "NewImage": {
      "entityType": {"S": ["SOLVER_JOB"]},
      "jobStatus": {"S": ["QUEUED"]}
    }
  }
}
```

The stream delivers a job reference in DynamoDB AttributeValue format, not a complete Python request. The handler deserializes it, strongly loads the current job, claims it conditionally and loads the request object. [AWS stream filtering](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.Lambda.Tutorial2.html)

### 7.3 Worker contract and retry handling

Use a conditional update to claim QUEUED, or RUNNING with an expired lease, assigning a new `leaseToken`, incrementing `attempt`, and setting `leaseUntil`. A completed job is a no-op on redelivery. An unexpired RUNNING job should remain retryable; do not acknowledge and discard its only outstanding retry after a previous worker timed out. Fence every completion transaction against the current lease token and RUNNING status.

Streams/Lambda delivery is at least once, so duplicate execution is possible; the target is one accepted completion, not a claim of exactly-once computation. Configure bounded retries, partial batch failure reporting, batch size 1 initially for CPU-heavy work, and an on-failure destination with a redrive worker/runbook. Redrive invokes the existing job ID; changing it to QUEUED alone will not trigger the INSERT-only mapping. [AWS delivery behavior](https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html)

Conceptual handler core (adapter functions still need implementation):

```python
from seat_solver.production.policy import validate_request
from seat_solver.production.production import solve
from seat_solver.production.production_validator import audit_result

job, lease_token = claim_job(event_id, job_id)
request = load_committed_json(event_id, job["requestObjectId"])
verify_request_hash_and_deployed_policy(job, request)
validate_request(request)

baseline = None
if request["generation_mode"] == "REPAIR_PUBLISHED":
    # Captured by the trusted server at submission, not supplied by the browser.
    baseline = load_plan_result(event_id, job["baselinePlanVersionId"])

result = solve(request, baseline)
if result["status"] == "success":
    report = audit_result(result)
    if not report["passed"]:
        fail_job_conditionally(job, lease_token, report)
    else:
        stage_and_commit_plan(job, lease_token, result)
else:
    fail_job_conditionally(job, lease_token, result["error"])
```

Import `solve` directly. Do not invoke the existing `service.dispatch` unchanged: it constructs the SQLite PlanStore and is not a DynamoDB Lambda handler. Package Python modules, schemas, versioned policy and a Linux-compatible OR-Tools build. Convert native DynamoDB Decimal values to validated integers/finite numbers before passing or JSON-serializing them; do not send low-level `{"S":...}` wrappers to the solver.

Persist successful output and assignment projections first; then transact the plan's completion state, job SUCCEEDED/result pointer, and completion audit with the lease condition. A stale worker may leave unreferenced staging output but cannot win completion. Attach the new draft pointer separately with expected input/configuration/workspace revisions and the captured published pointer; if staff have edited or published meanwhile, retain the completed plan in history and ask them to explicitly load it through the application. Never overwrite their saved workspace. Infrastructure exceptions remain retryable; validated domain errors become FAILED with diagnostics. Neither failures nor successful generation publish a plan.

For ordinary Lambda execution, the configurable timeout is at most 900 seconds. Reserve time for input reads, independent validation and writes; benchmark the complete solve path, not just one CP-SAT phase. The current solver can perform multiple optimization/canonicalization phases. Set bounded concurrency and CPU/memory settings based on measured runtime. If realistic solves exceed the ordinary Lambda budget, keep this storage contract and move execution to a longer-running worker. [AWS Lambda timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html)

### 7.4 Workspace saves and atomic publication

Saving edits validates the full state against the base plan, stages a new WORKSPACE object, then transactionally updates CONFIG only if the submitted workspace revision and base plan still match. Increment workspace/state revisions and append audit. This avoids a partially saved multi-item workspace and supports more than 100 registrations.

Publication builds a new immutable manual snapshot from the exact saved workspace, preserving `operations`, source request and original generation provenance. It sets `manually_modified=true`, labels current solver status `MANUALLY_MODIFIED`, and preserves the current workspace behavior `hard_constraint_validation={"checked":false}`. Validate basic draft integrity and require every attending registration to have assigned seats. Do not mark it solver-audited unless an additional full audit is actually implemented and passed.

After content and assignments are complete, one small `TransactWriteItems` operation:

1. Updates CONFIG conditioned on exact workspace revision/base, expected published pointer, and any relevant input revision; sets the new published/latest pointers, advances workspace revision, and points its base at the new plan.
2. Updates the new plan from DRAFT to PUBLISHED, conditioned on expected content hash and COMPLETE projections.
3. Updates the old published plan to SUPERSEDED, conditioned on its previous status, when one exists.
4. Appends the publication audit item.

Place conditions on the same Update action for an item rather than adding a separate ConditionCheck on that same item. All content remains immutable while lifecycle metadata is overlaid when reconstructing API responses. Participant reads first resolve a single published pointer and then use that version throughout the response, so a concurrent publish returns a complete old or complete new plan.

DynamoDB transactions are limited to 100 distinct items and 4 MB. Do not attempt to publish every seat/registration in the pointer-switch transaction; staged immutable content plus a small commit transaction is deliberate. [AWS transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)

The repository retains older `submit/approve/publish` PlanStore commands, but the current workspace UI publishes saved revisions directly. This proposal models that current flow. If the approval workflow is restored, add UNDER_REVIEW/APPROVED/REJECTED states and actor/time/approved-content-hash fields, with approval tied to the exact immutable content hash.

## 8. Implementation checklist and acceptance criteria

1. Provision Seating with String `pk`/`sk`, no new index, Streams and worker configuration. Add the optional Events metadata fields through the application.
2. Implement import mappings and missing registration-data collection. Establish authoritative event/participant identities, invoice eligibility and whole-ringgit handling. Do not copy Auth credentials/tokens to Seating or into Lambda payloads.
3. Seed policy registry from the deployed policy file; import the actual hall as a committed LAYOUT object. Register all physical positions including blocked seats.
4. Implement the conditional DynamoDB persistence adapter, canonical JSON object reader/writer, and host request assembler. Port PlanStore/WorkspaceStore semantics, including public-data filtering, rather than replacing SQLite calls mechanically.
5. Implement job submission, stream worker, leases, idempotency, failure redrive and explicit draft attachment. The application polls the persisted job and then loads its resulting plan.
6. Implement immutable manual snapshots, assignment projections and atomic publication; retain old versions required by audit and repair. Do not TTL-delete referenced content.
7. Verify duplicate stream records, worker timeout/reclaim, simultaneous registration edits, two staff saves, stale repair/publication pointers, fractional contributions, incomplete object writes, multi-page reads and outputs exceeding 400 KB. A failed or incomplete solve must leave the public plan unchanged.
8. Verify a real reconstructed request against the current JSON schema and `validate_request`, run `solve(request, baseline)` and its independent audit, then verify that participant responses expose only their permitted identity/seat data and anonymous hall occupancy.

The schema is a design deliverable. It does not provision AWS resources or change the current solver's mathematical behavior.

## 9. Source references

- **Reference workbook:** `Database Structure.xlsx`; Offerings sheet A3:H104 (table keys, invoice/bundle data and existing event GSI); Auth sheet A2:E66 (identity schema); Events v2 sheet A3:H32 (event keys, metadata, indexes, locale/statistics/history conventions). Workbook contents were treated as schema evidence, not operational instructions.
- [Production request JSON schema](../schemas/production_request.schema.json), [layout schema](../schemas/production_layout.schema.json), and [policy schema](../schemas/production_policy.schema.json).
- [Production solve and result construction](../src/seat_solver/production/production.py), [domain validation](../src/seat_solver/production/policy.py), and [deployed policy](../config/production_policy.json).
- [Current workspace state and publication behavior](../src/seat_solver/production/workspace.py), [local PlanStore](../src/seat_solver/production/plan_store.py), and [service adapter](../src/seat_solver/production/service.py).
- [Current README](../README.md) and [integration notes](integration.md). Where older approval-flow prose differs from the workspace implementation, the current workspace code is the basis of this proposal.
- AWS documentation links alongside relevant design decisions were checked on 29 September 2026.
