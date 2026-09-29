import { identity } from "@/lib/production-service";
import { VenueDisplay } from "@/components/public/venue-display";
export const dynamic = "force-dynamic";
export default async function VenuePage() {
    if ((await identity())?.role !== "admin")
        return <main className="p-8">Sign in as venue staff to open the published display.</main>;
    return <VenueDisplay />;
}
