"use client";
import { Armchair } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { HallMap } from "./hall-map";
import { MapLoadingOverlay } from "./map-loading-overlay";
import { SeatDashboard } from "./seat-dashboard";
import type { Workspace } from "@/lib/workspace";
import type { AllocationResult } from "@/lib/allocation-types";

export function GenerateDraft({
	floor,
	registrations,
	autoStart = false,
	generationMode = "INITIAL",
	eventId,
	entryAction = "new",
	showGenerateButton = true,
}: {
	eventId: string;
	entryAction?: "new" | "load";
	showGenerateButton?: boolean;
	floor: AllocationResult["floor_plan"];
	registrations: number;
	autoStart?: boolean;
	generationMode?: "INITIAL" | "REGENERATE_DRAFT";
}) {
	const [phase, setPhase] = useState<
		"idle" | "generating" | "loading-workspace" | "ready" | "error"
	>(
		autoStart
			? entryAction === "load"
				? "loading-workspace"
				: "generating"
			: "idle",
	);
	const [workspace, setWorkspace] = useState<Workspace | null>(null);
	const draftCreated = useRef(false);
	const generatedPlanId = useRef<string | null>(null);
	const [hasSavedDraft, setHasSavedDraft] = useState(entryAction === "load");
	const inFlight = useRef(false);
	const busy = phase === "generating" || phase === "loading-workspace";
	const [error, setError] = useState("");
	const started = useRef(false);
	const generate = useCallback(async () => {
		if (inFlight.current) return;
		inFlight.current = true;
		setPhase(
			draftCreated.current || entryAction === "load"
				? "loading-workspace"
				: "generating",
		);
		setError("");
		try {
			if (entryAction === "new" && !draftCreated.current) {
				const response = await fetch(
					`/api/solve?event_id=${encodeURIComponent(eventId)}`,
					{
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify({
							generation_mode: generationMode,
							preference_profile_version: "ranked-v1",
							preferences: [
								"contribution_seat",
								"activeness",
								"category_zone",
							].map((key) => ({ key, enabled: true })),
						}),
					},
				);
				const value = await response.json();
				if (!response.ok || value.status !== "success")
					throw new Error(
						value.error?.message ??
							"Unable to generate a seating plan. Please try again.",
					);
				generatedPlanId.current = value.plan_version_id;
				draftCreated.current = true;
				setHasSavedDraft(true);
			}
			setPhase("loading-workspace");
			const response = await fetch(
				`/api/workspace?event_id=${encodeURIComponent(eventId)}`,
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						command: "workspace_open",
						...(generatedPlanId.current
							? { plan_version_id: generatedPlanId.current }
							: {}),
					}),
				},
			);
			const value = await response.json();
			if (!response.ok || !value?.base || !value?.state)
				throw new Error(
					value?.error?.message ??
						"Unable to load the saved draft. Please try again.",
				);
			setWorkspace(value);
			setPhase("ready");
		} catch (e) {
			setError(e instanceof Error ? e.message : "Generation failed");
			setPhase("error");
		} finally {
			inFlight.current = false;
		}
	}, [generationMode, eventId, entryAction]);
	useEffect(() => {
		if (!autoStart) return;
		// Scheduling lets Strict Mode clean up its first effect before a POST begins.
		const timer = window.setTimeout(() => {
			if (started.current) return;
			started.current = true;
			void generate();
		}, 0);
		return () => window.clearTimeout(timer);
	}, [autoStart, generate]);
	if (phase === "ready" && workspace)
		return (
			<>
				<p className="sr-only" role="status">
					Seating draft ready.
				</p>
				<SeatDashboard
					initialResult={workspace.base}
					initialWorkspace={workspace}
				/>
			</>
		);
	return (
		<main className="seat-workspace">
			<header className="workspace-header">
				<Link
					href="/event"
					className="text-sm text-muted-foreground hover:text-foreground"
				>
					← Events
				</Link>
				<div className="brand-mark">
					<Armchair size={20} />
				</div>
				<div>
					<h1>PJKIT · Seating workspace</h1>
					<p>2026 梁皇寶懺大法會</p>
				</div>
			</header>
			<div className="context-bar">
				<span className="mode-pill">
					{busy
						? "Preparing seating"
						: phase === "error"
							? "Needs attention"
							: "Draft generation"}
				</span>
				<p>
					{registrations} registrations ready ·{" "}
					{busy
						? "Preparing the seating map for this event…"
						: phase === "error"
							? "Review the message below to continue."
							: "Generate a private draft to begin."}
				</p>
				{phase === "idle" && showGenerateButton && (
					<Button onClick={() => void generate()}>Generate draft</Button>
				)}
			</div>
			<section className="workspace-body" aria-label="Seating map">
				<div className="map-column">
					<div className="relative min-h-[60vh] overflow-hidden rounded-lg">
						<div
							className="pointer-events-none opacity-40"
							inert
							aria-busy={busy}
						>
							<HallMap floor={floor} names={{}} />
						</div>
						{phase !== "idle" && (
							<MapLoadingOverlay
								phase={
									phase === "error"
										? "error"
										: phase === "loading-workspace"
											? "loading-workspace"
											: "generating"
								}
								error={error}
								onRetry={() => void generate()}
								draftCreated={hasSavedDraft}
							/>
						)}
					</div>
					<footer className="map-footer">
						三寶佛 · 西單 · 東單 ·{" "}
						{floor.total_seats -
							floor.rows.flatMap((r) => r.seats).filter((s) => s.is_blocked)
								.length}{" "}
						assignable seats
					</footer>
				</div>
			</section>
		</main>
	);
}
