// LineSleuth front end. Plain JS, no build step. Copy follows docs/design/storyboard.md section 5.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { config: null, scenarios: [], scenario: null, invId: null, poll: null, tick: null,
                loadedAt: 0, rendered: {}, conclusionShown: false, autoScroll: true };

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
const pad = (n) => String(n).padStart(2, "0");
const hms = (s) => `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(Math.floor(s % 60))}`;
const mmss = (s) => `${pad(Math.floor(s / 60))}:${pad(Math.floor(s % 60))}`;
const toSec = (t) => { const [h, m, s] = t.split(":").map(Number); return h * 3600 + m * 60 + (s || 0); };

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
  return body;
}

// ------------------------------------------------------------------ plant SVG
function setMachine(line, m, cls, text) {
  const g = $(`L${line}-M${m}`);
  if (!g) return;
  g.classList.remove("is-normal", "is-warn", "is-stopped", "is-idle");
  g.classList.add(cls);
  $(`L${line}-M${m}-state`).textContent = text;
  const name = g.querySelector(".name").textContent;
  g.setAttribute("aria-label", `Line ${line} M${m} ${name}: ${text.toLowerCase()}`);
}
function resetPlant() {
  for (let l = 1; l <= 3; l++) {
    $(`L${l}`).classList.remove("is-stopped");
    $(`L${l}-status`).textContent = "Running";
    $(`L${l}-M3-CV${l}`).classList.remove("is-fault");
    for (let m = 1; m <= 4; m++) { setMachine(l, m, "is-normal", "RUNNING"); $(`L${l}-M${m}`).classList.remove("is-focus"); }
  }
}
function focusMachine(on) {
  const s = state.scenario;
  const m = s.machine ? s.machine.slice(1) : "3";
  $(`L${s.line}-M${m}`).classList.toggle("is-focus", on);
}

// ------------------------------------------------------------------ scenario + reset (F8)
function applyScenario() {
  const s = state.scenario;
  stopPolling();
  state.invId = null; state.rendered = {}; state.conclusionShown = false; state.autoScroll = true; state.loadedAt = Date.now();
  resetPlant();
  $("cards").replaceChildren(); $("result").replaceChildren();
  $("empty").classList.remove("hidden");
  setChip("Not started", "chip-muted");
  $("elapsed").classList.add("hidden");
  closeModal();
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
  applyScenario();
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
  focusMachine(true);
  try {
    const inv = await api("/api/investigations", { method: "POST", body: JSON.stringify({ scenario_id: state.scenario.id }) });
    state.invId = inv.id;
    render(inv);
    state.poll = setInterval(pollOnce, 700);
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
  $("elapsed").textContent = `Elapsed ${mmss(inv.elapsed_s)}`;
  for (const step of inv.steps) renderStep(inv, step);
  if (inv.status === "running") return;
  stopPolling();
  focusMachine(false);
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
  const c = step.card || {};
  const tone = c.tone === "danger" ? "danger" : c.tone === "warn" ? "warn" : "";
  let stateEl;
  if (step.status === "running") stateEl = el("span", { class: "card-state" }, el("span", { class: "spinner" }), "Querying…");
  else if (step.status === "error") stateEl = el("span", { class: "card-state error-text" }, "Failed");
  else if (step.status === "cached") stateEl = el("span", { class: "chip chip-warn", title: "Live query timed out. Showing last verified result." }, "Cached");
  else stateEl = el("span", { class: "card-state" }, el("span", { class: "ok" }, "✓"), "Done");

  const body = [];
  if (step.status === "running") body.push(el("div", { class: "skeleton" }), el("div", { class: "skeleton", style: "width:60%" }));
  else if (step.status === "error") body.push(el("div", { class: "error-text" }, "Query failed"));
  else {
    body.push(el("div", { class: "key" }, el("span", { class: `key-value ${tone}` }, c.key_value), el("span", { class: "key-detail" }, c.key_detail)));
    if (c.secondary) body.push(el("div", { class: "secondary" }, c.secondary));
  }
  const meta = el("div", { class: "meta" }, el("span", { class: "mono" }, step.function),
    step.time_range ? ` · ${step.time_range}` : "", step.row_count != null ? ` · ${step.row_count} rows` : "");
  const card = el("div", { class: "card", id: `card-${step.step}` },
    el("div", { class: "card-title" }, el("h3", {}, c.title || step.function), stateEl), ...body, meta,
    el("div", { class: "tags" }));
  if (step.status === "done" || step.status === "cached") {
    const rowsBox = el("div", { class: "rows hidden" });
    const btn = el("button", { class: "btn-text", type: "button", "aria-expanded": "false" }, `View source rows (${step.row_count})`);
    btn.addEventListener("click", () => toggleRows(inv.id, step, btn, rowsBox));
    card.append(btn, rowsBox);
  }
  const row = el("div", { class: "card-row" }, el("div", { class: "step-no" }, step.step), card);
  if (existing) existing.node.replaceWith(row); else $("cards").append(row);
  state.rendered[step.step] = { sig, node: row };
  if (state.autoScroll) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

async function toggleRows(invId, step, btn, box) {
  const open = btn.getAttribute("aria-expanded") === "true";
  if (open) { box.classList.add("hidden"); btn.textContent = `View source rows (${step.row_count})`; btn.setAttribute("aria-expanded", "false"); return; }
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

function tagCard(n, text, cls) {
  const card = $(`card-${n}`);
  if (card) card.querySelector(".tags").append(el("span", { class: `tag ${cls}` }, text));
}
function flashCard(n) {
  const card = $(`card-${n}`);
  if (!card) return;
  card.scrollIntoView({ block: "center", behavior: "smooth" });
  card.classList.add("flash"); setTimeout(() => card.classList.remove("flash"), 1200);
}

function renderConclusion(inv) {
  const c = inv.conclusion;
  setChip("Root cause found", "chip-warn");
  c.cited_evidence.forEach((n) => tagCard(n, "Cited in conclusion", "tag-cited"));
  c.ruled_out.forEach((r) => tagCard(r.evidence_id, "Ruled out", "tag-ruled"));
  if (c.root_cause_key && c.root_cause_key.startsWith("cv_valve")) $(`L${c.line}-M3-CV${c.line}`).classList.add("is-fault");
  const bars = { High: 3, Medium: 2, Low: 1 }[c.confidence];
  const box = el("div", { class: "conclusion" },
    c.confidence === "Low" ? el("div", { class: "low-warn" }, "Low confidence — verify on site before acting.") : null,
    el("div", { class: "eyebrow" }, "Root cause"),
    el("div", { class: "root-cause" }, c.root_cause),
    el("div", { class: "conf" }, el("span", { class: "bars" }, [1, 2, 3].map((i) => el("i", { class: i <= bars ? "on" : "" }))), `Confidence: ${c.confidence}`),
    el("div", { class: "conf-reason" }, c.confidence_reason),
    el("div", { class: "subhead" }, "Evidence"),
    el("div", {}, c.cited_evidence.map((n) => el("button", { class: "cite", type: "button", onclick: () => flashCard(n) }, `#${n}`))),
    c.ruled_out.length ? el("div", { class: "subhead" }, "Ruled out") : null,
    c.ruled_out.map((r) => el("div", {}, `${r.text} (#${r.evidence_id})`)),
    el("div", { class: "subhead" }, "Recommended actions"),
    el("ol", {}, c.recommended_actions.map((a) => el("li", {}, a))),
    el("div", { class: "conclusion-foot" }, el("button", { class: "btn-outline", type: "button", onclick: createWorkOrder }, "Create work order")));
  $("result").replaceChildren(box);
  box.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderGrey(inv) {
  const c = inv.conclusion;
  setChip("Insufficient evidence", "chip-grey");
  const box = el("div", { class: "grey" },
    el("div", { class: "grey-head" }, el("div", { class: "grey-icon", "aria-hidden": "true" }, "?"), el("h3", {}, "Insufficient evidence")),
    el("p", {}, "No root cause found. LineSleuth will not guess."),
    el("div", { class: "subhead" }, "Checked"),
    el("ul", {}, c.checked.map((k) => el("li", {}, el("span", { class: "check" }, "✓"), `${k.name} — `, el("span", { class: "res" }, k.result)))),
    el("div", { class: "subhead", style: "font-size:var(--fs-md);color:var(--color-grey-text)" }, "Recommended next step"),
    el("p", {}, c.next_step));
  $("result").replaceChildren(box);
  box.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function showFailure(msg) {
  stopPolling();
  focusMachine(false);
  setChip("Investigation failed", "chip-danger");
  setButton("done");
  $("result").replaceChildren(el("div", { class: "fail" }, el("p", {}, "Investigation failed. Press Reset and try again."),
    el("p", { class: "meta" }, msg || "")));
}

// ------------------------------------------------------------------ work order + QR (F7)
async function createWorkOrder() {
  $("modal").classList.remove("hidden");
  $("wo-ok").classList.add("hidden"); $("wo-fail").classList.add("hidden");
  try {
    const wo = await api(`/api/investigations/${state.invId}/workorder`, { method: "POST" });
    $("qr-img").src = `/api/workorders/${wo.wo_id}/qr.svg`;
    $("qr-url").textContent = wo.url.replace(/^https?:\/\//, "");
    $("wo-id").textContent = wo.wo_id;
    $("wo-line").textContent = `Line ${wo.line} · ${wo.machine_label}`;
    $("wo-cause").textContent = wo.root_cause;
    $("wo-priority").textContent = `Priority: ${wo.priority}`;
    $("wo-ok").classList.remove("hidden");
    $("wo-done").focus();
  } catch (e) {
    $("wo-fail").classList.remove("hidden");
  }
}
function closeModal() { $("modal").classList.add("hidden"); }

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
  $("wo-done").addEventListener("click", closeModal);
  $("wo-retry").addEventListener("click", createWorkOrder);
  $("panel-body").addEventListener("wheel", () => { state.autoScroll = false; }, { passive: true });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return closeModal();
    if (e.target.tagName === "SELECT" || e.ctrlKey || e.metaKey || e.altKey) return;
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
