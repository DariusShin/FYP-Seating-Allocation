import { SeatDashboard } from "@/components/seat/seat-dashboard";
import { loadAllocationResult } from "@/lib/allocation";

export const dynamic = "force-dynamic";

export default async function SeatPage() {
  const result = await loadAllocationResult();
  return <SeatDashboard initialResult={result} />;
}
