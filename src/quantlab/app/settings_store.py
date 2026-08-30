"""Window geometry and workspace prefs. Never secrets."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class ExperienceMode(StrEnum):
    GUIDED = "guided"
    FULL = "full"


class UiTheme(StrEnum):
    DARK = "dark"
    LIGHT = "light"


class UiDensity(StrEnum):
    COMFORTABLE = "comfortable"
    COMPACT = "compact"


class UiSettings(BaseModel):
    width: int = 1280
    height: int = 800
    x: int | None = None
    y: int | None = None
    nav: str = "home"
    experience_mode: ExperienceMode = ExperienceMode.GUIDED
    tk_display_name: str = "TK"
    theme: UiTheme = UiTheme.DARK
    density: UiDensity = UiDensity.COMFORTABLE
    milestones: list[str] = Field(default_factory=list)
    visited_pages: list[str] = Field(default_factory=list)
    journal_notes: dict[str, str] = Field(default_factory=dict)
    terminal_layouts: dict[str, dict[str, list[int]]] = Field(default_factory=dict)
    last_lookback: int = 20
    last_top_n: int = 2
    last_cost_bps: float = 10.0
    last_n_days: int = 80
    collapsed_nav_sections: list[str] = Field(default_factory=list)
    sidebar_collapsed: bool = False
    palette_recents: list[str] = Field(default_factory=list)
    broker_adapter: str = ""
    broker_wizard_complete: bool = False
    onboarding_intent: str = ""
    selected_template: str = "cs_momentum_v1"


class UiSettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.current = self.load()

    def load(self) -> UiSettings:
        if not self.path.exists():
            return UiSettings()
        try:
            raw = UiSettings.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return UiSettings()
        if raw.nav == "dashboard":
            raw.nav = "home"
        return raw

    def save(self, settings: UiSettings | None = None) -> None:
        data = settings or self.current
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
        self.current = data
