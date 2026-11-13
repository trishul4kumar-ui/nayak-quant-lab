"""Adapters to existing numerical engines, with explicit exploratory contracts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import numpy as np

from quantlab.app.research_workbench import (
    FrozenResearchResult,
    ResearchRunParameters,
    ResearchSeries,
)
from quantlab.core.errors import DataIntegrityError
from quantlab.features.engine import Panel, compute_panel
from quantlab.features.registry import get_feature
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.research.exploratory import ExploratoryFrame


def available_research_specifications(engine: str) -> tuple[str, ...]:
    if engine == "features":
        from quantlab.features.registry import list_features

        return tuple(row.feature_id for row in list_features())
    if engine == "alpha":
        from quantlab.alpha.definition import list_alphas

        return tuple(row.alpha_id for row in list_alphas())
    if engine == "regime":
        from quantlab.regimes.registry import list_regime_models

        return tuple(row.regime_model_id for row in list_regime_models())
    if engine == "adaptive":
        from quantlab.adaptive.registry import list_adaptive_models

        return tuple(row.adaptive_model_id for row in list_adaptive_models())
    if engine == "model":
        from quantlab.learning.registry import list_models

        return tuple(row.model_id for row in list_models())
    if engine == "ensemble":
        from quantlab.ensemble.registry import list_ensembles

        return tuple(row.ensemble_id for row in list_ensembles())
    if engine == "portfolio":
        from quantlab.portfolio.spec import list_portfolio_models

        return tuple(row.portfolio_id for row in list_portfolio_models())
    if engine == "risk":
        from quantlab.risk.model import list_risk_models

        return tuple(row.risk_model_id for row in list_risk_models())
    if engine == "econometrics":
        return ("stationarity_returns", "stationarity_log_price")
    if engine == "discovery":
        return ("GP-MOM-VOL-001",)
    return ()


def calculate_research(
    frame: ExploratoryFrame,
    parameters: ResearchRunParameters,
    specification: str,
    *,
    cancelled: Callable[[], None],
    parents: tuple[FrozenResearchResult, ...] = (),
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    cancelled()
    if specification not in available_research_specifications(parameters.engine):
        raise DataIntegrityError(
            "UNKNOWN_RESEARCH_SPECIFICATION: choose a definition for this engine"
        )
    names = [str(i.id) for i in frame.instruments]
    if parameters.engine in {"alpha", "adaptive", "ensemble", "discovery"} and len(names) < 3:
        raise DataIntegrityError(
            "CROSS_SECTION_REQUIRED: this method needs at least 3 aligned instruments; "
            "single-stock feature values, regimes and econometrics remain available."
        )
    if parameters.engine in {"portfolio", "risk"} and len(names) < 2:
        raise DataIntegrityError("MULTI_INSTRUMENT_REQUIRED: select at least 2 aligned instruments")
    if (
        parameters.engine in {"adaptive", "model", "ensemble", "portfolio", "discovery"}
        and parameters.horizon != 1
    ):
        raise DataIntegrityError(
            "HORIZON_NOT_SUPPORTED: this versioned engine uses a 1-bar forward label"
        )
    dispatch = {
        "features": _features,
        "alpha": _alpha,
        "regime": _regime,
        "adaptive": _adaptive,
        "model": _model,
        "ensemble": _ensemble,
        "portfolio": _portfolio,
        "risk": _risk,
        "econometrics": _econometrics,
        "discovery": _discovery,
    }
    if parameters.engine == "ensemble":
        report, series, warnings = _ensemble(frame, parameters, specification, cancelled, parents)
    elif parameters.engine == "portfolio":
        report, series, warnings = _portfolio(frame, parameters, specification, cancelled, parents)
    elif parameters.engine == "risk":
        report, series, warnings = _risk(frame, parameters, specification, cancelled, parents)
    else:
        report, series, warnings = dispatch[parameters.engine](
            frame, parameters, specification, cancelled
        )
    report["sample"] = {
        "aligned_bars": len(frame.dates),
        "instruments": len(names),
        "universe": names,
        "interval": frame.interval,
        "missing_volume": list(frame.missing_volume),
    }
    report["analytical_clock"] = "Interval close assumed; historical availability NOT_TESTED"
    return report, series, warnings


def _report(metrics: dict[str, Any], units: dict[str, str], **extra: Any) -> dict[str, Any]:
    return {"metrics": metrics, "metric_units": units, "tables": [], **extra}


def _table(name: str, columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"name": name, "columns": columns, "rows": rows}


def _panel_series(
    panel: Panel, name: str, unit: str, dates: tuple[datetime, ...]
) -> list[ResearchSeries]:
    names = sorted({key for row in panel.values() for key in row})
    return [
        ResearchSeries(
            name=name,
            instrument=key,
            unit=unit,
            timestamps=dates,
            values=tuple(panel.get(date, {}).get(key) for date in dates),
        )
        for key in names
    ]


def _ensure_feature(frame: ExploratoryFrame, feature_id: str) -> None:
    from quantlab.features.definition import FeatureOperator

    definition = get_feature(feature_id)
    if definition.operator in {FeatureOperator.NOT_IMPLEMENTED, FeatureOperator.ROLLING_BETA}:
        raise DataIntegrityError("FEATURE_SOURCE_UNAVAILABLE: " + (definition.notes or feature_id))
    if frame.missing_volume and (
        "volume" in definition.inputs or any("volume" in v for v in definition.inputs)
    ):
        raise DataIntegrityError(
            "VOLUME_UNAVAILABLE: source volume is missing; zero is not a substitute"
        )
    if len(frame.dates) < definition.lookback + 3:
        raise DataIntegrityError(
            f"FEATURE_WARMUP_REQUIRED: {feature_id} needs at least "
            f"{definition.lookback + 3} aligned bars"
        )


def _ensure_alpha_sources(frame: ExploratoryFrame, alpha_id: str) -> None:
    from quantlab.alpha.definition import get_alpha

    for feature_id in get_alpha(alpha_id).input_features:
        _ensure_feature(frame, feature_id)


def _ensure_component_sources(frame: ExploratoryFrame, definition: Any) -> None:
    from quantlab.adaptive.registry import get_adaptive_model
    from quantlab.ensemble.definition import ComponentType
    from quantlab.factors.definition import FactorSource
    from quantlab.factors.registry import get_factor
    from quantlab.learning.registry import get_model

    for item in definition.components:
        if item.component_type is ComponentType.ALPHA:
            _ensure_alpha_sources(frame, item.component_id)
        elif item.component_type in {ComponentType.MODEL, ComponentType.REGIME_CONDITIONED_MODEL}:
            for fid in get_model(item.component_id).features:
                _ensure_feature(frame, fid)
        elif item.component_type is ComponentType.ADAPTIVE_MODEL:
            for alpha_id in get_adaptive_model(item.component_id).alpha_ids:
                _ensure_alpha_sources(frame, alpha_id)
        elif item.component_type is ComponentType.FACTOR_SIGNAL:
            factor = get_factor(item.component_id)
            if factor.source is FactorSource.FEATURE:
                _ensure_feature(frame, factor.feature_id)
            elif factor.source is not FactorSource.EQUAL_WEIGHT_MARKET_BETA:
                raise DataIntegrityError("FACTOR_SOURCE_UNAVAILABLE: " + factor.factor_id)


def _feature_diagnostics(
    frame: ExploratoryFrame,
    panel: Panel,
    horizon: int,
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.alpha.ic import information_coefficient
    from quantlab.features.quality import summarize_quality
    from quantlab.research.cross_section import spearman_ic

    quality = summarize_quality(panel, expected_names=len(frame.bars))
    slots = len(frame.dates) * len(frame.bars)
    observed = sum(len(row) for row in panel.values())
    coverage = observed / slots
    quality = quality.model_copy(update={"coverage": coverage, "missingness": 1 - coverage})
    labels = compute_label_panel(forward_return(horizon), frame.bars, list(frame.dates))
    ic = information_coefficient(panel, labels)
    points = tuple(spearman_ic(panel.get(t, {}), labels.get(t, {})) for t in frame.dates)
    series = []
    warnings = []
    if len(frame.bars) < 3:
        warnings.append(
            "Cross-sectional IC/quantiles unavailable: fewer than 3 aligned instruments. "
            "No substitute time-series IC is reported."
        )
    else:
        series.append(
            ResearchSeries(
                name="Cross-sectional rank IC",
                unit="rank correlation",
                timestamps=frame.dates,
                values=points,
            )
        )
    metrics = {
        "observations": observed,
        "coverage": coverage,
        "missingness_including_warmup": 1 - coverage,
        "mean": quality.mean,
        "standard_deviation": quality.std,
        "rank_ic": ic.spearman_mean,
        "ic_dates": ic.n,
    }
    report = _report(
        metrics,
        {
            "observations": "instrument-bars",
            "coverage": "fraction",
            "missingness_including_warmup": "fraction",
            "mean": "feature units",
            "standard_deviation": "feature units",
            "rank_ic": "rank correlation",
            "ic_dates": "bars",
        },
        quality=quality.model_dump(mode="json"),
        ic=ic.model_dump(mode="json"),
        label={"horizon": horizon, "kind": "forward_close_return", "unit": "fraction"},
        scores=panel[max(panel)] if panel else {},
        score_panel={date.isoformat(): values for date, values in panel.items()},
        score_kind="feature_value_not_expected_return",
    )
    report["tables"] = [
        _table(
            "Feature coverage by instrument",
            ["Instrument", "Values", "Expected bars", "Coverage including warmup"],
            [
                [
                    str(key),
                    sum(str(key) in row for row in panel.values()),
                    len(frame.dates),
                    sum(str(key) in row for row in panel.values()) / len(frame.dates),
                ]
                for key in frame.bars
            ],
        )
    ]
    return report, series, warnings


def _features(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.features.definition import FeatureDefinition

    _ensure_feature(frame, spec)
    definition = FeatureDefinition.model_validate(
        {**get_feature(spec).model_dump(), "lookback": p.lookback}
    )
    panel = compute_panel(definition, frame.bars, list(frame.dates))
    cancelled()
    if not panel:
        raise DataIntegrityError(
            "FEATURE_NO_VALUES: method, warmup or source capability unavailable"
        )
    report, series, warnings = _feature_diagnostics(frame, panel, p.horizon)
    report["definition"] = definition.model_dump(mode="json")
    from quantlab.features.definition import FeatureOperator

    unit = {
        FeatureOperator.TRAILING_RETURN: "return fraction",
        FeatureOperator.ROLLING_MEAN: "provider price units",
        FeatureOperator.ROLLING_STD: "return fraction per aligned interval",
        FeatureOperator.ZSCORE_TS: "z-score",
        FeatureOperator.HIGH_LOW_RANGE: "fraction",
        FeatureOperator.CLOSE_TO_HIGH: "fraction",
        FeatureOperator.CLOSE_TO_LOW: "fraction",
        FeatureOperator.LAST_VOLUME: "provider volume units",
        FeatureOperator.VOLUME_CHANGE: "fraction",
        FeatureOperator.VOLUME_ZSCORE: "z-score",
        FeatureOperator.DISTANCE_FROM_MEAN: "fraction",
        FeatureOperator.DOLLAR_TURNOVER_RATIO: "ratio",
    }.get(definition.operator, "feature units")
    report["metric_units"].update(mean=unit, standard_deviation=unit)
    return (
        report,
        _panel_series(panel, definition.name, unit, frame.dates) + series,
        warnings,
    )


def _alpha(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.alpha.combinations import combine_panels
    from quantlab.alpha.definition import get_alpha
    from quantlab.alpha.ensemble import apply_panel_sign

    alpha = get_alpha(spec)
    for fid in alpha.input_features:
        _ensure_feature(frame, fid)
    panels = [
        compute_panel(get_feature(fid), frame.bars, list(frame.dates))
        for fid in alpha.input_features
    ]
    panel = apply_panel_sign(combine_panels(panels, alpha.transformation), alpha.expected_direction)
    cancelled()
    report, series, warnings = _feature_diagnostics(frame, panel, p.horizon)
    report.update(
        definition=alpha.model_dump(mode="json"), score_kind="rank_score_not_expected_return"
    )
    return report, _panel_series(panel, alpha.name, "rank score", frame.dates) + series, warnings


def _regime(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.regimes.definition import DetectorKind, RegimeModel
    from quantlab.regimes.engine import classify, detect_changes
    from quantlab.regimes.registry import get_regime_model
    from quantlab.research.exploratory_states import exploratory_state_panel

    model = RegimeModel.model_validate(
        {**get_regime_model(spec).model_dump(), "lookback": p.lookback}
    )
    snapshots = exploratory_state_panel(frame, lookback=p.lookback, cancelled=cancelled)
    cancelled()
    series = [
        ResearchSeries(
            name="Realized volatility (per interval)",
            unit="fraction per interval",
            timestamps=frame.dates,
            values=tuple(s.realized_vol_20 for s in snapshots),
        )
    ]
    warnings = [
        "Universe observables are not NIFTY or a sourced benchmark. "
        "No fundamental, index or ADV proxy is invented."
    ]
    if model.detector == DetectorKind.CHANGE_POINT:
        changes = detect_changes(snapshots)
        report = _report(
            {"snapshots": len(snapshots)},
            {"snapshots": "bars"},
            definition=model.model_dump(mode="json"),
            changes=changes.model_dump(mode="json"),
        )
    else:
        retrospective = model.detector in {
            DetectorKind.HMM_SMOOTH,
            DetectorKind.CLUSTER_FULL_SAMPLE,
        }
        observations = classify(model, snapshots, predictive=not retrospective)
        if not any(o.hard_label is not None for o in observations):
            raise DataIntegrityError(
                "REGIME_OBSERVABLES_UNAVAILABLE: selected method has no classifiable "
                "state after warmup; choose a supported volatility/trend detector "
                "or provide a compatible multi-instrument history."
            )
        if retrospective:
            warnings.append(
                "Retrospective smoothing/full-sample detector: "
                "not a predictive signal and cannot enter a causal model."
            )
        labels = sorted({o.hard_label for o in observations if o.hard_label is not None})
        code = {label: float(i) for i, label in enumerate(labels)}
        series.append(
            ResearchSeries(
                name="Regime code (see label table)",
                unit="category code",
                timestamps=frame.dates,
                values=tuple(
                    None if o.hard_label is None else code[o.hard_label] for o in observations
                ),
            )
        )
        report = _report(
            {
                "snapshots": len(snapshots),
                "labelled_bars": sum(o.hard_label is not None for o in observations),
                "regimes": len(labels),
            },
            {"snapshots": "bars", "labelled_bars": "bars", "regimes": "categories"},
            definition=model.model_dump(mode="json"),
            observations=[o.model_dump(mode="json") for o in observations],
            retrospective=retrospective,
        )
        report["tables"] = [
            _table("Regime labels", ["Code", "Label"], [[code[label], label] for label in labels])
        ]
    report["snapshots"] = [s.model_dump(mode="json") for s in snapshots]
    return report, series, warnings


def _prediction_report(
    result: Any, frame: ExploratoryFrame, name: str
) -> tuple[dict[str, Any], list[ResearchSeries]]:
    metrics = {
        "prediction_dates": result.n_predictions,
        "scored_ic_dates": result.n_scored,
        "rank_ic": result.mean_ic,
        "coverage": result.coverage,
    }
    report = _report(
        metrics,
        {
            "prediction_dates": "bars",
            "scored_ic_dates": "bars",
            "rank_ic": "rank correlation",
            "coverage": "fraction",
        },
        diagnostics=result.model_dump(mode="json"),
    )
    points = {p.as_of: p for p in result.points}
    series = [
        ResearchSeries(
            name=name + " rank IC",
            unit="rank correlation",
            timestamps=frame.dates,
            values=tuple(points[t].ic if t in points else None for t in frame.dates),
        )
    ]
    return report, series


def _adaptive(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.adaptive.definition import AdaptiveModelDefinition
    from quantlab.adaptive.engine import run_adaptive
    from quantlab.adaptive.registry import get_adaptive_model
    from quantlab.alpha.definition import get_alpha

    model = AdaptiveModelDefinition.model_validate(
        {**get_adaptive_model(spec).model_dump(), "window": p.training_window}
    )
    for alpha in model.alpha_ids:
        for fid in get_alpha(alpha).input_features:
            _ensure_feature(frame, fid)
    _, _, result = run_adaptive(model, frame.bars)
    cancelled()
    report, series = _prediction_report(result, frame, "Prequential")
    report.update(
        definition=model.model_dump(mode="json"),
        predictions={d.isoformat(): row for d, row in result.predictions.items()},
        scores=result.predictions.get(frame.dates[-1], {}),
        score_kind="adaptive_rank_score_not_expected_return",
    )
    report["metrics"].update(updates=len(result.updates), resets=len(result.resets))
    report["metric_units"].update(updates="events", resets="events")
    return (
        report,
        _panel_series(result.predictions, "Adaptive score", "rank score", frame.dates) + series,
        [],
    )


def _model(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.learning.definition import ModelDefinition
    from quantlab.learning.engine import run_learning
    from quantlab.learning.registry import get_model

    definition = ModelDefinition.model_validate(
        {**get_model(spec).model_dump(), "training_window": p.training_window}
    )
    for fid in definition.features:
        _ensure_feature(frame, fid)
    dataset, predictions, result, _ = run_learning(
        definition, frame.bars, snapshot_id=frame.input_hash
    )
    cancelled()
    if result.n_predictions == 0:
        raise DataIntegrityError(
            "MODEL_INSUFFICIENT_TRAINING_DATA: no out-of-sample prediction; "
            "capture a longer aligned history"
        )
    report, series = _prediction_report(result, frame, "Walk-forward")
    report["metrics"]["oos_rmse"] = result.oos_rmse
    report["metric_units"]["oos_rmse"] = "return fraction"
    report.update(
        definition=definition.model_dump(mode="json"),
        predictions={d.isoformat(): row for d, row in predictions.items()},
        labels={d.isoformat(): row for d, row in dataset.labels.items()},
        scores=predictions.get(frame.dates[-1], {}),
        score_kind="model_prediction_not_calibrated_expected_return",
    )
    warnings = (
        []
        if len(frame.bars) >= 3
        else [
            "Single-stock model: cross-sectional rank IC is unavailable; "
            "inspect chronological prediction errors instead."
        ]
    )
    return (
        report,
        _panel_series(predictions, "Walk-forward prediction", "return fraction", frame.dates)
        + series,
        warnings,
    )


def _ensemble(
    frame: ExploratoryFrame,
    p: ResearchRunParameters,
    spec: str,
    cancelled: Callable[[], None],
    parents: tuple[FrozenResearchResult, ...] = (),
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.ensemble.definition import EnsembleDefinition
    from quantlab.ensemble.engine import run_ensemble
    from quantlab.ensemble.registry import get_ensemble

    definition = EnsembleDefinition.model_validate(
        {**get_ensemble(spec).model_dump(), "training_window": p.training_window}
    )
    _ensure_component_sources(frame, definition)
    overrides: dict[str, Panel] = {}
    sources = {
        component.component_id: "RECOMPUTED_VERSIONED_COMPONENT"
        for component in definition.components
    }
    for parent in parents:
        component = next(
            (c for c in definition.components if c.component_id == parent.specification), None
        )
        if component is None or parent.specification in overrides:
            raise DataIntegrityError("ENSEMBLE_PARENT_COMPONENT_MISMATCH_OR_DUPLICATE")
        allowed = {
            "alpha": {"alpha"},
            "model": {"model", "regime_conditioned_model"},
            "adaptive": {"adaptive_model"},
        }
        if component.component_type.value not in allowed.get(parent.engine, set()):
            raise DataIntegrityError("ENSEMBLE_PARENT_COMPONENT_KIND_MISMATCH")
        overrides[parent.specification] = _parent_score_panel(parent)
        sources[parent.specification] = parent.content_hash
    panels, _, result = run_ensemble(
        definition, frame.bars, snapshot_id=frame.input_hash, overrides=overrides or None
    )
    if result.n_predictions == 0:
        raise DataIntegrityError("ENSEMBLE_NO_PREDICTIONS: component source or warmup unavailable")
    cancelled()
    report, series = _prediction_report(result, frame, "Ensemble")
    report.update(
        definition=definition.model_dump(mode="json"),
        predictions={d.isoformat(): row for d, row in result.predictions.items()},
        scores=result.predictions.get(frame.dates[-1], {}),
        score_kind="ensemble_rank_score_not_expected_return",
        component_sources=sources,
    )
    report["tables"] = [
        _table(
            "Component diagnostics",
            ["Component", "Rank IC", "Final weight"],
            [
                [
                    name,
                    result.component_ics.get(name),
                    result.weights_path[-1].get(name) if result.weights_path else None,
                ]
                for name in panels
            ],
        )
    ]
    return (
        report,
        _panel_series(result.predictions, "Ensemble score", "rank score", frame.dates) + series,
        [],
    )


def _portfolio(
    frame: ExploratoryFrame,
    p: ResearchRunParameters,
    spec: str,
    cancelled: Callable[[], None],
    parents: tuple[FrozenResearchResult, ...] = (),
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.alpha.ensemble import get_ensemble
    from quantlab.portfolio.experiment import build_weight_map, ensemble_score_panel
    from quantlab.portfolio.spec import PortfolioModel, get_portfolio_model

    definition = PortfolioModel.model_validate(
        {
            **get_portfolio_model(spec).model_dump(),
            "top_n": p.top_n,
            "cost_bps": p.cost_bps,
            "covariance_lookback": p.lookback,
        }
    )
    names = [str(i.id) for i in frame.instruments]
    if p.top_n > len(names):
        raise DataIntegrityError("TOP_N_EXCEEDS_SELECTED_UNIVERSE")
    if parents:
        if len(parents) != 1 or parents[0].engine not in {"alpha", "adaptive", "model", "ensemble"}:
            raise DataIntegrityError("PORTFOLIO_PARENT_REQUIRED: choose exactly one score artifact")
        scores = _parent_score_panel(parents[0])
        score_source = parents[0].content_hash
    else:
        for alpha_id in get_ensemble(definition.ensemble_id).alpha_ids():
            _ensure_alpha_sources(frame, alpha_id)
        scores, _ = ensemble_score_panel(
            get_ensemble(definition.ensemble_id), frame.bars, list(frame.dates)
        )
        score_source = "RECOMPUTED_VERSIONED_ENSEMBLE:" + definition.ensemble_id
    weights, diag, infeasible, rebalances = build_weight_map(definition, scores, frame.bars, names)
    cancelled()
    if infeasible:
        return (
            _report(
                {"target_names": 0, "rebalances": rebalances},
                {"target_names": "instruments", "rebalances": "events"},
                construction_state="INFEASIBLE",
                blocking_reasons=[
                    "Versioned portfolio constraints rejected a target; "
                    "no constraint was relaxed and no allocation is available."
                ],
                targets={},
                target_weights={},
                last_weights={},
                scores=scores.get(frame.dates[-1], {}),
                score_kind="rank_score_not_expected_return",
                definition=definition.model_dump(mode="json"),
                score_source=score_source,
            ),
            [],
            [
                "Portfolio rejected by hard constraints. This negative research result "
                "does not provide a capital or paper target."
            ],
        )
    weight_panel = {
        date: {str(t.instrument): t.weight for t in targets} for date, targets in weights.items()
    }
    targets = weight_panel.get(frame.dates[-1], {})
    if not targets:
        raise DataIntegrityError(
            "PORTFOLIO_NO_TARGET: signal/history or constraints leave no investable target"
        )
    covariance = _covariance(frame, p, "sample_cs")
    report = _report(
        {
            "target_names": len(targets),
            "gross_weight": sum(abs(v) for v in targets.values()),
            "net_weight": sum(targets.values()),
            "rebalances": rebalances,
        },
        {
            "target_names": "instruments",
            "gross_weight": "weight",
            "net_weight": "weight",
            "rebalances": "events",
        },
        targets=targets,
        target_weights=targets,
        last_weights=targets,
        scores=scores.get(frame.dates[-1], {}),
        score_kind="rank_score_not_expected_return",
        weights_path={d.isoformat(): row for d, row in weight_panel.items()},
        covariance=covariance,
        definition=definition.model_dump(mode="json"),
        diagnostics=None if diag is None else diag.model_dump(mode="json"),
        valuation_time=frame.dates[-1].isoformat(),
        current_prices={str(k): bars[-1].close for k, bars in frame.bars.items()},
        construction_state="CONSTRUCTED_RESEARCH_TARGET",
        score_source=score_source,
    )
    report["tables"] = [
        _table(
            "Research target weights (not orders)",
            ["Instrument", "Weight", "Score (not expected return)"],
            [
                [name, targets.get(name, 0.0), scores.get(frame.dates[-1], {}).get(name)]
                for name in names
            ],
        )
    ]
    return (
        report,
        _panel_series(weight_panel, "Research target weight", "weight", frame.dates),
        [
            "Constructor output only; no invented portfolio PnL or executable quantity. "
            "Research weights are not expected returns or broker holdings."
        ],
    )


def _covariance(frame: ExploratoryFrame, p: ResearchRunParameters, spec: str) -> dict[str, Any]:
    from quantlab.portfolio.covariance import estimate_covariance
    from quantlab.risk.model import get_risk_model

    definition = get_risk_model(spec)
    covariance = estimate_covariance(
        frame.bars,
        frame.dates[-1],
        [str(k) for k in frame.bars],
        p.lookback,
        estimator=definition.covariance_estimator,
        repair=definition.covariance_repair,
        ewma_lambda=definition.ewma_lambda,
        shrinkage=definition.shrinkage,
    ).model_dump(mode="json")
    covariance["note"] = (
        "Timestamp-aligned retrospective returns; per interval, not annualized; "
        "historical availability NOT_TESTED."
    )
    return covariance


def _risk(
    frame: ExploratoryFrame,
    p: ResearchRunParameters,
    spec: str,
    cancelled: Callable[[], None],
    parents: tuple[FrozenResearchResult, ...] = (),
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    covariance = _covariance(frame, p, spec)
    cancelled()
    matrix = np.asarray(covariance["matrix"], dtype=float)
    sigma = np.sqrt(np.maximum(np.diag(matrix), 0))
    denom = np.outer(sigma, sigma)
    correlation = np.divide(matrix, denom, out=np.full_like(matrix, np.nan), where=denom > 0)
    names = covariance["names"]
    report = _report(
        {
            "instruments": len(names),
            "return_observations": covariance["n_obs"],
            "condition_number": covariance["condition_number"],
            "minimum_eigenvalue": covariance["min_eigenvalue"],
        },
        {
            "instruments": "instruments",
            "return_observations": "bars",
            "condition_number": "ratio",
            "minimum_eigenvalue": "return variance",
        },
        covariance=covariance,
        correlation=correlation.tolist(),
        names=names,
        unsupported_capabilities=[
            "fundamentals",
            "sector membership",
            "sourced market-index beta",
            "observed ADV",
        ],
    )
    report["tables"] = [
        _table(
            "Covariance (per interval)",
            ["Instrument", *names],
            [[name, *row] for name, row in zip(names, matrix.tolist(), strict=True)],
        ),
        _table(
            "Return correlation",
            ["Instrument", *names],
            [[name, *row] for name, row in zip(names, correlation.tolist(), strict=True)],
        ),
    ]
    if parents:
        import json

        from quantlab.portfolio.covariance import CovarianceReport
        from quantlab.portfolio.risk_model import risk_contributions

        if len(parents) != 1 or parents[0].engine != "portfolio":
            raise DataIntegrityError("RISK_PARENT_REQUIRED: choose exactly one portfolio artifact")
        payload = json.loads(parents[0].report_json)
        weights = payload.get("target_weights", {})
        if not weights or any(name not in names for name in weights):
            raise DataIntegrityError("RISK_PARENT_HAS_NO_COMPATIBLE_TARGET")
        diagnostics = risk_contributions(weights, CovarianceReport.model_validate(covariance))
        diagnostics.note = "Selected research target and aligned retrospective covariance; "
        diagnostics.note += "per interval, historical availability NOT_TESTED."
        report.update(
            portfolio_source=parents[0].content_hash,
            target_weights=weights,
            portfolio_risk=diagnostics.model_dump(mode="json"),
        )
        report["metrics"]["portfolio_volatility"] = diagnostics.volatility
        report["metric_units"]["portfolio_volatility"] = "fraction per aligned return interval"
    else:
        report["portfolio_source"] = "NO_PORTFOLIO_SELECTED: asset covariance only"
    return (
        report,
        [],
        [
            "Covariance estimates the selected aligned asset returns, not an assumed portfolio. "
            "Fundamental/sector exposures require an independent source."
        ],
    )


def _parent_score_panel(parent: FrozenResearchResult) -> Panel:
    import json

    payload = json.loads(parent.report_json)
    raw = payload.get("score_panel", payload.get("predictions", {}))
    if not raw:
        raise DataIntegrityError("PARENT_PREDICTIONS_UNAVAILABLE")
    return {
        datetime.fromisoformat(date): {name: float(value) for name, value in row.items()}
        for date, row in raw.items()
    }


def _econometrics(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from scipy import stats  # type: ignore[import-untyped]

    from quantlab.econometrics.dependence import dependence_report
    from quantlab.econometrics.stationarity import adf_test, kpss_test

    diagnostics: dict[str, Any] = {}
    rows: list[list[Any]] = []
    series: list[ResearchSeries] = []
    qq_rows: list[list[Any]] = []
    for name, bars in frame.bars.items():
        cancelled()
        log_prices = np.log(np.asarray([b.close for b in bars], dtype=float))
        values = np.diff(log_prices) if spec == "stationarity_returns" else log_prices
        dates = frame.dates[1:] if spec == "stationarity_returns" else frame.dates
        if len(values) < 25 or float(np.std(values)) <= 1e-15:
            raise DataIntegrityError(
                "ECONOMETRICS_SAMPLE_INVALID: require at least 25 non-constant real observations"
            )
        adf = adf_test(values.tolist(), lags=min(p.lookback, 8))
        kpss = kpss_test(values.tolist())
        dependence = dependence_report(values.tolist(), nlags=min(p.lookback, 24))
        qq, fit = stats.probplot(values, dist="norm", fit=True)
        # Jarque–Bera's asymptotic p-value is not valid for a tiny or dependent
        # return sample; expose its statistic only, never an IID confidence claim.
        jb = float(stats.jarque_bera(values).statistic)
        diagnostics[str(name)] = {
            "adf": adf.model_dump(mode="json"),
            "kpss": kpss.model_dump(mode="json"),
            "dependence": dependence.model_dump(mode="json"),
            "jarque_bera_statistic": jb,
            "qq_normal_slope": float(fit[0]),
            "qq_normal_intercept": float(fit[1]),
        }
        rows.append(
            [
                str(name),
                len(values),
                adf.statistic,
                adf.rejects_unit_root,
                kpss.statistic,
                kpss.rejects_unit_root,
                jb,
            ]
        )
        qq_rows.extend([[str(name), float(x), float(y)] for x, y in zip(qq[0], qq[1], strict=True)])
        series.append(
            ResearchSeries(
                name="Log return" if spec == "stationarity_returns" else "Log price",
                unit="log fraction" if spec == "stationarity_returns" else "log price",
                instrument=str(name),
                timestamps=dates,
                values=tuple(float(v) for v in values),
            )
        )
    report = _report(
        {"tested_series": len(rows), "minimum_observations": min(row[1] for row in rows)},
        {"tested_series": "instruments", "minimum_observations": "bars"},
        diagnostics=diagnostics,
        method="ADF/KPSS descriptive stationarity; ACF/PACF dependence; "
        "scipy.stats normal Q-Q and Jarque-Bera statistic",
    )
    report["tables"] = [
        _table(
            "Exploratory stationarity diagnostics",
            [
                "Instrument",
                "n",
                "ADF statistic",
                "Reject unit root at tabulated 5%",
                "KPSS statistic",
                "Reject stationarity at tabulated 5%",
                "JB statistic (no IID p-value)",
            ],
            rows,
        ),
        _table(
            "Normal Q–Q coordinates",
            ["Instrument", "Theoretical quantile", "Ordered observation"],
            qq_rows,
        ),
    ]
    return (
        report,
        series,
        [
            "No causal claim. ADF/KPSS use documented tabulated critical values; "
            "dependent observations are not treated as independent normal returns."
        ],
    )


def _discovery(
    frame: ExploratoryFrame, p: ResearchRunParameters, spec: str, cancelled: Callable[[], None]
) -> tuple[dict[str, Any], list[ResearchSeries], list[str]]:
    from quantlab.alpha.ic import information_coefficient
    from quantlab.discovery.complexity import complexity
    from quantlab.discovery.evaluator import evaluate_expression, slice_panel
    from quantlab.discovery.generator import seed_expressions
    from quantlab.discovery.registry import get_family
    from quantlab.discovery.validation import split_dates

    family = get_family(spec)
    # Bounded deterministic candidate-family screen, not a disguised unbounded
    # optimizer or GP run. Every attempted expression and negative result remains.
    definitions = [get_feature(fid) for fid in family.grammar.allowed_features]
    for definition in definitions:
        _ensure_feature(frame, definition.feature_id)
    panels = {d.feature_id: compute_panel(d, frame.bars, list(frame.dates)) for d in definitions}
    labels = compute_label_panel(forward_return(1), frame.bars, list(frame.dates))
    # Drop warm-up and the final unavailable label before freezing all splits.
    eligible = [
        t for t in frame.dates if t in labels and all(t in panel for panel in panels.values())
    ]
    if len(eligible) < 40:
        raise DataIntegrityError(
            "DISCOVERY_SPLITS_TOO_SHORT: need 40 fully aligned labelled feature bars after warmup"
        )
    splits = split_dates(eligible)
    rows: list[list[Any]] = []
    attempts: list[tuple[dict[str, Any], Panel, list[datetime]]] = []
    candidates = seed_expressions(family.grammar)[: p.max_candidates]
    for expr in candidates:
        cancelled()
        panel = evaluate_expression(expr, panels)
        # Horizon-one train endpoints immediately adjacent to the next split
        # would consume that split's first close. Purge boundary decisions.
        train_dates = splits.train[:-1]
        validation_dates = splits.validation[:-1]
        train = information_coefficient(
            slice_panel(panel, train_dates), slice_panel(labels, train_dates), min_sample=8
        )
        cx = complexity(expr).score
        fitness = None if train.spearman_mean is None else train.spearman_mean - 0.04 * cx
        attempt = {
            "expression": expr.canonical_text(),
            "expression_hash": expr.identity_hash(),
            "complexity": cx,
            "train_ic": train.spearman_mean,
            "train_ic_dates": train.n,
            "selection_fitness": fitness,
            "validation_ic": None,
            "holdout_ic": None,
        }
        attempts.append((attempt, panel, validation_dates))
    valid = [row for row, _, _ in attempts if row["selection_fitness"] is not None]
    if not valid:
        raise DataIntegrityError(
            "DISCOVERY_NO_SCORABLE_CANDIDATES: require variable cross-sectional scores and labels"
        )
    winner = max(valid, key=lambda r: float(r["selection_fitness"]))
    winner_panel: Panel = {}
    for attempt, panel, validation_dates in attempts:
        cancelled()
        # Only the frozen training-selected winner is evaluated on validation /
        # holdout. Other candidates have no holdout feedback for tuning.
        if attempt is winner:
            val = information_coefficient(
                slice_panel(panel, validation_dates),
                slice_panel(labels, validation_dates),
                min_sample=5,
            )
            hold = information_coefficient(
                slice_panel(panel, splits.holdout),
                slice_panel(labels, splits.holdout),
                min_sample=5,
            )
            attempt.update(validation_ic=val.spearman_mean, holdout_ic=hold.spearman_mean)
            winner_panel = panel
        rows.append(
            [
                attempt[k]
                for k in (
                    "expression",
                    "complexity",
                    "train_ic",
                    "train_ic_dates",
                    "selection_fitness",
                    "validation_ic",
                    "holdout_ic",
                )
            ]
        )
    report = _report(
        {
            "attempted_candidates": len(attempts),
            "winner_train_ic": winner["train_ic"],
            "winner_holdout_ic": winner["holdout_ic"],
        },
        {
            "attempted_candidates": "candidates",
            "winner_train_ic": "rank correlation",
            "winner_holdout_ic": "rank correlation",
        },
        protocol="Bounded versioned seed-expression screen, train-only IC-minus-complexity "
        "selection; purged split boundaries; no GP evolution or independent validation claim",
        attempts=[a for a, _, _ in attempts],
        winner=winner,
        splits={
            "train": [t.isoformat() for t in splits.train[:-1]],
            "validation": [t.isoformat() for t in splits.validation[:-1]],
            "holdout": [t.isoformat() for t in splits.holdout],
        },
        scores=winner_panel.get(frame.dates[-1], {}),
        score_kind="discovered_feature_not_expected_return",
    )
    report["tables"] = [
        _table(
            "All bounded candidate attempts",
            [
                "Expression",
                "Complexity",
                "Train IC",
                "Train n",
                "Frozen fitness",
                "Winner-only validation IC",
                "Winner-only holdout IC",
            ],
            rows,
        )
    ]
    return (
        report,
        _panel_series(
            winner_panel, "Frozen training-selected candidate", "feature score", frame.dates
        ),
        [
            "This bounded candidate-family screen does not run GP evolution "
            "and is not independent validation; further selection after viewing holdout "
            "contaminates that holdout."
        ],
    )
