import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import ts from "typescript";

const require = createRequire(import.meta.url);
function compile(file, load) {
    const source = fs.readFileSync(new URL(file, import.meta.url), "utf8");
    const compiled = ts.transpileModule(source, {
        compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
    }).outputText;
    const mod = { exports: {} };
    new Function("require", "exports", "module", compiled)(load, mod.exports, mod);
    return mod.exports;
}
const workspaceFunctions = compile("../src/lib/workspace.ts", require);
// Exercise dashboard handlers and rendered props without a browser or new dependencies.
// Child components are boundaries; state/ref slots persist across explicit rerenders.
function dashboard(initialWorkspace) {
    const slots = [];
    let cursor = 0;
    const hooks = {
        useState(initial) {
            const index = cursor++;
            if (!(index in slots)) slots[index] = typeof initial === "function" ? initial() : initial;
            return [slots[index], next => { slots[index] = typeof next === "function" ? next(slots[index]) : next; }];
        },
        useRef(initial) {
            const index = cursor++;
            return slots[index] ??= { current: initial };
        },
        useMemo: fn => fn(),
        useEffect() {},
    };
    const { SeatDashboard } = compile("../src/components/seat/seat-dashboard.tsx", name => {
        if (name === "react") return hooks;
        if (name === "react/jsx-runtime") return require(name);
        if (name === "@/lib/workspace") return workspaceFunctions;
        if (name === "./seat-theme") return { TIER_STYLES: { MERIT: {} } };
        return new Proxy({}, { get: (_, key) => key === "__esModule" ? true : String(key) });
    });
    return () => {
        cursor = 0;
        const tree = SeatDashboard({ initialResult: initialWorkspace.base, initialWorkspace });
        const nodes = [];
        function visit(node) {
            if (Array.isArray(node)) return node.forEach(visit);
            if (!node || typeof node !== "object") return;
            nodes.push(node);
            visit(node.props?.children);
        }
        visit(tree);
        return {
            find: (type, predicate = () => true) => nodes.find(n => n.type === type && predicate(n.props))?.props,
        };
    };
}
function fixture(docked = false) {
    return {
        base: { event_id: "demo", plan_version_id: "old", publication_status: "DRAFT", assignments: [],
            floor_plan: { rows: [{ row_number: 1, seats: [1, 2, 3].map(n => ({ seat_id: `S${n}`, physical_position: n, side: "LEFT", is_blocked: n === 3 })) }] } },
        state: {
            participants: [{ participant_id: "P1", full_name: "Participant", contribution_tier: "MERIT", registration_status: "CONFIRMED", age: 30 }],
            items: { P1: { seat_ids: docked ? [] : ["S1"], display_names: ["Participant"], previous_seat_ids: [], note: "", locked: false } },
        }, revision: 0, saved_at: null,
    };
}
const request = { generation_mode: "REGENERATE_DRAFT", preferences: [{ key: "activeness", enabled: true }] };
const response = (body, ok = true) => ({ ok, json: async () => body });
const settle = () => new Promise(resolve => setImmediate(resolve));
function openSettings(render) {
    render().find("Button", p => p.children?.some?.(c => c?.type === "Settings2")).onClick();
    return render().find("WeightControls");
}

test("regeneration closes settings, blocks map, then opens and displays the exact new draft", async t => {
    const render = dashboard(fixture());
    const next = fixture();
    next.base.plan_version_id = "new";
    next.state.items.P1.seat_ids = ["S2"];
    let finishSolve;
    let finishOpen;
    const calls = [];
    t.mock.method(globalThis, "fetch", (url, options) => {
        calls.push([url, JSON.parse(options.body)]);
        return new Promise(resolve => { if (calls.length === 1) finishSolve = resolve; else finishOpen = resolve; });
    });
    const settings = openSettings(render);
    assert.ok(settings);
    settings.onGenerate(request);
    settings.onGenerate(request); // Duplicate clicks cannot start another solve.
    assert.equal(calls.length, 1);
    assert.equal(render().find("WeightControls"), undefined);
    assert.equal(render().find("MapLoadingOverlay").phase, "generating");
    assert.equal(render().find("div", p => p.className === "map-loading-content").inert, true);
    finishSolve(response({ status: "success", plan_version_id: "new" }));
    await settle();
    assert.equal(render().find("MapLoadingOverlay").phase, "loading-workspace");
    assert.deepEqual(calls[1], ["/api/workspace?event_id=demo", { command: "workspace_open", plan_version_id: "new" }]);
    assert.deepEqual(calls[0][1].preferences, request.preferences);
    finishOpen(response(next));
    await settle();
    assert.equal(render().find("MapLoadingOverlay"), undefined);
    assert.equal(render().find("HallMap").owners.S2, "P1");
    assert.equal(render().find("HallMap").owners.S1, undefined);
});

test("failed workspace opening retries the saved plan without solving again", async t => {
    const render = dashboard(fixture());
    const next = fixture();
    next.base.plan_version_id = "new";
    const calls = [];
    t.mock.method(globalThis, "fetch", async (url, options) => {
        calls.push([url, JSON.parse(options.body)]);
        if (calls.length === 1) return response({ status: "success", plan_version_id: "new" });
        if (calls.length === 2) return response({ error: { message: "Try opening again" } }, false);
        return response(next);
    });
    openSettings(render).onGenerate(request);
    await settle();
    const overlay = render().find("MapLoadingOverlay");
    assert.equal(overlay.phase, "error");
    assert.equal(overlay.draftCreated, true);
    assert.equal(overlay.error, "Try opening again");
    overlay.onRetry();
    await settle();
    assert.deepEqual(calls[2], calls[1]);
    assert.equal(calls.filter(([url]) => url.startsWith("/api/solve")).length, 1);
    assert.equal(render().find("MapLoadingOverlay"), undefined);
});

test("solve failure keeps the current map and retry uses the selected preferences", async t => {
    const render = dashboard(fixture());
    const calls = [];
    t.mock.method(globalThis, "fetch", async (url, options) => {
        calls.push([url, JSON.parse(options.body)]);
        return response({ status: "error", error: { message: "Unable to solve" } }, false);
    });
    openSettings(render).onGenerate(request);
    await settle();
    assert.equal(render().find("HallMap").owners.S1, "P1");
    assert.equal(render().find("MapLoadingOverlay").draftCreated, false);
    render().find("MapLoadingOverlay").onRetry();
    await settle();
    assert.deepEqual(calls[1], calls[0]);
});

test("empty seat opens dock in edit mode and accepts a drop; blocked seats do not", () => {
    const render = dashboard(fixture(true));
    render().find("HallMap").onSelect("S3");
    assert.equal(render().find("aside"), undefined);
    render().find("HallMap").onSelect("S2");
    assert.equal(render().find("aside")["aria-label"], "Holding dock");
    assert.equal(render().find("HallMap").editable, true);
    assert.equal(render().find("HallMap").selectedSeat, "S2");
    render().find("HallMap").onDrop("P1", "S2");
    assert.ok(render().find("Dialog", p => p.open));
    render().find("Button", p => p.children === "Confirm move / swap").onClick();
    assert.equal(render().find("HallMap").owners.S2, "P1");
});

test("empty seat without docked registrations does not enter edit mode", () => {
    const render = dashboard(fixture());
    render().find("HallMap").onSelect("S2");
    assert.equal(render().find("aside"), undefined);
    assert.equal(render().find("HallMap").editable, false);
});
