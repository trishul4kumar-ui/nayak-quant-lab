"""Versioned ensemble identity. An ensemble is not a portfolio and not an order."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from quantlab.backtest.spec import config_hash
from quantlab.core.errors import EnsembleError


class ComponentType(StrEnum):
    ALPHA = "alpha"
    MODEL = "model"
    ADAPTIVE_MODEL = "adaptive_model"
    REGIME_CONDITIONED_MODEL = "regime_conditioned_model"
    FACTOR_SIGNAL = "factor_signal"


class WeightingPolicy(StrEnum):
    EQUAL = "equal"
    STATIC_IC = "static_ic"
    INVERSE_VOL = "inverse_vol"
    CORRELATION_AWARE = "correlation_aware"
    ROLLING_IC = "rolling_ic"
    EWMA_IC = "ewma_ic"
    REGULARIZED = "regularized"
    BAYESIAN_HIT = "bayesian_hit"
    RIDGE_STACK = "ridge_stack"
    ELASTIC_STACK = "elastic_stack"
    OLS_META = "ols_meta"
    RANK_SUM = "rank_sum"


class CombinationMethod(StrEnum):
    WEIGHTED_ZSCORE = "weighted_zscore"
    RANK_AVERAGE = "rank_average"
    RANK_SUM = "rank_sum"
    LINEAR = "linear"
    STACKING = "stacking"
    META_ALPHA = "meta_alpha"


class Normalization(StrEnum):
    RAW = "raw"
    ZSCORE = "zscore"
    CS_ZSCORE = "cs_zscore"
    RANK = "rank"
    RANK_ZSCORE = "rank_zscore"
    VOL_SCALED = "vol_scaled"


class EnsembleComponent(BaseModel):
    component_id: str
    component_type: ComponentType
    version: str = "1"
    expected_direction: int = 1
    normalization: Normalization = Normalization.ZSCORE
    prediction_time: str = "session_close"
    available_information_cutoff: str = "as_of"
    universe: str = "synthetic_listed"
    lineage: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _direction(self) -> EnsembleComponent:
        if self.expected_direction not in {-1, 1}:
            raise EnsembleError("expected_direction must be +1 or -1")
        return self


class EnsembleDefinition(BaseModel):
    ensemble_id: str
    version: str
    name: str
    components: list[EnsembleComponent]
    combination_method: CombinationMethod = CombinationMethod.WEIGHTED_ZSCORE
    normalization: Normalization = Normalization.ZSCORE
    weighting_policy: WeightingPolicy = WeightingPolicy.EQUAL
    training_window: int = 20
    validation_window: int = 0
    rebalance_frequency: int = 1
    min_obs: int = 8
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_concentration: float = 1.0
    max_turnover: float | None = None
    l2: float = 1.0
    l1: float = 0.0
    risk_aversion: float = 1.0
    weight_stability_penalty: float = 0.0
    shrinkage: float = 0.2
    half_life: float | None = None
    prune_corr_threshold: float | None = None
    diversity_policy: str = "report_only"
    regime_policy: str = "none"
    adaptive_policy: str = "none"
    regime_model_id: str = ""
    seed: int = 0
    is_meta_alpha: bool = False
    meta_alpha_id: str = ""
    notes: str = (
        "Ensemble output is a research-time score, not an order. "
        "Equal-weight and best-component are mandatory baselines. "
        "Sign is not inferred from future performance."
    )
    implementation_version: str = "1.2.0"

    @model_validator(mode="after")
    def _components(self) -> EnsembleDefinition:
        if not self.components:
            raise EnsembleError("empty_components")
        ids = [item.component_id for item in self.components]
        if len(ids) != len(set(ids)):
            raise EnsembleError("duplicate_components")
        return self

    def identity_hash(self) -> str:
        return config_hash(
            {
                "ensemble_id": self.ensemble_id,
                "version": self.version,
                "components": [
                    {
                        "id": item.component_id,
                        "type": item.component_type.value,
                        "version": item.version,
                        "direction": item.expected_direction,
                        "normalization": item.normalization.value,
                    }
                    for item in self.components
                ],
                "combination_method": self.combination_method.value,
                "normalization": self.normalization.value,
                "weighting_policy": self.weighting_policy.value,
                "training_window": self.training_window,
                "validation_window": self.validation_window,
                "rebalance_frequency": self.rebalance_frequency,
                "min_obs": self.min_obs,
                "min_weight": self.min_weight,
                "max_weight": self.max_weight,
                "max_concentration": self.max_concentration,
                "max_turnover": self.max_turnover,
                "l2": self.l2,
                "l1": self.l1,
                "risk_aversion": self.risk_aversion,
                "weight_stability_penalty": self.weight_stability_penalty,
                "shrinkage": self.shrinkage,
                "half_life": self.half_life,
                "prune_corr_threshold": self.prune_corr_threshold,
                "diversity_policy": self.diversity_policy,
                "regime_policy": self.regime_policy,
                "adaptive_policy": self.adaptive_policy,
                "regime_model_id": self.regime_model_id,
                "seed": self.seed,
                "is_meta_alpha": self.is_meta_alpha,
                "meta_alpha_id": self.meta_alpha_id,
            }
        )

    def component_ids(self) -> list[str]:
        return [item.component_id for item in self.components]


class EnsembleLeakFlags(BaseModel):
    future_weights: bool = False
    future_correlation: bool = False
    future_component_performance: bool = False
    future_normalization: bool = False
    future_meta_feature: bool = False
    future_component_selection: bool = False
    future_stacking: bool = False
    future_pruning: bool = False
    future_hyperparameter: bool = False
    holdout_contaminated: bool = False
    stacking_leak: bool = False
    full_sample_replay: bool = False
    future_covariance: bool = False
    future_regime: bool = False


class EnsembleState(BaseModel):
    ensemble_definition_id: str
    fit_timestamp: datetime | None = None
    training_start: datetime | None = None
    training_end: datetime | None = None
    available_information_cutoff: datetime | None = None
    component_states: dict[str, str] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)
    weight_policy: str = ""
    normalization_state: str = ""
    correlation_state: str = ""
    hyperparameters: dict[str, float | int | str] = Field(default_factory=dict)
    random_seed: int = 0
    dataset_snapshot: str = ""
    config_hash: str = ""
    software_version: str = "1.2.0"
    note: str = "frozen research state; not a live agent"


class EnsemblePrediction(BaseModel):
    ensemble_state_id: str
    prediction_time: datetime
    security_id: str
    component_predictions: dict[str, float] = Field(default_factory=dict)
    component_weights: dict[str, float] = Field(default_factory=dict)
    composite_score: float
    normalization: str = ""
    regime_context: str | None = None
    available_information_cutoff: datetime | None = None


class MetaAlpha(BaseModel):
    meta_alpha_id: str
    ensemble_id: str
    version: str
    base_component_ids: list[str]
    algorithm: str
    note: str = "META-ALPHA ≠ ALPHA. Lineage of base components is retained."
