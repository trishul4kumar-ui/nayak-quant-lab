from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.settings_store import ExperienceMode, UiDensity, UiTheme
from quantlab.ui.navigation import FULL_NAV, NAV_FILTER_SHORTCUT, NAV_SHORTCUTS, SHORTCUT_CONFLICT_NOTES, shortcut_label
from quantlab.ui.widgets.lab_shell import LabPageShell


def _shortcut_help_text() -> str:
    lines = [
        "Navigation",
        "« / » — collapse or expand the sidebar (icon rail in Full Lab)",
        "Click section headers — collapse or expand Research / Validate / Execute groups",
        "⌘K / Ctrl+K — command palette (pages, actions, experiment search)",
        "Enter — open first sidebar filter match · Esc — clear sidebar filter",
        f"{NAV_FILTER_SHORTCUT.replace('Meta+', '⌘').replace('Meta', '⌘')} — focus sidebar page filter",
        "",
        "macOS shortcut notes",
        *SHORTCUT_CONFLICT_NOTES,
        "",
        "Home Pulse (Full Lab)",
        "Click any Pulse card to jump to that area · cards refresh while jobs run",
        "",
        "Status footer",
        "MODE · LIVE · BROKER — detailed ops status lives on Home Pulse",
        "",
        "Density",
        "Comfortable — roomier page margins · Compact — tighter layout for small screens",
        "",
        "Full Lab page shortcuts",
    ]
    for item in FULL_NAV:
        if item.header:
            continue
        hint = shortcut_label(item.key)
        if hint:
            lines.append(f"{hint} — {item.label}")
    return "\n".join(lines)


class SettingsPage(LabPageShell):
    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        on_theme_change: Callable[[UiTheme], None] | None = None,
        on_name_change: Callable[[], None] | None = None,
        on_density_change: Callable[[UiDensity], None] | None = None,
    ) -> None:
        super().__init__(
            "Settings",
            subtitle="Personalize your lab without touching secrets or live credentials.",
            nayak_summary=(
                "Your display name, theme, and launch mode live here. "
                "Terminal panel sizes save automatically when you resize splitters."
            ),
        )
        self._runtime = runtime
        self._on_theme_change = on_theme_change
        self._on_name_change = on_name_change
        self._on_density_change = on_density_change
        body = self.body()

        def card(title: str) -> tuple[QFrame, QVBoxLayout]:
            from PySide6.QtWidgets import QLabel, QVBoxLayout

            frame = QFrame()
            frame.setObjectName("card")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 14, 16, 14)
            head = QLabel(title)
            head.setStyleSheet("font-weight: 600;")
            layout.addWidget(head)
            return frame, layout

        from PySide6.QtWidgets import QLabel, QVBoxLayout

        profile, profile_layout = card("Profile")
        name_row = QHBoxLayout()
        self._name_input = QLineEdit()
        self._name_save = QPushButton("Save")
        self._name_save.clicked.connect(self._save_name)
        name_row.addWidget(QLabel("Display name"))
        name_row.addWidget(self._name_input, 1)
        name_row.addWidget(self._name_save)
        profile_layout.addLayout(name_row)
        body.addWidget(profile)

        appearance, appearance_layout = card("Appearance")
        theme_row = QHBoxLayout()
        self._dark_btn = QPushButton("Dark")
        self._dark_btn.setCheckable(True)
        self._light_btn = QPushButton("Light")
        self._light_btn.setCheckable(True)
        self._dark_btn.clicked.connect(lambda: self._set_theme(UiTheme.DARK))
        self._light_btn.clicked.connect(lambda: self._set_theme(UiTheme.LIGHT))
        theme_row.addWidget(QLabel("Theme"))
        theme_row.addWidget(self._dark_btn)
        theme_row.addWidget(self._light_btn)
        theme_row.addStretch()
        appearance_layout.addLayout(theme_row)
        density_row = QHBoxLayout()
        self._comfortable_btn = QPushButton("Comfortable")
        self._comfortable_btn.setCheckable(True)
        self._compact_btn = QPushButton("Compact")
        self._compact_btn.setCheckable(True)
        self._comfortable_btn.clicked.connect(lambda: self._set_density(UiDensity.COMFORTABLE))
        self._compact_btn.clicked.connect(lambda: self._set_density(UiDensity.COMPACT))
        density_row.addWidget(QLabel("Density"))
        density_row.addWidget(self._comfortable_btn)
        density_row.addWidget(self._compact_btn)
        density_row.addStretch()
        appearance_layout.addLayout(density_row)
        body.addWidget(appearance)

        lab, lab_layout = card("Lab mode")
        launch_row = QHBoxLayout()
        self._launch_guided = QPushButton("Guided Lab")
        self._launch_full = QPushButton("Full Lab")
        self._launch_guided.setCheckable(True)
        self._launch_full.setCheckable(True)
        self._launch_guided.clicked.connect(lambda: self._set_launch_mode(ExperienceMode.GUIDED))
        self._launch_full.clicked.connect(lambda: self._set_launch_mode(ExperienceMode.FULL))
        launch_row.addWidget(QLabel("Default on launch"))
        launch_row.addWidget(self._launch_guided)
        launch_row.addWidget(self._launch_full)
        launch_row.addStretch()
        lab_layout.addLayout(launch_row)
        history_row = QHBoxLayout()
        clear_recents = QPushButton("Clear palette recents")
        clear_recents.setToolTip("Clears ⌘K palette recents — not your journal, experiments, or assistant hints.")
        clear_recents.clicked.connect(self._clear_palette_recents)
        history_row.addWidget(clear_recents)
        history_row.addStretch()
        lab_layout.addLayout(history_row)
        body.addWidget(lab)

        shortcuts, shortcuts_layout = card("Keyboard shortcuts")
        shortcut_text = QLabel(_shortcut_help_text())
        shortcut_text.setObjectName("nayakVoice")
        shortcut_text.setWordWrap(True)
        shortcuts_layout.addWidget(shortcut_text)
        body.addWidget(shortcuts)

        self._info = QLabel()
        self._info.setWordWrap(True)
        self._info.setObjectName("nayakVoice")
        body.addWidget(self._info)
        body.addStretch()
        self.refresh()

    def _save_name(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            return
        prefs = self._runtime.ui_settings.current
        prefs.tk_display_name = name
        self._runtime.ui_settings.save()
        if self._on_name_change is not None:
            self._on_name_change()
        self.refresh()

    def _set_theme(self, theme: UiTheme) -> None:
        prefs = self._runtime.ui_settings.current
        if prefs.theme is theme:
            return
        prefs.theme = theme
        self._runtime.ui_settings.save()
        if self._on_theme_change is not None:
            self._on_theme_change(theme)
        self.refresh()

    def _set_launch_mode(self, mode: ExperienceMode) -> None:
        prefs = self._runtime.ui_settings.current
        prefs.experience_mode = mode
        self._runtime.ui_settings.save()
        self.refresh()

    def _set_density(self, density: UiDensity) -> None:
        prefs = self._runtime.ui_settings.current
        if prefs.density is density:
            return
        prefs.density = density
        self._runtime.ui_settings.save()
        if self._on_density_change is not None:
            self._on_density_change(density)
        self.refresh()

    def _clear_palette_recents(self) -> None:
        prefs = self._runtime.ui_settings.current
        prefs.palette_recents.clear()
        self._runtime.ui_settings.save()
        self.refresh()

    def _palette_recents_summary(self, recents: list[str]) -> str:
        if not recents:
            return "none yet"
        labels: list[str] = []
        for command_id in recents[:6]:
            if command_id.startswith("nav:"):
                labels.append(command_id[4:].replace("_", " ").title())
            elif command_id.startswith("action:"):
                labels.append(command_id[7:].replace("_", " "))
            elif command_id.startswith("experiment:"):
                labels.append(f"experiment {command_id[11:19]}")
            else:
                labels.append(command_id)
        return ", ".join(labels)

    def refresh(self) -> None:
        prefs = self._runtime.ui_settings.current
        self._name_input.setText(prefs.tk_display_name)
        self._dark_btn.setChecked(prefs.theme is UiTheme.DARK)
        self._light_btn.setChecked(prefs.theme is UiTheme.LIGHT)
        self._launch_guided.setChecked(prefs.experience_mode is ExperienceMode.GUIDED)
        self._launch_full.setChecked(prefs.experience_mode is ExperienceMode.FULL)
        self._comfortable_btn.setChecked(prefs.density is UiDensity.COMFORTABLE)
        self._compact_btn.setChecked(prefs.density is UiDensity.COMPACT)
        milestones = ", ".join(prefs.milestones) if prefs.milestones else "none yet"
        recents = self._palette_recents_summary(prefs.palette_recents)
        self._info.setText(
            f"Milestones: {milestones}\n"
            f"Palette recents: {recents}\n"
            f"Data directory: {self._runtime.paths.root}"
        )
