"""Query backends. Both run the same parameterised SQL templates.

SQL templates use `{sensor_readings}` / `{events}` / `{sensor_catalog}` / `{work_orders}`
placeholders for table names and `@name` for bound parameters. Only the fixed templates in
app/queries/functions.py and the work-order statements below are ever executed; the LLM
never supplies SQL.
"""
from __future__ import annotations

import re
import threading
from datetime import datetime
from typing import Any, Protocol

from app.config import DATA_DIR, Settings

TABLES = ("sensor_readings", "events", "sensor_catalog", "work_orders")

WORK_ORDER_DDL_DUCKDB = """
CREATE TABLE IF NOT EXISTS work_orders (
  wo_id VARCHAR PRIMARY KEY, created_at TIMESTAMP, scenario_id VARCHAR, investigation_id VARCHAR,
  line INTEGER, machine VARCHAR, root_cause_key VARCHAR, root_cause VARCHAR,
  confidence VARCHAR, priority VARCHAR, agent_mode VARCHAR, payload_json VARCHAR)
"""

INSERT_WORK_ORDER = """
INSERT INTO {work_orders} (wo_id, created_at, scenario_id, investigation_id, line, machine,
  root_cause_key, root_cause, confidence, priority, agent_mode, payload_json)
VALUES (@wo_id, @created_at, @scenario_id, @investigation_id, @line, @machine,
  @root_cause_key, @root_cause, @confidence, @priority, @agent_mode, @payload_json)
"""
SELECT_WORK_ORDER = "SELECT payload_json FROM {work_orders} WHERE wo_id = @wo_id"
COUNT_WORK_ORDERS = "SELECT COUNT(*) AS n FROM {work_orders}"


class QueryBackend(Protocol):
    name: str
    source_prefix: str  # shown on evidence cards, e.g. "linesleuth_demo"

    def run(self, sql: str, params: dict[str, Any]) -> list[dict]: ...


def _normalise(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        out[k] = v
    return out


class LocalDuckDBBackend:
    """In-process DuckDB loaded from the generated CSVs. For development and tests."""

    name = "local"

    def __init__(self, dataset: str = "linesleuth_demo"):
        import duckdb

        from app.data.generate import ensure_generated

        ensure_generated()
        self.source_prefix = f"{dataset} (local DuckDB)"
        self._lock = threading.Lock()
        self._con = duckdb.connect(":memory:")
        types = {
            "sensor_readings": "{'row_id':'VARCHAR','scenario_id':'VARCHAR','ts':'TIMESTAMP','line':'INTEGER','machine':'VARCHAR','sensor':'VARCHAR','value':'DOUBLE','unit':'VARCHAR'}",
            "events": "{'row_id':'VARCHAR','scenario_id':'VARCHAR','ts':'TIMESTAMP','line':'INTEGER','machine':'VARCHAR','event_type':'VARCHAR','code':'VARCHAR','severity':'VARCHAR','actor':'VARCHAR','message':'VARCHAR'}",
            "sensor_catalog": "{'row_id':'VARCHAR','machine':'VARCHAR','machine_name':'VARCHAR','sensor':'VARCHAR','unit':'VARCHAR','normal_low':'DOUBLE','normal_high':'DOUBLE','sop_section':'VARCHAR'}",
        }
        for table, cols in types.items():
            path = (DATA_DIR / f"{table}.csv").as_posix()
            self._con.execute(
                f"CREATE TABLE {table} AS SELECT * FROM read_csv('{path}', header=true, columns={cols})"
            )
        self._con.execute(WORK_ORDER_DDL_DUCKDB)

    def run(self, sql: str, params: dict[str, Any]) -> list[dict]:
        sql = sql.format(**{t: t for t in TABLES})
        sql = re.sub(r"@(\w+)", r"$\1", sql)
        with self._lock:
            cur = self._con.execute(sql, params)
            if cur.description is None:
                return []
            cols = [d[0] for d in cur.description]
            return [_normalise(dict(zip(cols, r))) for r in cur.fetchall()]


class BigQueryBackend:
    """BigQuery backend. Tables are created/loaded by scripts/load_bigquery.py.

    Timestamps are DATETIME (plant local time, no timezone) to match the CSVs exactly.
    """

    name = "bigquery"

    def __init__(self, project: str, dataset: str):
        from google.cloud import bigquery

        self._bq = bigquery
        self._client = bigquery.Client(project=project)
        self._prefix = f"`{project}.{dataset}"
        self.source_prefix = dataset

    def _param(self, name: str, value: Any):
        bq = self._bq
        if isinstance(value, bool):
            return bq.ScalarQueryParameter(name, "BOOL", value)
        if isinstance(value, int):
            return bq.ScalarQueryParameter(name, "INT64", value)
        if isinstance(value, float):
            return bq.ScalarQueryParameter(name, "FLOAT64", value)
        if isinstance(value, datetime):
            return bq.ScalarQueryParameter(name, "DATETIME", value)
        return bq.ScalarQueryParameter(name, "STRING", value)

    def run(self, sql: str, params: dict[str, Any]) -> list[dict]:
        sql = sql.format(**{t: f"{self._prefix}.{t}`" for t in TABLES})
        job_config = self._bq.QueryJobConfig(
            query_parameters=[self._param(k, v) for k, v in params.items()],
            use_query_cache=True,
        )
        rows = self._client.query(sql, job_config=job_config).result()
        return [_normalise(dict(r.items())) for r in rows]


def make_backend(settings: Settings) -> QueryBackend:
    if settings.query_backend == "bigquery":
        return BigQueryBackend(settings.gcp_project, settings.bq_dataset)
    return LocalDuckDBBackend(settings.bq_dataset)
