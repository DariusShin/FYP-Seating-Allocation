import "server-only";
import { notFound } from "next/navigation";
import { runProduction, type Identity } from "./production-service";
import type { Workspace } from "./workspace";

/** Read the active draft without opening/replacing another staff member's workspace. */
export async function seatRouteWorkspace(
  user: Identity,
  eventId: string,
  planId: string,
) {
  if (eventId !== user.event_id) notFound();
  const workspace = await runProduction<Workspace | null>({
    command: "workspace_load",
    event_id: eventId,
  });
  if (
    !workspace ||
    workspace.base.event_id !== eventId ||
    workspace.base.plan_version_id !== planId
  )
    notFound();
  return {
    ...workspace,
    history_scope: { actor: user.actor, event_id: user.event_id },
  };
}
