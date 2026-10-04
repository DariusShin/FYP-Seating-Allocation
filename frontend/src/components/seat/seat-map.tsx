"use client";

import { Fragment, useEffect, useRef } from "react";
import { ArrowRightLeft, Grip, UserRoundPlus } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { isAisleGap } from "@/lib/seat-groups";
import { cn } from "@/lib/utils";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";
import {
  matchesHighlight,
  seatMarkers,
  seatNumber,
  TIER_STYLES,
  type HighlightMode,
} from "./seat-theme";

import { useSeatDrag } from "./use-seat-drag";

interface SeatMapProps {
  result: AllocationResult;
  assignmentBySeat: Map<string, Assignment>;
  showNames: boolean;
  highlight: HighlightMode;
  selectedSeatId: string | null;
  focusedId: string | null;
  onSelect: (seatId: string) => void;
  onMove: (participantId: string, seatId: string) => void;
  validateDrop: (participantId: string, seatId: string) => string | null;
  disabled?: boolean;
}

export function SeatMap({
  result,
  assignmentBySeat,
  showNames,
  highlight,
  selectedSeatId,
  focusedId,
  onSelect,
  onMove,
  validateDrop,
  disabled,
}: SeatMapProps) {
  const drag = useSeatDrag(onMove);
  const { dragId, target } = drag;
  const focusedSeatRef = useRef<HTMLButtonElement | null>(null);
  const { rows, aisle_after_position, seats_per_row } = result.floor_plan;
  useEffect(() => {
    focusedSeatRef.current?.scrollIntoView({
      block: "nearest",
      inline: "center",
    });
  }, [focusedId]);
  const dropError = dragId && target ? validateDrop(dragId, target) : null;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <ArrowRightLeft className="size-3.5" />
          Drag to move or swap
        </span>
        <span className="flex items-center gap-2">
          <UserRoundPlus className="size-3.5" />
          Click a seat to assign or remove
        </span>
        <span className="ml-auto">Pairs move together</span>
      </div>
      <div
        className="overflow-x-auto pb-2"
        role="region"
        aria-label="Interactive hall seating plan"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Escape") drag.cancel();
        }}
      >
        <div className="mx-auto flex min-w-250 max-w-350 flex-col gap-1.5">
          <div className="mb-4 flex h-10 items-center justify-center rounded-lg border border-dashed bg-muted/30 text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Altar / Stage
          </div>
          <div className="mb-2 flex text-center text-[10px] tracking-wider text-muted-foreground">
            <span className="w-9" />
            <span className="flex-1">WEST · EVEN SEAT NUMBERS</span>
            <span className="w-10">AISLE</span>
            <span className="flex-1">EAST · ODD SEAT NUMBERS</span>
          </div>
          {rows.map((row) => (
            <div key={row.row_number} className="flex items-stretch gap-1.5">
              <span className="flex w-9 shrink-0 items-center justify-center font-mono text-[10px] text-muted-foreground">
                R{String(row.row_number).padStart(2, "0")}
              </span>
              {row.seats.map((seat) => {
                if (isAisleGap(row.row_number, seat.physical_position))
                  return (
                    <Fragment key={seat.seat_id}>
                      {seat.physical_position === aisle_after_position + 1 && (
                        <div aria-hidden="true" className="w-10 shrink-0" />
                      )}
                      <div aria-hidden="true" className="min-w-0 flex-1" />
                    </Fragment>
                  );
                const assignment = assignmentBySeat.get(seat.seat_id);
                const number = seatNumber(
                  row.row_number,
                  seat.priority_rank,
                  seats_per_row,
                );
                const displayName = assignment?.seats.find(
                  (s) => s.seat_id === seat.seat_id,
                )?.display_name;
                const isSource = Boolean(
                  dragId && assignment?.participant_id === dragId,
                );
                const isTarget = target === seat.seat_id;
                const dimmed =
                  !matchesHighlight(assignment, highlight) ||
                  Boolean(
                    focusedId && assignment?.participant_id !== focusedId,
                  );
                return (
                  <Fragment key={seat.seat_id}>
                    {seat.physical_position === aisle_after_position + 1 && (
                      <div className="w-10 shrink-0 border-x border-dashed border-border" />
                    )}
                    <Tooltip
                      delayDuration={350}
                      open={dragId ? false : undefined}
                    >
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          data-seat-id={seat.seat_id}
                          ref={
                            focusedId === assignment?.participant_id &&
                            assignment?.seat_ids[0] === seat.seat_id
                              ? focusedSeatRef
                              : undefined
                          }
                          aria-label={`Seat ${number}, ${seat.seat_id}: ${seat.is_blocked ? "blocked" : (displayName ?? "available")}${assignment?.allocation_type === "EMPEROR_PAIR" ? ", paired registration" : ""}`}
                          disabled={seat.is_blocked || disabled}
                          onClick={() => {
                            if (!drag.consumeClick()) onSelect(seat.seat_id);
                          }}
                          onDragStart={(event) => event.preventDefault()}
                          onPointerDown={(event) =>
                            drag.onPointerDown(
                              event,
                              disabled ? undefined : assignment?.participant_id,
                            )
                          }
                          onPointerMove={drag.onPointerMove}
                          onPointerUp={drag.onPointerUp}
                          onPointerCancel={drag.cancel}
                          onLostPointerCapture={drag.cancel}
                          className={cn(
                            "relative flex h-14 min-w-0 flex-1 flex-col justify-between rounded-lg border p-1.5 text-left transition-[background-color,opacity,box-shadow] select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                            seat.is_blocked
                              ? "cursor-not-allowed bg-[repeating-linear-gradient(135deg,transparent,transparent_4px,var(--muted)_4px,var(--muted)_6px)] text-muted-foreground/50"
                              : assignment
                                ? "touch-none cursor-grab border-border bg-secondary text-secondary-foreground hover:bg-accent active:cursor-grabbing"
                                : "border-dashed bg-background text-muted-foreground hover:border-primary/40 hover:bg-muted/50",
                            dimmed && "opacity-25",
                            isSource && "opacity-35",
                            isTarget &&
                              (dropError
                                ? "ring-2 ring-destructive"
                                : "ring-2 ring-primary ring-offset-1"),
                            selectedSeatId === seat.seat_id &&
                              "ring-2 ring-ring",
                            focusedId &&
                              assignment?.participant_id === focusedId &&
                              "ring-2 ring-ring",
                          )}
                        >
                          <span className="flex items-center justify-between font-mono text-[9px] text-muted-foreground">
                            <span>{number}</span>
                            {assignment && (
                              <span
                                className={cn(
                                  "size-1.5 rounded-full",
                                  TIER_STYLES[assignment.contribution_tier].dot,
                                )}
                              />
                            )}
                          </span>
                          <span className="truncate text-[10px] font-medium">
                            {seat.is_blocked
                              ? "×"
                              : showNames
                                ? displayName
                                : assignment?.participant_id}
                          </span>
                          {assignment && (
                            <span className="flex items-center justify-between text-[8px] text-muted-foreground">
                              <span>
                                {assignment.allocation_type === "EMPEROR_PAIR"
                                  ? "PAIR"
                                  : ""}
                              </span>
                              <span>{seatMarkers(assignment).join("")}</span>
                            </span>
                          )}
                        </button>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-64">
                        <p className="font-medium">
                          {displayName ??
                            (seat.is_blocked
                              ? "Blocked seat"
                              : "Available seat")}
                        </p>
                        <p>
                          Seat {number} · {seat.seat_id}
                          {seat.is_accessible ? " · Accessible" : ""}
                        </p>
                        {assignment && (
                          <p>
                            {TIER_STYLES[assignment.contribution_tier].label} ·{" "}
                            {assignment.seat_ids.join(" + ")}
                          </p>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  </Fragment>
                );
              })}
            </div>
          ))}
          <div className="mt-4 flex h-10 items-center justify-center rounded-lg border border-dashed bg-muted/30 text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Back of hall / Entrance
          </div>
        </div>
      </div>
      <p
        aria-live="polite"
        className={cn(
          "flex min-h-4 items-center gap-2 text-xs",
          dropError ? "text-destructive" : "text-muted-foreground",
        )}
      >
        <Grip className="size-3.5" />
        {dropError ??
          (dragId
            ? "Drop onto a seat to move the whole registration. Escape cancels."
            : "Use the seat dialog for keyboard and touch assignment. Scroll horizontally to view the whole hall.")}
      </p>
    </div>
  );
}
