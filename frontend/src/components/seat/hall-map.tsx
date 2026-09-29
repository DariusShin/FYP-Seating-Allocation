"use client";

import { useEffect, useRef } from "react";
import { Accessibility, StickyNote, Star } from "lucide-react";
import type { AllocationResult, TierName } from "@/lib/allocation-types";
import { cn } from "@/lib/utils";
import { seatGroups } from "@/lib/seat-groups";
import { TIER_STYLES } from "./seat-theme";

export interface SeatMarkers {
	hasNote?: boolean;
	elderly?: boolean;
	accessible?: boolean;
}

/** Reuses main's seat-card dimensions, surfaces and tier accents. */
export function HallMap({
	floor,
	names,
	owners = {},
	primaryNames = {},
	tiers = {},
	markers = {},
	selected,
	selectedSeat,
	matches,
	editable = false,
	onSelect,
	onDrop,
	onAllocationDragStart,
	onAllocationDragEnd,
	presentation = false,
}: {
	floor: AllocationResult["floor_plan"];
	names: Record<string, string>;
	owners?: Record<string, string>;
	primaryNames?: Record<string, string | undefined>;
	tiers?: Record<string, TierName>;
	markers?: Record<string, SeatMarkers>;
	selected?: string | null;
	selectedSeat?: string | null;
	matches?: Set<string>;
	editable?: boolean;
	onSelect?: (seat: string) => void;
	onDrop?: (pid: string, seat: string) => void;
	onAllocationDragStart?: (pid: string) => void;
	onAllocationDragEnd?: () => void;
	presentation?: boolean;
}) {
	const container = useRef<HTMLDivElement>(null);
	useEffect(() => {
		if (selected || selectedSeat)
			container.current
				?.querySelector<HTMLElement>(
					selectedSeat
						? `[data-seat~="${CSS.escape(selectedSeat)}"]`
						: `[data-owner="${CSS.escape(selected!)}"]`,
				)
				?.scrollIntoView({
					block: "nearest",
					inline: "center",
					behavior: "smooth",
				});
	}, [selected, selectedSeat]);
	return (
		<div className="hall-scroll" ref={container} aria-label="Hall seating plan">
			<div className="hall-width-frame">
				<div className="paper-hall" data-venue-boundary>
					<div className="hall-stage hall-front">
						<span>{presentation ? "三寶佛" : "三寶佛 / FRONT"}</span>
					</div>
					<div className="hall-sides">
						<span>{presentation ? "西單" : "西單 · WEST"}</span>
						<span>中央通道</span>
						<span>{presentation ? "東單" : "東單 · EAST"}</span>
					</div>
					{!presentation && (
						<div
							className="column-label-row"
							aria-label="Local column numbers: West 1 to 8 and East 1 to 8"
						>
							<span
								className="row-label"
								style={{ gridColumn: 1 }}
								aria-hidden="true"
							/>
							{Array.from({ length: 16 }, (_, index) => index + 1).map(
								(position) => (
									<span
										className="column-label"
										key={position}
										style={{
											gridColumn:
												position +
												1 +
												(position > floor.aisle_after_position ? 1 : 0),
										}}
									>
										{position <= floor.aisle_after_position
											? position
											: position - floor.aisle_after_position}
									</span>
								),
							)}
							<span
								className="row-label"
								style={{ gridColumn: 19 }}
								aria-hidden="true"
							/>
						</div>
					)}
					<div className="hall-rows">
						{floor.rows.map((row) => (
							<div className="paper-row" key={row.row_number}>
								<span className="row-label" style={{ gridColumn: 1 }}>
									西單{row.row_number}
								</span>
								{seatGroups(row.seats, owners).map((group) => {
									const first = group.seats[0];
									const owner = group.owner;
									const paired = group.seats.length === 2;
									const selectedGroup =
										(!!owner && selected === owner) ||
										(!selected &&
											group.seats.some((s) => s.seat_id === selectedSeat));
									const displaySeats = paired ? [first] : group.seats;
									return (
										<div
											key={first.seat_id}
											data-owner={owner}
											data-seat={group.seats.map((s) => s.seat_id).join(" ")}
											data-pair-display={paired ? "merged" : undefined}
											className={cn(
												"seat-slot allocation-seat-group rounded-lg",
												selectedGroup && "ring-2 ring-ring",
												paired && "focus-within:ring-2 focus-within:ring-ring",
												matches && owner && !matches.has(owner) && "opacity-25",
											)}
											style={{
												gridColumn: `${first.physical_position + 1 + (first.physical_position > floor.aisle_after_position ? 1 : 0)} / span ${group.seats.length}`,
											}}
										>
											{displaySeats.map((seat) => {
												const label = paired
													? (primaryNames[owner!] ??
														names[
															group.seats.reduce((a, b) =>
																a.priority_rank < b.priority_rank ? a : b,
															).seat_id
														])
													: names[seat.seat_id];
												const tier =
													(owner ? tiers[owner] : undefined) ?? seat.tier;
												const location = `${seat.side === "LEFT" ? "西單" : "東單"} ${row.row_number} · ${seat.physical_position <= 8 ? seat.physical_position : seat.physical_position - 8}`;
												const marker = owner ? markers[owner] : undefined;
												const markerDescription = [
													marker?.hasNote && "staff note",
													marker?.elderly && "elderly participant",
													marker?.accessible && "accessible seat required",
												]
													.filter(Boolean)
													.join(", ");
												return seat.is_blocked ? (
													<div
														key={seat.seat_id}
														className="structure seat-blocked"
														aria-label={`${location}: structural block`}
														title="Building structure"
													/>
												) : (
													<button
														key={seat.seat_id}
														type="button"
														data-owner={owner}
														data-seat={seat.seat_id}
														className={cn(
															"paper-seat relative flex h-14 min-w-0 flex-1 flex-col items-center justify-center rounded-lg border p-1.5 text-center transition-[background-color,opacity,box-shadow] select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
															owner && tier
																? TIER_STYLES[tier].cell
																: "border-dashed bg-background text-muted-foreground hover:border-primary/40 hover:bg-muted/50",
															editable &&
																owner &&
																"cursor-grab active:cursor-grabbing",
														)}
														draggable={editable && !!owner}
														onDragStart={(e) => {
															if (owner) {
																e.dataTransfer.setData("text/plain", owner);
																e.dataTransfer.effectAllowed = "move";
																onAllocationDragStart?.(owner);
															}
														}}
														onDragEnd={() => onAllocationDragEnd?.()}
														onDragOver={(e) => {
															if (editable) e.preventDefault();
														}}
														onDrop={(e) => {
															e.preventDefault();
															e.stopPropagation();
															if (editable)
																onDrop?.(
																	e.dataTransfer.getData("text/plain"),
																	seat.seat_id,
																);
														}}
														onClick={() => onSelect?.(seat.seat_id)}
														title={
															presentation
																? label || "空位"
																: `${label || "Empty seat"} · ${location}${paired ? " · Emperor pair, two seats" : ""}${markerDescription ? ` · ${markerDescription}` : ""}`
														}
														aria-label={
															presentation
																? label || "空位"
																: `${label || "Empty seat"} · ${location}${paired ? " · Emperor pair, two seats" : ""}${markerDescription ? ` · ${markerDescription}` : ""}`
														}
													>
														{!presentation && owner && (
															<span
																className="seat-marker-row"
																aria-hidden="true"
															>
																{tier && (
																	<span
																		className={cn(
																			"size-1.5 rounded-full",
																			TIER_STYLES[tier].dot,
																		)}
																	/>
																)}
																{marker?.hasNote && (
																	<StickyNote className="size-3" />
																)}
																{marker?.elderly && (
																	<Star className="size-3 text-amber-600" />
																)}
																{marker?.accessible && (
																	<span className="accessibility-marker">
																		<Accessibility className="size-3.5" />
																		<span className="sr-only">
																			Accessible seat required
																		</span>
																	</span>
																)}
															</span>
														)}
														<span className="seat-display-name w-full text-center font-semibold">
															{label ?? ""}
														</span>
													</button>
												);
											})}
										</div>
									);
								})}
								<span className="row-label" style={{ gridColumn: 19 }}>
									東單{row.row_number}
								</span>
							</div>
						))}
					</div>
					<div className="hall-stage hall-back">
						{presentation ? "入口" : "ENTRANCE / BACK · 入口"}
					</div>
				</div>
			</div>
		</div>
	);
}
