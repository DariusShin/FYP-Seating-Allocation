import type { AllocationResult, Registration, TierName } from "./allocation-types";

/** Backend tier precedence (seat_solver.production.policy.TIERS); index 0 is the highest. */
export const TIER_PRECEDENCE: readonly TierName[] = [
  "EMPEROR",
  "MERIT",
  "BODHI",
];

/** Emperor registrations always occupy an approved two-seat pair. */
const TIER_SEAT_COUNT: Record<TierName, number> = {
  EMPEROR: 2,
  MERIT: 1,
  BODHI: 1,
};

export interface TierBoundary {
  tier: TierName;
  rows: number | null;
  seat_id: string | null;
  row_number: number | null;
  priority_rank: number | null;
  order: number | null;
  start_seat_id: string | null;
  start_row_number: number | null;
  start_order: number;
}

export interface MovementBoundary {
  limit: (tier: TierName) => TierBoundary | null;
  assertAllowed: (tier: TierName, seatIds: string[], currentSeatIds?: string[]) => void;
}

/**
 * Pre-calculates the strict band every contribution tier may occupy from the
 * draft's own geometry and present registrations: the band starts right after
 * the seats the higher tiers need and ends at the seats this tier needs, so a
 * tier can never be dragged behind a lower tier or in front of a higher one,
 * mirroring safeguard C12 on the service.
 */
export function movementBoundary(
  floor: AllocationResult["floor_plan"],
  participants: Registration[],
): MovementBoundary | null {
  const width = floor.seats_per_row;
  const seats = floor.rows.flatMap((row) =>
    row.seats.map((seat) => ({ ...seat, row_number: row.row_number })),
  );
  if (!width || !floor.aisle_after_position || seats.some((s) => !s.priority_rank))
    return null;
  const orderOf = new Map(
    seats.map((s) => [s.seat_id, (s.row_number - 1) * width + s.priority_rank!]),
  );
  const assignable = seats
    .filter((s) => !s.is_blocked)
    .sort((a, b) => orderOf.get(a.seat_id)! - orderOf.get(b.seat_id)!);
  const order = (seat: (typeof assignable)[number]) => orderOf.get(seat.seat_id)!;
  const counts: Record<TierName, number> = { EMPEROR: 0, MERIT: 0, BODHI: 0 };
  for (const p of participants)
    if (p.registration_status === "CONFIRMED") counts[p.contribution_tier]++;
  const limits: Partial<Record<TierName, TierBoundary>> = {};
  let cumulative = 0;
  for (const tier of TIER_PRECEDENCE) {
    const start = assignable[cumulative];
    cumulative += counts[tier] * TIER_SEAT_COUNT[tier];
    const seat = assignable[cumulative - 1];
    limits[tier] = {
      tier,
      rows: cumulative ? Math.ceil(cumulative / width) : null,
      seat_id: seat?.seat_id ?? null,
      row_number: seat?.row_number ?? null,
      priority_rank: seat?.priority_rank ?? null,
      order: seat ? order(seat) : null,
      start_seat_id: start?.seat_id ?? null,
      start_row_number: start?.row_number ?? null,
      start_order: start ? order(start) : 0,
    };
  }
  return {
    limit: (tier) => limits[tier] ?? null,
    assertAllowed(tier, seatIds, currentSeatIds = []) {
      const limit = limits[tier];
      if (!limit) return;
      const outside = (id: string) => {
        const seatOrder = orderOf.get(id);
        if (seatOrder === undefined) return false;
        return (
          (limit.order !== null && seatOrder > limit.order) ||
          seatOrder < limit.start_order
        );
      };
      if (currentSeatIds.some(outside)) return;
      const offender = seatIds.find(outside);
      if (!offender) return;
      if (limit.order !== null && (orderOf.get(offender) ?? 0) > limit.order)
        throw Error(
          `${tier} seating cannot be placed behind ${limit.seat_id} (row ${limit.row_number}); keep it within rows 1-${limit.rows}.`,
        );
      throw Error(
        `${tier} seating cannot be placed in front of ${limit.start_seat_id} (row ${limit.start_row_number}); higher tiers must stay in front of it.`,
      );
    },
  };
}
