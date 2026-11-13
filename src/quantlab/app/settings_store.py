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


class WindowPlacement(BaseModel):
    """Preferred display and normal geometry in Qt logical coordinates."""

    screen_id: str = ""
    x: int = Field(default=40, ge=-100000, le=100000)
    y: int = Field(default=40, ge=-100000, le=100000)
    width: int = Field(default=1280, ge=200, le=16000)
    height: int = Field(default=800, ge=160, le=10000)
    maximized: bool = False


class CompanionPlacement(BaseModel):
    x_fraction: float = Field(default=1.0, ge=0.0, le=1.0)
    y_fraction: float = Field(default=1.0, ge=0.0, le=1.0)
    collapsed: bool = False


class UiSettings(BaseModel):
    ui_layout_schema_version: int = 2
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
    terminal_layouts: dict[str, dict[str, object]] = Field(default_factory=dict)
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
    window_placements: dict[str, WindowPlacement] = Field(default_factory=dict)
    nayak_companion: CompanionPlacement = Field(default_factory=CompanionPlacement)
    research_history_hashes: list[str] = Field(default_factory=list)
    strategy_history_hashes: list[str] = Field(default_factory=list)
    strategy_batch_hash: str = ""
    paper_arrival_history_hashes: list[str] = Field(default_factory=list)
    paper_mark_history_hashes: list[str] = Field(default_factory=list)
    research_result_hashes: dict[str, str] = Field(default_factory=dict)
    paper_workflow_id: str = ""
    paper_opening_cash: float | None = Field(default=None, gt=0)
    internal_account_snapshot_hash: str = ""
    selected_candidate_id: str = ""
    selected_backtest_id: str = ""


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
        if raw.ui_layout_schema_version != 2:
            raw.ui_layout_schema_version = 2
            raw.terminal_layouts = {}
        return raw

    def save(self, settings: UiSettings | None = None) -> None:
        data = settings or self.current
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
        self.current = data
