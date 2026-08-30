"""JSON reports for CLI and the desktop query layer."""

from __future__ import annotations

from typing import Any

from quantlab.monitoring.models import MonitoringResult


def result_report(result: MonitoringResult) -> dict[str, Any]:
    return {
        "monitoring_run_id": result.run.monitoring_run_id,
        "oms_run_id": result.run.oms_run_id,
        "status": result.run.status.value,
        "pnl_total": result.pnl.pnl_total,
        "residual_pnl": result.pnl.residual_pnl,
        "net_return": result.pnl.net_return,
        "identity_ok": result.pnl.identity_ok,
        "attribution_method": result.attribution.method.value,
        "attribution_residual": result.attribution.residual,
        "drift": result.drift.status.value,
        "implementation_gap": result.drift.implementation_gap,
        "max_drawdown": result.drawdown.max_drawdown,
        "concentration": result.concentration,
        "turnover": result.turnover,
        "benchmark": result.benchmark.benchmark_id,
        "benchmark_kind": result.benchmark.kind.value,
        "feedback": [item.kind.value for item in result.feedback],
        "live_trading": False,
        "note": result.note,
        "hash": result.run.run_hash,
    }
