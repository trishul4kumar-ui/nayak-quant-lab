"""Seed paper account, snapshot, and a research target. Not NSE market data."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.capital.definitions import DecisionStatus, InvestmentDecision, TargetPortfolio
from quantlab.paper_oms.models import CashLedger, PaperAccount, PaperMarketSnapshot, PaperOMSRequest

SEED_ACCOUNT_ID = "PAPER-001"
SEED_AS_OF = datetime(2024, 1, 15, tzinfo=UTC)
SEED_NAMES = ("NSE:AAA", "NSE:BBB", "NSE:CCC")
SEED_PRICES = {"NSE:AAA": 100.0, "NSE:BBB": 80.0, "NSE:CCC": 120.0}
SEED_VOLUMES: dict[str, float | None] = {
    "NSE:AAA": 10_000_000.0,
    "NSE:BBB": 10_000_000.0,
    "NSE:CCC": 10_000_000.0,
}
SEED_WEIGHTS = {"NSE:AAA": 0.40, "NSE:BBB": 0.30, "NSE:CCC": 0.20}
SEED_CASH = 1_000_000.0


def seed_snapshot(*, volumes: dict[str, float | None] | None = None) -> PaperMarketSnapshot:
    return PaperMarketSnapshot(
        snapshot_id="seed",
        as_of=SEED_AS_OF,
        prices=dict(SEED_PRICES),
        volumes=dict(volumes if volumes is not None else SEED_VOLUMES),
        tradable={name: True for name in SEED_NAMES},
        lot_size={name: 1 for name in SEED_NAMES},
        note="Synthetic research snapshot for paper OMS architecture. Not NSE quotes.",
    )


def seed_account(*, cash: float = SEED_CASH, allow_short: bool = False) -> PaperAccount:
    return PaperAccount(
        account_id=SEED_ACCOUNT_ID,
        cash=cash,
        reserved_cash=0.0,
        available_cash=cash,
        positions={},
        gross_exposure=0.0,
        net_exposure=0.0,
        market_value=0.0,
        equity=cash,
        ledger=CashLedger(opening_cash=cash, closing_cash=cash),
        allow_short=allow_short,
    )


def seed_target(*, starting: float = SEED_CASH) -> TargetPortfolio:
    notionals = {name: weight * starting for name, weight in SEED_WEIGHTS.items()}
    return TargetPortfolio(
        portfolio_id="TP-PAPER-SEED",
        decision_id="DEC-PAPER-SEED",
        timestamp=SEED_AS_OF,
        weights=dict(SEED_WEIGHTS),
        notional_targets=notionals,
        gross_exposure=sum(SEED_WEIGHTS.values()),
        net_exposure=sum(SEED_WEIGHTS.values()),
        cash_target=max(0.0, 1.0 - sum(SEED_WEIGHTS.values())),
        portfolio_hash="seed-target",
        note="Seed target for paper OMS tests. Not a live book.",
    )


def seed_decision() -> InvestmentDecision:
    return InvestmentDecision(
        decision_id="DEC-PAPER-SEED",
        decision_time=SEED_AS_OF,
        snapshot_id="seed",
        capital_policy_id="CAP-RESEARCH-001",
        decision_status=DecisionStatus.RESEARCH_ONLY,
        target_weights=dict(SEED_WEIGHTS),
        gross_target=sum(SEED_WEIGHTS.values()),
        net_target=sum(SEED_WEIGHTS.values()),
        data_kind="synthetic",
        decision_hash="seed-decision",
        config_hash="seed-policy",
        software_version="",
        live_trading=False,
        note="Seed investment decision for paper OMS. Not an order.",
    )


def seed_request(
    *,
    execution_policy_id: str = "base",
    live_trading: bool = False,
    volumes: dict[str, float | None] | None = None,
) -> PaperOMSRequest:
    del volumes
    return PaperOMSRequest(
        decision_id="DEC-PAPER-SEED",
        account_id=SEED_ACCOUNT_ID,
        execution_policy_id=execution_policy_id,
        snapshot_id="seed",
        as_of=SEED_AS_OF,
        live_trading=live_trading,
        data_kind="synthetic",
    )
