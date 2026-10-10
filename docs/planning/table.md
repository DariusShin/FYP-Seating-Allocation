# Seating — DynamoDB Table Design

One-table pattern. All row types share a single `seating` table. This document supersedes
`dynamodb-seating-schema.md` and the `Database Structure - Seating.csv` workbook: entities no
longer carry SQL-style foreign keys (`entityType`, duplicated `eventId`, embedded
`participant_id`); an item's kind is derived from its `pk`/`sk` shape, exactly like the
Offerings `table.md`. The existing Events, Offerings and Auth tables remain unchanged.

## Single-table design notes

- **Access-pattern first.** The access-pattern table below was written before the entities; every
  Key Condition is fully answerable by the base table, and the single Filter Expression operates
  over a bounded partition. No secondary index is justified.
- **Key-derived typing.** There is no `entityType` attribute. `"REG#"`, `"PLAN#"`, `"history#"`…
  prefixes and the fixed literals `"CONFIG"`/`"POLICY"` identify the row kind, mirroring how
  Offerings derives `entry`/`bundle` from the `sk` prefix.
- **Bare event partition keys.** `pk` is the host's canonical `eventId` with no `EVENT#` prefix —
  the prefix was never load-bearing in any Key Condition, and the Offerings `table.md` proves the
  bare form works when a table's partition families are known. The seating table has exactly one
  non-event family, the reserved literal partition `"POLICY"`; the adapter rejects any event ID
  equal to a reserved partition literal, so collision safety is enforced in code rather than
  bought with bytes in every key.
- **No duplicated foreign keys.** The owning event is already the partition key, so no item
  repeats `eventId`. A plan item does not store `planVersionId` (it *is* the `sk`), an assignment
  item does not store the plan it belongs to (it is in the `sk`), and a registration does not
  embed `participant_id` (it is the `sk`). Identifiers are re-derived in the facet layer.
- **Immutable versions vs mutable pointers.** Layout versions, plan versions and policy versions
  are written once and never updated. Mutable state is concentrated in three singletons per
  event (`CONFIG`, `WORKSPACE#CURRENT`, `REVIEW#…`) that hold pointers and revisions, so all
  concurrency control happens through conditional writes on few, well-known items.

## Type Enums

| Group                 | Values                                                         | Notes                                              |
| --------------------- | -------------------------------------------------------------- | -------------------------------------------------- |
| `REGISTRATION_STATUS` | `"CONFIRMED" \| "PENDING" \| "WAITLISTED" \| "CANCELLED"`      | Only `CONFIRMED` carries paid-seat entitlement     |
| `CONTRIBUTION_TIER`   | `"EMPEROR" \| "MERIT" \| "BODHI"`                              | Registered bundle tier; Emperor occupies two seats |
| `PARTICIPANT_CATEGORY`| `"MONASTIC" \| "COMMITTEE" \| "VOLUNTEER" \| "GENERAL_DEVOTEE"`| Solver category driving zone costs                 |
| `ATTENDANCE_STATUS`   | `"PRESENT" \| "ABSENT"`                                        | Applies to the whole registration incl. both Emperor seats |
| `PUBLICATION_STATUS`  | `"DRAFT" \| "PUBLISHED" \| "SUPERSEDED"`                       | Plan lifecycle                                     |
| `ALLOCATION_TYPE`     | `"SINGLE" \| "EMPEROR_PAIR"`                                   | One seat vs approved pair                          |
| `PREFERENCE_KEY`      | `"contribution_seat" \| "activeness" \| "category_zone"`       | Exactly these three, in priority order             |
| `REVIEW_STATUS`       | `"NOT_CHECKED" \| "IN_PROGRESS" \| "PASSED"`                   | Safeguard review state for one plan baseline       |
| `FINDING_SEVERITY`    | `"RED" \| "YELLOW"`                                            | Blocking vs advisory findings                      |
| `HISTORY_ACTION`      | `"create" \| "update" \| "delete" \| "restore"`                | Actions triggered for history operation            |

## Access patterns

Frequency is per event and per seating workflow cycle (import → generate → edit → review →
publish → event-day attendance). "high" = touched on nearly every screen or action; "low" =
written/read at setup, at explicit workflow steps, or for audit.

| Access Pattern | Table/GSI/LSI | Key Condition | Filter Expression | Frequency |
| -------------- | ------------- | ------------- | ----------------- | --------- |
| Get seating configuration for an event (and conditionally update its pointers/revisions) | Table | PK = eventId<br>SK = `"CONFIG"` | — | high |
| List all registrations for an event (import, solver request build, workspace open) | Table | PK = eventId<br>SK begins_with(`"REG#"`) | — | high |
| Get or update one registration | Table | PK = eventId<br>SK = `"REG#<participantId>"` | — | low |
| Find an existing registration by its contribution source during import | Table | PK = eventId<br>SK begins_with(`"REG#"`) | `source.pk = :pk AND source.sk = :sk AND source.bundleId = :bundle AND source.unitId = :unit` | low |
| Get attendance for one registration (and conditionally toggle it) | Table | PK = eventId<br>SK = `"ATTENDANCE#<participantId>"` | — | high (event day) |
| List the full attendance map for an event | Table | PK = eventId<br>SK begins_with(`"ATTENDANCE#"`) | — | high (event day) |
| Get a layout version (via `CONFIG.activeLayoutVersionId`) | Table | PK = eventId<br>SK = `"LAYOUT#<layoutId>"` | — | low |
| List all layout versions | Table | PK = eventId<br>SK begins_with(`"LAYOUT#"`) | — | low |
| Get one plan (open workspace, print, detail) | Table | PK = eventId<br>SK = `"PLAN#<planId>"` | — | high |
| List plan versions, newest first | Table | PK = eventId<br>SK begins_with(`"PLAN#"`) | — (plan IDs are ULIDs, so descending `sk` order is creation order) | low |
| Publish a plan — swap `CONFIG` pointers and plan status in one transaction with CAS on the published pointer | Table | PK = eventId<br>SK = `"CONFIG"` *and* SK = `"PLAN#<planId>"` | — (CAS is a condition expression on `publishedPlanVersionId`, not a filter) | low |
| Load and save the current workspace (save is conditional on `revision`) | Table | PK = eventId<br>SK = `"WORKSPACE#CURRENT"` | — | high |
| Get the workspace snapshot bound to an older plan | Table | PK = eventId<br>SK = `"WORKSPACE#<planId>"` | — | low |
| Get or patch the safeguard review for a plan | Table | PK = eventId<br>SK = `"REVIEW#<planId>"` | — | low |
| List all assignments of one plan (hall display, print) | Table | PK = eventId<br>SK begins_with(`"ASSIGN#<planId>#"`) | — | high |
| Participant views their own seat in a plan | Table | PK = eventId<br>SK = `"ASSIGN#<planId>#<participantId>"` | — | high |
| List all policy versions (Settings dialog) | Table | PK = `"POLICY"`<br>SK begins_with(`"policy#"`) | — | low |
| Get the active policy for a solve (via `CONFIG.policyVersionId`) | Table | PK = `"POLICY"`<br>SK = `"policy#<policyId>"` | — | low |
| Save a new policy version and repoint `CONFIG.policyVersionId` | Table | PK = `"POLICY"` *and* PK = eventId | — | low |
| List history, newest first (audit page) | Table | PK = eventId<br>SK begins_with(`"history#"`) | — | low |
| Get the most recent history entry ("what just happened") | Table | PK = eventId<br>SK begins_with(`"history#"`) | — (ascending `sk` = time order; `Limit 1`, `ScanIndexForward = false`) | low |

## Key design

| Key | Value | Kind | Reason |
| --- | ----- | ---- | ------ |
| `pk` | `<eventId>` | Bare domain ID | The host Events system's canonical event ID, the same value the Events table uses as its `pk`. Every seating item is event-owned, so one event = one partition and every per-event query is a single-partition read. No prefix: no Key Condition ever needed to distinguish partition kinds, and the table has exactly one other family — the reserved literal `"POLICY"` partition — which the adapter protects with a reserved-word check on incoming event IDs. Dropping the prefix keeps the key dialect identical to the Events and Offerings tables. |
| `pk` (policy) | `"POLICY"` | String literal | Policies are shared across events; a single tiny registry partition makes "list all policy versions" (Settings dialog) a one-partition query. The active version is chosen by the event's `CONFIG` pointer, not by the partition. `"POLICY"` is a reserved partition name; the adapter rejects any event ID matching it. |
| `sk` | `"CONFIG"`, `"WORKSPACE#CURRENT"` | String literal | Fixed sort keys for the per-event singletons. They sort deterministically and `GetItem` targets them exactly; no prefix is needed because there is exactly one such item per partition. |
| `sk` | `"REG#<participantId>"`, `"ATTENDANCE#<participantId>"`, `"LAYOUT#<layoutId>"`, `"PLAN#<planId>"`, `"REVIEW#<planId>"`, `"WORKSPACE#<planId>"` | Prefix + ID | The prefix separates entity families sharing the event partition so `begins_with` selects exactly one family, and the `#` delimiter guarantees no cross-family key collision (e.g. `PLAN#x` never equals `REVIEW#x`). These prefixes are load-bearing — unlike a pk prefix, the sort key is where family selection happens. |
| `sk` (assignment) | `"ASSIGN#<planId>#<participantId>"` | Prefix + composite ID | Keeps all assignments of one plan contiguous in the event partition, so "list one plan's assignments" is a single `begins_with` query and a participant's seat is an exact `GetItem`. Living in the event partition removes the old composite `EVENT#…#PLAN#…` partition key — one key dialect instead of two. |
| `sk` (history) | `"history#<timestamp>#<id>"` | Prefix + timestamp + ID | Timestamp first makes string order equal time order, so a plain `Query` returns newest-first without an index; the random `<id>` suffix prevents overwrite when two changesets share a millisecond — the same scheme as the Offerings `history#` keys. |
| `<planId>`, `<layoutId>`, `<policyId>` | ULID | — | Immutable versions; lexicographically time-sortable, so version lists are chronological without timestamp attributes or extra sort keys. |
| `<participantId>` | Stable allocation-unit ID | — | Scoped to the event, stable across plan versions; Emperor is one registration occupying two seats, never two registrations. |

Deliberately **not** keys: `publicationStatus`, `registrationStatus`, attendance `status`,
per-plan assignment pointers, etc. No listed access pattern needs to find items by those
attributes alone — they are always read inside a known partition — so indexing them would only
add write cost.

## Entities

### Configuration entity

#### Description

Per-event singleton holding the active pointers and the three revision counters. Everything
here is mutable; the item is the concurrency root of the event — pointer swaps and workspace
saves are conditional writes against it.

| Attribute                   | Type                        | Notes                                                                                                   |
| --------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------- |
| `pk`                        | `string`                    | Canonical event ID                                                                                      |
| `sk`                        | `"CONFIG"`                  | Fixed literal                                                                                            |
| `activeLayoutVersionId`     | `string`                    | Layout version used by new solves                                                                        |
| `policyVersionId`           | `string`                    | Policy version loaded by the solver; changed only through the Settings dialog                            |
| `preferences`               | `{key: PREFERENCE_KEY, enabled: boolean}[]` | Ordered preference list; order defines priority, exactly the three solver keys           |
| `inputRevision`             | `number`                    | Increments when registrations or solver-input configuration change                                       |
| `attendanceRevision`        | `number`                    | Increments when shared attendance changes                                                                |
| `workspaceRevision`         | `number`                    | Monotonic optimistic-concurrency revision for the current workspace                                      |
| `workspaceBasePlanVersionId`| `string \| null`            | Plan the current workspace is based on                                                                   |
| `latestPlanVersionId`       | `string \| null`            | Latest generated or published plan                                                                       |
| `publishedPlanVersionId`    | `string \| null`            | The only public-plan pointer; `null` until first publication                                             |
| `updatedAt`                 | `number`                    | Epoch milliseconds                                                                                       |
| `updatedBy`                 | `string`                    | Authenticated staff actor                                                                                |

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
    "inputRevision": 12,
    "attendanceRevision": 4,
    "workspaceRevision": 7,
    "workspaceBasePlanVersionId": "01JPLANEXAMPLE",
    "latestPlanVersionId": "01JPLANEXAMPLE",
    "publishedPlanVersionId": null,
    "updatedAt": 1790640000000,
    "updatedBy": "usr_staff_01"
}
```

### Registration entity

#### Description

One seating allocation unit per confirmed or prospective attendee. Flattened attributes replace
the old nested `participant` map — the map duplicated `participant_id` (already the `sk`) and
forced deep updates. Values are a frozen solver-input snapshot at solve time; upstream Offerings
changes arrive only through an explicit import/update operation. There is no `sourceHash`
attribute: import deduplication is a bounded partition query with a Filter Expression (see
access patterns), so a hash attribute and its GSI would be storage spent on a low-frequency
pattern.

| Attribute                  | Type                                          | Notes                                                                                        |
| -------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `pk`                       | `string`                                      | Canonical event ID                                                                           |
| `sk`                       | `"REG#<participantId>"`                       | `<participantId>` - stable allocation-unit key                                               |
| `fullName`                 | `string`                                      | Authoritative registered name                                                                |
| `registrationStatus`       | `REGISTRATION_STATUS`                         | Never derived from attendance                                                                |
| `contributionTier`         | `CONTRIBUTION_TIER`                           | Registered bundle tier                                                                       |
| `contributionAmountRm`     | `number`                                      | Whole-ringgit contribution amount                                                            |
| `requiresAccessibleSeat`   | `boolean`                                     | Explicit accessibility requirement                                                           |
| `participantCategory`      | `PARTICIPANT_CATEGORY`                        | Solver category                                                                              |
| `eventsJoinedLast2Years`   | `number`                                      | Snapshot used by activeness scoring                                                          |
| `age`                      | `number`                                      | Age snapshot used by the current request contract                                            |
| `adjacentPersonName`       | `string \| null`                              | Companion display field; not a separate registration                                         |
| `source`                   | `{table, pk, sk, bundleId, unitId}`           | **OPTIONAL** - authoritative Offerings reference for import reconciliation and deduplication |
| `revision`                 | `number`                                      | Conditional registration update revision                                                     |
| `createdAt` / `createdBy`  | `number` / `string`                           | Creation metadata                                                                            |
| `updatedAt` / `updatedBy`  | `number` / `string`                           | Last edit metadata                                                                           |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "REG#P001",
    "fullName": "Example Participant",
    "registrationStatus": "CONFIRMED",
    "contributionTier": "MERIT",
    "contributionAmountRm": 3000,
    "requiresAccessibleSeat": false,
    "participantCategory": "GENERAL_DEVOTEE",
    "eventsJoinedLast2Years": 0,
    "age": 30,
    "adjacentPersonName": null,
    "source": { "table": "Offerings", "pk": "0123456789", "sk": "A00001", "bundleId": "bundle_01", "unitId": "1" },
    "revision": 3,
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01",
    "updatedAt": 1790640000000,
    "updatedBy": "usr_staff_01"
}
```

### Attendance entity

#### Description

One current attendance item per registration, kept as a **separate item rather than an attribute
on the registration** so event-day toggles never collide with registration revisions and never
rewrite the frozen solver snapshot. Status applies to the whole registration including both
Emperor occupants.

| Attribute    | Type               | Notes                                          |
| ------------ | ------------------ | ---------------------------------------------- |
| `pk`         | `string`           | Canonical event ID                             |
| `sk`         | `"ATTENDANCE#<participantId>"` | One current item per registration   |
| `status`     | `ATTENDANCE_STATUS`| `PRESENT` or `ABSENT`                          |
| `changedAt`  | `number`           | Epoch milliseconds                             |
| `changedBy`  | `string`           | Authenticated staff actor                      |
| `revision`   | `number`           | Conditional attendance update revision         |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "ATTENDANCE#P001",
    "status": "ABSENT",
    "changedAt": 1790640000000,
    "changedBy": "usr_staff_01",
    "revision": 4
}
```

### Layout entity

#### Description

Immutable layout version. Written once at commit; never updated. The hall is small
(16 × 16 = 256 seats), so the complete seat list fits comfortably in one item — the old
manifest/part-chunking design is dropped.

| Attribute   | Type     | Notes                                                     |
| ----------- | -------- | --------------------------------------------------------- |
| `pk`        | `string` | Canonical event ID                                        |
| `sk`        | `"LAYOUT#<layoutId>"` | `<layoutId>` - immutable ULID version ID      |
| `layout`    | `map`    | Complete production layout: dimensions, `accessible_positions`, `approved_pairs`, every physical seat incl. blocked |
| `contentHash` | `string` | Hash of the canonical layout JSON                       |
| `createdAt` | `number` | Commit time as epoch milliseconds                         |
| `createdBy` | `string` | Layout author                                             |

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
    "contentHash": "sha256:…",
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01"
}
```

### Plan entity

#### Description

Immutable plan version carrying its frozen solver request and result. `planVersionId` is a ULID,
so `sk` order is creation order and the newest-first listing needs no timestamp attribute. The
old stored `expectedPublishedPlanVersionId` is removed — it was a compare-and-swap *condition
parameter*, not entity state; publication passes it as a condition instead. `operations`
preserves display names, notes, dock state and attendance so a published manual snapshot remains
self-contained.

| Attribute                  | Type                        | Notes                                                            |
| -------------------------- | --------------------------- | ---------------------------------------------------------------- |
| `pk`                       | `string`                    | Canonical event ID                                               |
| `sk`                       | `"PLAN#<planId>"`           | `<planId>` - immutable ULID version ID                           |
| `publicationStatus`        | `PUBLICATION_STATUS`        | `DRAFT`, `PUBLISHED` or `SUPERSEDED`                             |
| `contentHash`              | `string`                    | Hash of the complete plan document                               |
| `sourceRequest`            | `map`                       | Frozen solver input (participants, attendance, layout, preferences, solver settings) |
| `result`                   | `map`                       | Frozen assignments, floor plan, quality, diagnostics, solver status |
| `operations`               | `map`                       | `participantId → workspace item`; preserved manual snapshot state |
| `predecessorPlanVersionId` | `string \| null`            | Previous plan in the editing or repair lineage                   |
| `manuallyModified`         | `boolean`                   | True for manual or absence-repair output                         |
| `workingRevision`          | `number \| null`            | Workspace revision captured by a manual publication              |
| `createdAt` / `createdBy`  | `number` / `string`         | Creation metadata                                                |
| `publishedAt` / `publishedBy` | `number` / `string`, optional | Set only on explicit publication                             |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "PLAN#01JPLANEXAMPLE",
    "publicationStatus": "DRAFT",
    "contentHash": "sha256:…",
    "sourceRequest": { "event_id": "evt_2026_01", "generation_mode": "INITIAL", "participants": [], "layout": {}, "solver": {} },
    "result": { "status": "success", "assignments": [], "floor_plan": {} },
    "operations": { "P001": { "seat_ids": ["R01-S07"], "attendance_status": "PRESENT" } },
    "predecessorPlanVersionId": null,
    "manuallyModified": false,
    "workingRevision": 7,
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01",
    "publishedAt": null,
    "publishedBy": null
}
```

### Workspace entity

#### Description

The mutable current editing state. `WORKSPACE#CURRENT` is overwritten on every save under a
`revision` condition; history of saves is intentionally not kept here — durable history lives in
the History entity and per-plan snapshots in workspace versions. The state stores only the
editable `items`; registration context is read from the `REG#` items at load time instead of
duplicating a read-only snapshot inside every save.

| Attribute          | Type               | Notes                                                                    |
| ------------------ | ------------------ | ------------------------------------------------------------------------ |
| `pk`               | `string`           | Canonical event ID                                                       |
| `sk`               | `"WORKSPACE#CURRENT"` | Fixed literal; one active workspace per event                          |
| `basePlanVersionId`| `string`           | Plan opened by the workspace                                             |
| `revision`         | `number`           | Monotonic optimistic-concurrency revision                                |
| `state`            | `map`              | `{items: participantId → workspace item}`; exactly one entry per registration |
| `savedAt`          | `number`           | Epoch milliseconds                                                       |
| `savedBy`          | `string`           | Last workspace editor                                                    |

##### `state.items[<participantId>]`

| Attribute           | Type               | Notes                                                 |
| ------------------- | ------------------ | ----------------------------------------------------- |
| `seat_ids`          | `string[]`         | Empty only for a docked registration                  |
| `display_names`     | `string[]`         | One name per occupant; Emperor has two entries        |
| `note`              | `string`           | Staff note, maximum 2,000 characters                  |
| `dock_reason`       | `string`           | Temporary or absence-related dock explanation         |
| `previous_seat_ids` | `string[]`         | Previous location used by manual history and absence repair |
| `changed_at`        | `string \| null`   | Optional ISO timestamp for the working item           |
| `attendance_status` | `ATTENDANCE_STATUS`| `PRESENT` or `ABSENT` for the entire registration     |

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
                "dock_reason": "",
                "previous_seat_ids": [],
                "changed_at": null,
                "attendance_status": "PRESENT"
            }
        }
    },
    "savedAt": 1790640000000,
    "savedBy": "usr_staff_01"
}
```

### Workspace version entity

#### Description

Immutable workspace snapshot bound to a plan, used when staff explicitly reopen an older plan.
Same shape as `WORKSPACE#CURRENT` minus `basePlanVersionId`, which the `sk` already encodes.

| Attribute  | Type     | Notes                                                |
| ---------- | -------- | ---------------------------------------------------- |
| `pk`       | `string` | Canonical event ID                                   |
| `sk`       | `"WORKSPACE#<planId>"` | Saved workspace associated with one plan |
| `revision` | `number` | Workspace revision at the time this version was saved |
| `state`    | `map`    | Same `state` map as `WORKSPACE#CURRENT`              |
| `savedAt`  | `number` | Epoch milliseconds                                    |
| `savedBy`  | `string` | Actor who saved the version                           |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "WORKSPACE#01JPLANEXAMPLE",
    "revision": 6,
    "state": { "items": {} },
    "savedAt": 1790640000000,
    "savedBy": "usr_staff_01"
}
```

### Review entity

#### Description

Safeguard review state for one plan/workspace baseline. Mutable per plan; written and patched
during the review workflow only.

| Attribute          | Type                       | Notes                                                     |
| ------------------ | -------------------------- | --------------------------------------------------------- |
| `pk`               | `string`                   | Canonical event ID                                        |
| `sk`               | `"REVIEW#<planId>"`        | Review for one plan baseline                              |
| `reviewStatus`     | `REVIEW_STATUS`            | `NOT_CHECKED`, `IN_PROGRESS` or `PASSED`                  |
| `checkedRevision`  | `number \| null`           | Workspace revision checked                                |
| `findings`         | `map[]`                    | C12/C13 red and C15/C16 yellow findings                   |
| `acknowledgements` | `map`                      | Staff override status, note, actor and timestamp          |
| `updatedAt` / `updatedBy` | `number` / `string` | Review actor metadata                                     |

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "REVIEW#01JPLANEXAMPLE",
    "reviewStatus": "IN_PROGRESS",
    "checkedRevision": 6,
    "findings": [{ "finding_id": "C15:P001:R02-S01", "rule_id": "C15", "severity": "YELLOW", "status": "OPEN" }],
    "acknowledgements": {},
    "updatedAt": 1790640000000,
    "updatedBy": "usr_staff_01"
}
```

### Assignment entity

#### Description

Read projection of one plan's complete assignments, one item per eligible registration, stored
in the event partition under an `ASSIGN#` sort-key prefix. Contains public seat data only — no
payment, category, diagnostics or review fields.

| Attribute        | Type                              | Notes                                        |
| ---------------- | --------------------------------- | -------------------------------------------- |
| `pk`             | `string`                          | Canonical event ID                           |
| `sk`             | `"ASSIGN#<planId>#<participantId>"` | One assignment for an eligible registration |
| `registeredName` | `string`                          | Name from the registration snapshot          |
| `allocationType` | `ALLOCATION_TYPE`                 | `EMPEROR_PAIR` or `SINGLE`                   |
| `seatIds`        | `string[]`                        | Ordered assigned seat IDs                    |
| `seats`          | `map[]`                           | `seat_id`, `row_number`, `physical_position`, `priority_rank`, `zone`, `display_name` |

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

Immutable, event-independent solver-policy version. Written once; the Settings dialog never
edits a version in place — saving changes writes a **new** version and conditionally moves the
event's `CONFIG.policyVersionId` pointer, so every existing plan keeps referencing the exact
policy it was solved under. See [Policy mutability](#policy-mutability) for which fields the
dialog may change.

| Attribute              | Type                     | Notes                                                                     |
| ---------------------- | ------------------------ | ------------------------------------------------------------------------- |
| `pk`                   | `"POLICY"`               | Reserved literal; single shared registry partition                          |
| `sk`                   | `"policy#<policyId>"`    | `<policyId>` - immutable ULID version ID                                   |
| `tierOrder`            | `CONTRIBUTION_TIER[]`    | Tier precedence used by the solver                                         |
| `tierMinimums`         | `map`                    | Tier → whole-ringgit minimum (contribution tier boundary)                  |
| `categoryZoneCosts`    | `map`                    | `PARTICIPANT_CATEGORY → zone → cost`; defines category/zone behaviour      |
| `rankWeights`          | `number[]`               | Relative preference weights matched to preference rank order               |
| `initialPacking`       | `string`                 | Solver packing strategy                                                    |
| `tierSeatPrecedence`   | `string`                 | Solver tier-seat rule                                                      |
| `normalizationVersion` | `string`                 | Desirability normalization; engine-coupled, not user-editable              |
| `solverBuildId`        | `string`                 | Deployment artifact this policy is validated against                       |
| `contentHash`          | `string`                 | Hash of the canonical policy document                                      |
| `createdAt` / `createdBy` | `number` / `string`   | Creation provenance                                                        |

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
    "initialPacking": "STRICT",
    "tierSeatPrecedence": "HARD_ALL_PHYSICAL_SEATS",
    "normalizationVersion": "desirability-v2",
    "solverBuildId": "git:<commit-sha>",
    "contentHash": "sha256:…",
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01"
}
```

### History entity

#### Description

Append-only audit log modelled on the Offerings History entity. One row records one logical
action (a "changeset") that may touch several rows of this event at once (e.g. an import that
creates multiple registrations, or a workspace save with attendance toggles). Each item names
the affected row by that row's own `sk` — the prefix (`"REG#"`, `"ATTENDANCE#"`, `"PLAN#"`,
`"CONFIG"`, …) identifies the kind — and carries full-row snapshots: `before`/`after` for
updates, `after` only for creates and restores, `before` only for deletes. Snapshots are never
partial and never contain nulls: a removed attribute is simply absent.

This is a log, not working state: access frequency is **low**, and in practice only the most
recent changeset is read (`Limit 1`, descending) to answer "what changed last". Current state
is always read from the live entities, never reconstructed from history. The timestamp-first
`sk` makes "newest first" a plain `Query` with no index; the random `<id>` prevents identical-
timestamp overwrite.

| Attribute   | Type                        | Notes                                                                                                                 |
| ----------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `pk`        | `string`                    | Canonical event ID                                                                                                    |
| `sk`        | `"history#<timestamp>#<id>"`| `<timestamp>` - action trigger time as UNIX epoch timestamp <br><br> `<id>` - random ID preventing overwrite for identical timestamps |
| `updatedBy` | `string`                    | Authenticated actor that triggered the action                                                                          |
| `items`     | `SeatingHistoryItem[]`      | Affected rows of this event (minimum 1)                                                                                |

##### `SeatingHistoryItem`

| Attribute | Type                                          | Notes                                                                                              |
| --------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `sk`      | `"REG#<id>" \| "ATTENDANCE#<id>" \| "PLAN#<id>" \| "CONFIG" \| …` | The affected row's own `sk` value — the prefix identifies what changed             |
| `action`  | `HISTORY_ACTION`                              | Action triggered for this specific row — items within the same changeset may differ                |
| `before`  | Full entity row as persisted                  | The row before the change. Present for `"update"` and `"delete"` **ONLY**                          |
| `after`   | Full entity row as persisted                  | The row as written. Present for `"create"`, `"restore"`, and `"update"` **ONLY**                   |

Snapshots include audit fields and both table keys; the history facet strips them for display.

#### Example

```
{
    "pk": "evt_2026_01",
    "sk": "history#1790640000000#audit_01",
    "updatedBy": "usr_staff_01",
    "items": [
        {
            "sk": "ATTENDANCE#P001",
            "action": "update",
            "before": {
                "pk": "evt_2026_01",
                "sk": "ATTENDANCE#P001",
                "status": "PRESENT",
                "changedAt": 1790639000000,
                "changedBy": "usr_staff_01",
                "revision": 3
            },
            "after": {
                "pk": "evt_2026_01",
                "sk": "ATTENDANCE#P001",
                "status": "ABSENT",
                "changedAt": 1790640000000,
                "changedBy": "usr_staff_01",
                "revision": 4
            }
        },
        {
            "sk": "CONFIG",
            "action": "update",
            "before": { "pk": "evt_2026_01", "sk": "CONFIG", "attendanceRevision": 3, "…": "…" },
            "after":  { "pk": "evt_2026_01", "sk": "CONFIG", "attendanceRevision": 4, "…": "…" }
        }
    ]
}
```

## Facets

Facets are the application-facing shapes derived from entities. `pk` and `sk` are replaced with
clean domain IDs extracted from their values; no facet exposes table keys.

### Configuration facet

| Attribute                   | Derived from                              | Type                          |
| --------------------------- | ----------------------------------------- | ----------------------------- |
| `eventId`                   | `pk`                                      | `string`                      |
| `activeLayoutVersionId`     | `activeLayoutVersionId`                   | `string`                      |
| `policyVersionId`           | `policyVersionId`                         | `string`                      |
| `preferences`               | `preferences`                             | `{key, enabled}[]`            |
| `inputRevision`             | `inputRevision`                           | `number`                      |
| `attendanceRevision`        | `attendanceRevision`                      | `number`                      |
| `workspaceRevision`         | `workspaceRevision`                       | `number`                      |
| `workspaceBasePlanVersionId`| `workspaceBasePlanVersionId`              | `string \| null`              |
| `latestPlanVersionId`       | `latestPlanVersionId`                     | `string \| null`              |
| `publishedPlanVersionId`    | `publishedPlanVersionId`                  | `string \| null`              |
| `updatedAt` / `updatedBy`   | `updatedAt` / `updatedBy`                 | `number` / `string`           |

### Registration facet

`participantId` is extracted from the `sk`; the flattened attributes map one-to-one, so the
solver-request builder re-injects `participant_id` into the request payload without it ever
being stored.

| Attribute                 | Derived from                                        | Type                       |
| ------------------------- | --------------------------------------------------- | -------------------------- |
| `participantId`           | `sk` - extract id from `"REG#<id>"`                 | `string`                   |
| `fullName`                | `fullName`                                          | `string`                   |
| `registrationStatus`      | `registrationStatus`                                | `REGISTRATION_STATUS`      |
| `contributionTier`        | `contributionTier`                                  | `CONTRIBUTION_TIER`        |
| `contributionAmountRm`    | `contributionAmountRm`                              | `number`                   |
| `requiresAccessibleSeat`  | `requiresAccessibleSeat`                            | `boolean`                  |
| `participantCategory`     | `participantCategory`                               | `PARTICIPANT_CATEGORY`     |
| `eventsJoinedLast2Years`  | `eventsJoinedLast2Years`                            | `number`                   |
| `age`                     | `age`                                               | `number`                   |
| `adjacentPersonName`      | `adjacentPersonName`                                | `string \| null`           |
| `source`                  | `source`                                            | `{table, pk, sk, bundleId, unitId} \| undefined` |
| `revision`                | `revision`                                          | `number`                   |
| `createdAt` / `updatedAt` | `createdAt` / `updatedAt`                           | `number`                   |

### Plan summary facet

Listing shape for the plan-history dropdown; the heavy `sourceRequest`/`result`/`operations`
maps are loaded only when a plan is opened.

| Attribute                 | Derived from                                     | Type                    |
| ------------------------- | ------------------------------------------------ | ----------------------- |
| `planId`                  | `sk` - extract id from `"PLAN#<id>"`             | `string`                |
| `publicationStatus`       | `publicationStatus`                              | `PUBLICATION_STATUS`    |
| `manuallyModified`        | `manuallyModified`                               | `boolean`               |
| `predecessorPlanVersionId`| `predecessorPlanVersionId`                       | `string \| null`        |
| `createdAt` / `createdBy` | `createdAt` / `createdBy`                        | `number` / `string`     |
| `publishedAt` / `publishedBy` | `publishedAt` / `publishedBy`                | `number` / `string`, optional |

### Assignment display facet

Public projection returned to authenticated participants and the hall display; identical to the
entity minus both table keys, with the participant and plan IDs re-derived from the composite
`sk`.

| Attribute        | Derived from                                                        | Type             |
| ---------------- | ------------------------------------------------------------------- | ---------------- |
| `planId`         | `sk` - extract second segment from `"ASSIGN#<planId>#<participantId>"` | `string`      |
| `participantId`  | `sk` - extract third segment from `"ASSIGN#<planId>#<participantId>"`  | `string`      |
| `registeredName` | `registeredName`                                                    | `string`         |
| `allocationType` | `allocationType`                                                    | `ALLOCATION_TYPE`|
| `seats`          | `seats`                                                             | `map[]`          |

### History facet

Display projection of one changeset row, newest first when listed. Snapshots are stripped of the
table keys (`pk`/`sk`) and audit fields — the client never sees the table representation. Which
snapshot(s) an item carries is dictated by its action, so no `before`/`after` key is ever
`undefined`.

| Attribute   | Derived from                                                  | Type                          |
| ----------- | -------------------------------------------------------------- | ----------------------------- |
| `eventId`   | `pk`                                                          | `string`                      |
| `timestamp` | `sk` - extract timestamp from `"history#<timestamp>#<id>"`     | `number`                      |
| `updatedBy` | `updatedBy`                                                    | `string`                      |
| `items`     | `items`, per item:                                             | `SeatingHistoryItemDisplay[]` |

##### `SeatingHistoryItemDisplay`

| Attribute | Derived from                                                                       | Type                                           |
| --------- | ------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `kind`    | `sk` - `"REG#<id>"` → `"registration"`, `"ATTENDANCE#<id>"` → `"attendance"`, `"PLAN#<id>"` → `"plan"`, `"CONFIG"` → `"configuration"` | `string` |
| `targetId`| `sk` - extract id after the prefix; `null` for `"CONFIG"`                            | `string \| null`                               |
| `action`  | `action`                                                                             | `HISTORY_ACTION`                               |
| `before`  | `before` - audit fields and table keys stripped                                      | Entity-specific display map                     |
| `after`   | `after` - audit fields and table keys stripped                                       | Same as `before`                                |

`before` is present for `"update"`/`"delete"` only; `after` for `"create"`/`"restore"`/`"update"` only.

## Secondary indexes

None. Every access pattern above is a key-condition query on the base table; the only filter
(an import deduplication check on `source`) runs over one bounded event partition at low
frequency, which is cheaper than maintaining a GSI and a hash attribute for it. Lifecycle
attributes such as `publicationStatus` or attendance `status` are never queried alone — they are
always read inside a known partition — so indexing them would add write cost for patterns nobody
performs.

## Policy mutability

Inference on each policy field — will staff legitimately want to change it, and where.

| Field                  | Changes? | Rationale                                                                 | Settings dialog                          |
| ---------------------- | -------- | -------------------------------------------------------------------------- | ---------------------------------------- |
| `tierMinimums`         | **Yes**  | Contribution tier boundaries (RM5,000 / RM3,000 / RM2,000) are business decisions that shift per event cycle | **Editable** — tier boundary inputs |
| `categoryZoneCosts`    | **Yes**  | Which categories sit in which zones, and how strongly, is organisers' judgement | **Editable** — category list + per-zone costs |
| `tierOrder`            | Rarely   | Fixed by the temple's contribution hierarchy                               | **Editable** (advanced section) with validation against `tierMinimums` keys |
| `rankWeights`          | **Yes**  | Relative preference strength may be retuned between generations            | **Editable** — weight sliders/inputs; validated to match enabled preference count |
| `initialPacking`       | Rarely   | Solver strategy, but organisers may prefer loose packing for small events  | **Editable** (advanced section)          |
| `tierSeatPrecedence`   | No       | Business rule tied to solver semantics; changing it changes plan meaning    | Not exposed                              |
| `normalizationVersion` | No       | Tied to the deployed solver engine build                                   | Not exposed; changes only with a solver release |
| `solverBuildId`        | No       | Deployment provenance, recorded at seed time                               | Not exposed                              |

Flow for a Settings save: `PutItem` new `policy#<ULID>` → conditional `UpdateItem` on
`CONFIG.policyVersionId` → history changeset (`"create"` for the policy row, `"update"` for
`CONFIG`). Because versions are immutable, previously published plans remain reproducible, and
"reset to previous policy" is just repointing `CONFIG.policyVersionId`.

Preference enablement/order (`CONFIG.preferences`) is per-event state, not policy — it lives in
the Configuration entity and is likewise editable from the Settings dialog without a new policy
version.

## Boundary with existing tables

| Existing table | Change                                                            | Notes                                                                                       |
| -------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Events         | Optional attributes on the existing `meta` item: `seatingEnabled`, `offeringEventId`, `seatingSchemaVersion` | The Events table already defines the event metadata structure; Seating adds no event entity of its own and uses the Events `pk` value directly as its own partition key |
| Offerings      | None                                                              | Read-only import source; the canonical `[table, pk, sk, bundleId, unitId]` tuple is stored in `Registration.source` for reconciliation and deduplication |
| Auth           | None                                                              | Actor IDs only; user→registration authorization is resolved by the host system before Seating calls |
