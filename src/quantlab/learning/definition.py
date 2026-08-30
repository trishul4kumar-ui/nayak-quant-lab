"""Versioned statistical-model identity. A model is not alpha and not an order."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash


class Algorithm(StrEnum):
    NO_SIGNAL = "no_signal"
    MEAN = "mean"
    ALPHA = "alpha"
    OLS = "ols"
    RIDGE = "ridge"
    LASSO = "lasso"
    ELASTIC_NET = "elastic_net"
    HUBER = "huber"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    PCA_OLS = "pca_ols"
    SELECT_OLS = "select_ols"


class ScalingMethod(StrEnum):
    NONE = "none"
    ZSCORE = "zscore"
    ROBUST = "robust"


class MissingPolicy(StrEnum):
    DROP = "drop"


class PanelKind(StrEnum):
    CROSS_SECTION = "cross_section"
    TIME_SERIES = "time_series"
    POOLED_PANEL = "pooled_panel"


class SelectionMethod(StrEnum):
    NONE = "none"
    UNIVARIATE_IC = "univariate_ic"
    CORRELATION_FILTER = "correlation_filter"
    L1 = "l1"


class ModelDefinition(BaseModel):
    model_id: str
    version: str
    name: str
    algorithm: Algorithm
    features: list[str] = Field(default_factory=list)
    feature_versions: dict[str, str] = Field(default_factory=dict)
    target: str = "forward_return_1"
    target_version: str = "1"
    alpha_id: str = ""
    universe: list[str] = Field(default_factory=list)
    frequency: str = "1d"
    training_window: int = 24
    min_train_dates: int = 12
    min_obs: int = 20
    normalization: ScalingMethod = ScalingMethod.ZSCORE
    missing_value_policy: MissingPolicy = MissingPolicy.DROP
    panel_kind: PanelKind = PanelKind.POOLED_PANEL
    hyperparameters: dict[str, float] = Field(default_factory=dict)
    random_seed: int = 0
    regime_model_id: str = ""
    adaptive_policy: str = ""
    selection_method: SelectionMethod = SelectionMethod.NONE
    selection_k: int = 2
    pca_components: int = 2
    n_estimators: int = 8
    max_depth: int = 2
    min_leaf: int = 5
    learning_rate: float = 0.1
    notes: str = (
        "Model output is a research-time score. It is not an order. "
        "OLS is not causal. Importance is not causality. Synthetic cannot promote."
    )
    implementation_version: str = "1.1.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "model_id": self.model_id,
                "version": self.version,
                "algorithm": self.algorithm.value,
                "features": self.features,
                "feature_versions": self.feature_versions,
                "target": self.target,
                "alpha_id": self.alpha_id,
                "training_window": self.training_window,
                "min_train_dates": self.min_train_dates,
                "min_obs": self.min_obs,
                "normalization": self.normalization.value,
                "missing_value_policy": self.missing_value_policy.value,
                "panel_kind": self.panel_kind.value,
                "hyperparameters": self.hyperparameters,
                "random_seed": self.random_seed,
                "regime_model_id": self.regime_model_id,
                "selection_method": self.selection_method.value,
                "selection_k": self.selection_k,
                "pca_components": self.pca_components,
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "min_leaf": self.min_leaf,
                "learning_rate": self.learning_rate,
            }
        )
