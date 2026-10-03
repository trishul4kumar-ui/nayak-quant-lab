"""Position-sizing methods. Each method is explicit; none is a hidden default."""

from __future__ import annotations

from quantlab.capital.definitions import (
    AllocationRequest,
    CapitalPolicy,
    SizingMethod,
    SizingResult,
)
from quantlab.capital.errors import CapitalError, InfeasibleCapitalAllocation
from quantlab.capital.kelly import apply_fraction, full_kelly
from quantlab.core.errors import OptimizationError
from quantlab.portfolio.covariance import as_array
from quantlab.portfolio.optimize import equal_risk_contribution


def _normalize(raw: dict[str, float]) -> dict[str, float]:
    total = sum(abs(v) for v in raw.values())
    if total <= 0:
        raise CapitalError("sizing produced a zero weight vector")
    return {name: raw[name] / total for name in sorted(raw)}


def _positive_scores(scores: dict[str, float]) -> dict[str, float]:
    return {name: max(score, 0.0) for name, score in scores.items()}


def size_equal_weight(names: list[str], policy: CapitalPolicy) -> SizingResult:
    if not names:
        raise CapitalError("equal_weight requires at least one name")
    weight = 1.0 / len(names)
    weights = {name: weight for name in names}
    return SizingResult(
        method_id=SizingMethod.EQUAL_WEIGHT.value,
        parameters={"n": float(len(names))},
        output_weights=weights,
        diagnostics={"rule": "1/n"},
    )


def size_score_weight(scores: dict[str, float]) -> SizingResult:
    positive = _positive_scores(scores)
    weights = _normalize(positive)
    return SizingResult(
        method_id=SizingMethod.SCORE_WEIGHT.value,
        parameters={},
        output_weights=weights,
        diagnostics={"rule": "w ∝ max(score, 0)"},
    )


def size_inverse_vol(names: list[str], vols: dict[str, float]) -> SizingResult:
    raw: dict[str, float] = {}
    for name in names:
        sigma = vols.get(name)
        if sigma is None or sigma <= 0:
            raise CapitalError(f"inverse_vol requires a positive vol for {name}")
        raw[name] = 1.0 / sigma
    return SizingResult(
        method_id=SizingMethod.INVERSE_VOL.value,
        parameters={},
        output_weights=_normalize(raw),
        diagnostics={"rule": "w ∝ 1/σ"},
    )


def size_risk_budget(
    names: list[str], request: AllocationRequest, policy: CapitalPolicy
) -> SizingResult:
    method = policy.risk_budget_method.value
    if method in {"equal_risk", "risk_parity"}:
        if request.covariance is None:
            raise InfeasibleCapitalAllocation(
                "risk budget requires PIT covariance",
                violated_constraints=["covariance"],
                required_adjustment="supply CovarianceReport; missing is NOT_TESTED not zero",
            )
        ordered = [name for name in request.covariance.names if name in names]
        if len(ordered) != len(names):
            raise InfeasibleCapitalAllocation(
                "covariance names do not cover the allocation universe",
                violated_constraints=["covariance"],
                current_candidate={},
            )
        cov = as_array(request.covariance)
        try:
            array = equal_risk_contribution(cov)
        except OptimizationError as exc:
            raise InfeasibleCapitalAllocation(
                str(exc),
                violated_constraints=["risk_budget"],
                current_candidate={},
            ) from exc
        weights = {ordered[i]: float(array[i]) for i in range(len(ordered))}
        return SizingResult(
            method_id=SizingMethod.RISK_BUDGET.value,
            parameters={"method": method},
            output_weights=weights,
            diagnostics={"rule": "equal risk contribution via existing ERC"},
        )
    if method == "inverse_volatility":
        return size_inverse_vol(names, request.vols)
    if method == "custom_budget":
        if not request.risk_budget:
            raise CapitalError("custom_budget requires request.risk_budget")
        weights = _normalize({name: request.risk_budget.get(name, 0.0) for name in names})
        return SizingResult(
            method_id=SizingMethod.RISK_BUDGET.value,
            parameters={"method": method},
            output_weights=weights,
            diagnostics={"rule": "custom budget shares used as weights"},
        )
    raise CapitalError(f"{method} is NOT_TESTED without PIT factor/hierarchy inputs")


def size_fractional_kelly(
    names: list[str], request: AllocationRequest, policy: CapitalPolicy
) -> SizingResult:
    raw: dict[str, float] = {}
    notes: dict[str, str] = {}
    for name in names:
        mu = request.scores.get(name)
        sigma = request.vols.get(name)
        if mu is None or sigma is None or sigma <= 0:
            raise CapitalError("KELLY_UNRELIABLE: missing mu or sigma")
        result = apply_fraction(
            full_kelly(mu, sigma * sigma), policy.kelly_fraction, policy.kelly_cap
        )
        if result.capped is None:
            raise CapitalError(result.note)
        raw[name] = max(result.capped, 0.0)
        notes[name] = result.note
    if sum(raw.values()) <= 0:
        raise CapitalError("KELLY_UNRELIABLE: all capped Kelly weights are non-positive")
    total = sum(raw.values())
    if total > 1.0:
        raw = {name: raw[name] / total for name in names}
        notes["scale"] = "sum of independent Kelly fractions exceeded 1; scaled to capital limit"
    return SizingResult(
        method_id=SizingMethod.FRACTIONAL_KELLY.value,
        parameters={"kelly_fraction": policy.kelly_fraction, "kelly_cap": policy.kelly_cap},
        output_weights=raw,
        diagnostics=notes,
    )


def size_confidence_scaled(scores: dict[str, float], confidence: float) -> SizingResult:
    if not 0.0 <= confidence <= 1.0:
        raise CapitalError("confidence must be in [0, 1]")
    composition = _normalize(_positive_scores(scores))
    scaled = {name: weight * confidence for name, weight in composition.items()}
    return SizingResult(
        method_id=SizingMethod.CONFIDENCE_SCALED.value,
        parameters={"confidence": confidence},
        output_weights=scaled,
        diagnostics={
            "rule": "normalized score composition × allocation_confidence",
            "deployment": "confidence scales gross exposure; residual remains cash",
        },
    )


def size_hybrid(names: list[str], request: AllocationRequest, confidence: float) -> SizingResult:
    score = size_score_weight({name: request.scores[name] for name in names}).output_weights
    if request.vols and all(name in request.vols and request.vols[name] > 0 for name in names):
        inv = size_inverse_vol(names, request.vols).output_weights
        mixed = {name: 0.5 * score[name] + 0.5 * inv[name] for name in names}
    else:
        mixed = score
    if not 0.0 <= confidence <= 1.0:
        raise CapitalError("confidence must be in [0, 1]")
    mixed = _normalize(mixed)
    mixed = {name: mixed[name] * confidence for name in names}
    return SizingResult(
        method_id=SizingMethod.HYBRID.value,
        parameters={"score": 0.5, "inv_vol": 0.5, "confidence": confidence},
        output_weights=mixed,
        diagnostics={
            "rule": (
                "normalized 0.5 score + 0.5 inv-vol composition, then confidence deployment scale"
            )
        },
    )


def size_positions(
    names: list[str],
    request: AllocationRequest,
    policy: CapitalPolicy,
    *,
    confidence: float,
) -> SizingResult:
    method = policy.sizing_method
    versions = {
        "policy": policy.config_hash,
        "snapshot": request.snapshot_id,
    }
    if method is SizingMethod.EQUAL_WEIGHT:
        result = size_equal_weight(names, policy)
    elif method is SizingMethod.SCORE_WEIGHT:
        result = size_score_weight({name: request.scores[name] for name in names})
    elif method is SizingMethod.INVERSE_VOL:
        result = size_inverse_vol(names, request.vols)
    elif method is SizingMethod.RISK_BUDGET:
        result = size_risk_budget(names, request, policy)
    elif method is SizingMethod.FRACTIONAL_KELLY:
        result = size_fractional_kelly(names, request, policy)
    elif method is SizingMethod.CONFIDENCE_SCALED:
        result = size_confidence_scaled({name: request.scores[name] for name in names}, confidence)
    elif method is SizingMethod.VOL_TARGET:
        result = size_score_weight({name: request.scores[name] for name in names})
        result = result.model_copy(
            update={
                "method_id": SizingMethod.VOL_TARGET.value,
                "diagnostics": {"rule": "score then vol-target"},
            }
        )
    else:
        result = size_hybrid(names, request, confidence)
    return result.model_copy(update={"input_versions": versions})
