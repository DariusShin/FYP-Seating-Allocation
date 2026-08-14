"use client";

import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
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
  const weighted = assignment?.penalty.weighted;

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

        {assignment && tier && weighted && (
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
              {assignment.is_monk && <Badge variant="outline">☸ Monastic</Badge>}
              {assignment.is_elderly && (
                <Badge variant="outline">★ Elderly</Badge>
              )}
              {assignment.requires_accessible_seat && (
                <Badge variant="outline">♿ Accessible</Badge>
              )}
            </div>

            <div className="space-y-1.5">
              <Stat label="Seats" value={assignment.seat_ids.join(" + ")} />
              {assignment.pair_priority !== null && (
                <Stat
                  label="Pair priority"
                  value={`#${assignment.pair_priority}`}
                />
              )}
              <Stat
                label="Events (last 2 yrs)"
                value={String(assignment.events_joined_last_2_years)}
              />
              <Stat
                label="Previous seats"
                value={
                  assignment.previous_seat_ids.length
                    ? assignment.previous_seat_ids.join(" + ")
                    : "—"
                }
              />
              {assignment.moved !== null && (
                <Stat
                  label="Moved"
                  value={assignment.moved ? "↻ Yes" : "No (kept)"}
                />
              )}
            </div>

            <Separator />

            <div className="space-y-1.5">
              <Stat
                label="Weighted penalty"
                value={String(weighted.total)}
              />
              <Stat
                label="care / area / moves / activity"
                value={`${weighted.priority_seat} / ${weighted.category_zone} / ${weighted.movement} / ${weighted.activeness}`}
              />
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
