"""App-layer capital services. CLI and desktop call these. UI does not allocate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.capital.diagnostics import explain_decision, risk_view
from quantlab.capital.experiment import run_named_allocation
from quantlab.capital.library import get_policy, list_policies
from quantlab.capital.memory import get_decision, get_result, last_result, list_decisions
from quantlab.capital.report import capital_report
from quantlab.core.config import get_settings
from quantlab.models.registry import ExperimentLedger


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def list_payload() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_policies():
        rows.append(
            {
                "policy_id": item.policy_id,
                "currency": item.base_currency,
                "starting_capital": item.starting_capital,
                "target_vol": item.target_volatility,
                "kelly_fraction": item.kelly_fraction,
                "identity": item.config_hash,
                "note": "Research capital policy. Not a live book.",
            }
        )
    return rows


def inspect_payload(policy_id: str) -> dict[str, Any]:
    item = get_policy(policy_id)
    payload = item.model_dump(mode="json")
    payload["note"] = (
        "Capital policy for research allocation. Prompt 17 does not place orders. "
        "Synthetic cannot promote."
    )
    payload["live_trading"] = False
    return payload


def validate_payload(policy_id: str) -> dict[str, Any]:
    item = get_policy(policy_id)
    return {
        "policy_id": item.policy_id,
        "valid": True,
        "config_hash": item.config_hash,
        "cash_floor": item.cash_floor,
        "max_position_weight": item.max_position_weight,
        "live_trading": False,
        "note": "Policy validates as a research configuration.",
    }


def allocate_named(portfolio_id: str = "mom20_topn", *, ledger: str = "") -> dict[str, Any]:
    result, run = run_named_allocation(
        ledger_path=_ledger_path(ledger),
        portfolio_id=portfolio_id,
    )
    summary: dict[str, Any] = {
        "decision_id": result.decision.decision_id,
        "status": result.decision.decision_status.value,
        "capital_state": result.decision.capital_state.value,
        "gross_target": result.decision.gross_target,
        "net_target": result.decision.net_target,
        "weights": result.decision.target_weights,
        "decision_hash": result.decision.decision_hash,
        "data_kind": result.decision.data_kind,
        "selection_stage": run.selection_stage,
        "live_trading": False,
        "note": "Target portfolio only. Not an order.",
    }
    try:
        from quantlab.knowledge.ingest import persist_capital_decision

        persist_capital_decision(result.decision, _ledger_path(ledger))
    except Exception as exc:  # noqa: BLE001 — knowledge must not fail a recorded allocation
        summary["knowledge_ingest"] = f"WARN: {exc}"
    return summary


def _require(decision_id: str) -> Any:
    result = get_result(decision_id)
    if result is not None:
        return result
    decision = get_decision(decision_id)
    if decision is None:
        return None
    return decision


def decision_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet; run quantlab capital allocate"}
    return result.decision.model_dump(mode="json")


def explain_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return explain_decision(result.decision)


def constraints_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "decision_id": result.decision.decision_id,
        "constraints": [item.model_dump(mode="json") for item in result.decision.constraint_status],
    }


def risk_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "decision_id": result.decision.decision_id,
        "expected_volatility": result.decision.expected_volatility,
        "risk_contribution": result.decision.risk_contribution,
        "view": risk_view(result.decision.target_weights, None),
        "note": "Missing covariance remains NOT_TESTED in this view if not re-supplied.",
    }


def exposure_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "factor_exposure": result.decision.factor_exposure,
        "status": result.decision.factor_exposure_status.value,
        "note": "Missing factor exposure is NOT_TESTED, never zero.",
    }


def sizing_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "method": result.decision.allocation_method,
        "weights": result.decision.target_weights,
        "kelly_note": "Kelly is constrained and cannot override hard limits.",
    }


def turnover_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {"turnover_estimate": result.decision.turnover_estimate, "convention": "0.5 × L1"}


def liquidity_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "liquidity_status": result.decision.liquidity_status.value,
        "note": "Unknown liquidity is not treated as infinite.",
    }


def drawdown_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return {
        "drawdown_state": result.decision.drawdown_state.value,
        "capital_state": result.decision.capital_state.value,
    }


def compare_payload(decision_a: str, decision_b: str) -> dict[str, Any]:
    left = get_decision(decision_a)
    right = get_decision(decision_b)
    if left is None or right is None:
        return {"error": "both decisions must exist"}
    return {
        "a": left.decision_id,
        "b": right.decision_id,
        "hash_equal": left.decision_hash == right.decision_hash,
        "weights_a": left.target_weights,
        "weights_b": right.target_weights,
    }


def lineage_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    d = result.decision
    return {
        "decision_id": d.decision_id,
        "snapshot_id": d.snapshot_id,
        "capital_policy_id": d.capital_policy_id,
        "portfolio_spec_id": d.portfolio_spec_id,
        "knowledge_snapshot_id": d.knowledge_snapshot_id,
        "decision_hash": d.decision_hash,
        "software_version": d.software_version,
    }


def abstentions_payload() -> list[dict[str, Any]]:
    rows = []
    for item in list_decisions():
        if item.abstention_code.value != "none":
            rows.append(
                {
                    "decision_id": item.decision_id,
                    "code": item.abstention_code.value,
                    "reason": item.abstention_reason,
                    "stage": item.abstention_stage,
                }
            )
    return rows


def report_payload(decision_id: str) -> dict[str, Any]:
    result = get_result(decision_id)
    if result is None:
        return {"error": "no capital decision yet"}
    return capital_report(result.decision)


def policy_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for item in list_policies():
        rows.append(
            [
                item.policy_id,
                item.base_currency,
                f"{item.starting_capital:.0f}",
                f"{item.target_volatility:.0%}",
                item.sizing_method.value,
            ]
        )
    return rows


def last_decision_row(ledger: ExperimentLedger | None = None) -> dict[str, Any] | None:
    result = last_result()
    if result is not None:
        d = result.decision
        return {
            "id": d.decision_id,
            "status": d.decision_status.value,
            "capital_state": d.capital_state.value,
            "gross": d.gross_target,
            "net": d.net_target,
            "vol": d.expected_volatility,
            "abstention": d.abstention_code.value,
            "hash": d.decision_hash,
        }
    source = ledger or ExperimentLedger(Path(get_settings().experiment_ledger_path))
    runs = [run for run in source.list_runs() if run.selection_stage == "capital_allocation"]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.decision_id or run.id,
        "status": run.decision_status,
        "capital_state": run.capital_state,
        "gross": run.metrics.get("gross_target"),
        "net": run.metrics.get("net_target"),
        "vol": None,
        "abstention": run.abstention_code,
        "hash": run.target_portfolio_hash or run.config_hash,
    }
