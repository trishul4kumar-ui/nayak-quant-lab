"""Change classification. Material/major changes require a new candidate version."""

from __future__ import annotations

from quantlab.certification.enums import ChangeClass
from quantlab.certification.models import Candidate

_MATERIAL_FIELDS = (
    "strategy_id",
    "model_id",
    "alpha_id",
    "ensemble_id",
    "portfolio_policy_id",
    "capital_policy_id",
    "risk_policy_id",
    "paper_oms_policy_id",
    "snapshot_id",
    "regime_definition",
    "tca_policy_id",
    "econometric_spec_id",
    "family_id",
)

_MAJOR_FIELDS = (
    "model_id",
    "alpha_id",
    "ensemble_id",
    "capital_policy_id",
    "risk_policy_id",
)


def classify_change(before: Candidate, after: Candidate) -> ChangeClass:
    major = any(getattr(before, name) != getattr(after, name) for name in _MAJOR_FIELDS)
    if before.feature_versions != after.feature_versions:
        major = True
    if major:
        return ChangeClass.MAJOR
    material = any(getattr(before, name) != getattr(after, name) for name in _MATERIAL_FIELDS)
    if material:
        return ChangeClass.MATERIAL
    return ChangeClass.MINOR
