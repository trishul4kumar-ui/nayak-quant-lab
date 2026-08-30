"""Versioned feature definitions. Distinct from domain.research.Feature (a value)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash


class FeatureFamily(StrEnum):
    PRICE = "price"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    CROSS_SECTIONAL = "cross_sectional"
    MARKET_STRUCTURE = "market_structure"
    LIQUIDITY = "liquidity"
    SEASONALITY = "seasonality"
    REGIME = "regime"
    RELATIVE = "relative"
    STATISTICAL = "statistical"


class FeatureLifecycle(StrEnum):
    """Research lifecycle. Not fabric FeatureStatus and not a profitability claim."""

    DRAFT = "draft"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    FRAGILE = "fragile"
    REDUNDANT = "redundant"
    CONTAMINATED = "contaminated"
    DEPRECATED = "deprecated"


class MissingValuePolicy(StrEnum):
    DROP = "drop"
    FORWARD_FILL = "forward_fill"
    ZERO = "zero"
    NOT_AVAILABLE = "not_available"


class NormalizationMethod(StrEnum):
    NONE = "none"
    RANK = "rank"
    PERCENTILE_RANK = "percentile_rank"
    ZSCORE_CS = "zscore_cs"
    ROBUST_ZSCORE_CS = "robust_zscore_cs"
    WINSORIZED_ZSCORE_CS = "winsorized_zscore_cs"
    ZSCORE_TS = "zscore_ts"


class FeatureOperator(StrEnum):
    TRAILING_RETURN = "trailing_return"
    ROLLING_MEAN = "rolling_mean"
    ROLLING_STD = "rolling_std"
    ZSCORE_TS = "zscore_ts"
    HIGH_LOW_RANGE = "high_low_range"
    CLOSE_TO_HIGH = "close_to_high"
    CLOSE_TO_LOW = "close_to_low"
    LAST_VOLUME = "last_volume"
    VOLUME_CHANGE = "volume_change"
    VOLUME_ZSCORE = "volume_zscore"
    DISTANCE_FROM_MEAN = "distance_from_mean"
    DOLLAR_TURNOVER_RATIO = "dollar_turnover_ratio"
    ROLLING_BETA = "rolling_beta"
    NOT_IMPLEMENTED = "not_implemented"


class FeatureDefinition(BaseModel):
    feature_id: str
    version: str
    name: str
    mathematical_definition: str
    inputs: list[str]
    lookback: int
    operator: FeatureOperator
    family: FeatureFamily
    family_id: str
    frequency: str = "1d"
    timestamp_semantics: str = "available_time <= decision_time; trailing windows only"
    universe_requirements: str = "Universe(T) at decision_time"
    normalization: NormalizationMethod = NormalizationMethod.NONE
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.NOT_AVAILABLE
    winsorization: str = "none"
    price_field: str = "close"
    implementation_version: str = "0.6.0"
    lifecycle: FeatureLifecycle = FeatureLifecycle.TESTING
    params: dict[str, int | float | str] = Field(default_factory=dict)
    provenance: str = ""
    notes: str = ""

    def identity_payload(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "version": self.version,
            "mathematical_definition": self.mathematical_definition,
            "inputs": self.inputs,
            "lookback": self.lookback,
            "operator": self.operator.value,
            "normalization": self.normalization.value,
            "missing_value_policy": self.missing_value_policy.value,
            "winsorization": self.winsorization,
            "price_field": self.price_field,
            "params": self.params,
            "frequency": self.frequency,
            "implementation_version": self.implementation_version,
        }

    def identity_hash(self) -> str:
        return config_hash(self.identity_payload())
