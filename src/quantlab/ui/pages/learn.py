from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
)

from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.learn_content import LEARN_TOUR_TABS, LearnStage, learn_progress, unlocked_stages
from quantlab.ui.widgets import ExplainChip
from quantlab.ui.widgets.explain import glossary_entries
from quantlab.ui.widgets.lab_shell import LabPageShell


class LearnPage(LabPageShell):
    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        on_nav: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            "Learn",
            subtitle="Staged quant concepts — new sections unlock as you complete experiments.",
        )
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)
        self._on_nav = on_nav

        body = self.body()
        self._progress_label = QLabel()
        self._progress_label.setObjectName("nayakVoice")
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%v / %m stages unlocked")
        self._milestone_list = QLabel()
        self._milestone_list.setWordWrap(True)
        self._milestone_list.setObjectName("nayakVoice")
        progress_frame = QFrame()
        progress_frame.setObjectName("card")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(16, 14, 16, 14)
        progress_head = QLabel("Your learning path")
        progress_head.setStyleSheet("font-weight: 600;")
        progress_layout.addWidget(progress_head)
        progress_layout.addWidget(self._progress_label)
        progress_layout.addWidget(self._progress_bar)
        progress_layout.addWidget(self._milestone_list)
        body.addWidget(progress_frame)

        tour_frame = QFrame()
        tour_frame.setObjectName("card")
        tour_layout = QVBoxLayout(tour_frame)
        tour_layout.setContentsMargins(16, 14, 16, 14)
        tour_head = QLabel("Platform tour")
        tour_head.setStyleSheet("font-weight: 600;")
        tour_layout.addWidget(tour_head)
        self._tour_tabs = QTabWidget()
        for tab in LEARN_TOUR_TABS:
            page = QFrame()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(8, 8, 8, 8)
            body_lbl = QLabel(tab.body)
            body_lbl.setWordWrap(True)
            body_lbl.setObjectName("nayakVoice")
            go = QPushButton(f"{tab.action_label} →")
            go.setObjectName("primary")
            nav_key = tab.nav_key
            go.clicked.connect(lambda checked=False, key=nav_key: self._go_tab(key))
            page_layout.addWidget(body_lbl)
            page_layout.addWidget(go, alignment=Qt.AlignmentFlag.AlignLeft)
            self._tour_tabs.addTab(page, tab.title)
        tour_layout.addWidget(self._tour_tabs)
        body.addWidget(tour_frame)

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_body = QVBoxLayout()
        self._scroll_body.setSpacing(20)
        container = QFrame()
        container.setObjectName("learnScrollBody")
        container.setLayout(self._scroll_body)
        scroll.setWidget(container)
        body.addWidget(scroll, 1)

        glossary_frame = QFrame()
        glossary_frame.setObjectName("card")
        glossary_layout = QVBoxLayout(glossary_frame)
        glossary_layout.setContentsMargins(16, 14, 16, 14)
        glossary_head = QLabel("Metrics glossary")
        glossary_head.setStyleSheet("font-weight: 600;")
        glossary_sub = QLabel(
            "Every ? chip in the lab links here — plain language, no jargon wall."
        )
        glossary_sub.setWordWrap(True)
        glossary_sub.setObjectName("nayakVoice")
        glossary_layout.addWidget(glossary_head)
        glossary_layout.addWidget(glossary_sub)
        for key, text in glossary_entries():
            row = QVBoxLayout()
            row.setSpacing(4)
            row.addWidget(ExplainChip(key, label=key.replace("_", " ").title()))
            body_lbl = QLabel(text)
            body_lbl.setWordWrap(True)
            body_lbl.setObjectName("nayakVoice")
            body_lbl.setStyleSheet("margin-left: 4px; padding-bottom: 8px;")
            glossary_layout.addLayout(row)
            glossary_layout.addWidget(body_lbl)
        body.addWidget(glossary_frame)
        self.refresh()

    def _go_tab(self, nav_key: str) -> None:
        if self._on_nav is not None:
            self._on_nav(nav_key)

    def refresh(self) -> None:
        milestones = set(self._runtime.ui_settings.current.milestones)
        unlocked, total, rows = learn_progress(milestones)
        self._progress_label.setText(
            f"{self._assistant.tk_name}, {unlocked} of {total} learning stages unlocked. "
            "Complete experiments in the Test wizard to open more."
        )
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(unlocked)
        milestone_lines: list[str] = []
        for stage, ok in rows:
            mark = "✓" if ok else "○"
            milestone_lines.append(f"{mark} {stage.title}")
        self._milestone_list.setText("\n".join(milestone_lines))

        stages = unlocked_stages(milestones)
        while self._scroll_body.count():
            item = self._scroll_body.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for stage in stages:
            self._scroll_body.addWidget(self._stage_block(stage))

    def _stage_block(self, stage: LearnStage) -> QFrame:
        frame = QFrame()
        frame.setObjectName("learnCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        head = QLabel(stage.title)
        head.setStyleSheet("font-size: 16px; font-weight: 600;")
        sub = QLabel(stage.subtitle)
        sub.setStyleSheet("color: #6ba3b8; font-size: 12px;")
        layout.addWidget(head)
        layout.addWidget(sub)
        for topic in stage.topics:
            if topic.explain_key:
                layout.addWidget(ExplainChip(topic.explain_key, label=topic.heading))
            else:
                lbl = QLabel(topic.heading)
                lbl.setStyleSheet("font-weight: 600;")
                layout.addWidget(lbl)
            body = QLabel(topic.body)
            body.setWordWrap(True)
            body.setObjectName("nayakVoice")
            layout.addWidget(body)
        return frame
