# Seating — DynamoDB Table Design

One-table pattern. All row types share a single `seating` table.

The table integrates the seating allocation flow into the existing platform. Every item is
event-owned: `pk` is the host's canonical `eventId` — the same value the Events table uses as its
`pk`, with no prefix — so one event = one partition and every per-event query is a
single-partition read. The only non-event family is the reserved literal `"POLICY"` partition for
the shared solver-policy registry; the adapter rejects any event ID equal to a reserved partition
literal. Row kinds are derived from `pk`/`sk` shape (`"REG#"`, `"LAYOUT#"`, `"PLAN#"`,
`"WORKSPACE#"`, `"ASSIGN#"` prefixes and the fixed literals `"CONFIG"`/`"POLICY"`/`"WORKSPACE#CURRENT"`);
no item carries an `entityType` attribute or duplicated foreign keys — identifiers are re-derived
in the facet layer. The existing Events, Offerings, Invoice and Auth tables remain unchanged.
Design rationale and recorded key-shape decisions live in [table.md](table.md).

## Type Enums

| Group                 | Values                                                          | Notes                                              |
| --------------------- | --------------------------------------------------------------- | -------------------------------------------------- |
| `CONTRIBUTION_TIER`   | `"EMPEROR" \| "MERIT" \| "BODHI"`                               | Registered bundle tier; Emperor occupies two seats |
| `PARTICIPANT_CATEGORY`| `"MONASTIC" \| "COMMITTEE" \| "VOLUNTEER" \| "GENERAL_DEVOTEE"` | Solver category driving zone costs                 |
| `PUBLICATION_STATUS`  | `"DRAFT" \| "PUBLISHED" \| "SUPERSEDED"`                        | Plan lifecycle                                     |
| `ALLOCATION_TYPE`     | `"SINGLE" \| "EMPEROR_PAIR"`                                    | One seat vs approved pair                          |
| `PREFERENCE_KEY`      | `"contribution_seat" \| "activeness" \| "category_zone"`        | Exactly these three, in priority order             |
| `FINDING_SEVERITY`    | `"RED" \| "YELLOW"`                                             | Blocking vs advisory safeguard findings            |

## Entities

### Configuration entity

#### Description

Per-event singleton holding the solver context — the settings loaded before running the
allocation — plus the single publication pointer. Everything here is mutable; revision counters
and workspace state live on the items they belong to, not here.

| Attribute                | Type                                        | Notes                                                                                      |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `pk`                     | `string`                                    | Canonical event ID                                                                          |
| `sk`                     | `"CONFIG"`                                  | Fixed literal                                                                               |
| `activeLayoutVersionId`  | `string`                                    | Layout version used by new solves                                                           |
| `policyVersionId`        | `string`                                    | Policy version loaded by the solver; set at event setup, changed only at seed/deployment    |
| `preferences`            | `{key: PREFERENCE_KEY, enabled: boolean}[]` | Ordered preference list; order defines priority, exactly the three solver keys              |
| `publishedPlanVersionId` | `string \| null`                            | The only public-plan pointer; `null` until first publication; CAS anchor for publication    |
| `updatedAt`              | `number`                                    | Last edit time as UNIX epoch timestamp                                                      |
| `updatedBy`              | `string`                                    | Unique identifier of staff that updated the configuration                                   |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "CONFIG",
    "activeLayoutVersionId": "01JLAYOUTEXAMPLE",
    "policyVersionId": "01JPOLICYEXAMPLE",
    "preferences": [
        { "key": "contribution_seat", "enabled": true },
        { "key": "activeness", "enabled": true },
        { "key": "category_zone", "enabled": true }
    ],
    "publishedPlanVersionId": null,
    "updatedAt": 1790640000000,
    "updatedBy": "usr_staff_01"
}
```

### Registration entity

#### Description

The seating flow's own materialization of one allocation unit, created by an explicit import from
the invoicing and offering flows. The upstream tables carry no participant entity, so the import
is where the stable `participantId` is minted and where solver inputs that exist upstream (payer
name, tier, amount) are resolved and frozen. There is no `registrationStatus`: every row in this
family is seatable by construction, imported from an invoice with status `"paid"`; a post-import
refund is applied by re-running the import, which reconciles by `source` and deletes the row.

| Attribute                | Type                            | Notes                                                                                                                                |
| ------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `pk`                     | `string`                        | Canonical event ID                                                                                                                    |
| `sk`                     | `"REG#<participantId>"`         | `<participantId>` - stable allocation-unit key, minted at import                                                                      |
| `fullName`               | `string`                        | Payer's display name, materialized at import from the bundle's `payer` (not `invoice.customerName`); the one name staff edit per Emperor pair |
| `contributionTier`       | `CONTRIBUTION_TIER`             | Materialized at import from the matching bundle's `type` (`emperor` → `EMPEROR`, …)                                                    |
| `contributionAmountRm`   | `number`                        | Materialized at import from `bundle.amount`; importance-normalization input                                                            |
| `requiresAccessibleSeat` | `boolean`                       | Seating-captured; no upstream source                                                                                                   |
| `participantCategory`    | `PARTICIPANT_CATEGORY`          | Seating-captured solver category                                                                                                       |
| `recentEventsJoined`     | `number`                        | Distinct completed events the customer joined in a rolling five-year window; derived at import by walking the upstream event/invoice GSIs, frozen, refreshed only by re-import |
| `source`                 | `{table, pk, sk, bundleId}`     | **OPTIONAL** - authoritative Offerings/Invoice reference; reconciliation key for re-import                                              |
| `createdBy`              | `string`                        | Unique identifier of staff that imported the registration                                                                               |
| `createdAt`              | `number`                        | Import time as UNIX epoch timestamp                                                                                                     |
| `updatedBy`              | `string`                        | Unique identifier of staff that last updated the registration                                                                           |
| `updatedAt`              | `number`                        | Last edit time as UNIX epoch timestamp                                                                                                  |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "REG#P001",
    "fullName": "Example Participant",
    "contributionTier": "MERIT",
    "contributionAmountRm": 3000,
    "requiresAccessibleSeat": false,
    "participantCategory": "GENERAL_DEVOTEE",
    "recentEventsJoined": 0,
    "source": { "table": "Offerings", "pk": "INV00001", "sk": "bundle#z88p4tow4navrttm", "bundleId": "z88p4tow4navrttm" },
    "createdBy": "usr_staff_01",
    "createdAt": 1790640000000,
    "updatedBy": "usr_staff_01",
    "updatedAt": 1790640000000
}
```

### Layout entity

#### Description

Immutable layout version. Written once at commit; never updated. The hall is small
(16 × 16 = 256 seats), so the complete seat list fits in one item.

| Attribute   | Type     | Notes                                                                                                                |
| ----------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| `pk`        | `string` | Canonical event ID                                                                                                    |
| `sk`        | `"LAYOUT#<layoutId>"` | `<layoutId>` - immutable ULID version ID                                                                  |
| `layout`    | `map`    | Complete production layout: dimensions, `accessible_positions`, `approved_pairs`, every physical seat incl. blocked   |
| `createdBy` | `string` | Layout author                                                                                                         |
| `createdAt` | `number` | Commit time as UNIX epoch timestamp                                                                                    |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "LAYOUT#01JLAYOUTEXAMPLE",
    "layout": {
        "layout_version_id": "01JLAYOUTEXAMPLE",
        "row_count": 16,
        "seats_per_row": 16,
        "aisle_after_position": 8,
        "accessible_positions": [1, 2, 15, 16],
        "approved_pairs": [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16]],
        "seats": [
            { "seat_id": "R01-S01", "row_number": 1, "physical_position": 1, "is_blocked": false },
            { "seat_id": "R01-S02", "row_number": 1, "physical_position": 2, "is_blocked": false }
        ]
    },
    "createdBy": "usr_staff_01",
    "createdAt": 1790640000000
}
```

### Plan entity

#### Description

Immutable plan version carrying its frozen solver request and result. `planVersionId` is a ULID,
so `sk` order is creation order and newest-first listing needs no timestamp attribute.
`operations` preserves display names and notes so a published manual snapshot remains
self-contained. `printArtifacts` is the single post-hoc mutable map: every printed PDF/PNG of the
`/venue` map is uploaded to S3 once and recorded here, so repeated prints re-download the cached
file instead of regenerating it; entries store the S3 key (never a URL) under a deterministic
`plans/<planId>/venue.<format>` key, latest-wins per format.

| Attribute                  | Type                           | Notes                                                                            |
| -------------------------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `pk`                       | `string`                       | Canonical event ID                                                                |
| `sk`                       | `"PLAN#<planId>"`              | `<planId>` - immutable ULID version ID                                            |
| `publicationStatus`        | `PUBLICATION_STATUS`           | `DRAFT`, `PUBLISHED` or `SUPERSEDED`                                              |
| `sourceRequest`            | `map`                          | Frozen solver input (participants, layout, preferences, solver settings)          |
| `result`                   | `map`                          | Frozen assignments, floor plan, quality, diagnostics, solver status               |
| `operations`               | `map`                          | `participantId → workspace item`; preserved manual snapshot state                 |
| `printArtifacts`           | `map`                          | Format → `{s3Key, printedAt, printedBy}`; latest-wins per format (`"pdf"`, `"png"`) |
| `predecessorPlanVersionId` | `string \| null`               | Previous plan in the editing lineage                                              |
| `manuallyModified`         | `boolean`                      | True for manually edited output                                                   |
| `createdBy`                | `string`                       | Unique identifier of staff or system that created the plan version                 |
| `createdAt`                | `number`                       | Creation time as UNIX epoch timestamp                                              |
| `publishedBy`              | `string`                       | **OPTIONAL** - Unique identifier of staff that published the plan, set only on explicit publication |
| `publishedAt`              | `number`                       | **OPTIONAL** - Publication time as UNIX epoch timestamp, set only on explicit publication |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "PLAN#01JPLANEXAMPLE",
    "publicationStatus": "DRAFT",
    "sourceRequest": { "event_id": "evt_2026_01", "generation_mode": "INITIAL", "participants": [], "layout": {}, "solver": {} },
    "result": { "status": "success", "assignments": [], "floor_plan": {} },
    "operations": { "P001": { "seat_ids": ["R01-S07"] } },
    "printArtifacts": {
        "pdf": { "s3Key": "plans/01JPLANEXAMPLE/venue.pdf", "printedAt": 1790641000000, "printedBy": "usr_staff_01" }
    },
    "predecessorPlanVersionId": null,
    "manuallyModified": false,
    "createdBy": "usr_staff_01",
    "createdAt": 1790640000000,
    "publishedBy": null,
    "publishedAt": null
}
```

### Workspace entity

#### Description

The mutable current editing state. `WORKSPACE#CURRENT` is overwritten on every save under a
`revision` condition; history of saves is intentionally not kept here — durable history lives in
per-plan workspace versions and the client's local edit journal. Every registration keeps the
seats the algorithm assigned it — staff move and swap placements but can never exempt a
registration from the plan, so an assigned seat always preserves its name regardless of whether
the person attends.

| Attribute           | Type     | Notes                                                                         |
| ------------------- | -------- | ----------------------------------------------------------------------------- |
| `pk`                | `string` | Canonical event ID                                                             |
| `sk`                | `"WORKSPACE#CURRENT"` | Fixed literal; one active workspace per event                      |
| `basePlanVersionId` | `string` | Plan opened by the workspace                                                   |
| `revision`          | `number` | Monotonic optimistic-concurrency revision; saves and publication echo it        |
| `state`             | `map`    | `{items: participantId → workspace item}`; exactly one entry per registration   |
| `savedBy`           | `string` | Unique identifier of staff that last saved the workspace                        |
| `savedAt`           | `number` | Last save time as UNIX epoch timestamp                                          |

##### `state.items[<participantId>]`

| Attribute       | Type              | Notes                                            |
| --------------- | ----------------- | ------------------------------------------------ |
| `seat_ids`      | `string[]`        | Assigned seat IDs; one or two (Emperor pair), never empty |
| `display_names` | `string[]`        | One name per occupant; Emperor has two entries   |
| `note`          | `string`          | Staff note, maximum 2,000 characters             |
| `changed_at`    | `string \| null`  | Optional ISO timestamp for the working item      |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "WORKSPACE#CURRENT",
    "basePlanVersionId": "01JPLANEXAMPLE",
    "revision": 7,
    "state": {
        "items": {
            "P001": {
                "seat_ids": ["R01-S07"],
                "display_names": ["Example Participant"],
                "note": "",
                "changed_at": null
            }
        }
    },
    "savedBy": "usr_staff_01",
    "savedAt": 1790640000000
}
```

### Workspace version entity

#### Description

Immutable workspace snapshot bound to a plan, written when the workspace switches to another
plan or is explicitly saved. Same shape as `WORKSPACE#CURRENT` minus `basePlanVersionId`, which
the `sk` already encodes. Without this item, switching from plan A to plan B (or reopening A
later) would silently discard the last saved but unpublished edits.

| Attribute  | Type     | Notes                                                     |
| ---------- | -------- | --------------------------------------------------------- |
| `pk`       | `string` | Canonical event ID                                         |
| `sk`       | `"WORKSPACE#<planId>"` | Saved workspace associated with one plan     |
| `revision` | `number` | Workspace revision at the time this version was saved      |
| `state`    | `map`    | Same `state` map as `WORKSPACE#CURRENT`                    |
| `savedBy`  | `string` | Unique identifier of staff who saved the version           |
| `savedAt`  | `number` | Save time as UNIX epoch timestamp                          |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "WORKSPACE#01JPLANEXAMPLE",
    "revision": 6,
    "state": { "items": {} },
    "savedBy": "usr_staff_01",
    "savedAt": 1790640000000
}
```

### Assignment entity

#### Description

Read projection of one plan's complete assignments, one item per eligible registration, stored in
the event partition under an `ASSIGN#` sort-key prefix. Contains public seat data only — no
payment, category, diagnostics or review fields. The projection is complete by construction: a
seat is a contribution entitlement, so every `REG#` row yields exactly one `ASSIGN` row per plan,
and an assigned seat preserves its name whether or not the person attends.

| Attribute        | Type                                | Notes                                        |
| ---------------- | ----------------------------------- | -------------------------------------------- |
| `pk`             | `string`                            | Canonical event ID                            |
| `sk`             | `"ASSIGN#<planId>#<participantId>"` | One assignment for an eligible registration   |
| `registeredName` | `string`                            | Name from the registration snapshot           |
| `allocationType` | `ALLOCATION_TYPE`                   | `EMPEROR_PAIR` or `SINGLE`                    |
| `seatIds`        | `string[]`                          | Ordered assigned seat IDs                     |
| `seats`          | `map[]`                             | `seat_id`, `row_number`, `physical_position`, `priority_rank`, `zone`, `display_name` |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "ASSIGN#01JPLANEXAMPLE#P001",
    "registeredName": "Example Participant",
    "allocationType": "SINGLE",
    "seatIds": ["R01-S07"],
    "seats": [{ "seat_id": "R01-S07", "row_number": 1, "physical_position": 7, "priority_rank": 2, "zone": "RIGHT_CENTER", "display_name": "Example Participant" }]
}
```

### Policy entity

#### Description

Immutable, event-independent solver-policy version. Written once at seed/deployment time; no
runtime flow edits a version in place — a changed policy writes a **new** version and repoints
the event's `CONFIG.policyVersionId`, so every existing plan keeps referencing the exact policy
it was solved under. Contains exactly the four business-tunable number sets the solver reads;
engine-coupled behaviour (packing strategy, tier-seat rule, normalization/build stamps) is
hardcoded in the solver build and stamped into result diagnostics, never stored as policy data.

| Attribute              | Type                     | Notes                                                                        |
| ---------------------- | ------------------------ | ---------------------------------------------------------------------------- |
| `pk`                   | `"POLICY"`               | Reserved literal partition; single shared registry                            |
| `sk`                   | `"policy#<policyId>"`    | `<policyId>` - immutable ULID version ID                                      |
| `tierOrder`            | `CONTRIBUTION_TIER[]`    | Tier precedence used by the solver                                            |
| `tierMinimums`         | `map`                    | Tier → whole-ringgit minimum (contribution tier boundary)                     |
| `categoryZoneCosts`    | `map`                    | `PARTICIPANT_CATEGORY → zone → cost`; defines category/zone behaviour         |
| `rankWeights`          | `number[]`               | Relative preference weights matched to preference rank order                  |
| `createdBy`            | `string`                 | Unique identifier of the developer that seeded the version                    |
| `createdAt`            | `number`                 | Seed time as UNIX epoch timestamp                                             |

#### Example

```
{
    "pk": "POLICY",
    "sk": "policy#01JPOLICYEXAMPLE",
    "tierOrder": ["EMPEROR", "MERIT", "BODHI"],
    "tierMinimums": { "EMPEROR": 5000, "MERIT": 3000, "BODHI": 2000 },
    "categoryZoneCosts": {
        "MONASTIC":        { "RIGHT_CENTER": 0, "LEFT_CENTER": 2, "RIGHT_OUTER": 4, "LEFT_OUTER": 8 },
        "COMMITTEE":       { "RIGHT_CENTER": 0, "LEFT_CENTER": 2, "RIGHT_OUTER": 3, "LEFT_OUTER": 6 },
        "VOLUNTEER":       { "RIGHT_CENTER": 1, "LEFT_CENTER": 2, "RIGHT_OUTER": 1, "LEFT_OUTER": 3 },
        "GENERAL_DEVOTEE": { "RIGHT_CENTER": 2, "LEFT_CENTER": 2, "RIGHT_OUTER": 0, "LEFT_OUTER": 1 }
    },
    "rankWeights": [40, 30, 20, 10],
    "createdBy": "usr_staff_01",
    "createdAt": 1790640000000
}
```

## Facets

Facets are the application-facing shapes derived from entities. `pk` and `sk` are replaced with
clean domain IDs extracted from their values; no facet exposes table keys.

### Configuration facet

| Attribute                | Derived from              | Type                          |
| ------------------------ | ------------------------- | ----------------------------- |
| `eventId`                | `pk`                      | `string`                      |
| `activeLayoutVersionId`  | `activeLayoutVersionId`   | `string`                      |
| `policyVersionId`        | `policyVersionId`         | `string`                      |
| `preferences`            | `preferences`             | `{key, enabled}[]`            |
| `publishedPlanVersionId` | `publishedPlanVersionId`  | `string \| null`              |
| `updatedAt` / `updatedBy`| `updatedAt` / `updatedBy` | `number` / `string`           |

### Registration facet

`participantId` is extracted from the `sk`; the flattened attributes map one-to-one, so the
solver-request builder re-injects `participant_id` into the request payload without it ever being
stored. There is no `registrationStatus` in the facet: every exported row is an eligible
allocation unit by construction of the import.

| Attribute                 | Derived from                          | Type                                       |
| ------------------------- | ------------------------------------- | ------------------------------------------ |
| `participantId`           | `sk` - extract id from `"REG#<id>"`   | `string`                                   |
| `fullName`                | `fullName`                            | `string`                                   |
| `contributionTier`        | `contributionTier`                    | `CONTRIBUTION_TIER`                        |
| `contributionAmountRm`    | `contributionAmountRm`                | `number`                                   |
| `requiresAccessibleSeat`  | `requiresAccessibleSeat`              | `boolean`                                  |
| `participantCategory`     | `participantCategory`                 | `PARTICIPANT_CATEGORY`                     |
| `recentEventsJoined`      | `recentEventsJoined`                  | `number`                                   |
| `source`                  | `source`                              | `{table, pk, sk, bundleId} \| undefined`   |
| `createdAt` / `updatedAt` | `createdAt` / `updatedAt`             | `number`                                   |

### Plan summary facet

Listing shape for the plan-history dropdown; the heavy `sourceRequest`/`result`/`operations` maps
are loaded only when a plan is opened. `printArtifacts` rides along (small map) so the dropdown
can show which versions already have a cached venue print.

| Attribute                  | Derived from                        | Type                           |
| -------------------------- | ----------------------------------- | ------------------------------ |
| `planId`                   | `sk` - extract id from `"PLAN#<id>"`| `string`                       |
| `publicationStatus`        | `publicationStatus`                 | `PUBLICATION_STATUS`           |
| `manuallyModified`         | `manuallyModified`                  | `boolean`                      |
| `predecessorPlanVersionId` | `predecessorPlanVersionId`          | `string \| null`               |
| `printArtifacts`           | `printArtifacts`                    | `map`                          |
| `createdAt` / `createdBy`  | `createdAt` / `createdBy`           | `number` / `string`            |
| `publishedAt` / `publishedBy` | `publishedAt` / `publishedBy`    | `number` / `string`, optional  |

### Assignment display facet

Public projection returned to authenticated participants and the hall display; identical to the
entity minus both table keys, with the participant and plan IDs re-derived from the composite
`sk`.

| Attribute        | Derived from                                                                     | Type              |
| ---------------- | -------------------------------------------------------------------------------- | ----------------- |
| `planId`         | `sk` - extract second segment from `"ASSIGN#<planId>#<participantId>"`           | `string`          |
| `participantId`  | `sk` - extract third segment from `"ASSIGN#<planId>#<participantId>"`            | `string`          |
| `registeredName` | `registeredName`                                                                 | `string`          |
| `allocationType` | `allocationType`                                                                 | `ALLOCATION_TYPE` |
| `seats`          | `seats`                                                                          | `map[]`           |

## Secondary indexes

None. Every access pattern below is a key-condition query on the base table; the only Filter
Expression (import deduplication on `source`) runs over one bounded event partition at low
frequency, which is cheaper than maintaining a GSI and a hash attribute for it. Lifecycle
attributes such as `publicationStatus` are never queried alone — they are always read inside a
known partition — so indexing them would only add write cost.

## Access patterns

| Pattern                                            | Query                                                                                                                |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Get seating configuration for an event             | `Query pk = "<eventId>", sk = "CONFIG"`                                                                               |
| List all registrations for an event                | `Query pk = "<eventId>", sk begins_with("REG#")`                                                                       |
| Find registrations by contribution source (import) | `Query pk = "<eventId>", sk begins_with("REG#")` + FilterExpression `source.pk = :pk AND source.sk = :sk AND source.bundleId = :bundle` |
| Get a layout version                               | `Query pk = "<eventId>", sk = "LAYOUT#<layoutId>"`                                                                     |
| Get one plan                                       | `Query pk = "<eventId>", sk = "PLAN#<planId>"`                                                                         |
| List plan versions, newest first                   | `Query pk = "<eventId>", sk begins_with("PLAN#")` ORDER BY `sk` DESC (ULIDs sort in creation order)                    |
| Publish a plan                                     | `TransactWrite` on `CONFIG` + `PLAN#<planId>` with CAS on `publishedPlanVersionId`; blocking safeguard findings must be overridden in the same request |
| Load and save the current workspace                | `Query pk = "<eventId>", sk = "WORKSPACE#CURRENT"`, save conditional on `revision`                                     |
| Get the workspace snapshot bound to an older plan  | `Query pk = "<eventId>", sk = "WORKSPACE#<planId>"`                                                                    |
| List all assignments of one plan                   | `Query pk = "<eventId>", sk begins_with("ASSIGN#<planId>#")`                                                           |
| Participant views their own seat in a plan         | `Query pk = "<eventId>", sk = "ASSIGN#<planId>#<participantId>"`                                                       |
| Get the active policy for a solve                  | `Query pk = "POLICY", sk = "policy#<policyId>"`                                                                        |
