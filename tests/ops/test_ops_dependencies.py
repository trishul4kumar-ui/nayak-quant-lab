from __future__ import annotations

from quantlab.ops.dependencies import validate


def test_unexpected_dependency() -> None:
    missing = validate({"ledger", "broker"})
    assert "broker" in missing or "health" in missing
