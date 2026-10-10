"use client";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogHeader,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { equal } from "@/lib/manual-history";
import type {
  AllocationResult,
  Preference,
  Workspace,
  WorkingState,
  SeatMode,
  SeatModal,
  SeatSelection,
  PlanVersion,
  GenerationPhase,
} from "./types";
import { HallMap } from "./hall-map";
import { MapLoadingOverlay } from "./map-loading-overlay";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceToolbar } from "./workspace-toolbar";
import { WorkspaceFooter } from "./workspace-footer";
import { WorkspaceDialogs } from "./workspace-dialogs";
import { HoldingDock } from "./holding-dock";
import {
  dock,
  eligible,
  move,
  reviewMove,
  markAbsent,
  restoreAndMove,
  floorCells,
  seatLocation,
  workspaceMapData,
  participantMatches,
  verificationPath,
  eventApi,
} from "./helpers";
import {
  manualHistoryFor,
  openManualHistory,
  retainManualHistory,
} from "./history-controller";

export function SeatDashboard({
  initialResult,
  initialWorkspace,
  initialMode = "read",
  initialSeat = null,
}: {
  initialResult: AllocationResult;
  initialWorkspace?: Workspace;
  initialMode?: SeatMode;
  initialSeat?: string | null;
}) {
  const router = useRouter();
  const [workspace, setWorkspace] = useState<Workspace | null>(
    initialWorkspace ?? null,
  );
  const [state, setState] = useState<WorkingState | null>(
    initialWorkspace?.state ?? null,
  );
  const [resume, setResume] = useState(
    initialMode !== "edit" &&
      initialWorkspace?.review?.review_status === "IN_PROGRESS",
  );
  const [mode, setMode] = useState<SeatMode>(initialMode);
  const [selection, setSelection] = useState<SeatSelection>({
    participantId: null,
    seatId: initialSeat,
  });
  const [dockOpen, setDockOpen] = useState(false);
  const draggingParticipant = useRef<string | null>(null);
  const [destination, setDestination] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [modal, setModal] = useState<SeatModal>(null);
  const [history] = useState(() => manualHistoryFor(initialWorkspace));
  useSyncExternalStore(
    history.subscribe,
    history.getSnapshot,
    history.getSnapshot,
  );
  const historyStartup = useRef<Promise<WorkingState> | null>(null);
  const [chainPreview, setChainPreview] = useState<ReturnType<
    typeof reviewMove
  > | null>(null);
  const [restorePlacement, setRestorePlacement] = useState<{ pid: string; sid: string } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [generationPhase, setGenerationPhase] =
    useState<GenerationPhase | null>(null);
  const [generationError, setGenerationError] = useState("");
  const generationInFlight = useRef(false);
  const generationPreferences = useRef<Preference[]>([]);
  const generationMode = useRef<"REGENERATE_DRAFT" | "REPAIR_ABSENCE">("REGENERATE_DRAFT");
  const generatedPlanId = useRef<string | null>(null);
  const [draftCreated, setDraftCreated] = useState(false);
  const generationBlocked = generationPhase !== null;
  async function regenerate(preferences?: Preference[], requestedMode: "REGENERATE_DRAFT" | "REPAIR_ABSENCE" = "REGENERATE_DRAFT") {
    if (generationInFlight.current) return;
    generationInFlight.current = true;
    if (preferences) {
      generationMode.current = requestedMode;
      generationPreferences.current = preferences;
      generatedPlanId.current = null;
      setDraftCreated(false);
    }
    setModal(null);
    setResume(false);
    setDockOpen(false);
    draggingParticipant.current = null;
    setBusy(true);
    setError("");
    setGenerationError("");
    setGenerationPhase(
      generatedPlanId.current ? "loading-workspace" : "generating",
    );
    try {
      if (!generatedPlanId.current) {
        if (!workspace || !state || !history.ready) throw Error("Load the saved working draft first.");
        let saved = workspace;
        if (dirty || !workspace.saved_at) {
          const capture = await history.prepareSave(state, workspace.revision);
          const saveResponse = await fetch(eventApi("/api/workspace", initialResult.event_id!), {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: "workspace_save", plan_version_id: workspace.base.plan_version_id, revision: workspace.revision, state }),
          });
          saved = await saveResponse.json();
          if (!saveResponse.ok) throw Error((saved as unknown as {error?: {message: string}}).error?.message ?? "Unable to save the repair baseline");
          await history.saved(saved, capture);
          setWorkspace(saved);
          setState(saved.state);
        }
        const response = await fetch(
          eventApi("/api/solve", initialResult.event_id!),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              generation_mode: generationMode.current,
              plan_version_id: saved.base.plan_version_id,
              revision: saved.revision,
              preference_profile_version: "ranked-v1",
              preferences: generationPreferences.current,
            }),
          },
        );
        const result = await response.json();
        if (
          !response.ok ||
          result?.status !== "success" ||
          !result.plan_version_id
        )
          throw new Error(
            result?.error?.message ??
              "Unable to generate the draft. Please try again.",
          );
        generatedPlanId.current = result.plan_version_id;
        setDraftCreated(true);
      }
      setGenerationPhase("loading-workspace");
      const response = await fetch(
        eventApi("/api/workspace", initialResult.event_id!),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            command: "workspace_open",
            plan_version_id: generatedPlanId.current,
          }),
        },
      );
      const value = await response.json();
      if (!response.ok || !value?.base || !value?.state)
        throw new Error(
          value?.error?.message ?? "Unable to open the new draft",
        );
      setWorkspace(value);
      setState(await openManualHistory(history, value));
      setSelection({ participantId: null, seatId: null });
      setMode("read");
      setGenerationPhase(null);
      toast.success("New seating draft ready. Public seating is unchanged.");
    } catch (e) {
      setGenerationError(e instanceof Error ? e.message : "Generation failed");
      setGenerationPhase("error");
    } finally {
      generationInFlight.current = false;
      setBusy(false);
    }
  }
  const [versions, setVersions] = useState<PlanVersion[]>([]);
  async function load() {
    setBusy(true);
    try {
      const r = await fetch(
        eventApi("/api/workspace", initialResult.event_id!),
        { cache: "no-store" },
      );
      const value = await r.json();
      if (!r.ok || !value) throw Error("Unable to load the working draft.");
      setWorkspace(value);
      setState(await openManualHistory(history, value));
      setResume(value.review?.review_status === "IN_PROGRESS");

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
    if (initialWorkspace) {
      historyStartup.current ??= openManualHistory(history, initialWorkspace);
      void historyStartup.current.then(setState);
      return;
    }
    const startup = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(startup);
    // Startup only; later workspace changes explicitly reopen history.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialWorkspace]);
  const dirty =
    !!workspace && JSON.stringify(state) !== JSON.stringify(workspace.state);
  const base = workspace?.base ?? initialResult;
  const cells = useMemo(() => floorCells(base.floor_plan), [base.floor_plan]);
  const mapData = state
    ? workspaceMapData(state)
    : { names: {}, owners: {}, primaryNames: {}, tiers: {}, markers: {} };
  const { names, owners } = mapData;
  const people = state?.participants ?? [];
  const active = people.filter(eligible);
  const docked = active.filter(
    (p) => !state?.items[p.participant_id].seat_ids.length,
  );
  const temporaryDocked = docked.filter((p) => state?.items[p.participant_id].attendance_status !== "ABSENT");
  const matches = state ? participantMatches(state, query) : new Set<string>();
  const canEdit =
    mode === "edit" && !busy && !generationBlocked && history.ready;
  const blocked = cells.filter((s) => s.is_blocked).length;
  const published =
    base.publication_status === "PUBLISHED" &&
    (!workspace?.saved_at || workspace.saved_at === base.published_at) &&
    !dirty;
  const location = (ids: string[]) => seatLocation(cells, ids);
  async function loadVersions() {
    try {
      const response = await fetch(eventApi("/api/plans", base.event_id!));
      if (!response.ok) throw Error("Version history unavailable");
      setVersions((await response.json()).plans);
      setModal("versions");
    } catch (e) {
      setError(String(e));
    }
  }
  function commit(next: WorkingState) {
    if (!canEdit) return;
    history.commit(next);
    setState(next);

    setError("");
  }
  function applyMove(pid: string, sid: string) {
    if (!canEdit || !state) return;
    if (state.items[pid].attendance_status === "ABSENT") {
      setModal(null);
      setRestorePlacement({ pid, sid });
      return;
    }
    try {
      const result = state.items[pid].seat_ids.length
        ? reviewMove(state, base, pid, sid)
        : { state: move(state, base, pid, sid), chain: false, description: "" };
      if (result.state === state) return;
      if (result.chain) setChainPreview(result);
      else commit(result.state);
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
    if (!workspace || !state || temporaryDocked.length || !history.ready) return;
    setBusy(true);
    setError("");
    try {
      let value = workspace;
      if (dirty) {
        const capture = await history.prepareSave(state, workspace.revision);
        const response = await fetch(
          eventApi("/api/workspace", initialResult.event_id!),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              command: "workspace_save",
              plan_version_id: base.plan_version_id,
              revision: workspace.revision,
              state,
            }),
          },
        );
        value = await response.json();
        if (!response.ok)
          throw Error(
            (value as unknown as { error?: { message: string } }).error
              ?.message ?? "Unable to save draft",
          );
        await history.saved(value, capture);
      }
      setWorkspace(value);
      setState(value.state);
      setResume(false);
      setModal(null);
      await retainManualHistory(value, history);
      router.push(
        verificationPath(value.base.event_id!, value.base.plan_version_id!),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function operation(command: "workspace_save", nextState = state) {
    if (!workspace || !nextState || !history.ready) return false;
    setBusy(true);
    setError("");
    try {
      if (!equal(history.session?.state, nextState)) {
        history.commit(nextState, "DETAILS");
        setState(nextState);
      }
      const capture = await history.prepareSave(nextState, workspace.revision);
      const response = await fetch(
        eventApi("/api/workspace", initialResult.event_id!),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            command,
            plan_version_id: base.plan_version_id,
            revision: workspace.revision,
            state: nextState,
          }),
        },
      );
      const value = await response.json();
      if (!response.ok)
        throw Error(value.error?.message ?? "Unable to save draft");
      await history.saved(value, capture);
      setWorkspace(value);
      setState(value.state);
      toast.success("Working draft saved. Public seating is unchanged.");
      return true;
    } catch (e) {
      setError(String(e));
      return false;
    } finally {
      setBusy(false);
    }
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
  function selectParticipant(participantId: string, showDetails = true) {
    setSelection({
      participantId,
      seatId: state?.items[participantId]?.seat_ids[0] ?? null,
    });
    setModal(showDetails ? "allocation" : null);
  }
  const visible = people.filter((p) => {
    const m = state?.items[p.participant_id];
    if (!m || !matches.has(p.participant_id)) return false;
    switch (filter) {
      case "dock":
        return eligible(p) && !m.seat_ids.length;
      case "absent":
        return m.attendance_status === "ABSENT";
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
      className="relative flex h-dvh flex-col overflow-hidden bg-background text-[15px] text-foreground print:h-auto"
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
      <WorkspaceHeader
        state={state}
        selection={selection}
        query={query}
        setQuery={setQuery}
        matches={matches}
        people={people}
        location={location}
        selectParticipant={selectParticipant}
        generationBlocked={generationBlocked}
        historyReady={history.ready}
        setModal={setModal}
        loadVersions={loadVersions}
        eventId={base.event_id!}
      />
      {history.warning && (
        <p
          role="status"
          className="border-b bg-amber-50 p-2 text-sm text-amber-950"
        >
          {history.warning}
        </p>
      )}
      <WorkspaceToolbar
        generationBlocked={generationBlocked}
        published={published}
        mode={mode}
        busy={busy}
        dirty={dirty}
        workspace={workspace}
        registrationCount={active.length}
        dockCount={docked.length}
        presentDockCount={temporaryDocked.length}
        canUndo={canEdit && !!history.session?.active.length}
        historyReady={history.ready}
        onUndo={() => setState(history.undo())}
        onEdit={() => setMode("edit")}
        onSave={() => operation("workspace_save")}
        onReview={submitReview}
        onDock={() => setDockOpen((v) => !v)}
      />
      {base.repair_summary && <p role="status" className="border-b px-5 py-2 text-sm">Absence repair: {base.repair_summary.moved_registrations} registrations moved · movement distance {base.repair_summary.distance_doubled / 2} · rows {base.repair_summary.scope_rows.join(", ") || "unchanged"}. {base.repair_summary.optimality_proven === false && "Valid repair found; optimality is not proven. "}Review before publishing.</p>}
      {mode === "edit" && temporaryDocked.length > 0 && (
        <p role="status" className="border-b px-5 py-2 text-sm">
          {temporaryDocked.length} participants unseated — assign every present paid registration
          before review.
        </p>
      )}
      <Dialog open={resume} onOpenChange={setResume}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Safeguard review in progress</DialogTitle>
            <DialogDescription>
              {(workspace?.review?.summary?.acked ?? 0) +
                (workspace?.review?.summary?.resolved ?? 0)}{" "}
              of{" "}
              {(workspace?.review?.summary?.acked ?? 0) +
                (workspace?.review?.summary?.resolved ?? 0) +
                (workspace?.review?.summary?.open_blocking ?? 0) +
                (workspace?.review?.summary?.open_advisory ?? 0)}{" "}
              handled in the last saved review. Resume to check the latest
              seating plan.
            </DialogDescription>
          </DialogHeader>
          <Button
            disabled={busy || !history.ready || temporaryDocked.length > 0}
            onClick={submitReview}
          >
            Resume review
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setResume(false);
              setMode("edit");
            }}
          >
            Back to editing
          </Button>
        </DialogContent>
      </Dialog>
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
          <div
            className="relative flex min-h-0 flex-1 flex-col overflow-hidden"
            aria-label="Seating map"
          >
            <div
              className="flex min-h-0 flex-1 flex-col"
              inert={generationBlocked}
              aria-busy={generationBlocked}
            >
              <HallMap
                floor={base.floor_plan}
                {...mapData}
                selected={selection.participantId}
                selectedSeat={
                  selection.participantId
                    ? (state.items[selection.participantId]?.seat_ids[0] ??
                      null)
                    : selection.seatId
                }
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
            </div>
            {generationPhase && (
              <MapLoadingOverlay
                phase={generationPhase}
                error={generationError}
                onRetry={() => void regenerate()}
                draftCreated={draftCreated}
              />
            )}
          </div>
          <WorkspaceFooter
            active={active}
            occupied={Object.keys(owners).length}
            total={cells.length}
            blocked={blocked}
            mode={mode}
            canUndo={canEdit && !!history.session?.active.length}
            canRedo={canEdit && !!history.session?.redo.length}
            onUndo={() => setState(history.undo())}
            onRedo={() => setState(history.redo())}
          />
        </div>
        {mode === "edit" && dockOpen && (
          <HoldingDock
            state={state}
            docked={docked}
            selection={selection}
            canEdit={canEdit}
            location={location}
            onClose={() => setDockOpen(false)}
            sendToDock={sendToDock}
            selectParticipant={selectParticipant}
          />
        )}
      </section>
      <WorkspaceDialogs
        modal={modal}
        setModal={setModal}
        state={state}
        workspace={workspace}
        base={base}
        selection={selection}
        error={error}
        busy={busy}
        generationBlocked={generationBlocked}
        history={history}
        canEdit={canEdit}
        cells={cells}
        names={names}
        location={location}
        destination={destination}
        setDestination={setDestination}
        applyMove={applyMove}
        sendToDock={sendToDock}
        onMarkAbsent={(pid) => {
          commit(markAbsent(state, pid));
          setDockOpen(true);
          setModal(null);
        }}
        onSaveDetails={(details) =>
          operation("workspace_save", {
            ...state,
            items: {
              ...state.items,
              [selection.participantId!]: {
                ...state.items[selection.participantId!],
                ...details,
                changed_at: new Date().toISOString(),
              },
            },
          })
        }
        visible={visible}
        filter={filter}
        setFilter={setFilter}
        query={query}
        setQuery={setQuery}
        selectParticipant={(id) => selectParticipant(id, false)}
        dirty={dirty}
        regenerate={regenerate}
        repair={(preferences) => regenerate(preferences, "REPAIR_ABSENCE")}
        versions={versions}
        onRestore={(next) => {
          history.commit(next, "RESTORE_VERSION");
          setState(next);
          setMode("edit");
          setModal(null);
        }}
        onDelete={async () => {
          if (!workspace) return;
          setBusy(true);
          try {
            setState(await history.deleteHistory(workspace));
          } finally {
            setBusy(false);
          }
        }}
      />
      <Dialog open={!!restorePlacement} onOpenChange={(open) => { if (!open) setRestorePlacement(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore attendance and assign?</DialogTitle>
            <DialogDescription>{restorePlacement && state.items[restorePlacement.pid].display_names[0]} is marked absent. Assigning this registration restores {restorePlacement && state.participants.find((p) => p.participant_id === restorePlacement.pid)?.contribution_tier === "EMPEROR" ? "both occupants" : "attendance"} to present.</DialogDescription>
          </DialogHeader>
          <Button disabled={!canEdit} onClick={() => {
            if (!restorePlacement) return;
            try {
              commit(restoreAndMove(state, base, restorePlacement.pid, restorePlacement.sid));
              setRestorePlacement(null);
              setDestination("");
            } catch (e) { setError(String(e)); setRestorePlacement(null); }
          }}>Restore to present and assign</Button>
          <Button variant="outline" onClick={() => setRestorePlacement(null)}>Cancel</Button>
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!chainPreview}
        onOpenChange={(open) => {
          if (!open) setChainPreview(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply rearrangement</DialogTitle>
            <DialogDescription>{chainPreview?.description}</DialogDescription>
          </DialogHeader>
          <Button
            disabled={!canEdit}
            onClick={() => {
              if (chainPreview) commit(chainPreview.state);
              setChainPreview(null);
            }}
          >
            Apply rearrangement
          </Button>
        </DialogContent>
      </Dialog>
    </main>
  );
}
