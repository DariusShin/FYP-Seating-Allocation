import type { SeatCell } from "./allocation-types";

/** Group only two physically adjacent cells owned by the same allocation.
 * Never group across an aisle, a structural block, or separate registrations. */
export function seatGroups(seats: SeatCell[], owners: Record<string, string>) {
  const groups: { seats: SeatCell[]; owner?: string }[] = [];
  const sorted = [...seats].sort(
    (a, b) => a.physical_position - b.physical_position,
  );
  for (let i = 0; i < sorted.length; i++) {
    const seat = sorted[i];
    const next = sorted[i + 1];
    const owner = owners[seat.seat_id];
    if (
      owner &&
      next &&
      !seat.is_blocked &&
      !next.is_blocked &&
      owners[next.seat_id] === owner &&
      seat.side === next.side &&
      next.physical_position === seat.physical_position + 1
    ) {
      groups.push({ seats: [seat, next], owner });
      i++;
    } else groups.push({ seats: [seat], owner });
  }
  return groups;
}

/** Physical gaps in the PJKIT hall: West 5–8 and East 1–4 in rows 6 and 8.
 * Keep these blocked cells in solver data, but reserve blank space in the UI. */
export function isAisleGap(row: number, position: number): boolean {
  return (row === 6 || row === 8) && position >= 5 && position <= 12;
}
