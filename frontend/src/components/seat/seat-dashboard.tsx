"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Armchair,
  ArrowUpRight,
  BarChart3,
  PanelLeftClose,
  PanelLeftOpen,
  RotateCcw,
  Undo2,
  Users,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";
import {
  draftAssignments,
  initialPlacements,
  placeParticipant,
  removeParticipant,
  type EditOutcome,
  type SeatPlacements,
} from "@/lib/seat-editor";
import { cn } from "@/lib/utils";
import { AssignmentsTable } from "./assignments-table";
import { ParticipantPicker } from "./participant-picker";
import { SeatAssignmentDialog } from "./seat-assignment-dialog";
import { SeatMap } from "./seat-map";
import {
  HIGHLIGHT_OPTIONS,
  TIER_STYLES,
  type HighlightMode,
} from "./seat-theme";
import { StatsSidebar } from "./stats-sidebar";
import { RegistrationEditor } from "./registration-editor";
import { PlanActions } from "./plan-actions";
import { WeightControls } from "./weight-controls";

export function SeatDashboard({
  initialResult,
}: {
  initialResult: AllocationResult;
}) {
  const [result, setResult] = useState(initialResult);
  const [placements, setPlacements] = useState(() =>
    initialPlacements(initialResult),
  );
  const [history, setHistory] = useState<SeatPlacements[]>([]);
  const [highlight, setHighlight] = useState<HighlightMode>("none");
  const [showNames, setShowNames] = useState(true);
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null);
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const [panel, setPanel] = useState<"participants" | "stats" | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [solving, setSolving] = useState(false);
  const [notice, setNotice] = useState<{
    message: string;
    error: boolean;
  } | null>(null);
  const assignments = useMemo(
    () => draftAssignments(result, placements),
    [result, placements],
  );
  const assignmentBySeat = useMemo(
    () =>
      new Map(
        assignments.flatMap((a) =>
          a.seat_ids.map((s) => [s, a] as [string, Assignment]),
        ),
      ),
    [assignments],
  );
  const baseline = useMemo(() => initialPlacements(result), [result]);
  const dirty = JSON.stringify(placements) !== JSON.stringify(baseline);
  const unassigned = assignments.filter((a) => !a.seat_ids.length);
  const blocked = result.floor_plan.rows
    .flatMap((r) => r.seats)
    .filter((s) => s.is_blocked).length;
  const occupied = assignmentBySeat.size;

  function commit(outcome: EditOutcome) {
    if ("error" in outcome) {
      setNotice({ message: outcome.error, error: true });
      return;
    }
    if (outcome.placements !== placements) {
      setHistory((h) => [...h.slice(-49), placements]);
      setPlacements(outcome.placements);
    }
    setNotice({ message: outcome.message, error: false });
    setSelectedSeatId(null);
  }
  function regenerate(next: AllocationResult) {
    setResult(next);
    setPlacements(initialPlacements(next));
    setHistory([]);
    setFocusedId(null);
    setSelectedSeatId(null);
    setNotice({
      message: "Plan version loaded. Guest seats change only after explicit publication.",
      error: false,
    });
  }
  function undo() {
    const previous = history.at(-1);
    if (previous) {
      setPlacements(previous);
      setHistory((h) => h.slice(0, -1));
      setNotice({ message: "Last change undone.", error: false });
    }
  }
  return (
    <TooltipProvider>
      <div className="flex min-h-dvh flex-col bg-background lg:h-dvh lg:overflow-hidden">
        <header className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Armchair className="size-5" />
            </span>
            <div>
              <h1 className="text-sm font-semibold">Seat allocation</h1>
              <p className="text-xs text-muted-foreground">
                PJ Kwan Inn Teng · Event workspace
              </p>
            </div>
          </div>
          <nav
            aria-label="Workspace"
            className="flex flex-wrap items-center gap-2"
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPanel("participants")}
            >
              <Users data-icon="inline-start" />
              Participants
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setPanel("stats")}>
              <BarChart3 data-icon="inline-start" />
              Statistics
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/my-seat">
                Guest view
                <ArrowUpRight data-icon="inline-end" />
              </Link>
            </Button>
          </nav>
        </header>
        <div className="flex shrink-0 flex-wrap items-center gap-x-6 gap-y-2 border-b bg-muted/30 px-4 py-2.5 text-xs lg:px-6">
          <span>
            <strong className="tabular-nums">{occupied}</strong> /{" "}
            {result.input_summary.total_seat_count - blocked} seats assigned
          </span>
          <span className="text-muted-foreground">
            {result.input_summary.total_seat_count - blocked - occupied}{" "}
            available
          </span>
          <button
            className="underline-offset-4 hover:underline"
            onClick={() => setPanel("participants")}
          >
            {unassigned.length} unassigned registrations
          </button>
          <span className="ml-auto">
            <Badge variant={dirty ? "secondary" : "outline"}>
              {dirty ? "Unsaved manual draft" : result.publication_status ?? "Draft"}
            </Badge>
          </span>
        </div>
        <div className="px-4 py-2"><PlanActions result={result} assignments={assignments} dirty={dirty} onResult={regenerate}/><RegistrationEditor key={result.plan_version_id} result={result} onResult={regenerate}/></div>
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          <aside
            className={cn(
              "shrink-0 border-b bg-sidebar lg:overflow-y-auto lg:border-r lg:border-b-0",
              sidebarOpen ? "lg:w-72" : "lg:w-14",
            )}
          >
            <div className="flex items-center justify-between p-3">
              {sidebarOpen && (
                <h2 className="pl-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Configuration
                </h2>
              )}
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label={
                  sidebarOpen
                    ? "Collapse configuration"
                    : "Expand configuration"
                }
                aria-expanded={sidebarOpen}
                onClick={() => setSidebarOpen((v) => !v)}
              >
                {sidebarOpen ? <PanelLeftClose /> : <PanelLeftOpen />}
              </Button>
            </div>
            {sidebarOpen && (
              <div className="flex flex-col gap-5 px-4 pb-5">
                <WeightControls
                  key={result.run_id}
                  result={result}
                  previousAssignments={assignments.filter(
                    (a) => a.seat_ids.length,
                  )}
                  hasDraft={dirty}
                  onResult={regenerate}
                  onSolvingChange={setSolving}
                />
                <Separator />
                <div className="flex flex-col gap-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Display
                  </h3>
                  <Label htmlFor="highlight">Highlight guests</Label>
                  <Select
                    value={highlight}
                    onValueChange={(v) => setHighlight(v as HighlightMode)}
                  >
                    <SelectTrigger id="highlight" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {HIGHLIGHT_OPTIONS.map((o) => (
                          <SelectItem key={o.value} value={o.value}>
                            {o.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="show-names">Show names</Label>
                    <Switch
                      id="show-names"
                      checked={showNames}
                      onCheckedChange={setShowNames}
                    />
                  </div>
                </div>
                <Separator />
                <div className="flex flex-col gap-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Registration tiers
                  </h3>
                  {(["EMPEROR", "MERIT", "BODHI"] as const).map((tier) => {
                    const all = assignments.filter(
                      (a) => a.contribution_tier === tier,
                    );
                    return (
                      <div
                        key={tier}
                        className="flex items-center gap-2 text-xs"
                      >
                        <span
                          className={cn(
                            "size-2 rounded-full",
                            TIER_STYLES[tier].dot,
                          )}
                        />
                        <span>
                          {TIER_STYLES[tier].label}
                          {tier === "EMPEROR" ? " · pairs" : ""}
                        </span>
                        <span className="ml-auto tabular-nums text-muted-foreground">
                          {all.filter((a) => a.seat_ids.length).length} /{" "}
                          {all.length}
                        </span>
                      </div>
                    );
                  })}
                  <p className="text-[11px] leading-relaxed text-muted-foreground">
                    ★ Elderly · ☸ Monastic · ♿ Accessible
                    <br />
                    {blocked} structural seats are blocked.
                  </p>
                </div>
              </div>
            )}
          </aside>
          <main className="min-w-0 flex-1 lg:overflow-y-auto">
            <div className="flex flex-col gap-5 p-4 lg:p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight">
                    Hall seating plan
                  </h2>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {result.floor_plan.row_count} rows ·{" "}
                    {result.floor_plan.seats_per_row} seats per row · Facing the
                    altar
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!history.length || solving}
                    onClick={undo}
                  >
                    <Undo2 data-icon="inline-start" />
                    Undo
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!dirty || solving}
                    onClick={() =>
                      commit({
                        placements: baseline,
                        message:
                          "Manual changes discarded. Published plan restored.",
                      })
                    }
                  >
                    <RotateCcw data-icon="inline-start" />
                    Discard changes
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-full max-w-sm">
                  <ParticipantPicker
                    participants={assignments}
                    value={focusedId}
                    onChange={setFocusedId}
                    placeholder="Find a participant on the map…"
                  />
                </div>
                {focusedId && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFocusedId(null)}
                  >
                    Clear
                  </Button>
                )}
              </div>
              {focusedId && !placements[focusedId]?.length && (
                <Alert>
                  <AlertDescription>
                    This participant is unassigned. Click an available seat and
                    select their name to assign them.
                  </AlertDescription>
                </Alert>
              )}
              {dirty && (
                <Alert>
                  <AlertDescription>
                    Manual draft · Changes stay in this tab. Validate and save to
                    create a reviewable version; generation may rearrange seats
                    and reassign removed registrations.
                  </AlertDescription>
                </Alert>
              )}
              {notice && (
                <Alert variant={notice.error ? "destructive" : "default"}>
                  <AlertDescription aria-live="polite">
                    {notice.message}
                  </AlertDescription>
                </Alert>
              )}
              <SeatMap
                result={result}
                assignmentBySeat={assignmentBySeat}
                showNames={showNames}
                highlight={highlight}
                selectedSeatId={selectedSeatId}
                focusedId={focusedId}
                onSelect={setSelectedSeatId}
                onMove={(id, seat) =>
                  commit(placeParticipant(result, placements, id, seat))
                }
                validateDrop={(id, seat) => {
                  const outcome = placeParticipant(
                    result,
                    placements,
                    id,
                    seat,
                  );
                  return "error" in outcome ? outcome.error : null;
                }}
                disabled={solving}
              />
              <p className="text-center text-[11px] text-muted-foreground">
                {dirty
                  ? "Manual placements have not been checked for tier order, contribution order or front-to-back packing."
                  : `Published allocation · ${result.solver.status} · ${result.assignments.length} registrations · ${result.input_summary.required_seat_count} people`}
              </p>
            </div>
          </main>
        </div>
        {selectedSeatId && (
          <SeatAssignmentDialog
            key={selectedSeatId}
            seatId={selectedSeatId}
            result={result}
            placements={placements}
            assignments={assignments}
            onClose={() => setSelectedSeatId(null)}
            onCommit={commit}
            onRemove={(id) =>
              commit({
                placements: removeParticipant(placements, id),
                message:
                  "Assignment removed. The registration is available in the participant dropdown. Undo restores it.",
              })
            }
          />
        )}
        <Dialog
          open={panel !== null}
          onOpenChange={(open) => {
            if (!open) setPanel(null);
          }}
        >
          <DialogContent
            className={cn(
              "max-h-[85dvh] overflow-y-auto",
              panel === "participants" ? "sm:max-w-5xl" : "sm:max-w-lg",
            )}
          >
            <DialogHeader>
              <DialogTitle>
                {panel === "participants"
                  ? "Participants"
                  : "Generation statistics"}
              </DialogTitle>
              <DialogDescription>
                {panel === "participants"
                  ? "Find registrations, inspect current placements and return to the map."
                  : "Metrics from the saved plan version. Unsaved manual changes are not included."}
              </DialogDescription>
            </DialogHeader>
            {panel === "participants" ? (
              <AssignmentsTable
                assignments={assignments}
                seatsPerRow={result.floor_plan.seats_per_row}
                selectedId={focusedId}
                isDraft={dirty}
                onSelect={(id) => {
                  setFocusedId(id);
                  setPanel(null);
                }}
              />
            ) : (
              <StatsSidebar result={result} />
            )}
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
