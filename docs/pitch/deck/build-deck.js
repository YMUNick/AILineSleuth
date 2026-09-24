// Builds docs/pitch/LineSleuth-demo.pptx from the outline in docs/pitch/pitch-deck.md.
// Screenshots are read from docs/pitch/deck/assets/*.png (captured by capture-screens.py);
// a missing screenshot renders as a labelled placeholder box.
//
// Usage: node docs/pitch/deck/build-deck.js   (needs `pptxgenjs` on NODE_PATH or in node_modules)

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ASSETS = path.join(__dirname, "assets");
const OUT = path.join(__dirname, "..", "LineSleuth-demo.pptx");

// Colours mirror docs/design/ui-spec.md tokens.
const C = {
  bg: "0F1115",
  s1: "171A21",
  s2: "1F232C",
  s3: "282D38",
  border: "2E3440",
  borderStrong: "4A5263",
  text: "E8EAED",
  text2: "A3AAB8",
  muted: "8A93A3",
  amber: "F5A524",
  red: "F2555A",
  green: "3DD68C",
  blue: "5AA9FF",
  grey: "B8BEC9",
};
const HEAD = "Arial";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "LineSleuth — AI Builder Cup 2026";
pres.author = "Hung Che Nick Lai";

const W = 13.333;
const M = 0.6; // outer margin

function base(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M, y: 0.45, w: 8, h: 0.3, fontFace: HEAD, fontSize: 11, bold: true,
      color: C.amber, charSpacing: 3, margin: 0, isTextBox: true,
    });
  }
  if (title) {
    s.addText(title, {
      x: M, y: 0.75, w: W - 2 * M, h: 0.8, fontFace: HEAD, fontSize: 34, bold: true,
      color: C.text, margin: 0, isTextBox: true,
    });
  }
  return s;
}

function pending(s, text, y) {
  s.addText(text, {
    x: M, y: y || 7.0, w: W - 2 * M, h: 0.3, fontFace: BODY, fontSize: 10, italic: true,
    color: C.amber, margin: 0, isTextBox: true,
  });
}

function shot(s, file, x, y, w, h, label) {
  const p = path.join(ASSETS, file);
  if (fs.existsSync(p)) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x - 0.04, y: y - 0.04, w: w + 0.08, h: h + 0.08, rectRadius: 0.08,
      fill: { color: C.s3 }, line: { color: C.borderStrong, width: 1 },
    });
    s.addImage({ path: p, x, y, w, h, altText: label });
  } else {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w, h, rectRadius: 0.08, fill: { color: C.s2 },
      line: { color: C.borderStrong, width: 1, dashType: "dash" },
    });
    s.addText(`[Screenshot: ${label}]`, {
      x, y, w, h, align: "center", valign: "middle", fontFace: BODY, fontSize: 12,
      color: C.muted, isTextBox: true,
    });
  }
}

// Screenshots are real Gemini runs on the deployed prototype, but the plant data is simulated; say so on the slide.
function draftTag(s) {
  s.addText("Live prototype (Cloud Run, gemini-2.5-flash) · simulated plant data", {
    x: W - M - 5.2, y: 0.45, w: 5.2, h: 0.3, align: "right", fontFace: BODY, fontSize: 10, italic: true,
    color: C.muted, margin: 0, isTextBox: true,
  });
}

function card(s, x, y, w, h, fill) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.1, fill: { color: fill || C.s1 },
    line: { color: C.border, width: 1 },
  });
}

function bullets(s, items, x, y, w, h, size) {
  s.addText(
    items.map((t, i) => {
      const runs = Array.isArray(t) ? t : [{ text: t }];
      return runs.map((r, j) => ({
        text: r.text,
        options: {
          bold: !!r.bold, color: r.color || C.text,
          bullet: j === 0 ? { indent: 16 } : undefined,
          breakLine: j === runs.length - 1 && i < items.length - 1,
          paraSpaceAfter: 8,
        },
      }));
    }).flat(),
    { x, y, w, h, fontFace: BODY, fontSize: size || 18, color: C.text, valign: "top", margin: 0, isTextBox: true },
  );
}

function numDot(s, n, x, y, color) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: color || C.amber }, line: { color: color || C.amber } });
  s.addText(String(n), {
    x, y, w: 0.42, h: 0.42, align: "center", valign: "middle", fontFace: HEAD, fontSize: 14,
    bold: true, color: C.bg, margin: 0, isTextBox: true,
  });
}

// ---------- 1. Title ----------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  shot(s, "01-overview.png", 6.3, 1.2, 6.4, 3.6, "plant map, Line 2 stopped");
  draftTag(s);
  s.addText([
    { text: "Line", options: { color: C.text } },
    { text: "Sleuth", options: { color: C.amber } },
  ], { x: M, y: 1.6, w: 5.6, h: 1.1, fontFace: HEAD, fontSize: 54, bold: true, margin: 0, isTextBox: true });
  s.addText("Root-cause investigations for small factories, with evidence you can check.", {
    x: M, y: 2.8, w: 5.4, h: 1.2, fontFace: BODY, fontSize: 22, color: C.text2, margin: 0, isTextBox: true,
  });
  s.addText("AI Builder Cup 2026 · Manufacturing", {
    x: M, y: 5.6, w: 6, h: 0.35, fontFace: BODY, fontSize: 14, color: C.muted, margin: 0, isTextBox: true,
  });
  s.addText("Hung Che Nick Lai", {
    x: M, y: 5.95, w: 6, h: 0.35, fontFace: BODY, fontSize: 14, bold: true, color: C.text, margin: 0, isTextBox: true,
  });
  s.addNotes("On screen while we are introduced. Nothing to say.");
}

// ---------- 2. 3 a.m. Line 2 stops ----------
{
  const s = base(null, "The problem");
  s.addText("03:00", {
    x: M, y: 1.3, w: 5.6, h: 2.0, fontFace: HEAD, fontSize: 110, bold: true, color: C.red, margin: 0, isTextBox: true,
  });
  s.addText("Line 2 stops.", {
    x: M, y: 3.35, w: 5.6, h: 0.8, fontFace: HEAD, fontSize: 36, bold: true, color: C.text, margin: 0, isTextBox: true,
  });
  bullets(s, [
    [{ text: "Every hour of downtime costs " }, { text: "X*", bold: true, color: C.amber }],
    [{ text: "Finding the cause: " }, { text: "~40 min*", bold: true, color: C.amber }, { text: " of Excel and PLC logs" }],
    [{ text: "The night supervisor is alone" }],
  ], M, 4.5, 6.2, 2.0, 20);
  // messy file stack visual
  const files = [["Line2_temps.xlsx", 7.4, 1.6], ["PLC_export_0300.csv", 8.3, 2.5], ["shift_log.xlsx", 7.7, 3.5], ["alarms_L2.csv", 9.2, 4.4]];
  files.forEach(([name, x, y]) => {
    card(s, x, y, 3.4, 0.8, C.s2);
    s.addText(name, { x: x + 0.25, y, w: 3.0, h: 0.8, valign: "middle", fontFace: BODY, fontSize: 16, color: C.text2, margin: 0, isTextBox: true });
  });
  pending(s, "* pending validation: plant-manager interviews not yet completed.");
  s.addNotes("Script Segment 1 (0:00-0:15). If numbers are still unvalidated, drop the X line and keep the footnote on 40 min. Switch to the live app at about 0:15.");
}

// ---------- 3. Who we serve ----------
{
  const s = base("Who we serve", "Customer");
  card(s, M, 1.9, 5.8, 3.9);
  s.addText("Night-shift supervisor", { x: M + 0.35, y: 2.1, w: 5.2, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, color: C.text, margin: 0, isTextBox: true });
  s.addText("Contract manufacturer, 50–300 staff*", { x: M + 0.35, y: 2.6, w: 5.2, h: 0.4, fontFace: BODY, fontSize: 15, color: C.muted, margin: 0, isTextBox: true });
  bullets(s, [
    "No MES; data lives in Excel sheets and PLC CSV exports",
    "At night, decides alone; engineers are off site",
    "Every stoppage is a manual log hunt",
  ], M + 0.35, 3.3, 5.2, 3.0, 18);
  s.addText("“China plus one” is moving production south", {
    x: 7.0, y: 1.95, w: 5.7, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: C.text, margin: 0, isTextBox: true,
  });
  const regions = ["Vietnam", "Thailand", "Malaysia", "Taiwan"];
  regions.forEach((r, i) => {
    const x = 7.0 + (i % 2) * 2.9;
    const y = 2.7 + Math.floor(i / 2) * 1.35;
    card(s, x, y, 2.7, 1.1, C.s2);
    s.addText(r, { x, y, w: 2.7, h: 1.1, align: "center", valign: "middle", fontFace: HEAD, fontSize: 20, bold: true, color: C.amber, margin: 0, isTextBox: true });
  });
  s.addText("Small plants the big industrial platforms don't reach.", {
    x: 7.0, y: 5.6, w: 5.7, h: 0.6, fontFace: BODY, fontSize: 16, italic: true, color: C.text2, margin: 0, isTextBox: true,
  });
  pending(s, "* plant size pending interviews · China+1 trend: public source to verify.");
  s.addNotes("Submission only. Target plant size comes from the PRD and still needs interview confirmation. Add a public source for China+1 before use.");
}

// ---------- 4. One button ----------
{
  const s = base("One button: evidence, root cause, work order", "Solution");
  draftTag(s);
  const cols = [
    ["02-investigating.png", "Press Investigate", "No chat box, no prompt"],
    ["03-root-cause.png", "Evidence → root cause", "Every card traces back to source rows"],
    ["06-wo-modal.png", "Work order by QR", "On the technician's phone"],
  ];
  cols.forEach(([file, head, sub], i) => {
    const x = M + i * 4.1;
    shot(s, file, x, 1.95, 3.85, 2.17, head);
    numDot(s, i + 1, x, 4.4);
    s.addText(head, { x: x + 0.55, y: 4.38, w: 3.3, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: C.text, margin: 0, isTextBox: true });
    s.addText(sub, { x: x + 0.55, y: 4.85, w: 3.3, h: 0.7, fontFace: BODY, fontSize: 15, color: C.text2, margin: 0, isTextBox: true });
  });
  card(s, M, 5.85, W - 2 * M, 0.9, C.s2);
  s.addText([
    { text: "Gemini picks from 5 fixed, tested queries — it never writes SQL. ", options: { color: C.text } },
    { text: "Confidence is scored by the server.", options: { color: C.amber, bold: true } },
  ], { x: M + 0.3, y: 5.85, w: W - 2 * M - 0.6, h: 0.9, valign: "middle", fontFace: BODY, fontSize: 17, margin: 0, isTextBox: true });
  s.addNotes("Submission only. In the live pitch the app shows this itself.");
}

// ---------- 5. Live demo (fallback) ----------
{
  const s = base("Live: Line 2, 03:00", "Demo");
  draftTag(s);
  const frames = [
    ["01-overview.png", "03:00 — Line 2 stops."],
    ["02-investigating.png", "One click. No prompt."],
    ["03-root-cause.png", "Every number traces back to a source data row."],
    ["04-conclusion.png", "Root cause + confidence + what was ruled out."],
    ["05-before-after.png", "Before → after*"],
  ];
  frames.forEach(([file, cap], i) => {
    const w = 2.3, h = 1.29;
    const x = M + i * 2.45;
    shot(s, file, x, 2.3, w, h, `frame ${i + 1}`);
    numDot(s, i + 1, x, 3.8);
    s.addText(cap, { x: x + 0.5, y: 3.78, w: w - 0.45, h: 1.3, fontFace: BODY, fontSize: 13, color: C.text, valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Backup video: stored on the laptop, not streamed.", {
    x: M, y: 5.2, w: 8, h: 0.4, fontFace: BODY, fontSize: 14, color: C.muted, margin: 0, isTextBox: true,
  });
  pending(s, "* before-time pending interviews; after-time measured: median 12.6 s per investigation (gemini-2.5-flash, docs/qa/runs).");
  s.addNotes("Script Segments 2-5. Only shown if the live app fails.");
}

// ---------- 6. No evidence, no conclusion ----------
{
  const s = base("No evidence, no conclusion", "Trust");
  draftTag(s);
  shot(s, "07-insufficient.png", M, 1.95, 6.2, 3.49, "Insufficient evidence grey card");
  s.addText("On healthy data LineSleuth answers “Insufficient evidence”, lists what it checked, and hands the decision back to a human.", {
    x: 7.2, y: 1.95, w: 5.5, h: 1.4, fontFace: BODY, fontSize: 18, color: C.text, margin: 0, isTextBox: true,
  });
  bullets(s, [
    "Gemini can only call fixed queries with checked parameters",
    "Numbers on cards come from source rows, not the model",
    "A root cause needs 2+ evidence cards",
    "Logs treated as untrusted data (prompt-injection tested)",
  ], 7.2, 3.55, 5.5, 3.0, 16);
  s.addNotes("Script Segment 6 is the live version. For the submission deck this is the trust argument; keep it.");
}

// ---------- 7. Built on Google Cloud ----------
{
  const s = base("Built on Google Cloud", "Architecture");
  const box = (label, sub, x, y, w, color) => {
    card(s, x, y, w, 1.05, C.s2);
    s.addText(label, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.45, fontFace: HEAD, fontSize: 17, bold: true, color: color || C.text, margin: 0, isTextBox: true });
    s.addText(sub, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: 0.4, fontFace: BODY, fontSize: 13, color: C.text2, margin: 0, isTextBox: true });
  };
  box("Browser · Phone", "Supervisor screen, QR work order", M, 3.0, 2.8);
  box("Cloud Run", "UI + API · asia-southeast1", 4.3, 3.0, 2.8, C.amber);
  box("Vertex AI Gemini", "Function calling · 5 fixed queries · temp 0", 8.3, 1.85, 4.4, C.blue);
  // 9/24 meeting: demo data is DuckDB inside the Cloud Run image. BigQuery is only "swappable", never "supported".
  box("DuckDB · demo data", "In the Cloud Run image · swappable for BigQuery", 8.3, 3.0, 4.4);
  box("Cloud Logging", "Every query replayable", 8.3, 4.15, 4.4, C.blue);
  // Line extents must be non-negative; an upward arrow is drawn with flipV.
  const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, {
    x: x1, y: Math.min(y1, y2), w: x2 - x1, h: Math.abs(y2 - y1), flipV: y2 < y1,
    line: { color: C.borderStrong, width: 2, endArrowType: "triangle" },
  });
  arrow(3.45, 3.52, 4.25, 3.52);
  arrow(7.15, 3.35, 8.25, 2.4);
  arrow(7.15, 3.52, 8.25, 3.52);
  arrow(7.15, 3.7, 8.25, 4.65);
  const chips = ["IAM least privilege", "Secret Manager*", "Budget alerts 50/90/100%", "Rate limits"];
  chips.forEach((c, i) => {
    const x = M + i * 3.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.75, w: 2.85, h: 0.6, rectRadius: 0.3, fill: { color: C.s1 }, line: { color: C.borderStrong, width: 1 } });
    s.addText(c, { x, y: 5.75, w: 2.85, h: 0.6, align: "center", valign: "middle", fontFace: BODY, fontSize: 14, color: C.text, margin: 0, isTextBox: true });
  });
  pending(s, "* show Secret Manager only if the presenter key is stored there at submission. Model name only after it is verified.");
  s.addNotes("Spoken during Segment 3 of the live pitch. Name the Gemini model only after verifying it in Model Garden; otherwise just say Gemini.");
}

// ---------- 8. How we're different ----------
{
  const s = base("How we're different", "Positioning");
  const hdr = (t, hi) => ({ text: t, options: { bold: true, color: hi ? C.bg : C.text2, fill: { color: hi ? C.amber : C.s1 } } });
  const cell = (t, hi) => ({ text: t, options: { color: hi ? C.bg : C.text, bold: !!hi, fill: { color: hi ? C.amber : C.s2 } } });
  const rows = [
    [hdr(""), hdr("Siemens Industrial Copilot"), hdr("Cognite"), hdr("Google MDE"), hdr("LineSleuth", true)],
    [cell("Built for"), cell("Large plants in the Siemens ecosystem†"), cell("Asset-heavy enterprises with data teams†"), cell("Plants building a data platform on Google Cloud†"), cell("Small contract manufacturers without MES", true)],
    [cell("Starts from"), cell("Automation / MES data†"), cell("Industrial data platform†"), cell("Connected factory data†"), cell("Excel sheets and PLC CSV exports", true)],
    [cell("Job to be done"), cell("Broad industrial assistant"), cell("Industrial data operations"), cell("Data engine"), cell("Why did this line stop — with evidence", true)],
    [cell("Pricing"), cell("Enterprise"), cell("Enterprise"), cell("Platform"), cell("Onboarding fee + per-line monthly", true)],
  ];
  s.addTable(rows, {
    x: M, y: 1.9, w: W - 2 * M, colW: [1.9, 2.75, 2.5, 2.75, 2.23],
    fontFace: BODY, fontSize: 14, valign: "middle", border: { type: "solid", pt: 1, color: C.bg },
    rowH: [0.55, 0.95, 0.8, 0.8, 0.8], margin: 0.1,
  });
  s.addText("Google MDE is the platform our customers can grow into.", {
    x: M, y: 6.25, w: 10, h: 0.4, fontFace: BODY, fontSize: 15, italic: true, color: C.text2, margin: 0, isTextBox: true,
  });
  pending(s, "† competitor descriptions to verify against current public vendor material.");
  s.addNotes("Script Segment 7. Check every competitor cell against current public material. Never disparage.");
}

// ---------- 9. Business model ----------
{
  const s = base("Business model", "Revenue");
  const block = (x, label, price, sub) => {
    card(s, x, 1.95, 5.8, 2.4, C.s1);
    s.addText(label, { x: x + 0.35, y: 2.15, w: 5.1, h: 0.4, fontFace: HEAD, fontSize: 14, bold: true, color: C.muted, charSpacing: 2, margin: 0, isTextBox: true });
    s.addText(price, { x: x + 0.35, y: 2.6, w: 5.1, h: 0.9, fontFace: HEAD, fontSize: 40, bold: true, color: C.amber, margin: 0, isTextBox: true });
    s.addText(sub, { x: x + 0.35, y: 3.5, w: 5.1, h: 0.7, fontFace: BODY, fontSize: 16, color: C.text2, margin: 0, isTextBox: true });
  };
  block(M, "ONE-TIME", "X*", "Onboarding: turn Excel / PLC exports into clean data");
  block(6.93, "PER LINE / MONTH", "X*", "Subscription, priced below the downtime and labour it saves");
  card(s, M, 4.65, W - 2 * M, 1.5, C.s2);
  s.addText("Value per line per month", { x: M + 0.35, y: 4.8, w: 8, h: 0.4, fontFace: HEAD, fontSize: 15, bold: true, color: C.text, margin: 0, isTextBox: true });
  s.addText("incidents / month  ×  time saved  ×  downtime cost / hour  ×  share of time spent searching", {
    x: M + 0.35, y: 5.25, w: W - 2 * M - 0.7, h: 0.6, fontFace: BODY, fontSize: 18, color: C.text2, margin: 0, isTextBox: true,
  });
  pending(s, "* all amounts pending plant-manager interviews (model: docs/finance/roi-model.csv). Buyer: plant manager or owner — to confirm.");
  s.addNotes("Script Segment 8. Inputs are assumptions; show no numbers unless they come from interviews. Do not show gross margin: Gemini and GCP costs not yet estimated.");
}

// ---------- 10. Roadmap ----------
{
  const s = base("Roadmap", "What's next");
  const cols = [
    ["NOW · prototype", C.amber, ["One plant, simulated data", "Main story + grey-card test", "English work order via QR", "Regression set, 10 known root causes"]],
    ["NEXT", C.blue, ["Design-partner pilots on de-identified data", "Excel / PLC CSV import", "Vietnamese and Thai work orders", "Accounts and permissions"]],
    ["LATER", C.grey, ["Multiple lines and plants", "Multiple root causes per investigation", "Push notifications", "Early warning before a stoppage"]],
  ];
  cols.forEach(([head, color, items], i) => {
    const x = M + i * 4.1;
    card(s, x, 1.95, 3.85, 3.7, C.s1);
    s.addText(head, { x: x + 0.3, y: 2.15, w: 3.3, h: 0.45, fontFace: HEAD, fontSize: 15, bold: true, color, charSpacing: 2, margin: 0, isTextBox: true });
    bullets(s, items, x + 0.3, 2.8, 3.3, 3.6, 16);
  });
  pending(s, "No dates on Next / Later: they depend on design partners. Vietnamese work order is a concept, not in the prototype.");
  s.addNotes("Script Segment 9. Do not promise Vietnamese support beyond 'roadmap'.");
}

// ---------- 11. Close ----------
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  s.addText([
    { text: "Stoppage ", options: { color: C.text } },
    { text: "→ ", options: { color: C.amber } },
    { text: "root cause in ~12 s*", options: { color: C.text } },
  ], { x: M, y: 1.7, w: W - 2 * M, h: 1.6, align: "center", fontFace: HEAD, fontSize: 50, bold: true, margin: 0, isTextBox: true });
  s.addText("Every conclusion backed by evidence.", {
    x: M, y: 3.35, w: W - 2 * M, h: 0.7, align: "center", fontFace: BODY, fontSize: 28, color: C.text2, margin: 0, isTextBox: true,
  });
  card(s, 2.4, 4.6, 8.53, 1.3, C.s1);
  s.addText([
    { text: "Hung Che Nick Lai", options: { bold: true, color: C.text, breakLine: true } },
    { text: "hongchelai@gmail.com  ·  Live prototype: linesleuth-547147056278.asia-southeast1.run.app", options: { color: C.text2 } },
  ], { x: 2.4, y: 4.6, w: 8.53, h: 1.3, align: "center", valign: "middle", fontFace: BODY, fontSize: 17, margin: 0, isTextBox: true });
  s.addText("* measured median 12.6 s per investigation (gemini-2.5-flash, 10 root causes × 3 runs, docs/qa/runs) · manual baseline pending interviews", {
    x: M, y: 6.8, w: W - 2 * M, h: 0.3, align: "center", fontFace: BODY, fontSize: 11, italic: true, color: C.amber, margin: 0, isTextBox: true,
  });
  s.addNotes("Script Segment 10. Stay on this slide during Q&A.");
}

// ---------- A1. Validation status ----------
{
  const s = base("Validation status", "Appendix");
  const rows = [
    ["Regression set (10 known root causes, 3 distractors; bar ≥ 9/10, 3 runs each)", "10 / 10 (real Gemini)"],
    ["Healthy data returns “Insufficient evidence”", "2 / 2"],
    ["Median time to conclusion (gemini-2.5-flash, docs/qa/runs)", "12.6 s"],
    ["Plant-manager interviews completed", "[pending interviews]"],
  ];
  rows.forEach(([k, v], i) => {
    const y = 1.95 + i * 1.1;
    card(s, M, y, W - 2 * M, 0.9, C.s1);
    s.addShape(pres.shapes.OVAL, { x: M + 0.3, y: y + 0.27, w: 0.36, h: 0.36, fill: { color: C.s3 }, line: { color: C.grey, width: 1.5 } });
    s.addText(k, { x: M + 0.9, y, w: 8.4, h: 0.9, valign: "middle", fontFace: BODY, fontSize: 17, color: C.text, margin: 0, isTextBox: true });
    s.addText(v, { x: 9.6, y, w: 3.0, h: 0.9, valign: "middle", align: "right", fontFace: HEAD, fontSize: 16, bold: true, color: C.amber, margin: 0, isTextBox: true });
  });
  s.addNotes("Use in Q&A for 'does it really work?' and 'did you talk to customers?'. Only show measured results.");
}

// ---------- A2. Known limitations ----------
{
  const s = base("Known limitations", "Appendix");
  const items = [
    ["Data", "Simulated data; no live PLC / MES connection yet"],
    ["Scope", "One root cause per investigation"],
    ["Language", "English only"],
    ["Security", "No login in the prototype; not ready for real customer data"],
  ];
  items.forEach(([head, text], i) => {
    const x = M + (i % 2) * 6.13;
    const y = 1.95 + Math.floor(i / 2) * 2.2;
    card(s, x, y, 5.93, 1.95, C.s1);
    s.addText(head.toUpperCase(), { x: x + 0.35, y: y + 0.3, w: 5.2, h: 0.35, fontFace: HEAD, fontSize: 13, bold: true, color: C.grey, charSpacing: 2, margin: 0, isTextBox: true });
    s.addText(text, { x: x + 0.35, y: y + 0.75, w: 5.2, h: 1.0, fontFace: BODY, fontSize: 20, color: C.text, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes("Being upfront about limits builds trust. Details in docs/manual/user-manual.md Section 11.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
