"use client";
import { PanelRightClose } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { WorkingState, SeatSelection, LocationFormatter } from "./types";
export function HoldingDock({
  state,
  docked,
  selection,
  canEdit,
  location,
  onClose,
  sendToDock,
  selectParticipant,
}: {
  state: WorkingState;
  docked: WorkingState["participants"];
  selection: SeatSelection;
  canEdit: boolean;
  location: LocationFormatter;
  onClose: () => void;
  sendToDock: (id: string) => void;
  selectParticipant: (id: string) => void;
}) {
  return (
    <aside
      className="w-80 shrink-0 overflow-auto border-l bg-background p-4 print:hidden max-[1100px]:w-70"
      aria-label="Holding dock"
    >
      <div className="mb-2.5 flex items-center justify-between">
        <h2 className="text-base font-medium">Holding dock</h2>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Close holding dock"
          onClick={onClose}
        >
          <PanelRightClose />
        </Button>
      </div>
      <section
        className="mt-4 border-t-0 pt-0 [&>h3]:text-[15px] [&>h3]:font-medium [&>h3>span]:ml-1.5 [&>h3>span]:rounded-sm [&>h3>span]:bg-secondary [&>h3>span]:px-1.75 [&>h3>span]:py-0.5 [&>p]:my-1.25 [&>p]:mb-2.5 [&>p]:text-xs [&>p]:text-muted-foreground"
        onDragOver={(e) => {
          if (canEdit) e.preventDefault();
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          sendToDock(e.dataTransfer.getData("text/plain"));
        }}
      >
        <h3>
          Holding dock <span>{docked.length}</span>
        </h3>
        <p>Drop allocations here while rearranging.</p>
        {docked.length === 0 ? (
          <div className="rounded-lg border border-dashed px-3 py-5 text-center text-[13px] leading-[1.8] text-muted-foreground">
            Everyone has a place.
            <br />
            The dock is ready when you need it.
          </div>
        ) : (
          docked.map((p) => (
            <button
              className={`mb-2 flex w-full flex-col gap-0.75 rounded-lg border bg-secondary p-2.5 text-left ${selection.participantId === p.participant_id ? "outline-2 outline-ring" : ""} [&>strong]:text-[15px] [&>strong]:font-medium [&>span]:text-xs [&>span]:text-muted-foreground [&>small]:text-xs [&>small]:text-muted-foreground`}
              key={p.participant_id}
              draggable={canEdit}
              onDragStart={(e) =>
                e.dataTransfer.setData("text/plain", p.participant_id)
              }
              onClick={() => selectParticipant(p.participant_id)}
            >
              <strong>{state.items[p.participant_id].display_names[0]}</strong>
              <span>
                {p.contribution_tier === "EMPEROR"
                  ? "Pair · 2 seats"
                  : "Individual · 1 seat"}
              </span>
              <small>
                {state.items[p.participant_id].dock_reason ||
                  "Awaiting placement"}{" "}
                · from{" "}
                {location(state.items[p.participant_id].previous_seat_ids)}
              </small>
            </button>
          ))
        )}
      </section>
    </aside>
  );
}
