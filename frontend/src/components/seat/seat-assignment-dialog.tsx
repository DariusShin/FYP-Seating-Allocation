"use client";

import { useState } from "react";
import { ArrowRightLeft, UserMinus, UserRoundPlus } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";
import {
  placeParticipant,
  type EditOutcome,
  type SeatPlacements,
} from "@/lib/seat-editor";
import { ParticipantPicker } from "./participant-picker";
import { formatRM, TIER_STYLES } from "./seat-theme";

export function SeatAssignmentDialog({
  seatId,
  result,
  placements,
  assignments,
  onClose,
  onCommit,
  onRemove,
}: {
  seatId: string;
  result: AllocationResult;
  placements: SeatPlacements;
  assignments: Assignment[];
  onClose: () => void;
  onCommit: (outcome: EditOutcome) => void;
  onRemove: (id: string) => void;
}) {
  const current = assignments.find((a) => a.seat_ids.includes(seatId));
  const [pendingId, setPendingId] = useState<string | null>(null);
  const pending = assignments.find((a) => a.participant_id === pendingId);
  const preview = pendingId
    ? placeParticipant(result, placements, pendingId, seatId)
    : null;
  const error = preview && "error" in preview ? preview.error : null;
  const options = [...assignments]
    .filter((a) => a.participant_id !== current?.participant_id)
    .sort(
      (a, b) =>
        a.seat_ids.length - b.seat_ids.length ||
        a.full_name.localeCompare(b.full_name),
    );
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Seat {seatId}</DialogTitle>
          <DialogDescription>
            Assign, move or remove a participant. Emperor registrations always
            move together.
          </DialogDescription>
        </DialogHeader>
        {current ? (
          <div className="flex flex-col gap-3 rounded-lg border bg-muted/40 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium">{current.full_name}</p>
                <p className="text-xs text-muted-foreground">
                  {current.participant_id} · {current.seat_ids.join(" + ")}
                </p>
              </div>
              <Badge variant="outline">
                {TIER_STYLES[current.contribution_tier].label}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              {formatRM(current.contribution_amount_rm)}
              {current.requires_accessible_seat &&
                " · Accessible seating required"}
              {current.allocation_type === "EMPEROR_PAIR" && " · 2 seats"}
            </p>
          </div>
        ) : (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <UserRoundPlus className="size-4" />
            This seat is available.
          </p>
        )}
        <Separator />
        <div className="flex flex-col gap-2">
          <Label htmlFor="assign-participant">
            {current ? "Replace or swap participant" : "Assign participant"}
          </Label>
          <ParticipantPicker
            id="assign-participant"
            participants={options}
            value={pendingId}
            onChange={setPendingId}
          />
          <p className="text-xs text-muted-foreground">
            {assignments.filter((a) => !a.seat_ids.length).length} unassigned ·
            Search all registrations
          </p>
        </div>
        {pending && !error && (
          <Alert>
            <ArrowRightLeft />
            <AlertDescription>
              {current
                ? pending.seat_ids.length
                  ? `${current.full_name} will move to ${pending.seat_ids.join(" + ")}.`
                  : `${current.full_name} will return to the unassigned list.`
                : `${pending.full_name} will move here${pending.seat_ids.length ? ` from ${pending.seat_ids.join(" + ")}` : ""}.`}
            </AlertDescription>
          </Alert>
        )}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <DialogFooter className="sm:justify-between">
          {current && (
            <Button
              variant="destructive"
              onClick={() => onRemove(current.participant_id)}
            >
              <UserMinus data-icon="inline-start" />
              Remove{current.seat_ids.length === 2 ? " pair" : " assignment"}
            </Button>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={!preview || Boolean(error)}
              onClick={() => {
                if (preview) onCommit(preview);
              }}
            >
              Apply
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
