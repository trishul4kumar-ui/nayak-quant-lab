from datetime import UTC, datetime

from tests.trade_candidates.test_candidate_packet import build_input
from tests.trade_levels.test_engine import level_input

from quantlab.paper_candidate_execution import PaperMode, paper_eligibility
from quantlab.trade_candidates.builder import build_candidate
from quantlab.trade_candidates.models import CandidateBuildInput
from quantlab.trade_levels.engine import compute_trade_level_plan
from quantlab.trade_levels.models import TradeLevelPlan

NOW = datetime(2026, 10, 7, 7, tzinfo=UTC)


def candidate_and_plan() -> tuple[object, TradeLevelPlan]:
    plan, _ = compute_trade_level_plan(level_input())
    value = build_input().model_dump(mode="python", exclude={"content_hash"})
    value["level_plan_hash"] = plan.content_hash
    candidate = build_candidate(CandidateBuildInput.model_validate(value))
    return candidate, plan


def test_human_paper_mode_never_grants_broker_write() -> None:
    candidate, plan = candidate_and_plan()
    blocked = paper_eligibility(
        candidate,
        plan,
        now=NOW,
        mode=PaperMode.HUMAN_APPROVED_PAPER,
        human_approved=False,
    )
    assert not blocked.eligible and "HUMAN_PAPER_APPROVAL_REQUIRED" in blocked.blockers
    accepted = paper_eligibility(
        candidate,
        plan,
        now=NOW,
        mode=PaperMode.HUMAN_APPROVED_PAPER,
        human_approved=True,
    )
    assert accepted.eligible and not accepted.execution_authority
