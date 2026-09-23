"""OFFLINE FIXTURE mode - for UI development without GCP credentials ONLY.

What is real:  the query functions still run against the local data, so cards and source rows are real.
What is NOT:   which functions are called and the conclusion text are scripted here, not produced by Gemini.
The API returns agent_mode="offline_fixture" and the UI shows an "OFFLINE FIXTURE" banner on every screen
and on the work order. Never use this mode for the demo, the regression score or submission.
"""
from __future__ import annotations

import time

from app.config import Settings

W = dict(start="02:30", end="03:00")

FIXTURES: dict[str, dict] = {
    "R01": dict(
        calls=[
            ("get_alarm_events", dict(line=2, **W)),
            ("get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W)),
            ("compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", **W)),
            ("get_sensor_window", dict(line=2, machine="M3", sensor="cv_position_pct", **W)),
            ("get_shift_log", dict(line=2, start="02:00", end="03:00")),
        ],
        conclusion=dict(
            status="root_cause", root_cause_key="cv_valve_stuck_closed",
            root_cause="Cooling valve CV-2 stuck at 20% open",
            cited_evidence=[2, 3, 4],
            ruled_out=[dict(evidence_id=5, text="Shift handover at 02:30 — no parameter changes")],
            recommended_actions=["Open CV-2 manually per SOP 4.2.",
                                 "Inspect the CV-2 actuator for sticking or power loss.",
                                 "Restart Line 2 after mold temperature is below 205 °C."],
            sop_reference="SOP 4.2"),
    ),
    "N01": dict(
        calls=[
            ("get_alarm_events", dict(line=1, **W)),
            ("get_sensor_window", dict(line=1, machine="M3", sensor="mold_temp_c", **W)),
            ("compare_to_baseline", dict(line=1, machine="M3", sensor="coolant_flow_lpm", **W)),
            ("get_shift_log", dict(line=1, start="02:00", end="03:00")),
        ],
        conclusion=dict(status="insufficient_evidence", cited_evidence=[], recommended_actions=[]),
    ),
}


def run_fixture(ctx, settings: Settings) -> dict:
    fx = FIXTURES.get(ctx.scenario_id)
    if fx is None:
        raise RuntimeError(f"No offline fixture for scenario {ctx.scenario_id}; use AGENT_MODE=gemini")
    for name, args in fx["calls"]:
        ctx.check()
        time.sleep(settings.fixture_step_delay_s)  # pacing so the UI shows cards one by one
        ctx.call_tool(name, dict(args))
    return dict(fx["conclusion"])
