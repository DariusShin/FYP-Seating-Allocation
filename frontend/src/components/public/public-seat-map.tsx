"use client";

import { Fragment } from "react";
import { isAisleGap } from "@/lib/seat-groups";
import { cn } from "@/lib/utils";
import type { PublishedAllocation } from "@/lib/public-allocation-types";

/** No guest names appear on the hall map, including companion names. */
export function PublicSeatMap({
	floor,
	mySeatIds,
}: {
	floor: NonNullable<PublishedAllocation["floor_plan"]>;
	mySeatIds: Set<string>;
}) {
	return (
		<div className="space-y-3">
			<div className="rounded-lg border bg-muted/40 py-3 text-center text-sm font-semibold tracking-widest">
				三宝佛 · 佛台 / Altar
			</div>
			<div className="flex justify-around text-xs text-muted-foreground">
				<span>西单 · West</span>
				<span>中央走道 · Centre aisle</span>
				<span>东单 · East</span>
			</div>
			<div
				className="space-y-1.5"
				aria-label="全厅座位图 / Full hall seating plan"
			>
				{floor.rows.map((row) => (
					<div
						key={row.row_number}
						className="flex items-center gap-0.5 sm:gap-1"
					>
						<span className="w-9 shrink-0 text-center text-[9px] sm:w-12 sm:text-xs">
							西单{row.row_number}
						</span>
						{row.seats.map((seat) => {
                                if (isAisleGap(row.row_number, seat.physical_position)) return (
                                    <Fragment key={seat.seat_id}>
                                        {seat.physical_position === floor.aisle_after_position + 1 && <div aria-hidden="true" className="w-2 sm:w-5 shrink-0" />}
                                        <div aria-hidden="true" className="min-w-0 flex-1" />
                                    </Fragment>
                                );
							const mine = mySeatIds.has(seat.seat_id);
							const blocked = seat.occupancy_status === "BLOCKED";
							const side =
								seat.physical_position <= floor.aisle_after_position
									? "西单"
									: "东单";
							const label = `${side} 第${row.row_number}排 · 实体位置 ${seat.physical_position}${mine ? " · 您的座位" : blocked ? " · 障碍物" : ""}`;
							return (
								<Fragment key={seat.seat_id}>
									{seat.physical_position ===
										floor.aisle_after_position + 1 && (
										<div className="w-2 shrink-0 self-center border-x border-dashed border-muted-foreground/25 sm:w-5" />
									)}
									<div
										title={label}
										aria-label={label}
										className={cn(
											"flex h-7 min-w-0 flex-1 items-center justify-center rounded border text-[9px] font-medium tabular-nums sm:h-8 sm:text-xs lg:h-[clamp(1.5rem,3.4vh,2.75rem)]",
											mine
												? "border-emerald-700 bg-emerald-600 font-bold text-white ring-1 ring-emerald-700"
												: blocked
													? "border-destructive/30 bg-destructive/10 text-destructive"
													: seat.occupancy_status === "OCCUPIED"
														? "border-border bg-muted text-muted-foreground"
														: "border-dashed border-muted-foreground/30 text-muted-foreground",
										)}
									>
										{blocked ? "×" : seat.physical_position}
									</div>
								</Fragment>
							);
						})}
						<span className="w-9 shrink-0 text-center text-[9px] sm:w-12 sm:text-xs">
							东单{row.row_number}
						</span>
					</div>
				))}
			</div>
			<div className="flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-muted-foreground">
				<span className="flex items-center gap-1.5">
					<span className="size-3 rounded bg-emerald-600" />
					您的座位 / Your seats
				</span>
				<span className="flex items-center gap-1.5">
					<span className="size-3 rounded border bg-muted" />
					已安排 / Occupied
				</span>
				<span className="flex items-center gap-1.5">
					<span className="size-3 rounded border border-dashed" />
					空位 / Empty
				</span>
				<span>× 障碍物 / Obstacle</span>
			</div>
			<p className="text-[11px] text-muted-foreground">
				数字为每排从左至右的实体位置（1–{floor.seats_per_row}）。Numbers show
				physical positions from left to right.
			</p>
		</div>
	);
}
