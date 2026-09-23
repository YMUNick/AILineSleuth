"""Regression set runner: 10 known root causes (3 distractors) + insufficient-evidence cases.

    python -m scripts.run_regression               # every scenario once
    python -m scripts.run_regression --repeat 3    # consistency check (PRD: same answer 3 times)
    python -m scripts.run_regression --only R01 N01

Requires AGENT_MODE=gemini and Vertex AI credentials. Refuses to run in OFFLINE FIXTURE mode,
because a scripted agent would produce a meaningless score.
Gate (PRD section 9): >= 9/10 root causes correct AND every insufficient-evidence case correct.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from app.config import get_settings
from app.data.scenarios import SCENARIOS
from app.investigations import InvestigationManager
from app.queries.backends import make_backend


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--only", nargs="*")
    p.add_argument("--json", help="write detailed results to this file")
    a = p.parse_args()

    settings = get_settings()
    if settings.agent_mode != "gemini":
        print("Refusing to score: AGENT_MODE must be 'gemini' (offline fixture is not an AI result).")
        return 2
    mgr = InvestigationManager(settings, make_backend(settings))
    ids = a.only or list(SCENARIOS)
    results, rc_ok, rc_total, ie_ok, ie_total, inconsistent = [], 0, 0, 0, 0, []
    print(f"model={settings.gemini_model} backend={settings.query_backend} repeat={a.repeat}")
    for sid in ids:
        exp = SCENARIOS[sid]["expected"]
        answers = []
        for i in range(a.repeat):
            mgr.reset()
            inv = mgr.start(sid, background=False)
            got = inv.conclusion or {}
            answer = got.get("root_cause_key") if inv.status == "root_cause" else inv.status
            answers.append(answer)
            results.append(dict(scenario=sid, run=i + 1, status=inv.status, answer=answer, error=inv.error,
                                calls=[(s["function"], s["args"]) for s in inv.steps],
                                elapsed_s=inv.public()["elapsed_s"], conclusion=got))
        want = exp.get("root_cause_key", exp["status"])
        correct = all(x == want for x in answers)
        if len(set(answers)) > 1:
            inconsistent.append(sid)
        if exp["status"] == "root_cause":
            rc_total += 1
            rc_ok += correct
        else:
            ie_total += 1
            ie_ok += correct
        tag = " [distractor]" if sid in ("R04", "R06", "R08") else ""
        print(f"{'PASS' if correct else 'FAIL'} {sid}{tag}: expected={want} got={Counter(answers).most_common()}")
        for r in results[-a.repeat:]:
            if r["error"]:
                print(f"     error: {r['error'][:200]}")
    print(f"\nRoot causes: {rc_ok}/{rc_total}   Insufficient-evidence cases: {ie_ok}/{ie_total}   "
          f"Inconsistent across repeats: {inconsistent or 'none'}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1, default=str)
    allowed_misses = rc_total // 10  # 9/10 on the full set; no misses on partial runs
    gate = rc_ok >= rc_total - allowed_misses and ie_ok == ie_total and not inconsistent
    print("GATE: " + ("PASS" if gate else "FAIL"))
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
