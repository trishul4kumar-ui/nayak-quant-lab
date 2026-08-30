"""Fit/predict dispatch. Scaling, selection, and PCA use only the training window."""

from __future__ import annotations

from datetime import datetime

from quantlab import __version__
from quantlab.core.errors import ModelError
from quantlab.learning.definition import Algorithm, ModelDefinition, SelectionMethod
from quantlab.learning.linear import (
    fit_elastic,
    fit_huber,
    fit_lasso,
    fit_ols,
    fit_ridge,
    predict_linear,
    rmse,
)
from quantlab.learning.pca import apply_pca, fit_pca
from quantlab.learning.scale import apply_scaler, fit_scaler
from quantlab.learning.selection import project, select_features
from quantlab.learning.state import FitArtifact, ModelState
from quantlab.learning.trees import (
    fit_boosting,
    fit_forest,
    predict_boosting,
    predict_forest,
)


def fit_model(
    model: ModelDefinition,
    x_rows: list[list[float]],
    y: list[float],
    *,
    cutoff: datetime,
    training_start: datetime | None,
    training_end: datetime | None,
    snapshot_id: str = "",
    feature_names: list[str] | None = None,
) -> ModelState:
    names = feature_names or list(model.features)
    if len(x_rows) < model.min_obs:
        raise ModelError("insufficient_history")
    scaler = fit_scaler(x_rows, model.normalization)
    scaled = apply_scaler(x_rows, scaler)
    selected = list(names)
    work = scaled
    pca = None
    if (
        model.algorithm is Algorithm.SELECT_OLS
        or model.selection_method is not SelectionMethod.NONE
    ):
        l1 = float(model.hyperparameters.get("l1", 0.01))
        selected = select_features(
            scaled, y, names, model.selection_method, model.selection_k, l1=l1
        )
        work = project(scaled, names, selected)
    if model.algorithm is Algorithm.PCA_OLS:
        pca = fit_pca(scaled, model.pca_components)
        work = apply_pca(scaled, pca)
        selected = [f"pc{i + 1}" for i in range(pca.n_components)]
    artifact = _fit_algorithm(model, work, y, selected)
    artifact.scaler = scaler
    artifact.pca = pca
    artifact.selected = selected
    artifact.feature_names = list(names)
    artifact.n_train = len(y)
    artifact.train_rmse = rmse(_predict_artifact(artifact, x_rows), y)
    return ModelState(
        model_definition_id=f"{model.model_id}@{model.version}",
        fit_timestamp=cutoff,
        training_start=training_start,
        training_end=training_end,
        available_information_cutoff=cutoff,
        artifact=artifact,
        feature_schema=list(names),
        training_sample_count=len(y),
        random_seed=model.random_seed,
        software_version=__version__,
        data_snapshot=snapshot_id,
        config_hash=model.identity_hash(),
    )


def predict_model(state: ModelState, x_rows: list[list[float]]) -> list[float]:
    if state.artifact is None:
        raise ModelError("prediction_failure: empty model state")
    return _predict_artifact(state.artifact, x_rows)


def _fit_algorithm(
    model: ModelDefinition,
    work: list[list[float]],
    y: list[float],
    selected: list[str],
) -> FitArtifact:
    kind = model.algorithm
    if kind is Algorithm.NO_SIGNAL:
        return FitArtifact(algorithm=kind, train_mean=0.0)
    if kind is Algorithm.MEAN:
        return FitArtifact(algorithm=kind, train_mean=sum(y) / len(y))
    if kind is Algorithm.ALPHA:
        return FitArtifact(algorithm=kind)
    if kind is Algorithm.RANDOM_FOREST:
        trees = fit_forest(
            work,
            y,
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            min_leaf=model.min_leaf,
            seed=model.random_seed,
        )
        return FitArtifact(algorithm=kind, trees=trees, selected=selected)
    if kind is Algorithm.GRADIENT_BOOSTING:
        init, trees = fit_boosting(
            work,
            y,
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            min_leaf=model.min_leaf,
            learning_rate=model.learning_rate,
            seed=model.random_seed,
        )
        return FitArtifact(
            algorithm=kind,
            trees=trees,
            init_pred=init,
            learning_rate=model.learning_rate,
            selected=selected,
        )
    if kind is Algorithm.RIDGE:
        coef, intercept, cond = fit_ridge(work, y, float(model.hyperparameters.get("l2", 1.0)))
    elif kind is Algorithm.LASSO:
        coef, intercept, cond = fit_lasso(work, y, float(model.hyperparameters.get("l1", 0.01)))
    elif kind is Algorithm.ELASTIC_NET:
        coef, intercept, cond = fit_elastic(
            work,
            y,
            l1=float(model.hyperparameters.get("l1", 0.005)),
            l2=float(model.hyperparameters.get("l2", 0.005)),
        )
    elif kind is Algorithm.HUBER:
        coef, intercept, cond = fit_huber(work, y, float(model.hyperparameters.get("delta", 1.0)))
    else:
        coef, intercept, cond = fit_ols(work, y)
    return FitArtifact(
        algorithm=kind,
        intercept=intercept,
        coefficients=coef,
        selected=selected,
        condition_number=cond,
    )


def _predict_artifact(artifact: FitArtifact, x_rows: list[list[float]]) -> list[float]:
    if artifact.algorithm is Algorithm.NO_SIGNAL:
        return [0.0] * len(x_rows)
    if artifact.algorithm is Algorithm.MEAN:
        mu = 0.0 if artifact.train_mean is None else artifact.train_mean
        return [mu] * len(x_rows)
    if artifact.algorithm is Algorithm.ALPHA:
        raise ModelError("alpha passthrough does not use a fitted artifact")
    names = artifact.feature_names or []
    work = x_rows
    if artifact.scaler is not None:
        work = apply_scaler(work, artifact.scaler)
    if artifact.pca is not None:
        work = apply_pca(work, artifact.pca)
    elif (
        artifact.selected
        and names
        and artifact.algorithm is Algorithm.SELECT_OLS
        or (
            artifact.selected
            and names
            and artifact.algorithm in {Algorithm.RANDOM_FOREST, Algorithm.GRADIENT_BOOSTING}
            and artifact.selected != names
        )
    ):
        work = project(work, names, artifact.selected)
    if artifact.algorithm is Algorithm.RANDOM_FOREST:
        return predict_forest(artifact.trees, work)
    if artifact.algorithm is Algorithm.GRADIENT_BOOSTING:
        return predict_boosting(
            artifact.init_pred or 0.0, artifact.trees, artifact.learning_rate or 0.1, work
        )
    return predict_linear(work, artifact.coefficients, artifact.intercept)
