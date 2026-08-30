"""Diversity, leave-one-out, attribution, and weight stability. Not causal claims."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.alpha.combinations import weighted_zscore
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.research.cross_section import pearson_ic, spearman_ic


class PairCorrelation(BaseModel):
    left: str
    right: str
    pearson: float | None = None
    spearman: float | None = None
    n: int = 0


class DiversityReport(BaseModel):
    schema_version: str = "1"
    pairs: list[PairCorrelation] = Field(default_factory=list)
    mean_abs_spearman: float | None = None
    redundancy: str | None = None
    note: str = "Low correlation is not predictive value."


class LeaveOneOutRow(BaseModel):
    dropped: str
    remaining: list[str]
    mean_ic: float | None = None
    n_scored: int = 0
    delta_ic: float | None = None


class LeaveOneOutReport(BaseModel):
    schema_version: str = "1"
    full_ic: float | None = None
    rows: list[LeaveOneOutRow] = Field(default_factory=list)
    note: str = "Leave-one-out records every subset, not only the winner."


class AttributionRow(BaseModel):
    component_id: str
    component_ic: float | None = None
    mean_weight: float | None = None
    delta_ic: float | None = None
    redundant: bool = False


class AttributionReport(BaseModel):
    schema_version: str = "1"
    best_component_id: str | None = None
    best_component_ic: float | None = None
    equal_weight_ic: float | None = None
    ensemble_ic: float | None = None
    rows: list[AttributionRow] = Field(default_factory=list)
    note: str = "ΔIC is leave-one-out association, not a causal decomposition."


class WeightStabilityReport(BaseModel):
    schema_version: str = "1"
    n_sign_changes: int = 0
    weight_variance: float | None = None
    mean_turnover: float | None = None
    max_weight_change: float | None = None
    last_hhi: float | None = None
    flags: list[str] = Field(default_factory=list)
    status: CheckResult = CheckResult.NOT_TESTED


def _mean_ic(panel: Panel, labels: Panel, dates: list[datetime]) -> tuple[float | None, int]:
    values = [
        ic
        for as_of in dates
        if (ic := spearman_ic(panel.get(as_of, {}), labels.get(as_of, {}))) is not None
    ]
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def equal_weight_panel(panels: dict[str, Panel], names: list[str], dates: list[datetime]) -> Panel:
    out: Panel = {}
    n = float(len(names))
    weights = [1.0 / n for _ in names]
    for as_of in dates:
        rows = [panels.get(name, {}).get(as_of, {}) for name in names]
        if any(not row for row in rows):
            continue
        out[as_of] = weighted_zscore(rows, weights)
    return out


def pairwise_correlations(
    panels: dict[str, Panel],
    dates: list[datetime],
    names: list[str],
) -> DiversityReport:
    pairs: list[PairCorrelation] = []
    abs_s: list[float] = []
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            pearsons: list[float] = []
            spearmans: list[float] = []
            for as_of in dates:
                a = panels.get(left, {}).get(as_of, {})
                b = panels.get(right, {}).get(as_of, {})
                p = pearson_ic(a, b)
                s = spearman_ic(a, b)
                if p is not None:
                    pearsons.append(p)
                if s is not None:
                    spearmans.append(s)
            sp = None if not spearmans else sum(spearmans) / len(spearmans)
            pr = None if not pearsons else sum(pearsons) / len(pearsons)
            if sp is not None:
                abs_s.append(abs(sp))
            pairs.append(
                PairCorrelation(
                    left=left,
                    right=right,
                    pearson=pr,
                    spearman=sp,
                    n=len(spearmans),
                )
            )
    mean_abs = None if not abs_s else sum(abs_s) / len(abs_s)
    flag = "HIGH_REDUNDANCY" if mean_abs is not None and mean_abs > 0.85 else None
    return DiversityReport(pairs=pairs, mean_abs_spearman=mean_abs, redundancy=flag)


def leave_one_out(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    names: list[str],
) -> LeaveOneOutReport:
    full = equal_weight_panel(panels, names, dates)
    full_ic, _n = _mean_ic(full, labels, dates)
    rows: list[LeaveOneOutRow] = []
    for dropped in names:
        remaining = [name for name in names if name != dropped]
        if not remaining:
            continue
        subset = equal_weight_panel(panels, remaining, dates)
        mean, n_scored = _mean_ic(subset, labels, dates)
        delta = None if full_ic is None or mean is None else full_ic - mean
        rows.append(
            LeaveOneOutRow(
                dropped=dropped,
                remaining=remaining,
                mean_ic=mean,
                n_scored=n_scored,
                delta_ic=delta,
            )
        )
    return LeaveOneOutReport(full_ic=full_ic, rows=rows)


def attribution(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    names: list[str],
    ensemble_panel: Panel,
    weights_path: list[dict[str, float]],
    diversity: DiversityReport,
) -> AttributionReport:
    component_ics: dict[str, float | None] = {}
    best_id: str | None = None
    best_ic: float | None = None
    for name in names:
        mean, _n = _mean_ic(panels.get(name, {}), labels, dates)
        component_ics[name] = mean
        if mean is not None and (best_ic is None or mean > best_ic):
            best_ic = mean
            best_id = name
    equal = equal_weight_panel(panels, names, dates)
    equal_ic, _n = _mean_ic(equal, labels, dates)
    ens_ic, _n2 = _mean_ic(ensemble_panel, labels, dates)
    loo = leave_one_out(panels, labels, dates, names)
    loo_delta = {row.dropped: row.delta_ic for row in loo.rows}
    redundant = {pair.left for pair in diversity.pairs if diversity.redundancy == "HIGH_REDUNDANCY"}
    redundant |= {
        pair.right for pair in diversity.pairs if diversity.redundancy == "HIGH_REDUNDANCY"
    }
    rows: list[AttributionRow] = []
    for name in names:
        wvals = [path.get(name, 0.0) for path in weights_path]
        mean_w = None if not wvals else sum(wvals) / len(wvals)
        rows.append(
            AttributionRow(
                component_id=name,
                component_ic=component_ics[name],
                mean_weight=mean_w,
                delta_ic=loo_delta.get(name),
                redundant=name in redundant and len(names) > 1,
            )
        )
    return AttributionReport(
        best_component_id=best_id,
        best_component_ic=best_ic,
        equal_weight_ic=equal_ic,
        ensemble_ic=ens_ic,
        rows=rows,
    )


def assess_weight_stability(weights_path: list[dict[str, float]]) -> WeightStabilityReport:
    flags: list[str] = []
    if not weights_path:
        return WeightStabilityReport(flags=["insufficient_history"], status=CheckResult.WARN)
    names = sorted({key for path in weights_path for key in path})
    turnovers: list[float] = []
    max_change = 0.0
    n_sign = 0
    series = {name: [path.get(name, 0.0) for path in weights_path] for name in names}
    for i in range(1, len(weights_path)):
        prev = weights_path[i - 1]
        cur = weights_path[i]
        keys = set(prev) | set(cur)
        delta = 0.5 * sum(abs(cur.get(k, 0.0) - prev.get(k, 0.0)) for k in keys)
        turnovers.append(delta)
        for name in names:
            a = prev.get(name, 0.0)
            b = cur.get(name, 0.0)
            max_change = max(max_change, abs(b - a))
            if (a > 1e-12) != (b > 1e-12):
                n_sign += 1
    variances: list[float] = []
    for name in names:
        vals = series[name]
        mean = sum(vals) / len(vals)
        variances.append(sum((v - mean) ** 2 for v in vals) / len(vals))
    var = None if not variances else sum(variances) / len(variances)
    last = weights_path[-1]
    hhi = sum(v * v for v in last.values())
    mean_to = None if not turnovers else sum(turnovers) / len(turnovers)
    if hhi >= 0.8 and len(last) > 1:
        flags.append("weight_concentration")
    if mean_to is not None and mean_to > 0.25:
        flags.append("high_weight_turnover")
    if n_sign >= max(len(weights_path) - 1, 1) and len(weights_path) >= 8:
        flags.append("weight_sign_instability")
    status = CheckResult.WARN if flags else CheckResult.PASS
    return WeightStabilityReport(
        n_sign_changes=n_sign,
        weight_variance=var,
        mean_turnover=mean_to,
        max_weight_change=max_change,
        last_hhi=hhi,
        flags=flags,
        status=status,
    )
