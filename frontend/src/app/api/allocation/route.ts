import { NextResponse } from "next/server";

import { loadAllocationResult } from "@/lib/allocation";

export const runtime = "nodejs";
// Always serve the newest allocation — the public seat view polls this
// endpoint to pick up admin regenerations.
export const dynamic = "force-dynamic";

export async function GET() {
  const result = await loadAllocationResult();
  return NextResponse.json(result, {
    headers: { "Cache-Control": "no-store" },
  });
}
