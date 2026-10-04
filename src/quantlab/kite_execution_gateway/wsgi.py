"""Small WSGI surface for deployment behind an HTTPS reverse proxy.

It has no CORS headers, no browser session, and no endpoint that returns Kite
credentials.  The callback is intentionally the sole unauthenticated route.
"""

from __future__ import annotations

import hmac
import json
from collections.abc import Callable
from functools import lru_cache
from typing import Any
from urllib.parse import parse_qs

from quantlab.kite_execution_gateway.config import KiteExecutionGatewayConfig
from quantlab.kite_execution_gateway.models import ManualLimitOrder, ManualOrderSubmission
from quantlab.kite_execution_gateway.service import GatewayError, SecureKiteExecutionGateway

StartResponse = Callable[[str, list[tuple[str, str]]], Any]


class GatewayWsgiApp:
    def __init__(self, gateway: SecureKiteExecutionGateway, *, desktop_client_token: str) -> None:
        self._gateway = gateway
        self._desktop_client_token = desktop_client_token

    def __call__(self, environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET"))
        path = str(environ.get("PATH_INFO", ""))
        try:
            if path == "/v1/kite/callback" and method == "GET":
                query = parse_qs(str(environ.get("QUERY_STRING", "")))
                token = query.get("request_token", [""])[0]
                self._gateway.authenticate_request_token(token)
                return self._json(start_response, "200 OK", {"authenticated": True})
            self._require_client(environ)
            if path == "/v1/health" and method == "GET":
                return self._json(
                    start_response,
                    "200 OK",
                    {"ready": self._gateway.ready(), "execution_enabled": self._gateway.ready()},
                )
            if path == "/v1/kite/login-url" and method == "POST":
                return self._json(
                    start_response, "200 OK", {"login_url": self._gateway.login_url()}
                )
            if path == "/v1/orders/preview" and method == "POST":
                order = ManualLimitOrder.model_validate(self._body(environ))
                return self._json(
                    start_response, "200 OK", self._gateway.preview(order).model_dump(mode="json")
                )
            if path == "/v1/orders" and method == "POST":
                item = ManualOrderSubmission.model_validate(self._body(environ))
                return self._json(
                    start_response, "200 OK", self._gateway.submit(item).model_dump(mode="json")
                )
            return self._json(start_response, "404 Not Found", {"error": "unknown endpoint"})
        except GatewayError as exc:
            return self._json(start_response, "409 Conflict", {"error": str(exc)})
        except (ValueError, json.JSONDecodeError):
            return self._json(start_response, "400 Bad Request", {"error": "malformed request"})
        except PermissionError:
            return self._json(start_response, "401 Unauthorized", {"error": "unauthorized"})

    def _require_client(self, environ: dict[str, Any]) -> None:
        value = str(environ.get("HTTP_AUTHORIZATION", ""))
        prefix = "Bearer "
        if not value.startswith(prefix) or not hmac.compare_digest(
            value.removeprefix(prefix), self._desktop_client_token
        ):
            raise PermissionError

    @staticmethod
    def _body(environ: dict[str, Any]) -> dict[str, object]:
        raw_length = str(environ.get("CONTENT_LENGTH", "0"))
        length = int(raw_length) if raw_length.isdigit() else 0
        if length <= 0 or length > 16_384:
            raise ValueError("body size")
        stream = environ.get("wsgi.input")
        if stream is None:
            raise ValueError("body missing")
        value = json.loads(stream.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    @staticmethod
    def _json(
        start_response: StartResponse, status: str, payload: dict[str, object]
    ) -> list[bytes]:
        body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [body]


def application(environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
    """WSGI entrypoint: ``gunicorn quantlab.kite_execution_gateway.wsgi:application``."""
    return _configured_app()(environ, start_response)


@lru_cache(maxsize=1)
def _configured_app() -> GatewayWsgiApp:
    config = KiteExecutionGatewayConfig.from_environment()
    return GatewayWsgiApp(
        SecureKiteExecutionGateway(config), desktop_client_token=config.desktop_client_token
    )
