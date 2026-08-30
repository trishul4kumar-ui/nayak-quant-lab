"""Plain-language metric explanations for TK (NAYAK teacher layer)."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

EXPLANATIONS: dict[str, str] = {
    "sharpe": (
        "Return per unit of risk. Above 1.0 is often interesting on real data. "
        "On synthetic drift, lower values are normal — do not over-celebrate."
    ),
    "total_return": "How much the portfolio grew over the test window, before judging risk.",
    "max_drawdown": "Worst peak-to-trough loss. Smaller (less negative) is usually safer.",
    "momentum_20": (
        "20-day price trend. Positive means the name rose recently — "
        "a simple momentum feature, not a guarantee."
    ),
    "look_ahead_bias": (
        "Accidental use of future data. PASS means the backtest did not peek ahead."
    ),
    "cost_bps": "Trading cost in basis points (1 bp = 0.01%). Default 10 bps = 0.10% per trade.",
    "equity_curve": (
        "Portfolio value through time. Shape matters more than the final point alone."
    ),
    "close": "Last synthetic price for the instrument at the as-of timestamp.",
    "volume": "Shares traded in the bar. Higher volume often means easier simulated fills.",
    "regime": (
        "Descriptive market state label — not a forecast. "
        "Regimes summarize conditions, they do not predict tomorrow."
    ),
    "integrity": "Research integrity checks. FAIL blocks promotion to live trading.",
    "validation": (
        "Stricter tests than a single backtest: walk-forward, robustness, bootstrap, gate."
    ),
    "gate_outcome": "Research gate verdict. Synthetic-only runs cannot promote to live.",
    "n_days": "Number of synthetic trading days in the simulation window.",
    "lookback": "Momentum lookback in days (how far back we measure trend).",
    "top_n": "How many names we hold each rebalance (cross-sectional basket size).",
}


def glossary_entries() -> list[tuple[str, str]]:
    """Sorted (key, explanation) pairs for the metrics glossary."""
    return sorted(EXPLANATIONS.items(), key=lambda item: item[0])


class ExplainChip(QWidget):
    """Small ? control — NAYAK explains a metric on click or hover."""

    def __init__(self, explain_key: str, *, label: str | None = None) -> None:
        super().__init__()
        self._key = explain_key
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        if label:
            title = QLabel(label)
            title.setStyleSheet("font-weight: 600;")
            layout.addWidget(title)
        btn = QPushButton("?")
        btn.setFixedSize(22, 22)
        btn.setToolTip("Explain this")
        btn.setStyleSheet(
            "QPushButton { background: #2a3144; border: none; "
            "border-radius: 11px; font-weight: 700; font-size: 11px; color: #6ba3b8; }"
            "QPushButton:hover { background: #3d5a6a; }"
        )
        text = EXPLANATIONS.get(explain_key, "No explanation loaded yet.")
        btn.clicked.connect(
            lambda: QMessageBox.information(self.window(), f"About {explain_key}", text)
        )
        layout.addWidget(btn)
        layout.addStretch()

    @staticmethod
    def text_for(key: str) -> str:
        return EXPLANATIONS.get(key, "")
