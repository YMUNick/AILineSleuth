"""Live Vertex AI Gemini check. Skipped unless RUN_GEMINI_TESTS=1 and GCP credentials are configured.

    RUN_GEMINI_TESTS=1 AGENT_MODE=gemini GOOGLE_CLOUD_PROJECT=... pytest tests/test_gemini_live.py
For the full 10+2 regression set use scripts/run_regression.py.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("RUN_GEMINI_TESTS") != "1", reason="set RUN_GEMINI_TESTS=1 to call Vertex AI")


def test_main_scenario_with_gemini(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "gemini")
    from app.config import get_settings
    from app.investigations import InvestigationManager
    from app.queries.backends import make_backend

    s = get_settings()
    mgr = InvestigationManager(s, make_backend(s))
    inv = mgr.start("R01", background=False)
    assert inv.status == "root_cause", inv.error
    assert inv.conclusion["root_cause_key"] == "cv_valve_stuck_closed"
