"""Digital-twin integrity mapping. Unset flags remain NOT_TESTED."""

from __future__ import annotations

from quantlab.digital_twin.models import TwinMode, TwinRun
from quantlab.domain.research import IntegrityReport
from quantlab.research.integrity import evaluate_integrity


def report_from_twin(item: TwinRun) -> IntegrityReport:
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
        future_replay_input=False,
        future_shadow_state=False,
        replay_snapshot_mismatch=False,
        replay_state_mutation=False,
        replay_nondeterminism=False,
        event_order_violation=False,
        event_deletion=False,
        checkpoint_mutation=False,
        counterfactual_observation_confusion=item.counterfactual
        and item.mode is not TwinMode.COUNTERFACTUAL,
        simulated_fill_as_broker_fill=False,
        hidden_reconciliation_break=False,
        recovery_state_mismatch=False,
        release_mismatch=False,
        strategy_state_mismatch=False,
        shadow_routing_attempt=item.write_enabled,
    )
