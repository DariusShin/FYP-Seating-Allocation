import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";
const source = fs.readFileSync(
  new URL("../src/lib/seat-editor.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText;
const mod = { exports: {} };
new Function("exports", "module", compiled)(mod.exports, mod);
const {
  initialPlacements,
  placeParticipant,
  removeParticipant,
  draftAssignments,
} = mod.exports;
const result = JSON.parse(
  fs.readFileSync(
    new URL("../src/data/seat_allocation_result.json", import.meta.url),
    "utf8",
  ),
);
const base = initialPlacements(result);
const singles = result.assignments.filter(
  (a) => a.allocation_type === "SINGLE" && !a.requires_accessible_seat,
);
const pairs = result.assignments.filter(
  (a) => a.allocation_type === "EMPEROR_PAIR" && !a.requires_accessible_seat,
);
const empty = result.floor_plan.rows
  .flatMap((r) => r.seats)
  .filter((s) => !s.is_blocked && !s.participant_id);
function success(outcome) {
  assert.equal(outcome.error, undefined);
  return outcome.placements;
}
function unique(placements) {
  const ids = Object.values(placements).flat();
  assert.equal(new Set(ids).size, ids.length);
}

test("moving to an empty seat releases the previous seat without mutating the baseline", () => {
  const next = success(
    placeParticipant(result, base, singles[0].participant_id, empty[0].seat_id),
  );
  assert.deepEqual(next[singles[0].participant_id], [empty[0].seat_id]);
  assert.deepEqual(base[singles[0].participant_id], singles[0].seat_ids);
  unique(next);
});
test("occupied single seats swap atomically", () => {
  const [a, b] = singles;
  const next = success(
    placeParticipant(result, base, a.participant_id, b.seat_ids[0]),
  );
  assert.deepEqual(next[a.participant_id], b.seat_ids);
  assert.deepEqual(next[b.participant_id], a.seat_ids);
  unique(next);
});
test("dragging either seat of an Emperor pair swaps both registrations intact", () => {
  const [a, b] = pairs;
  const next = success(
    placeParticipant(result, base, a.participant_id, b.seat_ids[1]),
  );
  assert.deepEqual(new Set(next[a.participant_id]), new Set(b.seat_ids));
  assert.deepEqual(new Set(next[b.participant_id]), new Set(a.seat_ids));
  unique(next);
});
test("pairs cannot be split by a single-seat assignment", () => {
  assert.match(
    placeParticipant(
      result,
      base,
      singles[0].participant_id,
      pairs[0].seat_ids[0],
    ).error,
    /pairs/,
  );
});
test("blocked seats reject edits", () => {
  const seat = result.floor_plan.rows
    .flatMap((r) => r.seats)
    .find((s) => s.is_blocked);
  assert.match(
    placeParticipant(result, base, singles[0].participant_id, seat.seat_id)
      .error,
    /Blocked/,
  );
});
test("accessibility is checked for the moved participant and the swap recipient", () => {
  const accessible = result.assignments.find(
    (a) => a.requires_accessible_seat && a.allocation_type === "SINGLE",
  );
  assert.ok(accessible);
  const inner = singles.find(
    (a) =>
      !result.floor_plan.rows
        .flatMap((r) => r.seats)
        .find((s) => s.seat_id === a.seat_ids[0]).is_accessible,
  );
  assert.match(
    placeParticipant(result, base, accessible.participant_id, inner.seat_ids[0])
      .error,
    /accessible/,
  );
  assert.match(
    placeParticipant(result, base, inner.participant_id, accessible.seat_ids[0])
      .error,
    /accessible/,
  );
});
test("removing a pair frees both seats and retains its registration and guest names for reassignment", () => {
  const a = pairs[0];
  const removed = removeParticipant(base, a.participant_id);
  assert.deepEqual(removed[a.participant_id], []);
  assert.equal(
    Object.values(base).flat().length - Object.values(removed).flat().length,
    2,
  );
  assert.equal(
    draftAssignments(result, removed).find(
      (p) => p.participant_id === a.participant_id,
    ).seat_ids.length,
    0,
  );
  const next = success(
    placeParticipant(result, removed, a.participant_id, a.seat_ids[1]),
  );
  assert.deepEqual(
    draftAssignments(result, next)
      .find((p) => p.participant_id === a.participant_id)
      .seats.map((s) => s.display_name),
    a.seats.map((s) => s.display_name),
  );
  unique(next);
});
test("replacing with an unassigned participant returns the previous occupant to the list", () => {
  const [a, b] = singles;
  const removed = removeParticipant(base, a.participant_id);
  const next = success(
    placeParticipant(result, removed, a.participant_id, b.seat_ids[0]),
  );
  assert.deepEqual(next[b.participant_id], []);
  assert.deepEqual(next[a.participant_id], b.seat_ids);
  unique(next);
});
test("cancelled previews leave placements and solver output untouched", () => {
  const before = JSON.stringify(result);
  const original = JSON.stringify(base);
  placeParticipant(result, base, singles[0].participant_id, empty[0].seat_id);
  assert.equal(JSON.stringify(base), original);
  assert.equal(JSON.stringify(result), before);
});
test("pairs moved to empty seats never cross the centre aisle", () => {
  const a = pairs[0];
  for (const seat of empty) {
    const outcome = placeParticipant(
      result,
      base,
      a.participant_id,
      seat.seat_id,
    );
    if (outcome.error) continue;
    const ids = outcome.placements[a.participant_id];
    const row = result.floor_plan.rows.find((r) =>
      r.seats.some((s) => s.seat_id === ids[0]),
    );
    const seats = row.seats.filter((s) => ids.includes(s.seat_id));
    assert.equal(seats.length, 2);
    assert.equal(seats[0].side, seats[1].side);
    assert.equal(
      Math.abs(seats[0].physical_position - seats[1].physical_position),
      1,
    );
  }
});
