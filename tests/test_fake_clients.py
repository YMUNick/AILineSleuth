"""Gemini and BigQuery with fake clients (9/24 meeting, Quinn's checklist): no network, no credentials.

Gemini: the real run_gemini loop and the real google-genai request / response / error types; only
client.models.generate_content is scripted. Covers multi-turn function calling, forced submit, timeouts,
the 429 / 5xx retry cap and token usage (ENH-002).
BigQuery: the real BigQueryBackend and google-cloud-bigquery parameter classes; only bigquery.Client is fake.
It answers from the local DuckDB, so parameter TYPES and table names are checked and cards must match local.
conftest.py blocks every non-loopback connection, so any real call here fails instead of reaching Google.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import re
import socket
import threading
import time
from datetime import datetime

import pytest
from google.genai import errors, types

from app.agent import gemini_agent
from app.agent.prompt import MAX_QUERY_CALLS
from app.config import get_settings
from app.investigations import InvestigationManager
from app.queries.backends import COUNT_WORK_ORDERS, BigQueryBackend, LocalDuckDBBackend
from app.queries.functions import QueryExecutor

W = dict(start="02:30", end="03:00")
R01_QUERIES = [
    ("get_alarm_events", dict(line=2, **W)),
    ("get_sensor_window", dict(line=2, machine="M3", sensor="mold_temp_c", **W)),
    ("compare_to_baseline", dict(line=2, machine="M3", sensor="coolant_flow_lpm", **W)),
    ("get_sensor_window", dict(line=2, machine="M3", sensor="cv_position_pct", **W)),
    ("get_shift_log", dict(line=2, start="02:00", end="03:00")),
]
SUBMIT_R01 = ("submit_conclusion", dict(
    status="root_cause", root_cause_key="cv_valve_stuck_closed", root_cause="Cooling valve CV-2 stuck at 20% open",
    cited_evidence=[2, 3, 4], ruled_out=[dict(evidence_id=5, text="Shift handover at 02:30, no parameter changes")],
    recommended_actions=["Open CV-2 manually per SOP 4.2."], sop_reference="SOP 4.2"))
SUBMIT_GREY = ("submit_conclusion", dict(status="insufficient_evidence", cited_evidence=[], recommended_actions=[]))


@pytest.fixture(scope="module")
def local():
    return LocalDuckDBBackend()


# ==================================================================== Gemini
def reply(*calls, usage=(1000, 50, 200)):
    """A real GenerateContentResponse: function calls + usage_metadata (prompt, output, thinking)."""
    parts = [types.Part(function_call=types.FunctionCall(name=n, args=a)) for n, a in calls]
    meta = None if usage is None else types.GenerateContentResponseUsageMetadata(
        prompt_token_count=usage[0], candidates_token_count=usage[1], thoughts_token_count=usage[2] or None,
        total_token_count=sum(usage))
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts))], usage_metadata=meta)


def api_error(code: int):
    status = {429: "RESOURCE_EXHAUSTED", 503: "UNAVAILABLE", 400: "INVALID_ARGUMENT", 403: "PERMISSION_DENIED"}[code]
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, {"error": {"code": code, "message": status.lower(), "status": status}})


class Slow:
    def __init__(self, seconds, then):
        self.seconds, self.then = seconds, then


class FakeGemini:
    """Stands in for genai.Client. Each generate_content() takes the next scripted item: a response, an exception
    (raised) or Slow(seconds, response). Records every request so tests can inspect contents and config."""

    def __init__(self, script):
        self.script, self.requests, self.models = list(script), [], self

    def generate_content(self, *, model, contents, config):
        self.requests.append(dict(model=model, contents=list(contents), config=config))
        if not self.script:
            raise AssertionError("fake Gemini called more times than scripted")
        item = self.script.pop(0)
        if isinstance(item, Slow):
            time.sleep(item.seconds)
            item = item.then
        if isinstance(item, BaseException):
            raise item
        return item

    @property
    def forced(self) -> list[bool]:
        return [r["config"].tool_config.function_calling_config.allowed_function_names == ["submit_conclusion"]
                for r in self.requests]


@pytest.fixture
def gemini(monkeypatch, local):
    """run(script, sid, **settings overrides) -> (investigation, fake). Always AGENT_MODE=gemini, fast backoff."""
    def run(script, sid="R01", background=False, **overrides):
        fake = FakeGemini(script)
        monkeypatch.setattr(gemini_agent, "_client", fake)
        settings = dataclasses.replace(get_settings(), **{"agent_mode": "gemini", "gcp_project": "fake-project",
                                                          "gemini_retry_backoff_s": 0.01, **overrides})
        mgr = InvestigationManager(settings, local)
        return mgr.start(sid, background=background, owner="t"), fake, mgr
    return run


def _no_running(inv):
    return [s for s in inv.steps if s["status"] == "running"] == []


def _events(caplog, name):
    out = []
    for rec in caplog.records:
        try:
            msg = json.loads(rec.getMessage())
        except ValueError:
            continue
        if msg.get("event") == name:
            out.append(msg)
    return out


def test_multi_turn_function_calling_reaches_a_conclusion(gemini):
    q = R01_QUERIES
    replies = [reply(q[0]), reply(q[1], q[2]), reply(q[3], q[4]), reply(SUBMIT_R01)]
    inv, fake, _ = gemini(replies)
    assert inv.status == "root_cause", inv.error
    assert inv.conclusion["root_cause_key"] == "cv_valve_stuck_closed" and inv.conclusion["cited_evidence"] == [2, 3, 4]
    assert [s["function"] for s in inv.steps] == [n for n, _ in q] and _no_running(inv)
    assert [len(r["contents"]) for r in fake.requests] == [1, 3, 5, 7]  # prompt, then (model turn, results) each turn
    assert {r["model"] for r in fake.requests} == {get_settings().gemini_model}
    third = fake.requests[2]["contents"]
    assert third[1] is replies[0].candidates[0].content  # the model's own turn goes back untouched (thought signatures)
    assert third[3] is replies[1].candidates[0].content
    results = third[4].parts                              # turn 2 ran two calls in parallel -> two function responses
    assert third[4].role == "user" and [p.function_response.name for p in results] == ["get_sensor_window", "compare_to_baseline"]
    assert [p.function_response.response["evidence_id"] for p in results] == [2, 3]
    assert "chart" not in json.dumps([p.function_response.response for p in results], default=str)  # never sent to the model


def test_token_usage_is_logged_per_turn_and_totalled(gemini, caplog):
    caplog.set_level(logging.INFO)
    q = R01_QUERIES
    inv, _, _ = gemini([reply(q[0], usage=(1000, 40, 300)), reply(q[1], q[2], usage=(1800, 60, 0)),
                        reply(q[3], usage=None), reply(SUBMIT_R01, usage=(2600, 120, 500))])
    assert inv.status == "root_cause", inv.error
    expected = dict(applicable=True, note=None, turns=4, retries=0, input_tokens=5400, output_tokens=220,
                    thinking_tokens=800, cached_tokens=0, total_tokens=6420, turns_without_usage=1)
    assert inv.usage == expected and inv.public()["usage"] == expected
    turns = _events(caplog, "gemini_turn")
    assert [t["turn"] for t in turns] == [1, 2, 3, 4]
    assert turns[0]["usage"] == dict(input_tokens=1000, output_tokens=40, thinking_tokens=300, cached_tokens=0,
                                     total_tokens=1340)
    assert turns[1]["usage"]["thinking_tokens"] == 0 and turns[2]["usage"] is None  # not reported -> no guess
    [total] = _events(caplog, "usage")
    assert total["status"] == "root_cause" and total["investigation_id"] == inv.id
    assert {k: total[k] for k in expected} == expected


def test_offline_fixture_usage_is_not_applicable(local, caplog):
    caplog.set_level(logging.INFO)
    inv = InvestigationManager(get_settings(), local).start("R01", background=False)
    u = inv.public()["usage"]
    assert inv.agent_mode == "offline_fixture" and u["applicable"] is False and "OFFLINE FIXTURE" in u["note"]
    counts = {k: v for k, v in u.items() if k not in ("applicable", "note")}
    assert counts and set(counts.values()) == {None}  # "not applicable", never a made-up 0
    [total] = _events(caplog, "usage")
    assert total["applicable"] is False and total["input_tokens"] is None


def test_forced_submit_after_max_query_calls(gemini):
    script = [reply(R01_QUERIES[0]) for _ in range(MAX_QUERY_CALLS)] + [reply(SUBMIT_GREY)]
    inv, fake, _ = gemini(script, max_agent_turns=MAX_QUERY_CALLS + 2)
    assert inv.status == "insufficient_evidence", inv.error
    assert fake.forced == [False] * MAX_QUERY_CALLS + [True]


def test_forced_submit_after_parallel_calls_reach_the_limit(gemini):
    inv, fake, _ = gemini([reply(*[R01_QUERIES[i % 5] for i in range(MAX_QUERY_CALLS)]), reply(SUBMIT_GREY)])
    assert len(inv.steps) == MAX_QUERY_CALLS and fake.forced == [False, True]


def test_last_turn_is_forced_to_submit(gemini):
    inv, fake, _ = gemini([reply(R01_QUERIES[0]), reply(R01_QUERIES[1]), reply(SUBMIT_GREY)], max_agent_turns=3)
    assert inv.status == "insufficient_evidence", inv.error
    assert fake.forced == [False, False, True]


def test_no_conclusion_fails_and_never_fabricates_one(gemini):
    inv, fake, _ = gemini([reply(R01_QUERIES[0]), reply(R01_QUERIES[1])], max_agent_turns=2)
    assert inv.status == "failed" and inv.conclusion is None and "No conclusion after 2 turns" in inv.error
    assert len(fake.requests) == 2 and _no_running(inv)


def test_no_function_call_fails(gemini):
    inv, _, _ = gemini([reply()])
    assert inv.status == "failed" and "no function call" in inv.error and inv.usage["turns"] == 1


def test_gemini_timeout_is_retried_then_succeeds(gemini, caplog):
    caplog.set_level(logging.INFO)
    inv, fake, _ = gemini([Slow(0.6, reply(R01_QUERIES[0])), reply(R01_QUERIES[0]), reply(SUBMIT_GREY)],
                          step_timeout_s=0.2)
    assert inv.status == "insufficient_evidence", inv.error
    assert len(fake.requests) == 3 and inv.usage["retries"] == 1 and inv.usage["turns"] == 2
    [retry] = _events(caplog, "gemini_retry")
    assert retry["reason"].startswith("timed out") and retry["turn"] == 1 and retry["max_retries"] == 2


def test_gemini_timeout_gives_up_after_max_retries(gemini):
    t0 = time.monotonic()
    inv, fake, _ = gemini([Slow(0.5, reply(SUBMIT_GREY)), Slow(0.5, reply(SUBMIT_GREY))],
                          step_timeout_s=0.2, gemini_max_retries=1)
    assert inv.status == "failed" and inv.conclusion is None
    assert "timed out after 0.2s on turn 1" in inv.error and "gave up after 1 retry " in inv.error
    assert len(fake.requests) == 2 and inv.usage["retries"] == 1 and time.monotonic() - t0 < 2


def test_429_is_retried_at_most_max_retries_then_fails(gemini, caplog):
    caplog.set_level(logging.INFO)
    t0 = time.monotonic()
    inv, fake, _ = gemini([api_error(429)] * 10, gemini_max_retries=2, gemini_retry_backoff_s=0.05)
    assert inv.status == "failed" and inv.conclusion is None
    assert len(fake.requests) == 3  # 1 call + 2 retries, not 10
    assert "rate limited (429)" in inv.error and "gave up after 2 retries" in inv.error
    assert inv.usage["retries"] == 2 and inv.usage["turns"] == 0
    assert [r["backoff_s"] for r in _events(caplog, "gemini_retry")] == [0.05, 0.1]  # exponential backoff
    assert time.monotonic() - t0 >= 0.14


def test_429_then_success_continues_the_investigation(gemini):
    inv, fake, _ = gemini([api_error(429), api_error(429), reply(R01_QUERIES[0]), reply(SUBMIT_GREY)])
    assert inv.status == "insufficient_evidence", inv.error
    assert len(fake.requests) == 4 and inv.usage["retries"] == 2


def test_retry_budget_is_per_investigation_not_per_turn(gemini):
    inv, fake, _ = gemini([api_error(429), reply(R01_QUERIES[0]), api_error(503), api_error(429), reply(SUBMIT_GREY)],
                          gemini_max_retries=2)
    assert inv.status == "failed" and "on turn 2" in inv.error and "rate limited (429)" in inv.error
    assert len(fake.requests) == 4 and inv.usage["retries"] == 2 and inv.usage["turns"] == 1


@pytest.mark.parametrize("code", [400, 403])
def test_non_retryable_gemini_error_fails_at_once(gemini, code):
    inv, fake, _ = gemini([api_error(code), reply(SUBMIT_GREY)])
    assert inv.status == "failed" and str(code) in inv.error and len(fake.requests) == 1
    assert inv.usage["retries"] == 0


def test_reset_stops_a_retry_backoff_at_once(gemini):
    inv, fake, mgr = gemini([api_error(429), reply(SUBMIT_GREY)], background=True, gemini_retry_backoff_s=10)
    deadline = time.monotonic() + 5
    while inv.usage["retries"] < 1 and time.monotonic() < deadline:
        time.sleep(0.02)
    assert mgr.cancel("t") == 1
    worker = next(t for t in threading.enumerate() if t.name == f"inv-{inv.id}")
    worker.join(timeout=2)
    assert not worker.is_alive() and inv.status == "cancelled" and len(fake.requests) == 1


def test_retry_settings_come_from_env_and_are_capped(monkeypatch):
    s = get_settings()
    assert (s.gemini_max_retries, s.gemini_retry_backoff_s) == (2, 2.0)
    monkeypatch.setenv("GEMINI_MAX_RETRIES", "0")
    monkeypatch.setenv("GEMINI_RETRY_BACKOFF_S", "0.5")
    assert (get_settings().gemini_max_retries, get_settings().gemini_retry_backoff_s) == (0, 0.5)
    for name, bad in [("GEMINI_MAX_RETRIES", "9"), ("GEMINI_MAX_RETRIES", "-1"), ("GEMINI_RETRY_BACKOFF_S", "60")]:
        monkeypatch.setenv(name, bad)
        with pytest.raises(ValueError, match=name):
            get_settings()
        monkeypatch.setenv(name, "1")


def test_real_client_is_built_without_sdk_retries(monkeypatch):
    """Our loop is the only retry: the SDK must not multiply calls behind GEMINI_MAX_RETRIES."""
    import google.genai as genai

    built = {}
    monkeypatch.setattr(genai, "Client", lambda **kw: built.update(kw) or "client")
    monkeypatch.setattr(gemini_agent, "_client", None)
    settings = dataclasses.replace(get_settings(), gcp_project="fake-project", step_timeout_s=20)
    assert gemini_agent._get_client(settings) == "client"
    assert built["vertexai"] is True and built["project"] == "fake-project"
    assert built["http_options"].retry_options.attempts == 1 and built["http_options"].timeout == 25_000


# ==================================================================== BigQuery
BQ_TYPES = dict(scenario_id="STRING", line="INT64", machine="STRING", sensor="STRING", paired_sensor="STRING",
                start="DATETIME", end="DATETIME", baseline_start="DATETIME", baseline_end="DATETIME")


class FakeBigQueryClient:
    """Stands in for google.cloud.bigquery.Client: records each job, answers from the local DuckDB with the bound
    values, and returns DATETIME columns as datetime objects the way BigQuery does."""

    def __init__(self, local, project=None, **_):
        self.local, self.project, self.jobs = local, project, []

    def query(self, sql, job_config=None):
        self.jobs.append((sql, job_config))
        params = {p.name: p.value for p in job_config.query_parameters}
        local_sql = re.sub(r"`fake-project\.linesleuth_demo\.(\w+)`", r"{\1}", sql)
        rows = self.local.run(local_sql, params)
        return _Job([{k: datetime.strptime(v, "%Y-%m-%d %H:%M:%S") if k in ("ts", "created_at") and v else v
                      for k, v in r.items()} for r in rows])


class _Job:
    def __init__(self, rows):
        self.rows = rows

    def result(self, timeout=None):
        return [_Row(r) for r in self.rows]


class _Row(dict):
    pass  # google.cloud.bigquery.Row also has .items()


@pytest.fixture
def bq(monkeypatch):
    from google.cloud import bigquery

    local = LocalDuckDBBackend()  # own instance: the work-order test writes to it
    monkeypatch.setattr(bigquery, "Client", lambda project=None, **kw: FakeBigQueryClient(local, project, **kw))
    backend = BigQueryBackend("fake-project", "linesleuth_demo")
    return backend, local


def _check_job(sql, job_config):
    names = set(re.findall(r"@(\w+)", sql))
    params = {p.name: p for p in job_config.query_parameters}
    assert names == set(params), (names, set(params))  # every @name bound, nothing extra
    for name, p in params.items():
        assert p.type_ == BQ_TYPES[name], (name, p.type_, p.value)
        assert p.value is not None
    assert "{" not in sql and re.findall(r"FROM (\S+)", sql)[0].startswith("`fake-project.linesleuth_demo.")


@pytest.mark.parametrize("fn,args", R01_QUERIES + [("list_sensors", dict(machine="M3"))],
                         ids=lambda v: v if isinstance(v, str) else "")
def test_bigquery_parameter_types_and_same_card_as_local(bq, fn, args):
    backend, local = bq
    got = QueryExecutor(backend).execute("R01", fn, dict(args))
    want = QueryExecutor(local).execute("R01", fn, dict(args))
    [(sql, job_config)] = backend._client.jobs
    _check_job(sql, job_config)
    assert got.rows == want.rows and got.card == want.card and got.summary == want.summary


def test_bigquery_line_from_gemini_json_is_int64(bq):
    backend, _ = bq
    QueryExecutor(backend).execute("R01", "get_alarm_events", dict(line=2.0, **W))  # JSON numbers arrive as 2.0
    [(_, job_config)] = backend._client.jobs
    line = next(p for p in job_config.query_parameters if p.name == "line")
    assert (line.type_, line.value, type(line.value)) == ("INT64", 2, int)
    assert backend._param("x", True).type_ == "BOOL" and backend._param("x", 2.5).type_ == "FLOAT64"


def test_bigquery_work_order_statements(bq):
    backend, _ = bq
    mgr = InvestigationManager(get_settings(), backend)  # OFFLINE FIXTURE agent, fake BigQuery for data
    inv = mgr.start("R01", background=False)
    wo = mgr.create_work_order(inv)
    jobs = backend._client.jobs
    count_sql, count_cfg = next(j for j in jobs if "COUNT(*)" in j[0])
    assert count_cfg.query_parameters == [] and count_sql == COUNT_WORK_ORDERS.format(
        work_orders="`fake-project.linesleuth_demo.work_orders`")
    insert_sql, insert_cfg = next(j for j in jobs if j[0].lstrip().startswith("INSERT"))
    types_ = {p.name: p.type_ for p in insert_cfg.query_parameters}
    assert types_ == dict(wo_id="STRING", created_at="DATETIME", scenario_id="STRING", investigation_id="STRING",
                          line="INT64", machine="STRING", root_cause_key="STRING", root_cause="STRING",
                          confidence="STRING", priority="STRING", agent_mode="STRING", payload_json="STRING")
    assert "`fake-project.linesleuth_demo.work_orders`" in insert_sql and wo["wo_id"] == "WO-0001"


def test_network_is_blocked_during_tests():
    """Proof that this suite runs offline: a real call to Google would fail here, not silently succeed."""
    with pytest.raises(OSError, match="network access blocked"):
        socket.create_connection(("aiplatform.googleapis.com", 443), timeout=1)
    with pytest.raises(OSError, match="network access blocked"):
        socket.create_connection(("8.8.8.8", 53), timeout=1)
