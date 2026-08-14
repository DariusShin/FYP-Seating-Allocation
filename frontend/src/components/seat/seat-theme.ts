import type { Assignment, TierName } from "@/lib/allocation-types";

export interface TierStyle {
  label: string;
  cell: string;
  dot: string;
  badge: string;
  bar: string;
}

/** Gold / silver / bronze tier palette echoing the Buddy seat-map prototype.
 * Tier bands are demand-derived, so labels never carry a fixed row range. */
export const TIER_STYLES: Record<TierName, TierStyle> = {
  EMPEROR: {
    label: "Emperor",
    cell: "border-amber-500/70 bg-amber-200 text-amber-950 hover:bg-amber-300 dark:border-amber-400/60 dark:bg-amber-400/25 dark:text-amber-100 dark:hover:bg-amber-400/40",
    dot: "bg-amber-400 dark:bg-amber-500",
    badge:
      "border-amber-500/50 bg-amber-100 text-amber-900 dark:bg-amber-400/20 dark:text-amber-100",
    bar: "bg-amber-400 dark:bg-amber-500",
  },
  BODHI: {
    label: "Bodhi",
    cell: "border-zinc-400/80 bg-zinc-200 text-zinc-900 hover:bg-zinc-300 dark:border-zinc-500/60 dark:bg-zinc-500/25 dark:text-zinc-100 dark:hover:bg-zinc-500/40",
    dot: "bg-zinc-400 dark:bg-zinc-500",
    badge:
      "border-zinc-400/60 bg-zinc-100 text-zinc-800 dark:bg-zinc-500/20 dark:text-zinc-100",
    bar: "bg-zinc-400 dark:bg-zinc-500",
  },
  MERIT: {
    label: "Merit",
    cell: "border-orange-500/60 bg-orange-100 text-orange-950 hover:bg-orange-200 dark:border-orange-400/50 dark:bg-orange-400/20 dark:text-orange-100 dark:hover:bg-orange-400/35",
    dot: "bg-orange-400 dark:bg-orange-500",
    badge:
      "border-orange-500/50 bg-orange-100 text-orange-900 dark:bg-orange-400/20 dark:text-orange-100",
    bar: "bg-orange-400 dark:bg-orange-500",
  },
};

export const CATEGORY_LABELS: Record<Assignment["participant_category"], string> = {
  MONASTIC: "Monastic",
  COMMITTEE: "Committee",
  VOLUNTEER: "Volunteer",
  GENERAL_DEVOTEE: "General devotee",
};

/** Plain-language names for the four soft-constraint penalty components. */
export const COMPONENT_LABELS: Record<string, string> = {
  priority_seat: "Care & accessibility",
  category_zone: "Preferred areas",
  movement: "Seat changes",
  activeness: "Participation",
};

/**
 * Unique hall-wide seat number, counted from the centre aisle outward:
 * row 1 reads 12 10 8 6 4 2 | 1 3 5 7 9 11 and row 2 continues with
 * 24 22 20 18 16 14 | 13 15 17 19 21 23. The per-row pattern is exactly the
 * seat's priority_rank, offset by the seats in earlier rows.
 */
export function seatNumber(
  rowNumber: number,
  priorityRank: number,
  seatsPerRow: number,
): number {
  return (rowNumber - 1) * seatsPerRow + priorityRank;
}

export type HighlightMode =
  | "none"
  | "elderly"
  | "monk"
  | "accessible"
  | "moved"
  | "kept";

export const HIGHLIGHT_OPTIONS: { value: HighlightMode; label: string }[] = [
  { value: "none", label: "No highlight" },
  { value: "elderly", label: "Elderly ★" },
  { value: "monk", label: "Monastics ☸" },
  { value: "accessible", label: "Accessible ♿" },
  { value: "moved", label: "Moved since last plan" },
  { value: "kept", label: "Kept previous seat" },
];

export function matchesHighlight(
  assignment: Assignment | undefined,
  mode: HighlightMode,
): boolean {
  if (mode === "none") return true;
  if (!assignment) return false;
  switch (mode) {
    case "elderly":
      return assignment.is_elderly;
    case "monk":
      return assignment.is_monk;
    case "accessible":
      return assignment.requires_accessible_seat;
    case "moved":
      return assignment.moved === true;
    case "kept":
      return assignment.moved === false;
    default:
      return true;
  }
}

export function seatMarkers(assignment: Assignment | undefined): string[] {
  if (!assignment) return [];
  const markers: string[] = [];
  if (assignment.is_monk) markers.push("☸");
  if (assignment.is_elderly) markers.push("★");
  if (assignment.requires_accessible_seat) markers.push("♿");
  return markers;
}

export const formatNumber = (value: number): string =>
  value.toLocaleString("en-MY");

export const formatRM = (value: number): string =>
  `RM${value.toLocaleString("en-MY")}`;
