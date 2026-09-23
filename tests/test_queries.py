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


# ---------------------------------------------------------------- card.chart (ui-v2-spec 1.3): plotted = source rows
DEMO_CALLS = [
    ("get_alarm_events", dict(line=2, **W)),
    ("get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W)),
    ("compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", **W)),
    ("get_sensor_window", dict(line=2, machine="M3", sensor="cv_position_pct", **W)),
    ("get_shift_log", dict(line=2, start="02:00", end="03:00")),
]


def _chart_row_ids(chart):
    ids = [p[2] for s in chart.get("series", []) for p in s["points"]]
    ids += [e["row_id"] for e in chart.get("events", [])]
    ids += [chart[k]["row_id"] for k in ("marker", "key_point") if chart.get(k)]
    return ids


@pytest.mark.parametrize("sid", ["R01", "N01", "N02", "R07", "R10"])
def test_every_chart_row_id_is_in_rows_and_values_match(ex, sid):
    line = 1 if sid == "N01" else 3 if sid in ("N02", "R10") else 2
    for fn, args in DEMO_CALLS:
        r = ex.execute(sid, fn, dict(args, line=line))
        chart = r.card["chart"]
        by_id = {row["row_id"]: row for row in r.rows}
        ids = _chart_row_ids(chart)
        assert set(ids) <= set(by_id), (fn, set(ids) - set(by_id))
        for s in chart.get("series", []):  # every point is the raw value of its row, nothing smoothed
            assert all(by_id[i]["value"] == v and by_id[i]["ts"][11:16] == t for t, v, i in s["points"])
        if chart.get("key_point"):
            assert by_id[chart["key_point"]["row_id"]]["value"] == chart["key_point"]["value"]


def test_key_point_is_the_highlighted_row_and_the_card_number(ex):
    for fn, args in DEMO_CALLS[1:4]:
        r = ex.execute("R01", fn, args)
        kp = r.card["chart"]["key_point"]
        assert kp["row_id"] in r.card["highlight_row_ids"], fn
        if fn == "get_sensor_window":  # key_value is that row's value (baseline shows a % of it)
            assert _numbers(r.card["key_value"])[0] == kp["value"]


def test_chart_limit_is_the_catalog_sop_limit(ex):
    catalog = {row["sensor"]: row for row in ex.execute("R01", "list_sensors", dict(machine="M3")).rows}
    temp = ex.execute("R01", "get_sensor_window", DEMO_CALLS[1][1]).card
    assert temp["chart"]["kind"] == "series_limit"
    assert temp["chart"]["limit"]["side"] == "high"
    assert temp["chart"]["limit"]["value"] == catalog["mold_temp_c"]["normal_high"] == 205.0
    assert temp["chart"]["limit"]["label"] == "SOP limit 205 °C" and "205 °C" in temp["key_detail"]
    assert temp["chart"]["marker"]["label"] in temp["key_detail"]  # "since 02:5x" is the card's own text
    r10 = ex.execute("R10", "get_sensor_window", dict(line=3, machine="M3", sensor="mold_temp_c", **W)).card
    assert r10["chart"]["limit"]["side"] == "low"
    assert r10["chart"]["limit"]["value"] == catalog["mold_temp_c"]["normal_low"]
    normal = ex.execute("N01", "get_sensor_window", dict(line=1, machine="M3", sensor="mold_temp_c", **W)).card
    assert normal["chart"]["limit"] is None and normal["chart"]["marker"] is None
    assert normal["chart"]["band"] == dict(low=180.0, high=205.0)


def test_valve_and_baseline_chart_labels_repeat_card_numbers(ex):
    cv = ex.execute("R01", "get_sensor_window", DEMO_CALLS[3][1]).card
    assert cv["chart"]["kind"] == "command_vs_actual" and cv["chart"]["limit"] is None
    assert [s["role"] for s in cv["chart"]["series"]] == ["actual", "command"]
    assert cv["chart"]["command_label"] == "Commanded 80%" and "commanded 80%" in cv["key_detail"]
    base = ex.execute("R01", "compare_to_baseline", DEMO_CALLS[2][1])
    chart = base.card["chart"]
    assert chart["baseline"]["value"] == base.summary["baseline_mean"]
    assert chart["baseline"]["label"] == f"Baseline {base.summary['baseline_mean']:g} L/min"
    assert chart["marker"]["label"] == "since 02:41" and "since 02:41" in base.card["key_detail"]
    assert {p[2] for p in chart["series"][0]["points"]} == {r["row_id"] for r in base.rows if r["period"] == "window"}


def test_event_labels_are_fixed_templates_never_log_text(ex):
    alarms = ex.execute("R01", "get_alarm_events", DEMO_CALLS[0][1]).card["chart"]
    assert [(e["level"], e["label"]) for e in alarms["events"]] == [("warning", "Warning 02:54"), ("critical", "Trip 03:00")]
    log = ex.execute("R07", "get_shift_log", dict(line=2, start="02:00", end="03:00")).card["chart"]
    assert log["events"] and all(re.fullmatch(r"(Handover|Maintenance|Parameter change|Material change|Note) "
                                              r"\d\d:\d\d", e["label"]) for e in log["events"])
    assert "Parameter change 02:38" in [e["label"] for e in log["events"]]
    assert log["x_end"] == "03:00:59"  # same bound as the SQL (end + 59 s)
    empty = ex.execute("N01", "get_alarm_events", dict(line=1, **W)).card["chart"]
    assert empty["events"] == [] and empty["empty_label"] == "No alarms"


def test_chart_x_axis_stops_at_scenario_now_and_gaps_stay_gaps(ex):
    late = ex.execute("R01", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", start="02:30", end="03:30"))
    assert late.card["chart"]["x_end"] == "03:00:00"  # later minutes have not happened yet (BUG-002)
    gap = ex.execute("N02", "compare_to_baseline", dict(line=3, machine="M3", sensor="coolant_flow_lpm", **W)).card["chart"]
    times = [p[0] for p in gap["series"][0]["points"]]
    assert times and max(times) < "02:40"  # the missing minutes are absent, not filled in
    none = ex.execute("N02", "get_sensor_window", dict(line=3, machine="M3", sensor="coolant_flow_lpm",
                                                      start="02:45", end="03:00")).card
    assert none["key_value"] == "No data" and none["chart"]["series"][0]["points"] == []
    assert ex.execute("R01", "list_sensors", dict(machine="M3")).card["chart"] is None
