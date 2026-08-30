"""JSON serialization for capital decisions. Not a second ledger."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio


def dump_decision(decision: InvestmentDecision) -> str:
    return decision.model_dump_json(indent=2)


def dump_target(target: TargetPortfolio) -> str:
    return target.model_dump_json(indent=2)


def load_decision(raw: str) -> InvestmentDecision:
    return InvestmentDecision.model_validate(json.loads(raw))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
