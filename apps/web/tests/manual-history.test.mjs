import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import "fake-indexeddb/auto";
import ts from "typescript";
const require = createRequire(import.meta.url);
function compile(file) {
  const mod = { exports: {} };
  const code = ts.transpileModule(
    fs.readFileSync(new URL(file, import.meta.url), "utf8"),
    {
      compilerOptions: {
        target: ts.ScriptTarget.ES2022,
        module: ts.ModuleKind.CommonJS,
        esModuleInterop: true,
      },
    },
  ).outputText;
  new Function("require", "module", "exports", code)(require, mod, mod.exports);
  return mod.exports;
}
const { ManualHistory, HistoryDatabase, restoration, changesBetween, equal } =
  compile("../src/lib/manual-history.ts");
const { restorationResolves, focusedGroups } = compile(
  "../src/lib/verification.ts",
);
function fixture() {
  const item = (n) => ({
    seat_ids: [`s${n}`],
    display_names: [`Person ${n}`],
    note: "",
    dock_reason: "",
    previous_seat_ids: [],
    changed_at: null,
  });
  return {
    history_scope: { actor: "a", event_id: "event" },
    base: { plan_version_id: "plan", floor_plan: { rows: [] } },
    state: {
      participants: [{ participant_id: "A" }, { participant_id: "B" }],
      items: { A: item(1), B: item(2) },
    },
    revision: 0,
    saved_at: null,
  };
}
function swap(s) {
  const n = structuredClone(s);
  [n.items.A.seat_ids, n.items.B.seat_ids] = [
    n.items.B.seat_ids,
    n.items.A.seat_ids,
  ];
  return n;
}
async function setup(t) {
  const db = new HistoryDatabase(`test-${crypto.randomUUID()}`);
  t.after(() => db.delete());
  const h = new ManualHistory(db);
  const w = fixture();
  await h.open(w);
  return { h, w, db };
}
test("refresh recovers atomic swaps, ordered rapid edits, undo/redo and abandoned branches", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  const first = h.context().edits[0].operation_id;
  h.commit(swap(h.session.state));
  h.undo();
  h.redo();
  h.undo();
  h.commit(
    {
      ...h.session.state,
      items: {
        ...h.session.state.items,
        A: { ...h.session.state.items.A, note: "new branch" },
      },
    },
    "DETAILS",
  );
  await h.flush();
  const recovered = new ManualHistory(db);
  assert.deepEqual(await recovered.open(w), h.session.state);
  assert.equal(recovered.session.redo.length, 0);
  assert.equal(recovered.context().edits[0].operation_id, first);
  assert.equal(recovered.context().edits.length, 2);
  const log = await db.edits.toArray();
  assert.equal(log.length, 6);
  assert.deepEqual(
    log.map((e) => e.sequence),
    [1, 2, 3, 4, 5, 6],
  );
  assert.equal(log[0].changes.length, 2);
  assert.equal(log[2].kind, "UNDO");
});
test("no-ops produce no journal entry", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(structuredClone(w.state));
  await h.flush();
  assert.equal(await db.edits.count(), 0);
});
test("saved versions are immutable and edits during save remain recoverable", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  const capture = await h.prepareSave(h.session.state, 0);
  const newer = structuredClone(h.session.state);
  newer.items.A.note = "edited during save";
  h.commit(newer);
  const saved = { ...w, state: capture.state, revision: 1 };
  await h.saved(saved, capture);
  assert.equal(h.versions.length, 2);
  assert.equal(h.versions[0].state.items.A.seat_ids[0], "s1");
  assert.equal(h.versions[1].state.items.A.note, "");
  const r = new ManualHistory(db);
  assert.deepEqual(await r.open(saved), newer);
  assert.equal(r.context().edits.length, 2);
});
test("server success with local finalization failure reconciles without replaying edits", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  const capture = await h.prepareSave(h.session.state, 0);
  const saved = { ...w, state: capture.state, revision: 1 };
  const add = db.versions.add.bind(db.versions);
  db.versions.add = async () => {
    throw Error("disk full");
  };
  await h.saved(saved, capture);
  assert.match(h.warning, /disk full/);
  db.versions.add = add;
  const r = new ManualHistory(db);
  assert.deepEqual(await r.open(saved), saved.state);
  assert.equal(r.versions.length, 2);
  assert.equal(r.context().edits.length, 1);
});
test("failed save can retry without duplicating the edit", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  await h.prepareSave(h.session.state, 0);
  const r = new ManualHistory(db);
  await r.open(w);
  const capture = await r.prepareSave(r.session.state, 0);
  await r.saved({ ...w, state: capture.state, revision: 1 }, capture);
  assert.equal(await db.edits.count(), 1);
  assert.equal(r.versions.length, 2);
});
test("scope, changed layout and stale server revision retain branches without auto restoring", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  await h.flush();
  for (const replacement of [
    { ...w, revision: 2 },
    {
      ...w,
      base: { ...w.base, floor_plan: { rows: [{ row_number: 1, seats: [] }] } },
    },
  ]) {
    const r = new ManualHistory(db);
    assert.deepEqual(await r.open(replacement), w.state);
    assert.ok(r.conflicts.length);
  }
  for (const replacement of [
    { ...w, history_scope: { actor: "b", event_id: "event" } },
    { ...w, history_scope: { actor: "a", event_id: "other" } },
    { ...w, base: { ...w.base, plan_version_id: "other" } },
  ]) {
    const r = new ManualHistory(db);
    assert.deepEqual(await r.open(replacement), w.state);
    assert.equal(r.conflicts.length, 0);
  }
});
test("two-tab compare-and-swap prevents overwriting another local session", async (t) => {
  const { h, w, db } = await setup(t);
  const other = new ManualHistory(db);
  await other.open(w);
  h.commit(swap(w.state));
  await h.flush();
  const next = structuredClone(w.state);
  next.items.A.note = "stale";
  other.commit(next);
  await other.flush();
  assert.match(other.warning, /Another tab/);
  assert.equal(other.session.state.items.A.note, "stale");
  assert.deepEqual(
    (await db.sessions.get(h.session.id)).state,
    h.session.state,
  );
});
test("storage failure keeps memory usable and makes recovery failure explicit", async (t) => {
  const { h, w, db } = await setup(t);
  db.edits.add = async () => {
    throw Error("quota");
  };
  h.commit(swap(w.state));
  await h.flush();
  assert.match(h.warning, /quota/);
  assert.equal(h.undo().items.A.seat_ids[0], "s1");
});
test("deletion removes retained journal and starts a clean baseline", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  await h.flush();
  await h.deleteHistory(w);
  assert.equal(await db.edits.count(), 0);
  assert.equal(await db.sessions.count(), 1);
  assert.equal(h.session.active.length, 0);
});
test("restoration preserves current details and rejects moved registrations or occupied destinations", () => {
  const w = fixture();
  const next = swap(w.state);
  const changes = changesBetween(w.state, next);
  next.items.A.note = "keep me";
  assert.equal(restoration(next, changes).items.A.note, "keep me");
  assert.equal(restoration(next, changes).items.A.seat_ids[0], "s1");
  const moved = structuredClone(next);
  moved.items.A.seat_ids = ["s3"];
  assert.throws(() => restoration(moved, changes), /moved again/);
  const occupied = structuredClone(next);
  occupied.items.C = { seat_ids: ["s1"] };
  assert.throws(() => restoration(occupied, changes), /unavailable/);
});
test("grouping retains all findings and restoration rejects new advisory findings", () => {
  const f = (id) => ({
    finding_id: id,
    resolution_hint: { actor_participant_id: "A" },
  });
  const findings = [f("x"), f("y"), f("baseline")];
  const groups = focusedGroups(findings, {
    groups: [{ operation_id: "swap", finding_ids: ["x", "y"] }],
  });
  assert.deepEqual(
    groups.map(([id, items]) => [id, items.length]),
    [
      ["edit:swap", 2],
      ["A", 1],
    ],
  );
  assert.equal(
    restorationResolves(findings, [f("baseline")], ["x", "y"]),
    true,
  );
  assert.equal(
    restorationResolves(findings, [f("new-advisory")], ["x", "y"]),
    false,
  );
  assert.equal(restorationResolves(findings, [f("x")], ["x", "y"]), false);
  assert.equal(equal({ a: 1, b: 2 }, { b: 2, a: 1 }), true);
});
test("changed registration inputs retain the old branch even when server revision matches", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  await h.flush();
  const changed = structuredClone(w);
  changed.state.participants.push({ participant_id: "C" });
  changed.state.items.C = {
    ...changed.state.items.A,
    seat_ids: ["s3"],
    display_names: ["New registration"],
  };
  const r = new ManualHistory(db);
  assert.deepEqual(await r.open(changed), changed.state);
  assert.equal(r.session.active.length, 0);
  assert.equal(r.conflicts.length, 1);
  assert.deepEqual(r.conflicts[0].state, h.session.state);
  assert.notEqual(r.conflicts[0].fingerprint, r.session.fingerprint);
});
test("restoring a saved version is a new undoable edit with a child saved snapshot", async (t) => {
  const { h, w, db } = await setup(t);
  h.commit(swap(w.state));
  const capture = await h.prepareSave(h.session.state, 0);
  const saved = { ...w, state: capture.state, revision: 1 };
  await h.saved(saved, capture);
  const original = structuredClone(h.versions[0]);
  h.commit(original.state, "RESTORE_VERSION");
  assert.equal(h.session.active.at(-1).kind, "RESTORE_VERSION");
  assert.deepEqual(h.undo(), saved.state);
  assert.deepEqual(h.redo(), w.state);
  const restored = await h.prepareSave(h.session.state, 1);
  await h.saved({ ...w, revision: 2 }, restored);
  assert.equal(h.versions[2].parent, h.versions[1].id);
  assert.deepEqual(await db.versions.get(original.id), original);
  const r = new ManualHistory(db);
  assert.deepEqual(await r.open({ ...w, revision: 2 }), w.state);
  assert.equal(r.session.active.length, 2);
});

const { restorationFromHistory } = compile("../src/lib/manual-history.ts");
function dockSequence() {
  const item = (name, seats) => ({
    seat_ids: seats,
    display_names: seats.map(() => name),
    note: "",
    dock_reason: "",
    previous_seat_ids: [],
    changed_at: null,
  });
  const baseline = {
    participants: ["emperor", "merit1", "merit2", "unrelated"].map(
      (participant_id) => ({ participant_id }),
    ),
    items: {
      emperor: item("王德宇", ["R09-S13", "R09-S14"]),
      merit1: item("陳秀傑", ["R12-S09"]),
      merit2: item("何文華", ["R12-S10"]),
      unrelated: item("Unrelated", ["R10-S01"]),
    },
  };
  const context = {
    schema_version: 1,
    baseline: structuredClone(baseline),
    edits: [],
  };
  let state = structuredClone(baseline);
  function place(id, seats, operation_id) {
    const next = structuredClone(state);
    next.items[id].seat_ids = seats;
    context.edits.push({
      operation_id,
      kind: "EDIT",
      changes: changesBetween(state, next),
    });
    state = next;
  }
  place("merit1", [], "dock-first");
  place("merit2", [], "dock-second");
  place("emperor", ["R12-S09", "R12-S10"], "move-emperor");
  place("merit1", ["R09-S13"], "place-first");
  place("merit2", ["R09-S14"], "place-second");
  const details = structuredClone(state);
  details.items.emperor.note = "Keep this later note";
  details.items.merit1.display_names = ["Updated name"];
  context.edits.push({
    operation_id: "details",
    changes: changesBetween(state, details),
  });
  state = details;
  place("unrelated", ["R10-S02"], "unrelated-move");
  return { baseline, state, context };
}
test("either dock-to-seat card restores the full Emperor/two-Merit exchange, including existing history", () => {
  const { baseline, state, context } = dockSequence();
  // The old single-entry restore tries to put one Merit back into an empty dock.
  assert.throws(
    () => restoration(state, context.edits[3].changes),
    /earlier seated position/,
  );
  for (const selected of ["place-first", "place-second", "move-emperor"]) {
    const plan = restorationFromHistory(state, context, selected);
    assert.equal(plan.changes.length, 3);
    assert.deepEqual(
      new Set(plan.operation_ids),
      new Set([
        "dock-first",
        "dock-second",
        "move-emperor",
        "place-first",
        "place-second",
      ]),
    );
    for (const id of ["emperor", "merit1", "merit2"])
      assert.deepEqual(
        plan.state.items[id].seat_ids,
        baseline.items[id].seat_ids,
      );
    assert.deepEqual(plan.state.items.unrelated, state.items.unrelated);
    assert.equal(plan.state.items.emperor.note, "Keep this later note");
    assert.deepEqual(plan.state.items.merit1.display_names, ["Updated name"]);
    assert.equal(
      new Set(Object.values(plan.state.items).flatMap((i) => i.seat_ids)).size,
      5,
    );
  }
  assert.deepEqual(state.items.emperor.seat_ids, ["R12-S09", "R12-S10"]);
});
test("connected restoration includes later swaps without undoing unrelated placements", () => {
  const { state, context } = dockSequence();
  const next = structuredClone(state);
  [next.items.merit1.seat_ids, next.items.unrelated.seat_ids] = [
    next.items.unrelated.seat_ids,
    next.items.merit1.seat_ids,
  ];
  context.edits.push({
    operation_id: "later-swap",
    changes: changesBetween(state, next),
  });
  const plan = restorationFromHistory(next, context, "place-first");
  assert.equal(plan.changes.length, 4);
  assert.ok(plan.operation_ids.includes("later-swap"));
  assert.deepEqual(
    plan.state.items.unrelated.seat_ids,
    context.baseline.items.unrelated.seat_ids,
  );
  // Selecting just the latest swap uses the nearest complete preceding position.
  const latest = restorationFromHistory(next, context, "later-swap");
  assert.deepEqual(latest.state.items.emperor, state.items.emperor);
  assert.deepEqual(latest.state.items.unrelated.seat_ids, ["R10-S02"]);
  assert.equal(latest.operation_ids.length, 1);
});
test("missing original positions and stale history cannot produce a partial restoration", () => {
  const { state, context } = dockSequence();
  const incomplete = structuredClone(context);
  incomplete.baseline.items.merit1.seat_ids = [];
  incomplete.edits.shift();
  assert.throws(
    () => restorationFromHistory(state, incomplete, "place-first"),
    /earlier seated position is not recorded/,
  );
  const stale = structuredClone(state);
  stale.items.emperor.note = "intervening edit";
  assert.throws(
    () => restorationFromHistory(stale, context, "place-first"),
    /draft changed/,
  );
  assert.throws(
    () => restorationFromHistory(state, context, "undone-edit"),
    /no longer active/,
  );
  assert.deepEqual(state.items.merit1.seat_ids, ["R09-S13"]);
});
test("a connected restoration remains one undoable event after refresh", async (t) => {
  const { h, w, db } = await setup(t);
  const { baseline, state, context } = dockSequence();
  const workspace = { ...w, state: baseline };
  await h.open(workspace);
  for (const edit of context.edits) {
    const next = structuredClone(h.session.state);
    for (const c of edit.changes) next.items[c.participant_id] = c.after;
    h.commit(next);
  }
  const selected = h.context().edits[3].operation_id;
  const plan = restorationFromHistory(h.session.state, h.context(), selected);
  h.commit(plan.state, "RESTORE_POSITIONS");
  await h.flush();
  const recovered = new ManualHistory(db);
  await recovered.open(workspace);
  assert.deepEqual(recovered.session.state, plan.state);
  assert.deepEqual(recovered.undo(), state);
});
test("Emperor moved to empty seats is included when Merit fills its vacated pair", () => {
  const { baseline } = dockSequence();
  baseline.items.merit1.seat_ids = ["R10-S09"];
  baseline.items.merit2.seat_ids = ["R10-S10"];
  const context = {
    schema_version: 1,
    baseline: structuredClone(baseline),
    edits: [],
  };
  let state = structuredClone(baseline);
  const place = (pid, seats, id) => {
    const next = structuredClone(state);
    next.items[pid].seat_ids = seats;
    context.edits.push({
      operation_id: id,
      changes: changesBetween(state, next),
    });
    state = next;
  };
  place("emperor", ["R12-S09", "R12-S10"], "move-emperor");
  place("merit1", [], "dock-first");
  place("merit2", [], "dock-second");
  place("merit1", ["R09-S13"], "place-first");
  place("merit2", ["R09-S14"], "place-second");
  for (const selected of ["place-first", "place-second"]) {
    const plan = restorationFromHistory(state, context, selected, [
      "emperor",
      "merit1",
      "merit2",
    ]);
    assert.equal(plan.changes.length, 3);
    for (const pid of ["emperor", "merit1", "merit2"])
      assert.deepEqual(
        plan.state.items[pid].seat_ids,
        baseline.items[pid].seat_ids,
      );
    assert.equal(
      new Set(Object.values(plan.state.items).flatMap((i) => i.seat_ids)).size,
      5,
    );
  }
});
