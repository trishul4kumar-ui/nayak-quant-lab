"""Hard vs soft constraints. Hard constraints are never silently relaxed."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.core.errors import InfeasiblePortfolio
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import TargetPosition


class ConstraintHardness(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintKind(StrEnum):
    LONG_ONLY = "long_only"
    MAX_WEIGHT = "max_weight"
    MIN_WEIGHT = "min_weight"
    MAX_GROSS = "max_gross"
    MAX_NET = "max_net"
    MIN_NET = "min_net"
    MAX_TURNOVER = "max_turnover"
    MAX_NAMES = "max_names"
    SUM_TO_ONE = "sum_to_one"
    MAX_BETA = "max_beta"
    MAX_FACTOR_EXPOSURE = "max_factor_exposure"


class ConstraintSpec(BaseModel):
    constraint_id: str
    kind: ConstraintKind
    hardness: ConstraintHardness = ConstraintHardness.HARD
    lower: float | None = None
    upper: float | None = None
    active: bool = True
    provenance: str = "portfolio_construction"
    tag: str = ""


class ConstraintResult(BaseModel):
    feasible: bool = True
    weights: dict[str, float] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def long_only_invested() -> list[ConstraintSpec]:
    return [
        ConstraintSpec(
            constraint_id="long_only",
            kind=ConstraintKind.LONG_ONLY,
            hardness=ConstraintHardness.HARD,
        ),
        ConstraintSpec(
            constraint_id="sum_to_one",
            kind=ConstraintKind.SUM_TO_ONE,
            hardness=ConstraintHardness.HARD,
            upper=1.0,
        ),
        ConstraintSpec(
            constraint_id="max_gross",
            kind=ConstraintKind.MAX_GROSS,
            hardness=ConstraintHardness.HARD,
            upper=1.0,
        ),
    ]


def long_only_set() -> list[ConstraintSpec]:
    return [
        *long_only_invested(),
        ConstraintSpec(
            constraint_id="max_name",
            kind=ConstraintKind.MAX_WEIGHT,
            hardness=ConstraintHardness.HARD,
            upper=0.5,
        ),
    ]


def long_short_set() -> list[ConstraintSpec]:
    return [
        ConstraintSpec(
            constraint_id="max_gross",
            kind=ConstraintKind.MAX_GROSS,
            hardness=ConstraintHardness.HARD,
            upper=1.0,
        ),
        ConstraintSpec(
            constraint_id="max_net",
            kind=ConstraintKind.MAX_NET,
            hardness=ConstraintHardness.HARD,
            upper=0.05,
        ),
        ConstraintSpec(
            constraint_id="min_net",
            kind=ConstraintKind.MIN_NET,
            hardness=ConstraintHardness.HARD,
            lower=-0.05,
        ),
    ]


def to_targets(weights: dict[str, float], drop_zero: bool = True) -> list[TargetPosition]:
    out: list[TargetPosition] = []
    for key, weight in sorted(weights.items()):
        if drop_zero and abs(weight) < 1e-12:
            continue
        out.append(TargetPosition(instrument=InstrumentId.parse(key), weight=weight))
    return out


def apply_constraints(
    weights: dict[str, float],
    specs: list[ConstraintSpec],
    *,
    prev_weights: dict[str, float] | None = None,
    portfolio_exposures: dict[str, float] | None = None,
) -> ConstraintResult:
    """Validate weights. Hard failures raise; soft failures are warnings."""
    from quantlab.portfolio.turnover import two_sided_turnover

    active = [s for s in specs if s.active]
    current = dict(weights)
    warnings: list[str] = []
    violations: list[str] = []

    def check(spec: ConstraintSpec, ok: bool, message: str) -> None:
        if ok:
            return
        if spec.hardness is ConstraintHardness.HARD:
            violations.append(message)
        else:
            warnings.append(message)

    for spec in active:
        values = list(current.values())
        if spec.kind is ConstraintKind.LONG_ONLY:
            check(spec, all(v >= -1e-12 for v in values), "long_only: negative weight")
        elif spec.kind is ConstraintKind.MAX_WEIGHT and spec.upper is not None:
            check(
                spec,
                all(abs(v) <= spec.upper + 1e-12 for v in values),
                f"max_weight {spec.upper}",
            )
        elif spec.kind is ConstraintKind.MIN_WEIGHT and spec.lower is not None:
            held = [v for v in values if abs(v) > 1e-12]
            check(spec, all(abs(v) >= spec.lower - 1e-12 for v in held), f"min_weight {spec.lower}")
        elif spec.kind is ConstraintKind.MAX_GROSS and spec.upper is not None:
            check(
                spec, sum(abs(v) for v in values) <= spec.upper + 1e-12, f"max_gross {spec.upper}"
            )
        elif spec.kind is ConstraintKind.MAX_NET and spec.upper is not None:
            check(spec, sum(values) <= spec.upper + 1e-12, f"max_net {spec.upper}")
        elif spec.kind is ConstraintKind.MIN_NET and spec.lower is not None:
            check(spec, sum(values) >= spec.lower - 1e-12, f"min_net {spec.lower}")
        elif spec.kind is ConstraintKind.MAX_NAMES and spec.upper is not None:
            held_n = sum(1 for v in values if abs(v) > 1e-12)
            check(spec, held_n <= spec.upper + 1e-12, f"max_names {spec.upper}")
        elif spec.kind is ConstraintKind.SUM_TO_ONE:
            cap = 1.0 if spec.upper is None else spec.upper
            total = sum(values)
            check(spec, total <= cap + 1e-9 and total >= -1e-9, f"sum_to_one cap={cap} got={total}")
        elif spec.kind is ConstraintKind.MAX_TURNOVER and spec.upper is not None:
            turn = two_sided_turnover(prev_weights or {}, current)
            check(spec, turn <= spec.upper + 1e-12, f"max_turnover {spec.upper} got={turn}")
        elif spec.kind is ConstraintKind.MAX_BETA:
            key = spec.tag or "market_ew_beta"
            if portfolio_exposures is None or key not in portfolio_exposures:
                raise InfeasiblePortfolio(
                    f"max_beta: {key} unknown; missing beta is not assumed zero"
                )
            if spec.upper is not None:
                check(
                    spec,
                    abs(portfolio_exposures[key]) <= spec.upper + 1e-12,
                    f"max_beta {spec.upper} got={portfolio_exposures[key]}",
                )
        elif spec.kind is ConstraintKind.MAX_FACTOR_EXPOSURE:
            key = spec.tag
            if not key:
                raise InfeasiblePortfolio("max_factor_exposure requires constraint.tag")
            if portfolio_exposures is None or key not in portfolio_exposures:
                raise InfeasiblePortfolio(
                    f"max_factor_exposure: {key} unknown; missing exposure is not assumed zero"
                )
            if spec.upper is not None:
                check(
                    spec,
                    abs(portfolio_exposures[key]) <= spec.upper + 1e-12,
                    f"max_factor_exposure {key} {spec.upper}",
                )

    if violations:
        raise InfeasiblePortfolio("; ".join(violations))
    return ConstraintResult(feasible=True, weights=current, warnings=warnings, violations=[])
