"use client";

import { useMemo, useState } from "react";
import { BarChart3, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";

import { AssignmentsTable } from "./assignments-table";
import { ParticipantDialog } from "./participant-dialog";
import { SeatLegend } from "./seat-legend";
import { SeatMap } from "./seat-map";
import { HIGHLIGHT_OPTIONS, type HighlightMode } from "./seat-theme";
import { StatsSidebar } from "./stats-sidebar";
import { WeightControls } from "./weight-controls";

export function SeatDashboard({
  initialResult,
}: {
  initialResult: AllocationResult;
}) {
  const [result, setResult] = useState(initialResult);
  const [highlight, setHighlight] = useState<HighlightMode>("none");
  const [showNames, setShowNames] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statsOpen, setStatsOpen] = useState(false);
  const [participantsOpen, setParticipantsOpen] = useState(false);

  const assignmentBySeat = useMemo(() => {
    const map = new Map<string, Assignment>();
    for (const assignment of result.assignments) {
      for (const seatId of assignment.seat_ids) {
        map.set(seatId, assignment);
      }
    }
    return map;
  }, [result.assignments]);

  const selected = useMemo(
    () =>
      result.assignments.find((a) => a.participant_id === selectedId) ?? null,
    [result.assignments, selectedId],
  );

  const summary = result.input_summary;

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80">
          <div className="flex w-full flex-wrap items-center justify-between gap-2 px-4 py-3">
            <div>
              <h1 className="text-lg font-semibold leading-tight">
                Seat Allocation
              </h1>
              <p className="text-xs text-muted-foreground">
                {result.case_study} · {summary.required_seat_count}/
                {summary.total_seat_count} seats filled ·{" "}
                {summary.empty_seat_count} empty ·{" "}
                {result.unassigned_participants.length} unassigned
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                onClick={() => setParticipantsOpen(true)}
              >
                <Users className="size-4" />
                Participants
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                onClick={() => setStatsOpen(true)}
              >
                <BarChart3 className="size-4" />
                Statistics
              </Button>
              <a
                href="/my-seat"
                className="text-xs text-muted-foreground underline-offset-2 hover:underline"
              >
                Guest view →
              </a>
              <Badge className="bg-emerald-600 text-white hover:bg-emerald-600 dark:bg-emerald-500">
                {result.solver.status}
              </Badge>
              <Badge variant="outline" className="font-normal">
                {result.floor_plan.row_count} rows ·{" "}
                {result.floor_plan.seats_per_row} seats/row
              </Badge>
            </div>
          </div>
        </header>

        <main className="w-full px-4 py-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
            <aside className="w-full space-y-4 lg:sticky lg:top-20 lg:max-h-[calc(100vh-6rem)] lg:w-80 lg:shrink-0 lg:overflow-y-auto lg:pb-4">
              <div>
                <h2 className="text-sm font-semibold">Configuration</h2>
                <p className="text-xs text-muted-foreground">
                  Set what matters most, then regenerate the plan.
                </p>
              </div>

              <WeightControls result={result} onResult={setResult} />

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Display options</CardTitle>
                  <CardDescription className="text-xs">
                    Change how the map is drawn — this does not re-run the
                    solver.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-1.5">
                    <Label
                      htmlFor="highlight"
                      className="text-xs text-muted-foreground"
                    >
                      Highlight
                    </Label>
                    <Select
                      value={highlight}
                      onValueChange={(value) =>
                        setHighlight(value as HighlightMode)
                      }
                    >
                      <SelectTrigger
                        id="highlight"
                        size="sm"
                        className="w-full text-xs"
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {HIGHLIGHT_OPTIONS.map((option) => (
                          <SelectItem
                            key={option.value}
                            value={option.value}
                            className="text-xs"
                          >
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center justify-between">
                    <Label
                      htmlFor="show-names"
                      className="text-xs text-muted-foreground"
                    >
                      Show names
                    </Label>
                    <Switch
                      id="show-names"
                      checked={showNames}
                      onCheckedChange={setShowNames}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Legend</CardTitle>
                </CardHeader>
                <CardContent>
                  <SeatLegend />
                </CardContent>
              </Card>
            </aside>

            <div className="min-w-0 flex-1">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Hall Seat Map</CardTitle>
                  <CardDescription className="text-xs">
                    {summary.required_seat_count} occupied ·{" "}
                    {summary.empty_seat_count} empty · aisle between positions{" "}
                    {result.floor_plan.aisle_after_position} and{" "}
                    {result.floor_plan.aisle_after_position + 1} · front rows
                    fill first · seats fill outward from the aisle · click a seat
                    for details
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SeatMap
                    result={result}
                    assignmentBySeat={assignmentBySeat}
                    showNames={showNames}
                    highlight={highlight}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                  />
                </CardContent>
              </Card>
            </div>
          </div>

          <p className="pt-6 pb-4 text-center text-[11px] text-muted-foreground">
            Rendered from the CP-SAT solver output · objective{" "}
            {result.solver.objective_value.toLocaleString("en-MY")} · proven{" "}
            {result.solver.status} with gap {result.solver.optimality_gap} ·{" "}
            {result.solver.engine}
          </p>
        </main>

        <ParticipantDialog
          assignment={selected}
          onOpenChange={(open) => {
            if (!open) setSelectedId(null);
          }}
        />

        <Dialog open={statsOpen} onOpenChange={setStatsOpen}>
          <DialogContent className="max-h-[85vh] gap-4 overflow-y-auto sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Generation statistics</DialogTitle>
              <DialogDescription>
                Distribution, solver metrics, and the weighted penalty breakdown
                for the current plan.
              </DialogDescription>
            </DialogHeader>
            <StatsSidebar result={result} />
          </DialogContent>
        </Dialog>

        <Dialog open={participantsOpen} onOpenChange={setParticipantsOpen}>
          <DialogContent className="max-h-[85vh] gap-4 overflow-y-auto sm:max-w-4xl">
            <DialogHeader>
              <DialogTitle>Participants</DialogTitle>
              <DialogDescription>
                Every assignment in the current plan. Click a row for details.
              </DialogDescription>
            </DialogHeader>
            <AssignmentsTable
              assignments={result.assignments}
              seatsPerRow={result.floor_plan.seats_per_row}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
