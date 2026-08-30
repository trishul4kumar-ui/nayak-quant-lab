"""Process configuration. Live trading is off unless every gate passes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LiveSafetyGates(BaseSettings):
    """Every flag must be true for live orders. Defaults fail closed."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    live_trading: bool = False
    live_trading_enabled: bool = False
    broker_connected: bool = False
    risk_engine_healthy: bool = True
    strategy_approved: bool = False
    model_approved: bool = False
    data_healthy: bool = True
    session_valid: bool = False
    shadow_mode: bool = True
    broker_routing_enabled: bool = False
    live_order_submission_enabled: bool = False
    execution_gateway_armed: bool = False
    live_release_authorized: bool = False
    broker_write_enabled: bool = False

    def all_pass(self) -> bool:
        return all(
            (
                self.live_trading,
                self.live_trading_enabled,
                self.broker_connected,
                self.risk_engine_healthy,
                self.strategy_approved,
                self.model_approved,
                self.data_healthy,
                self.session_valid,
            )
        )

    def blocking_reasons(self) -> list[str]:
        names = (
            "live_trading",
            "live_trading_enabled",
            "broker_connected",
            "risk_engine_healthy",
            "strategy_approved",
            "model_approved",
            "data_healthy",
            "session_valid",
        )
        return [name for name in names if not getattr(self, name)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    quant_lab_env: str = "research"
    quant_lab_mode: str = "research"
    log_level: str = "INFO"
    tz: str = "Asia/Kolkata"
    experiment_ledger_path: Path = Field(default=Path("experiments/ledger.jsonl"))
    data_dir: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("QUANT_LAB_DATA_DIR", "data_dir"),
    )
    live: LiveSafetyGates = Field(default_factory=LiveSafetyGates)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
