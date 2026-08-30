"""In-run evaluation cache keyed by expression hash. Not a second ledger."""

from __future__ import annotations

from quantlab.features.engine import Panel


class ExpressionCache:
    def __init__(self) -> None:
        self.panels: dict[str, Panel] = {}
