"""Shadow execution wraps Prompt 18 paper OMS. No second slippage engine."""

from __future__ import annotations

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import (
    PaperAccount,
    PaperMarketSnapshot,
    PaperOMSRequest,
    PaperOMSResult,
)
from quantlab.paper_oms.service import run_paper_oms


def run_paper_execution(
    *,
    request: PaperOMSRequest | None = None,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    account: PaperAccount | None = None,
    snapshot: PaperMarketSnapshot | None = None,
) -> PaperOMSResult:
    return run_paper_oms(
        request or PaperOMSRequest(),
        decision=decision or seed_decision(),
        target=target or seed_target(),
        account=account or seed_account(),
        snapshot=snapshot or seed_snapshot(),
    )
