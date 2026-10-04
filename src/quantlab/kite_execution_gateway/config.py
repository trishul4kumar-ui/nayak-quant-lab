"""Server-only configuration. No desktop setting accepts Kite's API secret."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KiteExecutionGatewayConfig:
    api_key: str
    api_secret: str
    desktop_client_token: str
    operator_totp_secret: str
    expected_account_fingerprint: str
    allowed_symbols: frozenset[str]
    max_notional: float
    redirect_url: str
    journal_path: Path
    execution_enabled: bool = False

    @classmethod
    def from_environment(cls) -> KiteExecutionGatewayConfig:
        symbols = frozenset(
            item.strip().upper()
            for item in os.getenv("KITE_EXECUTION_ALLOWED_SYMBOLS", "").split(",")
            if item.strip()
        )
        config = cls(
            api_key=os.getenv("KITE_API_KEY", ""),
            api_secret=os.getenv("KITE_API_SECRET", ""),
            desktop_client_token=os.getenv("KITE_EXECUTION_DESKTOP_TOKEN", ""),
            operator_totp_secret=os.getenv("KITE_EXECUTION_TOTP_SECRET", ""),
            expected_account_fingerprint=os.getenv("KITE_EXECUTION_ACCOUNT_FINGERPRINT", ""),
            allowed_symbols=symbols,
            max_notional=float(os.getenv("KITE_EXECUTION_MAX_NOTIONAL", "0")),
            redirect_url=os.getenv("KITE_EXECUTION_REDIRECT_URL", ""),
            journal_path=Path(os.getenv("KITE_EXECUTION_JOURNAL", "./execution-gateway.sqlite")),
            execution_enabled=os.getenv("KITE_EXECUTION_ENABLED", "false").lower() == "true",
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not all(
            (
                self.api_key,
                self.api_secret,
                self.desktop_client_token,
                self.operator_totp_secret,
                self.expected_account_fingerprint,
                self.redirect_url,
            )
        ):
            raise ValueError("execution gateway server configuration is incomplete")
        if not self.redirect_url.startswith("https://"):
            raise ValueError("execution gateway redirect URL must use HTTPS")
        if not self.allowed_symbols:
            raise ValueError("execution gateway requires an explicit symbol allowlist")
        if self.max_notional <= 0:
            raise ValueError("execution gateway requires a positive max notional")
