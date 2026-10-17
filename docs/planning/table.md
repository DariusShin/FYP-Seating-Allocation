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
- **Key-derived typing.** There is no `entityType` attribute. `"REG#"`, `"PLAN#"`, `"ASSIGN#"`…
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
  are written once and never updated — with one documented exception: `PLAN#.printArtifacts`,
  a post-hoc provenance map of S3 print uploads (see the Plan entity) whose content-bearing
  attributes stay frozen. Mutable state is concentrated in few, well-known items —
  `CONFIG` (settings plus the publication pointer) and `WORKSPACE#CURRENT` (with its own
  optimistic-lock revision) — so all concurrency control happens through
  conditional writes on those items only.
- **Staleness by content, not counters.** There are no revision counters on `CONFIG` guarding
  registrations. Every plan embeds its frozen `sourceRequest`, and opening a draft
  already reads all live registrations and layout — so staleness ("registrations
  changed since this draft was generated") is detected at the moment it matters by comparing the
  plan snapshot against the live items already in hand. Counters would add a cross-item write to
  every registration save while answering only "something changed", never "what changed".

## Type Enums

| Group                 | Values                                                         | Notes                                              |
| --------------------- | -------------------------------------------------------------- | -------------------------------------------------- |
| `CONTRIBUTION_TIER`   | `"EMPEROR" \| "MERIT" \| "BODHI"`                              | Registered bundle tier; Emperor occupies two seats |
| `PARTICIPANT_CATEGORY`| `"MONASTIC" \| "COMMITTEE" \| "VOLUNTEER" \| "GENERAL_DEVOTEE"`| Solver category driving zone costs                 |
| `PUBLICATION_STATUS`  | `"DRAFT" \| "PUBLISHED" \| "SUPERSEDED"`                       | Plan lifecycle                                     |
| `ALLOCATION_TYPE`     | `"SINGLE" \| "EMPEROR_PAIR"`                                   | One seat vs approved pair                          |
| `PREFERENCE_KEY`      | `"contribution_seat" \| "activeness" \| "category_zone"`       | Exactly these three, in priority order             |
| `FINDING_SEVERITY`   | `"RED" \| "YELLOW"`                                            | Blocking vs advisory findings                      |

## Access patterns

Frequency is per event and per seating workflow cycle (import → generate → edit → review →
publish). "high" = touched on nearly every screen or action; "low" =
written/read at setup or at explicit workflow steps.

| Access Pattern | Table/GSI/LSI | Key Condition | Filter Expression | Frequency |
| -------------- | ------------- | ------------- | ----------------- | --------- |
| Get seating configuration for an event (and conditionally update its pointers: active layout, active policy, published plan) | Table | PK = eventId<br>SK = `"CONFIG"` | — | high |
| List all registrations for an event (import, solver request build, workspace open) | Table | PK = eventId<br>SK begins_with(`"REG#"`) | — | high |
| Import / re-import reconciliation — find existing seating rows by their Offerings/Invoice source before writing (create, update or delete the reconciled rows). After import no runtime flow edits a single registration row: display-name/note edits live in the workspace | Table | PK = eventId<br>SK begins_with(`"REG#"`) | `source.pk = :pk AND source.sk = :sk AND source.bundleId = :bundle` | low |
| Get a layout version (via `CONFIG.activeLayoutVersionId`) | Table | PK = eventId<br>SK = `"LAYOUT#<layoutId>"` | — | low |
| Get one plan (open workspace, print, detail) | Table | PK = eventId<br>SK = `"PLAN#<planId>"` | — | high |
| List plan versions, newest first (plan-history/version-selection dropdown; also draft discovery after a solve completes — the client lists the newest plan rather than reading a stored "latest" pointer) | Table | PK = eventId<br>SK begins_with(`"PLAN#"`) | — (plan IDs are ULIDs, so descending `sk` order is creation order) | low |
| Publish a plan — swap `CONFIG` pointers and plan status in one transaction with CAS on the published pointer. **Safeguard review is stateless:** findings are recomputed from the plan + workspace state inside the publication flow, and every blocking (RED) finding must be explicitly overridden in the same publish request (finding ID, note, actor), validated against the freshly computed set — review progress is never persisted, so leaving the review route restarts it | Table | PK = eventId<br>SK = `"CONFIG"` *and* SK = `"PLAN#<planId>"` | — (CAS is a condition expression on `publishedPlanVersionId`, not a filter) | low |
| Load and save the current workspace (save is conditional on the workspace item's own `revision`; no `CONFIG` write involved) | Table | PK = eventId<br>SK = `"WORKSPACE#CURRENT"` | — | high |
| Get the workspace snapshot bound to an older plan | Table | PK = eventId<br>SK = `"WORKSPACE#<planId>"` | — | low |
| List all assignments of one plan (hall display, print) | Table | PK = eventId<br>SK begins_with(`"ASSIGN#<planId>#"`) | — | high |
| Participant views their own seat in a plan | Table | PK = eventId<br>SK = `"ASSIGN#<planId>#<participantId>"` | — | high |
| Get the active policy for a solve (via `CONFIG.policyVersionId`; also validates the policy a plan references at publication) | Table | PK = `"POLICY"`<br>SK = `"policy#<policyId>"` | — | low |

## Key design

| Key | Value | Kind | Reason |
| --- | ----- | ---- | ------ |
| `pk` | `<eventId>` | Bare domain ID | The host Events system's canonical event ID, the same value the Events table uses as its `pk`. Every seating item is event-owned, so one event = one partition and every per-event query is a single-partition read. No prefix: no Key Condition ever needed to distinguish partition kinds, and the table has exactly one other family — the reserved literal `"POLICY"` partition — which the adapter protects with a reserved-word check on incoming event IDs. Dropping the prefix keeps the key dialect identical to the Events and Offerings tables. |
| `pk` (policy) | `"POLICY"` | String literal | Policies are shared across events and written only at seed/deployment time; a single tiny registry partition keeps the one policy read (exact `GetItem` by `CONFIG.policyVersionId`) one-partition simple. The active version is chosen by the event's `CONFIG` pointer, not by the partition. `"POLICY"` is a reserved partition name; the adapter rejects any event ID matching it. |
| `sk` | `"CONFIG"`, `"WORKSPACE#CURRENT"` | String literal | Fixed sort keys for the per-event singletons. They sort deterministically and `GetItem` targets them exactly; no prefix is needed because there is exactly one such item per partition. |
| `sk` | `"REG#<participantId>"`, `"LAYOUT#<layoutId>"`, `"PLAN#<planId>"`, `"WORKSPACE#<planId>"` | Prefix + ID | The prefix separates entity families sharing the event partition so `begins_with` selects exactly one family, and the `#` delimiter guarantees no cross-family key collision (e.g. `PLAN#x` never equals `WORKSPACE#x` even for the same plan ID). These prefixes are load-bearing — unlike a pk prefix, the sort key is where family selection happens. |
| `sk` (assignment) | `"ASSIGN#<planId>#<participantId>"` | Prefix + composite ID | Keeps all assignments of one plan contiguous in the event partition, so "list one plan's assignments" is a single `begins_with` query and a participant's seat is an exact `GetItem`. Living in the event partition removes the old composite `EVENT#…#PLAN#…` partition key — one key dialect instead of two. |
| `<planId>`, `<layoutId>`, `<policyId>` | ULID | — | Immutable versions; lexicographically time-sortable, so version lists are chronological without timestamp attributes or extra sort keys. |
| `<participantId>` | Stable allocation-unit ID | — | Scoped to the event, stable across plan versions; Emperor is one registration occupying two seats, never two registrations. |

Deliberately **not** keys: `publicationStatus`, per-plan assignment
pointers, etc. No listed access pattern needs to find items by those attributes alone — they are
always read inside a known partition — so indexing them would only add write cost.

## Key-shape decisions

The SK grammar is derived from the write pattern and the reference graph, never from UI surface:
a constant SK models a **mutable singleton guarded by a conditional write** (`CONFIG`,
`WORKSPACE#CURRENT`); a versioned SK
(`PREFIX#<ULID>`) models an **immutable, append-only collection whose members are addressed by
ID and referenced from other entities**. An evaluation of collapsing the versioned families to
constant SKs, on the argument that staff only ever consume the latest version, is recorded
here; all three alternatives were rejected.

**Plan — rejected (`sk = "plan"` singleton).** A constant SK is a destructive overwrite: the
published plan document must remain readable (via `CONFIG.publishedPlanVersionId`, participant
`ASSIGN#<planId>#<participantId>` lookups and the hall display) while a newer draft is
generated, so at minimum two plan versions routinely coexist and a singleton would dangle the
publication pointer. Overwriting also removes the `SUPERSEDED` lifecycle state from item space
and turns plan-by-ID retrieval (the high-frequency open/print path) into a FilterExpression
scan. The latest-version reads the proposal
optimises for are already answered without any key change: the published plan is an exact
`GetItem` through the `CONFIG` pointer, the newest draft is the `planId` returned by the solve
call (or a `Limit 1` descending query on ULID creation order — `publishedAt` is null for
drafts and therefore cannot order draft discovery).

**Layout — rejected (`sk = "layout"` singleton), lowest-stakes case.** Overwriting a layout is
survivable — every plan embeds its complete layout inside `sourceRequest`, so no reference
dangles, and the layout read is low frequency. The versioned key is retained
because a write-once singleton and a write-once versioned item are behaviourally and
financially identical, so the constant SK saves nothing while degrading three properties:
`layout_version_id` is a first-class identity in the request contract (payload/version match
is a hard validation rule), so the ID would become a name for changing bytes; draft staleness
detection downgrades from an identifier comparison to a deep content/hash comparison.
Per-event layouts also imply the current 16×16 hall is not permanent, and two concurrently
active layouts per event cannot be expressed by one item.

**Policy — rejected (`sk = "policy"` singleton), strongest case.** The policy partition is
shared across all events, so a singleton is one mutable item for the entire system: every
seed/deployment write would mutate the policy underneath every in-flight event simultaneously,
defeating the per-event `CONFIG.policyVersionId` pinning that lets different events stay on
the version they were solved under. Plans reference the exact policy version and reject
mismatches, so overwriting the item destroys the reproducibility guarantee that "every
existing plan keeps referencing the exact policy it was solved under". The policy-write flow
(append `policy#<ULID>`, then CAS the pointer) is contention-free and atomically reversible;
a singleton would replace it with overwrite CAS on one mutable item.

The general shape rule stays: collapse to a constant SK only when the item is mutable, never
referenced by identity, and needs no version lineage — which is why `preferences` lives as
attributes on `CONFIG` rather than as versioned items.

**History changeset log — deliberately excluded.** An Offerings-style `history#` audit entity
was evaluated and rejected for this flow. No seating access pattern consumes it: publication,
policy and workspace accountability are answered by per-item audit metadata that every mutable
entity already carries (`PLAN#.publishedAt/publishedBy`, `CONFIG.updatedAt/updatedBy`,
`REG#.updatedAt/updatedBy`), and the implemented service's
only audit surface is slim lifecycle rows, never full-row snapshots. Keeping the log would pair
a changeset `TransactWrite` with every mutation — including 2× snapshot cost on the
highest-frequency workspace save — for a log whose only realistic read is a `Limit 1` "what
changed last" already answered by `updatedAt`. It also carries no functional weight: versioning
is carried entirely by the immutable `PLAN#`/`LAYOUT#`/`policy#` families plus workspace
versions, staleness is detected by content comparison against live items, and post-import
refund deletions remain reconstructable from the upstream `Registration.source` reference. The
implemented client and server histories are explicitly not a shared audit trail, and no project
requirement asks for one. If traceability ever becomes a real consumer, the cheap extension is a
slim lifecycle log (action, actor, timestamp, affected `sk` list — no snapshots), listed in the
UI that reads it.

**Safeguard review state — deliberately stateless.** A persisted `REVIEW#<planId>` item
(`reviewStatus`, `checkedRevision`, findings list, acknowledgements) was evaluated and rejected
for the production integration. The safeguard check itself is stateless in the implementation —
findings are recomputed from plan + workspace state on every call, and attribution is
response-only, never persisted — so the item only stored review *progress*. Persisting progress
buys an invalidation problem (a stored `PASSED`/override can outlive the findings set it was
checked against; `checkedRevision`-style staleness rules are then mandatory) and costs a shared
mutable item that concurrent staff can race. Stateless review solves both by construction: every
check runs against the current revision, and any override of a blocking finding is carried
**inside the publish request** and validated against the freshly computed findings in the same
transaction — an acknowledgement can never authorize a finding set other than the one recomputed
at publication. The cost is accepted: leaving the review route discards progress, and overrides
(uncommon) are simply re-entered. The RED-blocking gate is therefore enforced on the publish
path, not in stored state; `FINDING_SEVERITY` survives as the classification of computed
findings.

## Cross-table provenance and derivation

The three upstream tables (events, offerings, invoice) contain **no participant or
allocation-unit entity**. Offerings partitions by invoice reference number; the only customer
identity anywhere upstream is `invoice.meta.phone`, and no reference table carries a
customer/phone index (invoice GSIs are `eventGSI`/`statusGSI` only). Two consequences:

- The seating flow must mint and persist the stable `participantId` itself — the Registration
  entity is the only place participant identity exists, so it cannot be replaced by live
  cross-table queries.
- Solver-required inputs that *do* exist upstream (`fullName`, `contributionTier`,
  `contributionAmountRm`) are **materialized at import**, not re-derived per read.

### Cost comparison: materialize at import vs derive at read

| Strategy | Reads at open/solve (high frequency) | Extra writes | Assessment |
| --- | --- | --- | --- |
| Materialize at import (chosen) | 1 Query (`REG#`) — attributes ride along rows already needed | None beyond the import's own PutItems | The cross-table join is paid once per event cycle at import (low frequency) |
| Derive at read (rejected) | `eventGSI` invoice query + ~1 offerings query per paid invoice (N ≈ 50–150) + invoice meta reads | None | ~30–150× more RCUs on every workspace open and solve; mixes live upstream data with the frozen draft state mid-edit |

Materializing also keeps the staleness model coherent: every plan embeds its frozen
`sourceRequest`, and "registrations changed since this draft" is answered by comparing that
snapshot against the live `REG#` items — including deletions from refund reconciliation —
without touching another table. Derived values that must not drift under an existing plan
(`recentEventsJoined`) are therefore *derived but frozen*: computed once at import,
refreshed only by an explicit re-import.

### Eligibility without `registrationStatus`

The four-state registration workflow (confirmed/pending/waitlisted/cancelled) belongs to the
upstream registration and invoicing flows. Seating stores only seatable allocation units:
eligibility is membership in the `REG#` family, and import admits rows sourced from invoices
with status `"paid"` only. A post-import refund or cancellation is applied by re-running the
import, which reconciles by `source` and deletes the row; an open draft detects the removal through the existing content-staleness comparison. The
current local solver contract keeps `registration_status`; the production adapter either maps
every imported row to the eligible constant or drops the field from the request schema — an
integration decision, not a table-shape one.

### Import dependencies and mapping decisions

- **Activeness derivation has no supporting index upstream — resolved by index walk.** Computing
  `recentEventsJoined` (distinct completed events the customer joined in a rolling five-year
  window) requires a phone-keyed read; the verified upstream schemas have no customer entity at
  all and the invoice table's access patterns contain no phone-keyed read, so neither a
  customer-identity source nor a justifiable `phoneGSI` exists. The derivation instead walks the
  two indexes the upstream tables already have, at import time:
  1. `events.statusGSI`: `status = "completed"`, ordered by `startDate` → keep events within the
     window ending at the seating event's own date.
  2. For each such event, `invoice.eventGSI`: `eventId = <event>` → invoice `meta` rows carry
     `phone`, `status` and `date`.
  3. Match `meta.phone` against the payer's phone **and** `status = "paid"`, collect distinct
     event IDs, count them.
  Cost is bounded by the window — one `statusGSI` query plus roughly one `eventGSI` query per
  completed event (~10–25 across a five-year window), once per import cycle — reading only
  invoices of window events, never
  the whole invoice table. Phone matching needs normalization upstream and downstream; `phone` is
  free-text per invoice and the only customer identity, so a shared family phone silently merges
  customers — document the caveat, do not "fix" it by introducing identity upstream. The count
  stays *derived but frozen* on the `REG#` row either way.
- **`fullName` source: `bundle.payer`, not `invoice.customerName` (verified against upstream).**
  The invoice `meta` carries a `customerName`, but each `bundle#<id>` row carries its own
  `payer`, and a payer may buy a bundle for someone else under their invoice. Registration is
  per bundle, so the seat display name materializes from `bundle.payer`.
- Emperor bundle → occupants mapping: **resolved — payer name only.** Both Emperor seats
  display the payer's `fullName`; the companion is not stored as a separate registration and
  no companion name attribute exists (staff edit one display name per pair in the workspace).
  The remaining open point is only whether Offerings entry `names` must stay in sync upstream.
- **Bundle → allocation unit: resolved — one bundle is exactly one allocation unit.** The
  bundle's `sk` under its invoice `pk` identifies the unit; `source.unitId` is therefore
  **removed** from `Registration.source` (it anticipated multi-unit bundles that the business
  confirms do not exist). `contributionAmountRm` is `bundle.amount` as recorded; invoice-level
  `tax`/`discount` stay in the invoice flow and are never split per bundle.

## Entities

### Configuration entity

#### Description

Per-event singleton holding the solver context — the settings a Lambda loads before running the
allocation — plus the single publication pointer. Everything here is mutable, but nothing else
is stored here: revision counters and workspace state live on the items they belong to
(`WORKSPACE#CURRENT.revision`), because duplicating them in `CONFIG` would recreate SQL-style foreign-key
redundancy and force every registration save through a config transaction.

| Attribute                   | Type                        | Notes                                                                                                   |
| --------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------- |
| `pk`                        | `string`                    | Canonical event ID                                                                                      |
| `sk`                        | `"CONFIG"`                  | Fixed literal                                                                                            |
| `activeLayoutVersionId`     | `string`                    | Layout version used by new solves                                                                        |
| `policyVersionId`           | `string`                    | Policy version loaded by the solver; set at event setup and changed only at seed/deployment — staff never edit policy in this scope |
| `preferences`               | `{key: PREFERENCE_KEY, enabled: boolean}[]` | Ordered preference list; order defines priority, exactly the three solver keys           |
| `publishedPlanVersionId`    | `string \| null`            | The only public-plan pointer; `null` until first publication; CAS anchor for publication  |
| `updatedAt`                 | `number`                    | Epoch milliseconds                                                                                       |
| `updatedBy`                 | `string`                    | Authenticated staff actor                                                                                |

#### Concurrency and staleness

- **Publication** is the only flow that writes `CONFIG` concurrently: one transaction marks the
  new plan `PUBLISHED`, marks the previous one `SUPERSEDED`, and swaps `publishedPlanVersionId`
  under a condition expression (compare-and-swap on the pointer). The pointer must live in one
  place precisely because it needs atomic swap semantics; `publicationStatus` on the plan items
  alone would give no single CAS anchor.
- **Workspace saves** never touch `CONFIG`: they are conditional writes on
  `WORKSPACE#CURRENT.revision`, which is the authoritative workspace counter. The workspace's
  `basePlanVersionId` likewise lives on the workspace item only.
- **Draft discovery** needs no `latestPlanVersionId`: plans are immutable and time-sortable, so
  the newest draft is `Query SK begins_with("PLAN#")`, `ScanIndexForward = false`, `Limit 1` —
  or simply the `planId` returned by the solve call. Keeping a "latest" pointer in `CONFIG`
  would force every plan write to transactionally update the config item for zero information
  gain.
- **Stale input** needs no `inputRevision`: every plan embeds its frozen
  `sourceRequest`, and opening a draft already lists all registrations and layout.
  The client/server compares the snapshot against those live items and surfaces "registrations
  changed since this draft — regenerate?" with the actual difference, which a counter could
  never express.

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

The seating flow's own materialization of one allocation unit, created by an explicit import
from the invoicing and offering flows — see
[Cross-table provenance and derivation](#cross-table-provenance-and-derivation). The upstream
tables carry no participant entity, so the import is where the stable `participantId` is minted
and where solver inputs that exist upstream (name, tier, amount) are resolved and frozen.
Seating-only attributes no upstream table carries (accessibility, solver category) are
captured in the same import. There is no `registrationStatus`:
every row in this family is seatable by construction, imported from an invoice with status
`"paid"`; a post-import refund is applied by re-running the import, which reconciles by
`source` and deletes the row. There is also no `sourceHash` attribute: import deduplication is
a bounded partition query with a Filter Expression (see access patterns), so a hash attribute
and its GSI would be storage spent on a low-frequency pattern. And there is no `revision`:
registration rows are written only by import reconciliation — a query-then-write pass by a
single actor that re-runs idempotently against the `source` key — so no conditional-update
consumer exists; display-name/note edits live in the workspace.

| Attribute                  | Type                                          | Notes                                                                                        |
| -------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `pk`                       | `string`                                      | Canonical event ID                                                                           |
| `sk`                       | `"REG#<participantId>"`                       | `<participantId>` - stable allocation-unit key, minted at import                             |
| `fullName`                 | `string`                                      | Payer's display name, materialized at import from the bundle's `payer` (not `invoice.customerName` — a payer may buy a bundle for someone else under their invoice); the one name staff edit per Emperor pair (both seats display it in the workspace) |
| `contributionTier`         | `CONTRIBUTION_TIER`                           | Materialized at import from the matching bundle's `type` (`emperor` → `EMPEROR`, …)          |
| `contributionAmountRm`     | `number`                                      | Materialized at import from `bundle.amount`; importance-normalization input                  |
| `requiresAccessibleSeat`   | `boolean`                                     | Seating-captured; no upstream source                                                         |
| `participantCategory`      | `PARTICIPANT_CATEGORY`                        | Seating-captured solver category                                                             |
| `recentEventsJoined`       | `number`                                      | Derived at import from the customer's prior completed events; the derivation window (rolling five years) is a documented rule, not part of the name. Frozen, refreshed only by re-import |
| `source`                   | `{table, pk, sk, bundleId}`                   | **OPTIONAL** - authoritative Offerings/Invoice reference; reconciliation key for re-import   |
| `createdAt` / `createdBy`  | `number` / `string`                           | Creation metadata                                                                            |
| `updatedAt` / `updatedBy`  | `number` / `string`                           | Last edit metadata                                                                           |

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
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01",
    "updatedAt": 1790640000000,
    "updatedBy": "usr_staff_01"
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
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01"
}
```

### Plan entity

#### Description

Immutable plan version carrying its frozen solver request and result. `planVersionId` is a ULID,
so `sk` order is creation order and the newest-first listing needs no timestamp attribute. The
old stored `expectedPublishedPlanVersionId` is removed — it was a compare-and-swap *condition
parameter*, not entity state; publication passes it as a condition instead. `workingRevision` is
removed for the same reason — the workspace revision is a live publish condition, written by the
transaction and read by no one; `publishedAt`/`publishedBy` and `manuallyModified` already mark a
manual publication. `contentHash` is removed too: it had no consumer — staleness compares frozen
`sourceRequest` against live `REG#` items by content, publication CAS keys on the pointer, and
findings recompute from the content itself; if the plan document ever moves to S3, integrity
comes free from S3 versioning/ETag and the item holds a pointer, not a duplicated hash.
`operations` preserves display names and notes so a published manual snapshot remains
self-contained. The remaining provenance attributes are all load-bearing: `sourceRequest` drives
draft-staleness detection, regeneration and the participant view's event details (and embeds the
layout so no plan reference dangles); `predecessorPlanVersionId` is the FR12 lineage reference
and the only durable record of which plan a draft was edited from once the workspace switches
base; `manuallyModified` marks output that is not the solver's as-solved result, i.e. not
reproducible from `sourceRequest` alone.

**Print artifacts (the one mutable map on an immutable item).** Every printed PDF/PNG of the
`/venue` map is uploaded to S3 once and recorded here, so repeated prints re-download the
existing file instead of regenerating it. The artifact depicts exactly this plan version's frozen
assignments and layout, which is why the pointer lives on the plan rather than on `CONFIG` (which
only knows the published plan) or the workspace (which is overwritten on every save). The plan's
*content* (`sourceRequest`, `result`, `operations`) stays frozen; `printArtifacts` is the single
post-hoc mutable map — provenance metadata, benign to mutate because the render is deterministic
from the frozen content, so a lost pointer is recovered by one re-print, never data loss. Entries
store the **S3 key, not a URL** (URLs embed bucket/prefix/expiry and rot; the adapter constructs
the URL at read time). Keys are deterministic (`plans/<planId>/venue.<format>`), so re-prints
overwrite idempotently and each format's entry is latest-wins. Written by a conditional
`UpdateItem` on the plan item after the S3 upload succeeds; read rides the existing plan
`GetItem` — no new access pattern.

| Attribute                  | Type                        | Notes                                                            |
| -------------------------- | --------------------------- | ---------------------------------------------------------------- |
| `pk`                       | `string`                    | Canonical event ID                                               |
| `sk`                       | `"PLAN#<planId>"`           | `<planId>` - immutable ULID version ID                           |
| `publicationStatus`        | `PUBLICATION_STATUS`        | `DRAFT`, `PUBLISHED` or `SUPERSEDED`                             |
| `sourceRequest`            | `map`                       | Frozen solver input (participants, layout, preferences, solver settings) |
| `result`                   | `map`                       | Frozen assignments, floor plan, quality, diagnostics, solver status |
| `operations`               | `map`                       | `participantId → workspace item`; preserved manual snapshot state |
| `printArtifacts`           | `map`                       | Format → `{s3Key, printedAt, printedBy}`; latest-wins per format (`"pdf"`, `"png"`); the only post-hoc mutable map on the plan item |
| `predecessorPlanVersionId` | `string \| null`            | Previous plan in the editing or repair lineage                   |
| `manuallyModified`         | `boolean`                   | True for manually edited output                                  |
| `createdAt` / `createdBy`  | `number` / `string`         | Creation metadata                                                |
| `publishedAt` / `publishedBy` | `number` / `string`, optional | Set only on explicit publication                             |

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
per-plan workspace versions and the client's local edit journal. The state stores only the
editable `items`; registration context is read from the `REG#` items at load time instead of
duplicating a read-only snapshot inside every save. Every registration keeps the seats the
algorithm assigned it — staff move and swap placements but can never exempt a registration from
the plan, so an assigned seat always preserves its name regardless of whether the person
attends (attendance is out of production scope; there is no absence-driven reallocation here).

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
| `seat_ids`          | `string[]`         | Assigned seat IDs; one or two (Emperor pair), never empty |
| `display_names`     | `string[]`         | One name per occupant; Emperor has two entries        |
| `note`              | `string`           | Staff note, maximum 2,000 characters                  |
| `changed_at`        | `string \| null`   | Optional ISO timestamp for the working item           |

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
    "savedAt": 1790640000000,
    "savedBy": "usr_staff_01"
}
```

### Workspace version entity

#### Description

Immutable workspace snapshot bound to a plan, used when staff explicitly reopen an older plan.
Same shape as `WORKSPACE#CURRENT` minus `basePlanVersionId`, which the `sk` already encodes.

**Why it exists despite `plan.operations`.** A plan item's `operations` map preserves only the
state as of the last manual *publication*; a solver-generated draft has none. An explicitly
saved, not-yet-published working state therefore exists nowhere else in the table — without
this item, switching from plan A to plan B (or reopening A later) would silently discard the
last saved but unpublished edits, a behaviour regression against the prototype, where saved
versions are immutable and restorable even before publication. Keeping it costs one small item
per explicit save and one exact `GetItem` on reopen; deriving instead would either lose data or
require a speculative reconstruction that can never reproduce a state no plan ever recorded.

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

### Assignment entity

#### Description

Read projection of one plan's complete assignments, one item per eligible registration, stored
in the event partition under an `ASSIGN#` sort-key prefix. Contains public seat data only — no
payment, category, diagnostics or review fields.

**Why no attendance status here (and why the projection is complete).** Attendance is out of
production scope: a seat is a contribution entitlement, so every registration keeps its assigned
seat and name whether or not the person attends, and there is no absence-driven reallocation in
this flow. The projection is therefore complete by construction — every `REG#` row yields exactly
one `ASSIGN` row per plan — and stamping a mutable status inside a write-once family that
participants read would go stale the moment reality changed and invite rewrites of immutable
rows. The event-day checklist is a read-only render over `REG#` and `ASSIGN#`, needing no status
attribute. One registration holds exactly one assignment **per plan** (Emperor is one item with
two seats); across the event it holds one per plan version, which is what makes "list one plan's
assignments" and "participant views their seat in plan X" exact key operations.

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

Immutable, event-independent solver-policy version. Written once at seed/deployment time; no
runtime flow edits a version in place — a changed policy writes a **new** version and
repoints the event's `CONFIG.policyVersionId`, so every existing plan keeps referencing the
exact policy it was solved under. See [Policy mutability](#policy-mutability) for which fields
may change and who changes them.

**Engine-coupled fields removed.** `initialPacking`, `tierSeatPrecedence`,
`normalizationVersion` and `solverBuildId` were evaluated and removed. Verified against the
solver: `initialPacking` was never read — packing is computed from the layout (`packing_pairs`)
with centre-out behaviour hardcoded in the build; `tierSeatPrecedence` was never read (it was
not even in the real policy config) — the tier-seat rule is hardcoded in the validator;
`normalizationVersion` was read once, only to echo into result diagnostics, so the stamp now
comes from the solver build's own constant; `solverBuildId` was never read — deployment
provenance lives with the deployment, and the build stamps itself into result diagnostics beside
the policy version. What remains is exactly what the solver reads: the four business-tunable
number sets below.

| Attribute              | Type                     | Notes                                                                     |
| ---------------------- | ------------------------ | ------------------------------------------------------------------------- |
| `pk`                   | `"POLICY"`               | Reserved literal; single shared registry partition                          |
| `sk`                   | `"policy#<policyId>"`    | `<policyId>` - immutable ULID version ID                                   |
| `tierOrder`            | `CONTRIBUTION_TIER[]`    | Tier precedence used by the solver                                         |
| `tierMinimums`         | `map`                    | Tier → whole-ringgit minimum (contribution tier boundary)                  |
| `categoryZoneCosts`    | `map`                    | `PARTICIPANT_CATEGORY → zone → cost`; defines category/zone behaviour      |
| `rankWeights`          | `number[]`               | Relative preference weights matched to preference rank order               |
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
    "createdAt": 1790640000000,
    "createdBy": "usr_staff_01"
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
| `publishedPlanVersionId`    | `publishedPlanVersionId`                  | `string \| null`              |
| `updatedAt` / `updatedBy`   | `updatedAt` / `updatedBy`                 | `number` / `string`           |

### Registration facet

`participantId` is extracted from the `sk`; the flattened attributes map one-to-one, so the
solver-request builder re-injects `participant_id` into the request payload without it ever
being stored. There is no `registrationStatus` in the facet: every exported row is an eligible
allocation unit by construction of the import.

| Attribute                 | Derived from                                        | Type                       |
| ------------------------- | --------------------------------------------------- | -------------------------- |
| `participantId`           | `sk` - extract id from `"REG#<id>"`                 | `string`                   |
| `fullName`                | `fullName`                                          | `string`                   |
| `contributionTier`        | `contributionTier`                                  | `CONTRIBUTION_TIER`        |
| `contributionAmountRm`    | `contributionAmountRm`                              | `number`                   |
| `requiresAccessibleSeat`  | `requiresAccessibleSeat`                            | `boolean`                  |
| `participantCategory`     | `participantCategory`                               | `PARTICIPANT_CATEGORY`     |
| `recentEventsJoined`      | `recentEventsJoined`                                | `number`                   |
| `source`                  | `source`                                            | `{table, pk, sk, bundleId} \| undefined` |
| `createdAt` / `updatedAt` | `createdAt` / `updatedAt`                           | `number`                   |

### Plan summary facet

Listing shape for the plan-history dropdown; the heavy `sourceRequest`/`result`/`operations`
maps are loaded only when a plan is opened. `printArtifacts` rides along (small map) so the
dropdown can show which versions already have a cached venue print.

| Attribute                 | Derived from                                     | Type                    |
| ------------------------- | ------------------------------------------------ | ----------------------- |
| `planId`                  | `sk` - extract id from `"PLAN#<id>"`             | `string`                |
| `publicationStatus`       | `publicationStatus`                              | `PUBLICATION_STATUS`    |
| `manuallyModified`        | `manuallyModified`                               | `boolean`               |
| `predecessorPlanVersionId`| `predecessorPlanVersionId`                       | `string \| null`        |
| `printArtifacts`          | `printArtifacts`                                 | `map`                   |
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

## Secondary indexes

None. Every access pattern above is a key-condition query on the base table; the only filter
(an import deduplication check on `source`) runs over one bounded event partition at low
frequency, which is cheaper than maintaining a GSI and a hash attribute for it. Lifecycle
attributes such as `publicationStatus` are never queried alone — they are
always read inside a known partition — so indexing them would add write cost for patterns nobody
performs.

## Policy mutability

Staff never edit policy in this scope: the only per-event solver tuning — preference
enablement and rank order — lives in `CONFIG.preferences`, and the solver reads weights by
enabled rank. Policy fields change only at seed/deployment time, by the developer, under the
same immutability discipline.

| Field                  | Changes? | Rationale                                                                 |
| ---------------------- | -------- | -------------------------------------------------------------------------- |
| `tierMinimums`         | **Yes**  | Contribution tier boundaries (RM5,000 / RM3,000 / RM2,000) are business decisions that shift per event cycle |
| `categoryZoneCosts`    | **Yes**  | Which categories sit in which zones, and how strongly, is organisers' judgement, fixed per deployment |
| `tierOrder`            | Rarely   | Fixed by the temple's contribution hierarchy                               |
| `rankWeights`          | **Yes**  | Retuned with solver releases; per-rank weights come from the enabled preference order |

Engine-coupled behaviour is not policy data: packing strategy and the tier-seat rule are
hardcoded engine semantics, and the normalization/build stamps come from the solver build's own
constants into result diagnostics (see the Policy entity).

Flow for a policy change (developer/seed time): `PutItem` new `policy#<ULID>` → conditional
`UpdateItem` on `CONFIG.policyVersionId`. Because versions are immutable, previously published
plans remain reproducible, and "reset to previous policy" is just repointing
`CONFIG.policyVersionId`.

Preference enablement/order (`CONFIG.preferences`) is per-event state, not policy — it lives in
the Configuration entity and is the one solver setting staff edit from the workspace Settings
dialog, without a new policy version.

## Boundary with existing tables

| Existing table | Change                                                            | Notes                                                                                       |
| -------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Events         | Optional attributes on the existing `meta` item: `seatingEnabled`, `offeringEventId`, `seatingSchemaVersion` | The Events table already defines the event metadata structure; Seating adds no event entity of its own and uses the Events `pk` value directly as its own partition key |
| Offerings      | None                                                              | Read-only import source; the canonical `[table, pk, sk, bundleId]` tuple is stored in `Registration.source` for reconciliation and deduplication |
| Auth           | None                                                              | Actor IDs only; user→registration authorization is resolved by the host system before Seating calls |
