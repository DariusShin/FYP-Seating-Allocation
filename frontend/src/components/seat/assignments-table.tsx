"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { Assignment, TierName } from "@/lib/allocation-types";

import { CATEGORY_LABELS, formatRM, seatNumber, TIER_STYLES } from "./seat-theme";

type TierFilter = "ALL" | TierName;

const PAGE_SIZE = 15;

export function AssignmentsTable({
  assignments,
  seatsPerRow,
  selectedId,
  onSelect,
}: {
  assignments: Assignment[];
  seatsPerRow: number;
  selectedId: string | null;
  onSelect: (participantId: string | null) => void;
}) {
  const [filter, setFilter] = useState<TierFilter>("ALL");
  const [page, setPage] = useState(0);

  const visible = useMemo(
    () =>
      filter === "ALL"
        ? assignments
        : assignments.filter((a) => a.contribution_tier === filter),
    [assignments, filter],
  );

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const start = currentPage * PAGE_SIZE;
  const paged = visible.slice(start, start + PAGE_SIZE);

  function changeFilter(value: TierFilter) {
    setFilter(value);
    setPage(0);
  }

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-3">
        <CardTitle className="text-sm">
          Participants ({visible.length})
        </CardTitle>
        <Tabs value={filter} onValueChange={(value) => changeFilter(value as TierFilter)}>
          <TabsList className="h-8">
            <TabsTrigger className="h-6 px-2 text-xs" value="ALL">
              All
            </TabsTrigger>
            <TabsTrigger className="h-6 px-2 text-xs" value="EMPEROR">
              Emperor
            </TabsTrigger>
            <TabsTrigger className="h-6 px-2 text-xs" value="BODHI">
              Bodhi
            </TabsTrigger>
            <TabsTrigger className="h-6 px-2 text-xs" value="MERIT">
              Merit
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-card">
              <tr className="border-b text-muted-foreground">
                <th className="py-2 pr-2 font-medium">ID</th>
                <th className="py-2 pr-2 font-medium">Name</th>
                <th className="py-2 pr-2 font-medium">Tier</th>
                <th className="py-2 pr-2 text-right font-medium">Contribution</th>
                <th className="py-2 pr-2 font-medium">Category</th>
                <th className="py-2 pr-2 font-medium">Seats</th>
                <th className="py-2 pr-2 font-medium">Flags</th>
                <th className="py-2 pr-2 text-right font-medium">Penalty</th>
                <th className="py-2 font-medium">Moved</th>
              </tr>
            </thead>
            <tbody>
              {paged.map((assignment) => {
                const tier = TIER_STYLES[assignment.contribution_tier];
                const selected = assignment.participant_id === selectedId;
                const guest = assignment.seats
                  .map((seat) => seat.display_name)
                  .find((name) => name !== assignment.full_name);
                return (
                  <tr
                    key={assignment.participant_id}
                    onClick={() =>
                      onSelect(selected ? null : assignment.participant_id)
                    }
                    className={cn(
                      "cursor-pointer border-b border-border/60 transition-colors hover:bg-muted/50",
                      selected && "bg-muted",
                    )}
                  >
                    <td className="py-1.5 pr-2 font-mono text-muted-foreground">
                      {assignment.participant_id}
                    </td>
                    <td className="py-1.5 pr-2 font-medium">
                      {assignment.full_name}
                      {guest && (
                        <span className="text-muted-foreground"> + {guest}</span>
                      )}
                    </td>
                    <td className="py-1.5 pr-2">
                      <Badge variant="outline" className={cn("font-normal", tier.badge)}>
                        {tier.label}
                      </Badge>
                    </td>
                    <td className="py-1.5 pr-2 text-right tabular-nums">
                      {formatRM(assignment.contribution_amount_rm)}
                    </td>
                    <td className="py-1.5 pr-2 text-muted-foreground">
                      {CATEGORY_LABELS[assignment.participant_category]}
                    </td>
                    <td
                      className="py-1.5 pr-2 tabular-nums"
                      title={assignment.seat_ids.join(" ")}
                    >
                      {assignment.seats
                        .map((seat) =>
                          seatNumber(
                            seat.row_number,
                            seat.priority_rank,
                            seatsPerRow,
                          ),
                        )
                        .sort((a, b) => a - b)
                        .join(" + ")}
                    </td>
                    <td className="py-1.5 pr-2">
                      {assignment.is_monk && "☸ "}
                      {assignment.is_elderly && "★ "}
                      {assignment.requires_accessible_seat && "♿"}
                    </td>
                    <td className="py-1.5 pr-2 text-right tabular-nums">
                      {assignment.penalty.weighted.total}
                    </td>
                    <td className="py-1.5">
                      {assignment.moved === null
                        ? "—"
                        : assignment.moved
                          ? "↻ yes"
                          : "kept"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 pt-3 text-xs text-muted-foreground">
          <span className="tabular-nums">
            {visible.length === 0
              ? "No participants"
              : `Showing ${start + 1}–${start + paged.length} of ${visible.length}`}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={currentPage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="size-4" />
              Prev
            </Button>
            <span className="tabular-nums">
              Page {currentPage + 1} of {pageCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={currentPage >= pageCount - 1}
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            >
              Next
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
