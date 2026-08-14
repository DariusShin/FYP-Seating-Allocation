import { spawn } from "child_process";
import { promises as fs } from "fs";
import os from "os";
import path from "path";

import { NextResponse } from "next/server";

export const runtime = "nodejs";
// A CP-SAT optimality proof can take tens of seconds.
export const maxDuration = 320;

interface SolveRequestBody {
  weights: Record<string, unknown>;
  previous_allocation: { participant_id: string; seat_ids: string[] }[];
}

const WEIGHT_KEYS = [
  "priority_seat_weight",
  "category_zone_weight",
  "movement_weight",
  "activeness_weight",
] as const;

function repoRoot(): string {
  return process.env.SEAT_SOLVER_ROOT ?? path.resolve(process.cwd(), "..");
}

function pythonExecutable(root: string): string {
  if (process.env.SEAT_SOLVER_PYTHON) return process.env.SEAT_SOLVER_PYTHON;
  return process.platform === "win32"
    ? path.join(root, ".venv", "Scripts", "python.exe")
    : path.join(root, ".venv", "bin", "python");
}

function runSolver(
  python: string,
  args: string[],
  cwd: string,
): Promise<{ code: number | null; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(python, args, { cwd, windowsHide: true });
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code, stderr }));
  });
}

export async function POST(request: Request) {
  let body: SolveRequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { status: "error", error: { code: "INVALID_INPUT", message: "invalid JSON body" } },
      { status: 400 },
    );
  }

  const weights: Record<string, number> = {};
  for (const key of WEIGHT_KEYS) {
    const value = body.weights?.[key];
    if (typeof value !== "number" || !Number.isInteger(value) || value < 0 || value > 100) {
      return NextResponse.json(
        {
          status: "error",
          error: {
            code: "INVALID_INPUT",
            message: `weight ${key} must be an integer between 0 and 100`,
          },
        },
        { status: 400 },
      );
    }
    weights[key] = value;
  }

  if (!Array.isArray(body.previous_allocation)) {
    return NextResponse.json(
      {
        status: "error",
        error: {
          code: "INVALID_INPUT",
          message: "previous_allocation must be an array of participant seat mappings",
        },
      },
      { status: 400 },
    );
  }

  const root = repoRoot();
  const python = pythonExecutable(root);
  const workDir = await fs.mkdtemp(path.join(os.tmpdir(), "seat-solve-"));
  const configPath = path.join(workDir, "solver_config.json");
  const previousPath = path.join(workDir, "previous_allocation.json");
  const outputPath = path.join(workDir, "result.json");

  try {
    const baseConfig = JSON.parse(
      await fs.readFile(path.join(root, "config", "solver_config.json"), "utf-8"),
    );
    baseConfig.weights = weights;
    await fs.writeFile(configPath, JSON.stringify(baseConfig, null, 2));
    await fs.writeFile(
      previousPath,
      JSON.stringify(
        {
          schema_version: "1.0.0",
          allocations: body.previous_allocation.map((entry) => ({
            participant_id: String(entry.participant_id),
            seat_ids: entry.seat_ids.map(String),
          })),
        },
        null,
        2,
      ),
    );

    const { code, stderr } = await runSolver(
      python,
      [
        "-m",
        "seat_solver.cli",
        "solve",
        "--participants",
        path.join(root, "data", "mock_participants.json"),
        "--floor-plan",
        path.join(root, "data", "floor_plan.json"),
        "--previous-allocation",
        previousPath,
        "--config",
        configPath,
        "--output",
        outputPath,
      ],
      root,
    );

    let result: unknown;
    try {
      result = JSON.parse(await fs.readFile(outputPath, "utf-8"));
    } catch {
      return NextResponse.json(
        {
          status: "error",
          error: {
            code: "SOLVER_UNKNOWN",
            message: `solver produced no output (exit ${code}): ${stderr.slice(0, 500)}`,
          },
        },
        { status: 500 },
      );
    }
    // The CLI writes structured error documents too; pass them through with
    // an HTTP status the client can branch on.
    const ok = (result as { status?: string }).status === "success";
    if (ok) {
      // Publish the regenerated plan so the public seat view (which polls
      // /api/allocation) sees the update. Best-effort: the admin dashboard
      // already receives the result in this response.
      await fs
        .writeFile(
          path.join(root, "output", "live_allocation_result.json"),
          JSON.stringify(result, null, 2),
        )
        .catch(() => {});
    }
    return NextResponse.json(result, { status: ok ? 200 : 422 });
  } catch (cause) {
    return NextResponse.json(
      {
        status: "error",
        error: {
          code: "SOLVER_UNKNOWN",
          message: cause instanceof Error ? cause.message : String(cause),
        },
      },
      { status: 500 },
    );
  } finally {
    await fs.rm(workDir, { recursive: true, force: true }).catch(() => {});
  }
}
