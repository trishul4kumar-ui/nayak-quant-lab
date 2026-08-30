"""Versioned regime models. Distinct from per-instrument domain.models.MarketState."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash


class DetectorKind(StrEnum):
    RULE = "rule"
    HMM_FILTER = "hmm_filter"
    HMM_SMOOTH = "hmm_smooth"
    CLUSTER_WALK_FORWARD = "cluster_walk_forward"
    CLUSTER_FULL_SAMPLE = "cluster_full_sample"
    CHANGE_POINT = "change_point"
    NOT_IMPLEMENTED = "not_implemented"


class RegimeLifecycle(StrEnum):
    TESTING = "testing"
    SUPPORTED = "supported"
    RETROSPECTIVE = "retrospective"
    NOT_TESTED = "not_tested"
    CONTAMINATED = "contaminated"


class StateVariable(BaseModel):
    variable_id: str
    version: str
    name: str
    mathematical_definition: str
    inputs: list[str] = Field(default_factory=list)
    lookback: int = 20
    missing_policy: str = "not_available"
    pit_requirements: str = "available_time <= decision_time; Universe(T)"
    known_limitations: str = ""
    notes: str = ""
    implementation_version: str = "0.9.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "variable_id": self.variable_id,
                "version": self.version,
                "mathematical_definition": self.mathematical_definition,
                "inputs": self.inputs,
                "lookback": self.lookback,
                "missing_policy": self.missing_policy,
            }
        )


class RegimeModel(BaseModel):
    regime_model_id: str
    version: str
    name: str
    detector: DetectorKind
    state_features: list[str] = Field(default_factory=list)
    lookback: int = 20
    n_regimes: int = 3
    min_obs: int = 10
    parameters: dict[str, float | int | str] = Field(default_factory=dict)
    labels: list[str] = Field(default_factory=list)
    lifecycle: RegimeLifecycle = RegimeLifecycle.TESTING
    notes: str = "A regime label is a description of state, not a forecast and not alpha."
    implementation_version: str = "0.9.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "regime_model_id": self.regime_model_id,
                "version": self.version,
                "detector": self.detector.value,
                "state_features": self.state_features,
                "lookback": self.lookback,
                "n_regimes": self.n_regimes,
                "min_obs": self.min_obs,
                "parameters": self.parameters,
                "labels": self.labels,
            }
        )
