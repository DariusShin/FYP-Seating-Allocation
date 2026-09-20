import { SeatDashboard } from "@/components/seat/seat-dashboard";
import { GenerateDraft } from "@/components/seat/generate-draft";
import { loadAllocationResult } from "@/lib/allocation";
import { identity } from "@/lib/production-service";
export const dynamic = "force-dynamic";
export default async function SeatPage() {
	if ((await identity())?.role !== "admin")
		return (
			<main className="p-8">
				Sign in as an event administrator through the host platform.
			</main>
		);
	const result = await loadAllocationResult();
	return result ? <SeatDashboard initialResult={result} /> : <GenerateDraft />;
}
