"""Native research workspace: resizable evidence, challenges and searchable history."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QListWidget,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from quantlab.agents.research import BullResearchMemo


class AnalystWorkspace(QWidget):
    historySelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.task = QLabel("No analyst runs yet · load or capture a healthy snapshot to start.")
        self.task.setWordWrap(True)
        layout.addWidget(self.task)
        self.scope = QLabel("Research only · final quantity and order prices unavailable")
        self.scope.setWordWrap(True)
        layout.addWidget(self.scope)
        vertical = QSplitter(Qt.Orientation.Vertical)
        horizontal = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter = vertical
        self.evidence_splitter = horizontal
        self.support = self._panel("Supporting evidence")
        self.contradictions = self._panel("Contradictions / unresolved evidence")
        horizontal.addWidget(self.support)
        horizontal.addWidget(self.contradictions)
        horizontal.setChildrenCollapsible(False)
        vertical.addWidget(horizontal)
        self.tabs = QTabWidget()
        self.memo = self._panel("Frozen research memo")
        self.challenge = self._panel("Self-falsification and uncertainties")
        self.timeline = self._panel("Actual tool and state timeline")
        for widget, title in (
            (self.memo, "Memo"),
            (self.challenge, "Challenge"),
            (self.timeline, "Timeline"),
        ):
            self.tabs.addTab(widget, title)
        history = QWidget()
        history_layout = QVBoxLayout(history)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search scope, thesis, invalidation, factor exposure…")
        self.search.setAccessibleName("Search Bull research history")
        self.history = QListWidget()
        self.history.setAccessibleName("Previous Bull hypotheses; outcomes not yet measured")
        self.search.textChanged.connect(self._filter)
        self.history.currentRowChanged.connect(self._select)
        history_layout.addWidget(self.search)
        history_layout.addWidget(self.history)
        self.tabs.addTab(history, "History")
        vertical.addWidget(self.tabs)
        vertical.setChildrenCollapsible(False)
        vertical.setSizes([220, 360])
        layout.addWidget(vertical, 1)
        self._history_hashes: list[str] = []
        self._search_text: list[str] = []

    @staticmethod
    def _panel(name: str) -> QTextBrowser:
        panel = QTextBrowser()
        panel.setAccessibleName(name)
        panel.setOpenExternalLinks(False)
        panel.setMinimumHeight(110)
        return panel

    def show_memo(self, memo: BullResearchMemo) -> None:
        self.scope.setText(
            f"{memo.data_kind} · {memo.as_of.isoformat()} · "
            + ", ".join(memo.security_scope)
            + f" · validation: {memo.validation}"
        )
        self.memo.setPlainText(
            f"{memo.stance} · RESEARCH ONLY\n\n{memo.thesis.hypothesis}\n\n"
            f"Rationale\n{memo.thesis.economic_rationale}\n\nHorizon: {memo.thesis.horizon}\n"
            f"Entry archetype: {memo.preferred_entry_archetype}\n"
            f"Exit archetype: {memo.preferred_exit_archetype}\n"
            f"Raw confidence (opinion): {memo.raw_confidence:.0%}\n"
            "Calibrated confidence: NOT_TESTED\nRealized outcome: NOT_TESTED\n"
            f"{memo.no_trade_reason or ''}\n\nMemo hash: {memo.content_hash}"
        )
        self.support.setPlainText(
            "SUPPORT · interpretations unverified\n\n"
            + "\n\n".join(
                f"{ref.kind}: {ref.status}\n{ref.artifact_hash}" for ref in memo.evidence_for
            )
        )
        self.contradictions.setPlainText(
            "CONTRADICTIONS / EVIDENCE GAPS\n\n"
            + "\n\n".join(
                f"{ref.kind}: {ref.status}\n{ref.artifact_hash}" for ref in memo.evidence_against
            )
            + "\n\n"
            + "\n".join(f"{row.name}: {row.status}" for row in memo.evidence_sections)
        )
        self.challenge.setPlainText(
            "AGENT INTERPRETATION · not independently verified\n\n"
            + "\n\n".join(f"{row.question}\n{row.answer}" for row in memo.self_falsification)
            + "\n\nINVALIDATION\n"
            + "\n".join(memo.thesis.invalidation_conditions)
            + "\n\nUNCERTAINTY\n"
            + "\n".join(row.description for row in memo.uncertainties)
        )

    def set_history(self, memos: tuple[BullResearchMemo, ...]) -> None:
        previous = self.history.currentRow()
        self.history.blockSignals(True)
        self.history.clear()
        self._history_hashes = []
        self._search_text = []
        for memo in reversed(memos[-100:]):
            self.history.addItem(
                f"{memo.created_at:%Y-%m-%d %H:%M} · {memo.stance} · "
                + ", ".join(memo.security_scope)
            )
            self._history_hashes.append(memo.content_hash)
            self._search_text.append(memo.model_dump_json().casefold())
        self.history.setCurrentRow(previous)
        self.history.blockSignals(False)
        self._filter(self.search.text())

    def _filter(self, text: str) -> None:
        for index, haystack in enumerate(self._search_text):
            self.history.item(index).setHidden(text.casefold() not in haystack)

    def _select(self, index: int) -> None:
        if 0 <= index < len(self._history_hashes):
            self.historySelected.emit(self._history_hashes[index])
