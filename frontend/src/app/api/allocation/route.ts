import { NextResponse } from "next/server";
import { identity, runProduction } from "@/lib/production-service";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
	const user = await identity();
	if (!user)
		return NextResponse.json(
			{
				status: "unauthorized",
				message: "Sign in through the event platform.",
			},
			{ status: 401 },
		);
	// Administrators may preview an individual; participants are always scoped by their signed identity.
	const participant =
		user.role === "participant"
			? user.participant_id
			: new URL(request.url).searchParams.get("participant");
	return NextResponse.json(
		await runProduction({
			command: "public",
			event_id: user.event_id,
			participant_id: participant,
		}),
		{ headers: { "Cache-Control": "no-store" } },
	);
}
