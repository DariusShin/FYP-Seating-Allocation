"use client";

import { Fragment } from "react";

import { cn } from "@/lib/utils";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";

import { seatNumber, TIER_STYLES } from "../seat/seat-theme";

/**
 * Read-only floor plan for the public seat view. Unlike the admin SeatMap it
 * hides every other guest's identity: occupied seats render as neutral cells
 * and only the signed-in participant's seat(s) are coloured, ringed, and
 * labelled with a name.
 */
export function PublicSeatMap({
  result,
  mySeatIds,
  assignment,
}: {
  result: AllocationResult;
  mySeatIds: Set<string>;
  assignment: Assignment | null;
}) {
  const { rows, aisle_after_position, seats_per_row } = result.floor_plan;
  const tierStyle = assignment ? TIER_STYLES[assignment.contribution_tier] : null;

  return (
    <div className="space-y-1.5">
      <div className="mb-3 rounded-lg border border-amber-500/40 bg-gradient-to-r from-amber-100 via-amber-50 to-amber-100 py-2 text-center text-xs font-semibold tracking-[0.3em] text-amber-900 dark:from-amber-400/20 dark:via-amber-400/10 dark:to-amber-400/20 dark:text-amber-200">
        ALTAR / STAGE
      </div>

      {rows.map((row) => (
        <div key={row.row_number} className="flex items-stretch gap-1">
          <div className="flex w-9 shrink-0 flex-col items-center justify-center rounded-md bg-muted/50 text-[10px] font-semibold text-muted-foreground">
            R{String(row.row_number).padStart(2, "0")}
          </div>
          {row.seats.map((seat) => {
            const mine = mySeatIds.has(seat.seat_id);
            const number = seatNumber(
              row.row_number,
              seat.priority_rank,
              seats_per_row,
            );
            return (
              <Fragment key={seat.seat_id}>
                {seat.physical_position === aisle_after_position + 1 && (
                  <div className="w-4 shrink-0 border-x border-dashed border-muted-foreground/25 sm:w-7" />
                )}
                <div
                  className={cn(
                    "flex h-11 min-w-0 flex-1 flex-col justify-between overflow-hidden rounded-md border px-1 py-0.5 sm:h-13",
                    mine && tierStyle
                      ? cn(
                          tierStyle.cell,
                          "animate-pulse ring-2 ring-ring ring-offset-1 ring-offset-background",
                        )
                      : seat.occupancy_status === "BLOCKED"
                        ? "border-destructive/40 bg-destructive/10 text-destructive"
                        : seat.occupancy_status === "OCCUPIED"
                          ? "border-border bg-muted/60 text-muted-foreground"
                          : "border-dashed border-muted-foreground/30 bg-muted/30 text-muted-foreground/70",
                  )}
                >
                  <span className="text-[9px] leading-none opacity-80">
                    {number}
                  </span>
                  <span className="truncate text-[10px] font-medium leading-tight">
                    {mine
                      ? (seat.display_name ?? "")
                      : seat.occupancy_status === "BLOCKED"
                        ? "✕"
                        : ""}
                  </span>
                </div>
              </Fragment>
            );
          })}
        </div>
      ))}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-3 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span
            className={cn(
              "size-3 rounded-sm border ring-1 ring-ring",
              tierStyle ? tierStyle.cell.split(" hover:")[0] : "bg-muted",
            )}
          />
          Your seat
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm border bg-muted/60" />
          Other guests
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm border border-dashed border-muted-foreground/40 bg-muted/30" />
          Empty
        </span>
        <span className="flex items-center gap-1.5">
          <span className="flex size-3 items-center justify-center rounded-sm border border-destructive/40 bg-destructive/10 text-[8px] text-destructive">
            ✕
          </span>
          Blocked
        </span>
      </div>
    </div>
  );
}
