import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import ts from "typescript";

const require = createRequire(import.meta.url);
const source = fs.readFileSync(
  new URL("../src/lib/production-service.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, esModuleInterop: true },
}).outputText;
const mod = { exports: {} };
new Function("require", "exports", "module", compiled)(
  (name) =>
    name === "server-only" || name === "next/headers" ? {} : require(name),
  mod.exports,
  mod,
);

test("frontend adapter launches the production Python package and loads event data", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "seat-service-"));
  const previous = process.env.SEAT_PLAN_DB;
  process.env.SEAT_PLAN_DB = path.join(directory, "plans.sqlite3");
  try {
    const result = await mod.exports.runProduction({ command: "setup" });
    assert.equal(result.floor_plan.rows.length, 16);
    assert.equal(result.floor_plan.total_seats, 256);
    assert.ok(result.registrations > 0);
    const invalid = await mod.exports.runProduction({ command: "unknown" });
    assert.equal(invalid.status, "error");
  } finally {
    if (previous === undefined) delete process.env.SEAT_PLAN_DB;
    else process.env.SEAT_PLAN_DB = previous;
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
