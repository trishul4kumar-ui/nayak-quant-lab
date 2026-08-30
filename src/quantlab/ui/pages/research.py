from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QPushButton

from quantlab.ui.widgets.lab_shell import LabPageShell


class ResearchPage(LabPageShell):
    def __init__(self, on_run: Callable[[], None]) -> None:
        super().__init__(
            "Research Lab",
            subtitle="The momentum hypothesis that drives your first experiments.",
            nayak_summary=(
                "Hypothesis: names with higher 20-day momentum outperform "
                "on the next bar after costs. "
                "Null: next-bar returns are independent of momentum rank. "
                "A high Sharpe on synthetic drift is architecture validation — not alpha."
            ),
            technical="Genome: rank(zscore(momentum_20)). Fill: next bar. Default costs: 10 bps.",
        )
        run = QPushButton("Open Backtest Lab and run")
        run.setObjectName("primary")
        run.clicked.connect(on_run)
        self.add_toolbar_widget(run)
