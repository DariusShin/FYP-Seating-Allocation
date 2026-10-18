import type { AllocationResult, Registration, TierName } from "./allocation-types";

/** Component counts the skeleton animates: one Emperor registration is a
 * joined pair component (two seats); Bodhi and Merit are single seats. */
export interface SkeletonCounts {
  emperor: number;
  bodhi: number;
  merit: number;
  accessible: Record<TierName, number>;
}

export interface SkeletonStep {
  /** Synthetic registration id so equal-tier neighbours never merge. */
  owner: string;
  tier: TierName;
  seat_ids: string[];
}

export const SKELETON_FILL_MS = 60_000;
export const SKELETON_FINISH_MS = 1_500;
export const MAP_REVEAL_MS = 2_400;

/** Count eligible registration units, using the same paid/attendance rules as
 * the solver. Emperor counts are pairs, not physical seat counts. */
export function countsFromRegistrations(
  registrations: readonly Registration[],
  attendance: Record<string, "PRESENT" | "ABSENT"> = {},
): SkeletonCounts {
  const tiers = { EMPEROR: 0, BODHI: 0, MERIT: 0 };
  const accessible = { EMPEROR: 0, BODHI: 0, MERIT: 0 };
  for (const registration of registrations) {
    if (
      registration.registration_status !== "CONFIRMED" ||
      attendance[registration.participant_id] === "ABSENT"
    ) continue;
    tiers[registration.contribution_tier] += 1;
    if (registration.requires_accessible_seat)
      accessible[registration.contribution_tier] += 1;
  }
  return {
    emperor: tiers.EMPEROR,
    merit: tiers.MERIT,
    bodhi: tiers.BODHI,
    accessible,
  };
}

export function countsFromSetup(setup: {
  tier_counts: { emperor_count: number; bodhi_count: number; merit_count: number };
  accessible_counts: {
    emperor_count: number;
    bodhi_count: number;
    merit_count: number;
  };
}): SkeletonCounts {
  return {
    emperor: setup.tier_counts.emperor_count,
    bodhi: setup.tier_counts.bodhi_count,
    merit: setup.tier_counts.merit_count,
    accessible: {
      EMPEROR: setup.accessible_counts.emperor_count,
      BODHI: setup.accessible_counts.bodhi_count,
      MERIT: setup.accessible_counts.merit_count,
    },
  };
}

/** Regeneration already knows the frozen solver snapshot. */
export function countsFromResult(
  result: Pick<AllocationResult, "source_request" | "input_summary">,
): SkeletonCounts {
  const participants = result.source_request?.participants;
  if (participants)
    return countsFromRegistrations(participants, result.source_request?.attendance);
  const s = result.input_summary;
  return {
    emperor: s?.emperor_count ?? 0,
    bodhi: s?.bodhi_count ?? 0,
    merit: s?.merit_count ?? 0,
    accessible: { EMPEROR: 0, BODHI: 0, MERIT: 0 },
  };
}

interface FlatSeat {
  seat_id: string;
  row_number: number;
  physical_position: number;
  side: "LEFT" | "RIGHT";
  priority_rank: number;
}

function flatSeats(floor: Pick<AllocationResult["floor_plan"], "rows">): FlatSeat[] {
  return floor.rows
    .flatMap((row) =>
      row.seats
        .filter((s) => !s.is_blocked)
        .map((s) => ({
          seat_id: s.seat_id,
          row_number: row.row_number,
          physical_position: s.physical_position,
          side: s.side,
          priority_rank: s.priority_rank,
        })),
    )
    .sort(
      (a, b) =>
        a.row_number - b.row_number ||
        a.priority_rank - b.priority_rank ||
        a.physical_position - b.physical_position,
    );
}

/** Pre-calculate the seat-filling sequence the animation replays: Emperor
 * registrations take joined approved pairs, then Merit and Bodhi take singles.
 * Priority ranks are local to each row: east 9–16, then west 8–1.
 * These anonymous components show entitlements; accessible registration
 * identities are assigned within their tier by the solver, without making
 * the preview jump to distant rows or leave gaps in the fill sequence. */
export function buildSkeletonPlan(
  floor: Pick<AllocationResult["floor_plan"], "rows" | "aisle_after_position" | "approved_pairs">,
  counts: SkeletonCounts,
  approvedPairs: readonly number[][] | undefined = floor.approved_pairs,
): SkeletonStep[] {
  const seats = flatSeats(floor);
  const occupied = new Set<string>();
  const steps: SkeletonStep[] = [];
  let sequence = 0;

  const pairable = (a: FlatSeat, b: FlatSeat) => {
    if (
      a.row_number !== b.row_number ||
      a.side !== b.side ||
      Math.abs(a.physical_position - b.physical_position) !== 1
    ) return false;
    const low = Math.min(a.physical_position, b.physical_position);
    const high = Math.max(a.physical_position, b.physical_position);
    if (approvedPairs)
      return approvedPairs.some(([first, second]) => first === low && second === high);
    // Older saved layouts omit approved_pairs. Reconstruct the hall's
    // disjoint pairs from each side's physical starting position.
    const sideStart = a.side === "LEFT" ? 1 : floor.aisle_after_position + 1;
    return (low - sideStart) % 2 === 0;
  };

  const claim = (tier: TierName, size: 1 | 2) => {
    for (let i = 0; i < seats.length; i++) {
      const first = seats[i];
      if (occupied.has(first.seat_id)) continue;
      if (size === 1) {
        occupied.add(first.seat_id);
        steps.push({
          owner: `skeleton-${tier.toLowerCase()}-${++sequence}`,
          tier,
          seat_ids: [first.seat_id],
        });
        return true;
      }
      const second = seats[i + 1];
      if (second && pairable(first, second) && !occupied.has(second.seat_id)) {
        occupied.add(first.seat_id);
        occupied.add(second.seat_id);
        steps.push({
          owner: `skeleton-${tier.toLowerCase()}-${++sequence}`,
          tier,
          seat_ids: [first.seat_id, second.seat_id],
        });
        return true;
      }
    }
    return false;
  };

  const queue: { tier: TierName; size: 1 | 2; count: number }[] = [
    { tier: "EMPEROR", size: 2, count: counts.emperor },
    { tier: "MERIT", size: 1, count: counts.merit },
    { tier: "BODHI", size: 1, count: counts.bodhi },
  ];
  // Consume the tier queue continuously, including mixed-tier boundary rows.
  for (const item of queue) {
    for (let n = 0; n < item.count; n++)
      if (!claim(item.tier, item.size)) break;
  }
  return steps;
}

/** Shared by the pacing hook: how many steps are visible at `elapsed` ms. */
export function placementAt(elapsed: number, total: number, durationMs: number) {
  if (total <= 0) return 0;
  if (elapsed >= durationMs) return total;
  return Math.min(total, Math.max(0, Math.floor((elapsed / durationMs) * total)));
}

/** Fetching the workspace overlaps this short handoff, rather than adding a
 * second full delay after a slow request. */
export function waitForMapReveal(openingStarted: number): Promise<void> {
  const remaining = MAP_REVEAL_MS - (performance.now() - openingStarted);
  return remaining > 0
    ? new Promise((resolve) => setTimeout(resolve, remaining))
    : Promise.resolve();
}
