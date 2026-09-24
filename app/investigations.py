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
from app.agent.gemini_agent import new_usage, run_gemini
from app.agent.offline_fixture import run_fixture
from app.config import Settings
from app.data.scenarios import SCENARIOS
from app.queries.backends import COUNT_WORK_ORDERS, INSERT_WORK_ORDER, SELECT_WORK_ORDER, QueryBackend
from app.queries.functions import QueryArgError, QueryExecutor

log = logging.getLogger("linesleuth.investigation")


class Cancelled(Exception):
    pass


class Investigation:
    def __init__(self, scenario_id: str, settings: Settings, owner: str = "", presenter: bool = False):
        self.id = uuid.uuid4().hex[:12]
        self.owner = owner          # browser session that started it; only that session can cancel it (BUG-004)
        self.presenter = presenter  # started with the presenter key: not counted against the public limits
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
        self.usage = new_usage(settings.agent_mode)  # Gemini turns / retries / tokens (ENH-002); None = offline
        self.started = time.monotonic()
        self.finished: float | None = None
        self.cancel_event = threading.Event()
        self.lock = threading.Lock()

    def public(self) -> dict:
        with self.lock:
            elapsed = (self.finished or time.monotonic()) - self.started
            return dict(id=self.id, scenario_id=self.scenario_id, status=self.status, agent_mode=self.agent_mode,
                        model=self.model, elapsed_s=round(elapsed, 1), steps=[dict(s) for s in self.steps],
                        conclusion=self.conclusion, error=self.error, work_order_id=self.work_order_id,
                        usage=dict(self.usage))


# Short text for the step and the model; the exception itself only goes to the log (BUG-009).
QUERY_BACKEND_ERROR = "Query failed on the data backend (not an argument problem). No data from this step."


def _fail_step(inv: Investigation, step: dict, error: str) -> None:
    """A step that did not produce a card: status error, "Query failed", no chart (ui-v2-spec 1.6)."""
    with inv.lock:
        step.update(status="error", error=error, card=dict(title=step["function"], tone="normal", key_value="",
                                                           key_detail="Query failed", check=None, chart=None))


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

    def wait(self, seconds: float) -> None:
        """Retry backoff: sleeps, but wakes up at once on cancel and never past the investigation deadline."""
        self._inv.cancel_event.wait(max(0.0, min(seconds, self._deadline - time.monotonic())))
        self.check()

    def add_usage(self, **counts: int) -> None:
        """Adds Gemini counts (turns, retries, tokens) to the investigation's totals (ENH-002)."""
        with self._inv.lock:
            u = self._inv.usage
            for k, v in counts.items():
                u[k] = (u.get(k) or 0) + v

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
            _fail_step(inv, step, str(e))
            return {"evidence_id": step_no, "error": str(e)}
        except Exception as e:  # backend error (e.g. BigQuery 503 / quota): this step fails, the rest goes on (BUG-009)
            log.exception(json.dumps({"event": "query_error", "investigation_id": inv.id, "step": step_no,
                                      "function": name, "error": f"{type(e).__name__}: {e}"}, default=str))
            _fail_step(inv, step, QUERY_BACKEND_ERROR)
            return {"evidence_id": step_no, "error": QUERY_BACKEND_ERROR}
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
        self._wo_lock = threading.Lock()  # investigations can now run side by side; keep WO numbering serial

    # ---------------------------------------------------------------- investigations
    def start(self, scenario_id: str, background: bool = True, owner: str = "",
              presenter: bool = False) -> Investigation:
        """One running investigation per owner (browser session). Public investigations are capped at
        MAX_CONCURRENT_INVESTIGATIONS; the presenter's never wait for, or get blocked by, other people's (BUG-004)."""
        with self._lock:
            running = [i for i in self._items.values() if i.status == "running"]
            if any(i.owner == owner for i in running):
                raise RuntimeError("Your investigation is still running. Press Reset first.")
            if not presenter and sum(not i.presenter for i in running) >= self.settings.max_concurrent_investigations:
                raise RuntimeError("Too many investigations are running right now. Try again in a minute.")
            inv = Investigation(scenario_id, self.settings, owner=owner, presenter=presenter)
            self._items[inv.id] = inv
        if background:
            threading.Thread(target=self._run, args=(inv,), daemon=True, name=f"inv-{inv.id}").start()
        else:
            self._run(inv)
        return inv

    def get(self, inv_id: str) -> Investigation | None:
        return self._items.get(inv_id)

    def reset(self) -> None:
        """Cancel EVERY running investigation. Internal use only (regression runner); the public
        /api/reset calls cancel(owner) so nobody can cancel someone else's investigation (BUG-004)."""
        with self._lock:
            targets = [i for i in self._items.values() if i.status == "running"]
        for inv in targets:
            self._cancel(inv)

    def cancel(self, owner: str) -> int:
        """Cancel the running investigations started by this owner. Returns how many were cancelled."""
        with self._lock:
            targets = [i for i in self._items.values() if i.status == "running" and i.owner == owner]
        return sum(self._cancel(inv) for inv in targets)

    @staticmethod
    def _cancel(inv: Investigation) -> bool:
        with inv.lock:
            if inv.status != "running":
                return False
            inv.cancel_event.set()
            inv.status = "cancelled"
            inv.finished = time.monotonic()
            return True

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
                    inv.finished = time.monotonic()  # the Recap "After" time stops at the conclusion
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
                left = [s for s in inv.steps if s["status"] == "running"]
            for s in left:  # safety net: a finished investigation never shows a spinning "Querying…" card (BUG-009)
                _fail_step(inv, s, "Investigation ended before this query finished")
            # one line per investigation for the cost estimate (ENH-002); counts are null in OFFLINE FIXTURE
            log.info(json.dumps({"event": "usage", "investigation_id": inv.id, "scenario_id": inv.scenario_id,
                                 "agent_mode": inv.agent_mode, "model": inv.model, "status": inv.status,
                                 **inv.public()["usage"]}))

    # ---------------------------------------------------------------- work orders
    def create_work_order(self, inv: Investigation) -> dict:
        with inv.lock:
            if inv.work_order_id:
                return self.get_work_order(inv.work_order_id)
            c = inv.conclusion
        if not c or c["status"] != "root_cause":
            raise ValueError("A work order needs a root-cause conclusion")
        with self._wo_lock:
            return self._insert_work_order(inv, c)

    def _insert_work_order(self, inv: Investigation, c: dict) -> dict:
        with inv.lock:  # a second click may have waited on _wo_lock while the first one created it
            if inv.work_order_id:
                return self.get_work_order(inv.work_order_id)
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
