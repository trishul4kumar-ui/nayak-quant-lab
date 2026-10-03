"""Expanding PIT walk-forward. Never fit-then-replay unless marked leaky."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import ModelError
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.learning.dataset import ModelDataset, labeled_rows, row_xy
from quantlab.learning.definition import Algorithm, ModelDefinition
from quantlab.learning.estimators import fit_model, predict_model
from quantlab.learning.linear import rmse
from quantlab.learning.state import ModelState
from quantlab.research.cross_section import spearman_ic


class LeakFlags(BaseModel):
    replay_full_sample: bool = False
    future_scaler: bool = False
    future_pca: bool = False
    future_selection: bool = False
    future_hyperparameter: bool = False
    label_as_feature: bool = False
    holdout_contaminated: bool = False
    permute_labels: bool = False


class WalkForwardPoint(BaseModel):
    as_of: datetime
    ic: float | None = None
    n_train: int = 0
    coverage: bool = False
    rmse: float | None = None


class WalkForwardResult(BaseModel):
    schema_version: str = "1"
    n_predictions: int = 0
    n_scored: int = 0
    mean_ic: float | None = None
    oos_rmse: float | None = None
    train_rmse: float | None = None
    coverage: float | None = None
    points: list[WalkForwardPoint] = Field(default_factory=list)
    final_state: ModelState | None = None
    n_candidates: int = 1
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "predict at T using a model frozen on labels available at T"


def run_walkforward(
    model: ModelDefinition,
    dataset: ModelDataset,
    *,
    leaks: LeakFlags | None = None,
    snapshot_id: str = "",
) -> tuple[Panel, WalkForwardResult]:
    flags = leaks or LeakFlags()
    dates = list(dataset.dates)
    if flags.permute_labels:
        dataset = _permute_labels(dataset, model.random_seed)
    predictions: Panel = {}
    points: list[WalkForwardPoint] = []
    state: ModelState | None = None
    oos_pred: list[float] = []
    oos_y: list[float] = []
    leak_xy = _all_labeled(dataset, dates, model, flags) if _needs_full_sample(flags) else None

    for i, as_of in enumerate(dates):
        train_dates = dates[:i]
        scores, state, n_train = _predict_at(
            model, dataset, as_of, train_dates, flags, leak_xy, snapshot_id, state
        )
        predictions[as_of] = scores
        ic = spearman_ic(scores, dataset.labels.get(as_of, {}))
        point_rmse = None
        labels = dataset.labels.get(as_of, {})
        if scores and labels:
            paired_p = [scores[k] for k in scores if k in labels]
            paired_y = [labels[k] for k in scores if k in labels]
            point_rmse = rmse(paired_p, paired_y)
            oos_pred.extend(paired_p)
            oos_y.extend(paired_y)
        points.append(
            WalkForwardPoint(
                as_of=as_of,
                ic=ic,
                n_train=n_train,
                coverage=bool(scores),
                rmse=point_rmse,
            )
        )

    scored = [p.ic for p in points if p.ic is not None]
    n_pred = sum(1 for p in points if p.coverage)
    mean = None if not scored else sum(scored) / len(scored)
    status = CheckResult.NOT_TESTED if len(scored) < 8 else CheckResult.PASS
    train_rmse = None if state is None or state.artifact is None else state.artifact.train_rmse
    return predictions, WalkForwardResult(
        n_predictions=n_pred,
        n_scored=len(scored),
        mean_ic=mean,
        oos_rmse=rmse(oos_pred, oos_y),
        train_rmse=train_rmse,
        coverage=None if not points else n_pred / len(points),
        points=points,
        final_state=state,
        n_candidates=1,
        status=status,
        note=(
            "leaky: fitted with information after T"
            if _needs_full_sample(flags)
            else "predict at T using a model frozen on labels available at T"
        ),
    )


def _predict_at(
    model: ModelDefinition,
    dataset: ModelDataset,
    as_of: datetime,
    train_dates: list[datetime],
    flags: LeakFlags,
    leak_xy: tuple[list[list[float]], list[float]] | None,
    snapshot_id: str,
    prev: ModelState | None,
) -> tuple[dict[str, float], ModelState | None, int]:
    insts, x_now, _y_now = row_xy(
        dataset, as_of, model.features, label_as_feature=flags.label_as_feature
    )
    if model.algorithm is Algorithm.ALPHA:
        return dict(dataset.alpha_panel.get(as_of, {})), prev, 0
    if model.algorithm is Algorithm.NO_SIGNAL:
        return {name: 0.0 for name in insts}, prev, 0
    if not insts:
        return {}, prev, 0
    if _needs_full_sample(flags):
        if leak_xy is None:
            raise ModelError("future_information: full-sample matrix missing")
        xs, ys = leak_xy
        if prev is not None and prev.artifact is not None:
            preds = predict_model(prev, x_now)
            return dict(zip(insts, preds, strict=True)), prev, prev.training_sample_count
        if flags.future_hyperparameter and model.algorithm.value in {
            "ridge",
            "lasso",
            "elastic_net",
        }:
            model = _pick_lambda(model, xs, ys)
        state = fit_model(
            model,
            xs,
            ys,
            cutoff=as_of,
            training_start=dataset.dates[0] if dataset.dates else as_of,
            training_end=dataset.dates[-1] if dataset.dates else as_of,
            snapshot_id=snapshot_id,
            feature_names=list(model.features),
        )
        preds = predict_model(state, x_now)
        return dict(zip(insts, preds, strict=True)), state, len(ys)
    if len(train_dates) < model.min_train_dates:
        return {}, prev, 0
    try:
        xs, ys = labeled_rows(
            dataset,
            train_dates,
            model.features,
            label_as_feature=flags.label_as_feature,
            training_cutoff=as_of,
        )
    except ModelError:
        return {}, prev, 0
    if len(ys) < model.min_obs:
        return {}, prev, 0
    state = fit_model(
        model,
        xs,
        ys,
        cutoff=as_of,
        training_start=train_dates[0],
        training_end=train_dates[-1],
        snapshot_id=snapshot_id,
        feature_names=list(model.features),
    )
    preds = predict_model(state, x_now)
    return dict(zip(insts, preds, strict=True)), state, len(ys)


def _needs_full_sample(flags: LeakFlags) -> bool:
    return (
        flags.replay_full_sample
        or flags.future_scaler
        or flags.future_pca
        or flags.future_selection
        or flags.future_hyperparameter
        or flags.label_as_feature
        or flags.holdout_contaminated
    )


def _all_labeled(
    dataset: ModelDataset,
    dates: list[datetime],
    model: ModelDefinition,
    flags: LeakFlags,
) -> tuple[list[list[float]], list[float]]:
    return labeled_rows(dataset, dates, model.features, label_as_feature=flags.label_as_feature)


def _pick_lambda(model: ModelDefinition, xs: list[list[float]], ys: list[float]) -> ModelDefinition:
    from quantlab.learning.linear import fit_ridge, predict_linear
    from quantlab.learning.linear import rmse as fit_rmse

    best = float(model.hyperparameters.get("l2", 1.0))
    best_err = float("inf")
    for lam in (0.1, 1.0, 10.0, 100.0):
        coef, intercept, _cond = fit_ridge(xs, ys, lam)
        err = fit_rmse(predict_linear(xs, coef, intercept), ys)
        if err is not None and err < best_err:
            best_err = err
            best = lam
    hp = dict(model.hyperparameters)
    hp["l2"] = best
    return model.model_copy(update={"hyperparameters": hp})


def _permute_labels(dataset: ModelDataset, seed: int) -> ModelDataset:
    values: list[float] = []
    keys: list[tuple[datetime, str]] = []
    for as_of, row in dataset.labels.items():
        for inst, value in row.items():
            keys.append((as_of, inst))
            values.append(value)
    rng = [seed * 997 + 13]
    shuffled = list(values)
    for i in range(len(shuffled) - 1, 0, -1):
        rng[0] = (1103515245 * rng[0] + 12345) % (2**31)
        j = rng[0] % (i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    labels: Panel = {}
    for (as_of, inst), value in zip(keys, shuffled, strict=True):
        labels.setdefault(as_of, {})[inst] = value
    return dataset.model_copy(update={"labels": labels})
