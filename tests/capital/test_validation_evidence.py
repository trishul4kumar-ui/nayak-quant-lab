from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.definitions import AbstentionCode, DecisionStatus, LiquidityStatus
from quantlab.capital.library import seed_policy, seed_request
from quantlab.capital.liquidity import classify_name
from quantlab.capital.validation import map_gate
from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate


def _candidate() -> ResearchGateResult:
    return evaluate_research_gate(
        integrity_failed=False,
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind="real",
        walk_forward_windows=3,
        oos_sharpe=0.1,
        cost_still_positive_at_20bps=True,
        parameter_fragile=False,
        statistical_status=CheckResult.PASS,
        n_hypotheses=1,
        test_used_for_selection=False,
        pit_evidence=CheckResult.PASS,
    )


def test_missing_gate_does_not_make_real_data_eligible() -> None:
    status, code, warnings = map_gate(None, "real", allow_research_only_on_warn=True)
    assert status is DecisionStatus.RESEARCH_ONLY
    assert code is AbstentionCode.NONE
    assert "research gate unavailable" in warnings
    result = allocate(seed_request().model_copy(update={"data_kind": "real", "gate": None}))
    assert result.decision.decision_status is DecisionStatus.RESEARCH_ONLY


def test_policy_can_require_the_gate() -> None:
    status, code, _ = map_gate(None, "real", allow_research_only_on_warn=True, require_gate=True)
    assert status is DecisionStatus.REJECTED
    assert code is AbstentionCode.GATE_FAIL


def test_incomplete_forged_candidate_and_unknown_data_kind_cannot_promote() -> None:
    forged = ResearchGateResult(outcome=GateOutcome.RESEARCH_CANDIDATE)
    assert (
        map_gate(forged, "real", allow_research_only_on_warn=True)[0]
        is DecisionStatus.RESEARCH_ONLY
    )
    assert map_gate(forged, "real", allow_research_only_on_warn=False)[0] is DecisionStatus.REJECTED
    assert (
        map_gate(_candidate(), "unknown", allow_research_only_on_warn=True)[0]
        is DecisionStatus.REJECTED
    )


def test_pit_candidate_can_be_eligible_but_paper_promotion_is_separate() -> None:
    candidate = _candidate()
    assert (
        map_gate(candidate, "real", allow_research_only_on_warn=True)[0] is DecisionStatus.ELIGIBLE
    )
    promoted = candidate.model_copy(update={"outcome": GateOutcome.PROMOTED_TO_PAPER})
    assert (
        map_gate(promoted, "real", allow_research_only_on_warn=True)[0]
        is DecisionStatus.RESEARCH_ONLY
    )


@pytest.mark.parametrize("adv", [float("nan"), float("inf"), -float("inf"), 0.0, -1.0])
def test_nonfinite_or_nonpositive_adv_is_unknown(adv: float) -> None:
    assert classify_name(adv, 1000.0, seed_policy().liquidity_policy) is LiquidityStatus.UNKNOWN


@pytest.mark.parametrize("limit", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_participation_limit_is_unknown(limit: float) -> None:
    policy = seed_policy().liquidity_policy.model_copy(update={"participation_limit": limit})
    assert classify_name(1_000_000.0, 1000.0, policy) is LiquidityStatus.UNKNOWN


def test_nonfinite_notional_is_unknown() -> None:
    assert (
        classify_name(1_000_000.0, float("nan"), seed_policy().liquidity_policy)
        is LiquidityStatus.UNKNOWN
    )


def test_permissive_unknown_liquidity_stays_research_only() -> None:
    base = seed_policy()
    liquidity = base.liquidity_policy.model_copy(update={"strict_unknown": False})
    policy = base.model_copy(update={"liquidity_policy": liquidity})
    request = seed_request(liquidity_adv={}).model_copy(
        update={"data_kind": "real", "gate": _candidate()}
    )
    result = allocate(request, policy=policy)
    assert result.decision.liquidity_status is LiquidityStatus.UNKNOWN
    assert result.decision.decision_status is DecisionStatus.RESEARCH_ONLY
    assert "unverified liquidity cannot support promotion" in result.decision.warnings
