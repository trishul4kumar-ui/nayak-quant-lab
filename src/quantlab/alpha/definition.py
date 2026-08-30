"""Alpha is a hypothesis-bound transformation of features, not a feature and not a strategy."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AlphaLifecycle(StrEnum):
    DRAFT = "draft"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    FRAGILE = "fragile"
    CONTAMINATED = "contaminated"
    DEPRECATED = "deprecated"


class AlphaDefinition(BaseModel):
    alpha_id: str
    version: str
    name: str
    hypothesis_id: str
    input_features: list[str]
    transformation: str
    expected_direction: str
    horizon: int
    universe: list[str] = Field(default_factory=list)
    normalization: str = "rank"
    mathematical_definition: str
    implementation_version: str = "0.6.0"
    family_id: str = ""
    lineage: dict[str, str] = Field(default_factory=dict)
    lifecycle: AlphaLifecycle = AlphaLifecycle.TESTING
    notes: str = ""


def seed_alphas() -> list[AlphaDefinition]:
    return [
        AlphaDefinition(
            alpha_id="rank_momentum_5",
            version="1",
            name="Rank of 5-session momentum",
            hypothesis_id="cs_momentum_persists",
            input_features=["momentum_5"],
            transformation="rank",
            expected_direction="long_high",
            horizon=1,
            mathematical_definition="rank(momentum_5) over Universe(T)",
            family_id="cs_momentum",
            lineage={"feature": "momentum_5@1"},
        ),
        AlphaDefinition(
            alpha_id="rank_momentum_20",
            version="1",
            name="Rank of 20-session momentum",
            hypothesis_id="cs_momentum_persists",
            input_features=["momentum_20"],
            transformation="rank",
            expected_direction="long_high",
            horizon=1,
            mathematical_definition="rank(momentum_20) over Universe(T)",
            family_id="cs_momentum",
            lineage={"feature": "momentum_20@1"},
        ),
        AlphaDefinition(
            alpha_id="zscore_momentum_20",
            version="1",
            name="Z-score of 20-session momentum",
            hypothesis_id="cs_momentum_persists",
            input_features=["momentum_20"],
            transformation="zscore",
            expected_direction="long_high",
            horizon=1,
            mathematical_definition="zscore_cs(momentum_20) over Universe(T)",
            family_id="cs_momentum",
            lineage={"feature": "momentum_20@1"},
        ),
        AlphaDefinition(
            alpha_id="momentum_minus_vol",
            version="1",
            name="Momentum minus volatility",
            hypothesis_id="momentum_net_of_vol",
            input_features=["momentum_20", "rolling_std_20"],
            transformation="zscore_sub",
            expected_direction="long_high",
            horizon=1,
            mathematical_definition="zscore(momentum_20)-zscore(rolling_std_20)",
            family_id="momentum_vol",
            lineage={"features": "momentum_20@1,rolling_std_20@1"},
            notes="Combination weights are explicit (1, -1). Not test-set optimized.",
        ),
    ]


_ALPHAS = {item.alpha_id: item for item in seed_alphas()}


def get_alpha(alpha_id: str) -> AlphaDefinition:
    if alpha_id not in _ALPHAS:
        raise KeyError(f"unknown alpha {alpha_id}")
    return _ALPHAS[alpha_id]


def list_alphas() -> list[AlphaDefinition]:
    return list(_ALPHAS.values())
