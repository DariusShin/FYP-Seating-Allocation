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
import {
	Dialog,
	DialogContent,
	DialogTitle,
	DialogDescription,
	DialogHeader,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
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
import { VerificationScreen } from "./verification-screen";
import { TIER_STYLES } from "./seat-theme";

type Modal =
	| "allocation"
	| "checklist"
	| "settings"
	| "versions"
	| "legend"
	| null;
export function SeatDashboard({
	initialResult,
	initialWorkspace,
}: {
	initialResult: AllocationResult;
	initialWorkspace?: Workspace;
}) {
	const [workspace, setWorkspace] = useState<Workspace | null>(initialWorkspace ?? null);
	const [state, setState] = useState<WorkingState | null>(initialWorkspace?.state ?? null);
	const [resume, setResume] = useState(initialWorkspace?.review?.review_status === "IN_PROGRESS");
	const [mode, setMode] = useState<"read" | "edit" | "review">("read");
	const [selection, setSelection] = useState<{
		participantId: string | null;
		seatId: string | null;
	}>({ participantId: null, seatId: null });
	const [dockOpen, setDockOpen] = useState(false);
	const draggingParticipant = useRef<string | null>(null);
	const [destination, setDestination] = useState("");
	const [query, setQuery] = useState("");
	const [filter, setFilter] = useState("all");
	const [modal, setModal] = useState<Modal>(null);
	const [timeline, setTimeline] = useState<{
		past: WorkingState[];
		future: WorkingState[];
	}>({ past: [], future: [] });
	const [error, setError] = useState("");
	const [busy, setBusy] = useState(false);
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
			setResume(value.review?.review_status === "IN_PROGRESS");
			setTimeline({ past: [], future: [] });

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
	const person = people.find((p) => p.participant_id === selection.participantId);
	const item = selection.participantId
		? state?.items[selection.participantId]
		: undefined;
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
		setTimeline((current) => ({
			past: [...current.past.slice(-49), state!],
			future: [],
		}));
		setState(next);

		setError("");
	}
	function applyMove(pid: string, sid: string) {
		if (!canEdit || !state) return;
		try {
			const next = move(state, base, pid, sid);
			if (next === state) return;
			commit(next);
			setModal(null);
			setDestination("");
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
    async function submitReview() {
        if (!workspace || !state || docked.length) return;
        setBusy(true); setError("");
        try {
            let value = workspace;
            if (dirty) {
                const response = await fetch("/api/workspace", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ command: "workspace_save", plan_version_id: base.plan_version_id, revision: workspace.revision, state }),
                });
                value = await response.json();
                if (!response.ok) throw Error((value as unknown as { error?: { message: string } }).error?.message ?? "Unable to save draft");
            }
            setWorkspace(value); setState(value.state); setResume(false); setModal(null); setMode("review");
        } catch (e) { setError(String(e)); } finally { setBusy(false); }
    }
    async function operation(command: "workspace_save", nextState = state) {
        if (!workspace || !nextState) return false;
        setBusy(true); setError("");
        try {
            const response = await fetch("/api/workspace", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command, plan_version_id: base.plan_version_id, revision: workspace.revision, state: nextState }),
            });
            const value = await response.json();
            if (!response.ok) throw Error(value.error?.message ?? "Unable to save draft");
            setWorkspace(value); setState(value.state);
            toast.success("Working draft saved. Public seating is unchanged.");
            return true;
        } catch (e) { setError(String(e)); return false; } finally { setBusy(false); }
    }
	function selectSeat(sid: string) {
		setSelection((current) => ({ ...current, seatId: sid }));
		if (owners[sid]) {
			setSelection({ participantId: owners[sid], seatId: sid });
			setDestination("");
			setModal("allocation");
		} else if (canEdit && selection.participantId) {
			setDestination(sid);
			applyMove(selection.participantId, sid);
		}
	}
	function selectParticipant(participantId: string) {
		setSelection({
			participantId,
			seatId: state?.items[participantId]?.seat_ids[0] ?? null,
		});
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
    if (mode === "review" && workspace) return <VerificationScreen initial={workspace}
        onExit={(value, seat) => { setWorkspace(value); setState(value.state); setMode("edit"); setSelection({ participantId: null, seatId: seat }); setTimeline({ past: [], future: [] }); }}
        onPublished={value => { setWorkspace(value); setState(value.state); setMode("read"); setTimeline({ past: [], future: [] }); toast.success("Seating plan published. Venue display now uses this version."); }} />;
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
			className="flex h-dvh flex-col overflow-hidden bg-background text-[15px] text-foreground print:h-auto"
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
			<header className="flex shrink-0 items-center gap-3 border-b px-5.5 py-2.5 max-[1100px]:px-3 max-[700px]:flex-wrap max-[700px]:gap-2 print:hidden">
				<div className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
					<Armchair size={20} />
				</div>
				<div>
					<h1 className="text-base font-semibold">
						PJKIT{" "}
						<span className="ml-2 text-sm font-normal text-muted-foreground max-[1100px]:hidden">
							Seating workspace
						</span>
					</h1>
					<p className="mt-0.5 text-[13px] text-muted-foreground">
						2026 梁皇寶懺大法會 · Staff workspace
					</p>
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
										aria-selected={selection.participantId === p.participant_id}
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
				<nav
					className="ml-auto flex items-center gap-1 max-[1100px]:ml-0 max-[1100px]:gap-0 max-[700px]:ml-auto"
					aria-label="Workspace"
				>
					<Button
						variant="ghost"
						size="sm"
						className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
						onClick={() => setModal("checklist")}
					>
						<Users /> Participants
					</Button>
					<Button
						variant="ghost"
						size="sm"
						className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
						onClick={() => setModal("settings")}
					>
						<Settings2 /> Settings
					</Button>
					<Button
						variant="ghost"
						size="sm"
						className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
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
					<Button
						variant="outline"
						size="sm"
						className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
						asChild
					>
						<Link href="/venue" target="_blank">
							Venue display ↗
						</Link>
					</Button>
				</nav>
			</header>
			<section className="flex min-h-13.5 shrink-0 items-center gap-4 border-b px-5.5 py-2 text-sm text-muted-foreground max-[1100px]:gap-2 max-[1100px]:px-3 print:hidden">
				<span
					className={`whitespace-nowrap rounded-md border bg-background px-2.5 py-1.25 font-medium text-foreground ${mode === "edit" ? "bg-secondary" : ""} ${mode === "review" ? "border-primary" : ""}`}
				>
					{published ? "Published" : "Draft"} ·{" "}
					{mode === "read" ? "Read mode" : "Edit mode"}
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
				<span className="text-muted-foreground max-[1100px]:hidden">
					{active.length} paid registrations · {docked.length} in dock
				</span>
				<div className="ml-auto flex gap-2">
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
								disabled={busy || docked.length > 0}
                                onClick={submitReview}
							>
								Submit for review
							</Button>
						</>
					)}

				</div>
			</section>
            {mode === "edit" && docked.length > 0 && <p role="status" className="border-b px-5 py-2 text-sm">{docked.length} participants unseated — assign every paid registration before review.</p>}
            <Dialog open={resume} onOpenChange={setResume}><DialogContent><DialogHeader><DialogTitle>Safeguard review in progress</DialogTitle><DialogDescription>{(workspace?.review?.summary?.acked ?? 0) + (workspace?.review?.summary?.resolved ?? 0)} of {(workspace?.review?.summary?.acked ?? 0) + (workspace?.review?.summary?.resolved ?? 0) + (workspace?.review?.summary?.open_blocking ?? 0) + (workspace?.review?.summary?.open_advisory ?? 0)} handled in the last saved review. Resume to check the latest seating plan.</DialogDescription></DialogHeader><Button disabled={busy || docked.length > 0} onClick={submitReview}>Resume review</Button><Button variant="outline" onClick={() => { setResume(false); setMode("edit"); }}>Back to editing</Button></DialogContent></Dialog>
			{error && (
				<div
					className="bg-muted px-6 py-2.25 text-sm text-destructive"
					role="alert"
				>
					{error}
				</div>
			)}
			<section className="flex min-h-0 flex-1">
				<div className="flex min-w-0 flex-1 flex-col overflow-hidden">
					<div className="flex min-h-14.25 items-center gap-2.5 border-b px-4 py-2.5 print:hidden">
						<div className="ml-auto flex items-center gap-0.5">
							{mode === "edit" && docked.length > 0 && (
								<Button
									variant="outline"
									size="sm"
									onClick={() => setDockOpen((v) => !v)}
								>
									Holding dock ({docked.length})
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
						selected={selection.participantId}
						selectedSeat={selection.seatId}
						matches={query ? matches : undefined}
						editable={canEdit}
						onSelect={selectSeat}
						onDrop={applyMove}
						onAllocationDragStart={(pid) => {
							draggingParticipant.current = pid;
						}}
						onAllocationDragEnd={() => {
							draggingParticipant.current = null;
						}}
					/>
					<footer className="flex min-h-10.5 shrink-0 items-center justify-between gap-2.5 border-t px-3.75 py-2 text-xs text-muted-foreground">
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
									disabled={!canEdit || !timeline.past.length}
									onClick={() => {
										const previous = timeline.past.at(-1)!;
										setTimeline((current) => ({
											past: current.past.slice(0, -1),
											future: [state, ...current.future],
										}));
										setState(previous);
									}}
								>
									<Undo2 />
								</Button>
								<Button
									variant="ghost"
									size="icon-sm"
									aria-label="Redo"
									disabled={!canEdit || !timeline.future.length}
									onClick={() => {
										const next = timeline.future[0];
										setTimeline((current) => ({
											past: [...current.past, state],
											future: current.future.slice(1),
										}));
										setState(next);
									}}
								>
									<Redo2 />
								</Button>
							</div>
						)}
					</footer>
				</div>
				{mode === "edit" && dockOpen && (
					<aside
						className="w-80 shrink-0 overflow-auto border-l bg-background p-4 print:hidden max-[1100px]:w-70"
						aria-label="Holding dock"
					>
						<div className="mb-2.5 flex items-center justify-between">
							<h2 className="text-base font-medium">Holding dock</h2>
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
							className="mt-4 border-t-0 pt-0 [&>h3]:text-[15px] [&>h3]:font-medium [&>h3>span]:ml-1.5 [&>h3>span]:rounded-sm [&>h3>span]:bg-secondary [&>h3>span]:px-1.75 [&>h3>span]:py-0.5 [&>p]:my-1.25 [&>p]:mb-2.5 [&>p]:text-xs [&>p]:text-muted-foreground"
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
								<div className="rounded-lg border border-dashed px-3 py-5 text-center text-[13px] leading-[1.8] text-muted-foreground">
									Everyone has a place.
									<br />
									The dock is ready when you need it.
								</div>
							) : (
								docked.map((p) => (
									<button
										className={`mb-2 flex w-full flex-col gap-0.75 rounded-lg border bg-secondary p-2.5 text-left ${selection.participantId === p.participant_id ? "outline-2 outline-ring" : ""} [&>strong]:text-[15px] [&>strong]:font-medium [&>span]:text-xs [&>span]:text-muted-foreground [&>small]:text-xs [&>small]:text-muted-foreground`}
										key={p.participant_id}
										draggable={canEdit}
										onDragStart={(e) =>
											e.dataTransfer.setData("text/plain", p.participant_id)
										}
										onClick={() => {
											setSelection({ participantId: p.participant_id, seatId: state.items[p.participant_id].seat_ids[0] ?? null });
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
									checklist: "Participant checklist",
									settings: "Allocation preferences",
									versions: "Version history",
									legend: "Map legend and help",
								}[modal ?? "legend"]
							}
						</DialogTitle>
						<DialogDescription>
							PJKIT staff workspace
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
										<div className="mt-2.5 flex flex-col gap-1.75 [&>label]:my-2.5 [&>label]:block [&>label]:text-[13px] [&>label]:text-muted-foreground [&_select]:mt-1 [&_select]:w-full [&_select]:rounded-md [&_select]:border [&_select]:border-input [&_select]:bg-background [&_select]:px-2 [&_select]:py-1.5 [&_select]:text-[15px] [&_select]:text-foreground">
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
													applyMove(person.participant_id, destination)
												}
											>
												<ArrowRightLeft /> Move / swap
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
							<div className="divide-y">
								{visible.map((p) => {
									const m = state.items[p.participant_id];
									return (
										<div
											key={p.participant_id}
											className={`flex items-center gap-3 p-2 text-[13px] ${selection.participantId === p.participant_id ? "bg-accent" : ""}`}
										>
											<button
												className="flex-1 text-left"
												onClick={() => {
																setSelection({ participantId: p.participant_id, seatId: m.seat_ids[0] ?? null });
													setModal("allocation");
												}}
											>
												<strong className="block text-base font-medium">
													{m.display_names[0]}
												</strong>
												<small className="block text-muted-foreground">
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
									onClick={() => {
										const index = visible.findIndex(
											(p) => p.participant_id === selection.participantId,
										);
										const participant = visible[
											(index - 1 + visible.length) % visible.length
										];
										if (participant) selectParticipant(participant.participant_id);
									}}
								>
									Previous
								</Button>
								<Button
									variant="outline"
									disabled={!visible.length}
									onClick={() => {
										const index = visible.findIndex(
											(p) => p.participant_id === selection.participantId,
										);
										const participant = visible[(index + 1) % visible.length];
										if (participant) selectParticipant(participant.participant_id);
									}}
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
														setTimeline({ past: [], future: [] });
														setSelection({ participantId: null, seatId: null });
									setDockOpen(false);
									setMode("read");
									setModal(null);
									toast.success(
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
									<div
										key={tier}
										className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]"
									>
										<span
											className={`inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-border ${TIER_STYLES[tier].cell.split(" hover:")[0]}`}
										/>
										<span>{label}</span>
									</div>
								))}
								<div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
									<span className="inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-dashed border-border bg-background" />{" "}
									Empty seat · available
								</div>
								<div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
									<span className="inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-[color-mix(in_oklab,var(--destructive)_35%,var(--border))] bg-[repeating-linear-gradient(135deg,transparent,transparent_4px,var(--muted)_4px,var(--muted)_6px)] text-destructive">
										×
									</span>{" "}
									Building structure · unavailable
								</div>
							</div>
							<section>
								<h3 className="mb-2.25 text-[13px] font-semibold">
									Participant indicators
								</h3>
								<div className="grid gap-2 sm:grid-cols-2">
									<div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
										<span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
											<Accessibility />
										</span>{" "}
										Accessible seating required
									</div>
									<div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
										<span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
											<Star />
										</span>{" "}
										Elderly participant
									</div>
									<div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
										<span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
											<StickyNote />
										</span>{" "}
										Staff note recorded
									</div>
								</div>
							</section>
							<div className="grid gap-1.75 rounded-lg bg-muted p-3 text-xs leading-[1.6] [&>strong]:text-[13px]">
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

				</DialogContent>
			</Dialog>
		</main>
	);
}
