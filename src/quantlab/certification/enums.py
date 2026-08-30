"""Certification enumerations. CERTIFIED is governance, never live authority."""

from enum import StrEnum


class CertificationState(StrEnum):
    DRAFT = "draft"
    UNDER_VALIDATION = "under_validation"
    VALIDATION_FAILED = "validation_failed"
    VALIDATION_PASSED = "validation_passed"
    PAPER_ELIGIBLE = "paper_eligible"
    PAPER_ACTIVE = "paper_active"
    PAPER_FAILED = "paper_failed"
    SHADOW_ELIGIBLE = "shadow_eligible"
    SHADOW_ACTIVE = "shadow_active"
    PRELIVE_REVIEW = "prelive_review"
    CERTIFIED = "certified"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class ReviewerRole(StrEnum):
    RESEARCHER = "researcher"
    VALIDATOR = "validator"
    RISK_REVIEWER = "risk_reviewer"
    DATA_REVIEWER = "data_reviewer"
    EXECUTION_REVIEWER = "execution_reviewer"
    OPERATIONS_REVIEWER = "operations_reviewer"
    CERTIFICATION_REVIEWER = "certification_reviewer"


class ChecklistCode(StrEnum):
    DATA_PIT = "data_pit"
    DATA_PROVENANCE = "data_provenance"
    DATA_CORPORATE_ACTIONS = "data_corporate_actions"
    SURVIVORSHIP = "survivorship"
    RESEARCH_LINEAGE = "research_lineage"
    MULTIPLE_TESTING = "multiple_testing"
    OOS_VALIDATION = "oos_validation"
    STATISTICAL_VALIDATION = "statistical_validation"
    REGIME_STABILITY = "regime_stability"
    EXECUTION_VALIDATION = "execution_validation"
    TCA = "tca"
    CAPACITY = "capacity"
    RISK = "risk"
    CAPITAL = "capital"
    PAPER_RECONCILIATION = "paper_reconciliation"
    MONITORING = "monitoring"
    OPERATIONAL_READINESS = "operational_readiness"
    SAFETY = "safety"
    AI_GOVERNANCE = "ai_governance"


class ItemStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_TESTED = "not_tested"
    WAIVED = "waived"


class RiskCategory(StrEnum):
    CONCEPTUAL = "conceptual"
    DATA = "data"
    IMPLEMENTATION = "implementation"
    PARAMETER = "parameter"
    ESTIMATION = "estimation"
    OVERFITTING = "overfitting"
    REGIME = "regime"
    LIQUIDITY = "liquidity"
    EXECUTION = "execution"
    OPERATIONAL = "operational"
    SOFTWARE = "software"
    DEPENDENCY = "dependency"
    MONITORING = "monitoring"
    GOVERNANCE = "governance"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    NOT_ASSESSED = "not_assessed"


class ChangeClass(StrEnum):
    MINOR = "minor"
    MATERIAL = "material"
    MAJOR = "major"


class SuspensionReason(StrEnum):
    PERFORMANCE_DECAY = "performance_decay"
    DATA_FAILURE = "data_failure"
    RISK_BREACH = "risk_breach"
    EXECUTION_DETERIORATION = "execution_deterioration"
    CAPACITY_COLLAPSE = "capacity_collapse"
    REGIME_INCOMPATIBILITY = "regime_incompatibility"
    RECONCILIATION_BREAK = "reconciliation_break"
    SOFTWARE_DEFECT = "software_defect"
    MODEL_DRIFT = "model_drift"
    VALIDATION_EXPIRY = "validation_expiry"
