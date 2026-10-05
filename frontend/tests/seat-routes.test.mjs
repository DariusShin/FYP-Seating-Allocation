import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import "fake-indexeddb/auto";
import ts from "typescript";
const require = createRequire(import.meta.url);
function compile(file, load = require) {
  const mod = { exports: {} };
  const code = ts.transpileModule(
    fs.readFileSync(new URL(file, import.meta.url), "utf8"),
    {
      fileName: file,
      compilerOptions: {
        target: ts.ScriptTarget.ES2022,
        module: ts.ModuleKind.CommonJS,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
      },
    },
  ).outputText;
  new Function("require", "module", "exports", code)(load, mod, mod.exports);
  return mod.exports;
}
const helpers = compile("../src/components/seat/helpers.ts", (name) => {
  if (name === "@/lib/workspace") return compile("../src/lib/workspace.ts");
  if (name === "@/lib/verification")
    return compile("../src/lib/verification.ts");
  return require(name);
});
const historyTypes = compile("../src/lib/manual-history.ts");
const { ManualHistory, HistoryDatabase } = historyTypes;
const controller = () =>
  compile("../src/components/seat/history-controller.ts", (name) => {
    assert.equal(name, "@/lib/manual-history");
    return historyTypes;
  });
function fixture() {
  return {
    history_scope: { actor: "staff", event_id: "event" },
    base: {
      event_id: "event",
      plan_version_id: "plan",
      floor_plan: { rows: [] },
    },
    state: {
      participants: [{ participant_id: "A" }, { participant_id: "B" }],
      items: Object.fromEntries(
        ["A", "B"].map((id) => [
          id,
          {
            seat_ids: [id],
            display_names: [id],
            note: "",
            dock_reason: "",
            previous_seat_ids: [],
            changed_at: null,
          },
        ]),
      ),
    },
    revision: 0,
    saved_at: null,
  };
}
test("route handoff keeps one atomic undo and attribution when browser storage fails", async (t) => {
  const db = new HistoryDatabase(`route-${crypto.randomUUID()}`);
  t.after(() => db.delete());
  db.transaction = async () => {
    throw Error("Storage unavailable");
  };
  const history = new ManualHistory(db),
    original = fixture(),
    routes = controller();
  await history.open(original);
  const moved = structuredClone(original.state);
  [moved.items.A.seat_ids, moved.items.B.seat_ids] = [
    moved.items.B.seat_ids,
    moved.items.A.seat_ids,
  ];
  history.commit(moved);
  const capture = await history.prepareSave(moved, 0);
  const saved = { ...original, state: moved, revision: 1 };
  await history.saved(saved, capture);
  await routes.retainManualHistory(saved, history);
  const resumed = routes.manualHistoryFor(saved);
  assert.equal(resumed, history);
  assert.deepEqual(await routes.openManualHistory(resumed, saved), moved);
  assert.equal(resumed.context().edits.length, 1);
  assert.deepEqual(resumed.undo(), original.state);
  assert.match(resumed.warning, /Storage unavailable/);
});
test("route handoff rejects changes in actor, event, plan, revision, layout and registrations", async (t) => {
  const db = new HistoryDatabase(`scope-${crypto.randomUUID()}`);
  t.after(() => db.delete());
  const history = new ManualHistory(db),
    workspace = fixture(),
    routes = controller();
  await history.open(workspace);
  await routes.retainManualHistory(workspace, history);
  for (const change of [
    (w) => {
      w.history_scope.actor = "other";
    },
    (w) => {
      w.history_scope.event_id = "other";
    },
    (w) => {
      w.base.plan_version_id = "other";
    },
    (w) => {
      w.revision++;
    },
    (w) => {
      w.base.floor_plan.rows = [{ row_number: 1, seats: [] }];
    },
    (w) => {
      w.state.participants[0].age = 65;
    },
    (w) => {
      w.state.items.A.seat_ids = ["changed"];
    },
  ]) {
    const changed = structuredClone(workspace);
    change(changed);
    assert.notEqual(routes.manualHistoryFor(changed), history);
  }
  history.session.revision++;
  assert.notEqual(
    routes.manualHistoryFor(workspace),
    history,
    "an old router snapshot cannot reuse a newer controller",
  );
});
test("verification route reads the exact active plan and rejects stale or cross-event links without opening a workspace", async () => {
  const calls = [],
    workspace = fixture();
  const { seatRouteWorkspace } = compile(
    "../src/lib/seat-route-workspace.ts",
    (name) => {
      if (name === "server-only") return {};
      if (name === "next/navigation")
        return {
          notFound: () => {
            throw Error("404");
          },
        };
      assert.equal(name, "./production-service");
      return {
        runProduction: async (body) => {
          calls.push(body);
          return workspace;
        },
      };
    },
  );
  const user = { actor: "staff", event_id: "event", role: "staff" };
  const loaded = await seatRouteWorkspace(user, "event", "plan");
  assert.equal(loaded.revision, workspace.revision);
  assert.deepEqual(loaded.history_scope, workspace.history_scope);
  await assert.rejects(
    seatRouteWorkspace(user, "event", "obsolete-plan"),
    /404/,
  );
  await assert.rejects(seatRouteWorkspace(user, "other-event", "plan"), /404/);
  assert.deepEqual(
    calls,
    Array(2).fill({ command: "workspace_load", event_id: "event" }),
  );
});
test("verification page checks staff access before reading a plan", async () => {
  let user = null;
  let calls = 0;
  const page = compile(
    "../src/app/events/[eventId]/seating-plans/[planId]/verification/page.tsx",
    (name) => {
      if (name === "react/jsx-runtime") return require(name);
      if (name === "@/lib/production-service")
        return { identity: async () => user };
      if (name === "@/lib/seat-route-workspace")
        return {
          seatRouteWorkspace: async () => {
            calls++;
            return fixture();
          },
        };
      return { VerificationEntry: "VerificationEntry" };
    },
  ).default;
  const props = {
    params: Promise.resolve({ eventId: "event", planId: "plan" }),
  };
  assert.equal((await page(props)).type, "main");
  user = { role: "participant", event_id: "event" };
  assert.equal((await page(props)).type, "main");
  assert.equal(calls, 0);
  user.role = "staff";
  assert.equal((await page(props)).type, "VerificationEntry");
  assert.equal(calls, 1);
});
test("event venue API refuses another event and returns only the authenticated event publication", async () => {
  const calls = [];
  const api = compile("../src/app/api/venue/route.ts", (name) =>
    name === "next/server"
      ? {
          NextResponse: {
            json: (body, options = {}) => ({
              body,
              status: options.status ?? 200,
              headers: options.headers,
            }),
          },
        }
      : {
          identity: async () => ({ role: "staff", event_id: "event" }),
          runProduction: async (body) => {
            calls.push(body);
            return { status: "published" };
          },
        },
  );
  assert.equal(
    (await api.GET(new Request("http://localhost/api/venue?event_id=other")))
      .status,
    403,
  );
  const result = await api.GET(
    new Request("http://localhost/api/venue?event_id=event"),
  );
  assert.equal(result.status, 200);
  assert.equal(result.headers["Cache-Control"], "no-store");
  assert.deepEqual(calls, [{ command: "venue", event_id: "event" }]);
});
test("event and plan identifiers are encoded as route segments", () => {
  assert.equal(
    helpers.verificationPath("event / one", "plan?#"),
    "/events/event%20%2F%20one/seating-plans/plan%3F%23/verification",
  );
  assert.equal(helpers.venuePath("event one"), "/events/event%20one/venue");
});

test("verification saves recovered local edits before checking the server revision", async (t) => {
  const db = new HistoryDatabase(`recovered-route-${crypto.randomUUID()}`);
  t.after(() => db.delete());
  const history = new ManualHistory(db),
    initial = fixture();
  await history.open(initial);
  const recovered = structuredClone(initial.state);
  [recovered.items.A.seat_ids, recovered.items.B.seat_ids] = [
    recovered.items.B.seat_ids,
    recovered.items.A.seat_ids,
  ];
  history.commit(recovered);
  const calls = [],
    effects = [];
  const checked = {
    findings: [],
    summary: { open_blocking: 0, open_advisory: 0, acked: 0, resolved: 0 },
  };
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    const body = JSON.parse(options.body);
    calls.push(body);
    return {
      ok: true,
      json: async () =>
        body.command === "workspace_save"
          ? { ...initial, state: recovered, revision: 1 }
          : checked,
    };
  });
  const { VerificationScreen } = compile(
    "../src/components/seat/verification-screen.tsx",
    (name) => {
      if (name === "react")
        return {
          useState: (value) => [value, () => {}],
          useRef: (current) => ({ current }),
          useMemo: (fn) => fn(),
          useEffect: (effect) => effects.push(effect),
          useSyncExternalStore: (_subscribe, get) => get(),
        };
      if (name === "react/jsx-runtime") return require(name);
      if (name === "@/lib/manual-history") return historyTypes;
      if (name === "@/lib/workspace") return compile("../src/lib/workspace.ts");
      if (name === "@/lib/verification")
        return compile("../src/lib/verification.ts");
      if (name === "./helpers") return helpers;
      return new Proxy(
        {},
        { get: (_, key) => (key === "__esModule" ? true : String(key)) },
      );
    },
  );
  VerificationScreen({
    initial,
    initialState: recovered,
    history,
    onExit() {},
    onPublished() {},
  });
  const cleanup = effects[0]();
  for (let i = 0; i < 30 && calls.length < 2; i++)
    await new Promise((resolve) => setImmediate(resolve));
  cleanup();
  assert.deepEqual(
    calls.map((body) => body.command),
    ["workspace_save", "workspace_check"],
  );
  assert.deepEqual(calls[0].state, recovered);
  assert.equal(calls[0].revision, 0);
  assert.equal(calls[1].revision, 1);
  assert.equal(calls[1].history_context.edits.length, 1);
});
