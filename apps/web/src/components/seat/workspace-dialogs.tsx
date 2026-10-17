"use client";
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
import type {
  WorkingState,
  Workspace,
  AllocationResult,
  Preference,
  SeatSelection,
  SeatModal,
  LocationFormatter,
  DetailChanges,
} from "./types";
export function WorkspaceDialogs({
  modal,
  setModal,
  state,
  workspace,
  base,
  selection,
  busy,
  history,
  canEdit,
  location,
  sendToDock,
  onMarkAbsent,
  onRestoreAttendance,
  onSetAttendance,
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
}: {
  modal: SeatModal;
  setModal: (value: SeatModal) => void;
  state: WorkingState;
  workspace: Workspace | null;
  base: AllocationResult;
  selection: SeatSelection;
  busy: boolean;
  history: ManualHistory;
  canEdit: boolean;
  location: LocationFormatter;
  sendToDock: (pid: string) => void;
  onMarkAbsent: (pid: string) => void;
  onRestoreAttendance: (pid: string) => void;
  onSetAttendance: (pid: string, status: "PRESENT" | "ABSENT") => void;
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
                legend: "Map legend and help",
              }[modal ?? "legend"]
            }
          </DialogTitle>
          {modal !== "allocation" && (
            <DialogDescription>PJKIT staff workspace</DialogDescription>
          )}
        </DialogHeader>
        {modal === "allocation" && (
          <>
            {person && item ? (
              <>
                <AllocationDetails
                  key={person.participant_id}
                  person={person}
                  item={item}
                  location={location(item.seat_ids)}
                  busy={busy || !history.ready}
                  canEdit={canEdit && eligible(person)}
                  onSave={onSaveDetails}
                  onSeatPrepared={(seat_prepared) =>
                    void onSaveDetails({
                      display_names: item.display_names,
                      note: item.note,
                      seat_prepared,
                    })
                  }
                  onSetAttendance={(status) =>
                    onSetAttendance(person.participant_id, status)
                  }
                />
                {canEdit && eligible(person) && (
                  <div className="mt-2.5 flex flex-col gap-1.75">
                    <Button
                      disabled={!item.seat_ids.length}
                      onClick={() => sendToDock(person.participant_id)}
                    >
                      Send to holding dock
                    </Button>
                    {item.attendance_status === "ABSENT" ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            onRestoreAttendance(person.participant_id)
                          }
                        >
                          Restore to present
                        </Button>
                        <p className="text-sm text-destructive">
                          Absent — excluded from repair and regeneration.
                          Restore to present to place this registration again.
                        </p>
                      </>
                    ) : (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => onMarkAbsent(person.participant_id)}
                      >
                        Mark{" "}
                        {person.contribution_tier === "EMPEROR"
                          ? "pair"
                          : "participant"}{" "}
                        absent
                      </Button>
                    )}
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
        {modal === "legend" && <MapLegend />}
      </DialogContent>
    </Dialog>
  );
}
