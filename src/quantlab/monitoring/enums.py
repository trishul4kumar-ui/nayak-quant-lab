"""Monitoring enumerations. Performance is not alpha and not a claim."""

from enum import StrEnum


class AttributionMethod(StrEnum):
    EXACT_ACCOUNTING = "exact_accounting"
    MODEL_BASED = "model_based"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class ReturnKind(StrEnum):
    SIMPLE = "simple"
    LOG = "log"
    CUMULATIVE = "cumulative"
    TIME_WEIGHTED = "time_weighted"
    MONEY_WEIGHTED = "money_weighted"


class DriftStatus(StrEnum):
    ALIGNED = "aligned"
    DRIFTED = "drifted"
    UNEXPLAINED = "unexplained"
    NOT_TESTED = "not_tested"


class FeedbackKind(StrEnum):
    EXECUTION_CONSUMED_EDGE = "execution_consumed_edge"
    CONCENTRATED_SECURITY = "concentrated_security"
    FACTOR_EXPLAINED = "factor_explained"
    CONSTRUCTION_DAMPENED = "construction_dampened"
    TURNOVER_COSTS = "turnover_costs"
    TARGET_DEVIATION = "target_deviation"
    UNEXPLAINED = "unexplained"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class MonitoringRunStatus(StrEnum):
    COMPLETE = "complete"
    ABSTAINED = "abstained"
    FAILED = "failed"


class BenchmarkKind(StrEnum):
    EQUAL_WEIGHT_UNIVERSE = "equal_weight_universe"
    USER_SUPPLIED = "user_supplied"
    INDEX = "index"
    UNAVAILABLE = "unavailable"
