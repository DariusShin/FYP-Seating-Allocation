import type { TierName } from "./types";

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
