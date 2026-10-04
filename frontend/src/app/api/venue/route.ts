import { NextResponse } from "next/server";
import { identity, runProduction } from "@/lib/production-service";
export const runtime = "nodejs";
export async function GET() {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff")
    return NextResponse.json(
      { error: "Venue staff sign-in required" },
      { status: 403 },
    );
  return NextResponse.json(
    await runProduction({ command: "venue", event_id: user.event_id }),
    { headers: { "Cache-Control": "no-store" } },
  );
}
