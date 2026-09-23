"""Query functions: validation, scenario isolation, and every card number traces back to a row."""
import re

import pytest

from app.queries.backends import LocalDuckDBBackend
from app.queries.functions import FUNCTION_NAMES, QueryArgError, QueryExecutor

W = dict(start="02:30", end="03:00")


@pytest.fixture(scope="module")
def ex():
    return QueryExecutor(LocalDuckDBBackend())


def test_exactly_five_fixed_functions():
    assert FUNCTION_NAMES == ["get_alarm_events", "get_sensor_window", "compare_to_baseline", "get_shift_log", "list_sensors"]


@pytest.mark.parametrize("fn,args", [
    ("get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c; DROP TABLE events", **W)),
    ("get_sensor_window", dict(line=2, machine="M1", sensor="mold_temp_c", **W)),   # sensor on wrong machine
    ("get_alarm_events", dict(line=7, **W)),
    ("get_alarm_events", dict(line=True, **W)),                                      # BUG-008: no coercion
    ("get_alarm_events", dict(line=2.7, **W)),
    ("get_alarm_events", dict(line="2", **W)),
    ("get_alarm_events", dict(line=2, start="2:30am", end="03:00")),
    ("get_alarm_events", dict(line=2, start="03:00", end="02:30")),
    ("get_alarm_events", dict(line=2, start="00:00", end="23:00")),                  # window too long
    ("run_sql", dict(sql="SELECT 1")),
])
def test_bad_arguments_are_rejected(ex, fn, args):
    with pytest.raises(QueryArgError):
        ex.execute("R01", fn, args)


def test_every_row_has_row_id_and_scenario_isolation(ex):
    r = ex.execute("R01", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W))
    assert r.row_count == 31
    assert all(row["row_id"].startswith("R01-") for row in r.rows)
    other = ex.execute("N01", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W))
    assert other.row_count == 0  # N01 is Line 1 only


def _numbers(text):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def test_sensor_card_numbers_trace_to_rows(ex):
    for sensor in ("mold_temp_c", "cv_position_pct"):
        r = ex.execute("R01", "get_sensor_window", dict(line=2, machine="M3", sensor=sensor, **W))
        values = {row["value"] for row in r.rows}
        assert _numbers(r.card["key_value"])[0] in values
        ids = {row["row_id"] for row in r.rows}
        assert r.card["highlight_row_ids"] and set(r.card["highlight_row_ids"]) <= ids


def test_baseline_card_is_computed_from_rows(ex):
    r = ex.execute("R01", "compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", **W))
    base = [row["value"] for row in r.rows if row["period"] == "baseline"]
    latest = [row for row in r.rows if row["period"] == "window"][-1]
    mean = round(sum(base) / len(base), 1)
    assert r.summary["baseline_mean"] == mean
    assert r.card["key_value"] == f"{round(latest['value'] / mean * 100)}%"
    assert latest["row_id"] in r.card["highlight_row_ids"]
    assert 35 <= int(r.card["key_value"].rstrip("%")) <= 47  # the "about 41%" of the story


def test_alarm_card_matches_row(ex):
    r = ex.execute("R01", "get_alarm_events", dict(line=2, **W))
    top = next(row for row in r.rows if row["row_id"] == r.card["highlight_row_ids"][0])
    assert top["ts"].endswith("03:00:12") and "03:00:12" in r.card["key_detail"]


def test_integral_float_line_is_accepted(ex):
    # Gemini function-call arguments arrive as JSON numbers (2.0), which must keep working
    a = ex.execute("R01", "get_alarm_events", dict(line=2.0, **W))
    b = ex.execute("R01", "get_alarm_events", dict(line=2, **W))
    assert [r["row_id"] for r in a.rows] == [r["row_id"] for r in b.rows] and a.rows
