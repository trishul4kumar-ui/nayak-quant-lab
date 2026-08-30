"""Broker-gateway integrity mapping. Unset flags remain NOT_TESTED."""

from __future__ import annotations

from quantlab.broker_gateway.models import ReconResult, ReconStatus
from quantlab.domain.research import IntegrityReport
from quantlab.research.integrity import evaluate_integrity


def report_from_recon(result: ReconResult) -> IntegrityReport:
    kinds = {item.kind for item in result.breaks}
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=result.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        broker_identity_mismatch="broker_identity_mismatch" in kinds,
        unknown_broker_order=bool(result.unknown_broker_orders),
        orphan_broker_fill=bool(result.orphan_fills),
        missing_broker_fill=bool(result.missing_fills),
        order_reconciliation_break="unknown_broker_order" in kinds,
        position_reconciliation_break="position_reconciliation_break" in kinds,
        cash_reconciliation_break="cash_reconciliation_break" in kinds,
        instrument_mapping_ambiguity="instrument_mapping_ambiguity" in kinds,
        event_ordering_failure="event_ordering_failure" in kinds,
        broker_write_attempt=False,
        live_mode_confusion=result.live_trading,
        safety_bypass=result.write_enabled,
        stale_broker_state=result.status is ReconStatus.RECONCILIATION_REQUIRED,
    )
