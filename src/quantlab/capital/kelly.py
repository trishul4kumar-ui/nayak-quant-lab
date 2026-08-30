"""Constrained Kelly research sizing. Never overrides hard limits."""

from __future__ import annotations

import math

from pydantic import BaseModel

from quantlab.capital.definitions import AbstentionCode
from quantlab.domain.research import CheckResult


class KellyResult(BaseModel):
    f_star: float | None
    fractional: float | None
    capped: float | None
    status: CheckResult
    abstention_code: AbstentionCode = AbstentionCode.NONE
    note: str = ""


def full_kelly(mu: float, sigma2: float) -> KellyResult:
    if not math.isfinite(mu) or not math.isfinite(sigma2) or sigma2 <= 0:
        return KellyResult(
            f_star=None,
            fractional=None,
            capped=None,
            status=CheckResult.FAIL,
            abstention_code=AbstentionCode.KELLY_UNRELIABLE,
            note="KELLY_UNRELIABLE: mu/sigma^2 undefined",
        )
    return KellyResult(
        f_star=mu / sigma2,
        fractional=None,
        capped=None,
        status=CheckResult.PASS,
        note="f* = μ/σ²; research sizing only",
    )


def binary_kelly(b: float, p: float) -> KellyResult:
    if not math.isfinite(b) or not math.isfinite(p) or b <= 0 or not 0.0 <= p <= 1.0:
        return KellyResult(
            f_star=None,
            fractional=None,
            capped=None,
            status=CheckResult.FAIL,
            abstention_code=AbstentionCode.KELLY_UNRELIABLE,
            note="KELLY_UNRELIABLE: binary inputs invalid",
        )
    q = 1.0 - p
    return KellyResult(
        f_star=(b * p - q) / b,
        fractional=None,
        capped=None,
        status=CheckResult.PASS,
        note="f* = (bp-q)/b; research sizing only",
    )


def apply_fraction(result: KellyResult, fraction: float, cap: float) -> KellyResult:
    if result.f_star is None:
        return result
    fractional = fraction * result.f_star
    capped = min(max(fractional, 0.0), cap)
    return result.model_copy(
        update={
            "fractional": fractional,
            "capped": capped,
            "note": f"fractional={fraction}; cap={cap}; does not override hard limits",
        }
    )
