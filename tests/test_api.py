"""API flow in OFFLINE FIXTURE mode (no GCP). Checks plumbing and labelling, not AI quality."""
import dataclasses
import time
from collections import defaultdict, deque

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.agent.conclusion import finalize
from app.data.scenarios import SCENARIOS
from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _run(client, sid):
    client.post("/api/reset", json={})
    r = client.post("/api/investigations", json={"scenario_id": sid})
    assert r.status_code == 201, r.text
    inv_id = r.json()["id"]
    for _ in range(100):
        inv = client.get(f"/api/investigations/{inv_id}").json()
        if inv["status"] != "running":
            return inv
        time.sleep(0.05)
    raise AssertionError("investigation did not finish")


def test_config_is_labelled_offline_fixture(client):
    cfg = client.get("/api/config").json()
    assert cfg["agent_mode"] == "offline_fixture" and cfg["offline_fixture"] is True


def test_index_inlines_svg(client):
    html = client.get("/").text
    assert 'id="L2-M3-CV2"' in html and "<img" not in html.split("fixture-banner")[0]
    assert "OFFLINE FIXTURE" in html


def test_main_scenario_flow_and_work_order(client):
    inv = _run(client, "R01")
    assert inv["status"] == "root_cause" and inv["agent_mode"] == "offline_fixture"
    c = inv["conclusion"]
    assert c["confidence"] == "High" and c["cited_evidence"] == [2, 3, 4]
    # evidence rows can be fetched for every card
    for step in inv["steps"]:
        ev = client.get(f"/api/investigations/{inv['id']}/evidence/{step['step']}").json()
        assert ev["row_count"] == step["row_count"]
        assert set(ev["highlight_row_ids"]) <= {r["row_id"] for r in ev["rows"]}
    wo = client.post(f"/api/investigations/{inv['id']}/workorder").json()
    again = client.post(f"/api/investigations/{inv['id']}/workorder").json()
    assert wo["wo_id"] == again["wo_id"]  # idempotent: one click, one work order
    page = client.get(f"/api/workorders/{wo['wo_id']}").json()
    assert page["root_cause"] == c["root_cause"] and page["evidence"] == c["evidence_lines"]
    assert page["recommended_actions"] == c["recommended_actions"] and page["agent_mode"] == "offline_fixture"
    assert client.get(f"/api/workorders/{wo['wo_id']}/qr.svg").text.startswith("<svg")
    assert client.get(f"/wo/{wo['wo_id']}").status_code == 200


def test_normal_scenario_gives_grey_card(client):
    inv = _run(client, "N01")
    assert inv["status"] == "insufficient_evidence"
    assert [k["name"] for k in inv["conclusion"]["checked"]] == ["Alarm events", "Mold temperature", "Coolant flow", "Shift & maintenance log"]
    assert client.post(f"/api/investigations/{inv['id']}/workorder").status_code == 409


def test_only_demo_scenarios_are_public(client):
    assert client.post("/api/investigations", json={"scenario_id": "R07"}).status_code == 400
    assert client.post("/api/investigations", json={"scenario_id": "'; DROP TABLE x"}).status_code == 400


def test_unknown_work_order(client):
    assert client.get("/api/workorders/WO-9999").status_code == 404
    assert client.get("/api/workorders/../../etc").status_code == 404


def test_root_cause_needs_two_valid_citations():
    steps = [dict(step=1, status="done", card=dict(tone="warn", title="A", key_value="1", key_detail="x", check=("A", "x")))]
    raw = dict(status="root_cause", root_cause="Something", root_cause_key="other", cited_evidence=[1, 99],
               recommended_actions=["Do it"])
    out = finalize(raw, steps, SCENARIOS["R01"])
    assert out["status"] == "insufficient_evidence" and out["note"]


# ---------------------------------------------------------------- BUG-003 / BUG-004: who is calling
KEY = "presenter-key-for-tests-0123"


@pytest.mark.parametrize("hops,xff,expected", [
    (1, None, "9.9.9.9"),                                   # local dev: no proxy header
    (1, "203.0.113.9", "203.0.113.9"),                      # Cloud Run: GFE appends the real IP
    (1, "10.0.0.1, 10.0.0.2, 203.0.113.9", "203.0.113.9"),  # forged entries in front are ignored
    (2, "10.0.0.1, 203.0.113.9, 34.1.2.3", "203.0.113.9"),  # behind an external load balancer
])
def test_client_ip_uses_proxy_appended_entry(monkeypatch, hops, xff, expected):
    import app.main as m
    monkeypatch.setattr(m, "settings", dataclasses.replace(m.settings, trusted_proxy_hops=hops))
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    assert m._client_ip(Request({"type": "http", "headers": headers, "client": ("9.9.9.9", 1)})) == expected


@pytest.fixture
def browsers(monkeypatch):
    """Presenter and a stranger: two browsers (separate cookie jars) behind the same IP."""
    import app.main as m
    monkeypatch.setattr(m, "_hits", defaultdict(deque))
    monkeypatch.setattr(m, "settings", dataclasses.replace(m.settings, presenter_key=KEY, rate_limit_per_hour=1))
    monkeypatch.setattr(m.manager, "settings", dataclasses.replace(
        m.manager.settings, fixture_step_delay_s=0.3, max_concurrent_investigations=1))
    presenter, stranger = TestClient(m.app), TestClient(m.app)
    yield presenter, stranger
    for c in (presenter, stranger):
        c.post("/api/reset", json={})


def _login(client, key):
    r = client.get(f"/?key={key}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"  # key is dropped from the address bar
    return client.get("/api/config").json()["presenter"]


def test_stranger_cannot_block_or_cancel_the_presenter(browsers):
    presenter, stranger = browsers
    assert _login(presenter, KEY) is True
    assert stranger.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 201  # fills public slot
    p = presenter.post("/api/investigations", json={"scenario_id": "R01"})
    assert p.status_code == 201                                             # not blocked by the stranger
    assert stranger.post("/api/reset", json={}).json()["cancelled"] == 1    # cancels only its own
    assert presenter.get(f"/api/investigations/{p.json()['id']}").json()["status"] == "running"


def test_public_concurrency_cap_and_own_reset(browsers, monkeypatch):
    import app.main as m
    monkeypatch.setattr(m, "settings", dataclasses.replace(m.settings, rate_limit_per_hour=10))
    presenter, stranger = browsers
    assert stranger.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 201
    assert presenter.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 409  # no key: cap 1
    assert presenter.post("/api/reset", json={}).json()["cancelled"] == 0   # nothing of its own to cancel


def test_presenter_skips_rate_limit_and_wrong_key_does_nothing(browsers):
    presenter, stranger = browsers
    assert _login(stranger, "wrong-key-wrong-key-wrong") is False
    assert _login(presenter, KEY) is True
    for _ in range(3):  # public limit is 1/hour; the presenter is never counted or blocked
        presenter.post("/api/reset", json={})
        assert presenter.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 201
    assert stranger.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 201
    stranger.post("/api/reset", json={})
    assert stranger.post("/api/investigations", json={"scenario_id": "N01"}).status_code == 429


# ---------------------------------------------------------------- UI v2: SVG v2, Recap baseline (ui-v2-spec 2, 4.2)
def test_index_inlines_line_layout_v2(client):
    html = client.get("/").text
    assert 'viewBox="0 0 1200 600"' in html and 'id="L2-badge"' in html and 'class="rc-tag"' in html
    assert 'id="plant-live"' in html and 'id="recap"' in html and 'id="show-summary"' in html


def test_steps_carry_chart_data(client):
    inv = _run(client, "R01")
    kinds = [s["card"]["chart"]["kind"] for s in inv["steps"]]
    assert kinds == ["events", "series_limit", "series_baseline", "command_vs_actual", "events"]


@pytest.mark.parametrize("minutes,source,expected", [
    ("", "", None),
    ("35", "", None),                                   # a number without a source counts as not set
    ("", "Median of 3 plant-manager interviews", None),
    ("0", "Interviews", None), ("481", "Interviews", None), ("nan", "Interviews", None), ("abc", "Interviews", None),
    ("35", "x" * 121, None),
    ("35", "Median of 3 plant-manager interviews, Sep 2026",
     dict(minutes=35, source="Median of 3 plant-manager interviews, Sep 2026")),
    ("12.5", "Stopwatch, 4 drills", dict(minutes=12.5, source="Stopwatch, 4 drills")),
])
def test_manual_baseline_needs_valid_minutes_and_a_source(client, monkeypatch, minutes, source, expected):
    import app.main as m
    monkeypatch.setattr(m, "settings", dataclasses.replace(m.settings, manual_baseline_min=minutes,
                                                           manual_baseline_source=source))
    assert client.get("/api/config").json()["manual_baseline"] == expected


def test_no_hard_coded_manual_baseline_in_app():
    from app.config import ROOT
    for path in ROOT.rglob("*"):
        if path.suffix in (".py", ".js", ".html", ".css", ".svg"):
            text = path.read_text(encoding="utf-8").lower()
            for banned in ("40 min", "40 minutes", "90 sec"):
                assert banned not in text, (path, banned)


# ---------------------------------------------------------------- daily limit (9/24 meeting: DAILY_INVESTIGATION_LIMIT)
@pytest.fixture
def daily(browsers, monkeypatch):
    """Daily limit of 2, hourly limits out of the way; fresh counter."""
    import app.main as m
    monkeypatch.setattr(m, "_daily", {"day": None, "count": 0})
    monkeypatch.setattr(m, "settings", dataclasses.replace(
        m.settings, rate_limit_per_hour=100, global_rate_limit_per_hour=100, daily_investigation_limit=2))
    return (m, *browsers)


def _start(client):
    client.post("/api/reset", json={})
    return client.post("/api/investigations", json={"scenario_id": "N01"})


def test_daily_limit_returns_429_with_a_clear_message(daily):
    m, _, stranger = daily
    assert _start(stranger).status_code == 201 and _start(stranger).status_code == 201
    r = _start(stranger)
    assert r.status_code == 429 and r.headers["x-limit"] == "daily"
    assert "Today's demo limit of 2 investigations" in r.json()["detail"] and "Taipei" in r.json()["detail"]
    assert m._daily["count"] == 2  # the refused request is not counted


def test_daily_limit_skips_the_presenter_and_resets_next_day(daily, monkeypatch):
    m, presenter, stranger = daily
    assert _login(presenter, KEY) is True
    for _ in range(3):  # like GLOBAL_RATE_LIMIT_PER_HOUR: the presenter is never counted or blocked
        assert _start(presenter).status_code == 201
    assert m._daily["count"] == 0
    _start(stranger), _start(stranger)
    assert _start(stranger).status_code == 429
    monkeypatch.setattr(m, "_today", lambda: "2099-01-01")  # 00:00 Asia/Taipei passed
    assert _start(stranger).status_code == 201 and m._daily == {"day": "2099-01-01", "count": 1}


def test_daily_limit_zero_means_no_limit(daily, monkeypatch):
    m, _, stranger = daily
    monkeypatch.setattr(m, "settings", dataclasses.replace(m.settings, daily_investigation_limit=0))
    for _ in range(4):
        assert _start(stranger).status_code == 201


def test_daily_limit_day_starts_at_midnight_taipei():
    import app.main as m
    from datetime import datetime, timezone
    assert m.DAY_TZ.utcoffset(None).total_seconds() == 8 * 3600
    assert datetime(2026, 9, 24, 16, 0, tzinfo=timezone.utc).astimezone(m.DAY_TZ).date().isoformat() == "2026-09-25"


def test_daily_limit_setting_is_validated(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("DAILY_INVESTIGATION_LIMIT", "-1")
    with pytest.raises(ValueError, match="DAILY_INVESTIGATION_LIMIT"):
        Settings.from_env().validate()
    monkeypatch.setenv("DAILY_INVESTIGATION_LIMIT", "0")
    Settings.from_env().validate()
    assert Settings.from_env().daily_investigation_limit == 0
