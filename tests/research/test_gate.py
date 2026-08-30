from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome, evaluate_research_gate


def test_synthetic_cannot_promote() -> None:
    result = evaluate_research_gate(
        integrity_failed=False,
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind="synthetic",
        walk_forward_windows=3,
        oos_sharpe=1.2,
        cost_still_positive_at_20bps=True,
        parameter_fragile=False,
        statistical_status=CheckResult.PASS,
        n_hypotheses=5,
        test_used_for_selection=False,
    )
    assert result.outcome is GateOutcome.WARN
    assert result.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert result.outcome is not GateOutcome.PROMOTED_TO_PAPER


def test_integrity_fail_rejects() -> None:
    result = evaluate_research_gate(
        integrity_failed=True,
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
    )
    assert result.outcome is GateOutcome.REJECT


def test_zero_cost_rejects() -> None:
    result = evaluate_research_gate(
        integrity_failed=False,
        next_bar_fill=True,
        cost_bps=0.0,
        data_kind="real",
        walk_forward_windows=3,
        oos_sharpe=0.1,
        cost_still_positive_at_20bps=True,
        parameter_fragile=False,
        statistical_status=CheckResult.PASS,
        n_hypotheses=1,
        test_used_for_selection=False,
    )
    assert result.outcome is GateOutcome.REJECT


def test_test_set_contamination_rejects() -> None:
    result = evaluate_research_gate(
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
        test_used_for_selection=True,
    )
    assert result.outcome is GateOutcome.REJECT
