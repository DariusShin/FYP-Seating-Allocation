/** Direct PDF/PNG exports of the venue seating map, matching the browser print preview. */

const TARGET_RASTER_WIDTH = 3000;
const PDF_PAGE = { width: 420, height: 297 };
const PDF_MARGIN = 10;
/** A3 landscape content width (420mm minus two 10mm margins) at 96dpi. */
export const EXPORT_WIDTH_PX = Math.round((400 / 25.4) * 96);

export function captureScale(width: number) {
  if (!width) return 2;
  const scale = TARGET_RASTER_WIDTH / width;
  return Math.min(3, Math.max(1, Math.round(scale * 10) / 10));
}

export function venueFileName(eventId: string, extension: "pdf" | "png") {
  const safe =
    eventId.replace(/[^a-z0-9-]+/gi, "-").replace(/^-+|-+$/g, "") || "event";
  return `seating-map-${safe}.${extension}`;
}

export function pdfPlacement(
  imageWidth: number,
  imageHeight: number,
  page = PDF_PAGE,
  margin = PDF_MARGIN,
) {
  const scale = Math.min(
    (page.width - margin * 2) / imageWidth,
    (page.height - margin * 2) / imageHeight,
  );
  const width = imageWidth * scale;
  const height = imageHeight * scale;
  return {
    x: (page.width - width) / 2,
    y: (page.height - height) / 2,
    width,
    height,
  };
}

const isMedia = (rule: CSSRule): rule is CSSMediaRule =>
  typeof CSSMediaRule !== "undefined" && rule instanceof CSSMediaRule;
const isGrouping = (rule: CSSRule): rule is CSSSupportsRule | CSSLayerBlockRule =>
  typeof CSSSupportsRule !== "undefined" &&
  (rule instanceof CSSSupportsRule || rule instanceof CSSLayerBlockRule);
const isPrintCondition = (condition: string) =>
  condition.split(",").some((part) => part.trim() === "print");

/** Re-declares every print-media rule unconditioned so an on-screen render matches the print preview. */
export function printStyleCss(source: Document): string {
  const chunks: string[] = [];
  const walk = (rules: CSSRuleList) => {
    for (const rule of Array.from(rules)) {
      if (isMedia(rule)) {
        if (isPrintCondition(rule.conditionText))
          for (const inner of Array.from(rule.cssRules))
            chunks.push(inner.cssText);
        else walk(rule.cssRules);
      } else if (isGrouping(rule)) walk(rule.cssRules);
    }
  };
  for (const sheet of Array.from(source.styleSheets)) {
    try {
      walk(sheet.cssRules);
    } catch {
      /* cross-origin stylesheets stay untouched */
    }
  }
  return chunks.join("\n");
}

async function captureNode(node: HTMLElement) {
  const { default: html2canvas } = await import("html2canvas-pro");
  const style = document.createElement("style");
  style.textContent = printStyleCss(document);
  const previousWidth = node.style.width;
  document.head.appendChild(style);
  node.style.width = `${EXPORT_WIDTH_PX}px`;
  try {
    await document.fonts.ready;
    await new Promise((resolve) => requestAnimationFrame(() => resolve(null)));
    return await withTimeout(
      html2canvas(node, {
        backgroundColor: "#ffffff",
        useCORS: true,
        scale: captureScale(node.offsetWidth),
        windowWidth: node.offsetWidth,
      }),
      20000,
      "The export took too long to render.",
    );
  } finally {
    style.remove();
    node.style.width = previousWidth;
  }
}

function withTimeout<T>(task: Promise<T>, ms: number, message: string) {
  return Promise.race([
    task,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(message)), ms),
    ),
  ]);
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function saveVenuePng(node: HTMLElement, filename: string) {
  const canvas = await captureNode(node);
  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/png"),
  );
  if (!blob) throw Error("Unable to render the seating map image.");
  download(blob, filename);
}

export async function saveVenuePdf(node: HTMLElement, filename: string) {
  const canvas = await captureNode(node);
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({
    orientation: "landscape",
    unit: "mm",
    format: "a3",
    compress: true,
  });
  const place = pdfPlacement(canvas.width, canvas.height);
  doc.addImage(
    canvas.toDataURL("image/png"),
    "PNG",
    place.x,
    place.y,
    place.width,
    place.height,
  );
  doc.save(filename);
}
