"""Configurable expression grammar. Unrestricted symbolic explosion is not permitted."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.discovery.operators import BINARY_OPS, CS_OPS, ROLLING_OPS, UNARY_OPS
from quantlab.discovery.primitives import allowed_feature_ids


class GrammarSpec(BaseModel):
    version: str = "1"
    max_depth: int = 4
    max_nodes: int = 12
    max_features: int = 4
    max_constants: int = 2
    max_nested_transforms: int = 4
    allowed_features: tuple[str, ...] = Field(default_factory=allowed_feature_ids)
    allowed_windows: tuple[int, ...] = (5, 10, 20)
    allowed_unary: tuple[str, ...] = UNARY_OPS + CS_OPS
    allowed_binary: tuple[str, ...] = BINARY_OPS
    allowed_rolling: tuple[str, ...] = ROLLING_OPS

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))
