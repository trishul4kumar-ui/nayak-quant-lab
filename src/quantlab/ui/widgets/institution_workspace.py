"""Accessible controls and frozen reports for the institutional research desk.

This surface presents data supplied by the page controller. It has no provider,
execution, or broker dependencies; every action leaves through an explicit signal.
"""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

ROLES = (
    ("SUPERVISOR", "Desk Supervisor", "Consolidates the desk's frozen reports."),
    ("BULL", "Bull Analyst", "Tests the supporting investment hypothesis."),
    ("BEAR", "Bear Analyst", "Finds contrary evidence and invalidation."),
    ("NEWS_DOCS", "News / Documents", "Reviews sourced documents and their provenance."),
    ("QUANT", "Quant Research", "Explains approved quantitative evidence."),
    ("RISK", "Risk Officer", "Reviews deterministic risk results."),
    ("EXECUTION_MONITOR", "Execution Monitor", "Reviews paper and shadow reconciliation."),
    ("AUDIT", "Audit / Compliance", "Checks evidence completeness and traceability."),
)

_ALIASES = {
    "DESK_SUPERVISOR": "SUPERVISOR",
    "BULL_ANALYST": "BULL",
    "BEAR_ANALYST": "BEAR",
    "NEWS": "NEWS_DOCS",
    "DOCUMENT_NEWS": "NEWS_DOCS",
    "DOCUMENT_NEWS_ANALYST": "NEWS_DOCS",
    "DOCS_NEWS": "NEWS_DOCS",
    "QUANT_ANALYST": "QUANT",
    "QUANT_RESEARCH": "QUANT",
    "RISK_OFFICER": "RISK",
    "EXECUTION": "EXECUTION_MONITOR",
    "AUDIT_COMPLIANCE": "AUDIT",
    "AUDIT_COMPLIANCE_AGENT": "AUDIT",
}


def _record(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        result = dump(mode="json")
        if isinstance(result, dict):
            return {str(key): item for key, item in result.items()}
    return {}


def _role(value: object) -> str:
    raw = str(getattr(value, "value", value)).upper().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(raw, raw)


def _references(value: object) -> list[str]:
    if not isinstance(value, (tuple, list)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            ref = item
        else:
            data = _record(item)
            ref = str(data.get("artifact_hash", data.get("content_hash", data.get("hash", ""))))
        if ref and ref not in result:
            result.append(ref)
    return result


class InstitutionWorkspace(QWidget):
    """A native companion to the 3D desk, usable by keyboard and screen readers."""

    requestCycle = Signal()
    cancelRequested = Signal()
    questionAsked = Signal(str)
    documentLoadRequested = Signal()
    roleSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("institutionWorkspace")
        self._busy = False
        self._reports: dict[str, dict[str, Any]] = {}
        self._cycle_hash = ""
        self._selected_role = "SUPERVISOR"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)

        heading = QHBoxLayout()
        title = QLabel("INSTITUTIONAL DESK  /  NAYAK")
        title.setObjectName("institutionTitle")
        title.setAccessibleName("Institutional desk and NAYAK research assistant")
        heading.addWidget(title, 1)
        mode = QLabel("RESEARCH · HUMAN REVIEW")
        mode.setObjectName("institutionMode")
        heading.addWidget(mode)
        layout.addLayout(heading)

        self.status = QLabel("Load a snapshot, then run your desk")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.status.setAccessibleName("Institutional desk cycle status")
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)

        controls = QHBoxLayout()
        self.run_button = QPushButton("Run institutional desk")
        self.run_button.setAccessibleName("Run bounded institutional research cycle")
        self.run_button.setToolTip(
            "Review the loaded frozen snapshot in research or explicit replay mode."
        )
        self.run_button.clicked.connect(self._request_cycle)
        controls.addWidget(self.run_button)
        self.document_button = QPushButton("Load documents")
        self.document_button.setToolTip("Load source documents for the news and document analyst.")
        self.document_button.clicked.connect(self._request_documents)
        controls.addWidget(self.document_button)
        self.cancel_button = QPushButton("Cancel cycle")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._request_cancel)
        controls.addWidget(self.cancel_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.input_status = QLabel("Uses the loaded snapshot and available frozen lab evidence.")
        self.input_status.setTextFormat(Qt.TextFormat.PlainText)
        self.input_status.setWordWrap(True)
        self.input_status.setAccessibleName("Institutional desk input availability")
        layout.addWidget(self.input_status)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        reports_panel = QWidget()
        reports_layout = QVBoxLayout(reports_panel)
        reports_layout.setContentsMargins(0, 0, 0, 0)
        self.role_table = QTableWidget(len(ROLES), 3)
        self.role_table.setHorizontalHeaderLabels(["Agent", "State", "Evidence"])
        self.role_table.setAccessibleName(
            "Institutional research team and frozen report availability"
        )
        self.role_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.role_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.role_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.role_table.verticalHeader().hide()
        self.role_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.role_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.role_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.role_table.setMinimumWidth(320)
        self.role_table.setMaximumHeight(258)
        for row, (role, label, purpose) in enumerate(ROLES):
            name = QTableWidgetItem(label)
            name.setData(Qt.ItemDataRole.UserRole, role)
            name.setToolTip(purpose)
            self.role_table.setItem(row, 0, name)
            self.role_table.setItem(row, 1, QTableWidgetItem("AWAITING"))
            self.role_table.setItem(row, 2, QTableWidgetItem("—"))
        self.role_table.itemSelectionChanged.connect(self._selection_changed)
        reports_layout.addWidget(self.role_table)
        self.report = QTextBrowser()
        self.report.setOpenExternalLinks(False)
        self.report.setOpenLinks(False)
        self.report.setAccessibleName(
            "Selected agent's frozen report, claims, and evidence references"
        )
        self.report.setMinimumHeight(140)
        reports_layout.addWidget(self.report, 1)
        self.splitter.addWidget(reports_panel)

        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_title = QLabel("NAYAK  /  ASK YOUR DESK")
        chat_layout.addWidget(chat_title)
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(False)
        self.chat.setOpenLinks(False)
        self.chat.setAccessibleName("NAYAK conversation with citations to frozen desk evidence")
        self.chat.setMinimumHeight(200)
        self.chat.setHtml(
            "<p><b>NAYAK</b></p><p>Run your desk, then ask about the findings, opposing views, "
            "evidence gaps, or paper and shadow results.</p>"
        )
        chat_layout.addWidget(self.chat, 1)
        question_row = QHBoxLayout()
        self.question = QLineEdit()
        self.question.setMaxLength(1200)
        self.question.setPlaceholderText("Ask NAYAK about your desk's evidence…")
        self.question.setAccessibleName("Question for NAYAK about frozen desk evidence")
        self.question.textChanged.connect(self._update_question_button)
        self.question.returnPressed.connect(self._submit_question)
        question_row.addWidget(self.question, 1)
        self.ask_button = QPushButton("Ask NAYAK")
        self.ask_button.setEnabled(False)
        self.ask_button.clicked.connect(self._submit_question)
        question_row.addWidget(self.ask_button)
        chat_layout.addLayout(question_row)
        self.splitter.addWidget(chat_panel)
        self.splitter.setSizes([520, 500])
        layout.addWidget(self.splitter, 1)
        self.role_table.selectRow(0)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.run_button.setEnabled(not busy)
        self.document_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        self.question.setEnabled(not busy)
        self._update_question_button()

    def set_input_status(self, message: str) -> None:
        self.input_status.setText(message)

    def set_error(self, message: str) -> None:
        self.status.setText(message)

    def set_cycle(self, cycle: object) -> None:
        data = _record(cycle)
        self._cycle_hash = str(data.get("content_hash", ""))
        status = str(data.get("status", "AWAITING"))
        summary = str(data.get("summary", "No consolidated report is available."))
        provenance = " · SYNTHETIC REPLAY" if data.get("synthetic") else ""
        self.status.setText(f"{status}{provenance} · {summary}")
        self._reports.clear()
        reports = data.get("reports", [])
        if isinstance(reports, (list, tuple)):
            for value in reports:
                report = _record(value)
                identity = _role(report.get("role", ""))
                if identity in {role for role, _, _ in ROLES}:
                    self._reports[identity] = report
        supervisor = _record(data.get("supervisor_report"))
        if supervisor:
            self._reports["SUPERVISOR"] = supervisor
        for row, (role, _, _) in enumerate(ROLES):
            report = self._reports.get(role, {})
            state_item = self.role_table.item(row, 1)
            evidence_item = self.role_table.item(row, 2)
            assert state_item is not None and evidence_item is not None
            state_item.setText(str(report.get("status", "AWAITING")))
            refs = _references(report.get("evidence_hashes", []))
            report_hash = str(report.get("content_hash", ""))
            evidence_item.setText(str(len(refs)) if refs else ("Frozen" if report_hash else "—"))
        self._render_report()

    def set_progress(self, role: str, status: str, message: str) -> None:
        identity = _role(role)
        for row, (key, label, _) in enumerate(ROLES):
            if key == identity:
                state_item = self.role_table.item(row, 1)
                assert state_item is not None
                state_item.setText(status)
                state_item.setToolTip(message)
                self.status.setText(f"{label} · {status} · {message}")
                break

    def select_role(self, role: str) -> None:
        identity = _role(role)
        if identity in {"NAYAK", "JARVIS"}:
            self.question.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        for row, (key, _, _) in enumerate(ROLES):
            if key == identity:
                self.role_table.selectRow(row)
                name_item = self.role_table.item(row, 0)
                assert name_item is not None
                self.role_table.scrollToItem(name_item)
                break

    def show_answer(self, answer: object) -> None:
        data = _record(answer)
        text = str(
            data.get("answer", data.get("text", data.get("summary", "No answer is available.")))
        )
        status = str(data.get("status", ""))
        refs = _references(
            data.get("citations", data.get("report_hashes", data.get("evidence_hashes", [])))
        )
        self.chat.append(f"<p><b>NAYAK</b> {escape(status)}</p>")
        claims = data.get("claims", [])
        claim_records = (
            [_record(item) for item in claims] if isinstance(claims, (list, tuple)) else []
        )
        if claim_records and all(item.get("text") for item in claim_records):
            for claim in claim_records:
                claim_refs = _references(claim.get("evidence_hashes", []))
                references = " · ".join(escape(ref) for ref in claim_refs)
                self.chat.append(
                    f"<p>{escape(str(claim['text']))}<br><small>{references}</small></p>"
                )
        else:
            self.chat.append(f"<p>{escape(text).replace(chr(10), '<br>')}</p>")
        if refs and not claim_records:
            self.chat.append(
                "<p>Frozen evidence</p><ul>"
                + "".join(f"<li><code>{escape(ref)}</code></li>" for ref in refs)
                + "</ul>"
            )
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def _request_cycle(self) -> None:
        if not self._busy:
            self.requestCycle.emit()

    def _request_documents(self) -> None:
        if not self._busy:
            self.documentLoadRequested.emit()

    def _request_cancel(self) -> None:
        if self._busy:
            self.cancelRequested.emit()

    def _update_question_button(self) -> None:
        self.ask_button.setEnabled(bool(self.question.text().strip()) and not self._busy)

    def _submit_question(self) -> None:
        text = self.question.text().strip()
        if not text or self._busy:
            return
        self.question.clear()
        self.chat.append(f"<p><b>You</b></p><p>{escape(text)}</p>")
        self.questionAsked.emit(text)

    def _selection_changed(self) -> None:
        row = self.role_table.currentRow()
        if 0 <= row < len(ROLES):
            self._selected_role = ROLES[row][0]
            self._render_report()
            self.roleSelected.emit(self._selected_role)

    def _render_report(self) -> None:
        role, label, purpose = next(item for item in ROLES if item[0] == self._selected_role)
        data = self._reports.get(role)
        if not data:
            self.report.setHtml(
                f"<h3>{escape(label)}</h3><p>{escape(purpose)}</p>"
                "<p>Awaiting a frozen report. Run the desk with a loaded snapshot.</p>"
            )
            return
        parts = [
            f"<h3>{escape(label)}</h3>",
            f"<p><b>{escape(str(data.get('status', 'AWAITING')))}</b></p>",
            f"<p>{escape(str(data.get('summary', 'No summary available.')))}</p>",
        ]
        claims = data.get("claims", [])
        if isinstance(claims, (list, tuple)) and claims:
            parts.append("<p><b>Cited research findings</b></p><ul>")
            for item in claims:
                claim = _record(item)
                text = str(
                    claim.get("text", claim.get("claim", item if isinstance(item, str) else ""))
                )
                parts.append(f"<li>{escape(text)}")
                refs = _references(claim.get("evidence_hashes", []))
                if refs:
                    parts.append(
                        "<br><small>" + " · ".join(escape(ref) for ref in refs) + "</small>"
                    )
                parts.append("</li>")
            parts.append("</ul>")
        gaps = data.get("missing_evidence", [])
        if isinstance(gaps, (list, tuple)) and gaps:
            parts.append(
                "<p><b>Evidence gaps</b></p><ul>"
                + "".join(f"<li>{escape(str(gap))}</li>" for gap in gaps)
                + "</ul>"
            )
        error = data.get("error_code")
        if error:
            parts.append(f"<p>Review required: {escape(str(error))}</p>")
        refs = _references(data.get("evidence_hashes", []))
        if refs:
            parts.append(
                "<p><b>Frozen evidence</b></p><ul>"
                + "".join(f"<li><code>{escape(ref)}</code></li>" for ref in refs)
                + "</ul>"
            )
        report_hash = str(data.get("content_hash", ""))
        if report_hash:
            parts.append(f"<p>Report <code>{escape(report_hash)}</code></p>")
        if self._cycle_hash:
            parts.append(f"<p>Desk cycle <code>{escape(self._cycle_hash)}</code></p>")
        self.report.setHtml("".join(parts))
