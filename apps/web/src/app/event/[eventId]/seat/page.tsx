import { notFound } from "next/navigation";
import { SeatingEntry } from "@/components/seat/seating-entry";
import { identity, runProduction } from "@/lib/production-service";
import { countsFromSetup } from "@/lib/skeleton-schedule";
import type { AllocationResult } from "@/lib/allocation-types";

export const dynamic = "force-dynamic";
export default async function EventSeatPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff")
    return (
      <main className="p-8">
        Sign in as event staff through the host platform.
      </main>
    );
  const { eventId } = await params;
  if (eventId !== user.event_id) notFound();
  const [plan, setup] = await Promise.all([
    runProduction<AllocationResult | null>({
      command: "load",
      event_id: eventId,
    }),
    runProduction<{
      floor_plan: AllocationResult["floor_plan"];
      registrations: number;
      tier_counts: { emperor_count: number; bodhi_count: number; merit_count: number };
      accessible_counts: {
        emperor_count: number;
        bodhi_count: number;
        merit_count: number;
      };
    }>({ command: "setup", event_id: eventId }),
  ]);
  return (
    <SeatingEntry
      eventId={eventId}
      hasPlan={!!plan}
      floor={setup.floor_plan}
      registrations={setup.registrations}
      skeletonCounts={countsFromSetup(setup)}
    />
  );
}
