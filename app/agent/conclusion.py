"""Turns the model's submit_conclusion call into the conclusion object shown in the UI and work order.

Server-side rules (not left to the model):
- A root cause needs >= 2 cited evidence cards that exist; otherwise it becomes Insufficient evidence (PRD F5/F6).
- Confidence is computed from the cards, not chosen by the model. PROVISIONAL rule until PRD Q4 is decided:
  High = 3+ cited cards show an abnormal signal; Medium = 2; Low = fewer.
- Evidence lines and the Checked list are built from the cards, so every number traces back to source rows.
"""
from __future__ import annotations

from app.data.catalog import MACHINES, ROOT_CAUSE_KEYS

SOP_TITLES = {"SOP 4.1": "Mold cooling circuit", "SOP 4.2": "Mold over-temperature", "SOP 4.3": "Rejects at inspection",
              "SOP 4.4": "Hydraulics", "SOP 4.5": "Dryer and resin", "SOP 4.6": "Feeder", "SOP 4.7": "Sensor validation"}


def _as_int_list(values) -> list[int]:
    out = []
    for v in values or []:
        try:
            i = int(v)
        except (TypeError, ValueError):
            continue
        if i not in out:
            out.append(i)
    return out


def _evidence_line(card: dict) -> str:
    detail = card["key_detail"]
    joiner = " " if detail[:1].islower() else " — "  # "41% of baseline since 02:41" vs "214 °C — Above ..."
    return f"{card['title']}: {card['key_value']}{joiner}{detail}"


def finalize(raw: dict, steps: list[dict], scenario: dict) -> dict:
    ok_steps = {s["step"]: s for s in steps if s["status"] in ("done", "cached")}
    line = scenario["line"]
    inc = scenario["incident"]
    checked = [dict(evidence_id=s["step"], name=s["card"]["check"][0], result=s["card"]["check"][1])
               for s in ok_steps.values() if s["card"].get("check")]
    base = dict(line=line, machine=inc["machine"], machine_label=MACHINES.get(inc["machine"] or "", None),
                detected=inc["stop_ts"][:5] if inc["stop_ts"] else None, checked=checked)

    cited = [i for i in _as_int_list(raw.get("cited_evidence")) if i in ok_steps]
    ruled_out = []
    for r in raw.get("ruled_out") or []:
        try:
            eid = int(r.get("evidence_id"))
        except (TypeError, ValueError, AttributeError):
            continue
        if eid in ok_steps and eid not in cited:
            ruled_out.append(dict(evidence_id=eid, text=str(r.get("text", "")).strip()[:160]))
    root_cause = str(raw.get("root_cause") or "").strip()[:120]
    key = raw.get("root_cause_key") if raw.get("root_cause_key") in ROOT_CAUSE_KEYS else "other"

    if raw.get("status") == "root_cause" and len(cited) >= 2 and root_cause:
        abnormal = [i for i in cited if ok_steps[i]["card"]["tone"] != "normal"]
        n, m = len(abnormal), len(ruled_out)
        confidence = "High" if n >= 3 else "Medium" if n == 2 else "Low"
        reason = (f"{n} independent signal{'s' if n != 1 else ''} agree · "
                  f"{m} alternative{'s' if m != 1 else ''} ruled out")
        sop = str(raw.get("sop_reference") or "").strip()[:20]
        actions = [str(a).strip()[:200] for a in (raw.get("recommended_actions") or []) if str(a).strip()][:4]
        return dict(base, status="root_cause", root_cause=root_cause, root_cause_key=key,
                    confidence=confidence, confidence_reason=reason, cited_evidence=cited, ruled_out=ruled_out,
                    evidence_lines=[_evidence_line(ok_steps[i]["card"]) for i in cited],
                    recommended_actions=actions,
                    sop_reference=f"{sop} — {SOP_TITLES[sop]}" if sop in SOP_TITLES else sop,
                    priority="High" if inc["stop_ts"] else "Medium")

    note = None
    if raw.get("status") == "root_cause":
        note = "Model proposed a root cause with fewer than 2 valid evidence citations; shown as insufficient evidence."
    return dict(base, status="insufficient_evidence", checked=checked, note=note,
                next_step=f"Manual inspection of Line {line} by the shift supervisor.")
