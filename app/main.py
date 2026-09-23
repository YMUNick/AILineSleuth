"""LineSleuth FastAPI service: API + static front end in one Cloud Run service.

    uvicorn app.main:app --reload
"""
from __future__ import annotations

import hmac
import json
import logging
import re
import secrets
import sys
import threading
import time
from collections import defaultdict, deque

import segno
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import STATIC_DIR, get_settings
from app.data.catalog import MACHINES
from app.data.scenarios import DEMO_SCENARIOS, SCENARIOS
from app.investigations import InvestigationManager
from app.queries.backends import make_backend

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("linesleuth.api")

settings = get_settings()
backend = make_backend(settings)
manager = InvestigationManager(settings, backend)

app = FastAPI(title="LineSleuth", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

WO_ID = re.compile(r"^WO-\d{4,6}$")


# ---------------------------------------------------------------- rate limit (per IP + whole service, per hour)
_hits: dict[str, deque] = defaultdict(deque)
GLOBAL_KEY = "(all clients)"  # not an IP; holds every counted start for GLOBAL_RATE_LIMIT_PER_HOUR


def _client_ip(request: Request) -> str:
    """Client IP for rate limiting (BUG-003).

    Cloud Run's Google Front End APPENDS the address it saw to X-Forwarded-For; everything before that was
    written by the client and can be forged. So take the entry TRUSTED_PROXY_HOPS positions from the right
    (1 = Cloud Run *.run.app; 2 = behind an external Application Load Balancer). request.client.host is only
    used when there is no header at all (local dev): with uvicorn --proxy-headers --forwarded-allow-ips="*"
    (Dockerfile) it holds the FIRST, forgeable entry. See docs/engineering/deploy.md.
    """
    entries = [e.strip() for v in request.headers.getlist("x-forwarded-for") for e in v.split(",") if e.strip()]
    hops = settings.trusted_proxy_hops
    if entries and hops > 0:
        return entries[max(0, len(entries) - hops)]
    return request.client.host if request.client else "unknown"


def _window(key: str, now: float) -> deque:
    q = _hits[key]
    while q and now - q[0] > 3600:
        q.popleft()
    return q


def _check_rate(ip: str) -> None:
    now = time.time()
    if len(_window(ip, now)) >= settings.rate_limit_per_hour:
        raise HTTPException(429, "Rate limit reached. Try again later.")
    if len(_window(GLOBAL_KEY, now)) >= settings.global_rate_limit_per_hour:
        raise HTTPException(429, "Service hourly limit reached. Try again later.")


def _record_hit(ip: str) -> None:
    now = time.time()
    _hits[ip].append(now)
    _hits[GLOBAL_KEY].append(now)


_rate_lock = threading.Lock()


# ---------------------------------------------------------------- who is calling (BUG-004)
# ls_sid: random per-browser id set on the first Investigate; an investigation can only be cancelled by it.
# ls_presenter: set by /?key=<PRESENTER_KEY>; skips the public limits so a stranger cannot block the demo.
SID_COOKIE, PRESENTER_COOKIE = "ls_sid", "ls_presenter"
_SID = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def _session_id(request: Request) -> str | None:
    sid = request.cookies.get(SID_COOKIE, "")
    return sid if _SID.match(sid) else None


def _key_ok(given: str) -> bool:
    key = settings.presenter_key
    return bool(key) and hmac.compare_digest(given.encode(), key.encode())


def _is_presenter(request: Request) -> bool:
    return _key_ok(request.cookies.get(PRESENTER_COOKIE, ""))


def _set_cookie(response: Response, request: Request, name: str, value: str, max_age: int | None = None) -> None:
    response.set_cookie(name, value, max_age=max_age, httponly=True, samesite="lax",
                        secure=request.url.scheme == "https")


# ---------------------------------------------------------------- pages
def _page(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, key: str | None = None):
    if key is not None:  # presenter login: store the key in a cookie, then drop it from the address bar
        resp = RedirectResponse("/", status_code=303)
        if _key_ok(key):
            _set_cookie(resp, request, PRESENTER_COOKIE, key, max_age=7 * 24 * 3600)
        return resp
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
def config(request: Request) -> dict:
    return dict(agent_mode=settings.agent_mode, offline_fixture=settings.agent_mode == "offline_fixture",
                model=settings.gemini_model if settings.agent_mode == "gemini" else None,
                query_backend=backend.name, source_prefix=backend.source_prefix,
                presenter=_is_presenter(request))


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
def start_investigation(body: StartBody, request: Request, response: Response) -> dict:
    if body.scenario_id not in DEMO_SCENARIOS:  # only F8 scenarios are accepted from the public API
        raise HTTPException(400, "Unknown scenario")
    presenter = _is_presenter(request)
    sid = _session_id(request)
    if not sid:
        sid = secrets.token_urlsafe(16)
        _set_cookie(response, request, SID_COOKIE, sid)
    ip = _client_ip(request)
    with _rate_lock:  # check -> start -> record as one step, so parallel requests cannot overshoot
        if not presenter:  # the presenter's own browser is never rate limited (shared venue NAT, rehearsals)
            _check_rate(ip)
        try:
            inv = manager.start(body.scenario_id, owner=sid, presenter=presenter)
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        if not presenter:
            _record_hit(ip)  # BUG-005: only an investigation that actually started uses quota
    log.info(json.dumps({"event": "start", "investigation_id": inv.id, "scenario_id": inv.scenario_id,
                         "client": ip, "xff_entries": sum(len(v.split(",")) for v in
                                                          request.headers.getlist("x-forwarded-for")),
                         "presenter": presenter}))
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
def reset(request: Request, body: ResetBody | None = None) -> dict:
    sid = _session_id(request)  # only this browser's own investigation is cancelled (BUG-004)
    return {"ok": True, "cancelled": manager.cancel(sid) if sid else 0}


@app.exception_handler(Exception)
def unhandled(request: Request, exc: Exception):  # pragma: no cover
    logging.getLogger("linesleuth").exception("unhandled error")
    return JSONResponse({"detail": "Internal error"}, status_code=500)
