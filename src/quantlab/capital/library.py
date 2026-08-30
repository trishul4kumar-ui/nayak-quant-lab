"""Seed capital policy. Research diagnostics, not a live book."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.capital.definitions import (
    AllocationRequest,
    CapitalPolicy,
    ConfidenceBundle,
    ConstraintPolicy,
    ExpectedReturnSource,
)
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport

SEED_POLICY_ID = "CAP-RESEARCH-001"
SEED_NAMES = ("NSE:AAA", "NSE:BBB", "NSE:CCC")
SEED_AS_OF = datetime(2024, 1, 15, tzinfo=UTC)


def seed_policy() -> CapitalPolicy:
    return CapitalPolicy(
        policy_id=SEED_POLICY_ID,
        version="1",
        base_currency="INR",
        starting_capital=1_000_000.0,
        available_capital=1_000_000.0,
        gross_leverage_limit=1.0,
        net_exposure_limit=1.0,
        cash_floor=0.05,
        max_position_weight=0.55,
        max_single_name_risk=0.50,
        max_turnover=1.0,
        target_volatility=0.15,
        kelly_fraction=0.25,
        kelly_cap=0.25,
        constraint_policy=ConstraintPolicy(
            allow_research_only_on_warn=True,
            fallback_sizing="",
            strict_missing_covariance=False,
        ),
    ).with_hash()


def list_policies() -> list[CapitalPolicy]:
    return [seed_policy()]


def get_policy(policy_id: str) -> CapitalPolicy:
    for item in list_policies():
        if item.policy_id == policy_id:
            return item
    from quantlab.capital.errors import CapitalError

    raise CapitalError(f"unknown capital policy {policy_id}")


def seed_covariance() -> CovarianceReport:
    names = list(SEED_NAMES)
    matrix = [
        [0.0400, 0.0100, 0.0080],
        [0.0100, 0.0484, 0.0090],
        [0.0080, 0.0090, 0.0324],
    ]
    return CovarianceReport(
        names=names,
        matrix=matrix,
        lookback=60,
        estimator="sample",
        as_of=SEED_AS_OF,
        n_obs=60,
        min_eigenvalue=0.02,
        psd=True,
        status=CheckResult.PASS,
        note="seed PIT-style covariance for architecture diagnostics; not market evidence",
    )


def seed_request(
    *,
    policy_id: str = SEED_POLICY_ID,
    live_trading: bool = False,
    data_kind: str = "synthetic",
    drawdown: float = 0.0,
    scores: dict[str, float] | None = None,
    liquidity_adv: dict[str, float | None] | None = None,
) -> AllocationRequest:
    return AllocationRequest(
        policy_id=policy_id,
        as_of=SEED_AS_OF,
        snapshot_id="seed",
        dataset_checksum="seed",
        scores=scores
        or {
            "NSE:AAA": 0.08,
            "NSE:BBB": 0.05,
            "NSE:CCC": 0.03,
        },
        expected_return_source=ExpectedReturnSource.BASELINE,
        vols={"NSE:AAA": 0.20, "NSE:BBB": 0.22, "NSE:CCC": 0.18},
        covariance=seed_covariance(),
        liquidity_adv=liquidity_adv
        if liquidity_adv is not None
        else {"NSE:AAA": 5_000_000.0, "NSE:BBB": 4_000_000.0, "NSE:CCC": 3_000_000.0},
        data_kind=data_kind,
        live_trading=live_trading,
        drawdown=drawdown,
        portfolio_spec_id="mom20_topn",
        knowledge_snapshot_id="KS-SEED-001",
        confidence=ConfidenceBundle(),
        n_obs_returns=60,
    )
