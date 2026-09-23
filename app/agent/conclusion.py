"""Turns the model's submit_conclusion call into the conclusion object shown in the UI and work order.

Server-side rules (not left to the model):
- A root cause needs >= 2 cited evidence cards that exist; otherwise it becomes Insufficient evidence (PRD F5/F6).
- At least one cited card must show an abnormal signal (tone != normal); citing only normal cards becomes
  Insufficient evidence, so healthy data always ends as a grey card even if the model is talked into a cause (BUG-001).
- Confidence is computed from the cards, not chosen by the model. PROVISIONAL rule until PRD Q4 is decided:
  High = 3+ cited cards show an abnormal signal; Medium = 2; Low = fewer.
- Evidence lines and the Checked list are built from the cards, so every number traces back to source rows.
"""
from __future__ import annotations

from app.data.catalog import MACHINES, ROOT_CAUSE_KEYS

SOP_TITLES = {"SOP 4.1": "Mold cooling circuit", "SOP 4.2": "Mold over-temperature", "SOP 4.3": "Rejects at inspection",
              "SOP 4.4": "Hydraulics", "SOP 4.5": "Dryer and resin", "SOP 4.6": "Feeder", "SOP 4.7": "Sensor validation"}


# Model output is checked by type, not coerced (BUG-006): a wrong type counts as a missing field, so a string
# is never split into characters and a list never reaches a set lookup.
def _list(value) -> list:
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value, limit: int) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ""


def _as_int(v) -> int | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():  # Gemini sends JSON numbers, e.g. 2.0
        return int(v)
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def _as_int_list(values) -> list[int]:
    out = []
    for v in _list(values):
        i = _as_int(v)
        if i is not None and i not in out:
            out.append(i)
    return out


def _evidence_line(card: dict) -> str:
    detail = card["key_detail"]
    joiner = " " if detail[:1].islower() else " — "  # "41% of baseline since 02:41" vs "214 °C — Above ..."
    return f"{card['title']}: {card['key_value']}{joiner}{detail}"


def finalize(raw: dict, steps: list[dict], scenario: dict) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    ok_steps = {s["step"]: s for s in steps if s["status"] in ("done", "cached")}
    line = scenario["line"]
    inc = scenario["incident"]
    checked = [dict(evidence_id=s["step"], name=s["card"]["check"][0], result=s["card"]["check"][1])
               for s in ok_steps.values() if s["card"].get("check")]
    base = dict(line=line, machine=inc["machine"], machine_label=MACHINES.get(inc["machine"] or "", None),
                detected=inc["stop_ts"][:5] if inc["stop_ts"] else None, checked=checked)

    cited = [i for i in _as_int_list(raw.get("cited_evidence")) if i in ok_steps]
    ruled_out = []
    for r in _list(raw.get("ruled_out")):
        eid = _as_int(r.get("evidence_id")) if isinstance(r, dict) else None
        if eid in ok_steps and eid not in cited:
            ruled_out.append(dict(evidence_id=eid, text=_text(r.get("text"), 160)))
    root_cause = _text(raw.get("root_cause"), 120)
    key = raw.get("root_cause_key")
    key = key if isinstance(key, str) and key in ROOT_CAUSE_KEYS else "other"

    abnormal = [i for i in cited if ok_steps[i]["card"]["tone"] != "normal"]
    if raw.get("status") == "root_cause" and len(cited) >= 2 and root_cause and abnormal:
        n, m = len(abnormal), len(ruled_out)
        confidence = "High" if n >= 3 else "Medium" if n == 2 else "Low"
        reason = (f"{n} independent signal{'s' if n != 1 else ''} agree · "
                  f"{m} alternative{'s' if m != 1 else ''} ruled out")
        sop = _text(raw.get("sop_reference"), 20)
        actions = [a for a in (_text(x, 200) for x in _list(raw.get("recommended_actions"))) if a][:4]
        return dict(base, status="root_cause", root_cause=root_cause, root_cause_key=key,
                    confidence=confidence, confidence_reason=reason, cited_evidence=cited, ruled_out=ruled_out,
                    evidence_lines=[_evidence_line(ok_steps[i]["card"]) for i in cited],
                    recommended_actions=actions,
                    sop_reference=f"{sop} — {SOP_TITLES[sop]}" if sop in SOP_TITLES else sop,
                    priority="High" if inc["stop_ts"] else "Medium")

    note = None
    if raw.get("status") == "root_cause":
        if len(cited) >= 2 and root_cause:  # BUG-001: healthy data must always end as a grey card
            note = "Model proposed a root cause but none of the cited evidence shows an abnormal signal; shown as insufficient evidence."
        else:
            note = "Model proposed a root cause with fewer than 2 valid evidence citations; shown as insufficient evidence."
    return dict(base, status="insufficient_evidence", checked=checked, note=note,
                next_step=f"Manual inspection of Line {line} by the shift supervisor.")
