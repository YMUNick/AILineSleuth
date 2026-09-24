import os
import socket
from pathlib import Path

import pytest

# Pin every setting to the .env.example defaults so a developer's local .env (loaded by
# app.config via load_dotenv, which never overrides existing variables) cannot change test
# expectations. Live Gemini runs keep the local .env for the project and model.
if os.environ.get("RUN_GEMINI_TESTS") != "1":
    for _line in (Path(__file__).resolve().parents[1] / ".env.example").read_text(encoding="utf-8").splitlines():
        _key, _sep, _value = _line.partition("=")
        if _sep and _key.strip() and not _key.lstrip().startswith("#"):
            os.environ[_key.strip()] = _value.strip()

# Tests never call Vertex AI unless explicitly asked (see test_gemini_live.py).
os.environ["AGENT_MODE"] = "offline_fixture"
os.environ["QUERY_BACKEND"] = "local"
os.environ["FIXTURE_STEP_DELAY_S"] = "0"

_LOOPBACK = ("localhost", "127.0.0.1", "::1")


def _is_loopback(host) -> bool:
    return host is None or (isinstance(host, str) and (host in _LOOPBACK or host.startswith("127.")))


@pytest.fixture(autouse=True, scope="session")
def _offline():
    """The suite must pass with no network (9/24 meeting): any non-loopback connection or DNS lookup raises.
    Loopback stays open (the Windows event loop and TestClient use it). RUN_GEMINI_TESTS=1 turns this off."""
    if os.environ.get("RUN_GEMINI_TESTS") == "1":
        yield
        return
    real_connect, real_connect_ex, real_getaddrinfo = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo

    def blocked(address):
        return OSError(f"network access blocked in tests: {address!r}")

    def connect(self, address):
        if isinstance(address, tuple) and not _is_loopback(address[0]):
            raise blocked(address)
        return real_connect(self, address)

    def connect_ex(self, address):
        if isinstance(address, tuple) and not _is_loopback(address[0]):
            raise blocked(address)
        return real_connect_ex(self, address)

    def getaddrinfo(host, *args, **kwargs):
        if not _is_loopback(host):
            raise blocked(host)
        return real_getaddrinfo(host, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, "connect", connect)
        mp.setattr(socket.socket, "connect_ex", connect_ex)
        mp.setattr(socket, "getaddrinfo", getaddrinfo)
        yield
