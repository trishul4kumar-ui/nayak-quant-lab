"""Ops policy. Live remains false."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OpsPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    live_trading: bool = False
    max_restarts: int = 3
    require_verified_backup: bool = True
    note: str = "Ops policy cannot authorize live trading."


POLICY = OpsPolicy()
