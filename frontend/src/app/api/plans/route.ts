import { NextResponse } from "next/server";
import { identity, runProduction, sameOrigin } from "@/lib/production-service";
export const runtime = "nodejs";
export async function GET() {
	const user = await identity();
	if (user?.role !== "admin")
		return NextResponse.json(
			{ error: "Administrative access required" },
			{ status: 403 },
		);
	return NextResponse.json(
		await runProduction({ command: "history", event_id: user.event_id }),
	);
}
export async function POST(request: Request) {
	const user = await identity();
	if (user?.role !== "admin" || !sameOrigin(request))
		return NextResponse.json(
			{ error: "Administrative access required" },
			{ status: 403 },
		);
	try {
		const body = await request.json();
		const allowed = new Set([
			"command",
			"plan_version_id",
			"validation_revision",
			"assignments",
		]);
		if (
			!body ||
			typeof body !== "object" ||
			Array.isArray(body) ||
			Object.keys(body).some((k) => !allowed.has(k)) ||
			!["manual", "submit", "approve", "publish", "reject", "get"].includes(
				body.command,
			)
		)
			return NextResponse.json(
				{ error: { message: "Invalid plan operation" } },
				{ status: 400 },
			);
		const result = await runProduction<{ status: string }>({
			...body,
			event_id: user.event_id,
			actor: user.actor,
		});
		return NextResponse.json(result, {
			status: result.status === "error" ? 422 : 200,
		});
	} catch (cause) {
		return NextResponse.json(
			{ error: { message: String(cause) } },
			{ status: 400 },
		);
	}
}
