"use client";
import Link from "next/link";
import { Armchair, Search, Users, Settings2, MapPinned } from "lucide-react";
import { Button } from "@/components/ui/button";
import { venuePath } from "./helpers";
import type {
  WorkingState,
  SeatSelection,
  SeatModal,
  LocationFormatter,
} from "./types";
export function WorkspaceHeader({
  state,
  selection,
  query,
  setQuery,
  matches,
  people,
  location,
  selectParticipant,
  generationBlocked,
  historyReady,
  setModal,
  loadVersions,
  eventId,
}: {
  state: WorkingState;
  selection: SeatSelection;
  query: string;
  setQuery: (query: string) => void;
  matches: Set<string>;
  people: WorkingState["participants"];
  location: LocationFormatter;
  selectParticipant: (id: string) => void;
  generationBlocked: boolean;
  historyReady: boolean;
  setModal: (modal: SeatModal) => void;
  loadVersions: () => Promise<void>;
  eventId: string;
}) {
  return (
    <header className="flex shrink-0 items-center gap-3 border-b px-5.5 py-2.5 max-[1100px]:px-3 max-[700px]:flex-wrap max-[700px]:gap-2 print:hidden">
      <Link
        href="/event"
        className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
      >
        ← Events
      </Link>
      <div className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
        <Armchair size={20} />
      </div>
      <div>
        <h1 className="text-base font-semibold">
          PJKIT{" "}
          <span className="ml-2 text-sm font-normal text-muted-foreground max-[1100px]:hidden">
            Seating workspace
          </span>
        </h1>
        <p className="mt-0.5 text-[13px] text-muted-foreground">
          2026 梁皇寶懺大法會 · Staff workspace
        </p>
      </div>
      <div
        inert={generationBlocked}
        className="relative z-30 ml-auto w-[min(340px,28vw)] max-[1100px]:w-[min(280px,30vw)] max-[700px]:order-3 max-[700px]:ml-0 max-[700px]:w-full"
      >
        <label className="flex h-9.5 items-center gap-2 rounded-lg border border-input bg-background px-2.5 text-muted-foreground focus-within:outline-2 focus-within:outline-ring focus-within:outline-offset-2">
          <Search aria-hidden="true" className="size-4 shrink-0" />
          <input
            aria-label="Search participants by name or ID"
            placeholder="Search participants · 搜尋姓名"
            value={query}
            className="min-w-0 flex-1 bg-transparent text-[13px] text-foreground outline-none placeholder:text-muted-foreground"
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                const firstMatch = people.find((p) =>
                  matches.has(p.participant_id),
                );
                if (firstMatch) selectParticipant(firstMatch.participant_id);
              }
            }}
          />
          {query && (
            <button
              type="button"
              aria-label="Clear participant search"
              className="grid size-6 shrink-0 place-items-center rounded text-lg hover:bg-muted"
              onClick={() => setQuery("")}
            >
              ×
            </button>
          )}
        </label>
        {query.trim() && (
          <div
            className="absolute inset-x-0 top-[calc(100%+7px)] max-h-[min(60vh,440px)] overflow-auto rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-xl"
            role="listbox"
            aria-label="Matching participants"
          >
            <p
              className="px-2 py-1.5 text-[11px] text-muted-foreground"
              aria-live="polite"
            >
              {matches.size} matches
            </p>
            {people
              .filter((p) => matches.has(p.participant_id))
              .slice(0, 8)
              .map((p) => (
                <button
                  type="button"
                  role="option"
                  aria-selected={selection.participantId === p.participant_id}
                  key={p.participant_id}
                  className="flex w-full flex-col gap-0.5 rounded-md p-2 text-left hover:bg-accent hover:text-accent-foreground aria-selected:bg-accent"
                  onClick={() => selectParticipant(p.participant_id)}
                >
                  <span className="text-[13px] font-medium">
                    {state.items[p.participant_id].display_names[0]}
                  </span>
                  <small className="text-[11px] text-muted-foreground">
                    {p.participant_id} ·{" "}
                    {location(state.items[p.participant_id].seat_ids)}
                  </small>
                </button>
              ))}
            {matches.size === 0 && (
              <span className="block p-2 text-[11px] text-muted-foreground">
                No matching participants
              </span>
            )}
            {matches.size > 8 && (
              <span className="block p-2 text-[11px] text-muted-foreground">
                Type more to narrow results
              </span>
            )}
          </div>
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        disabled={!historyReady || generationBlocked}
        onClick={() => setModal("history")}
      >
        Local history
      </Button>
      <nav
        className="ml-auto flex items-center gap-1 max-[1100px]:ml-0 max-[1100px]:gap-0 max-[700px]:ml-auto"
        aria-label="Workspace"
      >
        <Button
          variant="ghost"
          size="sm"
          className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
          onClick={() => setModal("legend")}
        >
          <MapPinned data-icon="inline-start" /> Legend & map guide
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
          disabled={generationBlocked}
          onClick={() => setModal("checklist")}
        >
          <Users /> Participants
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
          disabled={generationBlocked}
          onClick={() => setModal("settings")}
        >
          <Settings2 /> Settings
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
          disabled={generationBlocked}
          onClick={loadVersions}
        >
          Versions
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="max-[700px]:px-1.75 max-[700px]:text-[11px]"
          asChild
        >
          <Link href={venuePath(eventId)} target="_blank">
            Venue display ↗
          </Link>
        </Button>
      </nav>
    </header>
  );
}
