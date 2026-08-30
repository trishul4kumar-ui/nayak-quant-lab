"""Certification leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class CertificationLeakFlags(BaseModel):
    illegal_certification_transition: bool | None = None
    synthetic_production_evidence: bool | None = None
    reproduction_break: bool | None = None
    waiver_without_authority: bool | None = None
    ai_certification_override: bool | None = None
    critical_not_tested_certified: bool | None = None
