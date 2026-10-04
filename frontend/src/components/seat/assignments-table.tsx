"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { Assignment, TierName } from "@/lib/allocation-types";

import {
  CATEGORY_LABELS,
  formatRM,
  seatNumber,
  TIER_STYLES,
} from "./seat-theme";

type TierFilter = "ALL" | "UNASSIGNED" | TierName;

const PAGE_SIZE = 15;

export function AssignmentsTable({
  assignments,
  seatsPerRow,
  selectedId,
  onSelect,
  isDraft = false,
}: {
  isDraft?: boolean;
  assignments: Assignment[];
  seatsPerRow: number;
  selectedId: string | null;
  onSelect: (participantId: string | null) => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<TierFilter>("ALL");
  const [page, setPage] = useState(0);

  const visible = useMemo(
    () =>
      assignments.filter((a) => {
        const tierMatch =
          filter === "ALL" ||
          (filter === "UNASSIGNED"
            ? !a.seat_ids.length
            : a.contribution_tier === filter);
        const text = [
          a.full_name,
          a.participant_id,
          ...a.seats.map((s) => s.display_name),
        ]
          .join(" ")
          .toLowerCase();
        return tierMatch && text.includes(query.trim().toLowerCase());
      }),
    [assignments, filter, query],
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
        <Tabs
          value={filter}
          onValueChange={(value) => changeFilter(value as TierFilter)}
        >
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
            <TabsTrigger value="UNASSIGNED">Unassigned</TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent>
        <Input
          aria-label="Search registrations"
          placeholder="Search name, guest or ID…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(0);
          }}
          className="mb-4"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-card">
              <tr className="border-b text-muted-foreground">
                <th className="py-2 pr-2 font-medium">ID</th>
                <th className="py-2 pr-2 font-medium">Name</th>
                <th className="py-2 pr-2 font-medium">Tier</th>
                <th className="py-2 pr-2 text-right font-medium">
                  Contribution
                </th>
                <th className="py-2 pr-2 font-medium">Category</th>
                <th className="py-2 pr-2 font-medium">Seats</th>
                <th className="py-2 pr-2 font-medium">Flags</th>
                <th className="py-2 pr-2 text-right font-medium">
                  {isDraft ? "Status" : "Penalty"}
                </th>
              </tr>
            </thead>
            <tbody>
              {!paged.length && (
                <tr>
                  <td
                    colSpan={9}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No registrations match. Try another name or filter.
                  </td>
                </tr>
              )}
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
                      <button
                        type="button"
                        className="text-left underline-offset-4 hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(assignment.participant_id);
                        }}
                      >
                        {assignment.full_name}
                      </button>
                      {guest && (
                        <span className="text-muted-foreground">
                          {" "}
                          + {guest}
                        </span>
                      )}
                    </td>
                    <td className="py-1.5 pr-2">
                      <Badge
                        variant="outline"
                        className={cn("font-normal", tier.badge)}
                      >
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
                      {!assignment.seat_ids.length && "Unassigned"}
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
                      {isDraft ? "Draft" : assignment.penalty.weighted.total}
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
