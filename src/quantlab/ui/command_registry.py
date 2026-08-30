"""Raycast-style command registry for the palette."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.navigation import FULL_NAV, NAV_KEYWORDS, NAV_SHORTCUTS

PaletteKind = Literal["nav", "action", "experiment"]


@dataclass(frozen=True)
class PaletteCommand:
    command_id: str
    kind: PaletteKind
    title: str
    subtitle: str
    keywords: tuple[str, ...]


def build_palette_commands(runtime: ApplicationRuntime) -> list[PaletteCommand]:
    commands: list[PaletteCommand] = []

    for item in FULL_NAV:
        if item.header:
            continue
        key = item.key
        shortcuts = NAV_SHORTCUTS.get(key, "")
        kw = (key, item.label.lower(), *NAV_KEYWORDS.get(key, ()))
        if shortcuts:
            kw = (*kw, shortcuts.lower())
        commands.append(
            PaletteCommand(
                command_id=f"nav:{key}",
                kind="nav",
                title=item.label,
                subtitle=f"Go to {item.label}",
                keywords=kw,
            )
        )

    commands.extend(
        [
            PaletteCommand(
                command_id="action:run_backtest",
                kind="action",
                title="Run backtest",
                subtitle="Start momentum backtest in Backtest Lab",
                keywords=("run", "backtest", "start", "momentum", "execute"),
            ),
            PaletteCommand(
                command_id="action:run_validation",
                kind="action",
                title="Run validation suite",
                subtitle="Walk-forward validation on synthetic data",
                keywords=("validate", "validation", "walk-forward", "gate"),
            ),
            PaletteCommand(
                command_id="action:open_journal",
                kind="action",
                title="Open journal",
                subtitle="Your research notebook",
                keywords=("journal", "notes", "notebook"),
            ),
            PaletteCommand(
                command_id="action:toggle_theme",
                kind="action",
                title="Toggle light/dark theme",
                subtitle="Switch appearance",
                keywords=("theme", "dark", "light", "appearance"),
            ),
            PaletteCommand(
                command_id="action:full_lab",
                kind="action",
                title="Switch to Full Lab",
                subtitle="Unlock all research pages",
                keywords=("full", "lab", "advanced"),
            ),
            PaletteCommand(
                command_id="action:guided_lab",
                kind="action",
                title="Switch to Guided Lab",
                subtitle="Focused beginner workflow",
                keywords=("guided", "beginner", "simple"),
            ),
        ]
    )

    for run in reversed(runtime.ledger.list_runs()[-20:]):
        name = run.name.lower()
        commands.append(
            PaletteCommand(
                command_id=f"experiment:{run.id}",
                kind="experiment",
                title=f"Open experiment · {run.name}",
                subtitle=f"Sharpe {run.metrics.get('sharpe', '—')} · {run.data_kind}",
                keywords=(name, "experiment", "run", "open", run.id[:8]),
            )
        )

    return commands


def _score_command(cmd: PaletteCommand, tokens: list[str]) -> int | None:
    title = cmd.title.lower()
    subtitle = cmd.subtitle.lower()
    hay = " ".join((title, subtitle, *cmd.keywords)).lower()
    if not all(token in hay for token in tokens):
        return None
    score = 0
    for token in tokens:
        if title.startswith(token):
            score -= 40
        elif title == token:
            score -= 60
        elif token in title:
            score -= 20
        elif any(token == kw for kw in cmd.keywords):
            score -= 15
        elif token in subtitle:
            score += 5
        else:
            score += hay.index(token) if token in hay else 50
    if cmd.kind == "nav":
        score -= 3
    return score


def filter_palette_commands(
    commands: list[PaletteCommand],
    query: str,
    *,
    recents: list[str] | None = None,
) -> list[PaletteCommand]:
    by_id = {cmd.command_id: cmd for cmd in commands}
    q = query.strip().lower()
    if not q:
        ordered: list[PaletteCommand] = []
        seen: set[str] = set()
        for cid in recents or []:
            cmd = by_id.get(cid)
            if cmd is not None and cid not in seen:
                ordered.append(cmd)
                seen.add(cid)
        for cmd in commands:
            if cmd.command_id not in seen:
                ordered.append(cmd)
                seen.add(cmd.command_id)
        return ordered

    tokens = q.split()
    scored: list[tuple[int, PaletteCommand]] = []
    for cmd in commands:
        score = _score_command(cmd, tokens)
        if score is not None:
            if cmd.command_id in (recents or []):
                score -= 25
            scored.append((score, cmd))
    scored.sort(key=lambda pair: (pair[0], pair[1].title.lower()))
    return [cmd for _, cmd in scored]
