# Objective 2: absence-driven incremental reallocation

Status: implemented locally. Objective 2 is controlled dynamic allocation with minimum registration movement following participant absence. Safeguard verification is a supporting feature, not a replacement research objective. Substitutions, late registrations, group changes and separate companion absence are outside this implementation.

## Staff workflow

1. In Edit plan, select a registration and choose **Mark participant absent** (or **Mark pair absent**). Its seats are released immediately in the working map and its card moves to the dock. An Emperor registration is one unit: both occupants become absent and both seats move together. Other placements stay unchanged.
2. Absent dock cards use a distinct red tint and explicit Absent label. Ordinary drag-to-dock and Send to holding dock retain PRESENT status and remain temporary editing operations.
3. Settings offers **Repair gaps after absence**, using the selected preferences and the latest saved working map. The application saves outstanding edits first; a failed save stops the operation. Present registrations in the temporary dock must be seated before repair.
4. Repair creates a private version and displays moved-registration count, movement distance and affected rows. Review the result before publication. Preference-based **Generate new draft** remains a separate complete solve and excludes absent registrations; changing attendance also enables this action without changing preferences.
5. Drag an absent card to a seat, or choose its move destination, to open **Restore attendance and assign?**. Confirm restores PRESENT status and places the whole registration as one undoable edit. Cancel or closing the dialog changes nothing. Invalid destinations do not restore attendance.
6. Review/publication requires every present confirmed registration to have its full legal allocation. Absent registrations may remain docked. Manual packing gaps remain yellow review advisories under the existing publication policy. The public map changes only on explicit publication.

## Reduced repair model

`absence_repair.py` is a separate repair entry point; it never calls the initial-generation `solve()` function. It reuses hard-rule construction and independent placement auditing so pairing, accessibility, tier/contribution ordering, unique occupancy, blocked seats, front-packed rows and east-before-west packing agree with generation.

Let A0 be the latest saved placements of present confirmed registrations. Start with rows containing absent registrations' previous seats. Registrations outside that neighbourhood remain fixed constants; only registrations inside it have alternative legal options, confined to those rows. If that model is proven INFEASIBLE, expand by one adjacent row in each direction and try again. Stop at the first feasible neighbourhood. If expansion reaches the hall boundary without a solution, report failure and preserve the saved and published maps. Within the common time budget, retain the best valid incumbent found. Return it even when the solver has not proved optimality; a timeout is an error only when no valid incumbent exists. There is no automatic full-generation fallback.

Repair optimizes these objectives in priority order:

1. Number of present registrations whose seat-ID bundle differs from A0.
2. Sum of movement distances for those registrations.
3. Ranked contribution-seat, activeness and category-zone preference cost.

An Emperor pair counts as one moved registration and two moved physical seats. Distance is doubled Manhattan distance between old/new bundle centroids in row/physical-position coordinates; integers represent half-seat distances exactly. Absent registrations are excluded from all three objectives and physical demand. Preferences cannot outweigh movement. A proven OPTIMAL stage is fixed before optimizing the next objective. If a stage returns FEASIBLE, immediately accept its independently validated incumbent, label the repair FEASIBLE and stop further optimization. If a later stage times out or returns UNKNOWN, retain the earlier valid incumbent. A proven minimum is not required to create or render a repair draft; the generation benchmark require_optimal setting does not gate interactive absence repair.

Any proven optimality is scoped to the first feasible repair neighbourhood. FEASIBLE repairs explicitly report that optimization is unproven, alongside actual moved-registration and distance scores. It is not a global minimum-movement claim across the hall. Compulsory front packing can require a neighbourhood to expand substantially after an early-row absence. A map that already satisfies all rules after the absence is retained with zero moves and no solver search. Repair does not perform generation's canonicalization passes.

## Attendance, persistence and concurrency

Registration/payment status remains immutable. `WorkingItem.attendance_status` is PRESENT or ABSENT, defaults to PRESENT for earlier workspaces, and applies to the entire registration. Saved requests capture an independent `attendance` map; solver eligibility is CONFIRMED and not ABSENT. Names and registration records are preserved in the dock and immutable source snapshot.

Saving commits attendance changes to SQLite `event_attendance`, keyed by event and registration ID, in the same transaction as the workspace revision and audit entries. Opening another saved plan applies current event attendance: absent allocations are docked; restored registrations do not receive an invented placement if that version has them docked. Attendance reconciliation invalidates previous review. Existing published snapshots remain immutable until staff explicitly publishes another version.

Repair reads the saved plan ID/revision and records that baseline on the candidate. Transactional candidate creation and first adoption reject changes to the active saved revision during computation. Previously opened versions remain available through explicit version selection. Failed/stale repairs do not switch the published pointer. Attendance changes participate in ordinary undo/redo; their event-wide effect occurs when the edited draft is saved.

## Evaluation

`tests/test_absence_repair.py` checks separate repair dispatch, exhaustive tiny-case movement/preference optimality, progressive expansion, fixed outside placements, Emperor pair handling, shared attendance, absent publication, temporary-dock rejection, stale candidate rejection, independent movement reconstruction, zero-move/all-absent cases, acceptance of FEASIBLE incumbents at every objective stage and retention after a later stage ends without a solution. Frontend tests cover atomic restore-and-place, cancellation and failure, absent styling and save-before-repair.

Research evaluation should compare incremental repair with complete regeneration both with and without movement penalties on identical absence scenarios. Measure moved registrations, moved physical seats, centroid distance, preservation rate, preference cost, independent rule satisfaction, runtime and neighbourhood expansion. Include front/middle/tail absences, multiple absences, Emperor pairs, accessibility and manually edited saved baselines. Broader benchmark/deployment results remain to be measured.
