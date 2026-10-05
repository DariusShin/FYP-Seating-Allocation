import { Undo2, Redo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Registration, SeatMode } from "./types";
export function WorkspaceFooter({
  active,
  occupied,
  total,
  blocked,
  mode,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
}: {
  active: Registration[];
  occupied: number;
  total: number;
  blocked: number;
  mode: SeatMode;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
}) {
  return (
    <footer className="flex min-h-10.5 shrink-0 items-center justify-between gap-2.5 border-t px-3.75 py-2 text-xs text-muted-foreground">
      <span>
        {active.length} registrations ·{" "}
        {active.reduce(
          (n, p) => n + (p.contribution_tier === "EMPEROR" ? 2 : 1),
          0,
        )}{" "}
        people
      </span>
      <span>
        {occupied} occupied · {total - blocked - occupied} empty · {blocked}{" "}
        blocked
      </span>
      {mode === "edit" && (
        <div>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Undo"
            disabled={!canUndo}
            onClick={onUndo}
          >
            <Undo2 />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Redo"
            disabled={!canRedo}
            onClick={onRedo}
          >
            <Redo2 />
          </Button>
        </div>
      )}
    </footer>
  );
}
