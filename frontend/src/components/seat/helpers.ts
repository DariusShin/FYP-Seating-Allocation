import type {
  AllocationResult,
  SeatCellWithRow,
  SeatMarkers,
  WorkingState,
} from "./types";

// Keep domain semantics in their canonical modules while giving seat components
// one shared entry point for editing and review helpers.
export { dock, eligible, move, reviewMove } from "@/lib/workspace";
export {
  focusedGroups,
  restorationResolves,
  participantSeats,
  findingSeats,
  reviewSeatHighlights,
  followSelectedSeat,
} from "@/lib/verification";

export function planPath(eventId: string, planId: string) {
  return `/events/${encodeURIComponent(eventId)}/seating-plans/${encodeURIComponent(planId)}`;
}
export const verificationPath = (eventId: string, planId: string) =>
  `${planPath(eventId, planId)}/verification`;
export const venuePath = (eventId: string) =>
  `/events/${encodeURIComponent(eventId)}/venue`;
export const eventApi = (path: string, eventId: string) =>
  `${path}?event_id=${encodeURIComponent(eventId)}`;

export function savedTime(value: string) {
  return new Date(value).toLocaleTimeString("en-MY", {
    timeZone: "Asia/Kuala_Lumpur",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
}

export function floorCells(
  floor: AllocationResult["floor_plan"],
): SeatCellWithRow[] {
  return floor.rows.flatMap((r) =>
    r.seats.map((s) => ({ ...s, row: r.row_number })),
  );
}

export function seatLocation(cells: SeatCellWithRow[], ids: string[]) {
  return ids.length
    ? ids
        .map((id) => {
          const seat = cells.find((s) => s.seat_id === id);
          if (!seat) return id;
          return `${seat.side === "LEFT" ? "西單" : "東單"} ${seat.row} · ${seat.physical_position <= 8 ? seat.physical_position : seat.physical_position - 8}`;
        })
        .join(" + ")
    : "Holding dock";
}

export function workspaceMapData(state: WorkingState) {
  const names: Record<string, string> = {},
    owners: Record<string, string> = {};
  for (const [pid, item] of Object.entries(state.items)) {
    for (const sid of item.seat_ids) {
      owners[sid] = pid;
      names[sid] = item.display_names[0];
    }
  }
  return {
    names,
    owners,
    primaryNames: Object.fromEntries(
      Object.entries(state.items).map(([pid, item]) => [
        pid,
        item.display_names[0],
      ]),
    ),
    tiers: Object.fromEntries(
      state.participants.map((p) => [p.participant_id, p.contribution_tier]),
    ),
    markers: Object.fromEntries(
      state.participants.map((p) => [
        p.participant_id,
        {
          hasNote: !!state.items[p.participant_id]?.note,
          elderly: p.age >= 60,
          accessible: p.requires_accessible_seat,
        } satisfies SeatMarkers,
      ]),
    ),
  };
}

export function participantMatches(state: WorkingState, query: string) {
  const text = query.trim().toLocaleLowerCase();
  return new Set(
    state.participants
      .filter((p) =>
        `${p.full_name} ${p.participant_id} ${state.items[p.participant_id]?.display_names.join(" ") ?? ""}`
          .toLocaleLowerCase()
          .includes(text),
      )
      .map((p) => p.participant_id),
  );
}
