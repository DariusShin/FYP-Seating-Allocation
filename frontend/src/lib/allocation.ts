import "server-only";

import { promises as fs } from "fs";
import path from "path";

import bundledResult from "@/data/seat_allocation_result.json";
import type { AllocationResult } from "@/lib/allocation-types";

// live_allocation_result.json is written by /api/solve whenever an admin
// regenerates the plan, so the public seat view picks up the newest
// allocation; seat_allocation_result.json comes from CLI solver runs.
const RESULT_CANDIDATES = [
  path.resolve(process.cwd(), "../output/live_allocation_result.json"),
  path.resolve(process.cwd(), "../output/seat_allocation_result.json"),
];

async function readResult(candidate: string): Promise<AllocationResult | null> {
  try {
    const parsed = JSON.parse(
      await fs.readFile(candidate, "utf-8"),
    ) as AllocationResult;
    return parsed.status === "success" ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Load the latest solver output: an explicit SEAT_RESULT_PATH wins, then the
 * most recently modified of the repository's output/ files (so both admin
 * regenerations and CLI re-runs refresh the UI), falling back to the bundled
 * snapshot so the prototype always renders.
 */
export async function loadAllocationResult(): Promise<AllocationResult> {
  if (process.env.SEAT_RESULT_PATH) {
    const pinned = await readResult(process.env.SEAT_RESULT_PATH);
    if (pinned) return pinned;
  }

  const dated: { candidate: string; mtimeMs: number }[] = [];
  for (const candidate of RESULT_CANDIDATES) {
    try {
      dated.push({ candidate, mtimeMs: (await fs.stat(candidate)).mtimeMs });
    } catch {
      // missing file — skip
    }
  }
  dated.sort((a, b) => b.mtimeMs - a.mtimeMs);
  for (const { candidate } of dated) {
    const parsed = await readResult(candidate);
    if (parsed) return parsed;
  }
  return bundledResult as unknown as AllocationResult;
}
