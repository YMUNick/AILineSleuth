import os

# Tests never call Vertex AI unless explicitly asked (see test_gemini_live.py).
os.environ["AGENT_MODE"] = "offline_fixture"
os.environ["QUERY_BACKEND"] = "local"
os.environ["FIXTURE_STEP_DELAY_S"] = "0"
