"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
	buildSkeletonPlan,
	placementAt,
	SKELETON_FILL_MS,
	SKELETON_FINISH_MS,
	type SkeletonCounts,
	type SkeletonStep,
} from "@/lib/skeleton-schedule";
import type { AllocationResult, TierName } from "./types";
import { HallMap } from "./hall-map";

/** Drives a quick staged preview, then smoothly finishes under the opening
 * overlay when the result arrives. Each attempt has an independent timeline.
 * Reduced-motion users skip straight to the completed skeleton. */
export function useSkeletonProgress(
	total: number,
	complete: boolean,
	attempt: number | null,
	durationMs = SKELETON_FILL_MS,
) {
	const [progress, setProgress] = useState({ attempt, placed: 0 });
	const latest = useRef(progress);
	useEffect(() => {
		if (attempt === null || !total) return;
		const from =
			complete && latest.current.attempt === attempt
				? Math.min(latest.current.placed, total)
				: 0;
		const duration = complete ? SKELETON_FINISH_MS : durationMs;
		const start = performance.now();
		let frame = 0;
		let stopped = false;
		const tick = () => {
			if (stopped) return;
			if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
				latest.current = { attempt, placed: total };
				setProgress(latest.current);
				return;
			}
			const next =
				from + placementAt(performance.now() - start, total - from, duration);
			if (latest.current.attempt !== attempt || latest.current.placed !== next) {
				latest.current = { attempt, placed: next };
				setProgress(latest.current);
			}
			if (next < total) frame = requestAnimationFrame(tick);
		};
		frame = requestAnimationFrame(tick);
		return () => {
			stopped = true;
			cancelAnimationFrame(frame);
		};
	}, [total, complete, attempt, durationMs]);
	return attempt !== null && progress.attempt === attempt
		? Math.min(progress.placed, total)
		: 0;
}

export function useSkeletonPlan(
	floor: AllocationResult["floor_plan"],
	counts: SkeletonCounts | null,
	approvedPairs?: readonly number[][],
) {
	return useMemo(
		() =>
			counts
				? buildSkeletonPlan(floor, counts, approvedPairs ?? floor.approved_pairs)
				: [],
		[floor, counts, approvedPairs],
	);
}

export function skeletonProjection(steps: SkeletonStep[], placed: number) {
	const owners: Record<string, string> = {};
	const tiers: Record<string, TierName> = {};
	for (const step of steps.slice(0, placed)) {
		tiers[step.owner] = step.tier;
		for (const seat of step.seat_ids) {
			owners[seat] = step.owner;
			tiers[seat] = step.tier;
		}
	}
	const spotlight = new Set(placed > 0 ? steps[placed - 1]?.seat_ids ?? [] : []);
	return { owners, tiers, spotlight };
}

/** Slim progress strip replacing the old centred loading card. */
export function GenerationStatus({
	placed,
	total,
	complete,
	failed,
}: {
	placed: number;
	total: number;
	complete: boolean;
	failed?: boolean;
}) {
	const components = total ? Math.round((placed / total) * 100) : 100;
	return (
		<div
			className="border-b bg-background/95 px-5.5 py-2 text-sm text-muted-foreground backdrop-blur max-[700px]:px-3"
			aria-live="off"
		>
			{failed ? (
				"Generation needs attention."
			) : complete ? (
				<span role="status">
					Solver finished — opening the assigned seating map…
				</span>
			) : (
				<span className="flex items-center gap-2">
					<span
						aria-hidden="true"
						className="size-2 shrink-0 animate-pulse rounded-full bg-primary"
					/>
					Solver is running · Seating preview:{" "}
					{total
						? `${Math.min(placed, total)}/${total} registration units`
						: "preparing…"}
					<span aria-hidden="true" className="sr-only">
						{components}% sketched
					</span>
				</span>
			)}
		</div>
	);
}

export function SkeletonSeatingMap({
	floor,
	steps,
	placed,
	complete,
}: {
	floor: AllocationResult["floor_plan"];
	steps: SkeletonStep[];
	placed: number;
	complete: boolean;
}) {
	const { owners, tiers, spotlight } = useMemo(
		() => skeletonProjection(steps, placed),
		[steps, placed],
	);
	return (
		<div className="relative flex min-h-0 flex-1 flex-col" inert aria-busy="true">
			<HallMap
				floor={floor}
				names={{}}
				owners={owners}
				tiers={tiers}
				spotlight={spotlight}
				pulse={!complete}
				skeleton
			/>
		</div>
	);
}
