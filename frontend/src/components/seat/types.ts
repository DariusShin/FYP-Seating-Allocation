import type { SeatCell } from "@/lib/allocation-types";
import type { WorkingItem } from "@/lib/workspace";

// Domain types have one definition in lib; seat components import them here.
export type {
  AllocationResult,
  Preference,
  Registration,
  TierName,
} from "@/lib/allocation-types";
export type { Workspace, WorkingState, WorkingItem } from "@/lib/workspace";
export type { AttributedEdit, Finding, Review } from "@/lib/verification";

export type SeatMode = "read" | "edit";
export type SeatModal =
  | "allocation"
  | "checklist"
  | "settings"
  | "versions"
  | "history"
  | "legend"
  | null;
export type GenerationPhase = "generating" | "loading-workspace" | "error";
export type SeatCellWithRow = SeatCell & { row: number };
export type LocationFormatter = (ids: string[]) => string;
export type DetailChanges = Pick<WorkingItem, "display_names" | "note">;
export type PlanVersion = { id: string; state: string; created: string };
export interface SeatSelection {
  participantId: string | null;
  seatId: string | null;
}
export interface SeatMarkers {
  hasNote?: boolean;
  elderly?: boolean;
  accessible?: boolean;
}
