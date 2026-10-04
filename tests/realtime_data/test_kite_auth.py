from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.kite_auth import (
    KiteAuthenticationConfig,
    KiteSessionResponse,
    _exchange_request_token,
    _login_url,
    authenticate_locally,
)

pytestmark = pytest.mark.realtime_data


class _Transport:
    def __init__(self, response: KiteSessionResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, bytes, dict[str, str]]] = []

    def post(
        self,
        path: str,
        body: bytes,
        headers: dict[str, str],
        _timeout_seconds: float,
    ) -> KiteSessionResponse:
        self.calls.append((path, body, headers))
        return self.response


def _config() -> KiteAuthenticationConfig:
    fixture_auth = ("test-key", "test-secret")
    return KiteAuthenticationConfig(api_key=fixture_auth[0], api_secret=fixture_auth[1])


def test_local_login_exchanges_callback_token_and_writes_only_access_token(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("KITE_API_KEY=test-key\nKITE_API_SECRET=test-secret\n", encoding="utf-8")
    opened: list[str] = []
    transport = _Transport(
        KiteSessionResponse(
            200,
            json.dumps({"status": "success", "data": {"access_token": "daily-token"}}).encode(),
        )
    )

    result = authenticate_locally(
        config=_config(),
        dotenv_path=dotenv,
        open_browser=lambda url: opened.append(url) or True,
        request_token_receiver=lambda _state, _timeout: "one-time-request-token",
        transport=transport,
    )

    written = dotenv.read_text(encoding="utf-8")
    assert result.dotenv_path == dotenv
    assert opened and "api_key=test-key" in opened[0]
    assert "test-secret" not in opened[0]
    assert "KITE_ACCESS_TOKEN=daily-token" in written
    assert os.stat(dotenv).st_mode & 0o777 == 0o600
    assert transport.calls[0][0] == "/session/token"
    assert b"api_key=test-key" in transport.calls[0][1]
    assert b"one-time-request-token" in transport.calls[0][1]


def test_login_url_binds_the_local_callback_to_a_state_nonce() -> None:
    query = parse_qs(_login_url("test-key", "nonce").split("?", maxsplit=1)[1])
    assert query["v"] == ["3"]
    assert query["api_key"] == ["test-key"]
    assert parse_qs(query["redirect_params"][0]) == {"state": ["nonce"]}


def test_failed_token_exchange_never_echoes_provider_response_or_secret() -> None:
    transport = _Transport(KiteSessionResponse(403, b'{"status":"error","message":"test-secret"}'))
    with pytest.raises(RealTimeDataError, match="authentication was rejected") as exc:
        _exchange_request_token(_config(), "request-token", transport=transport)
    assert "test-secret" not in str(exc.value)
