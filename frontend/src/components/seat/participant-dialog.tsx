"use client";

import { Badge } from "@/components/ui/badge";
import { Accessibility, Star } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Assignment } from "@/lib/allocation-types";

import { CATEGORY_LABELS, formatRM, TIER_STYLES } from "./seat-theme";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-medium tabular-nums">{value}</span>
    </div>
  );
}

/**
 * Modal shown when a seat (or participant row) is selected. Replaces the
 * former side panel so the seat map can use the full viewport width.
 */
export function ParticipantDialog({
  assignment,
  onOpenChange,
}: {
  assignment: Assignment | null;
  onOpenChange: (open: boolean) => void;
}) {
  const tier = assignment ? TIER_STYLES[assignment.contribution_tier] : null;

  return (
    <Dialog open={assignment !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-baseline gap-2">
            {assignment?.full_name ?? "Participant"}
            {assignment && (
              <span className="text-xs font-normal text-muted-foreground">
                {assignment.participant_id}
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            {assignment
              ? `Assigned seat${assignment.seat_ids.length > 1 ? "s" : ""} ${assignment.seat_ids.join(" + ")}`
              : ""}
          </DialogDescription>
        </DialogHeader>

        {assignment && tier && (
          <div className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="outline" className={tier.badge}>
                {tier.label}
              </Badge>
              <Badge variant="outline">
                {formatRM(assignment.contribution_amount_rm)}
              </Badge>
              <Badge variant="outline">
                {CATEGORY_LABELS[assignment.participant_category]}
              </Badge>
              {assignment.is_monk && (
                <Badge variant="outline">☸ Monastic</Badge>
              )}
              {assignment.is_elderly && (
                <Badge variant="outline" className="gap-1">
                  <Star aria-hidden="true" className="size-3.5" /> Elderly
                </Badge>
              )}
              {assignment.requires_accessible_seat && (
                <Badge
                  variant="outline"
                  className="gap-1 border-sky-700/40 text-sky-900 dark:text-sky-200"
                >
                  <Accessibility aria-hidden="true" className="size-4" />{" "}
                  Accessible seating required
                </Badge>
              )}
            </div>

            <div className="space-y-1.5">
              <Stat label="Seats" value={assignment.seat_ids.join(" + ")} />
              <Stat
                label="Events (last 2 yrs)"
                value={String(assignment.events_joined_last_2_years)}
              />
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
