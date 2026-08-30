"""Typed, hashable research backtest identity. Extends, does not replace, BacktestConfig."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, Field


def config_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class ResearchBacktestSpec(BaseModel):
    schema_version: str = "1"
    dataset_id: str
    dataset_version: str
    snapshot_id: str
    strategy_name: str
    strategy_version: str
    feature_versions: dict[str, str] = Field(default_factory=dict)
    lookback: int = 20
    top_n: int = 2
    cost_bps: float = 10.0
    slippage_bps: float = 0.0
    slippage_model: str = "none"
    fill_policy: str = "next_bar"
    initial_equity: float = 1_000_000.0
    seed: int = 0
    data_kind: str = "synthetic"
    universe: list[str] = Field(default_factory=list)
    label_horizon_sessions: int = 1
    portfolio_rule: str = "equal_weight_top_n"
    rebalance_frequency: str = "1d"

    def identity(self) -> str:
        return config_hash(self.model_dump(mode="json"))
