"""Seed monitoring inputs. Synthetic diagnostic, not NSE evidence."""

from __future__ import annotations

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import PaperOMSRequest, PaperOMSResult
from quantlab.paper_oms.service import run_paper_oms
from quantlab.paper_oms.state import last_result


def seed_paper_result() -> tuple[PaperOMSResult, InvestmentDecision, TargetPortfolio]:
    existing = last_result()
    if existing is not None:
        return existing, seed_decision(), seed_target()
    result = run_paper_oms(
        PaperOMSRequest(),
        decision=seed_decision(),
        target=seed_target(),
        account=seed_account(),
        snapshot=seed_snapshot(),
    )
    return result, seed_decision(), seed_target()
