import { NextResponse } from "next/server";
import { identity, runProduction, sameOrigin } from "@/lib/production-service";
export const runtime = "nodejs";
export const maxDuration = 330;
export async function POST(request: Request) {
	const user = await identity();
	if ((user?.role !== "admin" && user?.role !== "staff") || !sameOrigin(request) || (new URL(request.url).searchParams.has("event_id") && new URL(request.url).searchParams.get("event_id") !== user.event_id))
		return NextResponse.json(
			{ error: { message: "Administrative access required" } },
			{ status: 403 },
		);
	try {
		const body = await request.json();
		const allowed = new Set([
			"generation_mode",
			"preferences",
			"preference_profile_version",
		]);
		if (
			!body ||
			typeof body !== "object" ||
			Array.isArray(body) ||
			Object.keys(body).some((k) => !allowed.has(k)) ||
			!Array.isArray(body.preferences) ||
			body.preferences.length !== 3 ||
			body.preference_profile_version !== "ranked-v1" ||
			![
				"INITIAL",
				"REGENERATE_DRAFT",
			].includes(body.generation_mode)
		) {
			return NextResponse.json(
				{
					error: {
						code: "INVALID_INPUT",
						message:
							"Send a mode and ranked-v1 preferences; raw weights and seat-map baselines are not accepted.",
					},
				},
				{ status: 400 },
			);
		}
		const result = await runProduction<{ status: string }>({
			...body,
			command: "solve",
			event_id: user.event_id,
			actor: user.actor,
		});
		return NextResponse.json(result, {
			status: result.status === "error" ? 422 : 200,
		});
	} catch (cause) {
		return NextResponse.json(
			{
				error: {
					message: cause instanceof Error ? cause.message : "Invalid request",
				},
			},
			{ status: 400 },
		);
	}
}
