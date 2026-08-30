"""Never log, hash, or persist raw credentials."""

from __future__ import annotations

from quantlab.broker_gateway.errors import BrokerGatewayError
from quantlab.data.fabric.checksums import sha256_bytes

_REDACTED = "***REDACTED***"
_FORBIDDEN = ("api_key", "api_secret", "access_token", "password", "totp_secret", "secret")


def redact(value: str | None = None) -> str:
    del value
    return _REDACTED


def account_id_hash(account_id: str) -> str:
    return sha256_bytes(account_id.encode())[:16]


def assert_no_secrets(payload: str) -> None:
    lowered = payload.lower()
    for token in _FORBIDDEN:
        if token in lowered and "redacted" not in lowered:
            raise BrokerGatewayError("credential exposure blocked")
