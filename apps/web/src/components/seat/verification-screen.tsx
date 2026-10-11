"use client";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
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
import type {
  WorkingState,
  Workspace,
  AttributedEdit,
  Finding,
  Review,
} from "./types";
import {
  reviewMove,
  workspaceMapData,
  floorCells,
  eventApi,
  focusedGroups,
  restorationResolves,
  participantSeats,
  findingSeats,
  reviewSeatHighlights,
  followSelectedSeat,
} from "./helpers";

import {
  ManualHistory,
  restorationFromHistory,
  type HistoryRestoration,
} from "@/lib/manual-history";

export function VerificationScreen({
  initial,
  initialState = initial.state,
  history,
  onExit,
  onPublished,
}: {
  initial: Workspace;
  initialState?: WorkingState;
  history: ManualHistory;
  onExit: (workspace: Workspace, seat: string | null) => void | Promise<void>;
  onPublished: (workspace: Workspace) => void | Promise<void>;
}) {
  const [state, setState] = useState(initialState);
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
  useSyncExternalStore(
    history.subscribe,
    history.getSnapshot,
    history.getSnapshot,
  );
  const [selectedEdit, setSelectedEdit] = useState<string | null>(null);
  const [restoreError, setRestoreError] = useState<{
    operation: string;
    message: string;
  } | null>(null);
  const [leaving, setLeaving] = useState(false);
  const [showCandidates, setShowCandidates] = useState(false);
  const [restorePreview, setRestorePreview] = useState<{
    state: WorkingState;
    source: WorkingState;
    revision: number;
    restoration: HistoryRestoration;
  } | null>(null);
  const saved = useRef(initial);
  const latest = useRef(initialState);
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const sequence = useRef(0);
  const mounted = useRef(true);
  const dirty = state !== checkedState;
  const base = initial.base;
  const findings = review?.findings ?? [];
  const summary = review?.summary;
  const selectedFinding = findings.find((f) => f.finding_id === selected);
  const groups = focusedGroups(
    findings.filter(
      (f) =>
        (showHandled || f.status === "OPEN") &&
        (filter === "All" || f.severity === filter || f.rule_id === filter),
    ),
    review?.attribution,
  );
  const reviewSeats = useMemo(
    () => reviewSeatHighlights(review, state),
    [review, state],
  );
  const focusedEdit = review?.attribution?.groups.find(
    (g) => g.operation_id === selectedEdit,
  );
  const spotlight = new Set(
    selectedFinding
      ? [
          ...findingSeats(selectedFinding, state),
          ...(showCandidates
            ? participantSeats(
                selectedFinding.resolution_hint.swap_candidates.map(
                  (p) => p.participant_id,
                ),
                state,
              )
            : []),
        ]
      : focusedEdit
        ? participantSeats(focusedEdit.participant_ids, state)
        : [],
  );
  const cells = floorCells(base.floor_plan);
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
  const mapData = workspaceMapData(state);
  const { owners } = mapData;
  async function request(command: string, extra: Record<string, unknown> = {}) {
    const response = await fetch(eventApi("/api/workspace", base.event_id!), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        command,
        plan_version_id: saved.current.base.plan_version_id,
        revision: saved.current.revision,
        history_context:
          command === "workspace_check" || command === "workspace_ack"
            ? history.context(
                (extra.state as WorkingState | undefined) ??
                  saved.current.state,
              )
            : undefined,
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
    if (JSON.stringify(snapshot) !== JSON.stringify(saved.current.state)) {
      const capture = await history.prepareSave(
        snapshot,
        saved.current.revision,
      );
      saved.current = await request("workspace_save", { state: snapshot });
      await history.saved(saved.current, capture);
    }
  }
  async function refresh(snapshot: WorkingState, token: number) {
    if (token !== sequence.current) return;
    // Save and check share one revision stream; obsolete queued snapshots are skipped.
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
      await persist(initialState);
      const result: Review = await request("workspace_check");
      saved.current = { ...saved.current, review: result };
      if (active) {
        setReview(result);
        setCheckedState(initialState);
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
    setRestorePreview(null);
    setRestoreError(null);
    setPreview(null);
    setShowCandidates(false);
    setSelectedSeat((current) => followSelectedSeat(current, state, next));
    sequence.current++;
    latest.current = next;
    setState(next);
    setError("");
  }
  function commit(next: WorkingState) {
    history.commit(next);
    update(next);
  }
  function move(pid: string, sid: string) {
    if (stale || phase || leaving || (working && confirmPublish)) return;
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
    setSelectedEdit(null);
    setShowCandidates(false);
    setSelected(f.finding_id);
    setPulse(true);
    setMoveActor(f.resolution_hint.actor_participant_id);
    setSelectedSeat(
      state.items[f.resolution_hint.actor_participant_id]?.seat_ids[0] ??
        findingSeats(f, state)[0] ??
        null,
    );
  }
  function focusEdit(group: AttributedEdit) {
    setSelected(null);
    setSelectedEdit(group.operation_id);
    setSelectedSeat(participantSeats(group.participant_ids, state)[0] ?? null);
    setPulse(true);
    document
      .getElementById(`edit-${group.operation_id}`)
      ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  async function previewRestore(group: AttributedEdit) {
    setWorking(true);
    setRestoreError(null);
    const source = latest.current;
    const revision = saved.current.revision;
    try {
      const related = findings
        .filter((f) => group.finding_ids.includes(f.finding_id))
        .flatMap((f) => f.participants.map((p) => p.participant_id));
      const plan = restorationFromHistory(
        source,
        history.context(source),
        group.operation_id,
        related,
      );
      const candidate = plan.state;
      const result: Review = await enqueue(() =>
        request("workspace_check", {
          state: candidate,
          history_context: undefined,
        }),
      );
      if (source !== latest.current || revision !== saved.current.revision)
        throw Error("The draft changed. Preview restoration again.");
      if (
        !restorationResolves(findings, result.findings ?? [], group.finding_ids)
      )
        throw Error(
          "Restoration would leave linked findings or introduce new violations. Use the related findings to choose another correction.",
        );
      setRestorePreview({
        state: candidate,
        source,
        revision,
        restoration: plan,
      });
    } catch (e) {
      setRestoreError({ operation: group.operation_id, message: String(e) });
      setExpanded((values) => ({
        ...values,
        [`edit:${group.operation_id}`]: true,
      }));
    } finally {
      setWorking(false);
    }
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
    setLeaving(true);
    setWorking(true);
    try {
      await enqueue(async () => {
        await persist(latest.current);
        await onExit(saved.current, selectedSeat);
      });
    } catch (e) {
      setError(String(e));
      setLeaving(false);
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
        await onPublished(value);
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
      {history.warning && (
        <p role="status" className="border-b p-2 text-sm">
          {history.warning}
        </p>
      )}
      {(error || stale) && (
        <div
          role="alert"
          className="flex items-center gap-3 border-b bg-destructive/10 p-3 text-sm"
        >
          <span>
            {error ||
              "Another staff member changed the saved draft. Reload before continuing."}
          </span>
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
              disabled={
                !history.session?.active.length || stale || leaving || !!phase
              }
              onClick={() => {
                update(history.undo());
              }}
            >
              <Undo2 />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Redo"
              disabled={
                !history.session?.redo.length || stale || leaving || !!phase
              }
              onClick={() => {
                update(history.redo());
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
              disabled={
                !moveActor || !destination || stale || leaving || !!phase
              }
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
            {...mapData}
            reviewSeats={reviewSeats}
            spotlight={spotlight}
            pulse={pulse}
            selectedSeat={selectedSeat}
            validTargets={validTargets}
            editable={!stale && !phase && !leaving}
            onDrop={move}
            onAllocationDragStart={setDragging}
            onAllocationDragEnd={() => setDragging(null)}
            onSelect={(sid) => {
              const edit = review?.attribution?.groups.find(
                (g) =>
                  participantSeats(g.participant_ids, state).includes(sid) &&
                  findings.some(
                    (f) =>
                      f.status === "OPEN" &&
                      g.finding_ids.includes(f.finding_id),
                  ),
              );
              if (edit) {
                setFilter("All");
                focusEdit(edit);
                return;
              }
              const f = findings.find(
                (f) =>
                  f.status === "OPEN" && findingSeats(f, state).includes(sid),
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
              {handled} of {total} findings handled ·{" "}
              {summary?.open_blocking ?? "…"} blocking
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
            {review?.attribution?.message && (
              <p className="text-xs text-muted-foreground">
                {review.attribution.message}
              </p>
            )}
            <p className="text-xs">
              {groups.filter(([key]) => key.startsWith("edit:")).length} edit
              groups ·{" "}
              {groups.filter(([key]) => !key.startsWith("edit:")).length}{" "}
              baseline / unattributed groups
            </p>
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
            {groups.map(([actor, issues]) => {
              const edit = review?.attribution?.groups.find(
                (g) => `edit:${g.operation_id}` === actor,
              );
              return (
                <article
                  id={edit ? `edit-${edit.operation_id}` : undefined}
                  key={actor}
                  className={`rounded-lg border-l-4 border p-3 ${issues.some((f) => f.severity === "RED") ? "border-l-red-500" : "border-l-amber-500"}`}
                >
                  <h3 className="font-semibold">
                    {edit
                      ? "Introduced by this edit"
                      : "Baseline / unattributed issue"}
                  </h3>
                  {edit ? (
                    <div className="my-2 space-y-2 text-sm">
                      {edit.changes.map((c) => (
                        <p key={c.participant_id}>
                          {state.items[c.participant_id].display_names[0]}:{" "}
                          {c.before.seat_ids.join(" + ") || "Dock"} →{" "}
                          {state.items[c.participant_id].seat_ids.join(" + ") ||
                            "Dock"}
                        </p>
                      ))}
                      <p>
                        {[...new Set(issues.map((f) => f.rule_id))].join(" · ")}
                      </p>
                      {restoreError?.operation === edit.operation_id && (
                        <p role="status" className="text-destructive">
                          {restoreError.message}
                        </p>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => focusEdit(edit)}
                      >
                        Locate edit
                      </Button>{" "}
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={
                          dirty || working || stale || leaving || !!phase
                        }
                        onClick={() => previewRestore(edit)}
                      >
                        Preview restore positions
                      </Button>
                    </div>
                  ) : (
                    <p>
                      {
                        issues[0].participants.find(
                          (p) => p.participant_id === actor,
                        )?.display_name
                      }
                    </p>
                  )}

                  <p className="mb-2 text-xs text-muted-foreground">
                    {issues.length} related{" "}
                    {issues.length === 1 ? "finding" : "findings"}
                  </p>
                  {(expanded[actor]
                    ? issues
                    : edit
                      ? []
                      : [
                          issues.find((f) => f.finding_id === selected) ??
                            issues[0],
                        ]
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
                        <button
                          className="ml-2 underline"
                          onClick={() => {
                            locate(f);
                            setShowCandidates(true);
                          }}
                        >
                          Inspect correction candidates
                        </button>
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
                  {(edit || issues.length > 1) && (
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
              );
            })}
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
      <Dialog
        open={!!restorePreview}
        onOpenChange={(open) => {
          if (!open) setRestorePreview(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore previous positions</DialogTitle>
            <DialogDescription>
              Checked against every safeguard: linked findings resolve and no
              new violations are introduced. Names and notes stay current.
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm">
            This restores {restorePreview?.restoration.changes.length}{" "}
            registrations across{" "}
            {restorePreview?.restoration.operation_ids.length} connected
            placement edits together.
          </p>
          {restorePreview?.restoration.changes.map((c) => (
            <p key={c.participant_id}>
              {state.items[c.participant_id].display_names[0]} →{" "}
              {c.before.seat_ids.join(" + ")}
            </p>
          ))}
          <Button
            disabled={
              !restorePreview ||
              restorePreview.source !== state ||
              working ||
              stale ||
              leaving ||
              !!phase
            }
            onClick={() => {
              if (
                restorePreview &&
                restorePreview.source === latest.current &&
                restorePreview.revision === saved.current.revision
              ) {
                history.commit(restorePreview.state, "RESTORE_POSITIONS");
                update(restorePreview.state);
              }
            }}
          >
            Apply restoration
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
