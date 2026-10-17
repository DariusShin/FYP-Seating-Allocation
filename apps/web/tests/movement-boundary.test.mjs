import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import ts from "typescript";
const require = createRequire(import.meta.url);
function compile(file, load = require) {
  const compiled = ts.transpileModule(
    fs.readFileSync(new URL(file, import.meta.url), "utf8"),
    {
      fileName: file,
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
        esModuleInterop: true,
      },
    },
  ).outputText;
  const mod = { exports: {} };
  new Function("require", "exports", "module", compiled)(
    load,
    mod.exports,
    mod,
  );
  return mod.exports;
}
const boundary = compile("../src/lib/movement-boundary.ts");
const { move, reviewMove, markAbsent, restore } = compile(
  "../src/lib/workspace.ts",
  (name) => (name === "./movement-boundary" ? boundary : require(name)),
);
const { movementBoundary } = boundary;

const APPROVED_PAIRS = [
  [1, 2],
  [3, 4],
  [5, 6],
  [7, 8],
  [9, 10],
  [11, 12],
  [13, 14],
  [15, 16],
];
function floorPlan(rows = 2, blocked = []) {
  return {
    row_count: rows,
    seats_per_row: 16,
    aisle_after_position: 8,
    rows: Array.from({ length: rows }, (_, r) => ({
      row_number: r + 1,
      seats: Array.from({ length: 16 }, (_, i) => {
        const position = i + 1;
        return {
          seat_id: `R${String(r + 1).padStart(2, "0")}-S${String(position).padStart(2, "0")}`,
          physical_position: position,
          priority_rank:
            position > 8 ? position - 8 : 16 - position + 1,
          side: position <= 8 ? "LEFT" : "RIGHT",
          is_blocked: blocked.includes(`${r + 1}-${position}`),
          is_accessible: [1, 2, 15, 16].includes(position),
        };
      }),
    })),
  };
}
const reg = (id, tier) => ({
  participant_id: id,
  contribution_tier: tier,
  registration_status: "CONFIRMED",
  requires_accessible_seat: false,
});
const people = (count, tier) =>
  Array.from({ length: count }, (_, i) =>
    reg(`${tier.toLowerCase()}${i + 1}`, tier),
  );
function state(placements, participants) {
  return {
    participants,
    items: Object.fromEntries(
      Object.entries(placements).map(([id, seat_ids]) => [
        id,
        {
          seat_ids,
          display_names: [id],
          note: "",
          dock_reason: "",
          previous_seat_ids: [],
        },
      ]),
    ),
  };
}
const reviewBase = (floor) => ({
  floor_plan: floor,
  source_request: { layout: { approved_pairs: APPROVED_PAIRS } },
});

test("emperor band covers ROUNDING UP (pairs * 2 / 16) rows", () => {
  const floor = floorPlan(3);
  const limit = movementBoundary(floor, people(8, "EMPEROR")).limit("EMPEROR");
  assert.equal(limit.rows, 1);
  assert.equal(limit.seat_id, "R01-S01");
  assert.equal(limit.order, 16);
  const nine = movementBoundary(floor, people(9, "EMPEROR")).limit("EMPEROR");
  assert.equal(nine.rows, 2);
  assert.equal(nine.row_number, 2);
  assert.equal(nine.priority_rank, 2);
  assert.equal(nine.seat_id, "R02-S10");
  assert.equal(nine.order, 18);
});

test("merit and bodhi bands extend the cumulative tier boundary", () => {
  const floor = floorPlan(3);
  const participants = [...people(1, "EMPEROR"), ...people(10, "MERIT")];
  const limits = movementBoundary(floor, participants);
  assert.equal(limits.limit("EMPEROR").start_order, 1);
  assert.equal(limits.limit("EMPEROR").seat_id, "R01-S10");
  assert.equal(limits.limit("MERIT").rows, 1);
  assert.equal(limits.limit("MERIT").start_seat_id, "R01-S11");
  assert.equal(limits.limit("MERIT").start_order, 3);
  assert.equal(limits.limit("MERIT").seat_id, "R01-S05");
  assert.equal(limits.limit("BODHI").seat_id, "R01-S05");
  assert.equal(limits.limit("BODHI").start_seat_id, "R01-S04");
  assert.equal(limits.limit("BODHI").start_order, 13);
  const withBodhi = [
    ...people(1, "EMPEROR"),
    ...people(2, "MERIT"),
    ...people(14, "BODHI"),
  ];
  const bodhi = movementBoundary(floor, withBodhi).limit("BODHI");
  assert.equal(bodhi.start_seat_id, "R01-S13");
  assert.equal(bodhi.seat_id, "R02-S10");
});

test("boundaries are skipped when the floor plan lacks rank geometry", () => {
  const floor = {
    rows: [
      {
        row_number: 1,
        seats: [{ seat_id: "s1", physical_position: 1, is_blocked: false }],
      },
    ],
  };
  assert.equal(movementBoundary(floor, people(1, "EMPEROR")), null);
});

test("a docked emperor pair cannot be dropped behind its band", () => {
  const base = reviewBase(floorPlan(2));
  const s = state({ emperor1: [] }, people(1, "EMPEROR"));
  const kept = move(s, base, "emperor1", "R01-S09");
  assert.deepEqual(kept.items.emperor1.seat_ids, ["R01-S09", "R01-S10"]);
  assert.throws(
    () => move(s, base, "emperor1", "R01-S11"),
    /EMPEROR seating cannot be placed behind R01-S10 \(row 1\)/,
  );
  assert.throws(
    () => move(s, base, "emperor1", "R02-S09"),
    /EMPEROR seating cannot be placed behind R01-S10/,
  );
});

test("the band caps the physical position within the boundary row", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [...people(1, "EMPEROR"), ...people(2, "MERIT")];
  const s = state(
    { emperor1: [], merit1: [], merit2: [] },
    participants,
  );
  const placed = move(s, base, "merit1", "R01-S12");
  assert.deepEqual(placed.items.merit1.seat_ids, ["R01-S12"]);
  assert.throws(
    () => move(s, base, "merit1", "R01-S13"),
    /MERIT seating cannot be placed behind R01-S12 \(row 1\)/,
  );
});

test("a merit cannot swap into emperor seats and push the emperor behind its band", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [...people(1, "EMPEROR"), ...people(1, "MERIT")];
  const s = state(
    { emperor1: ["R01-S09", "R01-S10"], merit1: ["R01-S11"] },
    participants,
  );
  assert.throws(
    () => reviewMove(s, base, "merit1", "R01-S09"),
    /MERIT seating cannot be placed in front of R01-S11 \(row 1\)/,
  );
});

test("merit and bodhi cannot move into the bands of higher tiers", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [
    ...people(1, "EMPEROR"),
    ...people(2, "MERIT"),
    ...people(2, "BODHI"),
  ];
  const s = state(
    {
      emperor1: ["R01-S09", "R01-S10"],
      merit1: ["R01-S11"],
      merit2: ["R01-S12"],
      bodhi1: ["R01-S13"],
      bodhi2: ["R01-S14"],
    },
    participants,
  );
  assert.throws(
    () => move(s, base, "bodhi1", "R01-S11"),
    /BODHI seating cannot be placed in front of R01-S13 \(row 1\)/,
  );
  assert.throws(
    () => move(s, base, "bodhi1", "R01-S12"),
    /BODHI seating cannot be placed in front of R01-S13 \(row 1\)/,
  );
  assert.throws(
    () => move(s, base, "merit1", "R01-S09"),
    /MERIT seating cannot be placed in front of R01-S11 \(row 1\)/,
  );
  const swapped = move(s, base, "bodhi1", "R01-S14");
  assert.deepEqual(swapped.items.bodhi1.seat_ids, ["R01-S14"]);
  assert.deepEqual(swapped.items.bodhi2.seat_ids, ["R01-S13"]);
  const forward = move(s, base, "merit1", "R01-S12");
  assert.deepEqual(forward.items.merit1.seat_ids, ["R01-S12"]);
  assert.deepEqual(forward.items.merit2.seat_ids, ["R01-S11"]);
});

test("swaps and chains stay possible inside every tier band", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [
    ...people(2, "EMPEROR"),
    ...people(2, "MERIT"),
    ...people(2, "BODHI"),
  ];
  const s = state(
    {
      emperor1: ["R01-S09", "R01-S10"],
      emperor2: ["R01-S11", "R01-S12"],
      merit1: ["R01-S13"],
      merit2: ["R01-S14"],
      bodhi1: ["R01-S15"],
      bodhi2: ["R01-S16"],
    },
    participants,
  );
  const swapped = reviewMove(s, base, "emperor1", "R01-S11");
  assert.deepEqual(swapped.state.items.emperor1.seat_ids, ["R01-S11", "R01-S12"]);
  assert.deepEqual(swapped.state.items.emperor2.seat_ids, ["R01-S09", "R01-S10"]);
  const forward = move(swapped.state, base, "merit1", "R01-S14");
  assert.deepEqual(forward.items.merit1.seat_ids, ["R01-S14"]);
  assert.deepEqual(forward.items.merit2.seat_ids, ["R01-S13"]);
});

test("pre-existing band violations do not lock repositioning", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [...people(1, "EMPEROR"), ...people(1, "MERIT")];
  const s = state(
    { emperor1: ["R01-S13", "R01-S14"], merit1: ["R01-S09"] },
    participants,
  );
  const moved = move(s, base, "emperor1", "R01-S15");
  assert.deepEqual(moved.items.emperor1.seat_ids, ["R01-S15", "R01-S16"]);
});

test("absent registrations do not consume tier band space", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [...people(1, "EMPEROR"), ...people(1, "MERIT")];
  const s = state({ emperor1: [], merit1: [] }, participants);
  const absent = markAbsent(s, "emperor1");
  const kept = move(absent, base, "merit1", "R01-S09");
  assert.deepEqual(kept.items.merit1.seat_ids, ["R01-S09"]);
  assert.throws(
    () => move(absent, base, "merit1", "R01-S10"),
    /MERIT seating cannot be placed behind R01-S09 \(row 1\)/,
  );
});

test("restore returns an absent registration to the dock as a normal candidate", () => {
  const base = reviewBase(floorPlan(2));
  const participants = [...people(1, "EMPEROR"), ...people(1, "MERIT")];
  const s = state(
    { emperor1: ["R01-S09", "R01-S10"], merit1: ["R01-S11"] },
    participants,
  );
  const absent = markAbsent(s, "emperor1");
  assert.equal(absent.items.emperor1.attendance_status, "ABSENT");
  const back = restore(absent, "emperor1");
  assert.equal(back.items.emperor1.attendance_status, "PRESENT");
  assert.deepEqual(back.items.emperor1.seat_ids, []);
  assert.equal(back.items.emperor1.dock_reason, "");
  assert.deepEqual(
    back.items.emperor1.previous_seat_ids,
    ["R01-S09", "R01-S10"],
  );
  assert.equal(restore(back, "emperor1"), back);
  const placed = move(back, base, "emperor1", "R01-S09");
  assert.deepEqual(placed.items.emperor1.seat_ids, ["R01-S09", "R01-S10"]);
});
