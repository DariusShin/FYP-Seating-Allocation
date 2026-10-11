import { ManualHistory, equal } from "@/lib/manual-history";
import type { Workspace } from "./types";

// A route handoff keeps in-memory history available when IndexedDB has failed.
// Refreshes and other tabs recover independently through ManualHistory.open.
let retained: { workspace: Workspace; history: ManualHistory } | null = null;
function matches(workspace: Workspace) {
  const previous = retained?.workspace;
  return (
    !!previous &&
    !!workspace.history_scope &&
    retained?.history.session?.revision === workspace.revision &&
    equal(previous.history_scope, workspace.history_scope) &&
    equal(previous.base, workspace.base) &&
    previous.revision === workspace.revision &&
    equal(previous.state, workspace.state)
  );
}

export function manualHistoryFor(workspace?: Workspace) {
  return workspace && matches(workspace)
    ? retained!.history
    : new ManualHistory();
}

export async function openManualHistory(
  history: ManualHistory,
  workspace: Workspace,
) {
  await history.flush();
  if (
    retained?.history === history &&
    matches(workspace) &&
    history.ready &&
    history.session
  )
    return structuredClone(history.session.state);
  return history.open(workspace);
}

export async function retainManualHistory(
  workspace: Workspace,
  history: ManualHistory,
) {
  await history.flush();
  retained = { workspace: structuredClone(workspace), history };
}
