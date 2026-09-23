"""Vertex AI Gemini function-calling loop (google-genai SDK).

The model only sees the five fixed query functions plus submit_conclusion. Automatic function calling
is disabled: we execute each call ourselves, so every call is validated, logged and turned into a card.
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from app.agent.prompt import MAX_QUERY_CALLS, SUBMIT_CONCLUSION, SYSTEM_PROMPT, incident_prompt
from app.config import Settings
from app.queries.functions import FUNCTION_DECLARATIONS

log = logging.getLogger("linesleuth.agent")

_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gemini")
_client = None


class AgentUnavailable(RuntimeError):
    pass


def _get_client(settings: Settings):
    global _client
    if _client is None:
        from google import genai

        if not settings.gcp_project:
            raise AgentUnavailable("GOOGLE_CLOUD_PROJECT is not set; cannot call Vertex AI Gemini")
        _client = genai.Client(vertexai=True, project=settings.gcp_project, location=settings.gemini_location)
    return _client


def _config(settings: Settings, force_submit: bool):
    from google.genai import types

    decls = [types.FunctionDeclaration(name=d["name"], description=d["description"],
                                       parameters_json_schema=d["parameters"])
             for d in FUNCTION_DECLARATIONS + [SUBMIT_CONCLUSION]]
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=settings.gemini_temperature,
        tools=[types.Tool(function_declarations=decls)],
        tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(
            mode="ANY",  # the model must always answer with a function call
            allowed_function_names=["submit_conclusion"] if force_submit else None)),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def run_gemini(ctx, settings: Settings) -> dict:
    """Returns the raw submit_conclusion args. Raises on failure (never fabricates a result)."""
    from google.genai import types

    client = _get_client(settings)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=incident_prompt(ctx.scenario))])]
    query_calls = 0
    for turn in range(settings.max_agent_turns):
        ctx.check()
        force = query_calls >= MAX_QUERY_CALLS
        future = _pool.submit(client.models.generate_content, model=settings.gemini_model,
                              contents=contents, config=_config(settings, force))
        try:
            resp = future.result(timeout=settings.step_timeout_s)
        except FutureTimeout:
            raise TimeoutError(f"Gemini did not answer within {settings.step_timeout_s}s (turn {turn + 1})")
        calls = resp.function_calls or []
        if not calls:
            raise RuntimeError("Gemini returned no function call")
        contents.append(resp.candidates[0].content)  # keeps thought signatures intact
        log.info(json.dumps({"event": "gemini_turn", "investigation_id": ctx.investigation_id, "turn": turn + 1,
                             "calls": [{"name": c.name, "args": dict(c.args or {})} for c in calls]}))
        conclusion = None
        parts = []
        for call in calls:
            args = dict(call.args or {})
            if call.name == "submit_conclusion":
                conclusion = args
                continue
            query_calls += 1
            payload = ctx.call_tool(call.name, args)
            parts.append(types.Part.from_function_response(name=call.name, response=payload))
        if conclusion is not None:
            return conclusion
        contents.append(types.Content(role="user", parts=parts))
    raise RuntimeError(f"No conclusion after {settings.max_agent_turns} turns")
