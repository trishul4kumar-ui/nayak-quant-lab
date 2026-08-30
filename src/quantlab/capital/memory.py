"""In-process capital decision store. Optional JSON beside the ledger."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.capital.allocator import AllocationResult
from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.core.config import get_settings

_DECISIONS: dict[str, InvestmentDecision] = {}
_TARGETS: dict[str, TargetPortfolio] = {}
_RESULTS: dict[str, AllocationResult] = {}
_LAST: str | None = None


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("capital_decisions.json")


def register(result: AllocationResult) -> AllocationResult:
    global _LAST
    decision = result.decision
    _DECISIONS[decision.decision_id] = decision
    _TARGETS[decision.decision_id] = result.target
    _RESULTS[decision.decision_id] = result
    _LAST = decision.decision_id
    return result


def get_decision(decision_id: str) -> InvestmentDecision | None:
    if decision_id in _DECISIONS:
        return _DECISIONS[decision_id]
    if _LAST and decision_id in {"", "last"}:
        return _DECISIONS.get(_LAST)
    prefix = [item for item in _DECISIONS if item.startswith(decision_id)]
    if len(prefix) == 1:
        return _DECISIONS[prefix[0]]
    return _DECISIONS.get(decision_id)


def get_result(decision_id: str) -> AllocationResult | None:
    decision = get_decision(decision_id)
    if decision is None:
        if _LAST:
            return _RESULTS.get(_LAST)
        return None
    return _RESULTS.get(decision.decision_id)


def last_decision() -> InvestmentDecision | None:
    if _LAST is None:
        return None
    return _DECISIONS.get(_LAST)


def last_result() -> AllocationResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)


def list_decisions() -> list[InvestmentDecision]:
    return list(_DECISIONS.values())


def persist(path: Path | None = None) -> None:
    target = path or default_path()
    payload = {
        "last": _LAST,
        "decisions": [item.model_dump(mode="json") for item in _DECISIONS.values()],
        "targets": [item.model_dump(mode="json") for item in _TARGETS.values()],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def reset() -> None:
    global _LAST
    _DECISIONS.clear()
    _TARGETS.clear()
    _RESULTS.clear()
    _LAST = None
