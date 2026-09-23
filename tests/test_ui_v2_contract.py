"""UI v2 contract tests (Quinn): what the API promises the new front end. Offline only (DuckDB + OFFLINE FIXTURE).

Covers docs/design/ui-v2-spec.md 1.3 / 1.6 (card.chart), 2.3 (where the root cause lights up on the map),
4.2 (Recap: Before = MANUAL_BASELINE_* only, After = measured) and 7.1 (token contrast, computed).
What these tests CANNOT prove: how charts, zoom, pulses and the Recap LOOK and MOVE. That is the browser
checklist in docs/qa/test-plan.md section 10 (host's Playwright run + manual checks).

Tests marked xfail(strict=True) document open bugs in docs/qa/bugs.md (BUG-009). When fixed they XPASS,
strict turns that into a failure, and the marker must be removed.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections import defaultdict, deque

import pytest
from fastapi.testclient import TestClient

from app.config import ROOT, STATIC_DIR, Settings, get_settings, manual_baseline
from app.data.catalog import ROOT_CAUSE_KEYS, SENSORS
from app.data.scenarios import SCENARIOS
from app.investigations import Investigation, InvestigationManager, _Context
from app.queries.backends import LocalDuckDBBackend
from app.queries.functions import QueryExecutor

PROJECT = ROOT.parent
W = dict(start="02:30", end="03:00")
SENSOR_LIST = [s for s in SENSORS if s != "cv_command_pct"]  # command comes back alongside cv_position_pct
ENUMS = {"events", "series_limit", "command_vs_actual", "series_baseline", "actual", "command", "high", "low",
         "critical", "warning", "notable", "info"}
LABEL = re.compile(  # every text the chart carries is one of these fixed templates (ui-v2-spec 1.1, 1.3)
    r"SOP limit -?\d+(\.\d)? \S+|Baseline -?\d+(\.\d)? \S+|Commanded \d+(\.\d)?%|since \d\d:\d\d"
    r"|(Trip|Critical|Warning|Alarm|Parameter change|Maintenance|Material change|Handover|Note) \d\d:\d\d"
    r"|No data|No alarms|No log entries")
CLOCK = re.compile(r"\d\d:\d\d(:\d\d)?")


def _num(v: float) -> str:
    return f"{v:g}"


def _numbers(text):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


@pytest.fixture(scope="module")
def ex():
    return QueryExecutor(LocalDuckDBBackend())


# ==================================================================== 1. card.chart, every scenario x every function
def _calls(line):
    yield "get_alarm_events", dict(line=line, **W)
    yield "get_shift_log", dict(line=line, start="02:00", end="03:00")
    late = dict(start="02:30", end="03:05")  # storyboard range, past the scenario's "now" (BUG-002)
    yield "get_alarm_events", dict(line=line, **late)
    yield "get_sensor_window", dict(line=line, machine="M3", sensor="mold_temp_c", **late)
    yield "compare_to_baseline", dict(line=line, machine="M3", sensor="coolant_flow_lpm", **late)
    for sensor in SENSOR_LIST:
        machine = SENSORS[sensor]["machine"]
        yield "get_sensor_window", dict(line=line, machine=machine, sensor=sensor, **W)
        yield "compare_to_baseline", dict(line=line, machine=machine, sensor=sensor, **W)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _expected_event(row, alarm):
    """ui-v2-spec 1.3 level / label table."""
    t = row["ts"][11:16]
    if alarm:
        if row["severity"] == "critical":
            return ("critical", f"Trip {t}") if str(row["code"]).endswith("_TRIP") else ("critical", f"Critical {t}")
        if row["severity"] == "warning":
            return "warning", f"Warning {t}"
        return "info", f"Alarm {t}"  # not in the spec table; no such alarm rows in the data today
    level, name = {"parameter_change": ("notable", "Parameter change"), "maintenance": ("notable", "Maintenance"),
                   "material_change": ("notable", "Material change"),
                   "shift_handover": ("info", "Handover")}.get(row["event_type"], ("info", "Note"))
    return level, f"{name} {t}"


def _check_events(where, fn, args, r):
    card, ch = r.card, r.card["chart"]
    alarm = fn == "get_alarm_events"
    assert ch["kind"] == "events" and "series" not in ch, where
    assert ch["empty_label"] == ("No alarms" if alarm else "No log entries"), where
    assert (ch["x_start"], ch["x_end"]) == (args["start"] + ":00", args["end"] + ":59"), where  # same bound as SQL
    assert [e["row_id"] for e in ch["events"]] == [row["row_id"] for row in r.rows], where  # one event per row
    for e, row in zip(ch["events"], r.rows):
        assert e["ts"] == row["ts"][11:19], where
        assert (e["level"], e["label"]) == _expected_event(row, alarm), (where, row)


def _check_series(where, fn, args, r, scenario):
    card, ch = r.card, r.card["chart"]
    sensor, spec = args["sensor"], SENSORS[args["sensor"]]
    lo, hi, unit = spec["normal_low"], spec["normal_high"], spec["unit"]
    valve = fn == "get_sensor_window" and sensor == "cv_position_pct"
    kind = "command_vs_actual" if valve else "series_limit" if fn == "get_sensor_window" else "series_baseline"
    assert ch["kind"] == kind and ch["unit"] == unit and ch["empty_label"] == "No data", where

    # plotted = exactly the source rows, in time order: nothing added, dropped, smoothed or interpolated
    if fn == "get_sensor_window":
        actual_rows = [row for row in r.rows if row["sensor"] == sensor]
        cmd_rows = [row for row in r.rows if row["sensor"] != sensor]
    else:
        actual_rows, cmd_rows = [row for row in r.rows if row["period"] == "window"], []
    series = {s["role"]: s["points"] for s in ch["series"]}
    assert series["actual"] == [[row["ts"][11:16], row["value"], row["row_id"]] for row in actual_rows], where
    if valve and cmd_rows:
        assert series["command"] == [[row["ts"][11:16], row["value"], row["row_id"]] for row in cmd_rows], where
    else:
        assert "command" not in series, where
    times = [p[0] for p in series["actual"]]
    assert times == sorted(times), where

    # x axis: the query window, cut at the scenario's current time (BUG-002), never before the start
    now = scenario["incident"]["now"][:5]
    assert ch["x_start"] == args["start"] + ":00", where
    assert ch["x_end"] == max(args["start"], min(args["end"], now)) + ":00", where
    assert all(ch["x_start"][:5] <= t <= ch["x_end"][:5] for pts in series.values() for t in (p[0] for p in pts)), where

    # no data: the chart shows no number the card cannot back
    no_data = card["key_value"] == "No data"
    if not series["actual"]:
        assert no_data, where
    if no_data:
        assert ch["key_point"] is None and ch["marker"] is None and ch.get("limit") is None, where
        assert card["tone"] == "normal", where
        if kind == "series_baseline":
            assert ch["band"] is None and ch["baseline"] is None, where
        return

    # key point: a plotted point, the highlighted row, and the card's number
    kp = ch["key_point"]
    assert [kp["ts"], kp["value"], kp["row_id"]] in series["actual"], where
    assert kp["row_id"] in card["highlight_row_ids"], where
    values = [p[1] for p in series["actual"]]

    # marker ("since HH:MM"): only on abnormal cards, the FIRST crossing point, text already on the card
    m = ch["marker"]
    assert (m is not None) == (card["tone"] != "normal"), where
    if m:
        assert m["label"] == f"since {m['ts']}" and m["label"] in card["key_detail"], where
        assert m["row_id"] in card["highlight_row_ids"], where
        if kind == "series_baseline":
            thr = 0.25 * (hi - lo)
            crossing = [p for p in series["actual"] if abs(p[1] - ch["baseline"]["value"]) > thr]
        else:
            crossing = [p for p in series["actual"] if p[1] > hi] or [p for p in series["actual"] if p[1] < lo]
        assert crossing and crossing[0][2] == m["row_id"] and crossing[0][0] == m["ts"], where

    if kind in ("series_limit", "command_vs_actual"):
        above = bool(m) and any(v > hi for v in values)
        expected_kp = max(values) if above else min(values) if m else values[-1]
        assert kp["value"] == expected_kp and _numbers(card["key_value"])[0] == kp["value"], where
    if kind == "series_limit":
        assert ch["band"] == dict(low=lo, high=hi), where
        lim = ch["limit"]
        if not m:
            assert lim is None, where
        else:
            assert (lim["side"], lim["value"]) == (("high", hi) if above else ("low", lo)), where
            assert lim["label"] == f"SOP limit {_num(lim['value'])} {unit}", where
            assert f"limit of {_num(lim['value'])} {unit}" in card["key_detail"], where
    elif kind == "command_vs_actual":
        assert ch["limit"] is None and ch["band"] is None, where
        if cmd_rows:  # "Commanded 80%": a raw command row value, and the card's own "commanded 80%" when shown
            assert ch["command_label"] == f"Commanded {_num(cmd_rows[-1]['value'])}%", where
            if "commanded" in card["key_detail"]:
                assert f"commanded {_num(cmd_rows[-1]['value'])}%" in card["key_detail"], where
        else:
            assert "command_label" not in ch, where
    else:
        base = [row["value"] for row in r.rows if row["period"] == "baseline"]
        b_mean, thr = round(sum(base) / len(base), 1), 0.25 * (hi - lo)
        assert ch["baseline"] == dict(value=b_mean, label=f"Baseline {_num(b_mean)} {unit}"), where
        assert f"baseline mean {_num(b_mean)} {unit}" in card["secondary"], where
        assert ch["band"] == dict(low=round(b_mean - thr, 2), high=round(b_mean + thr, 2)), where
        assert kp["row_id"] == actual_rows[-1]["row_id"], where  # latest reading = the card's percentage
        assert f"{_num(kp['value'])} {unit} at {kp['ts']}" in card["secondary"], where


@pytest.mark.parametrize("sid", sorted(SCENARIOS))
@pytest.mark.parametrize("which_line", ["own", "other"])  # "other" = a line with no data for this scenario
def test_chart_contract_for_every_function_and_scenario(ex, sid, which_line):
    scenario = SCENARIOS[sid]
    line = scenario["line"] if which_line == "own" else scenario["line"] % 3 + 1
    for fn, args in _calls(line):
        r = ex.execute(sid, fn, dict(args))
        where = (sid, fn, args.get("sensor"), line)
        ch = r.card["chart"]
        assert ch is not None, where
        ids = {row["row_id"] for row in r.rows}
        for s in _strings(ch):  # closed world: no free text, no number from nowhere
            assert s in ENUMS or s == ch.get("unit") or CLOCK.fullmatch(s) or s in ids or LABEL.fullmatch(s), (where, s)
        assert set(r.card["highlight_row_ids"]) <= ids, where
        if fn in ("get_alarm_events", "get_shift_log"):
            _check_events(where, fn, args, r)
        else:
            _check_series(where, fn, args, r, scenario)


# ==================================================================== 2. edge cases of the chart contract
class DropRows:
    """Real rows with some minutes removed: a sensor that went quiet mid-window."""

    def __init__(self, inner, sensor, minutes):
        self.inner, self.name, self.source_prefix = inner, inner.name, inner.source_prefix
        self.sensor, self.minutes = sensor, set(minutes)

    def run(self, sql, params):
        rows = self.inner.run(sql, params)
        return [r for r in rows if not (r.get("sensor") == self.sensor and r["ts"][11:16] in self.minutes)]


def test_mid_window_gap_stays_a_gap(ex):
    gone = [f"02:{m}" for m in range(40, 45)]
    r = QueryExecutor(DropRows(ex.backend, "mold_temp_c", gone)).execute(
        "R01", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W))
    pts = r.card["chart"]["series"][0]["points"]
    assert not {p[0] for p in pts} & set(gone)                    # nothing filled in
    assert ["02:39", "02:45"] in [[a[0], b[0]] for a, b in zip(pts, pts[1:])]  # the two sides are neighbours
    assert len(pts) == 31 - 5 and "5 min of data missing" in r.card["key_detail"]


def test_window_entirely_after_now_is_empty_not_missing(ex):
    r = ex.execute("R01", "get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", start="03:10", end="03:30"))
    ch = r.card["chart"]
    assert (ch["x_start"], ch["x_end"]) == ("03:10:00", "03:10:00")  # front end widens a zero-length axis itself
    assert ch["series"][0]["points"] == [] and r.card["key_value"] == "No data" and "missing" not in r.card["key_detail"]


def test_baseline_without_history_shows_no_baseline_numbers(ex):
    # start 00:15 -> baseline 22:45-23:45 the day before, before the data starts (00:00)
    r = ex.execute("R01", "compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", start="00:15", end="00:45"))
    ch, ids = r.card["chart"], {row["row_id"] for row in r.rows}
    assert r.card["key_value"] == "No data"
    assert ch["baseline"] is None and ch["band"] is None and ch["key_point"] is None and ch["marker"] is None
    assert {p[2] for p in ch["series"][0]["points"]} <= ids  # whatever is plotted is still a source row


def test_error_step_has_no_chart(ex):
    inv = Investigation("R01", get_settings())
    ctx = _Context(inv, ex, time.monotonic() + 30)
    ctx.call_tool("get_sensor_window", dict(line=2, machine="M3", sensor="no_such_sensor", **W))
    assert inv.steps[0]["status"] == "error" and inv.steps[0]["card"]["chart"] is None  # spec 1.6: no chart on error


def test_chart_is_never_sent_to_the_model(ex):
    inv = Investigation("R01", get_settings())
    ctx = _Context(inv, ex, time.monotonic() + 30)
    for fn, args in [("get_alarm_events", dict(line=2, **W)),
                     ("get_sensor_window", dict(line=2, machine="M3", sensor="cv_position_pct", **W)),
                     ("compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", **W))]:
        payload = json.dumps(ctx.call_tool(fn, args), default=str)
        assert '"chart"' not in payload and "key_point" not in payload and "command_label" not in payload
    assert all(s["card"]["chart"] for s in inv.steps)  # ...but the front end has it


class SlowBackend:
    def __init__(self, inner):
        self.inner, self.name, self.source_prefix, self.delay = inner, inner.name, inner.source_prefix, 0.0

    def run(self, sql, params):
        time.sleep(self.delay)
        return self.inner.run(sql, params)


def test_cached_step_keeps_the_same_chart_and_its_rows_resolve(ex):
    slow = SlowBackend(ex.backend)
    inv = Investigation("R01", get_settings())
    ctx = _Context(inv, QueryExecutor(slow, timeout_s=0.3), time.monotonic() + 30)
    args = dict(line=2, machine="M3", sensor="cv_position_pct", **W)
    ctx.call_tool("get_sensor_window", dict(args))
    slow.delay = 1.0
    ctx.call_tool("get_sensor_window", dict(args))
    live, cached = inv.steps
    assert (live["status"], cached["status"]) == ("done", "cached")
    assert cached["card"]["chart"] == live["card"]["chart"]
    rows = {r["row_id"]: r for r in inv.rows[2]}  # "View source rows" of the cached card
    assert all(rows[i]["value"] == v for s in cached["card"]["chart"]["series"] for _, v, i in s["points"])


# ==================================================================== 3. through the API (what the browser gets)
@pytest.fixture
def api(monkeypatch):
    import app.main as m
    monkeypatch.setattr(m, "_hits", defaultdict(deque))
    client = TestClient(m.app)
    yield m, client
    client.post("/api/reset", json={})


def _run(client, sid):
    client.post("/api/reset", json={})
    r = client.post("/api/investigations", json={"scenario_id": sid})
    assert r.status_code == 201, r.text
    for _ in range(300):
        inv = client.get(f"/api/investigations/{r.json()['id']}").json()
        if inv["status"] != "running":
            return inv
        time.sleep(0.05)
    raise AssertionError("investigation did not finish")


@pytest.mark.parametrize("sid", ["R01", "N01"])
def test_every_chart_point_resolves_in_view_source_rows(api, sid):
    _, client = api
    inv = _run(client, sid)
    for step in inv["steps"]:
        ch = step["card"]["chart"]
        ev = client.get(f"/api/investigations/{inv['id']}/evidence/{step['step']}").json()
        rows = {r["row_id"]: r for r in ev["rows"]}
        for s in ch.get("series", []):
            for t, v, i in s["points"]:
                assert rows[i]["value"] == v and rows[i]["ts"][11:16] == t, (step["step"], i)
        for e in ch.get("events", []):
            assert rows[e["row_id"]]["ts"][11:19] == e["ts"]
        for k in ("key_point", "marker"):
            if ch.get(k):
                assert ch[k]["row_id"] in ev["highlight_row_ids"], (step["step"], k)  # the highlighted row
        if ch.get("key_point"):
            assert rows[ch["key_point"]["row_id"]]["value"] == ch["key_point"]["value"]


def test_grey_card_charts_are_calm_and_nothing_is_marked_on_the_map(api):
    _, client = api
    inv = _run(client, "N01")
    c = inv["conclusion"]
    assert inv["status"] == "insufficient_evidence"
    assert "root_cause_key" not in c and not c.get("cited_evidence") and c["machine"] is None
    assert c["line"] == 1 and 'id="L1-badge"' in client.get("/").text  # the lane that gets the grey dashed frame
    assert [k["evidence_id"] for k in c["checked"]] == [s["step"] for s in inv["steps"]]  # D6: Checked = evidence
    by_fn = {s["function"]: s for s in inv["steps"]}
    alarms = by_fn["get_alarm_events"]["card"]
    assert alarms["chart"]["events"] == [] and alarms["chart"]["empty_label"] == "No alarms"
    assert alarms["highlight_row_ids"] == []
    log = by_fn["get_shift_log"]["card"]["chart"]
    assert log["events"] and {e["level"] for e in log["events"]} == {"info"}  # handover: hollow circle, not amber
    for s in inv["steps"]:
        card, ch = s["card"], s["card"]["chart"]
        assert card["tone"] == "normal" and ch.get("marker") is None and ch.get("limit") is None, s["step"]
        if ch["kind"] != "events":
            band = ch["band"]
            assert all(band["low"] <= v <= band["high"] for _, v, _ in ch["series"][0]["points"]), s["step"]
            assert ch["key_point"]["row_id"] in card["highlight_row_ids"]


# ==================================================================== 4. where the root cause lights up (spec 2.3)
STORY_SENSOR = {"R01": "cv_position_pct", "R02": "coolant_inlet_temp_c", "R03": "heater_power_pct", "R04": "mold_temp_c",
                "R05": "hydraulic_pressure_bar", "R06": "coolant_flow_lpm", "R07": "mold_temp_c", "R08": "dryer_temp_c",
                "R09": "feed_rate_kgph", "R10": "cv_position_pct"}


def _rc_target():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    block = re.search(r"const RC_TARGET = \{(.*?)\n\};", js, re.S).group(1)
    return {k: (m, bool(v)) for k, m, v in
            re.findall(r'(\w+):\s*\{\s*machine:\s*"(M\d)"(,\s*valve:\s*true)?\s*\}', block)}


def test_every_root_cause_lights_up_the_machine_that_holds_the_evidence():
    target = _rc_target()
    assert set(target) == set(ROOT_CAUSE_KEYS) - {"other"}  # "other": nothing marked, zoom back out
    svg = (STATIC_DIR / "line-layout.svg").read_text(encoding="utf-8")
    for sid, sensor in STORY_SENSOR.items():
        s = SCENARIOS[sid]
        machine, valve = target[s["expected"]["root_cause_key"]]
        assert machine == SENSORS[sensor]["machine"], sid
        assert valve == (sensor == "cv_position_pct"), sid
        line = s["line"]
        assert f'id="L{line}-{machine}"' in svg and (not valve or f'id="L{line}-M3-CV{line}"' in svg), sid


def test_svg_v2_has_every_id_the_map_states_need():
    svg = (STATIC_DIR / "line-layout.svg").read_text(encoding="utf-8")
    assert svg == (PROJECT / "docs" / "design" / "line-layout-v2.svg").read_text(encoding="utf-8")  # copied whole
    for line in (1, 2, 3):
        for mid in (f"L{line}", f"L{line}-status", f"L{line}-badge", f"L{line}-M3-CV{line}"):
            assert f'id="{mid}"' in svg, mid
        for m in (1, 2, 3, 4):
            assert f'id="L{line}-M{m}"' in svg and f'id="L{line}-M{m}-state"' in svg, (line, m)
    assert len(re.findall(r'<g class="rc-tag" transform=', svg)) == 12  # one ROOT CAUSE tag per machine
    assert 'id="ls-desc"' in svg


# ==================================================================== 5. Recap "Before": MANUAL_BASELINE_* only
SRC = "Median of 3 plant-manager interviews, Sep 2026"
BASELINE_CASES = [
    ("", "", None), ("35", "", None), ("", SRC, None),                    # neither / only one of the two
    ("   ", SRC, None), ("35", "   ", None),                              # blank counts as not set
    ("-5", SRC, None), ("-35", SRC, None), ("-0", SRC, None),             # negative
    ("0", SRC, None), ("0.5", SRC, None), ("480.1", SRC, None), ("1e9", SRC, None),  # out of 1-480
    ("abc", SRC, None), ("35 min", SRC, None), ("35分鐘", SRC, None), ("35,5", SRC, None), ("0x23", SRC, None),
    ("inf", SRC, None), ("-inf", SRC, None), ("NaN", SRC, None),          # not a usable number
    ("35", "y" * 121, None),
    ("1", SRC, 1), ("480", SRC, 480), (" 35 ", SRC, 35), ("35.0", SRC, 35), ("7.5", SRC, 7.5),
    ("35", "y" * 120, 35), ("35", "<b>Stopwatch</b>", 35),               # source is passed through as data
]


@pytest.mark.parametrize("minutes,source,expected", BASELINE_CASES)
def test_before_comes_only_from_both_env_vars(api, monkeypatch, minutes, source, expected):
    m, client = api
    monkeypatch.setenv("MANUAL_BASELINE_MIN", minutes)
    monkeypatch.setenv("MANUAL_BASELINE_SOURCE", source)
    s = Settings.from_env()  # the real env-reading path, not dataclasses.replace
    monkeypatch.setattr(m, "settings", s)
    got = client.get("/api/config").json()["manual_baseline"]
    value, problem = manual_baseline(s)
    if expected is None:
        assert got is None and value is None and problem, "null, plus a reason for the startup warning"
    else:
        assert got == dict(minutes=expected, source=source.strip()) and problem is None
        assert got["minutes"] == float(minutes)  # never a default, never a rounded-away number


@pytest.mark.parametrize("minutes,source,warning", [
    ("-5", "Interviews", "must be 1-480"),
    ("35", "", "must both be set"),
    ("35", "Median of 3 plant-manager interviews", None),
])
def test_startup_warns_once_when_the_baseline_is_not_usable(minutes, source, warning):
    env = dict(os.environ, MANUAL_BASELINE_MIN=minutes, MANUAL_BASELINE_SOURCE=source,
               AGENT_MODE="offline_fixture", QUERY_BACKEND="local")
    out = subprocess.run([sys.executable, "-c", "import app.main"], cwd=PROJECT, env=env, capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    lines = [ln for ln in out.stdout.splitlines() if "Recap shows no manual baseline" in ln]
    if warning:
        assert len(lines) == 1 and lines[0].startswith("WARNING") and warning in lines[0], out.stdout[-2000:]
    else:
        assert lines == []


def test_nothing_shipped_supplies_a_default_baseline():
    env_example = (PROJECT / ".env.example").read_text(encoding="utf-8").splitlines()
    assert "MANUAL_BASELINE_MIN=" in env_example and "MANUAL_BASELINE_SOURCE=" in env_example  # present, empty
    shipped = [PROJECT / ".env.example", PROJECT / "Dockerfile"]
    shipped += [p for p in ROOT.rglob("*") if p.suffix in (".py", ".js", ".html", ".css", ".svg")]
    banned = [re.compile(r"MANUAL_BASELINE_(MIN|SOURCE)[ \t]*=[ \t]*\S"),            # a value baked in
              re.compile(r"\b40\s*(min|mins|minutes|分鐘|分)(?![\w-])", re.I),          # the old slide number
              re.compile(r"\b90\s*(sec|secs|seconds|秒)(?![\w-])", re.I),
              re.compile(r"minutes\s*(:|\|\||\?\?)\s*\d")]                              # JS fallback like minutes: 40
    for path in shipped:
        text = path.read_text(encoding="utf-8")
        for rx in banned:
            assert not rx.search(text), (path.name, rx.pattern, rx.search(text))
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    for eid in ("recap-before-value", "recap-after-value", "recap-before-note", "recap-after-detail"):
        assert re.search(rf'id="{eid}"[^>]*></div>', html), eid  # no placeholder number that could flash


# ==================================================================== 6. Recap "After": measured by the server
def test_after_is_measured_not_a_constant_and_stops_at_the_conclusion(api, monkeypatch):
    m, client = api
    fast = _run(client, "R01")
    monkeypatch.setattr(m.manager, "settings", dataclasses.replace(m.manager.settings, fixture_step_delay_s=0.2))
    slow = _run(client, "R01")
    assert slow["status"] == fast["status"] == "root_cause"
    assert slow["elapsed_s"] >= 1.0 > fast["elapsed_s"]  # 5 steps x 0.2 s: the number follows the real run
    time.sleep(0.3)
    assert client.get(f"/api/investigations/{slow['id']}").json()["elapsed_s"] == slow["elapsed_s"]  # stopped
    wo = client.post(f"/api/investigations/{slow['id']}/workorder").json()
    later = client.get(f"/api/investigations/{slow['id']}").json()
    assert later["work_order_id"] == wo["wo_id"] and later["elapsed_s"] == slow["elapsed_s"]  # WO time not added


def test_elapsed_counts_while_running_and_freezes_on_cancel(api, monkeypatch):
    m, client = api
    monkeypatch.setattr(m.manager, "settings", dataclasses.replace(m.manager.settings, fixture_step_delay_s=0.4))
    client.post("/api/reset", json={})
    inv_id = client.post("/api/investigations", json={"scenario_id": "R01"}).json()["id"]
    a = client.get(f"/api/investigations/{inv_id}").json()
    time.sleep(0.35)
    b = client.get(f"/api/investigations/{inv_id}").json()
    assert a["status"] == b["status"] == "running" and b["elapsed_s"] > a["elapsed_s"]
    assert client.post("/api/reset", json={}).json()["cancelled"] == 1
    c = client.get(f"/api/investigations/{inv_id}").json()
    time.sleep(0.25)
    assert c["status"] == "cancelled" and client.get(f"/api/investigations/{inv_id}").json()["elapsed_s"] == c["elapsed_s"]


def test_elapsed_is_the_server_clock_difference():
    inv = Investigation("R01", get_settings())
    inv.started, inv.finished = 1000.0, 1072.46
    assert inv.public()["elapsed_s"] == 72.5  # front end: Math.round -> "1 min 12 s" and "Elapsed 01:12"


# ==================================================================== 7. static checks: no chart library, contrast
def test_no_chart_library_was_added():
    reqs = "".join((PROJECT / f).read_text(encoding="utf-8").lower() for f in ("requirements.txt", "requirements-dev.txt"))
    for lib in ("chart", "d3", "plotly", "echarts", "matplotlib", "bokeh", "altair", "vega", "highcharts"):
        assert lib not in reqs, lib
    for page in ("index.html", "wo.html"):
        srcs = re.findall(r"<script[^>]*src=\"([^\"]+)\"", (STATIC_DIR / page).read_text(encoding="utf-8"))
        assert all(s.startswith("/static/") for s in srcs), (page, srcs)  # no CDN scripts


def _tokens():
    css = (STATIC_DIR / "app.css").read_text(encoding="utf-8")
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)))


def _hex(tokens, name):
    v = tokens[name].strip()
    while v.startswith("var("):
        v = tokens[re.match(r"var\((--[\w-]+)", v).group(1)].strip()
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", v), (name, v)
    return v


def _contrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("fg,bg,minimum", [  # ui-v2-spec 7.1; 16px/600 chart labels are normal text -> 4.5
    ("--chart-series", "--color-surface-2", 3.0), ("--chart-series-abnormal", "--color-surface-2", 4.5),
    ("--chart-limit", "--color-surface-2", 4.5), ("--chart-command", "--color-surface-2", 4.5),
    ("--chart-baseline", "--color-surface-2", 4.5), ("--chart-missing", "--color-surface-2", 4.5),
    ("--chart-event-critical", "--color-surface-2", 4.5), ("--chart-event-warning", "--color-surface-2", 4.5),
    ("--chart-event-info", "--color-surface-2", 4.5), ("--rc-tag-text", "--color-warn", 4.5),
    ("--color-grey-accent", "--color-grey-card", 4.5), ("--color-grey-border", "--color-surface-1", 3.0),
    ("--recap-before", "--color-surface-1", 3.0), ("--recap-after", "--color-surface-1", 4.5),
])
def test_v2_colour_pairs_meet_wcag_aa(fg, bg, minimum):
    t = _tokens()
    assert _hex(t, "--chart-halo") == _hex(t, "--color-surface-2")  # labels sit on the card colour
    assert _contrast(_hex(t, fg), _hex(t, bg)) >= minimum, (fg, bg, round(_contrast(_hex(t, fg), _hex(t, bg)), 2))


# ==================================================================== 8. BUG-009: unexpected query data / errors
class NullReading:
    """Real rows, but one reading of one sensor comes back NULL (a real historian / BigQuery table can hold that)."""

    def __init__(self, inner, sensor, minute):
        self.inner, self.name, self.source_prefix = inner, inner.name, inner.source_prefix
        self.sensor, self.minute = sensor, minute

    def run(self, sql, params):
        rows = [dict(r) for r in self.inner.run(sql, params)]
        for r in rows:
            if r.get("sensor") == self.sensor and r["ts"][11:16] == self.minute:
                r["value"] = None
        return rows


@pytest.mark.xfail(strict=True, raises=TypeError, reason="BUG-009: a NULL reading crashes the query instead of being a gap")
@pytest.mark.parametrize("sid,fn,sensor,minute", [
    ("R01", "get_sensor_window", "mold_temp_c", "02:45"),          # in the window: max() / comparisons
    ("N01", "compare_to_baseline", "coolant_flow_lpm", "02:45"),   # in the window, no deviation found before it
    ("R01", "compare_to_baseline", "coolant_flow_lpm", "01:30"),   # in the baseline period: the mean
])
def test_null_reading_is_a_gap_not_a_crash(ex, sid, fn, sensor, minute):
    line = SCENARIOS[sid]["line"]
    r = QueryExecutor(NullReading(ex.backend, sensor, minute)).execute(
        sid, fn, dict(line=line, machine="M3", sensor=sensor, **W))
    pts = r.card["chart"]["series"][0]["points"]
    if W["start"] <= minute <= W["end"]:
        assert [minute, None] in [p[:2] for p in pts]  # spec 1.3: value null = missing, the line breaks there
    assert r.card["chart"]["key_point"]["value"] is not None and r.card["key_value"] != "No data"


class BrokenSensorQueries:
    """Sensor queries raise, like a transient BigQuery 503."""

    def __init__(self, inner):
        self.inner, self.name, self.source_prefix = inner, inner.name, inner.source_prefix

    def run(self, sql, params):
        if "paired_sensor" in params:
            raise RuntimeError("503 backend error")
        return self.inner.run(sql, params)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="BUG-009: the failed step stays 'running' (spinner) forever")
def test_unexpected_query_error_never_leaves_a_step_running(ex):
    mgr = InvestigationManager(get_settings(), BrokenSensorQueries(ex.backend))
    logging.disable(logging.ERROR)
    try:
        inv = mgr.start("R01", background=False)
    finally:
        logging.disable(logging.NOTSET)
    assert inv.status != "running"
    assert [s["status"] for s in inv.steps if s["status"] == "running"] == [], inv.public()["steps"]
