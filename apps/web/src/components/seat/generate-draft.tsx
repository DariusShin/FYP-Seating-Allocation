"use client";
import { Armchair } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { HallMap } from "./hall-map";
import { MapLoadingOverlay } from "./map-loading-overlay";
import { SeatDashboard } from "./seat-dashboard";
import type { Workspace } from "./types";
import type { AllocationResult } from "./types";

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
    <main className="flex h-dvh flex-col overflow-hidden bg-background text-[15px] text-foreground print:h-auto">
      <header className="flex shrink-0 items-center gap-3 border-b px-5.5 py-2.5 max-[1100px]:px-3 max-[700px]:flex-wrap max-[700px]:gap-2 print:hidden">
        <Link
          href="/event"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Events
        </Link>
        <div className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
          <Armchair size={20} />
        </div>
        <div>
          <h1 className="text-base font-semibold">PJKIT · Seating workspace</h1>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            2026 梁皇寶懺大法會
          </p>
        </div>
      </header>
      <div className="flex min-h-13.5 shrink-0 items-center gap-4 border-b px-5.5 py-2 text-sm text-muted-foreground max-[1100px]:gap-2 max-[1100px]:px-3 print:hidden">
        <span className="whitespace-nowrap rounded-md border border-border bg-background px-2.5 py-1.25 font-medium text-foreground">
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
      <section className="flex min-h-0 flex-1" aria-label="Seating map">
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
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
          <footer className="flex min-h-10.5 shrink-0 items-center justify-between gap-2.5 border-t px-3.75 py-2 text-xs text-muted-foreground">
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
