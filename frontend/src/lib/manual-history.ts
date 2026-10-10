import Dexie, { type Table } from "dexie";
import type { WorkingItem, WorkingState, Workspace } from "./workspace";

export interface EditChange {
  participant_id: string;
  before: WorkingItem;
  after: WorkingItem;
}
export interface ManualEdit {
  operation_id: string;
  timestamp: string;
  kind: string;
  changes: EditChange[];
}
export interface HistoryContext {
  schema_version: 1;
  baseline: WorkingState;
  edits: ManualEdit[];
}
interface SaveCapture {
  state: WorkingState;
  context: HistoryContext;
  revision: number;
  sequence: number;
}
export interface LocalVersion extends SaveCapture {
  schema_version: 1;
  id: string;
  scope: string;
  parent: string | null;
  saved_at: string;
  fingerprint: string;
}
export interface LocalSession {
  schema_version: 1;
  id: string;
  scope: string;
  parent: string | null;
  revision: number;
  fingerprint: string;
  baseline: WorkingState;
  state: WorkingState;
  active: ManualEdit[];
  redo: ManualEdit[];
  sequence: number;
  generation: number;
  updated_at: string;
  pending?: SaveCapture;
}
interface JournalEntry extends ManualEdit {
  session_id: string;
  sequence: number;
  reference?: string;
}
export class HistoryDatabase extends Dexie {
  versions!: Table<LocalVersion, string>;
  sessions!: Table<LocalSession, string>;
  edits!: Table<JournalEntry, [string, number]>;
  constructor(name = "seating-manual-history-v1") {
    super(name);
    this.version(1).stores({
      versions: "id, scope, saved_at",
      sessions: "id, scope, updated_at",
      edits: "[session_id+sequence], session_id, operation_id",
    });
  }
}
const clone = <T>(value: T): T => structuredClone(value);
// Stable across Python/JSON property ordering and browser reloads.
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`)
      .join(",")}}`;
  return JSON.stringify(value);
}
export const equal = (a: unknown, b: unknown) => canonical(a) === canonical(b);
export function changesBetween(
  before: WorkingState,
  after: WorkingState,
): EditChange[] {
  if (
    !equal(before.participants, after.participants) ||
    !equal(Object.keys(before.items).sort(), Object.keys(after.items).sort())
  )
    throw Error("Registration inputs changed; reload history for this draft.");
  return Object.keys(before.items)
    .filter((pid) => !equal(before.items[pid], after.items[pid]))
    .map((pid) => ({
      participant_id: pid,
      before: clone(before.items[pid]),
      after: clone(after.items[pid]),
    }));
}
const sameSeats = (a: string[], b: string[]) =>
  equal([...a].sort(), [...b].sort());
const placementChanges = (edit: ManualEdit) =>
  edit.changes.filter((c) => !sameSeats(c.before.seat_ids, c.after.seat_ids));

export function restoration(
  state: WorkingState,
  changes: EditChange[],
): WorkingState {
  const moved = changes.filter(
    (c) => !sameSeats(c.before.seat_ids, c.after.seat_ids),
  );
  if (!moved.length) throw Error("This edit did not change positions.");
  const next = clone(state);
  // Lift the entire connected rearrangement into temporary memory first. Never
  // publish or save this intermediate dock state, or swap one single into a pair.
  for (const change of moved) {
    const item = state.items[change.participant_id];
    if (item?.attendance_status === "ABSENT")
      throw Error("Restore attendance using the dock assignment controls before restoring these seats.");
    if (!item || !sameSeats(item.seat_ids, change.after.seat_ids))
      throw Error("A registration has moved again. Preview restoration again.");
    if (!change.before.seat_ids.length)
      throw Error(
        "No earlier seated position is recorded for this registration.",
      );
    next.items[change.participant_id].seat_ids = [];
  }
  const occupied = new Set(
    Object.values(next.items).flatMap((item) => item.seat_ids),
  );
  for (const change of moved) {
    if (change.before.seat_ids.some((s) => occupied.has(s)))
      throw Error(
        "The original positions are unavailable. Include the connected registrations before restoring.",
      );
    change.before.seat_ids.forEach((s) => occupied.add(s));
    const item = state.items[change.participant_id];
    next.items[change.participant_id] = {
      ...item,
      seat_ids: [...change.before.seat_ids],
      previous_seat_ids: [...item.seat_ids],
      dock_reason: "",
      changed_at: new Date().toISOString(),
    };
  }
  return next;
}

export interface HistoryRestoration {
  state: WorkingState;
  changes: EditChange[];
  operation_ids: string[];
}

/** Find the nearest complete placement before the selected edit, closing over
 * later coupled moves and registrations occupying the original destinations.
 * This works with already-recorded DOCK / MOVE / PLACE events; no migration or
 * invented seat destination is needed. Unrelated edits and current details stay.
 */
export function restorationFromHistory(
  state: WorkingState,
  context: HistoryContext | undefined,
  operationId: string,
  relatedParticipantIds: string[] = [],
): HistoryRestoration {
  if (!context)
    throw Error(
      "Matching edit history is unavailable. Reload the saved draft before restoring.",
    );
  let index = context.edits.findIndex((e) => e.operation_id === operationId);
  if (index < 0)
    throw Error("This edit is no longer active. Check the draft again.");
  const seed = placementChanges(context.edits[index]).map(
    (c) => c.participant_id,
  );
  if (!seed.length) throw Error("This edit did not change positions.");
  // A move into a vacated seat is also connected to its former occupant when
  // that occupant is named in the linked violation. This covers an Emperor
  // moved to EMPTY seats, followed by Merit registrations filling its old pair.
  // Do not roll back arbitrary earlier occupants unrelated to these findings.
  const destinations = new Set(
    placementChanges(context.edits[index]).flatMap((c) => c.after.seat_ids),
  );
  const related = new Set(relatedParticipantIds);
  for (let i = index - 1; i >= 0 && destinations.size; i--) {
    for (const c of placementChanges(context.edits[i])) {
      const vacated = c.before.seat_ids.filter(
        (sid) => destinations.has(sid) && !c.after.seat_ids.includes(sid),
      );
      if (!vacated.length) continue;
      vacated.forEach((sid) => destinations.delete(sid));
      if (related.has(c.participant_id) && !seed.includes(c.participant_id)) {
        seed.push(c.participant_id);
        index = Math.min(index, i);
      }
    }
  }

  const before = clone(context.baseline);
  for (let i = 0; i < context.edits.length; i++) {
    for (const c of context.edits[i].changes) {
      if (!equal(before.items[c.participant_id], c.before))
        throw Error("Edit history is incomplete. No positions were changed.");
      before.items[c.participant_id] = clone(c.after);
    }
  }
  if (!equal(before, state))
    throw Error("The draft changed. Preview restoration again.");
  // Rewind the private working copy to just before the selected operation.
  for (let i = context.edits.length - 1; i >= index; i--)
    for (const c of context.edits[i].changes)
      before.items[c.participant_id] = clone(c.before);

  const owners = new Map(
    Object.entries(state.items).flatMap(([pid, item]) =>
      item.seat_ids.map((sid) => [sid, pid] as const),
    ),
  );
  for (let start = index; start >= 0; start--) {
    const affected = new Set(seed);
    let expanded = true;
    while (expanded) {
      const count = affected.size;
      // Do not split a subsequent atomic swap or chain rearrangement.
      for (let i = start; i < context.edits.length; i++) {
        const changed = placementChanges(context.edits[i]);
        if (changed.some((c) => affected.has(c.participant_id)))
          changed.forEach((c) => affected.add(c.participant_id));
      }
      for (const pid of affected)
        for (const sid of before.items[pid].seat_ids) {
          const owner = owners.get(sid);
          if (owner) affected.add(owner);
        }
      expanded = count !== affected.size;
    }
    if ([...affected].every((pid) => before.items[pid].seat_ids.length > 0)) {
      const changes = [...affected]
        .filter(
          (pid) =>
            !sameSeats(before.items[pid].seat_ids, state.items[pid].seat_ids),
        )
        .map((pid) => ({
          participant_id: pid,
          before: clone(before.items[pid]),
          after: clone(state.items[pid]),
        }));
      const operation_ids = context.edits
        .slice(start)
        .filter((e) =>
          placementChanges(e).some((c) => affected.has(c.participant_id)),
        )
        .map((e) => e.operation_id);
      return { state: restoration(state, changes), changes, operation_ids };
    }
    if (start > 0)
      for (const c of context.edits[start - 1].changes)
        before.items[c.participant_id] = clone(c.before);
  }
  throw Error(
    "This history starts with an affected registration in the dock; its earlier seated position is not recorded. Use the move controls to resolve this issue.",
  );
}

/** Shared by edit and review. Memory remains usable if browser storage fails. */
export class ManualHistory {
  session: LocalSession | null = null;
  versions: LocalVersion[] = [];
  conflicts: LocalSession[] = [];
  journal: JournalEntry[] = [];
  warning = "";
  ready = false;
  private serial = Promise.resolve();
  private listeners = new Set<() => void>();
  private tick = 0;
  private failed = false;
  constructor(readonly db = new HistoryDatabase()) {}
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  getSnapshot = () => this.tick;
  private emit() {
    this.tick++;
    this.listeners.forEach((l) => l());
  }
  private write(task: () => Promise<void>) {
    this.serial = this.serial
      .then(async () => {
        if (!this.failed) await task();
      })
      .catch((e) => {
        this.failed = true;
        this.warning = `Local recovery unavailable: ${e instanceof Error ? e.message : String(e)}. Your changes remain in memory; save the draft to the server.`;
        this.emit();
      });
    return this.serial;
  }
  async open(workspace: Workspace) {
    await this.serial;
    this.ready = false;
    this.failed = false;
    this.warning = "";
    this.versions = [];
    this.conflicts = [];
    this.journal = [];
    this.emit();
    const identity = workspace.history_scope;
    const scope = canonical([
      identity?.actor,
      identity?.event_id,
      workspace.base.plan_version_id,
    ]);
    const fingerprint = canonical([
      workspace.base.source_request?.layout ??
        workspace.base.floor_plan.rows.map((r) => ({
          row_number: r.row_number,
          seats: r.seats.map((s) => ({
            seat_id: s.seat_id,
            physical_position: s.physical_position,
            priority_rank: s.priority_rank,
            side: s.side,
            is_blocked: s.is_blocked,
            is_accessible: s.is_accessible,
          })),
        })),
      workspace.state.participants,
    ]);
    const fresh: LocalSession = {
      schema_version: 1,
      id: crypto.randomUUID(),
      scope,
      parent: null,
      revision: workspace.revision,
      fingerprint,
      baseline: clone(workspace.state),
      state: clone(workspace.state),
      active: [],
      redo: [],
      sequence: 0,
      generation: 0,
      updated_at: new Date().toISOString(),
    };
    this.session = fresh;
    if (!identity) {
      this.warning =
        "Local history requires an authenticated workspace. Reload to enable recovery.";
      this.failed = true;
    } else
      await this.write(async () => {
        const sessions = (
          await this.db.sessions.where("scope").equals(scope).toArray()
        ).sort((a, b) => b.updated_at.localeCompare(a.updated_at));
        this.versions = await this.db.versions
          .where("scope")
          .equals(scope)
          .toArray();
        const match = sessions.find(
          (s) =>
            s.schema_version === 1 &&
            s.fingerprint === fingerprint &&
            ((s.revision === workspace.revision &&
              equal(
                this.versions.find((v) => v.id === s.parent)?.state ??
                  s.baseline,
                workspace.state,
              )) ||
              (s.pending &&
                s.pending.revision + 1 === workspace.revision &&
                equal(s.pending.state, workspace.state))),
        );
        this.conflicts = sessions.filter((s) => s !== match);
        if (match) {
          this.session = match;
          this.journal = (
            await this.db.edits.where("session_id").equals(match.id).toArray()
          ).sort((a, b) => a.sequence - b.sequence);
          if (match.revision !== workspace.revision && match.pending)
            await this.finalize(workspace, match.pending);
        } else {
          const version: LocalVersion = {
            schema_version: 1,
            id: crypto.randomUUID(),
            scope,
            parent: null,
            saved_at: new Date().toISOString(),
            fingerprint,
            state: clone(workspace.state),
            context: this.context()!,
            revision: workspace.revision,
            sequence: 0,
          };
          await this.db.transaction(
            "rw",
            this.db.sessions,
            this.db.versions,
            async () => {
              await this.db.versions.add(version);
              fresh.parent = version.id;
              await this.db.sessions.add(clone(fresh));
            },
          );
          this.versions.push(version);
          if (sessions.length)
            this.warning =
              "A different local branch was retained. Inspect it in Local history; it was not restored over the current server draft.";
        }
      });
    this.ready = true;
    this.emit();
    return clone(this.session!.state);
  }
  context(state = this.session?.state): HistoryContext | undefined {
    const s = this.session;
    return s && equal(s.state, state)
      ? {
          schema_version: 1,
          baseline: clone(s.baseline),
          edits: clone(s.active),
        }
      : undefined;
  }
  private persist(entry?: JournalEntry) {
    const s = this.session!;
    if (entry) this.journal.push(clone(entry));
    const expected = s.generation;
    s.generation++;
    s.updated_at = new Date().toISOString();
    const snapshot = clone(s);
    void this.write(async () => {
      await this.db.transaction(
        "rw",
        this.db.sessions,
        this.db.edits,
        async () => {
          const current = await this.db.sessions.get(snapshot.id);
          if (!current || current.generation !== expected)
            throw Error(
              "Another tab changed this local session. Reload before continuing history.",
            );
          if (entry) await this.db.edits.add(entry);
          await this.db.sessions.put(snapshot);
        },
      );
    });
    this.emit();
  }
  commit(next: WorkingState, kind = "EDIT") {
    const s = this.session;
    if (!s || !this.ready) throw Error("Local history is still loading.");
    const changes = changesBetween(s.state, next);
    if (!changes.length) return;
    if (kind === "EDIT") {
      const placements = changes.filter(
        (c) => !equal(c.before.seat_ids, c.after.seat_ids),
      );
      if (!placements.length) kind = "DETAILS";
      else if (placements.length > 2) kind = "REARRANGE";
      else if (placements.length === 2) kind = "SWAP";
      else
        kind = !placements[0].after.seat_ids.length
          ? "DOCK"
          : !placements[0].before.seat_ids.length
            ? "PLACE"
            : "MOVE";
    }
    const edit = {
      operation_id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      kind,
      changes,
    };
    s.active.push(edit);
    s.redo = [];
    s.state = clone(next);
    s.sequence++;
    this.persist({ ...edit, session_id: s.id, sequence: s.sequence });
  }
  undo() {
    return this.travel(false);
  }
  redo() {
    return this.travel(true);
  }
  private travel(forward: boolean) {
    const s = this.session!;
    const edit = forward ? s.redo.pop() : s.active.pop();
    if (!edit) return clone(s.state);
    const before = clone(s.state);
    for (const c of edit.changes)
      s.state.items[c.participant_id] = clone(forward ? c.after : c.before);
    if (forward) s.active.push(edit);
    else s.redo.push(edit);
    s.sequence++;
    this.persist({
      operation_id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      kind: forward ? "REDO" : "UNDO",
      reference: edit.operation_id,
      changes: changesBetween(before, s.state),
      session_id: s.id,
      sequence: s.sequence,
    });
    return clone(s.state);
  }
  async prepareSave(
    state: WorkingState,
    revision: number,
  ): Promise<SaveCapture> {
    const context = this.context(state);
    if (!context)
      throw Error("Draft and local history differ. Reload before saving.");
    const capture = {
      state: clone(state),
      context,
      revision,
      sequence: this.session!.sequence,
    };
    this.session!.pending = capture;
    this.persist();
    await this.serial;
    return capture;
  }
  private async finalize(workspace: Workspace, capture: SaveCapture) {
    const s = this.session!;
    const expected = s.generation;
    const version: LocalVersion = {
      schema_version: 1,
      ...capture,
      id: crypto.randomUUID(),
      scope: s.scope,
      parent: s.parent,
      revision: workspace.revision,
      state: clone(workspace.state),
      saved_at: workspace.saved_at ?? new Date().toISOString(),
      fingerprint: s.fingerprint,
    };
    s.parent = version.id;
    s.revision = workspace.revision;
    delete s.pending;
    s.generation++;
    const snapshot = clone(s);
    await this.db.transaction(
      "rw",
      this.db.sessions,
      this.db.versions,
      async () => {
        const stored = await this.db.sessions.get(s.id);
        if (!stored || stored.generation !== expected)
          throw Error("Another tab changed local history during save.");
        await this.db.versions.add(version);
        await this.db.sessions.put(snapshot);
      },
    );
    this.versions.push(version);
  }
  async saved(workspace: Workspace, capture: SaveCapture) {
    await this.serial;
    if (!this.failed) await this.write(() => this.finalize(workspace, capture));
    else this.session!.revision = workspace.revision;
    this.emit();
  }
  async deleteHistory(workspace: Workspace) {
    await this.serial;
    const scope = this.session!.scope;
    await this.db.transaction(
      "rw",
      this.db.sessions,
      this.db.edits,
      this.db.versions,
      async () => {
        const ids = await this.db.sessions
          .where("scope")
          .equals(scope)
          .primaryKeys();
        for (const id of ids)
          await this.db.edits.where("session_id").equals(id).delete();
        await this.db.sessions.bulkDelete(ids);
        await this.db.versions.where("scope").equals(scope).delete();
      },
    );
    this.versions = [];
    this.conflicts = [];
    return this.open(workspace);
  }
  async flush() {
    await this.serial;
  }
}
