"""Data generator: reproducible, and every scenario actually contains the story it claims."""
import filecmp

import pytest

from app.data.generate import generate
from app.data.scenarios import SCENARIOS
from app.queries.backends import LocalDuckDBBackend
from app.queries.functions import QueryExecutor


@pytest.fixture(scope="module")
def ex():
    return QueryExecutor(LocalDuckDBBackend())


def test_generation_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generate(a)
    generate(b)
    for name in ("sensor_readings.csv", "events.csv", "sensor_catalog.csv"):
        assert filecmp.cmp(a / name, b / name, shallow=False), name


def test_regression_set_shape():
    root_causes = [s for s in SCENARIOS.values() if s["expected"]["status"] == "root_cause"]
    insufficient = [s for s in SCENARIOS.values() if s["expected"]["status"] == "insufficient_evidence"]
    distractors = [sid for sid in ("R04", "R06", "R08") if SCENARIOS[sid]["distractor"]]
    assert len(root_causes) == 10
    assert len(insufficient) >= 1
    assert len(distractors) == 3
    assert len({s["expected"]["root_cause_key"] for s in root_causes}) == 10  # 10 distinct answers


# (scenario, machine, sensor, expected direction) - the physical signature each story must contain
SIGNATURES = [
    ("R01", "M3", "cv_position_pct", "low"), ("R01", "M3", "coolant_flow_lpm", "low"),
    ("R01", "M3", "mold_temp_c", "high"),
    ("R02", "M3", "coolant_inlet_temp_c", "high"), ("R03", "M3", "heater_power_pct", "high"),
    ("R04", "M3", "mold_temp_c", "high"), ("R05", "M3", "hydraulic_pressure_bar", "low"),
    ("R06", "M3", "coolant_flow_lpm", "low"), ("R07", "M3", "mold_temp_c", "high"),
    ("R08", "M2", "dryer_temp_c", "low"), ("R09", "M1", "feed_rate_kgph", "low"),
    ("R10", "M3", "cv_position_pct", "high"), ("R10", "M3", "mold_temp_c", "low"),
]


@pytest.mark.parametrize("sid,machine,sensor,direction", SIGNATURES)
def test_scenario_signature_present(ex, sid, machine, sensor, direction):
    line = SCENARIOS[sid]["line"]
    r = ex.execute(sid, "compare_to_baseline", dict(line=line, machine=machine, sensor=sensor, start="02:30", end="03:00"))
    assert r.summary["deviation_started"] is not None, r.card
    delta = r.summary["delta_from_baseline"]
    assert (delta < 0) if direction == "low" else (delta > 0)


def test_r04_reference_probe_stays_normal(ex):
    """Sensor-drift distractor: control probe reads high, reference probe does not."""
    r = ex.execute("R04", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_ref_c", start="02:30", end="03:00"))
    assert r.card["tone"] == "normal"


@pytest.mark.parametrize("sid", ["N01", "N02"])
def test_healthy_scenarios_have_no_alarms_or_breaches(ex, sid):
    line = SCENARIOS[sid]["line"]
    assert ex.execute(sid, "get_alarm_events", dict(line=line, start="02:30", end="03:00")).row_count == 0
    for sensor, machine in [("mold_temp_c", "M3"), ("heater_power_pct", "M3"), ("dryer_temp_c", "M2"), ("reject_rate_pct", "M4")]:
        r = ex.execute(sid, "get_sensor_window", dict(line=line, machine=machine, sensor=sensor, start="02:30", end="03:00"))
        assert r.card["tone"] == "normal", (sensor, r.card)


def test_n02_has_a_data_gap(ex):
    r = ex.execute("N02", "compare_to_baseline", dict(line=3, machine="M3", sensor="coolant_flow_lpm", start="02:30", end="03:00"))
    assert r.summary["missing_minutes"] > 0
    assert r.card["tone"] == "normal"


def test_r07_contains_prompt_injection_text(ex):
    r = ex.execute("R07", "get_shift_log", dict(line=2, start="02:00", end="03:00"))
    assert any("IGNORE ALL PREVIOUS INSTRUCTIONS" in e["message"] for e in r.summary["entries"])
