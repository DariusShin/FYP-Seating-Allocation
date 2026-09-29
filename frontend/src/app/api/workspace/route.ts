import { NextResponse } from "next/server";
import { identity, runProduction, sameOrigin } from "@/lib/production-service";
export const runtime = "nodejs";
export async function GET(request: Request) {
    const user = await identity();
    if (user?.role !== "admin" || (new URL(request.url).searchParams.has("event_id") && new URL(request.url).searchParams.get("event_id") !== user.event_id))
        return NextResponse.json({ error: { message: "Administrative access required" } }, { status: 403 });
    return NextResponse.json(await runProduction({ command: "workspace_load", event_id: user.event_id }));
}
export async function POST(request: Request) {
    const user = await identity();
    if (user?.role !== "admin" || !sameOrigin(request) || (new URL(request.url).searchParams.has("event_id") && new URL(request.url).searchParams.get("event_id") !== user.event_id))
        return NextResponse.json({ error: { message: "Administrative access required" } }, { status: 403 });
    try {
        const body = await request.json();
        const opening = body?.command === "workspace_open";
        if (!body || (opening
            ? (body.plan_version_id !== undefined && typeof body.plan_version_id !== "string")
            : (!["workspace_save", "workspace_publish"].includes(body.command) || !Number.isInteger(body.revision) || typeof body.plan_version_id !== "string")))
            return NextResponse.json({ error: { message: "Invalid working draft operation" } }, { status: 400 });
        const result = await runProduction<{
            status?: string;
        }>({ command: body.command, revision: body.revision, plan_version_id: body.plan_version_id, state: body.state, event_id: user.event_id, actor: user.actor });
        return NextResponse.json(result, { status: result?.status === "error" ? 422 : 200 });
    }
    catch {
        return NextResponse.json({ error: { message: "Unable to open, save, or publish this draft. Please try again." } }, { status: 500 });
    }
}
