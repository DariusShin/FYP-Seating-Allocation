"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import {
	LoaderCircle,
	Undo2,
	Redo2,
	ArrowLeft,
	ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogDescription,
} from "@/components/ui/dialog";
import { HallMap } from "./hall-map";
import { MapLoadingOverlay } from "./map-loading-overlay";
import { reviewMove, type WorkingState, type Workspace } from "@/lib/workspace";
import { groupFindings, type Finding, type Review } from "@/lib/verification";

export function VerificationScreen({
	initial,
	onExit,
	onPublished,
}: {
	initial: Workspace;
	onExit: (workspace: Workspace, seat: string | null) => void;
	onPublished: (workspace: Workspace) => void;
}) {
	const [state, setState] = useState(initial.state);
	const [review, setReview] = useState<Review | null>(null);
	const [checkedState, setCheckedState] = useState<WorkingState | null>(null);
	const [phase, setPhase] = useState<"entry" | "publish" | null>("entry");
	const [working, setWorking] = useState(false);
	const [error, setError] = useState("");
	const [stale, setStale] = useState(false);
	const [filter, setFilter] = useState("All");
	const [showHandled, setShowHandled] = useState(false);
	const [expanded, setExpanded] = useState<Record<string, boolean>>({});
	const [selected, setSelected] = useState<string | null>(null);
	const [selectedSeat, setSelectedSeat] = useState<string | null>(null);
	const [pulse, setPulse] = useState(false);
	const [dragging, setDragging] = useState<string | null>(null);
	const [moveActor, setMoveActor] = useState("");
	const [destination, setDestination] = useState("");
	const [notes, setNotes] = useState<Record<string, string>>({});
	const [preview, setPreview] = useState<ReturnType<typeof reviewMove> | null>(
		null,
	);
	const [confirmPublish, setConfirmPublish] = useState(false);
	const [history, setHistory] = useState<{
		past: WorkingState[];
		future: WorkingState[];
	}>({ past: [], future: [] });
	const saved = useRef(initial);
	const latest = useRef(initial.state);
	const queue = useRef<Promise<unknown>>(Promise.resolve());
	const sequence = useRef(0);
	const mounted = useRef(true);
	const dirty = state !== checkedState;
	const base = initial.base;
	const findings = review?.findings ?? [];
	const summary = review?.summary;
	const selectedFinding = findings.find((f) => f.finding_id === selected);
	const groups = groupFindings(
		findings.filter(
			(f) =>
				(showHandled || f.status === "OPEN") &&
				(filter === "All" || f.severity === filter || f.rule_id === filter),
		),
	);
	const reviewSeats = useMemo(() => {
		const result: Record<string, "RED" | "YELLOW"> = {};
		for (const f of review?.findings ?? [])
			if (f.status === "OPEN")
				for (const s of f.involved_seat_ids)
					if (result[s] !== "RED") result[s] = f.severity;
		return result;
	}, [review]);
	const spotlight = new Set(
		selectedFinding
			? [
					...selectedFinding.involved_seat_ids,
					...selectedFinding.resolution_hint.swap_candidates.flatMap(
						(p) => p.seat_ids,
					),
				]
			: [],
	);
	const cells = base.floor_plan.rows.flatMap((r) => r.seats);
	const validTargets = useMemo(() => {
		if (!dragging) return undefined;
		return new Set(
			base.floor_plan.rows
				.flatMap((r) => r.seats)
				.filter((s) => {
					try {
						reviewMove(state, base, dragging, s.seat_id);
						return true;
					} catch {
						return false;
					}
				})
				.map((s) => s.seat_id),
		);
	}, [dragging, state, base]);
	const owners: Record<string, string> = {},
		names: Record<string, string> = {};
	for (const [pid, item] of Object.entries(state.items))
		for (const sid of item.seat_ids) {
			owners[sid] = pid;
			names[sid] = item.display_names[0];
		}
	async function request(command: string, extra: Record<string, unknown> = {}) {
		const response = await fetch("/api/workspace", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				command,
				plan_version_id: saved.current.base.plan_version_id,
				revision: saved.current.revision,
				...extra,
			}),
		});
		const value = await response.json();
		if (!response.ok || value.status === "error") {
			if (value.error?.code === "STALE_BASELINE") setStale(true);
			throw Error(value.error?.message ?? "Unable to update safeguard review.");
		}
		return value;
	}
	function enqueue<T>(task: () => Promise<T>): Promise<T> {
		const next = queue.current.then(task);
		queue.current = next.catch(() => undefined);
		return next;
	}
	async function persist(snapshot: WorkingState) {
		if (JSON.stringify(snapshot) !== JSON.stringify(saved.current.state))
			saved.current = await request("workspace_save", { state: snapshot });
	}
	async function refresh(snapshot: WorkingState, token: number) {
		// Feedback validates the unsaved payload; the subsequent saved check is the
		// recoverable review snapshot. Both use the same serialized revision stream.
		if (JSON.stringify(snapshot) !== JSON.stringify(saved.current.state))
			await request("workspace_check", { state: snapshot });
		await persist(snapshot);
		const result: Review = await request("workspace_check");
		saved.current = { ...saved.current, review: result };
		if (mounted.current && token === sequence.current) {
			setReview(result);
			setCheckedState(snapshot);
			setError("");
		}
	}
	useEffect(() => {
		mounted.current = true;
		let active = true;
		void enqueue(async () => {
			const result: Review = await request("workspace_check");
			saved.current = { ...saved.current, review: result };
			if (active) {
				setReview(result);
				setCheckedState(initial.state);
				setPhase(null);
			}
		}).catch((e) => {
			if (active) {
				setError(String(e));
				setPhase(null);
			}
		});
		return () => {
			active = false;
			mounted.current = false;
		};
		// This component is a session bound to one opened workspace.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);
	useEffect(() => {
		if (!review || state === checkedState || stale) return;
		const token = sequence.current;
		const timer = window.setTimeout(() => {
			setWorking(true);
			void enqueue(() => refresh(state, token))
				.catch((e) => setError(String(e)))
				.finally(() => setWorking(false));
		}, 900);
		return () => window.clearTimeout(timer);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [state, stale, review, checkedState]);
	useEffect(() => {
		if (!pulse) return;
		const timer = window.setTimeout(() => setPulse(false), 2000);
		return () => window.clearTimeout(timer);
	}, [pulse, selected]);
	useEffect(() => {
		if (!selected) return;
		document
			.getElementById(`finding-${selected}`)
			?.scrollIntoView({ block: "nearest", behavior: "smooth" });
	}, [selected]);
	useEffect(() => {
		if (!dirty) return;
		const warn = (event: BeforeUnloadEvent) => {
			event.preventDefault();
		};
		window.addEventListener("beforeunload", warn);
		return () => window.removeEventListener("beforeunload", warn);
	}, [dirty]);
	function update(next: WorkingState) {
		sequence.current++;
		latest.current = next;
		setState(next);
		setError("");
	}
	function commit(next: WorkingState) {
		setHistory((h) => ({ past: [...h.past.slice(-49), state], future: [] }));
		update(next);
	}
	function move(pid: string, sid: string) {
		if (stale || phase || (working && confirmPublish)) return;
		setDragging(null);
		try {
			const next = reviewMove(state, base, pid, sid);
			if (next.chain) setPreview(next);
			else commit(next.state);
		} catch (e) {
			setError(String(e));
		}
	}
	function locate(f: Finding) {
		setSelected(f.finding_id);
		setPulse(true);
		setMoveActor(f.resolution_hint.actor_participant_id);
		setSelectedSeat(
			f.participants.find(
				(p) => p.participant_id === f.resolution_hint.actor_participant_id,
			)?.seat_ids[0] ?? f.involved_seat_ids[0],
		);
	}
	async function acknowledge(f: Finding) {
		setWorking(true);
		try {
			await enqueue(async () => {
				await persist(latest.current);
				const result: Review = await request("workspace_ack", {
					finding_id: f.finding_id,
					status: f.status === "ACKED" ? "OPEN" : "ACKED",
					note:
						notes[f.finding_id] ??
						review?.acknowledgements?.[f.finding_id]?.note ??
						"",
				});
				saved.current = { ...saved.current, review: result };
				setReview(result);
			});
		} catch (e) {
			setError(String(e));
		} finally {
			setWorking(false);
		}
	}
	async function exit() {
		setWorking(true);
		try {
			await enqueue(async () => {
				await persist(latest.current);
				onExit(saved.current, selectedSeat);
			});
		} catch (e) {
			setError(String(e));
			setWorking(false);
		}
	}
	async function publish() {
		setPhase("publish");
		setConfirmPublish(false);
		try {
			await enqueue(async () => {
				await persist(latest.current);
				const value: Workspace = await request("workspace_publish");
				onPublished(value);
			});
		} catch (e) {
			setError(String(e));
			setPhase(null);
		}
	}
	const canPublish =
		!!summary &&
		summary.open_blocking === 0 &&
		!dirty &&
		!working &&
		!stale &&
		!error;
	const handled = (summary?.acked ?? 0) + (summary?.resolved ?? 0);
	const total =
		handled + (summary?.open_blocking ?? 0) + (summary?.open_advisory ?? 0);
	return (
		<main className="relative flex h-dvh flex-col bg-background text-foreground">
			<header className="flex flex-wrap items-center gap-3 border-b p-4">
				<ShieldCheck className="size-6" />
				<h1 className="font-semibold">Safeguard verification</h1>
				<span className="rounded border px-2 py-1 text-sm">Verification</span>
				<span role="status" className="text-sm text-muted-foreground">
					{dirty
						? "Saving and checking changes…"
						: "Saved · public seating unchanged"}
				</span>
				<Button
					variant="outline"
					className="ml-auto"
					disabled={working || !!phase}
					onClick={exit}
				>
					<ArrowLeft /> Back to editing
				</Button>
			</header>
			{error && (
				<div
					role="alert"
					className="flex items-center gap-3 border-b bg-destructive/10 p-3 text-sm"
				>
					<span>{error}</span>
					{stale ? (
						<Button variant="outline" onClick={() => window.location.reload()}>
							Reload latest draft
						</Button>
					) : (
						<Button
							variant="outline"
							disabled={working}
							onClick={() => {
								setWorking(true);
								void enqueue(() => refresh(latest.current, sequence.current))
									.catch((e) => setError(String(e)))
									.finally(() => setWorking(false));
							}}
						>
							Retry check
						</Button>
					)}
					{!stale && (
						<Button variant="outline" disabled={working} onClick={exit}>
							Back to editing
						</Button>
					)}
				</div>
			)}
			<div className="flex min-h-0 flex-1 max-md:flex-col">
				<section
					className="flex min-h-0 min-w-0 flex-1 flex-col"
					aria-label="Verification map"
				>
					<div className="flex flex-wrap items-center gap-2 border-b p-2">
						<Button
							variant="ghost"
							size="icon-sm"
							aria-label="Undo"
							disabled={!history.past.length || stale || !!phase}
							onClick={() => {
								const next = history.past.at(-1)!;
								setHistory((h) => ({
									past: h.past.slice(0, -1),
									future: [state, ...h.future],
								}));
								update(next);
							}}
						>
							<Undo2 />
						</Button>
						<Button
							variant="ghost"
							size="icon-sm"
							aria-label="Redo"
							disabled={!history.future.length || stale || !!phase}
							onClick={() => {
								const next = history.future[0];
								setHistory((h) => ({
									past: [...h.past, state],
									future: h.future.slice(1),
								}));
								update(next);
							}}
						>
							<Redo2 />
						</Button>
						<select
							aria-label="Registration to move"
							className="max-w-48 rounded border p-2 text-sm"
							value={moveActor}
							onChange={(e) => setMoveActor(e.target.value)}
						>
							<option value="">Choose registration</option>
							{state.participants
								.filter((p) => state.items[p.participant_id].seat_ids.length)
								.map((p) => (
									<option key={p.participant_id} value={p.participant_id}>
										{state.items[p.participant_id].display_names[0]}
									</option>
								))}
						</select>
						<select
							aria-label="Review move destination"
							className="rounded border p-2 text-sm"
							value={destination}
							onChange={(e) => setDestination(e.target.value)}
						>
							<option value="">Choose seat</option>
							{cells
								.filter((s) => !s.is_blocked)
								.map((s) => (
									<option key={s.seat_id} value={s.seat_id}>
										{s.seat_id}
									</option>
								))}
						</select>
						<Button
							size="sm"
							variant="outline"
							disabled={!moveActor || !destination || stale || !!phase}
							onClick={() => move(moveActor, destination)}
						>
							Move / swap
						</Button>
						<span className="text-xs text-muted-foreground">
							Drag to fix · green outlines show valid destinations
						</span>
					</div>
					<HallMap
						floor={base.floor_plan}
						names={names}
						owners={owners}
						tiers={Object.fromEntries(
							state.participants.map((p) => [
								p.participant_id,
								p.contribution_tier,
							]),
						)}
						primaryNames={Object.fromEntries(
							Object.entries(state.items).map(([pid, item]) => [
								pid,
								item.display_names[0],
							]),
						)}
						reviewSeats={reviewSeats}
						spotlight={spotlight}
						pulse={pulse}
						selectedSeat={selectedSeat}
						validTargets={validTargets}
						editable={!stale && !phase}
						onDrop={move}
						onAllocationDragStart={setDragging}
						onAllocationDragEnd={() => setDragging(null)}
						onSelect={(sid) => {
							const f = findings.find(
								(f) => f.status === "OPEN" && f.involved_seat_ids.includes(sid),
							);
							if (f) {
								setFilter("All");
								locate(f);
							} else {
								setSelectedSeat(sid);
								if (owners[sid]) setMoveActor(owners[sid]);
							}
						}}
					/>
				</section>
				<aside
					aria-label="Review issues"
					className="flex w-96 shrink-0 flex-col border-l max-md:h-2/5 max-md:w-full max-md:border-t"
				>
					<div className="sticky top-0 z-10 space-y-3 border-b bg-background p-4">
						<div className="flex items-center justify-between">
							<h2 className="font-semibold">Review issues</h2>
							{(dirty || working) && (
								<LoaderCircle
									aria-label="Checking safeguards"
									className="size-4 animate-spin"
								/>
							)}
						</div>
						<p
							className={`text-sm ${dirty || working ? "opacity-50" : ""}`}
							role="status"
						>
							{handled} of {total} handled · {summary?.open_blocking ?? "…"}{" "}
							blocking
						</p>
						<div
							className="flex h-2 overflow-hidden rounded bg-muted"
							aria-label={`${handled} of ${total} findings handled`}
						>
							{summary && total > 0 && (
								<>
									<span
										className="bg-emerald-500"
										style={{ width: `${(summary.resolved / total) * 100}%` }}
									/>
									<span
										className="bg-sky-500"
										style={{ width: `${(summary.acked / total) * 100}%` }}
									/>
									<span
										className="bg-red-500"
										style={{
											width: `${(summary.open_blocking / total) * 100}%`,
										}}
									/>
									<span
										className="bg-amber-400"
										style={{
											width: `${(summary.open_advisory / total) * 100}%`,
										}}
									/>
								</>
							)}
						</div>
						<div className="flex flex-wrap gap-1">
							{["All", "RED", "YELLOW", "C12", "C13", "C15", "C16"].map((v) => (
								<Button
									key={v}
									size="sm"
									variant={filter === v ? "secondary" : "ghost"}
									aria-pressed={filter === v}
									onClick={() => setFilter(v)}
								>
									{v === "RED" ? "Blocking" : v === "YELLOW" ? "Advisory" : v}
								</Button>
							))}
						</div>
						{!!summary?.acked && (
							<label className="flex gap-2 text-xs">
								<input
									type="checkbox"
									checked={showHandled}
									onChange={(e) => setShowHandled(e.target.checked)}
								/>{" "}
								Show acknowledged issues to revoke
							</label>
						)}
						<Button
							className="w-full"
							disabled={!canPublish}
							onClick={() => setConfirmPublish(true)}
						>
							Publish seating plan
						</Button>
					</div>
					<div className="min-h-0 flex-1 space-y-3 overflow-auto p-4">
						{summary?.open_blocking === 0 && !dirty && (
							<div
								role="status"
								className="rounded-lg border border-emerald-600 bg-emerald-50 p-3 text-sm text-emerald-950"
							>
								All blocking safeguards handled.{" "}
								{summary.open_advisory
									? "Packing advisories are optional; you can publish."
									: "Ready to publish."}
							</div>
						)}
						{groups.map(([actor, issues]) => (
							<article
								key={actor}
								className={`rounded-lg border-l-4 border p-3 ${issues.some((f) => f.severity === "RED") ? "border-l-red-500" : "border-l-amber-500"}`}
							>
								<h3 className="font-semibold">
									{
										issues[0].participants.find(
											(p) => p.participant_id === actor,
										)?.display_name
									}
								</h3>
								<p className="mb-2 text-xs text-muted-foreground">
									{issues.length} related{" "}
									{issues.length === 1 ? "finding" : "findings"}
								</p>
								{(expanded[actor]
									? issues
									: [issues.find((f) => f.finding_id === selected) ?? issues[0]]
								).map((f) => (
									<section
										id={`finding-${f.finding_id}`}
										key={f.finding_id}
										className={`space-y-2 border-t py-3 text-sm ${selected === f.finding_id ? "rounded bg-accent px-2 ring-1 ring-ring" : ""}`}
									>
										<button
											className="w-full text-left font-medium"
											onClick={() => locate(f)}
										>
											{f.rule_id} ·{" "}
											{f.severity === "RED" ? "Blocking" : "Advisory"}{" "}
											{f.is_new && (
												<span className="rounded bg-primary px-1 text-primary-foreground">
													New
												</span>
											)}{" "}
											{f.status === "ACKED" && "· Acknowledged"}
										</button>
										{f.participants.map((p) => (
											<p key={p.participant_id}>
												{p.display_name} · RM{" "}
												{p.contribution_amount_rm.toLocaleString()} · row{" "}
												{p.row_number}
											</p>
										))}
										<p className="text-muted-foreground">
											{f.resolution_hint.message}
										</p>
										<details>
											<summary className="cursor-pointer text-xs">
												Registration details and optional note
											</summary>
											{f.participants.map((p) => (
												<p className="my-1 text-xs" key={p.participant_id}>
													{p.participant_id} · {p.contribution_tier} ·{" "}
													{p.seat_ids.join(", ")}
												</p>
											))}
											<textarea
												maxLength={2000}
												aria-label={`Optional note for ${f.finding_id}`}
												placeholder="Optional staff note"
												className="mt-2 w-full rounded border p-2"
												value={
													notes[f.finding_id] ??
													review?.acknowledgements?.[f.finding_id]?.note ??
													""
												}
												onChange={(e) =>
													setNotes((n) => ({
														...n,
														[f.finding_id]: e.target.value,
													}))
												}
											/>
										</details>
										<div className="flex gap-2">
											<Button
												variant="outline"
												size="sm"
												onClick={() => locate(f)}
											>
												Locate
											</Button>
											<Button
												size="sm"
												variant="secondary"
												disabled={dirty || working || stale}
												onClick={() => acknowledge(f)}
											>
												{f.status === "ACKED"
													? "Revoke"
													: f.severity === "RED"
														? "Override"
														: "Acknowledge"}
											</Button>
										</div>
									</section>
								))}
								{issues.length > 1 && (
									<Button
										size="sm"
										variant="ghost"
										onClick={() =>
											setExpanded((e) => ({ ...e, [actor]: !e[actor] }))
										}
									>
										{expanded[actor]
											? "Collapse related findings"
											: `Show all ${issues.length} related findings`}
									</Button>
								)}
							</article>
						))}
						{!groups.length && review && (
							<p className="text-sm text-muted-foreground">
								No open issues in this filter.
							</p>
						)}
					</div>
				</aside>
			</div>
			{phase && (
				<MapLoadingOverlay
					phase="loading-workspace"
					error=""
					onRetry={() => {}}
					draftCreated
					title={
						phase === "entry"
							? "Checking saved seating plan…"
							: "Publishing verified seating plan…"
					}
				/>
			)}
			<Dialog
				open={!!preview}
				onOpenChange={(open) => {
					if (!open) setPreview(null);
				}}
			>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Apply chain swap</DialogTitle>
						<DialogDescription>{preview?.description}</DialogDescription>
					</DialogHeader>
					<p className="text-sm">
						All registrations keep their paid seats. You can undo this change.
					</p>
					<Button
						onClick={() => {
							if (preview) commit(preview.state);
							setPreview(null);
						}}
					>
						Apply chain swap
					</Button>
				</DialogContent>
			</Dialog>
			<Dialog open={confirmPublish} onOpenChange={setConfirmPublish}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Publish seating plan</DialogTitle>
						<DialogDescription>
							This replaces the public seating plan with this saved, verified
							revision.
						</DialogDescription>
					</DialogHeader>
					<Button disabled={!canPublish} onClick={publish}>
						Confirm publication
					</Button>
				</DialogContent>
			</Dialog>
		</main>
	);
}
