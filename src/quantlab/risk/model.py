"""Versioned research risk model. Not the live firewall and not an optimizer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash


class RiskModelSpec(BaseModel):
    risk_model_id: str
    version: str
    name: str
    covariance_estimator: str = "sample"
    covariance_lookback: int = 20
    covariance_repair: str = "none"
    ewma_lambda: float = 0.94
    shrinkage: float = 0.2
    factor_ids: list[str] = Field(default_factory=lambda: ["market_ew_beta", "style_momentum_20"])
    benchmark: str = "equal_weight_universe"
    notes: str = "Risk estimates variance/exposure. It does not invent expected return."
    implementation_version: str = "0.8.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "risk_model_id": self.risk_model_id,
                "version": self.version,
                "covariance_estimator": self.covariance_estimator,
                "covariance_lookback": self.covariance_lookback,
                "covariance_repair": self.covariance_repair,
                "ewma_lambda": self.ewma_lambda,
                "shrinkage": self.shrinkage,
                "factor_ids": self.factor_ids,
                "benchmark": self.benchmark,
            }
        )


def seed_risk_models() -> list[RiskModelSpec]:
    return [
        RiskModelSpec(
            risk_model_id="sample_cs",
            version="1",
            name="Sample covariance + EW-universe beta",
        ),
        RiskModelSpec(
            risk_model_id="ewma_cs",
            version="1",
            name="EWMA covariance + EW-universe beta",
            covariance_estimator="ewma",
        ),
        RiskModelSpec(
            risk_model_id="shrink_cs",
            version="1",
            name="Diagonal-shrinkage sample covariance",
            covariance_estimator="shrinkage",
        ),
    ]


_MODELS = {item.risk_model_id: item for item in seed_risk_models()}


def get_risk_model(risk_model_id: str) -> RiskModelSpec:
    if risk_model_id not in _MODELS:
        raise KeyError(f"unknown risk model {risk_model_id}")
    return _MODELS[risk_model_id]


def list_risk_models() -> list[RiskModelSpec]:
    return list(_MODELS.values())
