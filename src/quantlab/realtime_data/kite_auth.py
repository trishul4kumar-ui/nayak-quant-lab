"""Local-only Kite session bootstrap for the read-only quote adapter."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
import webbrowser
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantlab.realtime_data.errors import RealTimeDataError

_API_BASE_URL = "https://api.kite.trade"
_LOGIN_URL = "https://kite.zerodha.com/connect/login"
_CALLBACK_HOST = "127.0.0.1"
_CALLBACK_PORT = 8765
_CALLBACK_PATH = "/kite/callback"


@dataclass(frozen=True)
class KiteSessionResponse:
    status: int
    body: bytes


class KiteSessionTransport(Protocol):
    """A narrowly-scoped transport for Kite's token exchange."""

    def post(
        self,
        path: str,
        body: bytes,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> KiteSessionResponse: ...


class UrllibKiteSessionTransport:
    """Fixed-host HTTPS transport for Kite's documented token endpoint."""

    def post(
        self,
        path: str,
        body: bytes,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> KiteSessionResponse:
        if path != "/session/token":
            raise RealTimeDataError("Kite session endpoint is not permitted")
        request = Request(
            f"{_API_BASE_URL}{path}",
            data=body,
            headers=dict(headers),
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed HTTPS host
                return KiteSessionResponse(status=int(response.status), body=response.read())
        except HTTPError as exc:
            return KiteSessionResponse(status=int(exc.code), body=exc.read())
        except URLError as exc:
            raise RealTimeDataError(
                f"Kite authentication network failure: {type(exc.reason).__name__}"
            ) from None


class KiteAuthenticationConfig(BaseSettings):
    """Secrets come only from the local environment or ignored .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    api_key: str = Field(default="", validation_alias=AliasChoices("KITE_API_KEY", "api_key"))
    api_secret: str = Field(
        default="", validation_alias=AliasChoices("KITE_API_SECRET", "api_secret")
    )
    timeout_seconds: float = Field(
        default=300.0, validation_alias="KITE_AUTH_TIMEOUT_SECONDS", gt=0
    )


@dataclass(frozen=True)
class KiteAuthenticationResult:
    """Safe completion record. It intentionally contains no credential values."""

    completed_at: datetime
    dotenv_path: Path
    callback_url: str
    note: str = "Kite access token saved locally for read-only quote polling."


def authenticate_locally(
    *,
    config: KiteAuthenticationConfig | None = None,
    dotenv_path: Path | None = None,
    open_browser: Callable[[str], bool] = webbrowser.open,
    transport: KiteSessionTransport | None = None,
    request_token_receiver: Callable[[str, float], str] | None = None,
) -> KiteAuthenticationResult:
    """Complete an explicit user login and atomically write KITE_ACCESS_TOKEN.

    This is separate from the quote adapter. It does not place orders, does not
    expose credential values in output, and does not enable live trading.
    """
    settings = config or KiteAuthenticationConfig()
    if not settings.api_key or not settings.api_secret:
        raise RealTimeDataError("KITE_API_KEY and KITE_API_SECRET must be configured locally")
    state = secrets.token_urlsafe(24)
    login_url = _login_url(settings.api_key, state)
    if request_token_receiver is not None:
        if not open_browser(login_url):
            raise RealTimeDataError("could not open the Kite login browser")
        request_token = request_token_receiver(state, settings.timeout_seconds)
    else:
        request_token = _open_and_receive(
            login_url,
            state,
            settings.timeout_seconds,
            open_browser=open_browser,
        )
    access_token = _exchange_request_token(
        settings,
        request_token,
        transport=transport or UrllibKiteSessionTransport(),
    )
    target = dotenv_path or Path.cwd() / ".env"
    _write_access_token(target, access_token)
    return KiteAuthenticationResult(
        completed_at=datetime.now(tz=UTC),
        dotenv_path=target,
        callback_url=f"http://{_CALLBACK_HOST}:{_CALLBACK_PORT}{_CALLBACK_PATH}",
    )


def _login_url(api_key: str, state: str) -> str:
    return (
        _LOGIN_URL
        + "?"
        + urlencode(
            {
                "v": "3",
                "api_key": api_key,
                "redirect_params": urlencode({"state": state}),
            }
        )
    )


def _open_and_receive(
    login_url: str,
    state: str,
    timeout_seconds: float,
    *,
    open_browser: Callable[[str], bool],
) -> str:
    server = HTTPServer((_CALLBACK_HOST, _CALLBACK_PORT), _callback_handler(state))
    server.timeout = timeout_seconds
    try:
        if not open_browser(login_url):
            raise RealTimeDataError("could not open the Kite login browser")
        server.handle_request()
        token = getattr(server, "request_token", "")
        if not token:
            raise RealTimeDataError("Kite login did not return a valid request token")
        return token
    finally:
        server.server_close()


def _callback_handler(expected_state: str) -> type[BaseHTTPRequestHandler]:
    class KiteCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            token = params.get("request_token", [""])[0]
            state = params.get("state", [""])[0]
            valid = (
                parsed.path == _CALLBACK_PATH
                and bool(token)
                and secrets.compare_digest(state, expected_state)
            )
            self.server.request_token = token if valid else ""  # type: ignore[attr-defined]
            self.send_response(200 if valid else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            page = (
                "<h1>QUANT LAB authentication completed.</h1><p>You may close this tab.</p>"
                if valid
                else "<h1>Authentication was rejected.</h1><p>Return to the terminal.</p>"
            )
            self.wfile.write(page.encode("utf-8"))

        def log_message(self, _format: str, *_args: object) -> None:
            """Do not emit callback query parameters containing the request token."""

    return KiteCallbackHandler


def _exchange_request_token(
    config: KiteAuthenticationConfig,
    request_token: str,
    *,
    transport: KiteSessionTransport,
) -> str:
    checksum = hashlib.sha256(
        f"{config.api_key}{request_token}{config.api_secret}".encode()
    ).hexdigest()
    body = urlencode(
        {
            "api_key": config.api_key,
            "request_token": request_token,
            "checksum": checksum,
        }
    ).encode("utf-8")
    response = transport.post(
        "/session/token",
        body,
        {"X-Kite-Version": "3", "Content-Type": "application/x-www-form-urlencoded"},
        config.timeout_seconds,
    )
    if response.status in {401, 403}:
        raise RealTimeDataError("Kite authentication was rejected")
    if response.status != 200:
        raise RealTimeDataError(f"Kite token exchange failed ({response.status})")
    try:
        payload = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RealTimeDataError("Kite token exchange returned invalid JSON") from None
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise RealTimeDataError("Kite token exchange was unsuccessful")
    data = payload.get("data")
    access_token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(access_token, str) or not access_token:
        raise RealTimeDataError("Kite token exchange did not return an access token")
    return access_token


def _write_access_token(path: Path, access_token: str) -> None:
    """Atomically update the local dotenv file with owner-only permissions."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    updated = False
    next_lines: list[str] = []
    for line in lines:
        if line.startswith("KITE_ACCESS_TOKEN="):
            next_lines.append(f"KITE_ACCESS_TOKEN={access_token}")
            updated = True
        else:
            next_lines.append(line)
    if not updated:
        next_lines.append(f"KITE_ACCESS_TOKEN={access_token}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".quantlab-kite-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write("\n".join(next_lines) + "\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
        raise
