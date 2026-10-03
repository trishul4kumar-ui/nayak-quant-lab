from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

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

        research_frame = QFrame()
        research_frame.setObjectName("card")
        research_layout = QVBoxLayout(research_frame)
        research_layout.setContentsMargins(16, 14, 16, 14)
        research_title = QLabel("Research brief")
        research_title.setObjectName("sectionTitle")
        research_body = QLabel(
            "This workspace records the hypothesis before a run. "
            "The next step produces a synthetic backtest and writes evidence to the ledger."
        )
        research_body.setObjectName("nayakVoice")
        research_body.setWordWrap(True)
        research_layout.addWidget(research_title)
        research_layout.addWidget(research_body)
        self.body().addWidget(research_frame)

        next_frame = QFrame()
        next_frame.setObjectName("terminalPanel")
        next_layout = QVBoxLayout(next_frame)
        next_layout.setContentsMargins(16, 14, 16, 14)
        next_title = QLabel("Next action")
        next_title.setObjectName("sectionTitle")
        next_body = QLabel("Open Backtest Lab to test the default momentum hypothesis.")
        next_body.setObjectName("nayakVoice")
        next_body.setWordWrap(True)
        next_run = QPushButton("Open Backtest Lab")
        next_run.setObjectName("primary")
        next_run.clicked.connect(on_run)
        next_layout.addWidget(next_title)
        next_layout.addWidget(next_body)
        next_layout.addWidget(next_run)
        self.body().addWidget(next_frame)
