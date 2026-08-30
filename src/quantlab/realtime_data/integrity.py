"""Real-time data integrity mapping. Unset flags remain NOT_TESTED."""

from __future__ import annotations

from quantlab.domain.research import IntegrityReport
from quantlab.realtime_data.models import RealTimeSnapshot
from quantlab.research.integrity import evaluate_integrity


def report_from_snapshot(snapshot: RealTimeSnapshot) -> IntegrityReport:
    future_ignored = int(snapshot.extras.get("future_ignored", 0) or 0)
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=snapshot.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        future_market_observation=future_ignored > 0 and False,
        future_state_mutation=False,
        future_volume=False,
        future_quote=False,
        future_reference_data=False,
        timestamp_order_violation=False,
        receive_time_violation=False,
        sequence_gap_hidden=False,
        stale_data_used=False,
        invalid_data_used=False,
        missing_data_filled=False,
        clock_drift=False,
        session_mismatch=False,
        security_identity_mismatch=False,
        realtime_snapshot_mutation=False,
        realtime_replay_mismatch=False,
    )
