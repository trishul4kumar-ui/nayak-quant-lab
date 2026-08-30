"""Seed combination ensembles. Prompt 07 alpha ensembles remain in quantlab.alpha.ensemble."""

from __future__ import annotations

from quantlab.ensemble.definition import (
    CombinationMethod,
    ComponentType,
    EnsembleComponent,
    EnsembleDefinition,
    WeightingPolicy,
)


def _alphas(*ids: str) -> list[EnsembleComponent]:
    return [
        EnsembleComponent(component_id=item, component_type=ComponentType.ALPHA) for item in ids
    ]


def seed_ensembles() -> list[EnsembleDefinition]:
    mom = ("rank_momentum_5", "rank_momentum_20")
    return [
        EnsembleDefinition(
            ensemble_id="ew_mom_5_20",
            version="1",
            name="Equal-weight rank momentum 5 + 20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.EQUAL,
            notes=(
                "Mandatory equal-weight baseline. "
                "Distinct from Prompt 07 mom_5_20 portfolio ensemble."
            ),
        ),
        EnsembleDefinition(
            ensemble_id="static_ic_mom",
            version="1",
            name="Static expanding-IC weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.STATIC_IC,
            notes="Weights from mean PIT IC through T-1. Fallback equal weight is explicit.",
        ),
        EnsembleDefinition(
            ensemble_id="invvol_mom",
            version="1",
            name="Inverse-vol weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.INVERSE_VOL,
        ),
        EnsembleDefinition(
            ensemble_id="corr_mom",
            version="1",
            name="Correlation-aware weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.CORRELATION_AWARE,
            shrinkage=0.2,
            notes=(
                "Component-IC covariance uses Prompt 08 diagonal shrinkage. "
                "Not a second asset-cov engine."
            ),
        ),
        EnsembleDefinition(
            ensemble_id="roll_ic_mom",
            version="1",
            name="Rolling-IC dynamic weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.ROLLING_IC,
            training_window=20,
            notes="max(mean trailing IC, 0). Does not flip component sign.",
        ),
        EnsembleDefinition(
            ensemble_id="ewma_ic_mom_ens",
            version="1",
            name="EWMA-IC dynamic weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.EWMA_IC,
            half_life=10.0,
            notes="Reuses Prompt 10 EWMA. Distinct from adaptive ensemble_ic_mom.",
        ),
        EnsembleDefinition(
            ensemble_id="ridge_stack_mom",
            version="1",
            name="Ridge stack on walk-forward mom5 + mom20 scores",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.RIDGE_STACK,
            combination_method=CombinationMethod.STACKING,
            l2=1.0,
            notes="Meta-model trains only on OOS base scores with labels available at T.",
        ),
        EnsembleDefinition(
            ensemble_id="elastic_stack_mom",
            version="1",
            name="Elastic-net stack on walk-forward mom5 + mom20 scores",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.ELASTIC_STACK,
            combination_method=CombinationMethod.STACKING,
            l1=0.01,
            l2=1.0,
        ),
        EnsembleDefinition(
            ensemble_id="meta_ols_mom",
            version="1",
            name="OLS meta-alpha on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.OLS_META,
            combination_method=CombinationMethod.META_ALPHA,
            is_meta_alpha=True,
            meta_alpha_id="meta_ols_mom",
            notes="META-ALPHA ≠ ALPHA. Same walk-forward stacking contract as ridge.",
        ),
        EnsembleDefinition(
            ensemble_id="rank_meta_mom",
            version="1",
            name="Rank-sum meta-alpha on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.RANK_SUM,
            combination_method=CombinationMethod.RANK_SUM,
            is_meta_alpha=True,
            meta_alpha_id="rank_meta_mom",
            notes="rank(A)+rank(B) baseline. Not proof of alpha.",
        ),
        EnsembleDefinition(
            ensemble_id="hetero_alpha_ols",
            version="1",
            name="Equal-weight rank_momentum_20 + ols_mom",
            components=[
                EnsembleComponent(
                    component_id="rank_momentum_20",
                    component_type=ComponentType.ALPHA,
                ),
                EnsembleComponent(
                    component_id="ols_mom",
                    component_type=ComponentType.MODEL,
                ),
            ],
            weighting_policy=WeightingPolicy.EQUAL,
            notes="Heterogeneous ALPHA + MODEL. Identities remain independent.",
        ),
        EnsembleDefinition(
            ensemble_id="regime_ew_mom",
            version="1",
            name="Equal-weight mom5+mom20 with PIT vol_tercile context",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.EQUAL,
            regime_model_id="vol_tercile",
            regime_policy="record",
            notes="Predictive vol_tercile only. Smoothed HMM is blocked.",
        ),
        EnsembleDefinition(
            ensemble_id="bayes_ic_mom",
            version="1",
            name="Beta-Bernoulli IC-hit weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.BAYESIAN_HIT,
            notes="Lightweight P(IC>0) heuristic. Rigorous Bayesian posteriors stay NOT_TESTED.",
        ),
        EnsembleDefinition(
            ensemble_id="reg_mom",
            version="1",
            name="Regularized IC/risk weights on mom5 + mom20",
            components=_alphas(*mom),
            weighting_policy=WeightingPolicy.REGULARIZED,
            risk_aversion=1.0,
            weight_stability_penalty=0.1,
            shrinkage=0.2,
        ),
    ]
