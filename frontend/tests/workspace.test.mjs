import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";
const mod = { exports: {} };
new Function(
  "exports",
  "module",
  ts.transpileModule(
    fs.readFileSync(
      new URL("../src/lib/workspace.ts", import.meta.url),
      "utf8",
    ),
    { compilerOptions: { module: ts.ModuleKind.CommonJS } },
  ).outputText,
)(mod.exports, mod);
const { move, dock } = mod.exports;
const cells = Array.from({ length: 16 }, (_, i) => ({
  seat_id: `s${i + 1}`,
  physical_position: i + 1,
  side: i < 8 ? "LEFT" : "RIGHT",
  is_blocked: false,
  is_accessible: [0, 1, 14, 15].includes(i),
}));
const base = { floor_plan: { rows: [{ row_number: 1, seats: cells }] } };
function state() {
  return {
    participants: [
      {
        participant_id: "pair",
        contribution_tier: "EMPEROR",
        registration_status: "CONFIRMED",
        requires_accessible_seat: false,
      },
      {
        participant_id: "single",
        contribution_tier: "MERIT",
        registration_status: "CONFIRMED",
        requires_accessible_seat: false,
      },
    ],
    items: {
      pair: {
        seat_ids: ["s7", "s8"],
        display_names: ["陳思恩", "林慧婷"],
        note: "pair note",
      },
      single: { seat_ids: ["s6"], display_names: ["黃志華"] },
    },
  };
}
test("dock round trip retains names, notes and provenance", () => {
  const s = state();
  const held = dock(s, "pair");
  assert.deepEqual(held.items.pair.previous_seat_ids, ["s7", "s8"]);
  assert.deepEqual(held.items.pair.seat_ids, []);
  const next = move(held, base, "pair", "s9");
  assert.deepEqual(next.items.pair.seat_ids, ["s9", "s10"]);
  assert.deepEqual(next.items.pair.display_names, s.items.pair.display_names);
  assert.equal(next.items.pair.note, "pair note");
  assert.deepEqual(s.items.pair.seat_ids, ["s7", "s8"]);
});
test("pair cannot overwrite a single and stays on one side of aisle", () => {
  const s = state();
  assert.throws(() => move(s, base, "single", "s7"), /Swap/);
  const next = move(s, base, "pair", "s9");
  assert.deepEqual(next.items.pair.seat_ids, ["s9", "s10"]);
});
test("paid Emperor allocation always moves as a complete pair", () => {
  const s = state();
  const held = dock(s, "pair");
  const next = move(held, base, "pair", "s9");
  assert.equal(next.items.pair.seat_ids.length, 2);
  assert.equal(next.participants.length, s.participants.length);
});

const { reviewMove } = mod.exports;
const reviewBase = {
  ...base,
  source_request: {
    layout: {
      approved_pairs: [
        [1, 2],
        [3, 4],
        [5, 6],
        [7, 8],
        [9, 10],
        [11, 12],
        [13, 14],
        [15, 16],
      ],
    },
  },
};
test("review chain moves a pair into a single and places the single in vacated seats", () => {
  const s = state();
  const result = reviewMove(s, reviewBase, "pair", "s6");
  assert.equal(result.chain, true);
  assert.deepEqual(result.state.items.pair.seat_ids, ["s5", "s6"]);
  assert.ok(["s7", "s8"].includes(result.state.items.single.seat_ids[0]));
  assert.equal(
    new Set(Object.values(result.state.items).flatMap((i) => i.seat_ids)).size,
    3,
  );
  assert.deepEqual(s.items.pair.seat_ids, ["s7", "s8"]);
});
test("review single-to-pair chain uses a free neighbour at the source", () => {
  const result = reviewMove(state(), reviewBase, "single", "s7");
  assert.deepEqual(result.state.items.pair.seat_ids, ["s5", "s6"]);
  assert.deepEqual(result.state.items.single.seat_ids, ["s7"]);
});
test("review offers the dock escape when displaced pair cannot fit", () => {
  const s = state();
  s.items.third = { seat_ids: ["s5"], display_names: ["Other"] };
  s.participants.push({
    participant_id: "third",
    contribution_tier: "MERIT",
    registration_status: "CONFIRMED",
  });
  assert.throws(
    () => reviewMove(s, reviewBase, "single", "s7"),
    /holding dock/,
  );
});
test("review targets use the actual approved pairs and accessibility of both registrations", () => {
  const s = state();
  const unusual = {
    ...reviewBase,
    source_request: { layout: { approved_pairs: [[2, 3]] } },
  };
  assert.deepEqual(
    reviewMove(s, unusual, "pair", "s2").state.items.pair.seat_ids,
    ["s2", "s3"],
  );
  assert.throws(() => reviewMove(s, unusual, "pair", "s7"), /cannot fit/);
  s.participants[0].requires_accessible_seat = true;
  assert.throws(
    () => reviewMove(s, reviewBase, "single", "s7"),
    /holding dock/,
  );
});
test("dropping a registration on its current seats is a no-op", () => {
  const s = state();
  assert.equal(move(s, base, "pair", "s8"), s);
  assert.equal(move(s, base, "single", "s6"), s);
});
test("pair-to-two-Merit exchange moves all three registrations in one preview", () => {
  const s = state();
  s.items.single.seat_ids = ["s3"];
  s.items.second = { seat_ids: ["s4"], display_names: ["Second"] };
  s.participants.push({
    participant_id: "second",
    contribution_tier: "MERIT",
    registration_status: "CONFIRMED",
    requires_accessible_seat: false,
  });
  const result = reviewMove(s, reviewBase, "pair", "s3");
  assert.equal(result.chain, true);
  assert.deepEqual(result.state.items.pair.seat_ids, ["s3", "s4"]);
  assert.deepEqual(result.state.items.single.seat_ids, ["s7"]);
  assert.deepEqual(result.state.items.second.seat_ids, ["s8"]);
  assert.equal(
    new Set(Object.values(result.state.items).flatMap((i) => i.seat_ids)).size,
    4,
  );
  assert.equal(reviewMove(s, reviewBase, "pair", "s8").state, s);
});
