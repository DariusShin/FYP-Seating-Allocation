"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { WorkingState, SeatSelection, LocationFormatter } from "./types";
export function ParticipantChecklist({
  state,
  visible,
  selection,
  filter,
  setFilter,
  query,
  setQuery,
  location,
  selectParticipant,
}: {
  state: WorkingState;
  visible: WorkingState["participants"];
  selection: SeatSelection;
  filter: string;
  setFilter: (value: string) => void;
  query: string;
  setQuery: (value: string) => void;
  location: LocationFormatter;
  selectParticipant: (id: string) => void;
}) {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(visible.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const start = (currentPage - 1) * pageSize;
  const pageParticipants = visible.slice(start, start + pageSize);

  return (
    <>
      <div className="flex items-center gap-3">
        <Select
          value={filter}
          onValueChange={(value) => {
            setPage(1);
            setFilter(value);
          }}
        >
          <SelectTrigger
            aria-label="Filter participants"
            className="w-44 shrink-0 max-[480px]:w-36"
          >
            <SelectValue placeholder="Filter participants" />
          </SelectTrigger>
          <SelectContent>
            {Object.entries({
              all: "All registrations",
              dock: "Unseated / in dock",
              note: "Has note",
              changed: "Changed today",
            }).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          type="search"
          className="min-w-0 flex-1"
          aria-label="Search checklist"
          placeholder="Search registered or displayed names"
          value={query}
          onChange={(e) => {
            setPage(1);
            setQuery(e.target.value);
          }}
        />
      </div>
      <div className="divide-y">
        {pageParticipants.map((p) => {
          const m = state.items[p.participant_id];
          return (
            <div
              key={p.participant_id}
              className={`flex items-center gap-3 p-2 text-[13px] ${selection.participantId === p.participant_id ? "bg-accent" : ""}`}
            >
              <button
                type="button"
                aria-label={`Highlight seats for ${m.display_names[0]}`}
                className="flex-1 text-left"
                onClick={() => selectParticipant(p.participant_id)}
              >
                <strong className="block text-base font-medium">
                  {m.display_names[0]}
                </strong>
                <small className="block text-muted-foreground">
                  {p.full_name} · {location(m.seat_ids)} ·{" "}
                  {p.registration_status}
                </small>
              </button>
            </div>
          );
        })}
        {!visible.length && <p>No matching participants.</p>}
      </div>
      <nav
        className="flex flex-wrap items-center justify-between gap-2"
        aria-label="Participant pagination"
      >
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {visible.length
            ? `Showing ${start + 1}–${Math.min(start + pageSize, visible.length)} of ${visible.length} participants`
            : "0 participants"}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            aria-label="Previous participant page"
            disabled={currentPage === 1}
            onClick={() => setPage(currentPage - 1)}
          >
            Previous
          </Button>
          <span className="text-sm" aria-live="polite">
            Page {currentPage} of {pageCount}
          </span>
          <Button
            variant="outline"
            aria-label="Next participant page"
            disabled={currentPage === pageCount}
            onClick={() => setPage(currentPage + 1)}
          >
            Next
          </Button>
        </div>
      </nav>
    </>
  );
}
