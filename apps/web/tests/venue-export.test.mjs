import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import ts from "typescript";
const require = createRequire(import.meta.url);
function compile(file, load = require) {
  const compiled = ts.transpileModule(
    fs.readFileSync(new URL(file, import.meta.url), "utf8"),
    {
      fileName: file,
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
      },
    },
  ).outputText;
  const mod = { exports: {} };
  new Function("require", "exports", "module", compiled)(
    load,
    mod.exports,
    mod,
  );
  return mod.exports;
}
const react = {
  useState: (value) => [value, () => {}],
  useRef: (current) => ({ current }),
  useEffect: () => {},
};
const proxy = new Proxy(
  {},
  { get: (_, key) => (key === "__esModule" ? true : String(key)) },
);
const load = (name) => {
  if (name === "react") return react;
  if (name === "react/jsx-runtime") return require(name);
  return proxy;
};
const { captureScale, venueFileName, pdfPlacement, EXPORT_WIDTH_PX, printStyleCss, saveVenuePng, saveVenuePdf } =
  compile("../src/lib/venue-export.ts", load);

test("the export savers are async functions ready for browser capture", () => {
  assert.equal(typeof saveVenuePng, "function");
  assert.equal(typeof saveVenuePdf, "function");
  assert.equal(typeof printStyleCss, "function");
});

test("the export width matches the A3 landscape content box", () => {
  assert.equal(EXPORT_WIDTH_PX, 1512);
});
const { VenueActions, VenueDisplay } = compile(
  "../src/components/public/venue-display.tsx",
  load,
);

function render(element) {
  const nodes = [];
  function visit(node) {
    if (Array.isArray(node)) return node.forEach(visit);
    if (!node || typeof node !== "object") return;
    nodes.push(node);
    if (typeof node.type === "function") return visit(node.type(node.props));
    visit(node.props?.children);
  }
  visit(element);
  return nodes;
}
const buttons = (nodes) =>
  nodes.filter((n) => n.type === "Button").map((n) => n.props);

test("capture scale targets a 3000px raster within sane bounds", () => {
  assert.equal(captureScale(1280), 2.3);
  assert.equal(captureScale(900), 3);
  assert.equal(captureScale(4000), 1);
  assert.equal(captureScale(0), 2);
});

test("venue file names sanitize the event identifier", () => {
  assert.equal(venueFileName("event / one", "pdf"), "seating-map-event-one.pdf");
  assert.equal(venueFileName("  event  ", "png"), "seating-map-event.png");
  assert.equal(venueFileName("", "png"), "seating-map-event.png");
});

test("pdf placement centers the raster inside A3 landscape with 10mm margins", () => {
  const wide = pdfPlacement(2944, 2000);
  assert.ok(Math.abs(wide.width - 400) < 0.01);
  assert.ok(Math.abs(wide.height - 271.74) < 0.01);
  assert.ok(Math.abs(wide.x - 10) < 0.01);
  assert.ok(Math.abs(wide.y - 12.63) < 0.01);
  const tall = pdfPlacement(2000, 2944);
  assert.ok(Math.abs(tall.width - 188.18) < 0.01);
  assert.ok(Math.abs(tall.height - 277) < 0.01);
  assert.ok(Math.abs(tall.x - 115.91) < 0.01);
  assert.ok(Math.abs(tall.y - 10) < 0.01);
});

test("venue actions keep print beside the direct PDF and PNG exports", () => {
  const saves = [];
  let printed = 0;
  let nodes = buttons(
    render(
      VenueActions({
        disabled: true,
        saving: "",
        onPrint: () => printed++,
        onSave: (format) => saves.push(format),
      }),
    ),
  );
  assert.deepEqual(
    nodes.map((p) => p.children),
    ["Print", "Save PDF", "Save PNG"],
  );
  assert.ok(nodes.every((p) => p.disabled));
  nodes = buttons(
    render(
      VenueActions({
        disabled: false,
        saving: "pdf",
        onPrint: () => printed++,
        onSave: (format) => saves.push(format),
      }),
    ),
  );
  assert.equal(nodes[0].disabled, false);
  assert.equal(nodes[1].children, "Rendering…");
  assert.ok(nodes[1].disabled && nodes[2].disabled);
  nodes[0].onClick();
  nodes[2].onClick();
  assert.equal(printed, 1);
  assert.deepEqual(saves, ["png"]);
});

test("venue display offers the export actions before a plan loads", () => {
  const nodes = buttons(render(VenueDisplay({ eventId: "event" })));
  assert.deepEqual(
    nodes.map((p) => p.children),
    ["Print", "Save PDF", "Save PNG", "Full screen"],
  );
  assert.ok(nodes.slice(0, 3).every((p) => p.disabled));
});
