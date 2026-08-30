"""Staged Learn content — unlocked by TK's journey milestones."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearnTopic:
    heading: str
    body: str
    explain_key: str | None = None


@dataclass(frozen=True)
class LearnStage:
    stage_id: str
    title: str
    subtitle: str
    required_milestone: str | None
    topics: tuple[LearnTopic, ...]


LEARN_STAGES: tuple[LearnStage, ...] = (
    LearnStage(
        stage_id="starting",
        title="Starting out",
        subtitle="Always available — your foundation",
        required_milestone=None,
        topics=(
            LearnTopic(
                "What is quant trading?",
                "Testing ideas on data before risking real money. "
                "NAYAK QUANT LAB runs in RESEARCH mode — no live NSE orders.",
            ),
            LearnTopic(
                "What is NAYAK?",
                "Your private lab assistant. I suggest next steps, explain metrics, "
                "and keep an honest journal — I never place trades for you.",
            ),
            LearnTopic(
                "Synthetic data first",
                "This build uses synthetic NSE-style names. "
                "Learn the workflow here before connecting real feeds.",
            ),
        ),
    ),
    LearnStage(
        stage_id="backtest_basics",
        title="Your first backtest",
        subtitle="Unlocked after onboarding",
        required_milestone="onboarding_complete",
        topics=(
            LearnTopic(
                "Momentum hypothesis",
                "If a stock rose over 20 days, it might keep rising on the next bar. "
                "That is a testable idea — not a guarantee.",
                "momentum_20",
            ),
            LearnTopic(
                "Next-bar fills",
                "We simulate buying/selling on the bar after the signal. "
                "Same-bar fills would cheat — the lab forbids them.",
            ),
            LearnTopic(
                "Costs matter",
                "10 bps (0.10%) per trade is a default friction assumption. "
                "Profits must survive costs.",
                "cost_bps",
            ),
        ),
    ),
    LearnStage(
        stage_id="read_results",
        title="Reading results",
        subtitle="Unlocked after your first experiment",
        required_milestone="first_backtest",
        topics=(
            LearnTopic(
                "Sharpe ratio",
                "Return per unit of risk. Above 1.0 is often interesting on real data. "
                "On synthetic drift, lower values are normal.",
                "sharpe",
            ),
            LearnTopic(
                "Equity curve",
                "Portfolio value through time. A smooth rise with small dips "
                "is easier to trust than one lucky spike.",
                "equity_curve",
            ),
            LearnTopic(
                "Look-ahead bias",
                "Using future data by mistake. PASS on integrity means "
                "the backtest did not peek ahead.",
                "look_ahead_bias",
            ),
        ),
    ),
    LearnStage(
        stage_id="validation",
        title="Validation",
        subtitle="Unlocked after you explore Sharpe",
        required_milestone="first_equity_view",
        topics=(
            LearnTopic(
                "Why validate?",
                "One backtest can overfit noise. Walk-forward and robustness checks "
                "ask whether the idea survives stricter scrutiny.",
                "validation",
            ),
            LearnTopic(
                "Research gate",
                "Synthetic-only runs cannot promote to live trading. "
                "The gate fails closed — by design.",
                "gate_outcome",
            ),
        ),
    ),
    LearnStage(
        stage_id="markets_india",
        title="Markets & India",
        subtitle="Unlocked after validation",
        required_milestone="first_validation",
        topics=(
            LearnTopic(
                "NSE & NIFTY",
                "India's National Stock Exchange and its flagship index. "
                "Real connectivity is a later phase — learn safely on synthetic data first.",
            ),
            LearnTopic(
                "Derivatives (F&O)",
                "Futures and options add leverage and complexity. "
                "We will cover them after spot research discipline is solid.",
            ),
            LearnTopic(
                "Regimes",
                "Descriptive labels for market conditions — not forecasts. "
                "See Market Lab in Full Lab when ready.",
                "regime",
            ),
        ),
    ),
)


def unlocked_stages(milestones: set[str]) -> list[LearnStage]:
    stages: list[LearnStage] = []
    for stage in LEARN_STAGES:
        if stage.required_milestone is None or stage.required_milestone in milestones:
            stages.append(stage)
    return stages


def learn_progress(milestones: set[str]) -> tuple[int, int, list[tuple[LearnStage, bool]]]:
    """Return unlocked count, total stages, and (stage, is_unlocked) pairs."""
    ms = set(milestones)
    rows: list[tuple[LearnStage, bool]] = []
    unlocked = 0
    for stage in LEARN_STAGES:
        ok = stage.required_milestone is None or stage.required_milestone in ms
        rows.append((stage, ok))
        if ok:
            unlocked += 1
    return unlocked, len(LEARN_STAGES), rows


@dataclass(frozen=True)
class LearnTourTab:
    tab_id: str
    title: str
    body: str
    nav_key: str
    action_label: str


LEARN_TOUR_TABS: tuple[LearnTourTab, ...] = (
    LearnTourTab(
        "research",
        "Research",
        "Frame a hypothesis and inspect synthetic market panels before you commit capital — even simulated.",
        "research",
        "Open Research Lab",
    ),
    LearnTourTab(
        "backtest",
        "Backtest",
        "Run the Test wizard to see if momentum survives costs on next-bar fills.",
        "test",
        "Open Test wizard",
    ),
    LearnTourTab(
        "validate",
        "Validate",
        "Walk-forward gates ask whether one lucky backtest would fool you.",
        "validation",
        "Open Validation",
    ),
    LearnTourTab(
        "execute",
        "Execute",
        "Paper broker setup and execution monitors — live orders stay gated.",
        "broker",
        "Open Broker",
    ),
)
