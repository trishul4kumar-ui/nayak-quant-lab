"""Versioned adaptive-model identity. A learner is not alpha and not an order."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash


class AdaptationPolicy(StrEnum):
    NO_ADAPTATION = "no_adaptation"
    ROLLING_REFIT = "rolling_refit"
    EXPANDING_REFIT = "expanding_refit"
    EWMA_UPDATE = "ewma_update"
    DRIFT_TRIGGERED_REFIT = "drift_triggered_refit"
    REGIME_CONDITIONAL = "regime_conditional"
    ENSEMBLE_ADAPTATION = "ensemble_adaptation"


class LearnerKind(StrEnum):
    STATIC = "static"
    ROLLING_IC = "rolling_ic"
    EXPANDING_IC = "expanding_ic"
    EWMA_IC = "ewma_ic"
    BAYESIAN_HIT = "bayesian_hit"
    IC_WEIGHTED_ENSEMBLE = "ic_weighted_ensemble"


class AdaptiveModelDefinition(BaseModel):
    adaptive_model_id: str
    version: str
    name: str
    policy: AdaptationPolicy
    learner: LearnerKind
    alpha_ids: list[str] = Field(default_factory=list)
    window: int = 20
    min_obs: int = 8
    half_life: float | None = None
    min_ess: float = 5.0
    update_frequency: int = 1
    refit_frequency: int = 1
    seed: int = 0
    regime_model_id: str = ""
    min_alpha_weight: float = 0.0
    max_alpha_weight: float = 1.0
    max_concentration: float = 1.0
    min_active_alphas: int = 1
    notes: str = (
        "Adaptive output is a research-time score or weight, not an order. "
        "Sign is not inferred from future performance."
    )
    implementation_version: str = "1.0.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "adaptive_model_id": self.adaptive_model_id,
                "version": self.version,
                "policy": self.policy.value,
                "learner": self.learner.value,
                "alpha_ids": self.alpha_ids,
                "window": self.window,
                "min_obs": self.min_obs,
                "half_life": self.half_life,
                "min_ess": self.min_ess,
                "update_frequency": self.update_frequency,
                "refit_frequency": self.refit_frequency,
                "seed": self.seed,
                "regime_model_id": self.regime_model_id,
                "min_alpha_weight": self.min_alpha_weight,
                "max_alpha_weight": self.max_alpha_weight,
                "max_concentration": self.max_concentration,
                "min_active_alphas": self.min_active_alphas,
            }
        )
