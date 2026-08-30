"""Discovery contracts. A discovered expression is not an alpha, strategy, or order."""

from __future__ import annotations

from enum import StrEnum


class ValueType(StrEnum):
    SCALAR = "scalar"
    CROSS_SECTION = "cross_section"
    TIME_SERIES = "time_series"
    PANEL = "panel"
    BOOLEAN = "boolean"
    RANKED_CROSS_SECTION = "ranked_cross_section"
    RETURN_SERIES = "return_series"
    VOLATILITY_SERIES = "volatility_series"


class ExprKind(StrEnum):
    FEATURE = "feature"
    CONSTANT = "constant"
    UNARY = "unary"
    BINARY = "binary"
    ROLLING = "rolling"
    CROSS_SECTION = "cross_section"


class CandidateStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    EVALUATED = "evaluated"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    FALSIFIED = "falsified"
    REDUNDANT = "redundant"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class NoveltyClass(StrEnum):
    NOVEL = "novel"
    LOW_REDUNDANCY = "low_redundancy"
    MODERATE_REDUNDANCY = "moderate_redundancy"
    HIGH_REDUNDANCY = "high_redundancy"
    DUPLICATE = "duplicate"


class SearchMode(StrEnum):
    RANDOM = "random"
    SEEDED = "seeded"
    GENETIC = "genetic"
    SYMBOLIC = "symbolic"
    HUMAN = "human"


class FitnessName(StrEnum):
    IC_COMPLEXITY_V1 = "ic_complexity_v1"


FORBIDDEN_PRIMITIVES = frozenset(
    {
        "future_return",
        "forward_return",
        "forward_volatility",
        "future_drawdown",
        "future_hit",
        "forward_excess_return",
        "label",
        "y_forward",
    }
)
