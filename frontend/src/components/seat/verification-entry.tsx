"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { Workspace } from "./types";
import {
  manualHistoryFor,
  openManualHistory,
  retainManualHistory,
} from "./history-controller";
import { eligible, planPath, venuePath } from "./helpers";
import { VerificationScreen } from "./verification-screen";

export function VerificationEntry({ initial }: { initial: Workspace }) {
  const router = useRouter();
  const [history] = useState(() => manualHistoryFor(initial));
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [error, setError] = useState("");
  const startup = useRef<Promise<Workspace> | null>(null);
  useEffect(() => {
    let active = true;
    startup.current ??= openManualHistory(history, initial).then((state) => ({
      ...initial,
      state,
    }));
    void startup.current
      .then((value) => {
        if (active) setWorkspace(value);
      })
      .catch((e) => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, [history, initial]);
  const editPath = planPath(
    initial.base.event_id!,
    initial.base.plan_version_id!,
  );
  if (error)
    return (
      <main className="p-8">
        <p role="alert">{error}</p>
        <Link href={editPath}>Back to editing</Link>
      </main>
    );
  if (!workspace)
    return (
      <main className="p-8" role="status">
        Loading verification workspace…
      </main>
    );
  if (
    workspace.state.participants.some(
      (p) =>
        eligible(p) &&
        !workspace.state.items[p.participant_id]?.seat_ids.length,
    )
  )
    return (
      <main className="p-8">
        <p role="alert">
          Assign every paid registration before entering verification.
        </p>
        <Link href={editPath}>Back to editing</Link>
      </main>
    );
  return (
    <VerificationScreen
      initial={initial}
      initialState={workspace.state}
      history={history}
      onExit={async (value, seat) => {
        await retainManualHistory(value, history);
        router.push(
          `${editPath}${seat ? `?seat=${encodeURIComponent(seat)}` : ""}`,
        );
      }}
      onPublished={() => {
        toast.success(
          "Seating plan published. Venue display now uses this version.",
        );
        router.push(venuePath(initial.base.event_id!));
      }}
    />
  );
}
