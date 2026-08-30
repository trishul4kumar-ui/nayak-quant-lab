"""Seed statistical models. Baselines come first. Complexity is explicit."""

from __future__ import annotations

from quantlab.features.registry import get_feature
from quantlab.learning.definition import (
    Algorithm,
    ModelDefinition,
    ScalingMethod,
    SelectionMethod,
)


def _versions(feature_ids: list[str]) -> dict[str, str]:
    return {fid: get_feature(fid).version for fid in feature_ids}


def seed_models() -> list[ModelDefinition]:
    mom = ["momentum_5", "momentum_20", "rolling_std_20"]
    versions = _versions(mom)
    return [
        ModelDefinition(
            model_id="no_signal",
            version="1",
            name="Constant zero score",
            algorithm=Algorithm.NO_SIGNAL,
            features=mom,
            feature_versions=versions,
            normalization=ScalingMethod.NONE,
            notes="No-information baseline. Rank IC is undefined for a constant.",
        ),
        ModelDefinition(
            model_id="mean_baseline",
            version="1",
            name="Training-mean predictor",
            algorithm=Algorithm.MEAN,
            features=mom,
            feature_versions=versions,
            normalization=ScalingMethod.NONE,
            notes="Pooled mean of realized labels. Cross-section ranks are constant.",
        ),
        ModelDefinition(
            model_id="alpha_mom20",
            version="1",
            name="Existing rank-momentum-20 alpha as a model",
            algorithm=Algorithm.ALPHA,
            features=["momentum_20"],
            feature_versions=_versions(["momentum_20"]),
            alpha_id="rank_momentum_20",
            normalization=ScalingMethod.NONE,
            notes="Prompt 06 alpha passthrough. MODEL ≠ ALPHA; this is the baseline score.",
        ),
        ModelDefinition(
            model_id="ols_mom",
            version="1",
            name="Pooled OLS on momentum and vol",
            algorithm=Algorithm.OLS,
            features=mom,
            feature_versions=versions,
        ),
        ModelDefinition(
            model_id="ridge_mom",
            version="1",
            name="Ridge on momentum and vol",
            algorithm=Algorithm.RIDGE,
            features=mom,
            feature_versions=versions,
            hyperparameters={"l2": 1.0},
        ),
        ModelDefinition(
            model_id="lasso_mom",
            version="1",
            name="Lasso on momentum and vol",
            algorithm=Algorithm.LASSO,
            features=mom,
            feature_versions=versions,
            hyperparameters={"l1": 0.01},
        ),
        ModelDefinition(
            model_id="elastic_mom",
            version="1",
            name="Elastic net on momentum and vol",
            algorithm=Algorithm.ELASTIC_NET,
            features=mom,
            feature_versions=versions,
            hyperparameters={"l1": 0.005, "l2": 0.005},
        ),
        ModelDefinition(
            model_id="huber_mom",
            version="1",
            name="Huber IRLS on momentum and vol",
            algorithm=Algorithm.HUBER,
            features=mom,
            feature_versions=versions,
            hyperparameters={"delta": 1.0},
        ),
        ModelDefinition(
            model_id="rf_mom",
            version="1",
            name="Shallow random forest",
            algorithm=Algorithm.RANDOM_FOREST,
            features=mom,
            feature_versions=versions,
            n_estimators=8,
            max_depth=2,
            min_leaf=5,
            notes="Depth and estimators are identity fields. Not an AutoML search.",
        ),
        ModelDefinition(
            model_id="gb_mom",
            version="1",
            name="Shallow gradient boosting",
            algorithm=Algorithm.GRADIENT_BOOSTING,
            features=mom,
            feature_versions=versions,
            n_estimators=8,
            max_depth=2,
            min_leaf=5,
            learning_rate=0.1,
        ),
        ModelDefinition(
            model_id="pca_ols_mom",
            version="1",
            name="Train-only PCA then OLS",
            algorithm=Algorithm.PCA_OLS,
            features=mom,
            feature_versions=versions,
            pca_components=2,
        ),
        ModelDefinition(
            model_id="select_ols_mom",
            version="1",
            name="Train-only univariate IC selection then OLS",
            algorithm=Algorithm.SELECT_OLS,
            features=mom,
            feature_versions=versions,
            selection_method=SelectionMethod.UNIVARIATE_IC,
            selection_k=2,
        ),
        ModelDefinition(
            model_id="regime_ols_mom",
            version="1",
            name="OLS with PIT vol-tercile context",
            algorithm=Algorithm.OLS,
            features=mom,
            feature_versions=versions,
            regime_model_id="vol_tercile",
            notes="Regime labels are Prompt 09 PIT rules. Smoothed HMM is blocked.",
        ),
    ]
