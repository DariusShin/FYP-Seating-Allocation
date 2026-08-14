"use client";

import { Fragment } from "react";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type {
  AllocationResult,
  Assignment,
  FloorPlanRow,
  SeatCell,
  TierName,
} from "@/lib/allocation-types";

import {
  formatRM,
  matchesHighlight,
  seatMarkers,
  seatNumber,
  TIER_STYLES,
  type HighlightMode,
} from "./seat-theme";

interface SeatMapProps {
  result: AllocationResult;
  assignmentBySeat: Map<string, Assignment>;
  showNames: boolean;
  highlight: HighlightMode;
  selectedId: string | null;
  onSelect: (participantId: string | null) => void;
}

function SeatTooltip({
  seat,
  number,
  assignment,
}: {
  seat: SeatCell;
  number: number;
  assignment?: Assignment;
}) {
  if (!assignment) {
    return (
      <div className="space-y-1 text-xs">
        <p className="font-semibold">
          Seat {number}
          <span className="ml-1.5 font-normal text-muted-foreground">
            {seat.seat_id}
          </span>
        </p>
        <p className="text-muted-foreground">
          {seat.is_blocked ? "Blocked seat" : "Empty seat"} · priority #
          {seat.priority_rank} · {seat.zone.replaceAll("_", " ").toLowerCase()}
        </p>
        {seat.is_accessible && <p>♿ Accessible seat</p>}
      </div>
    );
  }
  const weighted = assignment.penalty.weighted;
  return (
    <div className="w-56 space-y-1.5 text-xs">
      <div className="flex items-baseline justify-between gap-2">
        <p className="font-semibold">{seat.display_name}</p>
        <span className="text-muted-foreground">{assignment.participant_id}</span>
      </div>
      <p className="text-muted-foreground">
        {TIER_STYLES[assignment.contribution_tier].label} ·{" "}
        {formatRM(assignment.contribution_amount_rm)}
        {assignment.allocation_type === "EMPEROR_PAIR" &&
          ` · pair #${assignment.pair_priority}`}
      </p>
      <p className="text-muted-foreground">
        Seat {number} · {seat.seat_id} · priority #{seat.priority_rank}
        {seat.is_accessible && " · ♿ accessible"}
      </p>
      {(assignment.is_monk ||
        assignment.is_elderly ||
        assignment.requires_accessible_seat) && (
        <p>
          {assignment.is_monk && "☸ Monastic  "}
          {assignment.is_elderly && "★ Elderly  "}
          {assignment.requires_accessible_seat && "♿ Needs accessible"}
        </p>
      )}
      {assignment.moved !== null && (
        <p className={assignment.moved ? "text-orange-500" : "text-emerald-600"}>
          {assignment.moved
            ? `↻ Moved from ${assignment.previous_seat_ids.join(", ")}`
            : "Kept previous seat"}
        </p>
      )}
      <div className="border-t pt-1.5 text-muted-foreground">
        <div className="flex justify-between">
          <span>Weighted penalty</span>
          <span className="font-medium text-foreground">{weighted.total}</span>
        </div>
        <div className="flex justify-between">
          <span>care / area / moves / activity</span>
          <span>
            {weighted.priority_seat}/{weighted.category_zone}/{weighted.movement}/
            {weighted.activeness}
          </span>
        </div>
      </div>
    </div>
  );
}

function Seat({
  seat,
  number,
  assignment,
  showNames,
  highlight,
  selected,
  onSelect,
}: {
  seat: SeatCell;
  number: number;
  assignment?: Assignment;
  showNames: boolean;
  highlight: HighlightMode;
  selected: boolean;
  onSelect: (participantId: string | null) => void;
}) {
  const tier = assignment?.contribution_tier;
  const dimmed =
    highlight !== "none" && !matchesHighlight(assignment, highlight);
  const markers = seatMarkers(assignment);

  return (
    <Tooltip delayDuration={150}>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={() =>
            onSelect(
              assignment && !selected ? assignment.participant_id : null,
            )
          }
          className={cn(
            "flex h-11 min-w-0 flex-1 flex-col justify-between overflow-hidden rounded-md border px-1 py-0.5 text-left transition-all sm:h-13",
            seat.occupancy_status === "OCCUPIED" && tier
              ? TIER_STYLES[tier].cell
              : seat.occupancy_status === "BLOCKED"
                ? "cursor-default border-destructive/40 bg-destructive/10 text-destructive"
                : "cursor-default border-dashed border-muted-foreground/30 bg-muted/30 text-muted-foreground/70",
            dimmed && "opacity-30 saturate-50",
            selected && "ring-2 ring-ring ring-offset-1 ring-offset-background",
          )}
        >
          <span className="flex items-center justify-between text-[9px] leading-none opacity-80">
            <span>{number}</span>
            <span className="shrink-0">
              {assignment?.moved === true && "↻"}
              {markers.join("")}
            </span>
          </span>
          <span className="truncate text-[10px] font-medium leading-tight">
            {seat.occupancy_status === "BLOCKED"
              ? "✕"
              : showNames
                ? (seat.display_name ?? "")
                : (assignment?.participant_id ?? "")}
          </span>
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="bg-popover text-popover-foreground border shadow-md">
        <SeatTooltip seat={seat} number={number} assignment={assignment} />
      </TooltipContent>
    </Tooltip>
  );
}

function ZoneDivider({ tier }: { tier: TierName }) {
  const style = TIER_STYLES[tier];
  return (
    <div className="flex items-center gap-2 pt-2 first:pt-0">
      <span className={cn("size-2 rounded-full", style.dot)} />
      <span className="text-[11px] font-semibold tracking-wide text-muted-foreground">
        {style.label.toUpperCase()} ZONE
      </span>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}

export function SeatMap({
  result,
  assignmentBySeat,
  showNames,
  highlight,
  selectedId,
  onSelect,
}: SeatMapProps) {
  const { rows, aisle_after_position, seats_per_row } = result.floor_plan;

  const renderRow = (row: FloorPlanRow) => (
    <div key={row.row_number} className="flex items-stretch gap-1">
      <div className="flex w-9 shrink-0 flex-col items-center justify-center rounded-md bg-muted/50 text-[10px] font-semibold text-muted-foreground">
        R{String(row.row_number).padStart(2, "0")}
      </div>
      {row.seats.map((seat) => {
        const assignment = seat.participant_id
          ? assignmentBySeat.get(seat.seat_id)
          : undefined;
        return (
          <Fragment key={seat.seat_id}>
            {seat.physical_position === aisle_after_position + 1 && (
              <div className="w-4 shrink-0 border-x border-dashed border-muted-foreground/25 sm:w-7" />
            )}
            <Seat
              seat={seat}
              number={seatNumber(row.row_number, seat.priority_rank, seats_per_row)}
              assignment={assignment}
              showNames={showNames}
              highlight={highlight}
              selected={
                selectedId !== null &&
                assignment?.participant_id === selectedId
              }
              onSelect={onSelect}
            />
          </Fragment>
        );
      })}
    </div>
  );

  return (
    <div className="space-y-1.5">
      {/* Altar / stage reference, as on the Buddy prototype */}
      <div className="mb-3 rounded-lg border border-amber-500/40 bg-gradient-to-r from-amber-100 via-amber-50 to-amber-100 py-2 text-center text-xs font-semibold tracking-[0.3em] text-amber-900 dark:from-amber-400/20 dark:via-amber-400/10 dark:to-amber-400/20 dark:text-amber-200">
        ALTAR / STAGE
      </div>

      {/* Seats carry unique numbers counted outward from the aisle: even on
          the left half, odd on the right (row 1: 12 10 8 6 4 2 | 1 3 5 7 9 11). */}
      <div className="mb-1 flex items-stretch gap-1 text-center text-[9px] text-muted-foreground">
        <div className="w-9 shrink-0" />
        <div className="min-w-0 flex-1 truncate">
          even seat numbers ← counted from aisle
        </div>
        <div className="w-4 shrink-0 truncate sm:w-7">AISLE</div>
        <div className="min-w-0 flex-1 truncate">
          counted from aisle → odd seat numbers
        </div>
      </div>

      {rows.map((row, index) => {
        const previous = rows[index - 1];
        const startsBand =
          row.tier_band !== null &&
          (!previous || previous.tier_band !== row.tier_band);
        return (
          <Fragment key={row.row_number}>
            {startsBand && row.tier_band && <ZoneDivider tier={row.tier_band} />}
            {renderRow(row)}
          </Fragment>
        );
      })}
    </div>
  );
}
