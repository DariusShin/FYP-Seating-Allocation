import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import ts from "typescript";

const require = createRequire(import.meta.url);
function compile(file, load = require) {
  const source = fs.readFileSync(new URL(file, import.meta.url), "utf8");
  const compiled = ts.transpileModule(source, {
    fileName: file,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  }).outputText;
  const mod = { exports: {} };
  new Function("require", "exports", "module", compiled)(load, mod.exports, mod);
  return mod.exports;
}
const schedule = compile("../src/lib/skeleton-schedule.ts");
const { seatGroups } = compile("../src/lib/seat-groups.ts");
const counts = (emperor = 0, merit = 0, bodhi = 0) => ({
  emperor, merit, bodhi,
  accessible: { EMPEROR: 0, MERIT: 0, BODHI: 0 },
});
const seatId = (row, position) => `R${row}-S${position}`;
function floor(rowCount = 3, blocked = []) {
  return {
    row_count: rowCount,
    seats_per_row: 16,
    aisle_after_position: 8,
    total_seats: rowCount * 16,
    approved_pairs: Array.from({ length: 8 }, (_, i) => [i * 2 + 1, i * 2 + 2]),
    rows: Array.from({ length: rowCount }, (_, r) => ({
      row_number: r + 1,
      seats: Array.from({ length: 16 }, (_, p) => ({
        seat_id: seatId(r + 1, p + 1),
        physical_position: p + 1,
        side: p < 8 ? "LEFT" : "RIGHT",
        priority_rank: p < 8 ? 16 - p : p - 7,
        is_blocked: blocked.includes(seatId(r + 1, p + 1)),
        is_accessible: [0, 1, 14, 15].includes(p),
      })),
    })),
  };
}

test("fill completes each row east-first, then west centre-out, before moving back", () => {
  const hall = floor();
  // Backend array order must not determine the animation sequence.
  hall.rows.reverse();
  hall.rows.forEach((row) => row.seats.reverse());
  const steps = schedule.buildSkeletonPlan(hall, counts(10, 12));
  assert.deepEqual(steps.slice(0, 10).map((s) => s.seat_ids), [
    [seatId(1, 9), seatId(1, 10)],
    [seatId(1, 11), seatId(1, 12)],
    [seatId(1, 13), seatId(1, 14)],
    [seatId(1, 15), seatId(1, 16)],
    [seatId(1, 8), seatId(1, 7)],
    [seatId(1, 6), seatId(1, 5)],
    [seatId(1, 4), seatId(1, 3)],
    [seatId(1, 2), seatId(1, 1)],
    [seatId(2, 9), seatId(2, 10)],
    [seatId(2, 11), seatId(2, 12)],
  ]);
  assert.deepEqual(steps.slice(10).map((s) => s.seat_ids[0]),
    [13, 14, 15, 16, 8, 7, 6, 5, 4, 3, 2, 1].map((p) => seatId(2, p)));
});

test("mixed-tier rows continue immediately after the last Emperor pair", () => {
  const steps = schedule.buildSkeletonPlan(floor(), counts(5, 3, 3));
  assert.deepEqual(steps.map((s) => [s.tier, s.seat_ids]), [
    ...[[9, 10], [11, 12], [13, 14], [15, 16], [8, 7]].map((positions) =>
      ["EMPEROR", positions.map((p) => seatId(1, p))]),
    ...[6, 5, 4].map((p) => ["MERIT", [seatId(1, p)]]),
    ...[3, 2, 1].map((p) => ["BODHI", [seatId(1, p)]]),
  ]);
  const used = steps.flatMap((s) => s.seat_ids);
  assert.equal(new Set(used).size, used.length);
  assert.equal(new Set(steps.map((s) => s.owner)).size, steps.length);
});

test("Emperor pairs never cross rows, aisles, structural gaps or unapproved boundaries", () => {
  const hall = floor(2, [seatId(1, 10), seatId(1, 11)]);
  const steps = schedule.buildSkeletonPlan(hall, counts(12), hall.approved_pairs);
  for (const step of steps) {
    assert.equal(step.seat_ids.length, 2);
    const seats = step.seat_ids.map((id) => hall.rows.flatMap((r) =>
      r.seats.map((s) => ({ ...s, row: r.row_number }))).find((s) => s.seat_id === id));
    assert.equal(seats[0].row, seats[1].row);
    assert.equal(seats[0].side, seats[1].side);
    assert.ok(seats.every((s) => !s.is_blocked));
    assert.ok(hall.approved_pairs.some(([a, b]) =>
      a === Math.min(...seats.map((s) => s.physical_position)) &&
      b === Math.max(...seats.map((s) => s.physical_position))));
  }
  assert.deepEqual(steps[0].seat_ids, [seatId(1, 13), seatId(1, 14)]);
  const splitRows = floor(2);
  splitRows.rows[0].seats = splitRows.rows[0].seats.filter((s) => s.physical_position === 9);
  splitRows.rows[1].seats = splitRows.rows[1].seats.filter((s) => s.physical_position === 10);
  assert.deepEqual(schedule.buildSkeletonPlan(splitRows, counts(1)), []);
});

test("accessible registration identities do not cause anonymous preview components to jump rows", () => {
  const registrations = counts(8, 16);
  registrations.accessible = { EMPEROR: 1, MERIT: 2, BODHI: 0 };
  assert.deepEqual(
    schedule.buildSkeletonPlan(floor(), registrations),
    schedule.buildSkeletonPlan(floor(), counts(8, 16)),
  );
});

test("the production registration counts reproduce paired tier bands and skip hall structures", () => {
  const request = JSON.parse(fs.readFileSync(new URL(
    "../../../services/seating/data/production_request.json", import.meta.url), "utf8"));
  const hall = {
    ...request.layout,
    rows: Array.from({ length: request.layout.row_count }, (_, i) => ({
      row_number: i + 1,
      seats: request.layout.seats.filter((s) => s.row_number === i + 1),
    })),
  };
  const registrationCounts = schedule.countsFromRegistrations(request.participants);
  const steps = schedule.buildSkeletonPlan(hall, registrationCounts, hall.approved_pairs);
  assert.equal(steps.length, registrationCounts.emperor + registrationCounts.merit + registrationCounts.bodhi);
  assert.equal(steps.flatMap((s) => s.seat_ids).length,
    registrationCounts.emperor * 2 + registrationCounts.merit + registrationCounts.bodhi);
  const owners = Object.fromEntries(steps.flatMap((s) => s.seat_ids.map((id) => [id, s.owner])));
  const grouped = hall.rows.flatMap((r) => seatGroups(r.seats, owners));
  for (const step of steps) {
    const group = grouped.find((g) => g.owner === step.owner);
    assert.equal(group.seats.length, step.tier === "EMPEROR" ? 2 : 1);
  }
  const occupied = steps.flatMap((s) => s.seat_ids);
  const expected = [...request.layout.seats].filter((s) => !s.is_blocked)
    .sort((a, b) => a.row_number - b.row_number || a.priority_rank - b.priority_rank)
    .slice(0, occupied.length).map((s) => s.seat_id);
  assert.deepEqual(occupied, expected);
  assert.equal(steps[registrationCounts.emperor].tier, "MERIT");
  assert.equal(steps[registrationCounts.emperor + registrationCounts.merit].tier, "BODHI");
});

test("counts exclude unpaid and absent registration units, and an empty snapshot stays empty", () => {
  const participants = [
    { participant_id: "E1", registration_status: "CONFIRMED", contribution_tier: "EMPEROR", requires_accessible_seat: true },
    { participant_id: "E2", registration_status: "CONFIRMED", contribution_tier: "EMPEROR" },
    { participant_id: "M", registration_status: "CONFIRMED", contribution_tier: "MERIT" },
    { participant_id: "B", registration_status: "CONFIRMED", contribution_tier: "BODHI" },
    ...["PENDING", "WAITLISTED", "CANCELLED"].map((registration_status) =>
      ({ participant_id: registration_status, registration_status, contribution_tier: "EMPEROR" })),
  ];
  assert.deepEqual(schedule.countsFromResult({
    source_request: { participants, attendance: { E2: "ABSENT" } },
  }), { ...counts(1, 1, 1), accessible: { EMPEROR: 1, MERIT: 0, BODHI: 0 } });
  assert.deepEqual(schedule.countsFromResult({
    source_request: { participants: [] }, input_summary: { emperor_count: 20 },
  }), counts());
  assert.deepEqual(schedule.countsFromResult({
    input_summary: { emperor_count: 3, merit_count: 4, bodhi_count: 5 },
  }), counts(3, 4, 5));
  assert.deepEqual(schedule.countsFromSetup({
    tier_counts: { emperor_count: 6, merit_count: 7, bodhi_count: 8 },
    accessible_counts: { emperor_count: 1, merit_count: 0, bodhi_count: 2 },
  }), { ...counts(6, 7, 8), accessible: { EMPEROR: 1, MERIT: 0, BODHI: 2 } });
});

test("pacing fills over 60 seconds, clamps negative elapsed time, and always completes", () => {
  assert.equal(schedule.SKELETON_FILL_MS, 60_000);
  assert.equal(schedule.placementAt(-1, 100, 60_000), 0);
  assert.equal(schedule.placementAt(0, 100, 60_000), 0);
  assert.equal(schedule.placementAt(30_000, 100, 60_000), 50);
  assert.equal(schedule.placementAt(59_999, 100, 60_000), 99);
  assert.equal(schedule.placementAt(60_000, 100, 60_000), 100);
  assert.equal(schedule.placementAt(60_000, 0, 60_000), 0);
  assert.ok(schedule.SKELETON_FINISH_MS < schedule.MAP_REVEAL_MS);
});

test("the opening handoff lasts a few seconds and includes time spent fetching the workspace", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let now = 1_800;
  t.mock.method(performance, "now", () => now);
  let revealed = false;
  const pending = schedule.waitForMapReveal(1_000).then(() => { revealed = true; });
  t.mock.timers.tick(schedule.MAP_REVEAL_MS - 801);
  await Promise.resolve();
  assert.equal(revealed, false);
  t.mock.timers.tick(1);
  await pending;
  assert.equal(revealed, true);
  now = 4_000;
  await schedule.waitForMapReveal(1_000); // A slow open needs no extra delay.
});

function animation(t, reducedMotion = false) {
  const slots = [], effects = [], frames = new Map();
  let cursor = 0, now = 0, frame = 0;
  const originals = { window: globalThis.window, requestAnimationFrame: globalThis.requestAnimationFrame,
    cancelAnimationFrame: globalThis.cancelAnimationFrame };
  t.mock.method(performance, "now", () => now);
  globalThis.window = { matchMedia: () => ({ matches: reducedMotion }) };
  globalThis.requestAnimationFrame = (callback) => { frames.set(++frame, callback); return frame; };
  globalThis.cancelAnimationFrame = (id) => frames.delete(id);
  t.after(() => {
    for (const [key, value] of Object.entries(originals)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
  });
  const hooks = {
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) slots[i] = initial;
      return [slots[i], (value) => { slots[i] = value; }];
    },
    useRef(initial) { const i = cursor++; return (slots[i] ??= { current: initial }); },
    useMemo: (fn) => fn(),
    useEffect(fn, deps) {
      const i = cursor++;
      if (!slots[i] || deps.some((d, n) => !Object.is(d, slots[i].deps[n]))) {
        slots[i]?.cleanup?.();
        effects.push(() => { slots[i] = { deps, cleanup: fn() }; });
      }
    },
  };
  const skeleton = compile("../src/components/seat/map-skeleton.tsx", (name) => {
    if (name === "react") return hooks;
    if (name === "@/lib/skeleton-schedule") return schedule;
    if (name === "./hall-map") return {};
    return require(name);
  });
  return {
    ...skeleton,
    render(...args) {
      cursor = 0;
      const value = skeleton.useSkeletonProgress(...args);
      effects.splice(0).forEach((fn) => fn());
      return value;
    },
    advance(time) {
      now = time;
      const callbacks = [...frames.values()];
      frames.clear();
      callbacks.forEach((callback) => callback(time));
    },
  };
}

test("an early solver response accelerates remaining components without snapping to full", (t) => {
  const clock = animation(t);
  assert.equal(clock.render(100, false, 1), 0);
  clock.advance(15_000);
  assert.equal(clock.render(100, false, 1), 25);
  assert.equal(clock.render(100, true, 1), 25);
  clock.advance(15_750);
  assert.equal(clock.render(100, true, 1), 62);
  clock.advance(16_500);
  assert.equal(clock.render(100, true, 1), 100);
  assert.equal(clock.render(100, false, null), 0);
  assert.equal(clock.render(100, false, 2), 0);
  clock.advance(17_100);
  assert.equal(clock.render(100, false, 2), 1);
});

test("reduced motion shows the full paired preview without staged animation", (t) => {
  const clock = animation(t, true);
  clock.render(100, false, 1);
  clock.advance(16);
  assert.equal(clock.render(100, false, 1), 100);
});

test("spotlight is empty before the first registration and covers both seats of a pair", (t) => {
  const clock = animation(t);
  const steps = schedule.buildSkeletonPlan(floor(), counts(1));
  assert.equal(clock.skeletonProjection(steps, 0).spotlight.size, 0);
  const shown = clock.skeletonProjection(steps, 1);
  assert.equal(new Set(Object.values(shown.owners)).size, 1);
  assert.deepEqual([...shown.spotlight], steps[0].seat_ids);
});
