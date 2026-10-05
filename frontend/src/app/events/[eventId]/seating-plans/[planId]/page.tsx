import { identity } from "@/lib/production-service";
import { seatRouteWorkspace } from "@/lib/seat-route-workspace";
import { SeatDashboard } from "@/components/seat/seat-dashboard";

export const dynamic = "force-dynamic";
export default async function PlanPage({
  params,
  searchParams,
}: {
  params: Promise<{ eventId: string; planId: string }>;
  searchParams: Promise<{ seat?: string | string[] }>;
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
  const { seat } = await searchParams;
  const selectedSeat =
    typeof seat === "string" &&
    workspace.base.floor_plan.rows.some((r) =>
      r.seats.some((s) => s.seat_id === seat),
    )
      ? seat
      : null;
  return (
    <SeatDashboard
      key={`${eventId}:${planId}:${workspace.revision}`}
      initialResult={workspace.base}
      initialWorkspace={workspace}
      initialMode="edit"
      initialSeat={selectedSeat}
    />
  );
}
