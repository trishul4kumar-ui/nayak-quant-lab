"""Structured capital-allocation reports. Not market evidence."""

from __future__ import annotations

from typing import Any

from quantlab.capital.definitions import InvestmentDecision
from quantlab.capital.diagnostics import explain_decision


def capital_report(decision: InvestmentDecision) -> dict[str, Any]:
    explained = explain_decision(decision)
    return {
        "WHAT": "Capital allocation / investment decision (not an order)",
        "STATUS": decision.decision_status.value,
        "capital_state": decision.capital_state.value,
        "drawdown_state": decision.drawdown_state.value,
        "gross_target": decision.gross_target,
        "net_target": decision.net_target,
        "method": decision.allocation_method,
        "abstention_code": decision.abstention_code.value,
        "abstention_reason": decision.abstention_reason,
        "decision_hash": decision.decision_hash,
        "snapshot_id": decision.snapshot_id,
        "data_kind": decision.data_kind,
        "live_trading": False,
        "warnings": decision.warnings,
        "EXPLAIN": explained,
        "note": (
            "Synthetic diagnostics are not market evidence. "
            "Prompt 17 does not submit broker orders."
        ),
    }
