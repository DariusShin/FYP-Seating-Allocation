"use client";
import { Button } from "@/components/ui/button";
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
  return (
    <>
      <label className="flex gap-2 text-sm">
        Filter
        <select
          className="border p-1"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          {Object.entries({
            all: "All registrations",
            dock: "Unseated / in dock",
            note: "Has note",
            changed: "Changed today",
          }).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <input
        className="border rounded p-2"
        aria-label="Search checklist"
        placeholder="Search registered or displayed names"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="divide-y">
        {visible.map((p) => {
          const m = state.items[p.participant_id];
          return (
            <div
              key={p.participant_id}
              className={`flex items-center gap-3 p-2 text-[13px] ${selection.participantId === p.participant_id ? "bg-accent" : ""}`}
            >
              <button
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
      <div className="flex gap-2">
        <Button
          variant="outline"
          disabled={!visible.length}
          onClick={() => {
            const index = visible.findIndex(
              (p) => p.participant_id === selection.participantId,
            );
            const participant =
              visible[(index - 1 + visible.length) % visible.length];
            if (participant) selectParticipant(participant.participant_id);
          }}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          disabled={!visible.length}
          onClick={() => {
            const index = visible.findIndex(
              (p) => p.participant_id === selection.participantId,
            );
            const participant = visible[(index + 1) % visible.length];
            if (participant) selectParticipant(participant.participant_id);
          }}
        >
          Next
        </Button>
      </div>
    </>
  );
}
