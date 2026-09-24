"""Runtime settings, all from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # .env is optional; Cloud Run uses real env vars / Secret Manager
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "generated"
STATIC_DIR = ROOT / "static"

AGENT_MODES = ("gemini", "offline_fixture")
BACKENDS = ("local", "bigquery")


def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


@dataclass(frozen=True)
class Settings:
    query_backend: str   # "local" (DuckDB, dev) or "bigquery"
    gcp_project: str
    bq_dataset: str
    agent_mode: str      # "gemini" (Vertex AI) or "offline_fixture" (UI dev only, labelled in UI)
    gemini_model: str
    gemini_location: str
    gemini_temperature: float
    max_agent_turns: int
    gemini_max_retries: int       # retries of timed-out / 429 / 5xx Gemini calls, per investigation in total
    gemini_retry_backoff_s: float  # first retry waits this long, then x2 each retry
    step_timeout_s: float
    investigation_timeout_s: float
    fixture_step_delay_s: float
    rate_limit_per_hour: int
    global_rate_limit_per_hour: int  # all clients together: the real cost ceiling (BUG-003)
    trusted_proxy_hops: int  # X-Forwarded-For entries appended by trusted proxies (Cloud Run GFE = 1)
    max_concurrent_investigations: int  # public (non-presenter) investigations running at once (BUG-004)
    presenter_key: str  # secret; /?key=<it> marks the presenter's browser (BUG-004). Empty = feature off
    public_base_url: str  # absolute base URL used in QR codes (phones cannot reach "localhost")
    manual_baseline_min: str = ""     # Recap "Before" minutes; raw text, checked by manual_baseline()
    manual_baseline_source: str = ""  # where that number comes from (interview / measurement)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            query_backend=_env("QUERY_BACKEND", "local"),
            gcp_project=_env("GOOGLE_CLOUD_PROJECT", ""),
            bq_dataset=_env("BQ_DATASET", "linesleuth_demo"),
            agent_mode=_env("AGENT_MODE", "gemini"),
            gemini_model=_env("GEMINI_MODEL", "gemini-3-flash-preview"),
            gemini_location=_env("GOOGLE_CLOUD_LOCATION", "global"),
            gemini_temperature=float(_env("GEMINI_TEMPERATURE", "0")),
            max_agent_turns=int(_env("MAX_AGENT_TURNS", "10")),
            gemini_max_retries=int(_env("GEMINI_MAX_RETRIES", "2")),
            gemini_retry_backoff_s=float(_env("GEMINI_RETRY_BACKOFF_S", "2")),
            step_timeout_s=float(_env("STEP_TIMEOUT_S", "20")),
            investigation_timeout_s=float(_env("INVESTIGATION_TIMEOUT_S", "90")),
            fixture_step_delay_s=float(_env("FIXTURE_STEP_DELAY_S", "1.0")),
            rate_limit_per_hour=int(_env("RATE_LIMIT_PER_HOUR", "20")),
            global_rate_limit_per_hour=int(_env("GLOBAL_RATE_LIMIT_PER_HOUR", "60")),
            trusted_proxy_hops=int(_env("TRUSTED_PROXY_HOPS", "1")),
            max_concurrent_investigations=int(_env("MAX_CONCURRENT_INVESTIGATIONS", "3")),
            presenter_key=_env("PRESENTER_KEY", ""),
            public_base_url=_env("PUBLIC_BASE_URL", "").rstrip("/"),
            manual_baseline_min=_env("MANUAL_BASELINE_MIN", ""),
            manual_baseline_source=_env("MANUAL_BASELINE_SOURCE", ""),
        )

    def validate(self) -> None:
        if self.query_backend not in BACKENDS:
            raise ValueError(f"QUERY_BACKEND must be one of {BACKENDS}")
        if self.agent_mode not in AGENT_MODES:
            raise ValueError(f"AGENT_MODE must be one of {AGENT_MODES}")
        if self.query_backend == "bigquery" and not self.gcp_project:
            raise ValueError("QUERY_BACKEND=bigquery requires GOOGLE_CLOUD_PROJECT")
        if self.max_agent_turns < 1:
            raise ValueError("MAX_AGENT_TURNS must be >= 1")
        if not 0 <= self.gemini_max_retries <= 5:  # a cost ceiling, not a knob to turn up under load
            raise ValueError("GEMINI_MAX_RETRIES must be 0-5")
        if not 0 <= self.gemini_retry_backoff_s <= 30:
            raise ValueError("GEMINI_RETRY_BACKOFF_S must be 0-30 seconds")
        if self.trusted_proxy_hops < 0:
            raise ValueError("TRUSTED_PROXY_HOPS must be >= 0")
        if self.presenter_key and len(self.presenter_key) < 16:
            raise ValueError("PRESENTER_KEY must be at least 16 characters (or empty to disable)")


MANUAL_BASELINE_MAX_MIN = 480
MANUAL_BASELINE_SOURCE_MAX = 120


def manual_baseline(s: Settings) -> tuple[dict | None, str | None]:
    """The Recap "Before" value (ui-v2-spec 4.2): {minutes, source}, or None with the reason.

    Shown only when BOTH the minutes (1-480) and a source are set: a number without a source counts as
    not set. There is deliberately no default - the app never shows a manual baseline nobody measured.
    A bad value does not stop the server; the Recap just shows the neutral "Not yet measured" text."""
    raw, source = s.manual_baseline_min, s.manual_baseline_source
    if not raw and not source:
        return None, "MANUAL_BASELINE_MIN / MANUAL_BASELINE_SOURCE not set"
    if not raw or not source:
        return None, "MANUAL_BASELINE_MIN and MANUAL_BASELINE_SOURCE must both be set"
    try:
        minutes = float(raw)
    except ValueError:
        return None, f"MANUAL_BASELINE_MIN is not a number: {raw!r}"
    if not 1 <= minutes <= MANUAL_BASELINE_MAX_MIN:  # also rejects nan / inf
        return None, f"MANUAL_BASELINE_MIN must be 1-{MANUAL_BASELINE_MAX_MIN} minutes, got {raw!r}"
    if len(source) > MANUAL_BASELINE_SOURCE_MAX:
        return None, f"MANUAL_BASELINE_SOURCE is longer than {MANUAL_BASELINE_SOURCE_MAX} characters"
    return dict(minutes=int(minutes) if minutes.is_integer() else round(minutes, 1), source=source), None


def get_settings() -> Settings:
    s = Settings.from_env()
    s.validate()
    return s
