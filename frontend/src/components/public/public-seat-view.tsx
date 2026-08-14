"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Armchair, CalendarClock, RefreshCw, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import type { AllocationResult, ZoneName } from "@/lib/allocation-types";

import { seatNumber, TIER_STYLES } from "../seat/seat-theme";
import { PublicSeatMap } from "./public-seat-map";

const POLL_INTERVAL_MS = 5000;

const ZONE_LABELS: Record<ZoneName, string> = {
  LEFT_OUTER: "left outer section",
  LEFT_CENTER: "left centre section",
  RIGHT_CENTER: "right centre section",
  RIGHT_OUTER: "right outer section",
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

type UpdateNotice = { at: string; seatChanged: boolean } | null;

export function PublicSeatView({
  initialResult,
  initialParticipantId,
}: {
  initialResult: AllocationResult;
  initialParticipantId: string | null;
}) {
  const [result, setResult] = useState(initialResult);
  const [participantId, setParticipantId] = useState<string | null>(
    initialParticipantId,
  );
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<UpdateNotice>(null);

  const assignment = useMemo(
    () =>
      result.assignments.find((a) => a.participant_id === participantId) ??
      null,
    [result.assignments, participantId],
  );

  const participants = useMemo(
    () =>
      [...result.assignments].sort((a, b) =>
        a.full_name.localeCompare(b.full_name),
      ),
    [result.assignments],
  );

  const mySeatIds = useMemo(
    () => new Set(assignment?.seat_ids ?? []),
    [assignment],
  );

  // Poll the allocation endpoint so an admin regeneration shows up here
  // without a manual refresh. refs keep the interval callback reading fresh
  // state without re-arming the timer every render.
  const resultRef = useRef(result);
  const assignmentRef = useRef(assignment);
  useEffect(() => {
    resultRef.current = result;
    assignmentRef.current = assignment;
  }, [result, assignment]);

  useEffect(() => {
    let inFlight = false;
    const timer = setInterval(async () => {
      if (inFlight || document.visibilityState === "hidden") return;
      inFlight = true;
      try {
        const response = await fetch("/api/allocation", { cache: "no-store" });
        if (!response.ok) return;
        const next = (await response.json()) as AllocationResult;
        if (next.status !== "success") return;
        if (next.run_id === resultRef.current.run_id) return;
        const previousSeats = assignmentRef.current?.seat_ids.join(",");
        const nextSeats = next.assignments
          .find(
            (a) =>
              a.participant_id === assignmentRef.current?.participant_id,
          )
          ?.seat_ids.join(",");
        setResult(next);
        setNotice({
          at: next.generated_at,
          seatChanged: Boolean(previousSeats) && previousSeats !== nextSeats,
        });
      } catch {
        // transient network error — try again on the next tick
      } finally {
        inFlight = false;
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  function signIn(id: string | null) {
    setParticipantId(id);
    setNotice(null);
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("participant", id);
    else url.searchParams.delete("participant");
    window.history.replaceState(null, "", url);
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div>
            <h1 className="text-lg font-semibold leading-tight">
              {result.case_study}
            </h1>
            <p className="text-xs text-muted-foreground">
              Guest seat lookup — find where you are seated
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="gap-1.5 font-normal text-muted-foreground"
            >
              <span className="relative flex size-2">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-500 opacity-60" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              Live — updates automatically
            </Badge>
            {assignment && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground"
                onClick={() => signIn(null)}
              >
                Not you? Switch
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto space-y-4 px-4 py-4">
        {!assignment ? (
          <div className="flex justify-center pt-10">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <UserRound className="size-4" />
                  Find my seat
                </CardTitle>
                <CardDescription className="text-xs">
                  Prototype sign-in: pick your name to view your assigned seat.
                  In the real flow this would come from your account or a
                  ticket QR code.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="participant" className="text-xs">
                    Your name
                  </Label>
                  <Select
                    value={pendingId ?? ""}
                    onValueChange={(value) => setPendingId(value)}
                  >
                    <SelectTrigger id="participant" className="w-full text-sm">
                      <SelectValue placeholder="Select your name…" />
                    </SelectTrigger>
                    <SelectContent className="max-h-72">
                      {participants.map((participant) => (
                        <SelectItem
                          key={participant.participant_id}
                          value={participant.participant_id}
                          className="text-sm"
                        >
                          {participant.full_name}
                          <span className="ml-1.5 text-xs text-muted-foreground">
                            {participant.participant_id}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  className="w-full"
                  disabled={!pendingId}
                  onClick={() => signIn(pendingId)}
                >
                  <Armchair />
                  View my seat
                </Button>
              </CardContent>
            </Card>
          </div>
        ) : (
          <>
            {notice && (
              <div
                className={
                  notice.seatChanged
                    ? "rounded-md border border-orange-500/40 bg-orange-500/10 p-2.5 text-xs text-orange-700 dark:text-orange-300"
                    : "rounded-md border border-emerald-600/40 bg-emerald-500/10 p-2.5 text-xs text-emerald-700 dark:text-emerald-300"
                }
              >
                <RefreshCw className="mr-1.5 inline size-3.5 align-[-2px]" />
                {notice.seatChanged
                  ? `The seating plan was regenerated at ${formatDateTime(notice.at)} and your seat has changed — please check the updated details below.`
                  : `The seating plan was regenerated at ${formatDateTime(notice.at)}. Your seat is unchanged.`}
              </div>
            )}

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Hall floor plan</CardTitle>
                  <CardDescription className="text-xs">
                    Your seat is highlighted. Facing the altar, even seat
                    numbers are on the left of the centre aisle and odd numbers
                    on the right.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <PublicSeatMap
                    result={result}
                    mySeatIds={mySeatIds}
                    assignment={assignment}
                  />
                </CardContent>
              </Card>

              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Your seat</CardTitle>
                    <CardDescription className="text-xs">
                      Welcome, {assignment.full_name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      {assignment.seats.map((seat) => (
                        <div
                          key={seat.seat_id}
                          className="rounded-lg border bg-muted/40 px-3 py-2 text-center"
                        >
                          <p className="text-2xl font-bold leading-none tabular-nums">
                            {seatNumber(
                              seat.row_number,
                              seat.priority_rank,
                              result.floor_plan.seats_per_row,
                            )}
                          </p>
                          <p className="mt-1 text-[10px] text-muted-foreground">
                            Row {seat.row_number} · {seat.seat_id}
                          </p>
                        </div>
                      ))}
                    </div>

                    <Separator />

                    <dl className="space-y-1.5 text-xs">
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Tier</dt>
                        <dd>
                          <Badge
                            variant="outline"
                            className={
                              TIER_STYLES[assignment.contribution_tier].badge
                            }
                          >
                            {TIER_STYLES[assignment.contribution_tier].label}
                          </Badge>
                        </dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Area</dt>
                        <dd className="text-right">
                          {ZONE_LABELS[assignment.seats[0].zone]}, facing the
                          altar
                        </dd>
                      </div>
                      {assignment.allocation_type === "EMPEROR_PAIR" && (
                        <div className="flex justify-between gap-2">
                          <dt className="text-muted-foreground">Guest seat</dt>
                          <dd className="text-right">
                            {assignment.seats[1]?.display_name ===
                            assignment.full_name
                              ? "Reserved next to you"
                              : `${assignment.seats[1]?.display_name} sits next to you`}
                          </dd>
                        </div>
                      )}
                      {assignment.requires_accessible_seat && (
                        <div className="flex justify-between gap-2">
                          <dt className="text-muted-foreground">
                            Accessibility
                          </dt>
                          <dd>♿ Accessible seat</dd>
                        </div>
                      )}
                      {assignment.moved === true && (
                        <div className="flex justify-between gap-2">
                          <dt className="text-muted-foreground">Note</dt>
                          <dd className="text-right text-orange-600 dark:text-orange-400">
                            Moved from {assignment.previous_seat_ids.join(", ")}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <CalendarClock className="size-4" />
                      Event details
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <dl className="space-y-1.5 text-xs">
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Event</dt>
                        <dd className="text-right font-medium">
                          {result.case_study}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Seat assigned</dt>
                        <dd className="text-right">
                          {formatDateTime(result.generated_at)}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Plan reference</dt>
                        <dd className="text-right font-mono text-[10px]">
                          {result.run_id}
                        </dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}

        <p className="pb-4 text-center text-[11px] text-muted-foreground">
          This page refreshes automatically when the organizers update the
          seating plan.
        </p>
      </main>
    </div>
  );
}
