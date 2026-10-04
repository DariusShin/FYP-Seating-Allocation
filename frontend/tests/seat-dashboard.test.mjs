import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import ts from "typescript";

const require = createRequire(import.meta.url);
function compile(file, load) {
	const source = fs.readFileSync(new URL(file, import.meta.url), "utf8");
	const compiled = ts.transpileModule(source, {
        fileName: file,
		compilerOptions: {
			module: ts.ModuleKind.CommonJS,
            target: ts.ScriptTarget.ES2022,
			jsx: ts.JsxEmit.ReactJSX,
			esModuleInterop: true,
		},
	}).outputText;
	const mod = { exports: {} };
	new Function("require", "exports", "module", compiled)(
		load,
		mod.exports,
		mod,
	);
	return mod.exports;
}
const historyFunctions = compile("../src/lib/manual-history.ts", require);
const workspaceFunctions = compile("../src/lib/workspace.ts", require);
// Exercise dashboard handlers and rendered props without a browser or new dependencies.
// Child components are boundaries; state/ref slots persist across explicit rerenders.
function component(file, exportName, props) {
	const slots = [];
	const notifications = [];
	let cursor = 0;
	const hooks = {
		useState(initial) {
			const index = cursor++;
			if (!(index in slots))
				slots[index] = typeof initial === "function" ? initial() : initial;
			return [
				slots[index],
				(next) => {
					slots[index] = typeof next === "function" ? next(slots[index]) : next;
				},
			];
		},
		useRef(initial) {
			const index = cursor++;
			return (slots[index] ??= { current: initial });
		},
		useMemo: (fn) => fn(),
		useEffect() {},
        useSyncExternalStore(_subscribe, get) { return get(); },
	};
	const Component = compile(file, (name) => {
		if (name === "react") return hooks;
		if (name === "react/jsx-runtime") return require(name);
		if (name === "@/lib/workspace") return workspaceFunctions;
        if (name === "@/lib/manual-history") return { ...historyFunctions, ManualHistory: class extends historyFunctions.ManualHistory {
            constructor() { super(); this.ready = true; this.failed = true; this.session = { id: 'test', state: structuredClone(props.initialWorkspace.state), baseline: structuredClone(props.initialWorkspace.state), active: [], redo: [], sequence: 0, generation: 0 }; }
            async open(workspace) { this.session.state = structuredClone(workspace.state); return workspace.state; }
        }};
		if (name === "./seat-theme") return { TIER_STYLES: { MERIT: {} } };
		if (name === "sonner")
			return {
				toast: Object.fromEntries(
					["success", "info", "error"].map((level) => [
						level,
						(message) => notifications.push({ level, message }),
					]),
				),
			};
		return new Proxy(
			{},
			{ get: (_, key) => (key === "__esModule" ? true : String(key)) },
		);
	})[exportName];
	return () => {
		cursor = 0;
		const tree = Component(props);
		const nodes = [];
		function visit(node) {
			if (Array.isArray(node)) return node.forEach(visit);
			if (!node || typeof node !== "object") return;
			nodes.push(node);
			visit(node.props?.children);
		}
		visit(tree);
		return {
			notifications,
			find: (type, predicate = () => true) =>
				nodes.find((n) => n.type === type && predicate(n.props))?.props,
		};
	};
}
function fixture(docked = false) {
	return {
		base: {
			event_id: "demo",
			plan_version_id: "old",
			publication_status: "DRAFT",
			assignments: [],
            source_request: { layout: { approved_pairs: [[1,2]] } },
			floor_plan: {
				rows: [
					{
						row_number: 1,
						seats: [1, 2, 3].map((n) => ({
							seat_id: `S${n}`,
							physical_position: n,
							side: "LEFT",
							is_blocked: n === 3,
						})),
					},
				],
			},
		},
		state: {
			participants: [
				{
					participant_id: "P1",
					full_name: "Participant",
					contribution_tier: "MERIT",
					registration_status: "CONFIRMED",
					age: 30,
				},
			],
			items: {
				P1: {
					seat_ids: docked ? [] : ["S1"],
					display_names: ["Participant"],
					previous_seat_ids: [],
					note: "",
				},
			},
		},
		revision: 0,
		saved_at: null,
	};
}

const response = (body, ok = true) => ({ ok, json: async () => body });
const settle = () => new Promise((resolve) => setImmediate(resolve));
function openSettings(render) {
	render()
		.find("Button", (p) => p.children?.some?.((c) => c?.type === "Settings2"))
		.onClick();
	return render().find("WeightControls");
}

function dashboard(initialWorkspace) {
	return component(
		"../src/components/seat/seat-dashboard.tsx",
		"SeatDashboard",
		{ initialResult: initialWorkspace.base, initialWorkspace },
	);
}

test("new draft opens its exact version and updates the map", async (t) => {
	const render = dashboard(fixture());
	const next = fixture();
	next.base.plan_version_id = "new";
	next.state.items.P1.seat_ids = ["S2"];
	t.mock.method(globalThis, "fetch", async (url, options) => {
		if (url === "/api/solve") return response({ status: "success", plan_version_id: "new" });
		assert.equal(url, "/api/workspace");
		assert.deepEqual(JSON.parse(options.body), {
			command: "workspace_open",
			plan_version_id: "new",
		});
		return response(next);
	});
	await openSettings(render).onGenerate(preferences);
	assert.equal(render().find("HallMap").owners.S2, "P1");
	assert.equal(render().find("WeightControls"), undefined);
	assert.deepEqual(render().notifications, [
		{
			level: "success",
			message: "New seating draft ready. Public seating is unchanged.",
		},
	]);
});

test("saving a draft emits the success toast", async (t) => {
	const render = dashboard(fixture());
	t.mock.method(globalThis, "fetch", async () => response(fixture()));
	render()
		.find("Button", (p) => p.children === "Edit plan")
		.onClick();
	await render()
		.find("Button", (p) => p.children === "Save draft")
		.onClick();
	assert.deepEqual(render().notifications.at(-1), {
		level: "success",
		message: "Working draft saved. Public seating is unchanged.",
	});
});

test("submit for review opens the dedicated verification screen", async () => {
    const value = fixture();
    const render = dashboard(value);
    render().find("Button", p => p.children === "Edit plan").onClick();
    await render().find("Button", p => p.children === "Submit for review").onClick();
    assert.equal(render().find("VerificationScreen").initial, value);
});

test("unseated paid registrations block review entry", () => {
    const render = dashboard(fixture(true));
    render().find("Button", p => p.children === "Edit plan").onClick();
    assert.equal(render().find("Button", p => p.children === "Submit for review").disabled, true);
});

test("dock remains available for drag and drop in edit mode", () => {
	const render = dashboard(fixture(true));
	assert.equal(render().find("HallMap").editable, false);
	render()
		.find("Button", (p) => p.children === "Edit plan")
		.onClick();
	render()
		.find("Button", (p) => p.children?.[0] === "Holding dock (")
		.onClick();
	assert.equal(render().find("aside")["aria-label"], "Holding dock");
	assert.equal(render().find("HallMap").editable, true);
	render().find("HallMap").onDrop("P1", "S2");
	assert.equal(render().find("Button", (p) => p.children === "Confirm move / swap"), undefined);
	assert.equal(render().find("HallMap").owners.S2, "P1");
});

const preferences = ["contribution_seat", "activeness", "category_zone"].map(
	(key) => ({ key, enabled: true }),
);
function controls(onGenerate = async () => {}) {
	return component(
		"../src/components/seat/weight-controls.tsx",
		"WeightControls",
		{ result: { preferences }, onGenerate },
	);
}
const generateButton = (render) =>
	render().find("Button", (p) => p.className === "w-full");

test("generation is enabled only by changed preference order or enabled flags", () => {
	const render = controls();
	assert.equal(render().find("select"), undefined);
	assert.equal(generateButton(render).disabled, true);
	render()
		.find("Switch", (p) => p.id === "pref-activeness")
		.onCheckedChange(false);
	assert.equal(generateButton(render).disabled, false);
	render()
		.find("Switch", (p) => p.id === "pref-activeness")
		.onCheckedChange(true);
	assert.equal(generateButton(render).disabled, true);
	render()
		.find("Button", (p) => p["aria-label"]?.endsWith("desirable seats down"))
		.onClick();
	assert.equal(generateButton(render).disabled, false);
	render()
		.find("Button", (p) => p["aria-label"]?.endsWith("desirable seats up"))
		.onClick();
	assert.equal(generateButton(render).disabled, true);
});

test("regeneration closes settings and blocks editing until the exact draft opens", async (t) => {
	const render = dashboard(fixture());
	render().find("Button", p => p.children === "Edit plan").onClick();
	let finishSolve, finishOpen;
	const requests = [];
	t.mock.method(globalThis, "fetch", (url, options) => {
		requests.push({ url, body: JSON.parse(options.body) });
		return new Promise(resolve => {
			if (url === "/api/solve") finishSolve = resolve;
			else finishOpen = resolve;
		});
	});
	const settings = openSettings(render);
	const changed = preferences.map(p => ({ ...p, enabled: p.key !== "activeness" }));
	const pending = settings.onGenerate(changed);
	await settings.onGenerate(changed); // Double click cannot create another draft.
	assert.equal(requests.length, 1);
	assert.deepEqual(requests[0].body.preferences, changed);
	assert.equal(render().find("WeightControls"), undefined);
	assert.equal(render().find("MapLoadingOverlay").phase, "generating");
	assert.equal(render().find("div", p => p.inert === true && p["aria-busy"] === true)["aria-busy"], true);
	assert.equal(render().find("HallMap").editable, false);
	render().find("HallMap").onDrop("P1", "S2");
	assert.equal(render().find("HallMap").owners.S1, "P1");
	finishSolve(response({ status: "success", plan_version_id: "new" }));
	await settle();
	assert.equal(render().find("MapLoadingOverlay").phase, "loading-workspace");
	assert.equal(render().find("HallMap").editable, false);
	assert.equal(requests[1].body.plan_version_id, "new");
	const next = fixture();
	next.base.plan_version_id = "new";
	next.state.items.P1.seat_ids = ["S2"];
	finishOpen(response(next));
	await pending;
	assert.equal(render().find("MapLoadingOverlay"), undefined);
	assert.equal(render().find("div", p => p.inert === true), undefined);
	assert.equal(render().find("HallMap").owners.S2, "P1");
});

test("failed draft opening retries from the overlay without another solve", async (t) => {
	const render = dashboard(fixture());
	let solves = 0, opens = 0;
	t.mock.method(globalThis, "fetch", async url => {
		if (url === "/api/solve") {
			solves++;
			return response({ status: "success", plan_version_id: "new" });
		}
		return ++opens === 1 ? response({ error: { message: "Open failed" } }, false) : response(fixture());
	});
	await openSettings(render).onGenerate(preferences);
	assert.equal(render().find("MapLoadingOverlay").phase, "error");
	assert.equal(render().find("MapLoadingOverlay").draftCreated, true);
	assert.equal(render().find("MapLoadingOverlay").error, "Open failed");
	render().find("MapLoadingOverlay").onRetry();
	await settle();
	assert.equal(solves, 1);
	assert.equal(opens, 2);
	assert.equal(render().find("MapLoadingOverlay"), undefined);
});

test("failed generation keeps preferences for an overlay retry", async (t) => {
	const render = dashboard(fixture());
	const attempts = [];
	t.mock.method(globalThis, "fetch", async (url, options) => {
		if (url === "/api/workspace") return response(fixture());
		attempts.push(JSON.parse(options.body));
		return attempts.length === 1
			? response({ error: { message: "Try again" } }, false)
			: response({ status: "success", plan_version_id: "new" });
	});
	await openSettings(render).onGenerate(preferences);
	assert.equal(render().find("MapLoadingOverlay").phase, "error");
	assert.equal(render().find("MapLoadingOverlay").draftCreated, false);
	render().find("MapLoadingOverlay").onRetry();
	await settle();
	assert.deepEqual(attempts[0], attempts[1]);
	assert.equal(render().find("MapLoadingOverlay"), undefined);
});

function details(onSave) {
	const value = fixture();
	return component(
		"../src/components/seat/allocation-details.tsx",
		"AllocationDetails",
		{
			person: value.state.participants[0],
			item: value.state.items.P1,
			location: "West 1",
			busy: false,
			onSave,
			onClose() {},
		},
	);
}

test("details Edit and Cancel discard local changes without saving", () => {
	let saves = 0;
	const render = details(async () => {
		saves++;
		return true;
	});
	assert.equal(render().find("fieldset").disabled, true);
	render()
		.find("Button", (p) => p.children === "Edit")
		.onClick();
	render()
		.find("input")
		.onChange({ target: { value: "Edited name" } });
	render()
		.find("textarea")
		.onChange({ target: { value: "Edited note" } });
	assert.equal(
		render().find("Button", (p) => p.children === "Save draft").disabled,
		false,
	);
	render()
		.find("Button", (p) => p.children === "Cancel")
		.onClick();
	assert.equal(render().find("input").value, "Participant");
	assert.equal(render().find("textarea").value, "");
	assert.ok(render().find("Button", (p) => p.children === "Edit"));
	assert.equal(saves, 0);
});

test("details stay editable after failed save and exit editing only after success", async () => {
	const saved = [];
	const render = details(async (data) => {
		saved.push(data);
		return saved.length === 2;
	});
	render()
		.find("Button", (p) => p.children === "Edit")
		.onClick();
	render()
		.find("textarea")
		.onChange({ target: { value: "Retain paid seats" } });
	render()
		.find("Button", (p) => p.children === "Save draft")
		.onClick();
	await settle();
	assert.ok(render().find("Button", (p) => p.children === "Cancel"));
	render()
		.find("Button", (p) => p.children === "Save draft")
		.onClick();
	await settle();
	assert.ok(render().find("Button", (p) => p.children === "Edit"));
	assert.deepEqual(saved[0], {
		display_names: ["Participant"],
		note: "Retain paid seats",
	});
});

test("swaps apply immediately, undo and redo both registrations, and reject blocked targets", () => {
    const value = fixture();
    value.state.participants.push({ ...value.state.participants[0], participant_id: "P2", full_name: "Second" });
    value.state.items.P2 = { ...value.state.items.P1, seat_ids: ["S2"], display_names: ["Second"] };
    const render = dashboard(value);
    render().find("HallMap").onDrop("P1", "S2");
    assert.equal(render().find("HallMap").owners.S1, "P1");
    render().find("Button", p => p.children === "Edit plan").onClick();
    assert.equal(render().find("Button", p => p["aria-label"] === "Undo last change").disabled, true);
    render().find("HallMap").onDrop("P1", "S2");
    assert.deepEqual(render().find("HallMap").owners, { S2: "P1", S1: "P2" });
    assert.equal(render().find("DialogTitle", p => p.children === "Confirm seat changes"), undefined);
    assert.equal(render().find("Button", p => p["aria-label"] === "Undo last change").disabled, false);
    render().find("Button", p => p["aria-label"] === "Undo last change").onClick();
    assert.deepEqual(render().find("HallMap").owners, { S1: "P1", S2: "P2" });
    assert.equal(render().find("Button", p => p["aria-label"] === "Undo last change").disabled, true);
    render().find("Button", p => p["aria-label"] === "Redo").onClick();
    assert.deepEqual(render().find("HallMap").owners, { S2: "P1", S1: "P2" });
    render().find("HallMap").onDrop("P1", "S3");
    assert.deepEqual(render().find("HallMap").owners, { S2: "P1", S1: "P2" });
    assert.match(render().find("div", p => p.role === "alert").children, /cannot fit/);
});

test('the selected registration border follows swap, undo, redo and docking',()=>{
 const value=fixture();value.state.participants.push({...value.state.participants[0],participant_id:'P2',full_name:'Second'});value.state.items.P2={...value.state.items.P1,seat_ids:['S2'],display_names:['Second']};
 const render=dashboard(value);render().find('Button',p=>p.children==='Edit plan').onClick();
 render().find('HallMap').onSelect('S1');assert.equal(render().find('HallMap').selectedSeat,'S1');
 render().find('HallMap').onDrop('P1','S2');assert.equal(render().find('HallMap').selected,'P1');assert.equal(render().find('HallMap').selectedSeat,'S2');
 render().find('Button',p=>p['aria-label']==='Undo').onClick();assert.equal(render().find('HallMap').selectedSeat,'S1');
 render().find('Button',p=>p['aria-label']==='Redo').onClick();assert.equal(render().find('HallMap').selectedSeat,'S2');
 render().find('HallMap').onSelect('S2');render().find('Button',p=>p.children==='Send to holding dock').onClick();assert.equal(render().find('HallMap').selectedSeat,null);
});
