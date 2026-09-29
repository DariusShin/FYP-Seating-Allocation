"use client";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
	Armchair,
	Search,
	Undo2,
	Redo2,
	Users,
	Settings2,
	PanelRightClose,
	ArrowRightLeft,
	Accessibility,
	MapPinned,
	StickyNote,
	Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogTitle,
	DialogDescription,
	DialogHeader,
} from "@/components/ui/dialog";
import type { AllocationResult } from "@/lib/allocation-types";
import {
	dock,
	eligible,
	move,
	type Workspace,
	type WorkingState,
} from "@/lib/workspace";
import { HallMap, type SeatMarkers } from "./hall-map";
import { AllocationDetails } from "./allocation-details";
import { WeightControls } from "./weight-controls";
import { TIER_STYLES } from "./seat-theme";

type Modal =
	| "allocation"
	| "review"
	| "checklist"
	| "settings"
	| "versions"
	| "legend"
	| "publish"
	| null;
export function SeatDashboard({
	initialResult,
	initialWorkspace,
}: {
	initialResult: AllocationResult;
	initialWorkspace?: Workspace;
}) {
	const [workspace, setWorkspace] = useState<Workspace | null>(
		initialWorkspace ?? null,
	);
	const [state, setState] = useState<WorkingState | null>(
		initialWorkspace?.state ?? null,
	);
	const [mode, setMode] = useState<"read" | "edit" | "review">("read");
	const [selected, setSelected] = useState<string | null>(null);
	const [selectedSeat, setSelectedSeat] = useState<string | null>(null);
	const [dockOpen, setDockOpen] = useState(false);
	const draggingParticipant = useRef<string | null>(null);
	const [destination, setDestination] = useState("");
	const [query, setQuery] = useState("");
	const [filter, setFilter] = useState("all");
	const [modal, setModal] = useState<Modal>(null);
	const [history, setHistory] = useState<WorkingState[]>([]);
	const [future, setFuture] = useState<WorkingState[]>([]);
	const [notice, setNotice] = useState("");
	const [error, setError] = useState("");
	const [busy, setBusy] = useState(false);
	const [preview, setPreview] = useState<{
		state: WorkingState;
		description: string;
		returnToAllocation?: boolean;
	} | null>(null);
	const [versions, setVersions] = useState<
		{ id: string; state: string; created: string }[]
	>([]);
	async function load() {
		setBusy(true);
		try {
			const r = await fetch("/api/workspace", { cache: "no-store" });
			const value = await r.json();
			if (!r.ok || !value) throw Error("Unable to load the working draft.");
			setWorkspace(value);
			setState(value.state);
			setHistory([]);
			setFuture([]);

			setError("");
			setMode("read");
			setDockOpen(false);
			setModal(null);
		} catch (e) {
			setError(String(e));
		} finally {
			setBusy(false);
		}
	}
	useEffect(() => {
		if (initialWorkspace) return;
		const startup = window.setTimeout(() => void load(), 0);
		return () => window.clearTimeout(startup);
	}, [initialWorkspace]);
	const dirty =
		!!workspace && JSON.stringify(state) !== JSON.stringify(workspace.state);
	const base = workspace?.base ?? initialResult;
	const rows = base.floor_plan.rows;
	const cells = useMemo(
		() =>
			rows.flatMap((r) => r.seats.map((s) => ({ ...s, row: r.row_number }))),
		[rows],
	);
	const names: Record<string, string> = {};
	const owners: Record<string, string> = {};
	if (state)
		for (const [pid, m] of Object.entries(state.items))
			m.seat_ids.forEach((sid) => {
				names[sid] = m.display_names[0];
				owners[sid] = pid;
			});
	const people = state?.participants ?? [];
	const active = people.filter(eligible);
	const docked = active.filter(
		(p) => !state?.items[p.participant_id].seat_ids.length,
	);
	const matches = new Set(
		people
			.filter((p) =>
				`${p.full_name} ${state?.items[p.participant_id].display_names.join(" ")}`
					.toLocaleLowerCase()
					.includes(query.trim().toLocaleLowerCase()),
			)
			.map((p) => p.participant_id),
	);
	const person = people.find((p) => p.participant_id === selected);
	const item = selected ? state?.items[selected] : undefined;
	const canEdit = mode === "edit" && !busy;
	const blocked = cells.filter((s) => s.is_blocked).length;
	const published =
		base.publication_status === "PUBLISHED" &&
		(!workspace?.saved_at || workspace.saved_at === base.published_at) &&
		!dirty;
	function location(ids: string[]) {
		return ids.length
			? ids
					.map((id) => {
						const s = cells.find((s) => s.seat_id === id)!;
						return `${s.side === "LEFT" ? "西單" : "東單"} ${s.row} · ${s.physical_position <= 8 ? s.physical_position : s.physical_position - 8}`;
					})
					.join(" + ")
			: "Holding dock";
	}
	function commit(next: WorkingState) {
		if (!canEdit) return;
		setHistory((h) => [...h.slice(-49), state!]);
		setFuture([]);
		setState(next);

		setError("");
	}
	function proposeMove(pid: string, sid: string) {
		if (!canEdit || !state) return;
		try {
			const next = move(state, base, pid, sid);
			const other = owners[sid];
			setModal(null);
			setPreview({
				state: next,
				returnToAllocation: modal === "allocation",
				description: `${state.items[pid].display_names[0]}: ${location(state.items[pid].seat_ids)} → ${location(next.items[pid].seat_ids)}${other && other !== pid ? `. ${state.items[other].display_names[0]}: ${location(state.items[other].seat_ids)} → ${location(next.items[other].seat_ids)}` : ""}`,
			});
		} catch (e) {
			setError(String(e));
		}
	}
	function sendToDock(pid: string) {
		if (!canEdit || !state) return;
		if (!state.items[pid]?.seat_ids.length) {
			setDockOpen(true);
			return;
		}
		try {
			commit(dock(state, pid));
			setDockOpen(true);
			setModal(null);
			draggingParticipant.current = null;
		} catch (e) {
			setError(String(e));
		}
	}
	async function operation(
		command: "workspace_save" | "workspace_publish",
		nextState = state,
	) {
		if (!workspace || !nextState) return false;
		setBusy(true);
		setError("");
		try {
			const r = await fetch("/api/workspace", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					command,
					plan_version_id: base.plan_version_id,
					revision: workspace.revision,
					state: nextState,
				}),
			});
			const value = await r.json();
			if (!r.ok) throw Error(value.error?.message ?? "Operation failed");
			setWorkspace(value);
			setState(value.state);

			setNotice(
				command === "workspace_publish"
					? "Seating plan published. Venue display now uses this version."
					: "Working draft saved. Public seating is unchanged.",
			);
			if (command === "workspace_publish") {
				setMode("read");
				setModal(null);
				setHistory([]);
				setFuture([]);
			}
			return true;
		} catch (e) {
			setError(String(e));
			return false;
		} finally {
			setBusy(false);
		}
	}
	function selectSeat(sid: string) {
		setSelectedSeat(sid);
		if (owners[sid]) {
			setSelected(owners[sid]);
			setDestination("");
			setModal("allocation");
		} else if (canEdit && selected) {
			setDestination(sid);
			proposeMove(selected, sid);
		}
	}
	function selectParticipant(participantId: string) {
		setSelected(participantId);
		setSelectedSeat(state?.items[participantId]?.seat_ids[0] ?? null);
		setModal("allocation");
	}
	const visible = people.filter((p) => {
		const m = state?.items[p.participant_id];
		if (!m || !matches.has(p.participant_id)) return false;
		switch (filter) {
			case "dock":
				return eligible(p) && !m.seat_ids.length;
			case "note":
				return !!m.note;
			case "changed":
				return (
					m.changed_at?.slice(0, 10) === new Date().toISOString().slice(0, 10)
				);
			default:
				return true;
		}
	});
	if (!state)
		return (
			<main className="p-8">
				<h1>Loading seating workspace…</h1>
				{error && <p role="alert">{error}</p>}
				<Button onClick={load}>Retry</Button>
			</main>
		);
	return (
		<main
			className="seat-workspace"
			onDragOver={(e) => {
				if (
					canEdit &&
					draggingParticipant.current &&
					!(e.target as Element).closest("[data-venue-boundary]")
				) {
					e.preventDefault();
					e.dataTransfer.dropEffect = "move";
					setDockOpen(true);
				}
			}}
			onDrop={(e) => {
				if (
					canEdit &&
					draggingParticipant.current &&
					!e.defaultPrevented &&
					!(e.target as Element).closest("[data-venue-boundary]")
				) {
					e.preventDefault();
					sendToDock(draggingParticipant.current);
				}
			}}
		>
			<header className="workspace-header">
				<div className="brand-mark">
					<Armchair size={20} />
				</div>
				<div>
					<h1>
						PJKIT <span>Seating workspace</span>
					</h1>
					<p>2026 梁皇寶懺大法會 · Staff workspace</p>
				</div>
				<div className="relative z-30 ml-auto w-[min(340px,28vw)] max-[1100px]:w-[min(280px,30vw)] max-[700px]:order-3 max-[700px]:ml-0 max-[700px]:w-full">
					<label className="flex h-9.5 items-center gap-2 rounded-lg border border-input bg-background px-2.5 text-muted-foreground focus-within:outline-2 focus-within:outline-ring focus-within:outline-offset-2">
						<Search aria-hidden="true" className="size-4 shrink-0" />
						<input
							aria-label="Search participants by name or ID"
							placeholder="Search participants · 搜尋姓名"
							value={query}
							className="min-w-0 flex-1 bg-transparent text-[13px] text-foreground outline-none placeholder:text-muted-foreground"
							onChange={(event) => setQuery(event.target.value)}
							onKeyDown={(event) => {
								if (event.key === "Enter") {
									const firstMatch = people.find((p) =>
										matches.has(p.participant_id),
									);
									if (firstMatch) selectParticipant(firstMatch.participant_id);
								}
							}}
						/>
						{query && (
							<button
								type="button"
								aria-label="Clear participant search"
								className="grid size-6 shrink-0 place-items-center rounded text-lg hover:bg-muted"
								onClick={() => setQuery("")}
							>
								×
							</button>
						)}
					</label>
					{query.trim() && (
						<div
							className="absolute inset-x-0 top-[calc(100%+7px)] max-h-[min(60vh,440px)] overflow-auto rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-xl"
							role="listbox"
							aria-label="Matching participants"
						>
							<p
								className="px-2 py-1.5 text-[11px] text-muted-foreground"
								aria-live="polite"
							>
								{matches.size} matches
							</p>
							{people
								.filter((p) => matches.has(p.participant_id))
								.slice(0, 8)
								.map((p) => (
									<button
										type="button"
										role="option"
										aria-selected={selected === p.participant_id}
										key={p.participant_id}
										className="flex w-full flex-col gap-0.5 rounded-md p-2 text-left hover:bg-accent hover:text-accent-foreground aria-selected:bg-accent"
										onClick={() => selectParticipant(p.participant_id)}
									>
										<span className="text-[13px] font-medium">
											{state.items[p.participant_id].display_names[0]}
										</span>
										<small className="text-[11px] text-muted-foreground">
											{p.participant_id} ·{" "}
											{location(state.items[p.participant_id].seat_ids)}
										</small>
									</button>
								))}
							{matches.size === 0 && (
								<span className="block p-2 text-[11px] text-muted-foreground">
									No matching participants
								</span>
							)}
							{matches.size > 8 && (
								<span className="block p-2 text-[11px] text-muted-foreground">
									Type more to narrow results
								</span>
							)}
						</div>
					)}
				</div>
				<nav aria-label="Workspace">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setModal("checklist")}
					>
						<Users /> Participants
					</Button>
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setModal("settings")}
					>
						<Settings2 /> Settings
					</Button>
					<Button
						variant="ghost"
						size="sm"
						onClick={async () => {
							try {
								const r = await fetch("/api/plans");
								if (!r.ok) throw Error("Version history unavailable");
								setVersions((await r.json()).plans);
								setModal("versions");
							} catch (e) {
								setError(String(e));
							}
						}}
					>
						Versions
					</Button>
					<Button variant="outline" size="sm" asChild>
						<Link href="/venue" target="_blank">
							Venue display ↗
						</Link>
					</Button>
				</nav>
			</header>
			<section className="context-bar">
				<span className={`mode-pill ${mode}`}>
					{published ? "Published" : "Draft"} ·{" "}
					{mode === "read"
						? "Read mode"
						: mode === "edit"
							? "Edit mode"
							: "Review"}
				</span>
				<span role="status">
					{busy
						? "Working…"
						: dirty
							? "Unsaved changes"
							: workspace?.saved_at
								? `Saved ${new Date(workspace.saved_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
								: "Generated draft"}
				</span>
				<span className="readiness">
					{active.length} paid registrations · {docked.length} in dock
				</span>
				<div className="context-actions">
					{mode !== "edit" ? (
						<Button
							size="sm"
							variant="outline"
							disabled={busy}
							onClick={() => {
								setMode("edit");
							}}
						>
							{published ? "Start revision" : "Edit plan"}
						</Button>
					) : (
						<>
							<Button
								size="sm"
								variant="outline"
								disabled={busy || !dirty}
								onClick={() => operation("workspace_save")}
							>
								Save draft
							</Button>
							<Button
								size="sm"
								onClick={() => {
									setMode("review");
									setModal("review");
									setNotice(
										"Review your changes, save, then continue to publication.",
									);
								}}
							>
								Finish editing
							</Button>
						</>
					)}
					{mode === "review" && (
						<Button
							size="sm"
							disabled={busy || dirty}
							title={
								dirty
									? "Save your changes before publishing"
									: "Review this saved revision for publication"
							}
							onClick={() => setModal("review")}
						>
							Review publication
						</Button>
					)}
				</div>
			</section>
			{error && (
				<div className="workspace-banner error" role="alert">
					{error}
				</div>
			)}
			{notice && (
				<div className="workspace-notice" role="status">
					{notice}
					<button aria-label="Dismiss notice" onClick={() => setNotice("")}>
						×
					</button>
				</div>
			)}
			<section className="workspace-body">
				<div className="map-column">
					<div className="map-toolbar">
						<div className="map-tools">
							{mode === "edit" && docked.length > 0 && (
								<Button
									variant="outline"
									size="sm"
									onClick={() => setDockOpen((v) => !v)}
								>
									Holding dock ({docked.length})
								</Button>
							)}
							{mode === "review" && (
								<Button
									variant="outline"
									size="sm"
									onClick={() => setModal("review")}
								>
									Review plan
								</Button>
							)}
							<Button
								variant="outline"
								size="sm"
								onClick={() => setModal("legend")}
							>
								<MapPinned data-icon="inline-start" /> Legend & map guide
							</Button>
						</div>
					</div>
					<HallMap
						floor={base.floor_plan}
						names={names}
						owners={owners}
						primaryNames={Object.fromEntries(
							people.map((p) => [
								p.participant_id,
								state.items[p.participant_id].display_names[0],
							]),
						)}
						tiers={Object.fromEntries(
							people.map((p) => [p.participant_id, p.contribution_tier]),
						)}
						markers={Object.fromEntries(
							people.map((p) => [
								p.participant_id,
								{
									hasNote: !!state.items[p.participant_id].note,
									elderly: p.age >= 60,
									accessible: p.requires_accessible_seat,
								} satisfies SeatMarkers,
							]),
						)}
						selected={selected}
						selectedSeat={selectedSeat}
						matches={query ? matches : undefined}
						editable={canEdit}
						onSelect={selectSeat}
						onDrop={proposeMove}
						onAllocationDragStart={(pid) => {
							draggingParticipant.current = pid;
						}}
						onAllocationDragEnd={() => {
							draggingParticipant.current = null;
						}}
					/>
					<footer className="map-footer">
						<span>
							{active.length} registrations ·{" "}
							{active.reduce(
								(n, p) => n + (p.contribution_tier === "EMPEROR" ? 2 : 1),
								0,
							)}{" "}
							people
						</span>
						<span>
							{Object.keys(owners).length} occupied ·{" "}
							{cells.length - blocked - Object.keys(owners).length} empty ·{" "}
							{blocked} blocked
						</span>
						{mode === "edit" && (
							<div>
								<Button
									variant="ghost"
									size="icon-sm"
									aria-label="Undo"
									disabled={!canEdit || !history.length}
									onClick={() => {
										setFuture((f) => [state, ...f]);
										setState(history.at(-1)!);
										setHistory((h) => h.slice(0, -1));
									}}
								>
									<Undo2 />
								</Button>
								<Button
									variant="ghost"
									size="icon-sm"
									aria-label="Redo"
									disabled={!canEdit || !future.length}
									onClick={() => {
										setHistory((h) => [...h, state]);
										setState(future[0]);
										setFuture((f) => f.slice(1));
									}}
								>
									<Redo2 />
								</Button>
							</div>
						)}
					</footer>
				</div>
				{mode === "edit" && dockOpen && (
					<aside className="work-panel" aria-label="Holding dock">
						<div className="panel-heading">
							<h2>Holding dock</h2>
							<Button
								variant="ghost"
								size="icon-sm"
								aria-label="Close holding dock"
								onClick={() => setDockOpen(false)}
							>
								<PanelRightClose />
							</Button>
						</div>
						<section
							className="holding-dock dock-panel-content"
							onDragOver={(e) => {
								if (canEdit) e.preventDefault();
							}}
							onDrop={(e) => {
								e.preventDefault();
								e.stopPropagation();
								sendToDock(e.dataTransfer.getData("text/plain"));
							}}
						>
							<h3>
								Holding dock <span>{docked.length}</span>
							</h3>
							<p>Drop allocations here while rearranging.</p>
							{docked.length === 0 ? (
								<div className="empty-dock">
									Everyone has a place.
									<br />
									The dock is ready when you need it.
								</div>
							) : (
								docked.map((p) => (
									<button
										className={`dock-card ${selected === p.participant_id ? "active" : ""}`}
										key={p.participant_id}
										draggable={canEdit}
										onDragStart={(e) =>
											e.dataTransfer.setData("text/plain", p.participant_id)
										}
										onClick={() => {
											setSelected(p.participant_id);
											setModal("allocation");
										}}
									>
										<strong>
											{state.items[p.participant_id].display_names[0]}
										</strong>
										<span>
											{p.contribution_tier === "EMPEROR"
												? "Pair · 2 seats"
												: "Individual · 1 seat"}
										</span>
										<small>
											{state.items[p.participant_id].dock_reason ||
												"Awaiting placement"}{" "}
											· from{" "}
											{location(
												state.items[p.participant_id].previous_seat_ids,
											)}
										</small>
									</button>
								))
							)}
						</section>
					</aside>
				)}
			</section>
			<Dialog
				open={!!preview}
				onOpenChange={(open) => {
					if (!open) {
						if (preview?.returnToAllocation) setModal("allocation");
						setPreview(null);
					}
				}}
			>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Confirm seat changes</DialogTitle>
						<DialogDescription>{preview?.description}</DialogDescription>
					</DialogHeader>
					<p className="text-sm">
						Names and notes stay with each allocation. Packing and priority can
						be inspected on the map.
					</p>
					<div className="flex gap-2">
						<Button
							disabled={!canEdit}
							onClick={() => {
								if (preview) commit(preview.state);
								setPreview(null);
							}}
						>
							Confirm move / swap
						</Button>
						<Button
							variant="outline"
							onClick={() => {
								if (preview?.returnToAllocation) setModal("allocation");
								setPreview(null);
							}}
						>
							Cancel
						</Button>
					</div>
				</DialogContent>
			</Dialog>
			<Dialog
				open={!!modal}
				onOpenChange={(open) => {
					if (!open) setModal(null);
				}}
			>
				<DialogContent
					className={
						modal === "checklist"
							? "sm:max-w-3xl max-h-[85vh] overflow-auto"
							: "max-h-[85vh] overflow-auto"
					}
				>
					<DialogHeader>
						<DialogTitle>
							{
								{
									allocation: "Allocation details",
									review: "Review before publishing",
									checklist: "Participant checklist",
									settings: "Allocation preferences",
									versions: "Version history",
									legend: "Map legend and help",
									publish: "Publish seating plan",
								}[modal ?? "legend"]
							}
						</DialogTitle>
						<DialogDescription>
							{modal === "publish"
								? "This makes the saved seating plan visible on the venue display and participant lookup."
								: "PJKIT staff workspace"}
						</DialogDescription>
					</DialogHeader>
					{modal === "allocation" && (
						<>
							{error && (
								<p role="alert" className="text-destructive">
									{error}
								</p>
							)}
							{person && item ? (
								<>
									<AllocationDetails
										key={person.participant_id}
										person={person}
										item={item}
										location={location(item.seat_ids)}
										busy={busy}
										onClose={() => setModal(null)}
										onSave={(details) =>
											operation("workspace_save", {
												...state,
												items: {
													...state.items,
													[person.participant_id]: {
														...item,
														...details,
														changed_at: new Date().toISOString(),
													},
												},
											})
										}
									/>
									{canEdit && eligible(person) && (
										<div className="allocation-actions">
											<label>
												Move / swap destination
												<select
													aria-label="Move or swap destination"
													value={destination}
													onChange={(e) => setDestination(e.target.value)}
												>
													<option value="">Choose a seat…</option>
													{cells
														.filter((s) => !s.is_blocked)
														.map((s) => (
															<option key={s.seat_id} value={s.seat_id}>
																{location([s.seat_id])} ·{" "}
																{names[s.seat_id] || "Empty"}
															</option>
														))}
												</select>
											</label>
											<Button
												variant="outline"
												size="sm"
												disabled={!destination}
												onClick={() =>
													proposeMove(person.participant_id, destination)
												}
											>
												<ArrowRightLeft /> Preview move / swap
											</Button>
											<Button
												variant="outline"
												size="sm"
												disabled={!item.seat_ids.length}
												onClick={() => sendToDock(person.participant_id)}
											>
												Send to holding dock
											</Button>
										</div>
									)}
								</>
							) : (
								<p>Select a registration to view its details.</p>
							)}
						</>
					)}
					{modal === "review" && (
						<>
							{error && (
								<p role="alert" className="text-destructive">
									{error}
								</p>
							)}
							<p className="muted-copy">
								The public continues to see the last published version until you
								confirm publication.
							</p>
							{dirty && (
								<Button
									disabled={busy}
									onClick={() => operation("workspace_save")}
								>
									Save working draft
								</Button>
							)}
							<div className="review-summary">
								<strong>{docked.length} docked</strong>
								<span>
									{people.filter((p) => !eligible(p)).length} excluded
									registrations
								</span>
								<span>
									{
										people.filter(
											(p) => state.items[p.participant_id].changed_at,
										).length
									}{" "}
									manually changed
								</span>
							</div>
							<p className="muted-copy">
								Inspect the map and names before publishing this saved draft.
							</p>
							{docked.length > 0 && (
								<p className="muted-copy">
									Assign every docked registration before publishing; paid seats
									are retained regardless of attendance.
								</p>
							)}
							<Button
								disabled={busy || dirty || docked.length > 0}
								onClick={() => setModal("publish")}
							>
								Continue to publication
							</Button>
						</>
					)}

					{modal === "checklist" && (
						<>
							<label className="flex gap-2 text-sm">
								Filter
								<select
									className="border p-1"
									value={filter}
									onChange={(e) => setFilter(e.target.value)}
								>
									{Object.entries({
										all: "All registrations",
										dock: "Unseated / in dock",
										note: "Has note",
										changed: "Changed today",
									}).map(([value, label]) => (
										<option key={value} value={value}>
											{label}
										</option>
									))}
								</select>
							</label>
							<input
								className="border rounded p-2"
								aria-label="Search checklist"
								placeholder="Search registered or displayed names"
								value={query}
								onChange={(e) => setQuery(e.target.value)}
							/>
							<div className="checklist">
								{visible.map((p) => {
									const m = state.items[p.participant_id];
									return (
										<div
											key={p.participant_id}
											className={
												selected === p.participant_id ? "selected" : ""
											}
										>
											<button
												onClick={() => {
													setSelected(p.participant_id);
													setModal("allocation");
												}}
											>
												<strong>{m.display_names[0]}</strong>
												<small>
													{p.full_name} · {location(m.seat_ids)} ·{" "}
													{p.registration_status}
												</small>
											</button>
										</div>
									);
								})}
								{!visible.length && <p>No matching participants.</p>}
							</div>
							<div className="flex gap-2">
								<Button
									variant="outline"
									disabled={!visible.length}
									onClick={() =>
										setSelected(
											visible[
												(visible.findIndex(
													(p) => p.participant_id === selected,
												) -
													1 +
													visible.length) %
													visible.length
											].participant_id,
										)
									}
								>
									Previous
								</Button>
								<Button
									variant="outline"
									disabled={!visible.length}
									onClick={() =>
										setSelected(
											visible[
												(visible.findIndex(
													(p) => p.participant_id === selected,
												) +
													1) %
													visible.length
											].participant_id,
										)
									}
								>
									Next
								</Button>
							</div>
						</>
					)}
					{modal === "settings" && (
						<>
							<p className="text-sm">
								Preferences affect future generation. Existing manual work is
								kept in the saved working draft. Regeneration is secondary to
								manual maintenance.
							</p>
							<WeightControls
								result={base}
								hasDraft={dirty || !!workspace?.saved_at}
								onResult={async (result) => {
									const response = await fetch("/api/workspace", {
										method: "POST",
										headers: { "Content-Type": "application/json" },
										body: JSON.stringify({
											command: "workspace_open",
											plan_version_id: result.plan_version_id,
										}),
									});
									const value = await response.json();
									if (!response.ok || !value?.base || !value?.state)
										throw new Error(
											value?.error?.message ?? "Unable to open the new draft",
										);
									setWorkspace(value);
									setState(value.state);
									setHistory([]);
									setFuture([]);
									setSelected(null);
									setSelectedSeat(null);
									setPreview(null);
									setDockOpen(false);
									setMode("read");
									setModal(null);
									setNotice(
										"New seating draft ready. Public seating is unchanged.",
									);
								}}
								onSolvingChange={setBusy}
							/>
						</>
					)}
					{modal === "versions" && (
						<div className="space-y-2">
							{versions.map((v) => (
								<div className="rounded border p-3 text-sm" key={v.id}>
									<strong>{v.state}</strong> ·{" "}
									{new Date(v.created).toLocaleString()}
									<p className="text-xs text-muted-foreground">{v.id}</p>
								</div>
							))}
						</div>
					)}
					{modal === "legend" && (
						<div className="space-y-5">
							<div className="grid gap-3 sm:grid-cols-2">
								{(
									[
										["EMPEROR", "Emperor · Pair registration"],
										["MERIT", "Merit · Individual registration"],
										["BODHI", "Bodhi · Individual registration"],
									] as const
								).map(([tier, label]) => (
									<div key={tier} className="legend-row">
										<span
											className={`legend-tier-swatch ${TIER_STYLES[tier].cell.split(" hover:")[0]}`}
										/>
										<span>{label}</span>
									</div>
								))}
								<div className="legend-row">
									<span className="legend-empty-swatch" /> Empty seat ·
									available
								</div>
								<div className="legend-row">
									<span className="legend-blocked-swatch">×</span> Building
									structure · unavailable
								</div>
							</div>
							<section>
								<h3 className="legend-section-title">Participant indicators</h3>
								<div className="grid gap-2 sm:grid-cols-2">
									<div className="legend-row">
										<span className="legend-icon">
											<Accessibility />
										</span>{" "}
										Accessible seating required
									</div>
									<div className="legend-row">
										<span className="legend-icon">
											<Star />
										</span>{" "}
										Elderly participant
									</div>
									<div className="legend-row">
										<span className="legend-icon">
											<StickyNote />
										</span>{" "}
										Staff note recorded
									</div>
								</div>
							</section>
							<div className="legend-directions">
								<strong>How to read the hall</strong>
								<p>
									三寶佛 is the front. 西單 columns are 1–8; 東單 columns are
									9–16. The centre aisle separates the two sides. Emperor pairs
									appear as one double-width card and move together.
								</p>
								<p>
									Select a participant card to review its registration. Search
									highlights matching names; other allocations are dimmed. In
									read mode the plan is protected; edit mode enables
									drag-and-drop and move/swap.
								</p>
							</div>
						</div>
					)}
					{modal === "publish" && (
						<>
							{error && (
								<p role="alert" className="text-destructive">
									{error}
								</p>
							)}
							<p>
								{active.length} registrations · {Object.keys(owners).length}{" "}
								occupied seats.
							</p>
							<p className="text-sm">
								Publishing replaces the current public version. Future edits
								create a private working revision.
							</p>
							<Button
								disabled={busy || dirty || docked.length > 0}
								onClick={() => operation("workspace_publish")}
							>
								Publish seating plan
							</Button>
						</>
					)}
				</DialogContent>
			</Dialog>
		</main>
	);
}
