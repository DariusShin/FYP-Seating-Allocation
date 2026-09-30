# Event seating allocation — DynamoDB schema proposal

This proposal adds seating allocation to the main application's event domain. It follows the reference workbook's **Facet → Attribute → Type → Sub-attribute → Remarks → Example** representation. It describes infrastructure to create and integration work to implement; the repository currently uses SQLite (`output/paid-seats-v4.sqlite3`) and a synchronous Python process adapter, not a deployed DynamoDB/Lambda service. The DynamoDB design below is a target architecture, not a description of the running application.

## Requirement correction: paid seats and verification

A confirmed paid registration retains its name and full seat entitlement regardless of attendance. Emperor remains a two-seat unit. No attendance, absence, replacement-link, allocation-lock or staff-checkbox fields are stored in the current production contract. Manual moves and a temporary dock remain; publication must contain every paid registration. Preference changes may generate a new private draft, never automatically publish it.

Objective 2 now proposes explainable server-side safeguard verification. A future `VERIFICATION` facet would bind findings to an immutable workspace object/hash, exact workspace revision, input revision and policy version, with `PASSED`/`FAILED`, rule IDs, affected registrations/seats, verifier version and timestamp. Publication would condition-check that exact verification reference and revision. This facet and full manual business-rule gate are **planned**, not implemented by the current local store.

Local development uses the fresh `output/paid-seats-v4.sqlite3`; the previous database is preserved. Production policy is `pjkit-v4`. Existing archived records must not be silently imported into this contract. The local implementation has no DynamoDB table, event registration import, stream-triggered job, or full manual-plan safeguard verification yet.

## 1. Use cases

| ID | Actor and use case | Data required | Storage facets | Access pattern |
|---|---|---|---|---|
| UC01 | Administrator enables seating for an event | Existing event, offering-event mapping, seating configuration | Events metadata; Seating configuration | Get event by its existing key; get configuration |
| UC02 | Staff imports or updates seating registrations | Selected contribution bundle, registered person, status, category, accessibility, activity, age | Registration; contribution link | Query registrations for event; get/update one registration; exact source lookup |
| UC04 | Administrator defines the hall | Dimensions, physical seats, blocked positions, pairs, accessibility | Layout object | Get immutable layout by event and version |
| UC05 | Administrator orders/enables solver preferences | Ordered preferences, policy version, solver settings | Configuration; policy | Read/update configuration with revision check |
| UC06 | Administrator generates or regenerates a draft | Consistent registration/layout/configuration snapshot | Request object; job; idempotency record | Commit request; insert queued job; trigger Lambda |
| UC07 | Staff polls a solve or retries a failed infrastructure attempt | Job status, lease, attempt, error, resulting plan | Job | Exact get by event and job; conditional state changes |
| UC08 | Staff loads a generated draft and views its diagnostics | Assignments, quality, solver proof/status, source request | Plan; result object; assignment | Get plan/result; query assignments |
| UC09 | Staff saves manual moves, display names, notes or dock state | Complete working state, base plan and monotonic revision | Workspace object; configuration; audit | Stage immutable state, conditionally advance workspace pointer |
| UC10 | Staff publishes the exact saved revision | Completed result, expected published pointer, workspace revision | Plan; configuration; assignment; audit | Small transaction switches pointers after all content exists |
| UC11 | Participant views their own published seat | Signed identity, event registration mapping, published pointer | Identity link; configuration; assignment | Exact key reads; no participant/contribution table scan |
| UC12 | Staff displays or prints the published hall | Published result with seat/display metadata | Configuration; plan; result object | Resolve pointer and load immutable result |
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

The workbook does not define seating registration status, accessibility needs, participant category, activity count, age or companion name. Collect/verify these through registration or staff entry. Attendance does not determine paid seat entitlement. Resolve the correct paid registration and display name from the contribution source, independently of physical attendance.

### 2.2 Relational-database mental model

Treat `Seating` as one physical table that stores many **record types** (called facets here), rather than as one SQL table per entity. Every item has the same two key columns, `pk` and `sk`; `entityType` tells the application what kind of row it is. A key pair identifies exactly one item.

| Relational concept | DynamoDB equivalent in this proposal |
|---|---|
| Table | Physical `Seating` table (plus the existing host tables) |
| Row / record | One DynamoDB item, such as one `REGISTRATION` or one `SOLVER_JOB` |
| Primary key | Composite `(pk, sk)`, not a generated SQL row number |
| Parent/child relationship | Key values repeated or referenced in ordinary attributes; DynamoDB does not enforce foreign keys |
| `WHERE event_id = ?` | `Query` one partition using `pk=EVENT#...`; sort-key prefixes select the relevant record family |
| Join | Usually several known-key `GetItem`/`Query` calls in application code, or a prewritten read projection such as `Assignment` |
| Transaction | Conditional `TransactWriteItems` for a bounded set of items; not an arbitrary multi-table SQL transaction |
| Large JSON column | Immutable object manifest plus ordered `PART#...` items, reassembled and hash-checked by the adapter |

The `#` text is a naming convention inside String keys, not a special DynamoDB feature. The application constructs the full key and checks referenced IDs, object hashes, revisions and permissions. A `Query` reads one partition efficiently; it cannot query arbitrary attributes such as `eventId` unless an index is explicitly designed for that access pattern. This proposal intentionally starts without a Seating GSI.

### 2.3 Existing workbook changes and project boundary

The reference workbook is a design source; this repository does not contain `Database Structure.xlsx` (the checked-in spreadsheets are unrelated FYP/Gantt/layout files). Therefore the precise deployed key names and workbook cells cannot be independently re-verified here. Based on the workbook conventions recorded above, do **not** replace or reshape the existing `Auth`, `Offerings`, or `Events` tables. Make only these planned changes:

1. Provision the new `Seating` table with String `pk` and `sk`, on-demand capacity, point-in-time recovery and a `NEW_IMAGE` stream; no new GSI is currently justified.
2. Optionally extend an existing `Events` `meta` item with `seatingEnabled`, `offeringEventId` and `seatingSchemaVersion`. Preserve the existing event ID, `pk`/`sk`, GSIs and unrelated locale/statistics records.
3. Reuse the existing Offerings event-discovery GSI if its deployed key attributes really are `eventId` and `serialNo`; confirm that in the deployed table before writing the importer. Do not add a duplicate index without evidence.
4. Reuse the existing Auth identity/role source. Add no credentials or seating fields to Auth. Create a `Seating` identity-link item only for an explicitly verified user-to-registration relationship.

These are deployment changes, not changes required by the current SQLite demo. The current project's solver schemas (`schemas/production_request.schema.json`, layout and policy schemas) remain the solver contract; the proposed storage envelope/records do not replace them. Confirm actual workbook and deployed-table details with the host system owner before applying migrations.

### 2.4 Additions to Events metadata — UC01

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

### 3.2 Plain-JSON relationship map

This is illustrative, ordinary JSON—not DynamoDB's low-level `{"S": ...}` AttributeValue format. Each entry in `Seating.items` is one item in the same physical `Seating` table; its `pk` and `sk` identify it. References are application-checked links, not enforced foreign keys. Host table keys below are examples and must be checked against the deployed workbook/system. The example combines related records from different workflow moments to show their links; it is not a single atomic snapshot (a newly initialized config has null plan pointers).

```json
{
  "hostTables": {
    "Events": [
      {
        "pk": "evt_2026_01",
        "sk": "meta",
        "offeringEventId": "202507LH",
        "seatingEnabled": true,
        "seatingSchemaVersion": 1
      }
    ],
    "Offerings": [
      {
        "pk": "payer-example",
        "sk": "A00001",
        "eventId": "202507LH",
        "bundleId": "bundle_01",
        "unitId": "1",
        "registeredName": "Example Participant",
        "tier": "merit"
      }
    ],
    "Auth": [
      {
        "pk": "USER#usr_01",
        "sk": "PROFILE",
        "role": "participant"
      }
    ]
  },
  "Seating": {
    "physicalTable": "Seating",
    "items": [
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "CONFIG",
        "entityType": "SEATING_CONFIG",
        "eventId": "evt_2026_01",
        "registrationPrefix": "REG#",
        "activeLayoutObjectId": "LAYOUT#layout_v1",
        "policyVersionId": "pjkit-v4",
        "inputRevision": 1,
        "stateRevision": 0,
        "workspaceRevision": 0,
        "workspaceObjectId": null,
        "latestPlanVersionId": "01JPLANEXAMPLE",
        "publishedPlanVersionId": "01JPLANEXAMPLE"
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "REG#P001",
        "entityType": "REGISTRATION",
        "eventId": "evt_2026_01",
        "participant": {
          "participant_id": "P001",
          "full_name": "Example Participant",
          "registration_status": "CONFIRMED",
          "contribution_tier": "MERIT",
          "contribution_amount_rm": 3000,
          "requires_accessible_seat": false,
          "participant_category": "GENERAL_DEVOTEE",
          "events_joined_last_2_years": 0,
          "age": 30,
          "adjacent_person_name": null
        },
        "source": {
          "table": "Offerings",
          "pk": "payer-example",
          "sk": "A00001",
          "bundleId": "bundle_01",
          "unitId": "1"
        },
        "revision": 1
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "SOURCE#<sha256-of-canonical-source-tuple>",
        "entityType": "CONTRIBUTION_LINK",
        "eventId": "evt_2026_01",
        "participantId": "P001",
        "registrationKey": "REG#P001"
      },
      {
        "pk": "USER#usr_01",
        "sk": "EVENT#evt_2026_01#REG#P001",
        "entityType": "IDENTITY_LINK",
        "eventId": "evt_2026_01",
        "participantId": "P001"
      },
      {
        "pk": "EVENT#evt_2026_01#OBJECT#REQUEST#req_01",
        "sk": "META",
        "entityType": "OBJECT_MANIFEST",
        "eventId": "evt_2026_01",
        "objectId": "REQUEST#req_01",
        "objectKind": "REQUEST",
        "storageState": "COMMITTED",
        "partCount": 1,
        "sha256": "<sha256-of-canonical-request-bytes>"
      },
      {
        "pk": "EVENT#evt_2026_01#OBJECT#REQUEST#req_01",
        "sk": "PART#000000",
        "entityType": "OBJECT_PART",
        "eventId": "evt_2026_01",
        "partIndex": 0,
        "data": "<binary-request-json>"
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "IDEMP#<sha256-of-actor-and-client-token>",
        "entityType": "IDEMPOTENCY",
        "eventId": "evt_2026_01",
        "submissionHash": "<sha256-of-normalized-command>",
        "jobId": "job_01"
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "JOB#job_01",
        "entityType": "SOLVER_JOB",
        "eventId": "evt_2026_01",
        "jobStatus": "SUCCEEDED",
        "requestObjectId": "REQUEST#req_01",
        "resultPlanVersionId": "01JPLANEXAMPLE"
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "PLAN#01JPLANEXAMPLE",
        "entityType": "SEATING_PLAN",
        "eventId": "evt_2026_01",
        "planVersionId": "01JPLANEXAMPLE",
        "requestObjectId": "REQUEST#req_01",
        "resultObjectId": "RESULT#01JPLANEXAMPLE",
        "publicationStatus": "PUBLISHED",
        "projectionState": "COMPLETE"
      },
      {
        "pk": "EVENT#evt_2026_01#OBJECT#RESULT#01JPLANEXAMPLE",
        "sk": "META",
        "entityType": "OBJECT_MANIFEST",
        "eventId": "evt_2026_01",
        "objectId": "RESULT#01JPLANEXAMPLE",
        "objectKind": "RESULT",
        "storageState": "COMMITTED",
        "partCount": 1,
        "sha256": "<sha256-of-canonical-result-bytes>"
      },
      {
        "pk": "EVENT#evt_2026_01#PLAN#01JPLANEXAMPLE",
        "sk": "REG#P001",
        "entityType": "SEAT_ASSIGNMENT",
        "eventId": "evt_2026_01",
        "planVersionId": "01JPLANEXAMPLE",
        "participantId": "P001",
        "registeredName": "Example Participant",
        "allocationType": "SINGLE",
        "seatIds": ["R01-S07"]
      },
      {
        "pk": "EVENT#evt_2026_01",
        "sk": "AUDIT#1790640000000#audit_01",
        "entityType": "SEATING_AUDIT",
        "eventId": "evt_2026_01",
        "action": "PUBLISHED",
        "actorId": "usr_staff_01",
        "planVersionId": "01JPLANEXAMPLE",
        "createdAt": 1790640000000
      }
    ]
  }
}
```

The config pointer links to the plan; that plan references the immutable request and result; assignment items are keyed under that plan; registration/source-link items map back to the contribution record. Layout and policy objects are omitted from this shortened example but follow the same layout described in §3 and §4.4–4.5. In live writes, publication pointer, plan status and audit are changed in one conditional transaction—the JSON above is a relationship illustration, not a claim that these records were written atomically together.

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
| Configuration | policyVersionId | S | — | Current code supports this policy only | `pjkit-v4` |
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

Create registration + unique source link + increment `inputRevision` in one transaction. On repeated import, resolve the link and update the existing registration conditionally. Never silently create a second allocation for the same bundle/unit. Upstream payment/registration changes need an explicit import policy; attendance changes must never update seat entitlement. The seating workspace cannot add, remove or change registrations.

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

The solver returns repeated layout and source-request data plus diagnostics. Store complete JSON without assuming it fits in one item. Use the same bounded object representation for all four large document kinds. This keeps every required durable payload in DynamoDB, with no required S3 dependency.

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
| RESULT | Full generated/manual result plus plan provenance required by the adapter | Complete diagnostics and immutable source request; no lost output fields |
| WORKSPACE | `{"participants":[...],"items":{"P001":{...}}}` | Exact current staff editing state, including unassigned/docked entries |

The request intentionally embeds its layout and participants even though current registrations/layout also exist. Current records are editable; submitted input must remain frozen. The result retains the solver's own `source_request`. These duplicates are deliberate historical snapshots.

### 4.5 Policy registry — UC05–06, UC13

| Facet | Attribute | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Policy | pk / sk | S / S | — | Policy version / metadata | `POLICY#pjkit-v4` / `META` |
| Policy | entityType | S | — | Fixed | `SOLVER_POLICY` |
| Policy | policyVersionId | S | — | Immutable version ID | `pjkit-v4` |
| Policy | document | M | Exact policy JSON, see §5 | Copy of validated deployed policy | `{"policy_version_id":"pjkit-v4", ...}` |
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
| Job | generationMode | S | — | Copy of request mode for status display; currently `INITIAL` or `REGENERATE_DRAFT` | `INITIAL` |
| Job | inputRevision | N, integer | — | Revision frozen at submission | `12` |
| Job | expectedStateRevision / expectedWorkspaceRevision | N / N, integers | — | Guard eventual draft attachment | `20` / `4` |
| Job | expectedPublishedPlanVersionId | S or NULL | — | Pointer at submission, for concurrency control | `01JOLDPLAN` |
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
| Plan | predecessorPlanVersionId | S or NULL | — | Editing predecessor; not a solver input | `01JOLDPLAN` |
| Plan | expectedPublishedPlanVersionId | S or NULL | — | Publication compare-and-swap expectation | `01JOLDPLAN` |
| Plan | inputRevision | N, integer | — | Captured source input revision | `12` |
| Plan | workingRevision | N, integer, optional | — | Workspace revision, if manually published | `4` |
| Plan | solverStatusAtGeneration | S | — | Preserve original OPTIMAL/FEASIBLE provenance | `FEASIBLE` |
| Plan | manuallyModified | BOOL | — | Manual editing must not claim original proof still holds | `true` |
| Plan | verificationId | S, optional | — | Planned Objective 2: immutable verification bound to the exact published workspace/hash and captured revisions; absent until implemented | `VERIFY#ver_01` |
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

Stage the result and all assignment records before setting `projectionState=COMPLETE`. Verify exact participant IDs, assignment count, unique valid seat IDs and projection equality with the canonical result. Publication requires both COMMITTED content and COMPLETE projections. Published content/projections are immutable; only lifecycle metadata can change. History reads the full result, not the reduced assignment projection.

### 4.8 Workspace payload and audit — UC09–10, UC14

Workspace objects hold the exact `WorkspaceStore` state. The configuration row holds its active pointer, base-plan ID and revision.

| Facet | Attribute / JSON path | Type | Sub-attribute | Remarks | Example |
|---|---|---|---|---|---|
| Workspace payload | participants | L of M | Full participant contract | Preserves registration records, including excluded ones | `[{"participant_id":"P001", ...}]` |
| Workspace payload | items | M | Keys are participant IDs | Exactly one entry per participant | `{"P001":{...}}` |
| Workspace item | seat_ids | L of S | — | Empty means dock/unassigned | `["R01-S07","R01-S08"]` |
| Workspace item | display_names | L of S | — | Current normalization repeats payer display name for a pair; registered name unchanged | `["Example Participant","Example Participant"]` |
| Workspace item | note / dock_reason | S each | — | Staff note / temporary manual placement reason; max 2,000 characters | `Awaiting manual placement` |
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

Workspace metadata contains only seat_ids, display_names, note, dock_reason, previous_seat_ids and changed_at. Server checks preserve the full paid allocation, valid pairs, accessibility, immutable registration records and unique valid seats. Docked registrations prevent publication. A complete manual contribution-order/packing safeguard gate remains planned under revised Objective 2.

### 4.9 Planned verification facet — Objective 2

This is a planned addition to the target DynamoDB contract, not a current feature of the local SQLite workspace. A verification run is immutable and applies only to the exact saved workspace hash and captured revisions. It cannot be reused after a save, input change, base-plan change, policy change or verifier deployment.

| Facet | Attribute | Type | Remarks | Example |
|---|---|---|---|---|
| Verification | pk / sk | S / S | `EVENT#<eventId>` / `VERIFY#<verificationId>` | `EVENT#evt_2026_01` / `VERIFY#ver_01` |
| Verification | entityType / eventId | S / S | Discriminator and owner | `SEATING_VERIFICATION` / `evt_2026_01` |
| Verification | verificationId | S | Unique immutable run | `ver_01` |
| Verification | workspaceObjectId / workspaceHash | S / S | Exact committed workspace being checked | `WORKSPACE#ws_04` / `<64-hex-digits>` |
| Verification | workspaceRevision / inputRevision | N / N | Captured revisions; both checked during publication | `4` / `12` |
| Verification | basePlanVersionId / policyVersionId | S / S | Context used by the verifier | `01JPLANEXAMPLE` / `pjkit-v4` |
| Verification | status | S | `PASSED` or `FAILED`; independent of solver status | `FAILED` |
| Verification | findingsObjectId | S | Committed object with rule IDs, severity, affected registration/seat IDs and explanations | `VERIFICATION_RESULT#ver_01` |
| Verification | verifierVersion / verifiedAt | S / N | Verifier build / epoch milliseconds | `git:<commit-sha>` / `1790640000000` |

The exact plan/workspace revision should reference `verificationId`. The publisher must condition-check PASSED status and equality of workspace hash, workspace/input revisions, base plan, policy and verifier version. The planned rule set includes paid-seat entitlement, valid Emperor pairs, accessibility, tier/order and packing. Do not claim this gate is active until implemented and tested; failure leaves the existing public pointer unchanged.

## 5. Exact nested solver data contract

The following attribute dictionaries use the current `production_request.schema.json` and policy file. Within a JSON payload, `object`, `array`, `string`, `integer`, `number`, `boolean`, and `null` are JSON types; if stored natively they correspond to M, L, S, N, N, BOOL and NULL. The object storage format preserves these types through JSON serialization. All fields marked required must be emitted; nullable required fields must be explicitly null when empty. The request forbids unknown properties.

### 5.1 Request envelope — REQUEST object

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `schema_version` | string | Yes | Fixed `2.0.0` | `"2.0.0"` |
| `event_id` | string | Yes | minLength: 1; Equals the existing Events ID; never a job ID | `"evt_2026_01"` |
| `generation_mode` | string | Yes | `INITIAL` or `REGENERATE_DRAFT`; same complete model | `"INITIAL"` |
| `layout_version_id` | string | Yes | minLength: 1 | `"demo-layout-v1"` |
| `policy_version_id` | string | Yes | Fixed `pjkit-v4` | `"pjkit-v4"` |
| `preference_profile_version` | string | Yes | Fixed `ranked-v1` | `"ranked-v1"` |
| `preferences` | array of object | Yes | minItems: 3; maxItems: 3; Exactly one of each preference key, in priority order | `[{"key":"contribution_seat","enabled":true},{"key":"activeness","enabled":true},{"key":"category_zone","enabled":true}]` |
| `participants` | array of object | Yes | Frozen upstream registration snapshot; staff cannot replace or change registrations in a workspace | `[{"participant_id":"P001","registration_status":"CONFIRMED", ...}]` |
| `layout` | object | Yes | Full embedded layout, not just its database pointer | `{"layout_version_id":"demo-layout-v1", …}` |
| `solver` | object | Yes | — | `{"max_time_seconds":60, …}` |
| `event_details` | object | No | Optional display snapshot; do not derive event time from solve time | `{"name":"Example Assembly", …}` |

### 5.2 Participant — Registration.participant and request.participants[]

| Attribute | Type | Required | Remarks / allowed values | Example value |
|---|---|---|---|---|
| `participant_id` | string | Yes | minLength: 1; Allocation-unit ID, scoped to event; stable across versions | `"P001"` |
| `full_name` | string | Yes | minLength: 1 | `"Example Participant"` |
| `registration_status` | string | Yes | `CONFIRMED`, `PENDING`, `WAITLISTED`, `CANCELLED`; only CONFIRMED represents paid seat entitlement. Never derived from attendance. | `"CONFIRMED"` |
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
| `policy_version_id` | string | Yes | — | `"pjkit-v4"` |
| `normalization_version` | string | Yes | — | `"desirability-v2"` |
| `tier_order` | array of string | Yes | — | `["EMPEROR","MERIT","BODHI"]` |
| `tier_minimums` | object | Yes | — | `{"EMPEROR":5000,"MERIT":3000,"BODHI":2000}` |
| `rank_weights` | array of number | Yes | Current three ordinary preferences use the first three enabled ranks | `[40,30,20,10]` |
| `paid_seat_retention` | string | Yes | Independent of physical attendance | `"INDEPENDENT_OF_ATTENDANCE"` |
| `initial_packing` | string | Yes | — | `"STRICT"` |
| `tier_seat_precedence` | string | Yes | — | `"HARD_ALL_PHYSICAL_SEATS"` |
| `category_zone_costs` | object | Yes | Map category → zone → numeric penalty; copy the entire versioned matrix | `{"MONASTIC":{"RIGHT_CENTER":0,"LEFT_CENTER":2,"RIGHT_OUTER":4,"LEFT_OUTER":8},"COMMITTEE":{"RIGHT_CENTER":0,"LEFT_CENTER":2,"RIGHT_OUTER":3,"LEFT_OUTER":6},"VOLUNTEER":{"RIGHT_CENTER":1,"LEFT_CENTER":…` |

### 5.9 Full result payload — RESULT object

Preserve every key returned by `production.format_result()` and persistence/workspace additions. The following dictionary covers the top-level production output; nested diagnostics are retained losslessly rather than flattened into mutable columns. Exact assignment maps retain all participant fields from §5.2 in addition to the fields below.

| Attribute | JSON type | Remarks | Example |
|---|---|---|---|
| schema_version / status | string each | Result contract / success discriminator | `2.0.0` / `success` |
| run_id / generated_at | string each | Solver run UUID / ISO timestamp | `run-uuid` / `2026-09-29T00:00:00+00:00` |
| event_id / generation_mode | string each | Input provenance | `evt_2026_01` / `INITIAL` |
| policy_version_id / layout_version_id | string each | Exact applied versions | `pjkit-v4` / `demo-layout-v1` |
| preference_profile_version / normalization_version | string each | Preference/scoring versions | `ranked-v1` / `desirability-v2` |
| preferences | array of object | Original ordered preference list | `[{"key":"activeness","enabled":true}, …]` |
| effective_weights | object of numbers | Derived enabled coefficients by preference | `{"contribution_seat":40,"activeness":30,"category_zone":20}` |
| source_request | object | Complete §5.1 request | `{"schema_version":"2.0.0", …}` |
| manually_modified | boolean | True only for manually edited output | `false` |
| publication_status | string | Adapter overlays current lifecycle state from plan metadata | `DRAFT` |
| solver_status_at_generation | string | Retain original solver provenance after edits | `OPTIMAL` |
| solver | object | Status, timings, search statistics, proof and canonicalization flag | `{"status":"FEASIBLE", …}` |
| quality | object | Complete computed penalties and quality diagnostics | `{"penalties":{"P001":{…}}, …}` |
| input_summary | object of integer counts | Submitted/eligible/excluded registrations, units, primary participants, tier counts, required/total/available/blocked/empty seats | `{"required_seat_count":1, …}` |
| weights | object of numbers | priority_seat_weight, activeness_weight, category_zone_weight | `{"priority_seat_weight":40,"activeness_weight":30,"category_zone_weight":20}` |
| constraint_config | object | enforce_front_fill, enforce_middle_fill, normalize_penalties booleans; normalization_scale number | `{"enforce_front_fill":true,"enforce_middle_fill":true,"normalize_penalties":true,"normalization_scale":100}` |
| penalty_summary | object | unweighted, normalized and weighted maps | `{"weighted":{"total":0, …}, …}` |
| tier_bands | object of integer arrays | Rows used by each tier, including shared boundary rows | `{"EMPEROR":[],"MERIT":[1],"BODHI":[]}` |
| floor_plan | object | row_count, seats_per_row, aisle_after_position, total_seats and rows[] | `{"row_count":1,"total_seats":4, …}` |
| floor_plan.rows[].seats[] | object | Physical seat fields plus occupancy_status, participant_id, display_name, tier and section | `{"seat_id":"R01-S01","occupancy_status":"EMPTY", …}` |
| assignments | array of object | Full participant fields; is_monk/is_elderly booleans; allocation_type string; seat_ids string array; seats object array; pair_priority number/null; penalty object | `[{"participant_id":"P001","seat_ids":["R01-S03"], …}]` |
| empty_seat_ids | array of string | Assignable vacant positions | `["R01-S01","R01-S02","R01-S04"]` |
| excluded_participants | array of object | participant_id and reason strings | `[{"participant_id":"P002","reason":"PENDING"}]` |
| unassigned_participants | array | Empty for a successful complete solve | `[]` |
| hard_constraint_validation | object | Solver: all_constraints_satisfied BOOL, duplicate_seat_count N, unassigned_count N; current manual flow: checked BOOL=false | `{"all_constraints_satisfied":true,"duplicate_seat_count":0,"unassigned_count":0}` |
| plan_version_id / predecessor_plan_version_id | string / string or null | Added by persistence; identity / lineage | `01JNEWPLAN` / `null` |
| expected_published_version_id | string or null | Added by persistence; stale publication check | `null` |
| created_at | string | Persistence ISO timestamp | `2026-09-29T00:00:00+00:00` |
| operations | object, optional | Published workspace items keyed by participant ID; §4.8 | `{"P001":{"note":"", ...}}` |
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
  "policy_version_id": "pjkit-v4",
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
3. Read CONFIG again. If `inputRevision` changed, discard the mixed snapshot and retry. Strong individual reads alone do not provide a multi-item snapshot. Include upstream registration statuses for traceability; confirmation is a paid entitlement and does not depend on attendance.
4. Construct and validate the request, stage/commit its immutable object, then transact: condition-check unchanged input/state/workspace revisions and expected published pointer; put absent idempotency row; put absent QUEUED job; append audit. A failed condition leaves an unreferenced object, never a submitted mixed-version request.
5. Submit INITIAL or REGENERATE_DRAFT without a previous-plan payload. Keep expected published pointers only for concurrency checks; they are not optimization baselines.

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

result = solve(request)
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

Publication builds a new immutable manual snapshot from the exact saved workspace, preserving `operations`, source request and original generation provenance. It sets `manually_modified=true`, labels current solver status `MANUALLY_MODIFIED`, and preserves the current workspace behavior `hard_constraint_validation={"checked":false}`. Validate basic draft integrity and require every eligible/confirmed paid registration to have its full seat entitlement assigned. Do not mark it solver-audited unless an additional full audit is actually implemented and passed.

After content and assignments are complete, one small `TransactWriteItems` operation:

1. Updates CONFIG conditioned on exact workspace revision/base, expected published pointer, and any relevant input revision; sets the new published/latest pointers, advances workspace revision, and points its base at the new plan.
2. Updates the new plan from DRAFT to PUBLISHED, conditioned on expected content hash and COMPLETE projections.
3. Updates the old published plan to SUPERSEDED, conditioned on its previous status, when one exists.
4. Appends the publication audit item.

Place conditions on the same Update action for an item rather than adding a separate ConditionCheck on that same item. All content remains immutable while lifecycle metadata is overlaid when reconstructing API responses. Participant reads first resolve a single published pointer and then use that version throughout the response, so a concurrent publish returns a complete old or complete new plan.

DynamoDB transactions are limited to 100 distinct items and 4 MB. Do not attempt to publish every seat/registration in the pointer-switch transaction; staged immutable content plus a small commit transaction is deliberate. [AWS transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)

The repository retains older `submit/approve/publish` PlanStore commands, but the current workspace UI publishes saved revisions directly. This proposal models that current flow. If the approval workflow is restored, add UNDER_REVIEW/APPROVED/REJECTED states and actor/time/approved-content-hash fields, with approval tied to the exact immutable content hash.

### 7.5 End-to-end implementation flow by record family

| Order | Record family | Create / update | Link and read pattern |
|---|---|---|---|
| 1 | Existing `Events` metadata | Confirm the existing event key; add optional seating metadata only through the host migration | `offeringEventId` maps to Offerings discovery; keep the opaque event ID as the seating identity |
| 2 | `CONFIG` | Create one item per enabled event with revision zero and null pointers; update via conditional writes | Root event control record; `GetItem(pk=EVENT#id, sk=CONFIG)` |
| 3 | `REG#...` + `SOURCE#...` | Import normalized participant, source tuple and unique link; increment `inputRevision` in the same transaction | Event registration query by `REG#`; source link exact get prevents duplicate bundle/unit import |
| 4 | Identity link | Create only after Auth ownership is verified | Query `USER#authId` with event sort-key prefix for participant lookup |
| 5 | Policy + layout | Seed immutable policy; commit layout as manifest and parts; conditionally select active layout | Read by exact global policy key and committed object ID; validate hash/version |
| 6 | Request + idempotency + job | Assemble a consistent snapshot, commit REQUEST, then transact idempotency + QUEUED job + audit while checking captured revisions | Job links to request ID/hash and stores revisions; same token/same command returns the same job |
| 7 | Worker + result + plan + assignments | Claim a lease; validate/solve/audit; commit RESULT, plan and assignment projection; mark job SUCCEEDED conditionally | Staff reads plan/result; participant reads CONFIG → published plan → one assignment, not a registration scan |
| 8 | Workspace | Save complete state as a new immutable object and advance CONFIG only for the expected base/revision | Concurrent stale saves fail; prior workspace objects remain immutable history |
| 9 | Verification (planned) | Audit the saved object and persist immutable findings bound to hash and revisions | Publisher accepts only PASSED for the exact current hash/revisions and compatible policy/verifier |
| 10 | Publication + audit | Stage manual result/projection and perform a small conditional pointer-switch transaction | `publishedPlanVersionId` is the sole public pointer; old plan content remains immutable |

Recommended rollout: (a) freeze the API/key contract and verify deployed host table keys; (b) provision `Seating`, configuration, policy and layout; (c) implement imports/revisioning; (d) build and stress-test canonical object serialization; (e) introduce a persistence interface while retaining the SQLite adapter; (f) implement asynchronous jobs, idempotency, leases and redrive; (g) implement workspace, assignments and explicit publication; (h) add and evaluate the planned safeguard verification; (i) pass concurrency, privacy, failure-recovery and cloud acceptance tests. DynamoDB is not a prerequisite for the present local app, so keep the SQLite flow working throughout migration.

## 8. Implementation checklist and acceptance criteria

1. Provision Seating with String `pk`/`sk`, no new index, Streams and worker configuration. Add the optional Events metadata fields through the application.
2. Implement import mappings and missing registration-data collection. Establish authoritative event/participant identities, invoice eligibility and whole-ringgit handling. Do not copy Auth credentials/tokens to Seating or into Lambda payloads.
3. Seed policy registry from the deployed policy file; import the actual hall as a committed LAYOUT object. Register all physical positions including blocked seats.
4. Implement the conditional DynamoDB persistence adapter, canonical JSON object reader/writer, and host request assembler. Port PlanStore/WorkspaceStore semantics, including public-data filtering, rather than replacing SQLite calls mechanically.
5. Implement job submission, stream worker, leases, idempotency, failure redrive and explicit draft attachment. The application polls the persisted job and then loads its resulting plan.
6. Implement immutable manual snapshots, assignment projections and atomic publication; retain old versions required by audit and history. Do not TTL-delete referenced content.
7. Verify duplicate stream records, worker timeout/reclaim, simultaneous registration edits, two staff saves, stale workspace/publication pointers, fractional contributions, incomplete object writes, multi-page reads and outputs exceeding 400 KB. A failed or incomplete solve must leave the public plan unchanged.
8. Verify a real reconstructed request against the current JSON schema and `validate_request`, run `solve(request)` and its independent audit, then verify that participant responses expose only their permitted identity/seat data and anonymous hall occupancy.

The schema is a design deliverable. It does not provision AWS resources or change the current solver's mathematical behavior.

## 9. Source references

- **Reference workbook:** `Database Structure.xlsx`; Offerings sheet A3:H104 (table keys, invoice/bundle data and existing event GSI); Auth sheet A2:E66 (identity schema); Events v2 sheet A3:H32 (event keys, metadata, indexes, locale/statistics/history conventions). Workbook contents were treated as schema evidence, not operational instructions.
- [Production request JSON schema](../../schemas/production_request.schema.json), [layout schema](../../schemas/production_layout.schema.json), and [policy schema](../../schemas/production_policy.schema.json).
- [Production solve and result construction](../../src/seat_solver/production/production.py), [domain validation](../../src/seat_solver/production/policy.py), and [deployed policy](../../config/production_policy.json).
- [Current workspace state and publication behavior](../../src/seat_solver/production/workspace.py), [local PlanStore](../../src/seat_solver/production/plan_store.py), and [service adapter](../../src/seat_solver/production/service.py).
- [Current README](../../README.md) and [integration notes](../archived/integration.md). Where older approval-flow prose differs from the workspace implementation, the current workspace code is the basis of this proposal.
- AWS documentation links alongside relevant design decisions were checked on 29 September 2026.
