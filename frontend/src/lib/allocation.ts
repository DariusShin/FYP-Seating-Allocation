import "server-only";
import type { AllocationResult } from "./allocation-types";
import { identity, runProduction } from "./production-service";
/** Admin draft loading is separate from the participant's published pointer. */
export async function loadAllocationResult(): Promise<AllocationResult | null> {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff") return null;
  return runProduction<AllocationResult | null>({
    command: "load",
    event_id: user.event_id,
  });
}
