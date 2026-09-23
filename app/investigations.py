"""Investigation lifecycle: start (background thread), steps, conclusion, cancel/reset, work orders.

State is kept in process memory. Cloud Run must therefore run with max-instances=1 and
CPU always allocated (--no-cpu-throttling), see docs/engineering/deploy.md.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone

from app.agent.conclusion import finalize
from app.agent.gemini_agent import run_gemini
from app.agent.offline_fixture import run_fixture
from app.config import Settings
from app.data.scenarios import SCENARIOS
from app.queries.backends import COUNT_WORK_ORDERS, INSERT_WORK_ORDER, SELECT_WORK_ORDER, QueryBackend
from app.queries.functions import QueryArgError, QueryExecutor

log = logging.getLogger("linesleuth.investigation")


class Cancelled(Exception):
    pass


class Investigation:
    def __init__(self, scenario_id: str, settings: Settings):
        self.id = uuid.uuid4().hex[:12]
        self.scenario_id = scenario_id
        self.scenario = SCENARIOS[scenario_id]
        self.agent_mode = settings.agent_mode
        self.model = settings.gemini_model if settings.agent_mode == "gemini" else None
        self.status = "running"  # running | root_cause | insufficient_evidence | failed | cancelled
        self.steps: list[dict] = []
        self.rows: dict[int, list[dict]] = {}
        self.conclusion: dict | None = None
        self.error: str | None = None
        self.work_order_id: str | None = None
        self.started = time.monotonic()
        self.finished: float | None = None
        self.cancel_event = threading.Event()
        self.lock = threading.Lock()

    def public(self) -> dict:
        with self.lock:
            elapsed = (self.finished or time.monotonic()) - self.started
            return dict(id=self.id, scenario_id=self.scenario_id, status=self.status, agent_mode=self.agent_mode,
                        model=self.model, elapsed_s=round(elapsed, 1), steps=[dict(s) for s in self.steps],
                        conclusion=self.conclusion, error=self.error, work_order_id=self.work_order_id)


class _Context:
    """What an agent runner may do: call a fixed function, and check for cancel/deadline."""

    def __init__(self, inv: Investigation, executor: QueryExecutor, deadline: float):
        self._inv, self._executor, self._deadline = inv, executor, deadline
        self.scenario_id, self.scenario, self.investigation_id = inv.scenario_id, inv.scenario, inv.id

    def check(self) -> None:
        if self._inv.cancel_event.is_set():
            raise Cancelled()
        if time.monotonic() > self._deadline:
            raise TimeoutError("Investigation exceeded its time budget")

    def call_tool(self, name: str, args: dict) -> dict:
        self.check()
        inv = self._inv
        with inv.lock:
            step_no = len(inv.steps) + 1
            step = dict(step=step_no, function=name, args=args, status="running", card=None)
            inv.steps.append(step)
        try:
            r = self._executor.execute(inv.scenario_id, name, args, inv.id)
        except (QueryArgError, TimeoutError) as e:
            with inv.lock:
                step.update(status="error", error=str(e), card=dict(title=name, tone="normal", key_value="",
                                                                   key_detail="Query failed", check=None))
            return {"evidence_id": step_no, "error": str(e)}
        with inv.lock:
            inv.rows[step_no] = r.rows
            step.update(status="cached" if r.cached else "done", card=r.card, query_id=r.query_id,
                        source_table=r.source_table, time_range=r.time_range, row_count=r.row_count,
                        duration_ms=r.duration_ms)
        return {"evidence_id": step_no, "function": name, "time_range": r.time_range,
                "row_count": r.row_count, "summary": r.summary}


class InvestigationManager:
    def __init__(self, settings: Settings, backend: QueryBackend):
        self.settings = settings
        self.backend = backend
        self.executor = QueryExecutor(backend, timeout_s=settings.step_timeout_s)
        self._items: dict[str, Investigation] = {}
        self._work_orders: dict[str, dict] = {}
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- investigations
    def active(self) -> Investigation | None:
        with self._lock:
            return next((i for i in self._items.values() if i.status == "running"), None)

    def start(self, scenario_id: str, background: bool = True) -> Investigation:
        if self.active():
            raise RuntimeError("An investigation is already running. Press Reset first.")
        inv = Investigation(scenario_id, self.settings)
        with self._lock:
            self._items[inv.id] = inv
        if background:
            threading.Thread(target=self._run, args=(inv,), daemon=True, name=f"inv-{inv.id}").start()
        else:
            self._run(inv)
        return inv

    def get(self, inv_id: str) -> Investigation | None:
        return self._items.get(inv_id)

    def reset(self) -> None:
        with self._lock:
            for inv in self._items.values():
                if inv.status == "running":
                    inv.cancel_event.set()
                    inv.status = "cancelled"
                    inv.finished = time.monotonic()

    def _run(self, inv: Investigation) -> None:
        ctx = _Context(inv, self.executor, inv.started + self.settings.investigation_timeout_s)
        runner = run_gemini if inv.agent_mode == "gemini" else run_fixture
        try:
            raw = runner(ctx, self.settings)
            ctx.check()
            conclusion = finalize(raw, inv.steps, inv.scenario)
            with inv.lock:
                if inv.status == "running":
                    inv.conclusion = conclusion
                    inv.status = conclusion["status"]
            log.info(json.dumps({"event": "conclusion", "investigation_id": inv.id, "scenario_id": inv.scenario_id,
                                 "agent_mode": inv.agent_mode, "raw": raw, "status": conclusion["status"],
                                 "root_cause_key": conclusion.get("root_cause_key")}, default=str))
        except Cancelled:
            pass
        except Exception as e:  # surfaced as "Investigation failed" - never replaced by a fake answer
            log.exception("investigation %s failed", inv.id)
            with inv.lock:
                if inv.status == "running":
                    inv.status = "failed"
                    inv.error = f"{type(e).__name__}: {e}"
        finally:
            with inv.lock:
                inv.finished = inv.finished or time.monotonic()

    # ---------------------------------------------------------------- work orders
    def create_work_order(self, inv: Investigation) -> dict:
        with inv.lock:
            if inv.work_order_id:
                return self.get_work_order(inv.work_order_id)
            c = inv.conclusion
        if not c or c["status"] != "root_cause":
            raise ValueError("A work order needs a root-cause conclusion")
        n = self.backend.run(COUNT_WORK_ORDERS, {})[0]["n"] + 1
        wo_id = f"WO-{n:04d}"
        created = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        payload = dict(wo_id=wo_id, created_at=created.strftime("%Y-%m-%d %H:%M UTC"), status="Open",
                       scenario_id=inv.scenario_id, investigation_id=inv.id, agent_mode=inv.agent_mode,
                       model=inv.model, line=c["line"], machine=c["machine"], machine_label=c["machine_label"],
                       detected=c["detected"], root_cause=c["root_cause"], confidence=c["confidence"],
                       evidence=c["evidence_lines"],
                       ruled_out=[r["text"] for r in c["ruled_out"]], recommended_actions=c["recommended_actions"],
                       sop_reference=c["sop_reference"], priority=c["priority"])
        self.backend.run(INSERT_WORK_ORDER, dict(
            wo_id=wo_id, created_at=created, scenario_id=inv.scenario_id, investigation_id=inv.id,
            line=int(c["line"]), machine=c["machine"] or "", root_cause_key=c["root_cause_key"],
            root_cause=c["root_cause"], confidence=c["confidence"], priority=c["priority"],
            agent_mode=inv.agent_mode, payload_json=json.dumps(payload, ensure_ascii=False)))
        with inv.lock:
            inv.work_order_id = wo_id
        self._work_orders[wo_id] = payload
        log.info(json.dumps({"event": "work_order", "wo_id": wo_id, "investigation_id": inv.id}))
        return payload

    def get_work_order(self, wo_id: str) -> dict | None:
        if wo_id in self._work_orders:
            return self._work_orders[wo_id]
        rows = self.backend.run(SELECT_WORK_ORDER, dict(wo_id=wo_id))
        return json.loads(rows[0]["payload_json"]) if rows else None
