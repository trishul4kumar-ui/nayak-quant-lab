"""Data-only, causal long/cash strategies. No generated code or broker capability.

Every rule reads completed closes and trailing observations only. Stops are
close-triggered decisions filled at the NEXT available open, not intrabar stops.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Sequence
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantlab.agents.hashing import digest, reject_sensitive_payload, safe_text

Feature = Literal[
    "close_sma_gap",
    "sma_cross_gap",
    "rsi",
    "return",
    "breakout_high_gap",
    "breakout_low_gap",
    "realized_volatility",
    "volume_ratio",
]
Comparison = Literal["gt", "lt", "ge", "le", "cross_above", "cross_below"]
StrategyId = Literal[
    "close_sma_next_open_v1",
    "sma_cross_v1",
    "rsi_reversion_v1",
    "breakout_v1",
    "momentum_v1",
    "volatility_trend_v1",
    "rules_v1",
]


class Bar(Protocol):
    @property
    def open(self) -> float: ...
    @property
    def high(self) -> float: ...
    @property
    def low(self) -> float: ...
    @property
    def close(self) -> float: ...
    @property
    def volume(self) -> float | None: ...


class StrategyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    feature: Feature
    comparison: Comparison
    period: int = Field(default=20, ge=2, le=60, strict=True)
    slow_period: int = Field(default=40, ge=3, le=60, strict=True)
    threshold: float = Field(default=0.0, ge=-100, le=100, strict=True)

    @model_validator(mode="after")
    def sensible_units(self) -> StrategyRule:
        if self.feature == "sma_cross_gap" and self.period >= self.slow_period:
            raise ValueError("FAST_WINDOW_MUST_BE_LESS_THAN_SLOW")
        if self.feature == "rsi" and not 0 <= self.threshold <= 100:
            raise ValueError("RSI_THRESHOLD_MUST_BE_0_TO_100")
        if self.feature in {"realized_volatility", "volume_ratio"} and self.threshold < 0:
            raise ValueError("NONNEGATIVE_FEATURE_THRESHOLD_REQUIRED")
        return self

    def warmup(self) -> int:
        base = self.slow_period if self.feature == "sma_cross_gap" else self.period
        if self.feature in {
            "rsi",
            "return",
            "realized_volatility",
            "breakout_high_gap",
            "breakout_low_gap",
        }:
            base += 1
        return base + int(self.comparison.startswith("cross_"))


class StrategyDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    name: str = Field(min_length=3, max_length=80)
    hypothesis: str = Field(min_length=10, max_length=600)
    entry: tuple[StrategyRule, ...] = Field(min_length=1, max_length=4)
    exit: tuple[StrategyRule, ...] = Field(min_length=1, max_length=4)
    entry_mode: Literal["all", "any"] = "all"
    exit_mode: Literal["all", "any"] = "any"
    allocation: float = Field(default=1.0, ge=0.05, le=1.0, strict=True)
    stop_loss: float = Field(default=0.0, ge=0, le=0.30, strict=True)
    take_profit: float = Field(default=0.0, ge=0, le=1.0, strict=True)
    max_holding_bars: int = Field(default=0, ge=0, le=252, strict=True)
    implementation_version: Literal["causal-rules-v1"] = "causal-rules-v1"

    @model_validator(mode="after")
    def clean_text(self) -> StrategyDefinition:
        reject_sensitive_payload(self.model_dump(mode="json"))
        if any(safe_text(s) != s for s in (self.name, self.hypothesis)):
            raise ValueError("SECRET_LIKE_STRATEGY_TEXT_REJECTED")
        return self

    def identity_hash(self) -> str:
        return digest(self.model_dump(mode="json"))

    def economic_hash(self) -> str:
        """Ignore prose, unused slow windows, clause order and repeated conditions."""
        payload = self.model_dump(mode="json", exclude={"name", "hypothesis"})
        for phase in ("entry", "exit"):
            unique = {}
            for raw in payload[phase]:
                rule = dict(raw)
                if rule["feature"] != "sma_cross_gap":
                    rule.pop("slow_period")
                unique[digest(rule)] = rule
            payload[phase] = [unique[key] for key in sorted(unique)]
            if len(unique) == 1:
                payload[phase + "_mode"] = "all"  # Single-clause all/any are identical.
        return digest(payload)

    def warmup(self) -> int:
        return max(rule.warmup() for rule in (*self.entry, *self.exit))


STRATEGY_NAMES: dict[str, str] = {
    "close_sma_next_open_v1": "Close above SMA · long/cash",
    "sma_cross_v1": "Fast/slow SMA crossover · long/cash",
    "rsi_reversion_v1": "RSI mean reversion · long/cash",
    "breakout_v1": "Prior-channel breakout · long/cash",
    "momentum_v1": "Trailing momentum · long/cash",
    "volatility_trend_v1": "SMA trend with volatility filter · long/cash",
}


def describe_rule(rule: StrategyRule) -> str:
    """Host-owned description of executable data, never an LLM's interpretation."""
    operators = {
        "gt": ">",
        "lt": "<",
        "ge": ">=",
        "le": "<=",
        "cross_above": "crosses above",
        "cross_below": "crosses below",
    }
    window = (
        f"{rule.period}/{rule.slow_period}" if rule.feature == "sma_cross_gap" else str(rule.period)
    )
    unit = (
        "RSI points"
        if rule.feature == "rsi"
        else ("volume multiple" if rule.feature == "volume_ratio" else "fraction")
    )
    return f"{rule.feature}[{window} bars] {operators[rule.comparison]} {rule.threshold:g} {unit}"


def describe_strategy(definition: StrategyDefinition) -> str:
    entry = f" {definition.entry_mode.upper()} ".join(map(describe_rule, definition.entry))
    exit_ = f" {definition.exit_mode.upper()} ".join(map(describe_rule, definition.exit))
    return (
        f"Long/cash only; allocate {definition.allocation:.0%} of cash. Entry: {entry}. "
        f"Exit to cash: {exit_}. Next available open after a completed-bar signal; "
        f"close-triggered stop={definition.stop_loss:g}, target={definition.take_profit:g}; "
        f"maximum holding={definition.max_holding_bars} bars (0 means no time exit)."
    )


def preset_strategy(strategy: str, lookback: int = 20) -> StrategyDefinition:
    """Presets and AI definitions share exactly the same evaluator and units."""

    def rule(
        feature: Feature, comparison: Comparison, threshold: float = 0.0, period: int = lookback
    ) -> StrategyRule:
        return StrategyRule(
            feature=feature,
            comparison=comparison,
            threshold=threshold,
            period=period,
            slow_period=lookback,
        )

    entry: tuple[StrategyRule, ...]
    exit_: tuple[StrategyRule, ...]
    if strategy == "close_sma_next_open_v1":
        entry, exit_ = (rule("close_sma_gap", "gt"),), (rule("close_sma_gap", "le"),)
    elif strategy == "sma_cross_v1":
        entry = (rule("sma_cross_gap", "gt", period=max(2, lookback // 2)),)
        exit_ = (rule("sma_cross_gap", "lt", period=max(2, lookback // 2)),)
    elif strategy == "rsi_reversion_v1":
        entry, exit_ = (rule("rsi", "lt", 30.0),), (rule("rsi", "gt", 55.0),)
    elif strategy == "breakout_v1":
        entry, exit_ = (rule("breakout_high_gap", "gt"),), (rule("breakout_low_gap", "lt"),)
    elif strategy == "momentum_v1":
        entry, exit_ = (rule("return", "gt"),), (rule("return", "lt"),)
    elif strategy == "volatility_trend_v1":
        entry = (rule("close_sma_gap", "gt"), rule("realized_volatility", "lt", 0.025))
        exit_ = (rule("close_sma_gap", "lt"), rule("realized_volatility", "gt", 0.04))
    else:
        raise ValueError("UNKNOWN_STRATEGY")
    return StrategyDefinition(
        name=STRATEGY_NAMES[strategy],
        hypothesis="Test this versioned price-rule hypothesis after modeled costs; no alpha claim.",
        entry=entry,
        exit=exit_,
    )


def feature_values(
    rule: StrategyRule,
    bars: Sequence[Bar],
    cancelled: Callable[[], bool] = lambda: False,
) -> list[float | None]:
    closes = [b.close for b in bars]
    result: list[float | None] = []
    p = rule.period
    for i, close in enumerate(closes):
        if cancelled():
            raise ValueError("cancelled")
        value: float | None = None
        if i + 1 >= rule.warmup() - int(rule.comparison.startswith("cross_")):
            window = closes[i - p + 1 : i + 1]
            if rule.feature == "close_sma_gap":
                value = close / statistics.fmean(window) - 1
            elif rule.feature == "sma_cross_gap":
                value = (
                    statistics.fmean(window)
                    / statistics.fmean(closes[i - rule.slow_period + 1 : i + 1])
                    - 1
                )
            elif rule.feature == "return":
                value = close / closes[i - p] - 1
            elif rule.feature == "rsi":
                diffs = [closes[k] - closes[k - 1] for k in range(i - p + 1, i + 1)]
                gains = sum(max(d, 0) for d in diffs)
                losses = sum(max(-d, 0) for d in diffs)
                value = 50.0 if gains + losses == 0 else 100.0 * gains / (gains + losses)
            elif rule.feature in {"breakout_high_gap", "breakout_low_gap"}:
                previous = bars[i - p : i]  # excludes the current signal bar
                channel = (
                    max(b.high for b in previous)
                    if rule.feature == "breakout_high_gap"
                    else min(b.low for b in previous)
                )
                value = close / channel - 1
            elif rule.feature == "realized_volatility":
                value = statistics.pstdev(
                    closes[k] / closes[k - 1] - 1 for k in range(i - p + 1, i + 1)
                )
            elif rule.feature == "volume_ratio":
                volumes = [b.volume for b in bars[i - p + 1 : i + 1]]
                if any(v is None for v in volumes):
                    raise ValueError("REAL_VOLUME_REQUIRED_FOR_STRATEGY")
                numbers = [float(v) for v in volumes if v is not None]
                average = statistics.fmean(numbers)
                value = numbers[-1] / average if average > 0 else None
        result.append(value if value is not None and math.isfinite(value) else None)
    return result


def matches(rule: StrategyRule, values: list[float | None], index: int) -> bool:
    current = values[index]
    if current is None:
        return False
    threshold = rule.threshold
    if rule.comparison == "gt":
        return current > threshold
    if rule.comparison == "lt":
        return current < threshold
    if rule.comparison == "ge":
        return current >= threshold
    if rule.comparison == "le":
        return current <= threshold
    prior = values[index - 1] if index > 0 else None
    if prior is None:
        return False
    return (
        prior <= threshold < current
        if rule.comparison == "cross_above"
        else prior >= threshold > current
    )


def strategy_signals(
    definition: StrategyDefinition,
    bars: Sequence[Bar],
    cancelled: Callable[[], bool] = lambda: False,
) -> tuple[list[bool], list[bool]]:
    """Causal signals at each completed bar; callers shift execution to the next open."""
    panels = {
        rule: feature_values(rule, bars, cancelled)
        for rule in dict.fromkeys((*definition.entry, *definition.exit))
    }
    entries, exits = [], []
    for i in range(len(bars)):
        if cancelled():
            raise ValueError("cancelled")
        entry = [matches(rule, panels[rule], i) for rule in definition.entry]
        exit_ = [matches(rule, panels[rule], i) for rule in definition.exit]
        entries.append(all(entry) if definition.entry_mode == "all" else any(entry))
        exits.append(all(exit_) if definition.exit_mode == "all" else any(exit_))
    return entries, exits
