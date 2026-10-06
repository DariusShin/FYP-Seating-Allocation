import { identity } from "@/lib/production-service";
import { seatRouteWorkspace } from "@/lib/seat-route-workspace";
import { VerificationEntry } from "@/components/seat/verification-entry";

export const dynamic = "force-dynamic";
export default async function VerificationPage({
  params,
}: {
  params: Promise<{ eventId: string; planId: string }>;
}) {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff")
    return (
      <main className="p-8">
        Sign in as event staff through the host platform.
      </main>
    );
  const { eventId, planId } = await params;
  const workspace = await seatRouteWorkspace(user, eventId, planId);
  return (
    <VerificationEntry
      key={`${eventId}:${planId}:${workspace.revision}`}
      initial={workspace}
    />
  );
}
