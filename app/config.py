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
    step_timeout_s: float
    investigation_timeout_s: float
    fixture_step_delay_s: float
    rate_limit_per_hour: int
    global_rate_limit_per_hour: int  # all clients together: the real cost ceiling (BUG-003)
    trusted_proxy_hops: int  # X-Forwarded-For entries appended by trusted proxies (Cloud Run GFE = 1)
    max_concurrent_investigations: int  # public (non-presenter) investigations running at once (BUG-004)
    presenter_key: str  # secret; /?key=<it> marks the presenter's browser (BUG-004). Empty = feature off
    public_base_url: str  # absolute base URL used in QR codes (phones cannot reach "localhost")

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
            step_timeout_s=float(_env("STEP_TIMEOUT_S", "20")),
            investigation_timeout_s=float(_env("INVESTIGATION_TIMEOUT_S", "90")),
            fixture_step_delay_s=float(_env("FIXTURE_STEP_DELAY_S", "1.0")),
            rate_limit_per_hour=int(_env("RATE_LIMIT_PER_HOUR", "20")),
            global_rate_limit_per_hour=int(_env("GLOBAL_RATE_LIMIT_PER_HOUR", "60")),
            trusted_proxy_hops=int(_env("TRUSTED_PROXY_HOPS", "1")),
            max_concurrent_investigations=int(_env("MAX_CONCURRENT_INVESTIGATIONS", "3")),
            presenter_key=_env("PRESENTER_KEY", ""),
            public_base_url=_env("PUBLIC_BASE_URL", "").rstrip("/"),
        )

    def validate(self) -> None:
        if self.query_backend not in BACKENDS:
            raise ValueError(f"QUERY_BACKEND must be one of {BACKENDS}")
        if self.agent_mode not in AGENT_MODES:
            raise ValueError(f"AGENT_MODE must be one of {AGENT_MODES}")
        if self.query_backend == "bigquery" and not self.gcp_project:
            raise ValueError("QUERY_BACKEND=bigquery requires GOOGLE_CLOUD_PROJECT")
        if self.trusted_proxy_hops < 0:
            raise ValueError("TRUSTED_PROXY_HOPS must be >= 0")
        if self.presenter_key and len(self.presenter_key) < 16:
            raise ValueError("PRESENTER_KEY must be at least 16 characters (or empty to disable)")


def get_settings() -> Settings:
    s = Settings.from_env()
    s.validate()
    return s
