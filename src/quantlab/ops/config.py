"""Versioned typed ops configuration. Safety-critical mutation is not silent."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from quantlab import __version__
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.ops.models import EnvironmentName


class OpsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    config_id: str = "ops-config-v1"
    config_version: str = "1"
    environment: EnvironmentName = EnvironmentName.RESEARCH
    software_version: str = __version__
    schema_version: str = "3.1.0"
    timestamp: datetime = datetime(2024, 1, 2, tzinfo=UTC)
    live_trading: bool = False
    max_restarts: int = 3
    disk_min_free_bytes: int = 10_000_000
    note: str = "Material changes invalidate dependent operational state."

    def config_hash(self) -> str:
        return sha256_bytes(self.model_dump_json().encode())


ACTIVE = OpsConfig()


def bind() -> OpsConfig:
    return ACTIVE


def detect_mutation(current: OpsConfig, observed_hash: str) -> bool:
    return current.config_hash() != observed_hash
