import "server-only";
import { spawn } from "node:child_process";
import path from "node:path";
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

export type Identity = {
	actor: string;
	role: "admin" | "participant";
	event_id: string;
	participant_id?: string;
	exp: number;
};

/** Host adapter: signed HttpOnly seat_session cookie. Never trust a browser actor/role field. */
export async function identity(): Promise<Identity | null> {
	const secret = process.env.SEAT_HOST_SECRET;
	if (!secret && process.env.NODE_ENV !== "production") {
		return {
			actor: "local-development",
			role: "admin",
			event_id: "PJKIT-2026",
			exp: Number.MAX_SAFE_INTEGER,
		};
	}
	if (!secret) return null;
	const token = (await cookies()).get("seat_session")?.value;
	if (!token) return null;
	const [payload, signature, extra] = token.split(".");
	if (!payload || !signature || extra) return null;
	const expected = createHmac("sha256", secret).update(payload).digest();
	const actual = Buffer.from(signature, "base64url");
	if (actual.length !== expected.length || !timingSafeEqual(actual, expected))
		return null;
	try {
		const value = JSON.parse(
			Buffer.from(payload, "base64url").toString(),
		) as Identity;
		if (
			typeof value.actor !== "string" ||
			typeof value.event_id !== "string" ||
			!["admin", "participant"].includes(value.role) ||
			typeof value.exp !== "number" ||
			value.exp <= Date.now() / 1000
		)
			return null;
		if (
			value.role === "participant" &&
			typeof value.participant_id !== "string"
		)
			return null;
		return value;
	} catch {
		return null;
	}
}

export function runProduction<T>(body: Record<string, unknown>): Promise<T> {
	const root =
		process.env.SEAT_SOLVER_ROOT ?? path.resolve(process.cwd(), "..");
	const python =
		process.env.SEAT_SOLVER_PYTHON ?? path.join(root, ".venv", "bin", "python");
	return new Promise((resolve, reject) => {
		const child = spawn(python, ["-m", "seat_solver.production.service"], {
			cwd: root,
			env: { ...process.env, PYTHONPATH: path.join(root, "src") },
		});
		let stdout = "";
		let stderr = "";
		const timer = setTimeout(() => {
			child.kill();
			reject(
				new Error("Allocation operation timed out; published plan unchanged."),
			);
		}, 330_000);
		child.stdout.on("data", (chunk) => {
			stdout += chunk;
		});
		child.stderr.on("data", (chunk) => {
			stderr += chunk;
		});
		child.on("error", (err) => {
			clearTimeout(timer);
			reject(err);
		});
		child.on("close", (code) => {
			clearTimeout(timer);
			if (code) {
				reject(
					new Error(
						`Allocation service failed (${code}): ${stderr.slice(-300)}`,
					),
				);
				return;
			}
			try {
				resolve(JSON.parse(stdout));
			} catch {
				reject(new Error("Invalid allocation service response"));
			}
		});
		child.stdin.end(JSON.stringify(body));
	});
}

export function sameOrigin(request: Request): boolean {
	const origin = request.headers.get("origin");
	if (origin === null) return true;
	try {
		const supplied = new URL(origin);
		// Next.js may normalize request.url to localhost behind its Node server.
		// Compare the browser origin to the actual incoming Host, not that internal URL.
		return (
			["http:", "https:"].includes(supplied.protocol) &&
			supplied.host === request.headers.get("host")
		);
	} catch {
		return false;
	}
}
