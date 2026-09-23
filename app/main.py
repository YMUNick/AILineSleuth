"""LineSleuth FastAPI service: API + static front end in one Cloud Run service.

    uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
import re
import sys
import time
from collections import defaultdict, deque

import segno
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import STATIC_DIR, get_settings
from app.data.catalog import MACHINES
from app.data.scenarios import DEMO_SCENARIOS, SCENARIOS
from app.investigations import InvestigationManager
from app.queries.backends import make_backend

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

settings = get_settings()
backend = make_backend(settings)
manager = InvestigationManager(settings, backend)

app = FastAPI(title="LineSleuth", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

WO_ID = re.compile(r"^WO-\d{4,6}$")


# ---------------------------------------------------------------- rate limit (per IP, per hour)
_hits: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")


def _rate_limit(request: Request) -> None:
    now = time.time()
    q = _hits[_client_ip(request)]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= settings.rate_limit_per_hour:
        raise HTTPException(429, "Rate limit reached. Try again later.")
    q.append(now)


# ---------------------------------------------------------------- pages
def _page(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    svg = _page("line-layout.svg")
    svg = svg[svg.index("<svg"):]  # inline (not <img>) so JS can change machine classes (ui-spec 3.2)
    return _page("index.html").replace("<!--LINE_LAYOUT_SVG-->", svg)


@app.get("/wo/{wo_id}", response_class=HTMLResponse)
def work_order_page(wo_id: str) -> str:
    return _page("wo.html")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


# ---------------------------------------------------------------- API
@app.get("/api/config")
def config() -> dict:
    return dict(agent_mode=settings.agent_mode, offline_fixture=settings.agent_mode == "offline_fixture",
                model=settings.gemini_model if settings.agent_mode == "gemini" else None,
                query_backend=backend.name, source_prefix=backend.source_prefix)


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    out = []
    for sid in DEMO_SCENARIOS:
        s = SCENARIOS[sid]
        inc = s["incident"]
        out.append(dict(id=sid, label=s["demo_label"], line=s["line"], machine=inc["machine"],
                        machine_label=MACHINES.get(inc["machine"] or ""), alarm=inc["alarm"],
                        stop_ts=inc["stop_ts"], now=inc["now"], window=list(s["window"])))
    return out


class StartBody(BaseModel):
    scenario_id: str


@app.post("/api/investigations", status_code=201)
def start_investigation(body: StartBody, request: Request) -> dict:
    if body.scenario_id not in DEMO_SCENARIOS:  # only F8 scenarios are accepted from the public API
        raise HTTPException(400, "Unknown scenario")
    _rate_limit(request)
    try:
        inv = manager.start(body.scenario_id)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return inv.public()


def _inv(inv_id: str):
    inv = manager.get(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return inv


@app.get("/api/investigations/{inv_id}")
def get_investigation(inv_id: str) -> dict:
    return _inv(inv_id).public()


@app.get("/api/investigations/{inv_id}/evidence/{step}")
def get_evidence_rows(inv_id: str, step: int) -> dict:
    inv = _inv(inv_id)
    with inv.lock:
        s = next((s for s in inv.steps if s["step"] == step), None)
        rows = inv.rows.get(step)
    if s is None or rows is None:
        raise HTTPException(404, "Evidence not found")
    return dict(step=step, function=s["function"], args=s["args"], query_id=s["query_id"],
                source=f"{backend.source_prefix}.{s['source_table']}", row_count=len(rows),
                highlight_row_ids=s["card"].get("highlight_row_ids", []), rows=rows)


@app.post("/api/investigations/{inv_id}/workorder", status_code=201)
def create_work_order(inv_id: str, request: Request) -> dict:
    inv = _inv(inv_id)
    try:
        wo = manager.create_work_order(inv)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return dict(wo, url=_wo_url(request, wo["wo_id"]))


def _wo_url(request: Request, wo_id: str) -> str:
    base = settings.public_base_url or str(request.base_url).rstrip("/")
    return f"{base}/wo/{wo_id}"


@app.get("/api/workorders/{wo_id}")
def get_work_order(wo_id: str) -> dict:
    if not WO_ID.match(wo_id):
        raise HTTPException(404, "Work order not found")
    wo = manager.get_work_order(wo_id)
    if not wo:
        raise HTTPException(404, "Work order not found")
    return wo


@app.get("/api/workorders/{wo_id}/qr.svg")
def work_order_qr(wo_id: str, request: Request) -> Response:
    if not WO_ID.match(wo_id):
        raise HTTPException(404, "Work order not found")
    qr = segno.make(_wo_url(request, wo_id), error="m")
    svg = qr.svg_inline(scale=8, border=0, dark="#000000", light="#FFFFFF")
    return Response(svg, media_type="image/svg+xml")


class ResetBody(BaseModel):
    scenario_id: str | None = None


@app.post("/api/reset")
def reset(body: ResetBody | None = None) -> dict:
    manager.reset()
    return {"ok": True}


@app.exception_handler(Exception)
def unhandled(request: Request, exc: Exception):  # pragma: no cover
    logging.getLogger("linesleuth").exception("unhandled error")
    return JSONResponse({"detail": "Internal error"}, status_code=500)
