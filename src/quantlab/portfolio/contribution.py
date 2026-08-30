"""Incremental ensemble contribution. Standalone IC is not diversification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.alpha.ic import information_coefficient
from quantlab.features.engine import Panel


class ComponentContribution(BaseModel):
    alpha_id: str
    weight: float
    standalone_ic: float | None = None
    leave_one_out_ic: float | None = None
    incremental_ic: float | None = None
    score_correlation: float | None = None


class ContributionReport(BaseModel):
    schema_version: str = "1"
    ensemble_ic: float | None = None
    components: list[ComponentContribution] = Field(default_factory=list)
    note: str = "incremental IC is ensemble minus leave-one-out; not a causal claim"


def incremental_ic(
    ensemble_panel: Panel,
    component_panels: dict[str, Panel],
    weights: dict[str, float],
    label: Panel,
) -> ContributionReport:
    ens = information_coefficient(ensemble_panel, label)
    rows: list[ComponentContribution] = []
    from quantlab.features.correlation import mean_daily_spearman

    for alpha_id, panel in component_panels.items():
        stand = information_coefficient(panel, label)
        others = [p for aid, p in component_panels.items() if aid != alpha_id]
        loo_ic = None
        if others:
            from quantlab.alpha.combinations import equal_weight_zscore
            from quantlab.features.engine import Panel as PanelType

            loo: PanelType = {}
            dates = set(others[0])
            for other in others[1:]:
                dates &= set(other)
            for as_of in dates:
                loo[as_of] = equal_weight_zscore([p[as_of] for p in others])
            loo_report = information_coefficient(loo, label)
            loo_ic = loo_report.spearman_mean
        inc = None
        if ens.spearman_mean is not None and loo_ic is not None:
            inc = ens.spearman_mean - loo_ic
        corr = mean_daily_spearman(ensemble_panel, panel)
        rows.append(
            ComponentContribution(
                alpha_id=alpha_id,
                weight=weights.get(alpha_id, 0.0),
                standalone_ic=stand.spearman_mean,
                leave_one_out_ic=loo_ic,
                incremental_ic=inc,
                score_correlation=corr,
            )
        )
    return ContributionReport(ensemble_ic=ens.spearman_mean, components=rows)
