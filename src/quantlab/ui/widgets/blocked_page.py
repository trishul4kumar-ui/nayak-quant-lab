"""Designed blocked-state pages for Operate section."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.ui.widgets.lab_shell import LabPageShell, StatusBadge


class BlockedLabPage(LabPageShell):
    def __init__(
        self,
        title: str,
        *,
        summary: str,
        reasons: list[str],
        requirements: list[tuple[str, bool]],
    ) -> None:
        super().__init__(
            title,
            subtitle="Research mode — live paths stay closed until every gate passes.",
            nayak_summary=summary,
        )
        body = self.body()
        badge_row = StatusBadge("blocked", text="LIVE ORDERING BLOCKED")
        body.addWidget(badge_row)

        why = QLabel("Why this is blocked")
        why.setStyleSheet("font-weight: 600; margin-top: 8px;")
        body.addWidget(why)
        for reason in reasons:
            line = QLabel(f"• {reason}")
            line.setWordWrap(True)
            line.setObjectName("nayakVoice")
            body.addWidget(line)

        req_title = QLabel("What would need to be true")
        req_title.setStyleSheet("font-weight: 600; margin-top: 12px;")
        body.addWidget(req_title)
        for label, met in requirements:
            mark = "✓" if met else "✗"
            line = QLabel(f"{mark}  {label}")
            line.setObjectName("nayakVoice")
            body.addWidget(line)
        body.addStretch()
