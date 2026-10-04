"""Accessible neutral decision inspector; evidence scores are not trade instructions."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantlab.agents.adjudication_contracts import AdjudicationDecision


class AdjudicationWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel("No adjudication yet · NO_TRADE until evidence is evaluated")
        self.summary.setWordWrap(True)
        self.summary.setAccessibleName("Neutral adjudication outcome and no trade state")
        layout.addWidget(self.summary)
        controls = QHBoxLayout()
        self.run_button = QPushButton("Evaluate selected transcript")
        self.run_button.setToolTip("Deterministic policy only · zero model calls · no order")
        self.history = QComboBox()
        self.history.setAccessibleName("Saved immutable adjudication decisions")
        controls.addWidget(self.run_button)
        controls.addWidget(self.history, 1)
        layout.addLayout(controls)
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.components = QTreeWidget()
        self.components.setHeaderLabels(
            ["Role / component", "Canonical status", "Normalized evidence"]
        )
        self.components.setAccessibleName("Adjudication score components and canonical status")
        self.components.setColumnWidth(0, 260)
        self.components.setColumnWidth(1, 140)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(False)
        self.details.setAccessibleName(
            "Adjudication blockers warnings policy and immutable lineage"
        )
        self.splitter.addWidget(self.components)
        self.splitter.addWidget(self.details)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([300, 200])
        layout.addWidget(self.splitter, 1)

    def display(self, decision: AdjudicationDecision, *, expired: bool) -> None:
        disposition = "NO_TRADE" if decision.no_trade else "RESEARCH PROCESSING ONLY"
        currency = (
            "Historical / expired — re-evaluation required" if expired else "Frozen evaluation"
        )
        self.summary.setText(
            f"{decision.outcome} · {disposition}\n"
            f"Bull {decision.bull_score:.2f} / Bear {decision.bear_score:.2f} · "
            f"{len(decision.hard_blockers)} blockers · "
            f"{currency} · "
            "NO EXECUTION AUTHORITY"
        )
        self.components.clear()
        for component in decision.score_components:
            item = QTreeWidgetItem(
                [
                    f"{component.role} / {component.name}",
                    component.status.value,
                    "",
                ]
            )
            item.setToolTip(0, "\n".join(component.evidence_refs))
            self.components.addTopLevelItem(item)
            bar = QProgressBar()
            bar.setRange(0, 10000)
            bar.setValue(round(10000 * (component.normalized_value or 0)))
            bar.setFormat(
                f"{component.points:.2f} pts / weight {component.weight:.2f}"
                if component.normalized_value is not None
                else "NOT SCORED — missing/failed evidence"
            )
            bar.setAccessibleName(f"{component.role} {component.name} {component.status}")
            self.components.setItemWidget(item, 2, bar)
        self.details.setPlainText(
            "HARD BLOCKERS\n"
            + ("\n".join(decision.hard_blockers) or "None")
            + "\n\nWARNINGS\n"
            + "\n".join(decision.warnings)
            + f"\n\nPOLICY {decision.policy_id}\n{decision.policy_hash}"
            + f"\nDECISION\n{decision.content_hash}\nQUANTITATIVE RESULT\n{decision.result_hash}"
            + f"\nINPUT\n{decision.input_hash}\nTRANSCRIPT\n{decision.transcript_hash}"
            + "\n\nEVIDENCE REFERENCES\n"
            + "\n".join(decision.evidence_refs)
        )
