"use client";
import { Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Workspace, SeatMode } from "./types";
import { savedTime } from "./helpers";
export function WorkspaceToolbar({
  generationBlocked,
  published,
  mode,
  busy,
  dirty,
  workspace,
  registrationCount,
  dockCount,
  presentDockCount = dockCount,
  canUndo,
  historyReady,
  onUndo,
  onEdit,
  onSave,
  onReview,
  onDock,
}: {
  generationBlocked: boolean;
  published: boolean;
  mode: SeatMode;
  busy: boolean;
  dirty: boolean;
  workspace: Workspace | null;
  registrationCount: number;
  dockCount: number;
  presentDockCount?: number;
  canUndo: boolean;
  historyReady: boolean;
  onUndo: () => void;
  onEdit: () => void;
  onSave: () => void;
  onReview: () => void;
  onDock: () => void;
}) {
  return (
    <section
      inert={generationBlocked}
      className="flex min-h-13.5 shrink-0 items-center gap-4 border-b px-5.5 py-2 text-sm text-muted-foreground max-[1100px]:gap-2 max-[1100px]:px-3 print:hidden"
    >
      <span
        className={`whitespace-nowrap rounded-md border bg-background px-2.5 py-1.25 font-medium text-foreground ${mode === "edit" ? "bg-secondary" : ""} `}
      >
        {published ? "Published" : "Draft"} ·{" "}
        {mode === "read" ? "Read mode" : "Edit mode"}
      </span>
      <span role="status">
        {busy
          ? "Working…"
          : dirty
            ? "Unsaved changes"
            : workspace?.saved_at
              ? `Saved ${savedTime(workspace.saved_at)}`
              : "Generated draft"}
      </span>
      <span className="text-muted-foreground max-[1100px]:hidden">
        {registrationCount} paid registrations · {dockCount} in dock
      </span>
      <div className="ml-auto flex gap-2">
        {mode === "edit" && (
          <Button size="sm" variant="outline" onClick={onDock} disabled={busy}>
            Holding dock ({dockCount})
          </Button>
        )}
        {mode !== "edit" ? (
          <Button size="sm" disabled={busy} onClick={onEdit}>
            {published ? "Start revision" : "Edit plan"}
          </Button>
        ) : (
          <>
            <Button
              size="sm"
              variant="outline"
              aria-label="Undo last change"
              disabled={!canUndo}
              onClick={onUndo}
            >
              <Undo2 />
              Undo last change
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy || !dirty}
              onClick={onSave}
            >
              Save draft
            </Button>
            <Button
              size="sm"
              disabled={busy || !historyReady || presentDockCount > 0}
              onClick={onReview}
            >
              Submit for review
            </Button>
          </>
        )}
      </div>
    </section>
  );
}
