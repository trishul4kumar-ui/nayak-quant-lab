"""Portfolio model identity. A config change requires a new version."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.portfolio.constraints import (
    ConstraintSpec,
    long_only_invested,
    long_only_set,
    long_short_set,
)


class ConstructorKind(StrEnum):
    TOP_N = "top_n"
    BOTTOM_N = "bottom_n"
    RANK_WEIGHT = "rank_weight"
    EQUAL_WEIGHT = "equal_weight"
    LONG_SHORT_TOP_BOTTOM = "long_short_top_bottom"
    SCORE_WEIGHT = "score_weight"
    MIN_VARIANCE = "min_variance"
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"


class RebalancePolicy(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MissingAlphaPolicy(StrEnum):
    EXCLUDE = "exclude"
    NEUTRALIZE = "neutralize"
    MISSING = "missing"


class PortfolioModel(BaseModel):
    portfolio_id: str
    version: str
    name: str
    ensemble_id: str
    constructor: ConstructorKind = ConstructorKind.TOP_N
    top_n: int = 2
    bottom_n: int = 0
    long_only: bool = True
    constraints: list[ConstraintSpec] = Field(default_factory=long_only_set)
    covariance_lookback: int = 60
    covariance_estimator: str = "sample"
    covariance_repair: str = "none"
    vol_target: float | None = None
    max_leverage: float = 1.0
    risk_aversion: float = 1.0
    rebalance: RebalancePolicy = RebalancePolicy.DAILY
    cost_bps: float = 10.0
    missing_alpha: MissingAlphaPolicy = MissingAlphaPolicy.EXCLUDE
    family_id: str = ""
    notes: str = ""
    implementation_version: str = "0.7.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "portfolio_id": self.portfolio_id,
                "version": self.version,
                "ensemble_id": self.ensemble_id,
                "constructor": self.constructor.value,
                "top_n": self.top_n,
                "bottom_n": self.bottom_n,
                "long_only": self.long_only,
                "constraints": [c.model_dump(mode="json") for c in self.constraints],
                "covariance_lookback": self.covariance_lookback,
                "covariance_estimator": self.covariance_estimator,
                "covariance_repair": self.covariance_repair,
                "vol_target": self.vol_target,
                "max_leverage": self.max_leverage,
                "risk_aversion": self.risk_aversion,
                "rebalance": self.rebalance.value,
                "cost_bps": self.cost_bps,
                "missing_alpha": self.missing_alpha.value,
            }
        )


def seed_portfolios() -> list[PortfolioModel]:
    return [
        PortfolioModel(
            portfolio_id="mom20_topn",
            version="1",
            name="Top-N equal-weight rank momentum 20",
            ensemble_id="mom20",
            constructor=ConstructorKind.TOP_N,
            top_n=2,
            family_id="cs_momentum_portfolios",
            notes="Transparent baseline matching the architecture slice constructor",
        ),
        PortfolioModel(
            portfolio_id="mom_5_20_ew",
            version="1",
            name="Equal-weight names from 5/20 momentum ensemble",
            ensemble_id="mom_5_20",
            constructor=ConstructorKind.EQUAL_WEIGHT,
            family_id="cs_momentum_portfolios",
        ),
        PortfolioModel(
            portfolio_id="mom20_rank_weight",
            version="1",
            name="Rank-weighted momentum 20",
            ensemble_id="mom20",
            constructor=ConstructorKind.RANK_WEIGHT,
            family_id="cs_momentum_portfolios",
        ),
        PortfolioModel(
            portfolio_id="mom20_minvar",
            version="1",
            name="Projected min-variance of momentum-20 names",
            ensemble_id="mom20",
            constructor=ConstructorKind.MIN_VARIANCE,
            family_id="cs_momentum_portfolios",
            constraints=long_only_invested(),
            covariance_lookback=20,
            notes="Projected gradient on the simplex, not a commercial QP solver",
        ),
        PortfolioModel(
            portfolio_id="mom20_ls",
            version="1",
            name="Long-short top/bottom momentum 20",
            ensemble_id="mom20",
            constructor=ConstructorKind.LONG_SHORT_TOP_BOTTOM,
            top_n=2,
            bottom_n=2,
            long_only=False,
            family_id="cs_momentum_portfolios",
            constraints=long_short_set(),
            notes="Gross 1.0, net ~0. Not a market-neutral claim without a beta series.",
        ),
    ]


_MODELS = {item.portfolio_id: item for item in seed_portfolios()}


def get_portfolio_model(portfolio_id: str) -> PortfolioModel:
    if portfolio_id not in _MODELS:
        raise KeyError(f"unknown portfolio {portfolio_id}")
    return _MODELS[portfolio_id]


def list_portfolio_models() -> list[PortfolioModel]:
    return list(_MODELS.values())
