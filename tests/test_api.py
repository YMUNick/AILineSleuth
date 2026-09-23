"""API flow in OFFLINE FIXTURE mode (no GCP). Checks plumbing and labelling, not AI quality."""
import time

import pytest
from fastapi.testclient import TestClient

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
