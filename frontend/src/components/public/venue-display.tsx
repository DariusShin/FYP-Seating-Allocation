"use client";
import { useEffect, useRef, useState } from "react";
import type { AllocationResult } from "@/lib/allocation-types";
import { HallMap } from "@/components/seat/hall-map";
import { chineseVenueName } from "@/lib/venue-names";
import { Button } from "@/components/ui/button";
import styles from "./venue-display.module.css";
type Venue = {
	status: string;
	floor_plan?: AllocationResult["floor_plan"];
	published_at?: string;
	pair_display?: Record<string, { primary_name: string }>;
};
export function VenueDisplay() {
	const [value, setValue] = useState<Venue | null>(null);
	const [error, setError] = useState("");
	const root = useRef<HTMLDivElement>(null);
	useEffect(() => {
		let active = true;
		let pending = false;
		async function load() {
			if (pending) return;
			pending = true;
			try {
				const r = await fetch("/api/venue", {
					cache: "no-store",
					signal: AbortSignal.timeout(10000),
				});
				if (!r.ok)
					throw Error(
						"Venue display unavailable. An online connection is required.",
					);
				const v = await r.json();
				if (active && navigator.onLine) {
					setValue(v);
					setError("");
				}
			} catch (e) {
				if (active) {
					setValue(null);
					setError(String(e));
				}
			} finally {
				pending = false;
			}
		}
		const offline = () => {
			setValue(null);
			setError("Venue display unavailable. An online connection is required.");
		};
		window.addEventListener("offline", offline);
		void load();
		const id = setInterval(load, 10000);
		return () => {
			active = false;
			clearInterval(id);
			window.removeEventListener("offline", offline);
		};
	}, []);
	const names: Record<string, string> = {};
	const owners: Record<string, string> = {};
	value?.floor_plan?.rows.forEach((r) =>
		r.seats.forEach((s) => {
			if (s.participant_id) names[s.seat_id] = chineseVenueName(s.display_name);
			if (s.participant_id) owners[s.seat_id] = s.participant_id;
		}),
	);
	return (
		<div className={`venue-page ${styles.screen}`} ref={root}>
			<div className="venue-controls">
				<span>
					PJKIT · Published seating{" "}
					{value?.published_at
						? `· ${new Date(value.published_at).toLocaleString()}`
						: ""}
				</span>
				<div className="flex gap-2">
					<Button
						variant="outline"
						size="sm"
						disabled={!value?.floor_plan}
						onClick={() => window.print()}
					>
						Print / Save PDF
					</Button>
					<Button
						size="sm"
						onClick={() =>
							root.current
								?.requestFullscreen()
								.catch(() =>
									setError("Full screen unavailable in this browser."),
								)
						}
					>
						Full screen
					</Button>
				</div>
			</div>
			{error && (
				<p role="alert" className="workspace-banner">
					{error}
				</p>
			)}
			{value?.floor_plan ? (
				<>
					<h1 className="venue-event-title">梁皇寶懺大法會功德主排位</h1>
					<HallMap
						presentation
						floor={value.floor_plan}
						names={names}
						owners={owners}
						primaryNames={Object.fromEntries(
							Object.entries(value.pair_display ?? {}).map(([id, p]) => [
								id,
								chineseVenueName(p.primary_name) || undefined,
							]),
						)}
					/>
				</>
			) : (
				<p className="p-8">
					{error
						? "請連線以查看已公布的座位表。"
						: value
							? "No published seating plan yet."
							: "Loading published seating…"}
				</p>
			)}
		</div>
	);
}
