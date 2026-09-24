"""Vertex AI Gemini function-calling loop (google-genai SDK).

The model only sees the five fixed query functions plus submit_conclusion. Automatic function calling
is disabled: we execute each call ourselves, so every call is validated, logged and turned into a card.

Retries (Quinn's risk, 9/24 meeting): a Gemini call that times out, gets 429 or a 5xx is retried with
exponential backoff, at most GEMINI_MAX_RETRIES times per investigation in total. Past that the investigation
fails. So one investigation makes at most MAX_AGENT_TURNS + GEMINI_MAX_RETRIES Gemini calls.
Token usage (ENH-002): every response's usage_metadata is logged per turn and added to the investigation.
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

RETRY_HTTP_CODES = (429, 500, 502, 503, 504)  # rate limited / transient server errors
USAGE_KEYS = ("turns", "retries", "input_tokens", "output_tokens", "thinking_tokens", "cached_tokens",
              "total_tokens", "turns_without_usage")


class AgentUnavailable(RuntimeError):
    pass


def _get_client(settings: Settings):
    global _client
    if _client is None:
        from google import genai
        from google.genai import types

        if not settings.gcp_project:
            raise AgentUnavailable("GOOGLE_CLOUD_PROJECT is not set; cannot call Vertex AI Gemini")
        # Retries are ours (GEMINI_MAX_RETRIES), so the SDK must never retry on its own (attempts=1). The HTTP
        # request is abandoned a little after STEP_TIMEOUT_S so a hung call does not hold a pool thread forever.
        _client = genai.Client(vertexai=True, project=settings.gcp_project, location=settings.gemini_location,
                               http_options=types.HttpOptions(timeout=int((settings.step_timeout_s + 5) * 1000),
                                                              retry_options=types.HttpRetryOptions(attempts=1)))
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


# ---------------------------------------------------------------- token usage (ENH-002)
def new_usage(agent_mode: str) -> dict:
    """Per-investigation Gemini usage. OFFLINE FIXTURE never calls Gemini: every count is None (not applicable),
    never a made-up 0, so nobody mistakes a fixture run for a cost measurement."""
    if agent_mode != "gemini":
        return dict(applicable=False, note="OFFLINE FIXTURE: no Gemini call, token counts not applicable",
                    **{k: None for k in USAGE_KEYS})
    return dict(applicable=True, note=None, **{k: 0 for k in USAGE_KEYS})


def turn_usage(resp) -> dict | None:
    """Token counts of one response, or None if the API did not report usage_metadata.
    input = prompt tokens (includes cached_tokens); output = answer tokens; thinking = thought tokens
    (billed at the output price)."""
    m = getattr(resp, "usage_metadata", None)
    if m is None:
        return None

    def n(name: str) -> int:
        return int(getattr(m, name, None) or 0)  # the API omits a count that is zero (e.g. no thinking)

    return dict(input_tokens=n("prompt_token_count"), output_tokens=n("candidates_token_count"),
                thinking_tokens=n("thoughts_token_count"), cached_tokens=n("cached_content_token_count"),
                total_tokens=n("total_token_count"))


# ---------------------------------------------------------------- retries
def _retry_reason(e: BaseException) -> str | None:
    """Why a failed Gemini call may be retried, or None if it must not be (bad request, permission, ...)."""
    if isinstance(e, (FutureTimeout, TimeoutError)):
        return "timeout"
    from google.genai import errors

    if isinstance(e, errors.APIError) and e.code in RETRY_HTTP_CODES:
        return "rate limited (429)" if e.code == 429 else f"server error ({e.code})"
    import httpx  # dependency of google-genai: connection reset / HTTP-level timeout

    if isinstance(e, httpx.TransportError):
        return f"network error ({type(e).__name__})"
    return None


def _generate(client, ctx, settings: Settings, contents, force: bool, turn: int, retries: list[int]):
    """One Gemini call with bounded retries. retries[0] = retries used so far in this investigation."""
    while True:
        ctx.check()
        future = _pool.submit(client.models.generate_content, model=settings.gemini_model,
                              contents=contents, config=_config(settings, force))
        try:
            return future.result(timeout=settings.step_timeout_s)
        except Exception as e:  # noqa: BLE001 - classified below; anything not retryable is re-raised
            reason = _retry_reason(e)
            if reason is None:
                raise
            if reason == "timeout":
                reason = f"timed out after {settings.step_timeout_s:g}s"
            if retries[0] >= settings.gemini_max_retries:
                raise AgentUnavailable(
                    f"Gemini {reason} on turn {turn}; gave up after {retries[0]} "
                    f"{'retry' if retries[0] == 1 else 'retries'} (GEMINI_MAX_RETRIES={settings.gemini_max_retries})"
                ) from (None if isinstance(e, FutureTimeout) else e)
            delay = settings.gemini_retry_backoff_s * (2 ** retries[0])
            retries[0] += 1
            ctx.add_usage(retries=1)
            log.warning(json.dumps({"event": "gemini_retry", "investigation_id": ctx.investigation_id,
                                    "turn": turn, "reason": reason, "retry": retries[0],
                                    "max_retries": settings.gemini_max_retries, "backoff_s": delay}))
            ctx.wait(delay)  # returns early and raises on cancel / investigation deadline


def run_gemini(ctx, settings: Settings) -> dict:
    """Returns the raw submit_conclusion args. Raises on failure (never fabricates a result)."""
    from google.genai import types

    client = _get_client(settings)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=incident_prompt(ctx.scenario))])]
    query_calls = 0
    retries = [0]
    for turn in range(settings.max_agent_turns):
        ctx.check()
        # force submit_conclusion after MAX_QUERY_CALLS queries, and on the last allowed turn
        force = query_calls >= MAX_QUERY_CALLS or turn == settings.max_agent_turns - 1
        resp = _generate(client, ctx, settings, contents, force, turn + 1, retries)
        usage = turn_usage(resp)
        ctx.add_usage(turns=1, **(usage or {"turns_without_usage": 1}))
        calls = resp.function_calls or []
        log.info(json.dumps({"event": "gemini_turn", "investigation_id": ctx.investigation_id, "turn": turn + 1,
                             "model": settings.gemini_model, "forced_submit": force, "usage": usage,
                             "calls": [{"name": c.name, "args": dict(c.args or {})} for c in calls]}, default=str))
        if not calls:
            raise RuntimeError("Gemini returned no function call")
        contents.append(resp.candidates[0].content)  # keeps thought signatures intact
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
