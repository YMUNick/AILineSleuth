// Mobile work order page (/wo/{id}). Content comes from the same conclusion object as the big screen.
"use strict";

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  for (const c of children.flat()) if (c != null) e.append(c instanceof Node ? c : String(c));
  return e;
}
const field = (label, value) => [el("div", { class: "wo-label" }, label), el("div", { class: "wo-value" }, value)];
const list = (tag, label, items) => items && items.length ? [el("div", { class: "wo-label" }, label), el(tag, {}, items.map((i) => el("li", {}, i)))] : [];

async function load() {
  const body = document.getElementById("wo-body");
  const id = decodeURIComponent(location.pathname.split("/").pop());
  const res = await fetch(`/api/workorders/${encodeURIComponent(id)}`);
  if (!res.ok) {
    body.replaceChildren(el("div", { class: "wo-id" }, "Work order not found"), el("p", {}, "This link may be expired or mistyped."));
    return;
  }
  const wo = await res.json();
  if (wo.agent_mode === "offline_fixture") document.getElementById("fixture-banner").classList.remove("hidden");
  const bars = { High: "▮▮▮", Medium: "▮▮▯", Low: "▮▯▯" }[wo.confidence] || "";
  body.replaceChildren(
    el("section", {}, el("div", { class: "wo-id" }, wo.wo_id),
      el("span", { class: "chip chip-info" }, wo.status), " ",
      el("span", { class: "chip chip-warn" }, `Priority: ${wo.priority}`)),
    el("section", {},
      ...field("Line / Machine", `Line ${wo.line} · ${wo.machine_label || "—"}`),
      ...field("Detected", wo.detected ? `${wo.detected} (scenario time)` : "—"),
      ...field("Root cause", wo.root_cause),
      ...field("Confidence", `${wo.confidence} ${bars}`)),
    el("section", {},
      ...list("ul", "Evidence", wo.evidence),
      ...list("ul", "Ruled out", wo.ruled_out),
      ...list("ol", "Recommended actions", wo.recommended_actions)),
    el("section", {},
      ...field("SOP reference", wo.sop_reference || "—"),
      ...field("Created", `${wo.created_at} by LineSleuth`)));
}
load().catch(() => {
  document.getElementById("wo-body").replaceChildren(el("p", { class: "center" }, "Could not load work order."));
});
