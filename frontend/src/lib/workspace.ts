import type { AllocationResult, Registration } from "./allocation-types";
export interface WorkingItem {
  attendance_status?: "PRESENT" | "ABSENT";
  seat_ids: string[];
  display_names: string[];
  note: string;
  dock_reason: string;
  previous_seat_ids: string[];
  changed_at: string | null;
}
export interface WorkingState {
  participants: Registration[];
  items: Record<string, WorkingItem>;
}
export interface Workspace {
  history_scope?: { actor: string; event_id: string };
  review?: import("./verification").Review;
  base: AllocationResult & {
    published_at?: string;
  };
  state: WorkingState;
  revision: number;
  saved_at: string | null;
  actor: string | null;
  has_newer_plan?: boolean;
}
export const eligible = (p: Registration) =>
  p.registration_status === "CONFIRMED";
export function move(
  state: WorkingState,
  base: AllocationResult,
  pid: string,
  sid: string,
): WorkingState {
  const p = state.participants.find((p) => p.participant_id === pid);
  const m = state.items[pid];
  if (!p || !eligible(p))
    throw Error("Only paid registrations can occupy a seat.");
  if (m.attendance_status === "ABSENT")
    throw Error("Restore attendance before assigning this registration.");
  const cells = base.floor_plan.rows.flatMap((r) =>
    r.seats.map((s) => ({ ...s, row: r.row_number })),
  );
  const target = cells.find((s) => s.seat_id === sid);
  if (!target || target.is_blocked)
    throw Error("This structural position cannot be assigned.");
  function destination(person: Registration, cell: typeof target): string[] {
    if (!cell) throw Error("Choose a destination.");
    const pair = person.contribution_tier === "EMPEROR";
    const start =
      cell.physical_position % 2
        ? cell.physical_position
        : cell.physical_position - 1;
    const seats = pair
      ? cells.filter(
          (s) =>
            s.row === cell.row &&
            [start, start + 1].includes(s.physical_position),
        )
      : [cell];
    if (
      seats.length !== (pair ? 2 : 1) ||
      seats.some((s) => s.is_blocked || s.side !== cell.side)
    )
      throw Error(
        "A pair needs two adjacent seats on the same side of the aisle.",
      );
    if (person.requires_accessible_seat && seats.some((s) => !s.is_accessible))
      throw Error("This allocation requires accessible seats.");
    return seats.map((s) => s.seat_id);
  }
  const ids = destination(p, target);
  if (
    m.seat_ids.length === ids.length &&
    m.seat_ids.every((id) => ids.includes(id))
  )
    return state;
  const others = Object.entries(state.items).filter(
    ([id, v]) => id !== pid && v.seat_ids.some((s) => ids.includes(s)),
  );
  if (others.length > 1)
    throw Error("Move the separate occupants to the dock first.");
  const next = structuredClone(state);
  const stamp = new Date().toISOString();
  if (others.length) {
    const [otherId, other] = others[0];
    if (
      other.seat_ids.length !== ids.length ||
      !other.seat_ids.every((s) => ids.includes(s))
    )
      throw Error(
        "Swap individuals with individuals or pairs with pairs; use the dock to rearrange different sizes.",
      );
    next.items[otherId].seat_ids = m.seat_ids.length
      ? destination(
          state.participants.find((p) => p.participant_id === otherId)!,
          cells.find((s) => s.seat_id === m.seat_ids[0]),
        )
      : [];
    next.items[otherId].previous_seat_ids = other.seat_ids;
    next.items[otherId].dock_reason = m.seat_ids.length
      ? ""
      : "Displaced during assignment";
    next.items[otherId].changed_at = stamp;
  }
  next.items[pid] = {
    ...m,
    seat_ids: ids,
    previous_seat_ids: m.seat_ids,
    dock_reason: "",
    changed_at: stamp,
  };
  return next;
}
export function dock(state: WorkingState, pid: string): WorkingState {
  const m = state.items[pid];
  const next = structuredClone(state);
  next.items[pid] = {
    ...m,
    seat_ids: [],
    previous_seat_ids: m.seat_ids,
    dock_reason: "Manual rearrangement",
    changed_at: new Date().toISOString(),
  };
  return next;
}

/** Attendance belongs to the entire registration, including both Emperor seats. */
export function markAbsent(state: WorkingState, pid: string): WorkingState {
  const person = state.participants.find((p) => p.participant_id === pid);
  if (!person || !eligible(person)) throw Error("Choose a paid registration.");
  const next = dock(state, pid);
  next.items[pid].previous_seat_ids = state.items[pid].seat_ids.length
    ? [...state.items[pid].seat_ids] : [...state.items[pid].previous_seat_ids];
  next.items[pid].attendance_status = "ABSENT";
  next.items[pid].dock_reason = "Marked absent";
  return next;
}

/** Build a single undoable restore-and-place edit; failed placement changes nothing. */
export function restoreAndMove(state: WorkingState, base: AllocationResult, pid: string, sid: string): WorkingState {
  const next = structuredClone(state);
  next.items[pid].attendance_status = "PRESENT";
  return move(next, base, pid, sid);
}

/** Review rearrangements preserve every paid entitlement, including mixed sizes. */
export function reviewMove(
  state: WorkingState,
  base: AllocationResult,
  pid: string,
  sid: string,
) {
  const cells = base.floor_plan.rows.flatMap((row) =>
    row.seats.map((s) => ({ ...s, row: row.row_number })),
  );
  const people = Object.fromEntries(
    state.participants.map((p) => [p.participant_id, p]),
  );
  const person = people[pid];
  if (!person || !eligible(person)) throw Error("Choose a paid registration.");
  if (state.items[pid].attendance_status === "ABSENT")
    throw Error("Restore attendance before assigning this registration.");
  const pairs = base.source_request?.layout?.approved_pairs;
  if (!pairs)
    throw Error("Reload the draft to retrieve its approved seat pairs.");
  const optionsFor = (id: string) => {
    const p = people[id];
    const available = cells.filter(
      (s) => !s.is_blocked && (!p.requires_accessible_seat || s.is_accessible),
    );
    if (p.contribution_tier !== "EMPEROR")
      return available.map((s) => [s.seat_id]);
    return base.floor_plan.rows.flatMap((row) =>
      pairs.flatMap((pair) => {
        const seats = pair.map((pos) =>
          available.find(
            (s) => s.row === row.row_number && s.physical_position === pos,
          ),
        );
        return seats.every((s) => s) && seats[0]!.side === seats[1]!.side
          ? [seats.map((s) => s!.seat_id)]
          : [];
      }),
    );
  };
  const target = optionsFor(pid).find((ids) => ids.includes(sid));
  if (!target)
    throw Error(
      "This destination cannot fit the required seats or accessibility.",
    );
  if (
    target.length === state.items[pid].seat_ids.length &&
    target.every((s) => state.items[pid].seat_ids.includes(s))
  )
    return { state, chain: false, description: "" };
  const displaced = Object.keys(state.items).filter(
    (id) =>
      id !== pid && state.items[id].seat_ids.some((s) => target.includes(s)),
  );
  const occupied = new Set(
    Object.entries(state.items)
      .filter(([id]) => id !== pid && !displaced.includes(id))
      .flatMap(([, item]) => item.seat_ids),
  );
  target.forEach((s) => occupied.add(s));
  const source = state.items[pid].seat_ids;
  const assignments: Record<string, string[]> = { [pid]: target };
  function place(index: number): boolean {
    if (index === displaced.length) return true;
    const id = displaced[index];
    for (const option of optionsFor(id).filter((ids) =>
      ids.some((s) => source.includes(s)),
    )) {
      if (option.some((s) => occupied.has(s))) continue;
      assignments[id] = option;
      option.forEach((s) => occupied.add(s));
      if (place(index + 1)) return true;
      option.forEach((s) => occupied.delete(s));
    }
    return false;
  }
  if (!place(0))
    throw Error(
      "This rearrangement needs the holding dock — go back to editing.",
    );
  const next = structuredClone(state);
  for (const [id, ids] of Object.entries(assignments))
    next.items[id] = {
      ...next.items[id],
      seat_ids: ids,
      previous_seat_ids: state.items[id].seat_ids,
      changed_at: new Date().toISOString(),
      dock_reason: "",
    };
  return {
    state: next,
    chain:
      displaced.some(
        (id) => state.items[id].seat_ids.length !== target.length,
      ) || displaced.length > 1,
    description: Object.keys(assignments)
      .map(
        (id) =>
          `${state.items[id].display_names[0]} → ${assignments[id].join(" + ")}`,
      )
      .join("; "),
  };
}
