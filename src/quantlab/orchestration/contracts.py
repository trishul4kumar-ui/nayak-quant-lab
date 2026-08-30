"""Orchestration contracts. A research experiment is not an alpha or a backtest."""

from __future__ import annotations

from enum import StrEnum


class ExperimentType(StrEnum):
    DISCOVERY = "discovery"
    CONFIRMATION = "confirmation"
    REPLICATION = "replication"
    ROBUSTNESS = "robustness"
    ABLATION = "ablation"
    FALSIFICATION = "falsification"
    SENSITIVITY = "sensitivity"
    MODEL_COMPARISON = "model_comparison"
    ENSEMBLE_COMPARISON = "ensemble_comparison"
    PORTFOLIO_COMPARISON = "portfolio_comparison"
    EXECUTION_COMPARISON = "execution_comparison"
    REGIME_CONDITIONAL = "regime_conditional"
    TEMPORAL_STABILITY = "temporal_stability"


class ResearchStatus(StrEnum):
    DRAFT = "draft"
    REGISTERED = "registered"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALID = "invalid"
    FALSIFIED = "falsified"
    DISCOVERED = "discovered"
    REPLICATING = "replicating"
    REPLICATED = "replicated"
    ROBUST_CANDIDATE = "robust_candidate"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ResearchQuality(StrEnum):
    UNEXPLORED = "unexplored"
    EXPLORATORY = "exploratory"
    DISCOVERED = "discovered"
    WEAK = "weak"
    PROMISING = "promising"
    ROBUST = "robust"
    REPLICATED = "replicated"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"


class MetricRole(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DIAGNOSTIC = "diagnostic"


class SelectionPolicy(StrEnum):
    PRE_REGISTERED = "pre_registered"
    MAX_SHARPE = "max_sharpe"


class StoppingPolicy(StrEnum):
    PRE_REGISTERED_BUDGET = "pre_registered_budget"
    POSTHOC = "posthoc"


class FailureKind(StrEnum):
    PIT = "pit"
    INTEGRITY = "integrity"
    MODEL = "model"
    DATA = "data"
    EXECUTION = "execution"
    BUDGET = "budget"
    CANDIDATE_INVALID = "candidate_invalid"
    STATISTICAL = "statistical"
    INFEASIBLE_PORTFOLIO = "infeasible_portfolio"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[ResearchStatus, frozenset[ResearchStatus]] = {
    ResearchStatus.DRAFT: frozenset({ResearchStatus.REGISTERED, ResearchStatus.INVALID}),
    ResearchStatus.REGISTERED: frozenset(
        {ResearchStatus.PLANNED, ResearchStatus.SUPERSEDED, ResearchStatus.INVALID}
    ),
    ResearchStatus.PLANNED: frozenset(
        {ResearchStatus.RUNNING, ResearchStatus.INVALID, ResearchStatus.SUPERSEDED}
    ),
    ResearchStatus.RUNNING: frozenset(
        {
            ResearchStatus.COMPLETED,
            ResearchStatus.FAILED,
            ResearchStatus.INVALID,
            ResearchStatus.REJECTED,
        }
    ),
    ResearchStatus.COMPLETED: frozenset(
        {
            ResearchStatus.FALSIFIED,
            ResearchStatus.DISCOVERED,
            ResearchStatus.REJECTED,
            ResearchStatus.SUPERSEDED,
            ResearchStatus.REPLICATING,
            ResearchStatus.ROBUST_CANDIDATE,
        }
    ),
    ResearchStatus.FAILED: frozenset({ResearchStatus.SUPERSEDED, ResearchStatus.INVALID}),
    ResearchStatus.INVALID: frozenset(),
    ResearchStatus.FALSIFIED: frozenset({ResearchStatus.SUPERSEDED}),
    ResearchStatus.DISCOVERED: frozenset(
        {
            ResearchStatus.REPLICATING,
            ResearchStatus.FALSIFIED,
            ResearchStatus.ROBUST_CANDIDATE,
            ResearchStatus.REJECTED,
            ResearchStatus.SUPERSEDED,
        }
    ),
    ResearchStatus.REPLICATING: frozenset(
        {ResearchStatus.REPLICATED, ResearchStatus.FAILED, ResearchStatus.REJECTED}
    ),
    ResearchStatus.REPLICATED: frozenset(
        {ResearchStatus.ROBUST_CANDIDATE, ResearchStatus.FALSIFIED, ResearchStatus.SUPERSEDED}
    ),
    ResearchStatus.ROBUST_CANDIDATE: frozenset(
        {ResearchStatus.FALSIFIED, ResearchStatus.SUPERSEDED, ResearchStatus.REJECTED}
    ),
    ResearchStatus.REJECTED: frozenset({ResearchStatus.SUPERSEDED}),
    ResearchStatus.SUPERSEDED: frozenset(),
}
