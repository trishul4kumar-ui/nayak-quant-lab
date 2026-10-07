"""Deterministic intraday research; agent and broker clients are outside the hot path."""

from quantlab.intraday_research.engine import evaluate_signal

__all__ = ["evaluate_signal"]
