"""Real-time decision integrity mapping. Unset flags remain NOT_TESTED."""

from __future__ import annotations

from quantlab.domain.research import IntegrityReport
from quantlab.realtime_decision.models import RealTimeDecision
from quantlab.research.integrity import evaluate_integrity


def report_from_decision(item: RealTimeDecision) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=item.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        future_realtime_feature=False,
        future_realtime_model=False,
        future_realtime_regime=False,
        future_adaptive_update=False,
        release_mutation=False,
        uncertified_model_use=False,
        expired_release_use=False,
        decision_state_mutation=False,
        rt_snapshot_mismatch=False,
        stale_state_decision=False,
        missing_critical_input=False,
        capital_constraint_bypass=False,
        decision_replay_mismatch=False,
        ai_authority_violation=False,
    )
