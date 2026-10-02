"""NAYAK assistant voice — rule-based Jarvis layer for the desktop shell."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER, format_sharpe
from quantlab.app.settings_store import ExperienceMode, UiSettingsStore
from quantlab.domain.models import ExperimentRun
from quantlab.ui.time_format import format_ist_from_iso

IST = ZoneInfo("Asia/Kolkata")


class FocusAction(StrEnum):
    ONBOARDING = "onboarding"
    FIRST_BACKTEST = "first_backtest"
    LEARN_SHARPE = "learn_sharpe"
    VALIDATION = "validation"
    FEATURES = "features"
    FULL_LAB = "full_lab"
    EXPLORE = "explore"
    JOURNAL = "journal"
    COMPARE = "compare"
    MARKET = "market"


@dataclass(frozen=True)
class FocusSuggestion:
    title: str
    body: str
    action_label: str
    action: FocusAction
    step: int
    total_steps: int = 5


@dataclass(frozen=True)
class JournalEntry:
    experiment_id: str
    name: str
    summary: str
    sharpe: str
    note: str
    data_kind: str = "synthetic"
    run_at: str = ""


@dataclass(frozen=True)
class JournalGroup:
    name: str
    latest_id: str
    count: int
    summary: str
    note: str
    run_at: str = ""


@dataclass(frozen=True)
class ContextNudge:
    text: str
    nav_key: str | None = None
    action_label: str | None = None


class NayakAssistant:
    """Contextual copy and milestone memory. Not an LLM — honest, deterministic."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        self._runtime = runtime
        self._store: UiSettingsStore = runtime.ui_settings

    @property
    def tk_name(self) -> str:
        return self._store.current.tk_display_name or "TK"

    def greeting(self) -> str:
        hour = datetime.now(tz=IST).hour
        if hour < 12:
            period = "Good morning"
        elif hour < 17:
            period = "Good afternoon"
        else:
            period = "Good evening"
        return f"{period}, {self.tk_name}."

    def status_line(self) -> str:
        status = self._runtime.status
        live = "off" if "DISABLED" in status.live_trading.upper() else "on"
        return (
            f"Your lab is in {status.mode.value.upper()} mode. "
            f"Live trading is {live}. "
            f"Data is {status.data.lower()}."
        )

    def focus(self) -> FocusSuggestion:
        prefs = self._store.current
        runs = self._runtime.ledger.list_runs()
        milestones = set(prefs.milestones)

        if "onboarding_complete" not in milestones:
            return FocusSuggestion(
                title="Welcome to your private lab",
                body=(
                    "I'm NAYAK — your quantitative research assistant. "
                    "We'll start with synthetic NSE-style data. Nothing here places real trades."
                ),
                action_label="Tour the lab",
                action=FocusAction.ONBOARDING,
                step=1,
            )

        if not runs:
            return FocusSuggestion(
                title="Run your first experiment",
                body=(
                    "Let's test a simple momentum idea: names that rose recently may keep rising "
                    "on the next bar — after costs. I'll explain Sharpe when we're done."
                ),
                action_label="Start backtest",
                action=FocusAction.FIRST_BACKTEST,
                step=2,
            )

        if "first_backtest" not in milestones:
            self.record_milestone("first_backtest")

        last = runs[-1]
        sharpe_txt = format_sharpe(
            last.metrics.get("sharpe") if isinstance(last.metrics.get("sharpe"), float) else None
        )

        if "first_equity_view" not in milestones:
            return FocusSuggestion(
                title="Read your first result",
                body=(
                    f"Your last run ({last.name}) finished with Sharpe {sharpe_txt} "
                    f"on synthetic data. {SYNTHETIC_SHARPE_DISCLAIMER}"
                ),
                action_label="Learn what Sharpe means",
                action=FocusAction.LEARN_SHARPE,
                step=3,
            )

        validation_runs = [r for r in runs if "validation" in r.name.lower()]
        if not validation_runs:
            return FocusSuggestion(
                title="Validate before you trust it",
                body=(
                    "A single backtest can lie. Next, run walk-forward validation "
                    "in Full Lab to see if the idea holds up under stricter checks."
                ),
                action_label="Run validation in Full Lab",
                action=FocusAction.VALIDATION,
                step=4,
            )

        notes = prefs.journal_notes
        noted = sum(1 for run in runs if notes.get(run.id, "").strip())
        if noted == 0 and len(runs) >= 1:
            return FocusSuggestion(
                title="Capture what you learned",
                body=(
                    f"Validation passed on synthetic data (Sharpe {sharpe_txt}). "
                    "Write one line in your journal — what surprised you?"
                ),
                action_label="Open journal",
                action=FocusAction.JOURNAL,
                step=5,
            )

        duplicate_names = self._duplicate_run_names(runs)
        if len(runs) >= 3 and duplicate_names:
            dup = duplicate_names[0]
            return FocusSuggestion(
                title="Compare similar runs",
                body=(
                    f"You have {dup[1]} runs named {dup[0]}. "
                    "Side-by-side metrics show whether results are stable or noise."
                ),
                action_label="Compare in Full Lab",
                action=FocusAction.COMPARE,
                step=5,
            )

        if prefs.experience_mode is ExperienceMode.GUIDED and "full_lab_unlocked" not in milestones:
            return FocusSuggestion(
                title="You're building momentum",
                body=(
                    f"You have {len(runs)} experiment(s) logged. "
                    "Switch to Full Lab for market panels and the compare view."
                ),
                action_label="Open Full Lab",
                action=FocusAction.FULL_LAB,
                step=5,
            )

        if "market" not in set(prefs.visited_pages):
            return FocusSuggestion(
                title="Explore the synthetic market",
                body=(
                    f"Last run: {last.name} (Sharpe {sharpe_txt}). "
                    f"{SYNTHETIC_SHARPE_DISCLAIMER} "
                    "Open Market to inspect the watchlist."
                ),
                action_label="Open Market in Full Lab",
                action=FocusAction.MARKET,
                step=5,
            )

        return FocusSuggestion(
            title="Run another experiment",
            body=(f"Last: {last.name} (Sharpe {sharpe_txt}). {SYNTHETIC_SHARPE_DISCLAIMER}"),
            action_label="Start Test wizard",
            action=FocusAction.FIRST_BACKTEST,
            step=5,
        )

    @staticmethod
    def _duplicate_run_names(runs: list[ExperimentRun]) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for run in runs:
            counts[run.name] = counts.get(run.name, 0) + 1
        return sorted(
            [(name, count) for name, count in counts.items() if count >= 2],
            key=lambda item: item[1],
            reverse=True,
        )

    def journal_entries(self, limit: int = 8) -> list[JournalEntry]:
        notes = self._store.current.journal_notes
        rows = []
        for run in reversed(self._runtime.ledger.list_runs()[-limit:]):
            sharpe_val = run.metrics.get("sharpe")
            sharpe_txt = format_sharpe(sharpe_val if isinstance(sharpe_val, float) else None)
            kind = run.data_kind or "synthetic"
            badge = "SYNTHETIC" if kind == "synthetic" else kind.upper()
            completed = self._runtime.jobs.experiment_completed_at(run.id)
            run_at = format_ist_from_iso(completed) if completed else ""
            rows.append(
                JournalEntry(
                    experiment_id=run.id,
                    name=run.name,
                    summary=f"Sharpe {sharpe_txt} · {badge} · {run.status.value}",
                    sharpe=sharpe_txt,
                    note=notes.get(run.id, ""),
                    data_kind=kind,
                    run_at=run_at,
                )
            )
        return rows

    def journal_groups(self, limit: int = 5) -> list[JournalGroup]:
        groups: dict[str, JournalGroup] = {}
        order: list[str] = []
        for entry in self.journal_entries(limit=30):
            if entry.name not in groups:
                groups[entry.name] = JournalGroup(
                    name=entry.name,
                    latest_id=entry.experiment_id,
                    count=1,
                    summary=entry.summary,
                    note=entry.note,
                    run_at=entry.run_at,
                )
                order.append(entry.name)
            else:
                existing = groups[entry.name]
                groups[entry.name] = JournalGroup(
                    name=existing.name,
                    latest_id=existing.latest_id,
                    count=existing.count + 1,
                    summary=existing.summary,
                    note=existing.note or entry.note,
                    run_at=existing.run_at or entry.run_at,
                )
            if len(order) >= limit:
                break
        return [groups[name] for name in order]

    def record_milestone(self, milestone_id: str) -> None:
        prefs = self._store.current
        if milestone_id not in prefs.milestones:
            prefs.milestones.append(milestone_id)
            self._store.save()

    def record_visit(self, page_key: str) -> None:
        prefs = self._store.current
        if page_key not in prefs.visited_pages:
            prefs.visited_pages.append(page_key)
            self._store.save()

    def complete_onboarding(self) -> None:
        self.record_milestone("onboarding_complete")

    def save_journal_note(self, experiment_id: str, note: str) -> bool:
        """Persist a TK journal note; returns True if text was saved."""
        cleaned = note.strip()
        if not experiment_id or not cleaned:
            return False
        prefs = self._store.current
        prefs.journal_notes[experiment_id] = cleaned
        self._store.save()
        if sum(1 for value in prefs.journal_notes.values() if value.strip()) >= 5:
            self.record_milestone("five_journal_entries")
        return True

    def primary_context_nudge(self) -> ContextNudge | None:
        """Single best proactive suggestion — avoids noisy multi-message strips."""
        prefs = self._store.current
        milestones = set(prefs.milestones)
        runs = self._runtime.ledger.list_runs()
        notes = prefs.journal_notes
        noted = sum(1 for run in runs if notes.get(run.id, "").strip())

        if not runs and "onboarding_complete" in milestones:
            return ContextNudge(
                "Your lab is ready — run the momentum wizard when you are.",
                nav_key="test",
                action_label="Open Test",
            )
        if runs and "first_validation" not in milestones:
            return ContextNudge(
                "One backtest is a start — Validation checks if the idea survives scrutiny.",
                nav_key="validation",
                action_label="Open Validation",
            )
        if len(runs) >= 2 and noted == 0:
            return ContextNudge(
                "Save a one-line note in Journal — your future self will thank you.",
                nav_key="journal",
                action_label="Open Journal",
            )
        dupes = self._duplicate_run_names(runs)
        if len(runs) >= 3 and dupes:
            return ContextNudge(
                f"{dupes[0][1]} similar runs logged — compare them side by side.",
                nav_key="compare",
                action_label="Compare",
            )
        if (
            prefs.experience_mode is ExperienceMode.GUIDED
            and "full_lab_unlocked" not in milestones
            and len(runs) >= 2
        ):
            return ContextNudge(
                "Ready for terminal panels? Try Full Lab from the header.",
                nav_key=None,
                action_label=None,
            )
        visited = set(prefs.visited_pages)
        if "learn" not in visited and "first_backtest" in milestones:
            return ContextNudge(
                "Learn has new stages unlocked since your first experiment.",
                nav_key="learn",
                action_label="Open Learn",
            )
        notifications = self._runtime.notifications
        if notifications:
            return ContextNudge(notifications[-1])
        return None

    def context_nudges(self) -> list[str]:
        """Short proactive text for context strips."""
        nudge = self.primary_context_nudge()
        if nudge is None:
            return []
        return [nudge.text]
