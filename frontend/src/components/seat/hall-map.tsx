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
	reviewSeats,
	spotlight,
	pulse = false,
	validTargets,
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
	reviewSeats?: Record<string, "RED" | "YELLOW">;
	spotlight?: Set<string>;
	pulse?: boolean;
	validTargets?: Set<string>;
}) {
	const container = useRef<HTMLDivElement>(null);
	const reviewing = !!reviewSeats;
	useEffect(() => {
		if (selected || selectedSeat)
			container.current
				?.querySelector<HTMLElement>(
					selectedSeat
						? `[data-seat~="${CSS.escape(selectedSeat)}"]`
						: `[data-owner="${CSS.escape(selected!)}"]`,
				)
				?.scrollIntoView({
					block: reviewing ? "center" : "nearest",
					inline: "center",
					behavior: "smooth",
				});
	}, [selected, selectedSeat, reviewing]);
	return (
		<div
			className={`hall-scroll flex min-h-0 flex-1 overflow-auto px-4 py-3 print:overflow-visible print:p-0 ${presentation ? "h-full min-w-0" : ""}`}
			ref={container}
			aria-label="Hall seating plan"
		>
			<div
				className={`hall-width-frame relative mx-auto w-full ${presentation ? "h-full min-w-7xl" : ""} print:h-auto print:w-full`}
			>
				<div
					className={`paper-hall @container static flex w-full min-w-0 flex-col ${presentation ? "h-full min-h-190 min-w-7xl max-w-none" : ""} print:static print:w-full print:min-w-0 ${presentation ? "print:max-w-none print:break-inside-avoid print:font-[Songti_SC,PMingLiU,serif]" : ""}`}
					data-venue-boundary
				>
					<div
						className={`hall-front mb-4 flex h-10 shrink-0 items-center justify-center rounded-lg border border-dashed bg-muted/30 text-xl font-medium uppercase tracking-[0.2em] text-muted-foreground ${presentation ? "mb-0" : ""} ${presentation ? "print:mx-16 print:mb-[7mm] print:h-[8mm] print:rounded-none print:border-[0.3mm] print:border-[#555] print:bg-white print:text-[17pt] print:text-black" : ""}`}
					>
						<span>{presentation ? "三寶佛" : "三寶佛 / FRONT"}</span>
					</div>
					<div
						className={`hall-sides mb-2 grid shrink-0 grid-cols-[1fr_100px_1fr] text-center text-[22px] tracking-widest text-muted-foreground ${presentation ? "print:hidden" : ""}`}
					>
						<span>{presentation ? "西單" : "西單 · WEST"}</span>
						<span className="self-center text-[18px]">中央通道</span>
						<span>{presentation ? "東單" : "東單 · EAST"}</span>
					</div>
					{!presentation && (
						<div
							className="column-label-row mb-1 grid min-h-5.5 grid-cols-[64px_repeat(8,minmax(0,1fr))_40px_repeat(8,minmax(0,1fr))_64px] gap-1.5 text-center"
							aria-label="Local column numbers: West 1 to 8 and East 1 to 8"
						>
							<span
								className="row-label self-center whitespace-nowrap text-center text-base text-muted-foreground"
								style={{ gridColumn: 1 }}
								aria-hidden="true"
							/>
							{Array.from({ length: 16 }, (_, index) => index + 1).map(
								(position) => (
									<span
										className="column-label flex min-w-0 items-center justify-center whitespace-nowrap text-center text-sm font-bold leading-tight text-foreground max-[700px]:text-xs"
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
								className="row-label self-center whitespace-nowrap text-center text-base text-muted-foreground"
								style={{ gridColumn: 19 }}
								aria-hidden="true"
							/>
						</div>
					)}
					<div
						className={`hall-rows flex min-h-0 flex-1 flex-col gap-1.5 ${presentation ? "gap-1" : ""} print:gap-0.75 ${presentation ? "print:gap-[6mm]" : ""}`}
					>
						{floor.rows.map((row) => (
							<div
								className={`paper-row grid h-14 grid-cols-[64px_repeat(8,minmax(0,1fr))_40px_repeat(8,minmax(0,1fr))_64px] gap-1.5 ${presentation ? "h-auto min-h-8 flex-1" : ""} print:h-[3.8vh] print:break-inside-avoid ${presentation ? "print:grid-cols-[16mm_repeat(8,minmax(0,1fr))_10mm_repeat(8,minmax(0,1fr))_16mm] print:gap-0 print:h-[8mm]" : ""}`}
								key={row.row_number}
							>
								<span
									className="row-label self-center whitespace-nowrap text-center text-base text-muted-foreground"
									style={{ gridColumn: 1 }}
								>
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
												`seat-slot allocation-seat-group h-13 min-w-0 rounded-lg print:h-[3.8vh] ${presentation ? "h-full" : ""} ${presentation ? "print:h-[8mm] print:min-h-0 print:rounded-none print:shadow-none" : ""}`,
												selectedGroup && "ring-2 ring-ring",
												reviewSeats && !group.seats.some(s => spotlight?.size ? spotlight.has(s.seat_id) : reviewSeats[s.seat_id]) && "opacity-20",
												reviewSeats && group.seats.some(s => reviewSeats[s.seat_id] === "RED") && "ring-2 ring-red-500",
												reviewSeats && !group.seats.some(s => reviewSeats[s.seat_id] === "RED") && group.seats.some(s => reviewSeats[s.seat_id] === "YELLOW") && "ring-2 ring-amber-500",
												spotlight?.size && group.seats.some(s => spotlight.has(s.seat_id)) && !group.seats.some(s => reviewSeats?.[s.seat_id]) && "ring-2 ring-sky-500",
												pulse && group.seats.some(s => spotlight?.has(s.seat_id)) && "animate-pulse",
												validTargets && group.seats.some(s => validTargets.has(s.seat_id)) && "outline-2 outline-emerald-500",
												validTargets && !group.seats.some(s => validTargets.has(s.seat_id)) && "cursor-not-allowed",
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
														className={`structure h-14 rounded-lg border border-border bg-[repeating-linear-gradient(135deg,transparent,transparent_4px,var(--muted)_4px,var(--muted)_6px)] print:h-[3.8vh] print:rounded-none print:border-[0.25mm] print:border-[#555] print:bg-[repeating-linear-gradient(135deg,#ddd,#ddd_1mm,#fff_1mm,#fff_2mm)] print:[print-color-adjust:exact] ${presentation ? "h-full min-h-0" : ""} ${presentation ? "print:h-[8mm]" : ""}`}
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
															`paper-seat relative flex h-13 w-full min-w-0 flex-1 flex-col items-center justify-center rounded-lg border p-1.5 text-center transition-[background-color,opacity,box-shadow] select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 print:h-[3.8vh] print:rounded-none print:border-[0.25mm] print:border-[#555] print:bg-white print:p-[0_0.5mm] print:text-black print:shadow-none ${presentation ? "h-full shrink-0 rounded-none px-1 py-0.5 shadow-none" : ""} ${presentation ? "print:h-[8mm] print:min-h-0" : ""}`,
															owner && tier
																? TIER_STYLES[tier].cell
																: "border-dashed bg-background text-muted-foreground hover:border-primary/40 hover:bg-muted/50",
													reviewSeats?.[seat.seat_id] === "RED" && "!bg-red-50 !text-red-950 dark:!bg-red-950 dark:!text-red-100",
													reviewSeats?.[seat.seat_id] === "YELLOW" && "!bg-amber-50 !text-amber-950 dark:!bg-amber-950 dark:!text-amber-100",
													validTargets && !validTargets.has(seat.seat_id) && "!cursor-not-allowed",
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
															if (editable && (!validTargets || validTargets.has(seat.seat_id))) e.preventDefault();
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
																className="seat-marker-row absolute right-1.5 top-1 flex min-h-3.5 w-auto items-center justify-end gap-1 text-muted-foreground [&>span:first-child]:mr-px [&>svg]:shrink-0 [&>svg]:stroke-[2.3]"
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
																	<span className="inline-flex items-center justify-center text-[oklch(0.43_0.14_255)] dark:text-[oklch(0.82_0.1_245)]">
																		<Accessibility className="size-3.5" />
																		<span className="sr-only">
																			Accessible seat required
																		</span>
																	</span>
																)}
															</span>
														)}
														<span
															className={`seat-display-name w-full text-center font-semibold ${presentation ? "block text-[clamp(14px,0.95vw,18px)] leading-[1.15] whitespace-nowrap break-keep overflow-hidden wrap-normal text-clip" : "text-[clamp(14px,1.2cqw,16px)] leading-5"} print:text-[15pt] print:font-normal print:leading-[1.05] print:whitespace-normal print:overflow-visible print:wrap-anywhere`}
														>
															{label ?? ""}
														</span>
													</button>
												);
											})}
										</div>
									);
								})}
								<span
									className="row-label self-center whitespace-nowrap text-center text-base text-muted-foreground"
									style={{ gridColumn: 19 }}
								>
									東單{row.row_number}
								</span>
							</div>
						))}
					</div>
					<div className="hall-back mt-4 flex h-10 shrink-0 items-center justify-center rounded-lg border border-dashed bg-muted/30 text-xl font-medium uppercase tracking-[0.2em] text-muted-foreground print:hidden">
						{presentation ? "入口" : "ENTRANCE / BACK · 入口"}
					</div>
				</div>
			</div>
		</div>
	);
}
