"""Versioned alpha ensembles. Weights are explicit; test-set search is forbidden."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.alpha.combinations import combine_panels
from quantlab.alpha.definition import AlphaDefinition, get_alpha
from quantlab.backtest.spec import config_hash
from quantlab.features.engine import Panel


class EnsembleMethod(StrEnum):
    EQUAL_WEIGHT = "equal_weight"
    FIXED_WEIGHTS = "fixed_weights"
    RANK_AVERAGE = "rank_average"
    ZSCORE_AVERAGE = "zscore_average"
    WEIGHTED_RANK = "weighted_rank"


class EnsembleComponent(BaseModel):
    alpha_id: str
    weight: float
    version: str = "1"


class AlphaEnsemble(BaseModel):
    ensemble_id: str
    version: str
    name: str
    components: list[EnsembleComponent]
    method: EnsembleMethod = EnsembleMethod.EQUAL_WEIGHT
    expected_direction: str = "long_high"
    hypothesis_id: str = ""
    lineage: dict[str, str] = Field(default_factory=dict)
    notes: str = ""
    implementation_version: str = "0.7.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "ensemble_id": self.ensemble_id,
                "version": self.version,
                "components": [c.model_dump() for c in self.components],
                "method": self.method.value,
                "expected_direction": self.expected_direction,
            }
        )

    def weights(self) -> list[float]:
        return [c.weight for c in self.components]

    def alpha_ids(self) -> list[str]:
        return [c.alpha_id for c in self.components]


def score_sign(expected_direction: str) -> int:
    lowered = expected_direction.lower().strip()
    if lowered in {"long_low", "short_high", "-1", "negative"}:
        return -1
    return 1


def apply_sign(scores: dict[str, float], expected_direction: str) -> dict[str, float]:
    sign = score_sign(expected_direction)
    if sign == 1:
        return dict(scores)
    return {key: -value for key, value in scores.items()}


def combine_alpha_panels(
    ensemble: AlphaEnsemble,
    panels: list[Panel],
) -> Panel:
    if len(panels) != len(ensemble.components):
        raise ValueError("panel count must match ensemble components")
    method = ensemble.method
    if method is EnsembleMethod.WEIGHTED_RANK:
        from quantlab.math.metrics import cross_sectional_ranks

        dates = set(panels[0])
        for panel in panels[1:]:
            dates &= set(panel)
        weights = ensemble.weights()
        total = sum(weights)
        if total == 0:
            raise ValueError("ensemble weights must not sum to zero")
        out: Panel = {}
        for as_of in sorted(dates):
            ranks = [cross_sectional_ranks(panel[as_of]) for panel in panels]
            keys = set(ranks[0])
            for row in ranks[1:]:
                keys &= set(row)
            out[as_of] = {
                key: sum(weights[i] * ranks[i][key] for i in range(len(ranks))) / total
                for key in keys
            }
        return apply_panel_sign(out, ensemble.expected_direction)
    if method is EnsembleMethod.RANK_AVERAGE:
        combined = combine_panels(panels, "rank_average")
    elif method is EnsembleMethod.FIXED_WEIGHTS:
        combined = combine_panels(panels, "weighted_zscore", ensemble.weights())
    else:
        combined = combine_panels(panels, "equal_weight_zscore")
    return apply_panel_sign(combined, ensemble.expected_direction)


def apply_panel_sign(panel: Panel, expected_direction: str) -> Panel:
    if score_sign(expected_direction) == 1:
        return panel
    return {as_of: apply_sign(row, expected_direction) for as_of, row in panel.items()}


def resolve_components(ensemble: AlphaEnsemble) -> list[AlphaDefinition]:
    return [get_alpha(item.alpha_id) for item in ensemble.components]


def seed_ensembles() -> list[AlphaEnsemble]:
    return [
        AlphaEnsemble(
            ensemble_id="mom20",
            version="1",
            name="Single 20-session momentum",
            components=[EnsembleComponent(alpha_id="rank_momentum_20", weight=1.0)],
            method=EnsembleMethod.EQUAL_WEIGHT,
            hypothesis_id="cs_momentum_persists",
            lineage={"alphas": "rank_momentum_20@1"},
        ),
        AlphaEnsemble(
            ensemble_id="mom_5_20",
            version="1",
            name="Equal-weight 5- and 20-session momentum",
            components=[
                EnsembleComponent(alpha_id="rank_momentum_5", weight=0.5),
                EnsembleComponent(alpha_id="rank_momentum_20", weight=0.5),
            ],
            method=EnsembleMethod.EQUAL_WEIGHT,
            hypothesis_id="cs_momentum_persists",
            lineage={"alphas": "rank_momentum_5@1,rank_momentum_20@1"},
            notes="Fixed 50/50. Not fit on the test set.",
        ),
        AlphaEnsemble(
            ensemble_id="mom_minus_vol",
            version="1",
            name="Momentum minus volatility alpha",
            components=[EnsembleComponent(alpha_id="momentum_minus_vol", weight=1.0)],
            method=EnsembleMethod.EQUAL_WEIGHT,
            hypothesis_id="momentum_net_of_vol",
            lineage={"alphas": "momentum_minus_vol@1"},
        ),
    ]


_ENSEMBLES = {item.ensemble_id: item for item in seed_ensembles()}


def get_ensemble(ensemble_id: str) -> AlphaEnsemble:
    if ensemble_id not in _ENSEMBLES:
        raise KeyError(f"unknown ensemble {ensemble_id}")
    return _ENSEMBLES[ensemble_id]


def list_ensembles() -> list[AlphaEnsemble]:
    return list(_ENSEMBLES.values())
