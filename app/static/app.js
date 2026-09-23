// LineSleuth front end. Plain JS, no build step. Copy follows docs/design/storyboard.md section 5 (v2: 5.8-5.10);
// layout, evidence charts, plant-map states and the Recap follow docs/design/ui-v2-spec.md.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { config: null, scenarios: [], scenario: null, invId: null, poll: null, tick: null,
                loadedAt: 0, rendered: {}, conclusionShown: false, autoScroll: true, inv: null, woId: null,
                manual: new Set(), rowsOpen: new Set(), drawn: new Set(),   // evidence accordion (ui-v2-spec 1.8)
                mapTimers: [], tweenId: 0, modalOpener: null, recapOpener: null, recapTimer: null };

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) e.append(c instanceof Node ? c : String(c));
  return e;
}
const SVGNS = "http://www.w3.org/2000/svg";
function sv(tag, attrs = {}, ...children) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) e.setAttribute(k, v);
  for (const c of children.flat()) if (c != null) e.append(c instanceof Node ? c : String(c));
  return e;
}
const pad = (n) => String(n).padStart(2, "0");
const hms = (s) => `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(Math.floor(s % 60))}`;
const mmss = (s) => `${pad(Math.floor(s / 60))}:${pad(Math.floor(s % 60))}`;
const toSec = (t) => { const [h, m, s] = t.split(":").map(Number); return h * 3600 + m * 60 + (s || 0); };
const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const singleColumn = () => matchMedia("(max-width: 1023.98px)").matches;
const scrollBehavior = () => (reduceMotion() ? "auto" : "smooth");
// One rounding for the panel's final Elapsed and the Recap "After" (ui-v2-spec 4.2): both show the same second.
const elapsedSec = (inv) => Math.round(inv.elapsed_s);
const fmtElapsed = (s) => (s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
  return body;
}

// ------------------------------------------------------------------ plant SVG (ui-v2-spec 2)
const OVERVIEW = [0, 0, 1200, 600];
// Root cause -> place on the map. "other" / unknown: nothing is marked (we do not guess for the model).
const RC_TARGET = {
  cv_valve_stuck_closed:    { machine: "M3", valve: true },
  cv_valve_stuck_open:      { machine: "M3", valve: true },
  coolant_supply_temp_high: { machine: "M3" },
  coolant_filter_clogged:   { machine: "M3" },
  heater_stuck_on:          { machine: "M3" },
  temp_sensor_drift:        { machine: "M3" },
  setpoint_change:          { machine: "M3" },
  hydraulic_pressure_low:   { machine: "M3" },
  dryer_temp_low:           { machine: "M2" },
  feeder_blockage:          { machine: "M1" },
};
const DESC_BASE = "Top-down view of Lines 1 to 3. Each line has four machines: M1 Feeder, M2 Dryer, M3 Molding, M4 Inspection.";

function setMachine(line, m, cls, text) {
  const g = $(`L${line}-M${m}`);
  if (!g) return;
  g.classList.remove("is-normal", "is-warn", "is-stopped", "is-idle");
  g.classList.add(cls);
  $(`L${line}-M${m}-state`).textContent = text;
  const name = g.querySelector(".name").textContent;
  g.setAttribute("aria-label", `Line ${line} M${m} ${name}: ${text.toLowerCase()}`);
}
function focusBox(line, m) {                 // 2:1 box around one machine, kept inside the drawing
  const cx = 180 + (m - 1) * 256 + 114, cy = 12 + (line - 1) * 200 + 88, w = 768, h = 384;
  return [Math.min(Math.max(cx - w / 2, 0), 1200 - w), Math.min(Math.max(cy - h / 2, 0), 600 - h), w, h];
}
function tweenViewBox(to, ms) {
  const svg = $("line-layout");
  if (!svg) return;
  const id = ++state.tweenId;
  if (reduceMotion() || !ms) { svg.setAttribute("viewBox", to.join(" ")); return; }
  const b = svg.viewBox.baseVal, from = [b.x, b.y, b.width, b.height];
  const t0 = performance.now(), ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
  requestAnimationFrame(function step(now) {
    if (id !== state.tweenId) return;          // a newer move (or Reset) took over
    const t = Math.min(1, Math.max(0, (now - t0) / ms)), e = ease(t);
    svg.setAttribute("viewBox", from.map((v, i) => v + (to[i] - v) * e).join(" "));
    if (t < 1) requestAnimationFrame(step);
  });
}
function mapLater(fn, ms) {
  if (reduceMotion()) return fn();
  state.mapTimers.push(setTimeout(fn, ms));
}
function clearMapTimers() { state.mapTimers.forEach(clearTimeout); state.mapTimers = []; }
function clearMapMarks() {
  for (let l = 1; l <= 3; l++) {
    $(`L${l}`).classList.remove("is-dimmed", "is-inconclusive");
    $(`L${l}-M3-CV${l}`).classList.remove("is-root-cause");
    for (let m = 1; m <= 4; m++) $(`L${l}-M${m}`).classList.remove("is-focus", "is-root-cause", "is-low-confidence");
  }
}
const focusM = () => (state.scenario.machine ? Number(state.scenario.machine.slice(1)) : 3);
function setPlantDesc(extra, live) {  // role="img" hides the <g> labels from screen readers, so <desc> carries the state
  const s = state.scenario;
  const now = s.stop_ts ? ` Line ${s.line} stopped. ${s.machine_label} stopped.` : " All lines running.";
  $("ls-desc").textContent = DESC_BASE + now + (extra ? ` ${extra}` : "");
  $("plant-live").textContent = live || "";
}
function resetPlant(ms) {
  clearMapTimers();
  for (let l = 1; l <= 3; l++) {
    $(`L${l}`).classList.remove("is-stopped");
    $(`L${l}-status`).textContent = "Running";
    for (let m = 1; m <= 4; m++) setMachine(l, m, "is-normal", "RUNNING");
  }
  clearMapMarks();
  tweenViewBox(OVERVIEW, ms);
}
function mapInvestigating() {                  // M2-M4: +150ms, zoom 700ms, dim the other lanes
  const s = state.scenario, m = focusM();
  mapLater(() => {
    for (let l = 1; l <= 3; l++) $(`L${l}`).classList.toggle("is-dimmed", l !== s.line);
    $(`L${s.line}-M${m}`).classList.add("is-focus");
    tweenViewBox(focusBox(s.line, m), 700);
  }, 150);
}
function mapRootCause(c) {                     // M13-M16 timing lives in the SVG's CSS; JS only swaps classes
  clearMapTimers();
  const line = c.line, t = RC_TARGET[c.root_cause_key];
  if (!t) { clearMapMarks(); tweenViewBox(OVERVIEW, 700); setPlantDesc(""); return; }
  const m = Number(t.machine.slice(1)), g = $(`L${line}-${t.machine}`);
  for (let l = 1; l <= 3; l++) $(`L${l}`).classList.toggle("is-dimmed", l !== line);
  for (let i = 1; i <= 4; i++) $(`L${line}-M${i}`).classList.remove("is-focus");
  g.classList.add("is-root-cause");
  if (c.confidence === "Low") g.classList.add("is-low-confidence");
  if (t.valve) $(`L${line}-M3-CV${line}`).classList.add("is-root-cause");
  tweenViewBox(focusBox(line, m), 700);        // no visible move when it is already the focus machine
  const where = t.valve ? `CV-${line} cooling valve` : `Line ${line} ${t.machine} ${g.querySelector(".name").textContent}`;
  setPlantDesc(t.valve ? `Root cause located: ${where} on Line ${line} M3.` : `Root cause located: ${where}.`,
               t.valve ? `Root cause located on the plant map: ${where}, Line ${line} M3.`
                       : `Root cause located on the plant map: ${where}.`);
}
function mapInconclusive(line) {               // M19-M21: zoom back out, then the grey dashed lane + badge
  clearMapTimers();
  clearMapMarks();
  mapLater(() => tweenViewBox(OVERVIEW, 700), 150);
  mapLater(() => $(`L${line}`).classList.add("is-inconclusive"), 850);
  const msg = `No root cause found on Line ${line}. The whole line was checked.`;
  setPlantDesc(msg, msg);
}
function mapCleared() { clearMapTimers(); clearMapMarks(); tweenViewBox(OVERVIEW, 700); setPlantDesc(""); }

// ------------------------------------------------------------------ scenario + reset (F8)
function applyScenario(animate = false) {
  const s = state.scenario;
  stopPolling();
  Object.assign(state, { invId: null, inv: null, rendered: {}, conclusionShown: false, autoScroll: true,
                         loadedAt: Date.now(), woId: null });
  state.manual.clear(); state.rowsOpen.clear(); state.drawn.clear();
  resetPlant(animate ? 400 : 0);
  $("cards").replaceChildren(); $("result").replaceChildren();
  $("evidence-head").classList.add("hidden");
  $("empty").classList.remove("hidden");
  setChip("Not started", "chip-muted");
  $("elapsed").classList.add("hidden");
  closeModal(false);
  closeRecap(false);
  const alert = $("alert");
  if (s.stop_ts) {
    alert.className = "alert stopped";
    $("alert-title").textContent = `Line ${s.line} stopped`;
    $("alert-sub").textContent = `${s.machine_label} · ${s.alarm} at ${s.stop_ts.slice(0, 5)}`;
    $("downtime-box").classList.remove("hidden");
    $(`L${s.line}`).classList.add("is-stopped");
    $(`L${s.line}-status`).textContent = "Stopped";
    setMachine(s.line, s.machine.slice(1), "is-stopped", "STOPPED");
  } else {
    alert.className = "alert normal";
    $("alert-title").textContent = "All lines running";
    $("alert-sub").textContent = "No active alarms";
    $("downtime-box").classList.add("hidden");
  }
  setPlantDesc("");
  setButton("idle");
  tick();
}
function tick() {
  const s = state.scenario;
  const passed = Math.floor((Date.now() - state.loadedAt) / 1000);
  const now = toSec(s.now) + passed;
  $("clock").textContent = hms(now);
  if (s.stop_ts) $("downtime").textContent = hms(now - toSec(s.stop_ts));  // keeps running after conclusion
}
async function doReset() {
  try { await api("/api/reset", { method: "POST", body: JSON.stringify({ scenario_id: state.scenario.id }) }); } catch (e) { /* still reset UI */ }
  applyScenario(true);
}

// ------------------------------------------------------------------ investigate (F2)
function setButton(mode) {
  const b = $("investigate");
  const s = state.scenario;
  const idleLabel = s.stop_ts ? "Investigate" : `Investigate Line ${s.line}`;
  const label = { idle: idleLabel, running: "Investigating…", done: "Investigated" }[mode];
  $("investigate-label").textContent = label;
  b.disabled = mode !== "idle";
  b.setAttribute("aria-busy", mode === "running" ? "true" : "false");
  $("investigate-icon").replaceChildren();
  if (mode === "running") $("investigate-icon").append(el("span", { class: "spinner" }));
  else $("investigate-icon").innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="10" cy="10" r="7"/><path d="M15.5 15.5 21 21"/></svg>';
}
function setChip(text, cls) { const c = $("status-chip"); c.textContent = text; c.className = `chip ${cls}`; }

async function investigate() {
  setButton("running");
  setChip("Investigating", "chip-info");
  $("empty").classList.add("hidden");
  $("elapsed").classList.remove("hidden");
  mapInvestigating();
  try {
    const inv = await api("/api/investigations", { method: "POST", body: JSON.stringify({ scenario_id: state.scenario.id }) });
    state.invId = inv.id;
    render(inv);
    if (inv.status === "running") state.poll = setInterval(pollOnce, 700);
  } catch (e) {
    showFailure(e.message);
  }
}
function stopPolling() { if (state.poll) clearInterval(state.poll); state.poll = null; }
async function pollOnce() {
  if (!state.invId) return;
  const id = state.invId;
  try {
    const inv = await api(`/api/investigations/${id}`);
    if (id === state.invId) render(inv);
  } catch (e) { /* transient; keep polling */ }
}

// ------------------------------------------------------------------ rendering (F4-F6)
function render(inv) {
  state.inv = inv;
  $("elapsed").textContent = `Elapsed ${mmss(elapsedSec(inv))}`;
  for (const step of inv.steps) renderStep(inv, step);
  if (inv.status === "running") return;
  stopPolling();
  setButton("done");
  if (state.conclusionShown) return;
  state.conclusionShown = true;
  if (inv.status === "root_cause") renderConclusion(inv);
  else if (inv.status === "insufficient_evidence") renderGrey(inv);
  else if (inv.status === "failed") showFailure(inv.error);
}

function renderStep(inv, step) {
  const sig = JSON.stringify([step.status, step.card && step.card.key_value]);
  const existing = state.rendered[step.step];
  if (existing && existing.sig === sig) return;
  if (!existing) collapseOthers(step.step);             // rule 1: only the newest card stays full
  const compact = existing ? existing.node.classList.contains("is-compact") : false;
  const row = buildRow(inv, step, !existing, compact);
  if (existing) existing.node.replaceWith(row); else $("cards").append(row);
  state.rendered[step.step] = { sig, node: row, step };
  drawRowCharts(step.step);
  if (state.autoScroll && !state.conclusionShown) row.scrollIntoView({ block: "nearest", behavior: scrollBehavior() });
}

function buildRow(inv, step, isNew, compact) {
  const n = step.step, c = step.card || {};
  const tone = c.tone === "danger" ? "danger" : c.tone === "warn" ? "warn" : "";
  const ok = step.status === "done" || step.status === "cached";
  const title = c.title || step.function;
  let stateEl;
  if (step.status === "running") stateEl = el("span", { class: "card-state" }, el("span", { class: "spinner" }), "Querying…");
  else if (step.status === "error") stateEl = el("span", { class: "card-state error-text" }, "Failed");
  else if (step.status === "cached") stateEl = el("span", { class: "chip chip-warn", title: "Live query timed out. Showing last verified result." }, "Cached");
  else stateEl = el("span", { class: "card-state" }, el("span", { class: "ok" }, "✓"), "Done");
  const collapseBtn = step.status === "running" ? null : el("button", { class: "collapse-btn", type: "button",
    "aria-expanded": "true", "aria-controls": `card-${n}-full`, "aria-label": `Collapse step ${n}`,
    onclick: () => userToggle(n, true) }, "▾");

  const body = [];
  if (step.status === "running") {
    body.push(el("div", { class: "skeleton" }), el("div", { class: "skeleton", style: "width:60%" }));
    if (step.function !== "list_sensors") body.push(el("div", { class: "chart-skel", "aria-hidden": "true" }));
  } else if (step.status === "error") body.push(el("div", { class: "error-text" }, "Query failed"));
  else {
    body.push(el("div", { class: "key" }, el("span", { class: `key-value ${tone}` }, c.key_value), el("span", { class: "key-detail" }, c.key_detail)));
    if (c.chart) body.push(el("div", { class: "chart" }));
    if (c.secondary) body.push(el("div", { class: "secondary" }, c.secondary));
  }
  const meta = el("div", { class: "meta" }, el("span", { class: "mono" }, step.function),
    step.time_range ? ` · ${step.time_range}` : "", step.row_count != null ? ` · ${step.row_count} rows` : "");
  const card = el("div", { class: "card", id: `card-${n}-full` },
    el("div", { class: "card-title" }, el("h3", {}, title), el("span", { class: "card-title-right" }, stateEl, collapseBtn)),
    ...body, meta, el("div", { class: "tags" }));
  if (ok) {
    const rowsBox = el("div", { class: "rows hidden" });
    const btn = el("button", { class: "btn-text", type: "button", "aria-expanded": "false" }, `View source rows (${step.row_count})`);
    btn.addEventListener("click", () => toggleRows(inv.id, step, btn, rowsBox));
    card.append(btn, rowsBox);
  }

  const line2 = step.status === "error"
    ? [el("span", { class: "c-value error-text" }, "Query failed")]
    : [el("span", { class: `c-value ${tone}` }, c.key_value || ""),
       step.status === "cached" ? el("span", { class: "c-tag chip-warn" }, "Cached") : null,
       el("span", { class: "c-tags" }), el("span", { class: "c-caret", "aria-hidden": "true" }, "▸")];
  const compactBtn = el("button", { class: "compact", type: "button", "aria-expanded": String(!compact),
    "aria-controls": `card-${n}-full`, onclick: () => userToggle(n, false) },
    el("span", { class: "c-title" }, title), el("span", { class: "c-line2" }, line2),
    el("span", { class: "c-mini", "aria-hidden": "true" }));
  const row = el("div", { class: `card-row${isNew ? " is-new" : ""}${compact ? " is-compact" : ""}`, id: `card-${n}` },
    el("div", { class: "step-no" }, n), el("div", { class: "card-slot" }, compactBtn, card));
  row.dataset.tag = "";
  setCompactLabel(row, n, title, step.status === "error" ? "Query failed" : c.key_value);
  return row;
}
function setCompactLabel(row, n, title, value) {
  const tag = row.dataset.tag === "cited" ? ", cited in conclusion" : row.dataset.tag === "ruled" ? ", ruled out" : "";
  row.querySelector(".compact").setAttribute("aria-label", `Step ${n}, ${title}, ${value || ""}${tag}. Show details`);
}

// ---- accordion: full card <-> compact row (ui-v2-spec 1.8)
function setCompact(n, compact) {
  const r = state.rendered[n];
  if (!r || r.node.classList.contains("is-compact") === compact) return;
  if (compact && r.step.status === "running") return;    // a running step has no compact row
  r.node.classList.toggle("is-compact", compact);
  r.node.querySelector(".compact").setAttribute("aria-expanded", String(!compact));
  const shown = r.node.querySelector(compact ? ".compact" : ".card");
  if (!reduceMotion()) { shown.classList.remove("swap-in"); void shown.offsetWidth; shown.classList.add("swap-in"); }
  if (!compact) drawFullChart(n);                          // it may have been hidden at the last resize
}
function collapseOthers(newest) {
  for (const k of Object.keys(state.rendered)) if (Number(k) !== newest && !state.manual.has(Number(k))) setCompact(Number(k), true);
}
function collapseForResult() {                             // rule 4: all compact, except rows being read
  for (const k of Object.keys(state.rendered)) if (!state.rowsOpen.has(Number(k))) setCompact(Number(k), true);
  state.manual.clear();
}
function userToggle(n, collapse) {
  state.autoScroll = false;
  if (collapse) state.manual.delete(n); else state.manual.add(n);
  setCompact(n, collapse);
  const r = state.rendered[n];
  const target = r && r.node.querySelector(collapse ? ".compact" : ".collapse-btn");
  if (target) target.focus();
}

async function toggleRows(invId, step, btn, box) {
  const open = btn.getAttribute("aria-expanded") === "true";
  if (open) {
    box.classList.add("hidden"); btn.textContent = `View source rows (${step.row_count})`; btn.setAttribute("aria-expanded", "false");
    state.rowsOpen.delete(step.step); return;
  }
  state.rowsOpen.add(step.step);
  if (!box.dataset.loaded) {
    try {
      const ev = await api(`/api/investigations/${invId}/evidence/${step.step}`);
      const cols = ev.rows.length ? Object.keys(ev.rows[0]) : [];
      const hl = new Set(ev.highlight_row_ids);
      const table = el("table", {}, el("thead", {}, el("tr", {}, cols.map((k) => el("th", {}, k)))),
        el("tbody", {}, ev.rows.map((r) => el("tr", { class: hl.has(r.row_id) ? "hl" : "" }, cols.map((k) => el("td", {}, r[k] ?? ""))))));
      box.append(el("div", { class: "rows-scroll" }, table),
        el("div", { class: "source" }, `Source: ${ev.source} · ${ev.row_count} rows · query ${ev.query_id}`));
      box.dataset.loaded = "1";
      const first = table.querySelector("tr.hl");
      box.classList.remove("hidden");
      if (first) first.scrollIntoView({ block: "nearest" });
    } catch (e) { box.append(el("div", { class: "error-text" }, "Query failed")); }
  }
  box.classList.remove("hidden");
  btn.textContent = "Hide source rows"; btn.setAttribute("aria-expanded", "true");
}

function tagCard(n, kind) {
  const r = state.rendered[n];
  if (!r) return;
  const cited = kind === "cited";
  r.node.querySelector(".tags").append(el("span", { class: `tag ${cited ? "tag-cited" : "tag-ruled"}` }, cited ? "Cited in conclusion" : "Ruled out"));
  const slot = r.node.querySelector(".c-tags");
  if (slot) slot.append(el("span", { class: `c-tag ${cited ? "tag-cited" : "tag-ruled"}` }, cited ? "Cited" : "Ruled out"));
  r.node.dataset.tag = kind;
  const c = r.step.card || {};
  setCompactLabel(r.node, n, c.title || r.step.function, c.key_value);
}
function flashCard(n) {                                    // rule 5: citation chip -> scroll, expand, flash
  const r = state.rendered[n];
  if (!r) return;
  state.manual.add(n);
  setCompact(n, false);
  const card = $(`card-${n}-full`);
  card.scrollIntoView({ block: "nearest", behavior: scrollBehavior() });
  card.classList.add("flash"); setTimeout(() => card.classList.remove("flash"), 1200);
}

function showEvidenceHead(inv) {
  if (!inv || !inv.steps.length) return;
  const head = $("evidence-head");
  head.textContent = `Evidence · ${plural(inv.steps.length, "query", "queries")}`;
  head.classList.remove("hidden");
}
function scrollToResult() {
  if (singleColumn()) $("result").scrollIntoView({ block: "start", behavior: scrollBehavior() });
  else $("cards").scrollTo({ top: 0, behavior: scrollBehavior() });
}

function renderConclusion(inv) {
  const c = inv.conclusion;
  setChip("Root cause found", "chip-warn");
  collapseForResult();
  c.cited_evidence.forEach((n) => tagCard(n, "cited"));
  c.ruled_out.forEach((r) => tagCard(r.evidence_id, "ruled"));
  mapRootCause(c);
  const bars = { High: 3, Medium: 2, Low: 1 }[c.confidence];
  const nActions = c.recommended_actions.length;
  const disclosure = nActions ? el("button", { class: "btn-text disclosure", type: "button", "aria-expanded": "false",
    "aria-controls": "rc-actions" }, `▸ Recommended actions (${nActions})`) : el("span");
  const actions = el("div", { class: "conc-actions" },
    nActions ? el("div", { class: "subhead actions-head" }, "Recommended actions") : null,
    nActions ? el("ol", { class: "actions-list", id: "rc-actions" }, c.recommended_actions.map((a) => el("li", {}, a))) : null,
    el("div", { class: "conclusion-foot" }, disclosure,
      el("button", { class: "btn-outline", type: "button", id: "create-wo", onclick: createWorkOrder }, "Create work order")));
  if (nActions) disclosure.addEventListener("click", () => {
    const open = actions.classList.toggle("is-open");
    disclosure.setAttribute("aria-expanded", String(open));
    disclosure.textContent = `${open ? "▾" : "▸"} Recommended actions (${nActions})`;
  });
  const box = el("div", { class: "conclusion" },
    c.confidence === "Low" ? el("div", { class: "low-warn" }, "Low confidence — verify on site before acting.") : null,
    el("div", { class: "conc-head" }, el("div", { class: "eyebrow" }, "Root cause"),
      el("div", { class: "conf" }, el("span", { class: "bars", "aria-hidden": "true" }, [1, 2, 3].map((i) => el("i", { class: i <= bars ? "on" : "" }))), `Confidence: ${c.confidence}`)),
    el("div", { class: "root-cause" }, c.root_cause),
    el("div", { class: "conf-reason" }, c.confidence_reason),
    el("div", { class: "conc-line" }, el("div", { class: "subhead" }, "Evidence"),      // label inline on short screens
      el("div", {}, c.cited_evidence.map((n) => el("button", { class: "cite", type: "button", onclick: () => flashCard(n) }, `#${n}`)))),
    c.ruled_out.length ? el("div", { class: "conc-line" }, el("div", { class: "subhead" }, "Ruled out"),
      el("div", {}, c.ruled_out.map((r) => el("div", {}, `${r.text} (#${r.evidence_id})`)))) : null,
    actions);
  $("result").replaceChildren(box);
  showEvidenceHead(inv);
  scrollToResult();
}

function renderGrey(inv) {
  const c = inv.conclusion;
  setChip("Insufficient evidence", "chip-grey");
  collapseForResult();
  mapInconclusive(c.line);
  const box = el("div", { class: "grey" },
    el("div", { class: "grey-head" }, el("div", { class: "grey-icon", "aria-hidden": "true" }, "?"), el("h3", {}, "Insufficient evidence")),
    el("p", {}, "No root cause found. LineSleuth will not guess."),
    el("div", { class: "subhead" }, "Checked"),
    el("ul", {}, c.checked.map((k) => el("li", {}, el("span", { class: "check" }, "✓"), `${k.name} — `, el("span", { class: "res" }, k.result)))),
    el("div", { class: "subhead", style: "font-size:var(--fs-md);color:var(--color-grey-text)" }, "Recommended next step"),
    el("p", {}, c.next_step));
  $("result").replaceChildren(box);
  showEvidenceHead(inv);
  scrollToResult();
}

function showFailure(msg) {
  stopPolling();
  if (state.scenario) { mapCleared(); setButton("done"); }
  setChip("Investigation failed", "chip-danger");
  $("result").replaceChildren(el("div", { class: "fail" }, el("p", {}, "Investigation failed. Press Reset and try again."),
    el("p", { class: "meta" }, msg || "")));
  if (state.inv) { collapseForResult(); showEvidenceHead(state.inv); }
}

// ------------------------------------------------------------------ evidence charts (ui-v2-spec 1.4-1.7)
// Inline SVG, no chart library. Every point is a raw row value from card.chart; nothing is smoothed or filled in.
let chartSeq = 0;
const EASE_DECEL = "cubic-bezier(0, 0, 0.2, 1)";
const cssPx = (node, name) => parseFloat(getComputedStyle(node).getPropertyValue(name)) || 0;
const pts = (ch, role) => ((ch.series || []).find((s) => s.role === role) || { points: [] }).points
  .map(([t, v, id]) => ({ t: toSec(t), v, id }));
const hasPoints = (ch) => pts(ch, "actual").some((p) => p.v != null);

function segmentsOf(points) {                   // new sub-path at a missing value or a jump of more than 90 s
  const segs = []; let cur = [];
  for (const p of points) {
    if (p.v == null) { if (cur.length) segs.push(cur); cur = []; continue; }
    if (cur.length && p.t - cur[cur.length - 1].t > 90) { segs.push(cur); cur = []; }
    cur.push(p);
  }
  if (cur.length) segs.push(cur);
  return segs;
}
function gapsOf(segs, xs, xe) {                 // stretches without data, including both ends of the window
  if (!segs.length) return [[xs, xe]];
  const out = [];
  segs.forEach((s, i) => {
    if (i === 0) { if (s[0].t - xs >= 60) out.push([xs, s[0].t]); } else out.push([segs[i - 1][segs[i - 1].length - 1].t, s[0].t]);
  });
  const last = segs[segs.length - 1];
  if (xe - last[last.length - 1].t >= 60) out.push([last[last.length - 1].t, xe]);
  return out;
}
function chartLabel(card, ch) {
  if (ch.kind === "events") return `${card.title}: ${ch.events.length ? ch.events.map((e) => e.label).join(", ") : ch.empty_label}.`;
  const n = pts(ch, "actual").filter((p) => p.v != null).length;
  return `${card.title}: ${card.key_value} ${card.key_detail}. Chart of ${n} readings, ${ch.x_start.slice(0, 5)}–${ch.x_end.slice(0, 5)}.`;
}

function drawSeries(svg, ch, tone, w, h, mini, animate) {
  const P = mini ? { t: 3, r: 4, b: 3, l: 3 } : { t: 6, r: 10, b: 6, l: 6 };
  const uid = `ch${++chartSeq}`;
  const xs = toSec(ch.x_start), xe = Math.max(toSec(ch.x_end), xs + 60);
  const X = (t) => P.l + ((t - xs) / (xe - xs)) * (w - P.l - P.r);
  const actual = pts(ch, "actual"), command = pts(ch, "command");
  let y0 = 0, y1 = 100;                         // command_vs_actual: fixed 0-100 %
  if (ch.kind !== "command_vs_actual") {
    const extra = ch.kind === "series_limit"
      ? (ch.limit ? [ch.limit.value] : ch.band ? [ch.band.low, ch.band.high] : [])
      : [ch.band && ch.band.low, ch.band && ch.band.high, ch.baseline && ch.baseline.value].filter((v) => v != null);
    const all = actual.filter((p) => p.v != null).map((p) => p.v).concat(extra);
    y0 = Math.min(...all); y1 = Math.max(...all);
    if (y1 - y0 < 1e-9) { y0 -= 1; y1 += 1; } else { const m = (y1 - y0) * 0.15; y0 -= m; y1 += m; }
  }
  const Y = (v) => P.t + (1 - (v - y0) / (y1 - y0)) * (h - P.t - P.b);
  const clampY = (y) => Math.max(15, Math.min(h - 3, y));
  const txt = (x, y, s, cls, anchor = "start") => sv("text", { x: x.toFixed(1), y: y.toFixed(1), class: `ch-text ${cls}`, "text-anchor": anchor }, s);
  const d = (p) => p.map((q, i) => `${i ? "L" : "M"}${X(q.t).toFixed(1)} ${Y(q.v).toFixed(1)}`).join("") + (p.length === 1 ? `L${X(p[0].t).toFixed(1)} ${Y(p[0].v).toFixed(1)}` : "");
  const segs = segmentsOf(actual);
  const abnFrom = tone !== "normal" && ch.marker ? toSec(ch.marker.ts) : Infinity;
  const markerT = ch.marker ? toSec(ch.marker.ts) : null;
  const defs = sv("defs"), under = sv("g"), data = sv("g"), late = sv("g"), labels = [];
  svg.append(defs, under, data, late);

  if (ch.band && !mini) {                       // decorative normal band, clipped to the plot
    const top = Math.max(P.t, Y(ch.band.high)), bot = Math.min(h - P.b, Y(ch.band.low));
    if (bot > top) under.append(sv("rect", { x: P.l, y: top, width: w - P.l - P.r, height: bot - top, class: "ch-band" }));
    if (ch.kind === "series_limit" && !ch.limit) labels.push(txt(P.l + 4, clampY(top + 16), "SOP range", "t-muted"));
  }
  if (!mini) {                                  // missing stretches: hatched, "No data" when wide enough
    defs.append(sv("pattern", { id: `${uid}-hatch`, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" },
      sv("line", { x1: 0, y1: 0, x2: 0, y2: 6, class: "ch-hatch" })));
    for (const [a, b] of gapsOf(segs, xs, xe)) {
      const xa = X(a), wd = X(b) - xa;
      if (wd <= 0) continue;
      under.append(sv("rect", { x: xa, y: P.t, width: wd, height: h - P.t - P.b, fill: `url(#${uid}-hatch)`, opacity: 0.6 }));
      if (wd >= 48) labels.push(txt(xa + wd / 2, h / 2 + 6, "No data", "t-missing", "middle"));
    }
  }
  const firstPt = actual.find((p) => p.v != null), lastPt = [...actual].reverse().find((p) => p.v != null);
  if (ch.limit) {
    const ly = Y(ch.limit.value);
    under.append(sv("line", { x1: P.l, y1: ly, x2: w - P.r, y2: ly, class: "ch-limit" }));
    if (!mini) labels.push(txt(P.l + 4, clampY(Y(firstPt.v) > ly ? ly - 4 : ly + 16), ch.limit.label, "t-limit"));
  }
  if (ch.baseline) {
    const by = Y(ch.baseline.value);
    under.append(sv("line", { x1: P.l, y1: by, x2: w - P.r, y2: by, class: "ch-baseline" }));
    if (!mini) labels.push(txt(w - P.r - 4, clampY(Y(lastPt.v) > by ? by - 4 : by + 16), ch.baseline.label, "t-baseline", "end"));
  }
  if (!mini && command.length && markerT != null) {   // gap between command and actual, from the marker on
    const a = actual.filter((p) => p.v != null && p.t >= markerT), c = command.filter((p) => p.v != null && p.t >= markerT);
    if (a.length && c.length) data.append(sv("polygon", { class: "ch-gap",
      points: a.concat([...c].reverse()).map((p) => `${X(p.t).toFixed(1)},${Y(p.v).toFixed(1)}`).join(" ") }));
  }
  for (const s of segmentsOf(command)) data.append(sv("path", { d: d(s), class: "ch-command" }));
  for (const s of segs) {                       // blue before the marker, amber from the marker point on
    const before = s.filter((p) => p.t < abnFrom), after = s.filter((p) => p.t >= abnFrom);
    if (before.length) data.append(sv("path", { d: d(after.length ? before.concat(after[0]) : before), class: "ch-line" }));
    if (after.length) data.append(sv("path", { d: d(after), class: "ch-line abn" }));
  }
  if (markerT != null && !mini) {
    const mx = X(markerT), right = mx > P.l + 0.7 * (w - P.l - P.r);
    late.append(sv("line", { x1: mx, y1: 0, x2: mx, y2: h, class: "ch-marker" }));
    labels.push(txt(right ? mx - 6 : mx + 6, h - P.b - 2, ch.marker.label, "t-marker", right ? "end" : "start"));
  }
  if (ch.key_point) {
    const kt = toSec(ch.key_point.ts);
    late.append(sv("circle", { cx: X(kt), cy: Y(ch.key_point.value), r: mini ? 3 : 5, class: `ch-key${kt >= abnFrom ? " abn" : ""}` }));
  }
  if (!mini && command.length) {
    const lc = command.filter((p) => p.v != null).pop();
    if (lc && ch.command_label) labels.push(txt(w - P.r - 4, clampY(Y(lc.v) - 6), ch.command_label, "t-command", "end"));
    if (lc && lastPt) {
      const ya = Y(lastPt.v), below = ya > Y(lc.v);
      labels.push(txt(w - P.r - 4, clampY(below ? ya + 18 : ya - 6), "Actual", lastPt.t >= abnFrom ? "t-abn" : "t-series", "end"));
    }
  }
  late.append(...labels);
  if (animate && data.animate) {                // M7 reveal left to right, M8 marker/key point/labels fade in
    const clip = sv("rect", { x: 0, y: 0, width: w, height: h });
    defs.append(sv("clipPath", { id: `${uid}-clip` }, clip));
    data.setAttribute("clip-path", `url(#${uid}-clip)`);
    clip.animate([{ transform: "scaleX(0)" }, { transform: "scaleX(1)" }], { duration: 600, delay: 120, easing: EASE_DECEL, fill: "both" });
    late.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, delay: 720, easing: EASE_DECEL, fill: "both" });
  }
}

function drawEvents(svg, ch, w, h, mini, animate) {
  const P = mini ? { l: 3, r: 4 } : { l: 6, r: 10 };
  const xs = toSec(ch.x_start), xe = Math.max(toSec(ch.x_end), xs + 60);
  const X = (t) => P.l + ((t - xs) / (xe - xs)) * (w - P.l - P.r);
  const cy = h / 2, k = mini ? 8 / 12 : 1;      // mini: 8px shapes
  svg.append(sv("line", { x1: P.l, y1: cy, x2: w - P.r, y2: cy, class: "ev-axis" }),
             sv("line", { x1: P.l, y1: cy - 2, x2: P.l, y2: cy + 2, class: "ev-axis" }),
             sv("line", { x1: w - P.r, y1: cy - 2, x2: w - P.r, y2: cy + 2, class: "ev-axis" }));
  if (!ch.events.length) {
    if (!mini) svg.append(sv("text", { x: w / 2, y: cy + 6, class: "ch-text t-muted", "text-anchor": "middle" }, ch.empty_label));
    return;
  }
  const shape = (lvl, x) => {                   // severity by SHAPE, not only colour
    const s = 6 * k;
    if (lvl === "critical") return sv("polygon", { points: `${x},${cy - s} ${x + s},${cy} ${x},${cy + s} ${x - s},${cy}`, class: "ev-critical" });
    if (lvl === "warning") return sv("polygon", { points: `${x},${cy - s} ${x + s},${cy + s * 0.85} ${x - s},${cy + s * 0.85}`, class: "ev-warning" });
    if (lvl === "notable") return sv("rect", { x: x - 5 * k, y: cy - 5 * k, width: 10 * k, height: 10 * k, class: "ev-notable" });
    return sv("circle", { cx: x, cy, r: 5 * k, class: "ev-info" });
  };
  let prev = -Infinity;
  const xsOf = ch.events.map((e) => { let x = X(toSec(e.ts)); if (Math.abs(x - prev) < 8) x += 4; prev = x; return x; });
  const shapes = ch.events.map((e, i) => shape(e.level, xsOf[i]));
  svg.append(...shapes);
  const labels = [];
  if (!mini) {                                  // up to 3 labels, newest first: above, below, above
    for (let j = 0; j < Math.min(3, ch.events.length); j++) {
      const i = ch.events.length - 1 - j, x = xsOf[i], end = x > 0.7 * w;
      labels.push(sv("text", { x: end ? x - 8 : x + 8, y: j % 2 === 0 ? cy - 12 : cy + 24, class: `ch-text t-${ch.events[i].level}`,
        "text-anchor": end ? "end" : "start" }, ch.events[i].label));
    }
    svg.append(...labels);
  }
  if (animate && svg.animate) {                 // M9: shapes pop in 80 ms apart
    shapes.forEach((s, i) => {
      s.style.transformBox = "fill-box"; s.style.transformOrigin = "center";
      s.animate([{ opacity: 0, transform: "scale(0.6)" }, { opacity: 1, transform: "scale(1)" }],
                { duration: 200, delay: 120 + 80 * i, easing: EASE_DECEL, fill: "both" });
    });
    labels.forEach((t) => t.animate([{ opacity: 0 }, { opacity: 1 }],
      { duration: 200, delay: 120 + 80 * (shapes.length - 1) + 200, easing: EASE_DECEL, fill: "both" }));
  }
}

function fullChart(card, w, h, animate) {
  const ch = card.chart;
  if (ch.kind !== "events" && !hasPoints(ch))
    return el("div", { class: "chart-empty", role: "img", "aria-label": chartLabel(card, ch) }, ch.empty_label || "No data");
  const svg = sv("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h, role: "img", "aria-label": chartLabel(card, ch) });
  if (ch.kind === "events") drawEvents(svg, ch, w, h, false, animate);
  else drawSeries(svg, ch, card.tone, w, h, false, animate);
  return svg;
}
function drawMini(n) {
  const r = state.rendered[n], box = r && r.node.querySelector(".c-mini");
  const ch = r && r.step.card && r.step.card.chart;
  if (!box || !ch) return;
  const w = cssPx(box, "--chart-mini-w"), h = cssPx(box, "--chart-mini-h");
  const svg = sv("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h, class: "mini", "aria-hidden": "true", focusable: "false" });
  if (ch.kind === "events") drawEvents(svg, ch, w, h, true, false);
  else if (hasPoints(ch)) drawSeries(svg, ch, r.step.card.tone, w, h, true, false);
  box.replaceChildren(svg);
}
function drawFullChart(n, force = false) {
  const r = state.rendered[n], box = r && r.node.querySelector(".chart");
  if (!box) return;
  const w = box.clientWidth, h = box.clientHeight;
  if (!w || !h) return;                         // hidden (compact row): drawn when expanded
  if (!force && box.dataset.size === `${w}x${h}` && box.firstChild) return;
  const first = !state.drawn.has(n);            // M7-M9 play once per card, never on resize or re-expand
  state.drawn.add(n);
  box.replaceChildren(fullChart(r.step.card, w, h, first && !reduceMotion()));
  box.dataset.size = `${w}x${h}`;
}
function drawRowCharts(n) {
  const r = state.rendered[n];
  if (!r || !(r.step.status === "done" || r.step.status === "cached") || !r.step.card || !r.step.card.chart) return;
  drawMini(n);
  drawFullChart(n);
}
let resizeTimer = null;
function onResize() {                           // redraw 150 ms after resizing stops, in real pixels
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    for (const k of Object.keys(state.rendered)) {
      const r = state.rendered[k];
      if (r.step.card && r.step.card.chart && (r.step.status === "done" || r.step.status === "cached")) { drawMini(Number(k)); drawFullChart(Number(k), true); }
    }
  }, 150);
}

// ------------------------------------------------------------------ work order + QR (F7)
async function createWorkOrder(e) {
  const modal = $("modal");
  if (e && e.currentTarget && !modal.contains(e.currentTarget)) state.modalOpener = e.currentTarget;
  modal.classList.remove("hidden");
  $("wo-ok").classList.add("hidden"); $("wo-fail").classList.add("hidden"); $("show-summary").classList.add("hidden");
  try {
    const wo = await api(`/api/investigations/${state.invId}/workorder`, { method: "POST" });
    state.woId = wo.wo_id;
    $("qr-img").src = `/api/workorders/${wo.wo_id}/qr.svg`;
    $("qr-url").textContent = wo.url.replace(/^https?:\/\//, "");
    $("wo-id").textContent = wo.wo_id;
    $("wo-line").textContent = `Line ${wo.line} · ${wo.machine_label}`;
    $("wo-cause").textContent = wo.root_cause;
    $("wo-priority").textContent = `Priority: ${wo.priority}`;
    $("wo-ok").classList.remove("hidden");
    $("show-summary").classList.remove("hidden");
    $("wo-done").focus();
  } catch (err) {
    $("wo-fail").classList.remove("hidden");     // no "Show summary" here; S still opens the Recap
  }
}
const modalOpen = () => !$("modal").classList.contains("hidden");
function closeModal(restoreFocus = true) {
  if (!modalOpen()) return;
  $("modal").classList.add("hidden");
  if (restoreFocus && state.modalOpener && document.contains(state.modalOpener)) state.modalOpener.focus();
}

// ------------------------------------------------------------------ Recap: Before / After (ui-v2-spec 4)
const recapOpen = () => !$("recap").classList.contains("hidden");
const canRecap = () => state.conclusionShown && state.inv && state.inv.status === "root_cause";
function openRecap(opener) {
  if (!canRecap() || recapOpen()) return;
  const inv = state.inv, c = inv.conclusion, base = state.config.manual_baseline || null;
  closeModal(false);
  clearTimeout(state.recapTimer);
  state.recapOpener = opener || null;
  $("recap-fixture").classList.toggle("hidden", !state.config.offline_fixture);
  $("recap-where").textContent = c.machine_label ? `Line ${c.line} · ${c.machine_label}` : `Line ${c.line}`;
  $("recap-cause").textContent = c.root_cause;
  const after = elapsedSec(inv);
  // Before is shown only with a configured, sourced number; otherwise a neutral text and no bars at all.
  $("recap-before-value").textContent = base ? `${base.minutes} min` : "—";
  $("recap-before-value").classList.toggle("is-empty", !base);
  $("recap-before-note").textContent = base ? `Source: ${base.source}` : "Not yet measured for this plant.";
  $("recap-before-bar").classList.toggle("hidden", !base);
  $("recap-after-bar").classList.toggle("hidden", !base);
  if (base) {
    const before = base.minutes * 60, full = Math.max(before, after, 1);
    $("recap-before-bar").firstElementChild.style.width = `${(before / full) * 100}%`;
    $("recap-after-bar").firstElementChild.style.width = `${(after / full) * 100}%`;
  }
  $("recap-after-value").textContent = fmtElapsed(after);
  const ok = inv.steps.filter((s) => s.status === "done" || s.status === "cached").length;
  const cached = inv.steps.filter((s) => s.status === "cached").length;
  const wo = state.woId || inv.work_order_id;
  $("recap-after-detail").textContent = `${plural(ok, "query", "queries")} · ${c.cited_evidence.length} evidence cited · `
    + `${c.ruled_out.length} ruled out${cached ? ` · ${cached} cached` : ""}${wo ? ` · Work order ${wo}` : ""}`;
  $("recap").classList.remove("hidden", "is-closing");
  $("recap-close").focus();
}
function closeRecap(restoreFocus = true) {
  const r = $("recap");
  if (!recapOpen()) return;
  const done = () => { r.classList.add("hidden"); r.classList.remove("is-closing"); };
  clearTimeout(state.recapTimer);
  if (!restoreFocus || reduceMotion()) done();
  else { r.classList.add("is-closing"); state.recapTimer = setTimeout(done, 150); }
  if (restoreFocus && state.recapOpener && document.contains(state.recapOpener)) state.recapOpener.focus();
}
function trapRecapFocus(e) {
  const f = [...$("recap").querySelectorAll("button:not([disabled])")];
  if (!f.length) return;
  const i = f.indexOf(document.activeElement);
  e.preventDefault();
  f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
}

// ------------------------------------------------------------------ boot
async function boot() {
  state.config = await api("/api/config");
  if (state.config.offline_fixture) $("fixture-banner").classList.remove("hidden");
  $("mode").textContent = state.config.offline_fixture ? "Agent: OFFLINE FIXTURE" : `Agent: ${state.config.model} · data: ${state.config.query_backend}`;
  state.scenarios = await api("/api/scenarios");
  const sel = $("scenario");
  state.scenarios.forEach((s) => sel.append(el("option", { value: s.id }, s.label)));
  state.scenario = state.scenarios[0];
  sel.addEventListener("change", () => { state.scenario = state.scenarios.find((s) => s.id === sel.value); doReset(); });
  $("investigate").addEventListener("click", investigate);
  $("reset").addEventListener("click", doReset);
  $("wo-done").addEventListener("click", () => closeModal());
  $("wo-retry").addEventListener("click", createWorkOrder);
  $("show-summary").addEventListener("click", () => openRecap(state.modalOpener));
  $("recap-close").addEventListener("click", () => closeRecap());
  const pause = () => { state.autoScroll = false; };
  $("cards").addEventListener("wheel", pause, { passive: true });
  $("cards").addEventListener("pointerdown", pause);
  for (const ev of ["wheel", "touchmove"]) window.addEventListener(ev, () => { if (singleColumn()) pause(); }, { passive: true });
  window.addEventListener("resize", onResize);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return recapOpen() ? closeRecap() : closeModal();
    if (e.key === "Tab" && recapOpen()) return trapRecapFocus(e);
    if (e.target.tagName === "SELECT" || e.ctrlKey || e.metaKey || e.altKey) return;
    if ((e.key === "s" || e.key === "S") && canRecap() && !recapOpen()) openRecap(modalOpen() ? state.modalOpener : document.activeElement);
    if (e.key === "r" || e.key === "R") doReset();
    if (e.key === "1" || e.key === "2") {
      const s = state.scenarios[Number(e.key) - 1];
      if (s) { sel.value = s.id; state.scenario = s; doReset(); }
    }
  });
  applyScenario();
  state.tick = setInterval(tick, 1000);
}
boot().catch((e) => showFailure(e.message));
