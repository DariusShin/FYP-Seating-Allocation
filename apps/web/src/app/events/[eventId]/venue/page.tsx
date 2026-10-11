import { notFound } from "next/navigation";
import { identity } from "@/lib/production-service";
import { VenueDisplay } from "@/components/public/venue-display";

export const dynamic = "force-dynamic";
export default async function EventVenuePage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff")
    return (
      <main className="p-8">
        Sign in as venue staff to open the published display.
      </main>
    );
  const { eventId } = await params;
  if (eventId !== user.event_id) notFound();
  return <VenueDisplay eventId={eventId} />;
}
