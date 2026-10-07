"""Native, read-only decision surface for a frozen candidate packet."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from quantlab.trade_candidates.models import CandidateStatus, TradeCandidatePacket
from quantlab.trade_levels.engine import chart_overlay
from quantlab.trade_levels.models import ExitPolicy, TradeLevelPlan


class TradeDecisionConsole(QDialog):
    """Candidate review only; all real-money controls are permanently disabled here."""

    candidateAction = Signal(str, str)

    def __init__(
        self,
        candidate: TradeCandidatePacket,
        plan: TradeLevelPlan,
        exit_policy: ExitPolicy | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Trade Decision Console · {candidate.security_id}")
        self.setMinimumSize(720, 520)
        self.resize(1120, 760)
        layout = QVBoxLayout(self)
        stale = datetime.now(UTC) >= candidate.expires_at
        status = "STALE — refresh required" if stale else candidate.status.value
        header = QLabel(
            f"{candidate.security_id} · {candidate.stance} · {status}\n"
            f"Reference {candidate.reference_price:g} · {candidate.data_freshness} · "
            f"Bull raw {candidate.raw_bull_confidence:.2f} / "
            f"Bear raw {candidate.raw_bear_confidence:.2f} · "
            "NO LIVE ORDER AUTHORITY"
        )
        header.setWordWrap(True)
        header.setAccessibleName("Candidate status and research-only decision header")
        layout.addWidget(header)
        tabs = QTabWidget()
        tabs.addTab(self._chart_tab(plan, exit_policy), "Levels / Chart")
        tabs.addTab(self._evidence_tab(candidate), "Research / Analytics")
        tabs.addTab(self._provenance_tab(candidate, plan), "Provenance / Audit")
        layout.addWidget(tabs, 1)
        controls = QHBoxLayout()
        for label, action in (
            ("REJECT", "REJECTED"),
            ("WATCH", "WATCHED"),
            ("REFRESH ANALYSIS", "REFRESH_REQUESTED"),
            ("RUN MORE VALIDATION", "MORE_VALIDATION_REQUESTED"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, value=action: self._emit_action(value))
            controls.addWidget(button)
        paper = QPushButton("APPROVE FOR PAPER")
        paper.setEnabled(not stale and candidate.status is CandidateStatus.READY_FOR_REVIEW)
        paper.setToolTip("Candidate lifecycle only; no order is created in Phase 46")
        paper.clicked.connect(lambda: self._emit_action("PAPER_APPROVED"))
        controls.addWidget(paper)
        for label in ("APPROVE & STAGE", "PLACE ORDER"):
            button = QPushButton(label)
            button.setEnabled(False)
            button.setToolTip("Disabled until Phase 53 and explicit human-bound authorization")
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        close.accepted.connect(self.accept)
        layout.addWidget(close)

    def _emit_action(self, action: str) -> None:
        self.candidateAction.emit(action, self.windowTitle())

    @staticmethod
    def _chart_tab(plan: TradeLevelPlan, exit_policy: ExitPolicy | None) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        overlay = chart_overlay(plan)
        chart = QTextBrowser()
        chart.setAccessibleName("Immutable level plan chart representation")
        chart.setPlainText(
            "APPROVED CHART REPRESENTATION — no candles are fabricated\n\n"
            f"Entry zone: {overlay.entry_zone_low} — {overlay.entry_zone_high}\n"
            f"Hard invalidation: {overlay.hard_invalidation}\n"
            f"Protective stop: {overlay.protective_stop}\n"
            f"Targets: {', '.join(str(item) for item in overlay.targets) or 'None'}\n"
            f"Trailing rule: {overlay.trailing_rule or 'None'}\n"
            f"Time horizon: {overlay.time_horizon or 'None'}\n\n"
            "EXIT POLICY\n"
            + (
                "\n".join(f"{rule.rule}: {rule.condition}" for rule in exit_policy.rules)
                if exit_policy
                else "No entry / no exit policy"
            )
        )
        layout.addWidget(chart)
        return panel

    @staticmethod
    def _evidence_tab(candidate: TradeCandidatePacket) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        details = QTextBrowser()
        details.setAccessibleName("Candidate evidence summaries and unknown values")
        details.setPlainText(
            "BULL / BEAR RESEARCH\n"
            f"Raw Bull confidence: {candidate.raw_bull_confidence:.2f}\n"
            f"Raw Bear confidence: {candidate.raw_bear_confidence:.2f}\n"
            f"Calibrated confidence: {candidate.calibrated_confidence}\n\n"
            + "\n\n".join(
                f"{item.category} · {item.status}\n{item.summary}\n"
                + "\n".join(item.evidence_refs)
                for item in candidate.summaries
            )
            + "\n\nHARD BLOCKERS\n"
            + ("\n".join(candidate.hard_blockers) or "None")
            + "\n\nNOT TESTED\n"
            + ("\n".join(candidate.not_tested) or "None")
        )
        layout.addWidget(details)
        return panel

    @staticmethod
    def _provenance_tab(candidate: TradeCandidatePacket, plan: TradeLevelPlan) -> QWidget:
        panel = QWidget()
        layout = QGridLayout(panel)
        values = {
            "Candidate": candidate.content_hash,
            "Snapshot": candidate.snapshot_hash,
            "Bull memo": candidate.bull_memo_hash,
            "Bear memo": candidate.bear_memo_hash,
            "Debate": candidate.debate_hash,
            "Adjudication": candidate.adjudication_hash,
            "Level plan": plan.content_hash,
            "Policy": candidate.candidate_policy_hash,
        }
        for row, (label, value) in enumerate(values.items()):
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(QLabel(value), row, 1)
        return panel
