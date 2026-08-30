"""Versioned factor definitions. Distinct from domain.research.Factor (a named stub)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.features.definition import MissingValuePolicy, NormalizationMethod


class FactorCategory(StrEnum):
    MARKET = "market"
    STYLE = "style"
    SECTOR = "sector"
    MACRO = "macro"
    LIQUIDITY = "liquidity"
    VOLATILITY = "volatility"
    MICROSTRUCTURE = "microstructure"
    CUSTOM = "custom"


class FactorLifecycle(StrEnum):
    DRAFT = "draft"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    FRAGILE = "fragile"
    CONTAMINATED = "contaminated"
    DEPRECATED = "deprecated"
    NOT_TESTED = "not_tested"


class FactorSource(StrEnum):
    FEATURE = "feature"
    EQUAL_WEIGHT_MARKET_BETA = "equal_weight_market_beta"
    RESIDUAL = "residual"
    NOT_IMPLEMENTED = "not_implemented"


class FactorDefinition(BaseModel):
    factor_id: str
    version: str
    name: str
    category: FactorCategory
    mathematical_definition: str
    economic_intuition: str = ""
    inputs: list[str] = Field(default_factory=list)
    lookback: int = 20
    source: FactorSource = FactorSource.FEATURE
    feature_id: str = ""
    normalization: NormalizationMethod = NormalizationMethod.RANK
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.NOT_AVAILABLE
    winsorization: str = "none"
    expected_direction: str = "long_high"
    frequency: str = "1d"
    pit_requirements: str = "available_time <= decision_time; Universe(T)"
    known_limitations: str = ""
    family_id: str = ""
    lineage: dict[str, str] = Field(default_factory=dict)
    lifecycle: FactorLifecycle = FactorLifecycle.TESTING
    implementation_version: str = "0.8.0"
    notes: str = ""

    def identity_payload(self) -> dict[str, object]:
        return {
            "factor_id": self.factor_id,
            "version": self.version,
            "mathematical_definition": self.mathematical_definition,
            "inputs": self.inputs,
            "lookback": self.lookback,
            "source": self.source.value,
            "feature_id": self.feature_id,
            "normalization": self.normalization.value,
            "missing_value_policy": self.missing_value_policy.value,
            "winsorization": self.winsorization,
            "expected_direction": self.expected_direction,
            "frequency": self.frequency,
            "implementation_version": self.implementation_version,
            "lineage": self.lineage,
        }

    def identity_hash(self) -> str:
        return config_hash(self.identity_payload())
