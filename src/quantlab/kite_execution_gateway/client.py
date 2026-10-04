"""Desktop client for the separately deployed HTTPS manual-execution gateway."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from quantlab.kite_execution_gateway.models import (
    ManualLimitOrder,
    ManualOrderPreview,
    ManualOrderSubmission,
    ManualSubmissionResult,
)


class RemoteGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class RemoteGatewayConfig:
    url: str
    client_token: str

    @classmethod
    def from_environment(cls) -> RemoteGatewayConfig:
        config = cls(
            url=os.getenv("KITE_EXECUTION_GATEWAY_URL", "").rstrip("/"),
            client_token=os.getenv("KITE_EXECUTION_GATEWAY_CLIENT_TOKEN", ""),
        )
        if not config.url or not config.client_token:
            raise RemoteGatewayError("secure Kite execution gateway is not configured")
        if not config.url.startswith("https://"):
            raise RemoteGatewayError("secure Kite execution gateway must use HTTPS")
        return config


class RemoteGatewayClient:
    def __init__(self, config: RemoteGatewayConfig | None = None) -> None:
        self._config = config or RemoteGatewayConfig.from_environment()

    def health(self) -> dict[str, object]:
        return self._request("GET", "/v1/health")

    def login_url(self) -> str:
        value = self._request("POST", "/v1/kite/login-url")
        url = value.get("login_url")
        if not isinstance(url, str) or not url.startswith("https://kite.zerodha.com/"):
            raise RemoteGatewayError("gateway returned an invalid Kite login URL")
        return url

    def preview(self, order: ManualLimitOrder) -> ManualOrderPreview:
        return ManualOrderPreview.model_validate(
            self._request("POST", "/v1/orders/preview", order.model_dump(mode="json"))
        )

    def submit(self, request: ManualOrderSubmission) -> ManualSubmissionResult:
        return ManualSubmissionResult.model_validate(
            self._request("POST", "/v1/orders", request.model_dump(mode="json"))
        )

    def _request(
        self, method: str, path: str, payload: dict[str, object] | None = None
    ) -> dict[str, object]:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            f"{self._config.url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._config.client_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:  # noqa: S310 - HTTPS config enforced
                raw = response.read()
        except HTTPError as exc:
            raw = exc.read()
        except URLError as exc:
            raise RemoteGatewayError(
                f"execution gateway unavailable: {type(exc.reason).__name__}"
            ) from None
        try:
            decoded: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RemoteGatewayError("execution gateway returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise RemoteGatewayError("execution gateway returned malformed data")
        if error := decoded.get("error"):
            raise RemoteGatewayError(str(error))
        return decoded
