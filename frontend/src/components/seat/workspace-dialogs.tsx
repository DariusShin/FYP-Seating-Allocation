"use client";
import { ArrowRightLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { eligible } from "./helpers";
import type { ManualHistory } from "@/lib/manual-history";
import { AllocationDetails } from "./allocation-details";
import { ParticipantChecklist } from "./participant-checklist";
import { MapLegend } from "./map-legend";
import { WeightControls } from "./weight-controls";
import { LocalHistoryPanel } from "./local-history-panel";
import type {
  WorkingState,
  Workspace,
  AllocationResult,
  Preference,
  SeatSelection,
  SeatModal,
  SeatCellWithRow,
  LocationFormatter,
  PlanVersion,
  DetailChanges,
} from "./types";
export function WorkspaceDialogs({
  modal,
  setModal,
  state,
  workspace,
  base,
  selection,
  error,
  busy,
  generationBlocked,
  history,
  canEdit,
  cells,
  names,
  location,
  destination,
  setDestination,
  applyMove,
  sendToDock,
  onMarkAbsent,
  repair,
  onSaveDetails,
  visible,
  filter,
  setFilter,
  query,
  setQuery,
  selectParticipant,
  dirty,
  regenerate,
  versions,
  onRestore,
  onDelete,
}: {
  modal: SeatModal;
  setModal: (value: SeatModal) => void;
  state: WorkingState;
  workspace: Workspace | null;
  base: AllocationResult;
  selection: SeatSelection;
  error: string;
  busy: boolean;
  generationBlocked: boolean;
  history: ManualHistory;
  canEdit: boolean;
  cells: SeatCellWithRow[];
  names: Record<string, string>;
  location: LocationFormatter;
  destination: string;
  setDestination: (value: string) => void;
  applyMove: (pid: string, sid: string) => void;
  sendToDock: (pid: string) => void;
  onMarkAbsent: (pid: string) => void;
  repair: (preferences: Preference[]) => Promise<void>;
  onSaveDetails: (details: DetailChanges) => Promise<boolean>;
  visible: WorkingState["participants"];
  filter: string;
  setFilter: (value: string) => void;
  query: string;
  setQuery: (value: string) => void;
  selectParticipant: (id: string) => void;
  dirty: boolean;
  regenerate: (preferences: Preference[]) => Promise<void>;
  versions: PlanVersion[];
  onRestore: (state: WorkingState) => void;
  onDelete: () => Promise<void>;
}) {
  const person = state.participants.find(
    (p) => p.participant_id === selection.participantId,
  );
  const item = selection.participantId
    ? state.items[selection.participantId]
    : undefined;
  return (
    <Dialog
      open={!!modal}
      onOpenChange={(open) => {
        if (!open) setModal(null);
      }}
    >
      <DialogContent
        className={
          modal === "checklist"
            ? "sm:max-w-3xl max-h-[85vh] overflow-auto"
            : "max-h-[85vh] overflow-auto"
        }
      >
        <DialogHeader>
          <DialogTitle>
            {
              {
                allocation: "Allocation details",
                checklist: "Participant checklist",
                settings: "Allocation preferences",
                versions: "Version history",
                history: "Local history · this browser",
                legend: "Map legend and help",
              }[modal ?? "legend"]
            }
          </DialogTitle>
          <DialogDescription>PJKIT staff workspace</DialogDescription>
        </DialogHeader>
        {modal === "allocation" && (
          <>
            {error && (
              <p role="alert" className="text-destructive">
                {error}
              </p>
            )}
            {person && item ? (
              <>
                <AllocationDetails
                  key={person.participant_id}
                  person={person}
                  item={item}
                  location={location(item.seat_ids)}
                  busy={busy || !history.ready}
                  onClose={() => setModal(null)}
                  onSave={onSaveDetails}
                />
                {canEdit && eligible(person) && (
                  <div className="mt-2.5 flex flex-col gap-1.75 [&>label]:my-2.5 [&>label]:block [&>label]:text-[13px] [&>label]:text-muted-foreground [&_select]:mt-1 [&_select]:w-full [&_select]:rounded-md [&_select]:border [&_select]:border-input [&_select]:bg-background [&_select]:px-2 [&_select]:py-1.5 [&_select]:text-[15px] [&_select]:text-foreground">
                    <label>
                      Move / swap destination
                      <select
                        aria-label="Move or swap destination"
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                      >
                        <option value="">Choose a seat…</option>
                        {cells
                          .filter((s) => !s.is_blocked)
                          .map((s) => (
                            <option key={s.seat_id} value={s.seat_id}>
                              {location([s.seat_id])} ·{" "}
                              {names[s.seat_id] || "Empty"}
                            </option>
                          ))}
                      </select>
                    </label>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!destination}
                      onClick={() =>
                        applyMove(person.participant_id, destination)
                      }
                    >
                      <ArrowRightLeft /> Move / swap
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!item.seat_ids.length}
                      onClick={() => sendToDock(person.participant_id)}
                    >
                      Send to holding dock
                    </Button>
                    <Button variant="destructive" size="sm" disabled={item.attendance_status === "ABSENT"}
                      onClick={() => onMarkAbsent(person.participant_id)}>
                      Mark {person.contribution_tier === "EMPEROR" ? "pair" : "participant"} absent
                    </Button>
                    {item.attendance_status === "ABSENT" && <p className="text-sm text-destructive">Absent — excluded from repair and regeneration. Assigning a seat will ask to restore attendance.</p>}
                  </div>
                )}
              </>
            ) : (
              <p>Select a registration to view its details.</p>
            )}
          </>
        )}

        {modal === "checklist" && (
          <ParticipantChecklist
            state={state}
            visible={visible}
            selection={selection}
            filter={filter}
            setFilter={setFilter}
            query={query}
            setQuery={setQuery}
            location={location}
            selectParticipant={selectParticipant}
          />
        )}
        {modal === "settings" && (
          <>
            <p className="text-sm">
              Preferences affect future generation. Existing manual work is kept
              in the saved working draft. Regeneration is secondary to manual
              maintenance.
            </p>
            <WeightControls
              result={base}
              hasDraft={dirty || !!workspace?.saved_at}
              onGenerate={regenerate}
              onRepair={repair}
              hasAbsences={Object.values(state.items).some((item) => item.attendance_status === "ABSENT")}
              attendanceChanged={Object.entries(state.items).some(([pid, item]) => (item.attendance_status ?? "PRESENT") !== (base.source_request?.attendance?.[pid] ?? "PRESENT"))}
            />
          </>
        )}
        {modal === "history" && workspace && (
          <LocalHistoryPanel
            history={history}
            workspace={workspace}
            current={state}
            disabled={busy || generationBlocked}
            onRestore={onRestore}
            onDelete={onDelete}
          />
        )}
        {modal === "versions" && (
          <div className="space-y-2">
            {versions.map((v) => (
              <div className="rounded border p-3 text-sm" key={v.id}>
                <strong>{v.state}</strong> ·{" "}
                {new Date(v.created).toLocaleString()}
                <p className="text-xs text-muted-foreground">{v.id}</p>
              </div>
            ))}
          </div>
        )}
        {modal === "legend" && <MapLegend />}
      </DialogContent>
    </Dialog>
  );
}
