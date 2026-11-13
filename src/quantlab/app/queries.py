"""Read-only queries for the desktop shell. No broker calls."""

from __future__ import annotations

import json
import math
from typing import Any

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.data.fabric.catalog import DatasetCatalog, DatasetRecord
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.policy import fixtures_enabled
from quantlab.data.providers.research import ResearchBarProvider
from quantlab.domain.models import ExperimentRun
from quantlab.market.state import build_market_state


def market_rows() -> list[dict[str, Any]]:
    provider = ResearchBarProvider(n_days=80)
    rows: list[dict[str, Any]] = []
    for inst in provider.get_instruments():
        series = provider.all_bars()[inst.id]
        if not series:
            continue
        last = series[-1]
        state = build_market_state(series, last.pit.event_time, lookback=20)
        momentum = None if state is None else state.features.get("momentum_20")
        rows.append(
            {
                "instrument": str(inst.id),
                "name": inst.name,
                "close": last.close,
                "volume": last.volume,
                "as_of": last.pit.event_time.isoformat(),
                "momentum_20": momentum,
            }
        )
    return rows


def market_close_series(instrument_id: str, *, n_days: int = 40) -> list[float]:
    """Close prices for sparkline charts in Market Lab."""
    provider = ResearchBarProvider(n_days=n_days)
    series = next(
        (
            bars
            for instrument, bars in provider.all_bars().items()
            if str(instrument) == instrument_id
        ),
        None,
    )
    if not series:
        return []
    return [float(bar.close) for bar in series]


def experiment_rows(
    runtime: ApplicationRuntime, *, limit: int | None = 50, include_archived: bool = False
) -> list[dict[str, Any]]:
    runs = runtime.ledger.list_runs()
    if not include_archived and not fixtures_enabled():
        runs = [run for run in runs if run.data_kind.lower() == "real"]
    selected = runs if limit is None else runs[-limit:]
    rows: list[dict[str, Any]] = []
    for run in reversed(selected):
        rows.append(
            {
                "id": run.id,
                "name": run.name,
                "status": run.status.value,
                "sharpe": run.metrics.get("sharpe"),
                "total_return": run.metrics.get("total_return"),
                "max_drawdown": run.metrics.get("max_drawdown"),
                "look_ahead": run.integrity.get("look_ahead_bias", ""),
                "genome_id": run.genome_id,
                "version": run.application_version,
                "dataset_id": run.dataset_id,
                "data_kind": run.data_kind,
                "gate_outcome": run.gate_outcome,
                "dataset_version": run.dataset_version,
                "universe": tuple(run.universe),
                "strategy_id": run.strategy_id or run.name,
                "interval": str(run.hyperparameters.get("interval", "unspecified")),
                "cost_bps": run.transaction_cost_bps,
                "slippage_model": run.slippage_model,
                "test_period": run.test_period,
                "research_type": run.research_type,
                "validation_protocol": run.validation_protocol,
                "parent_experiment_id": run.parent_experiment_id,
            }
        )
    return rows


def _catalog_records(
    runtime: ApplicationRuntime, *, include_archived: bool = False
) -> list[DatasetRecord]:
    catalog = DatasetCatalog(FabricLayout(runtime.paths.fabric_dir))
    try:
        records = catalog.list_records()
    finally:
        catalog.close()
    if not include_archived and not fixtures_enabled():
        return [record for record in records if record.data_kind.value.lower() == "real"]
    return records


def fabric_catalog_rows(
    runtime: ApplicationRuntime, *, include_archived: bool = False
) -> list[dict[str, Any]]:
    records = _catalog_records(runtime, include_archived=include_archived)
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append(
            {
                "dataset_id": record.dataset_id,
                "version": record.version,
                "state": record.state.value,
                "data_kind": record.data_kind.value,
                "checksum": record.checksum,
                "source": record.source,
                "calendar": record.calendar_version,
                "ca_policy": record.corporate_action_policy,
            }
        )
    return rows


def fabric_health_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    layout = FabricLayout(runtime.paths.fabric_dir)
    layout.ensure()
    records = _catalog_records(runtime)
    all_records = _catalog_records(runtime, include_archived=True)
    quarantined = sum(1 for row in records if row.state.value == "quarantined")
    ready = sum(1 for row in records if row.state.value == "research_ready")
    return [
        {"name": "fabric_root", "value": str(layout.root)},
        {"name": "datasets", "value": str(len(records))},
        {
            "name": "archived_fixtures",
            "value": str(sum(row.data_kind.value.lower() != "real" for row in all_records)),
        },
        {"name": "research_ready", "value": str(ready)},
        {"name": "quarantined", "value": str(quarantined)},
        {"name": "raw_exists", "value": str(layout.raw.exists())},
        {"name": "pit_exists", "value": str(layout.pit.exists())},
    ]


def fabric_coverage_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    records = _catalog_records(runtime)

    def count(value: str) -> int | None:
        try:
            number = int(value)
        except ValueError:
            return None
        return number if number >= 0 else None

    return [
        {
            "dataset": f"{record.dataset_id}@{record.version}",
            "coverage": record.coverage,
            "kind": record.data_kind.value,
            "state": record.state.value,
            "closed_bar_count": count(record.extra.get("closed_bar_count", "")),
            "instrument_count": count(record.extra.get("instrument_count", "")),
            "exploratory_ready": record.extra.get("exploratory_ready", "false"),
            "historical_availability_verified": record.extra.get(
                "historical_availability_verified", "false"
            ),
            "first_bar": record.extra.get("first_bar", ""),
            "last_bar": record.extra.get("last_bar", ""),
        }
        for record in records
    ]


def fabric_pit_status(runtime: ApplicationRuntime) -> dict[str, Any]:
    records = _catalog_records(runtime)
    ready = [
        row
        for row in records
        if row.state.value == "research_ready"
        and (fixtures_enabled() or row.extra.get("historical_availability_verified") == "true")
    ]
    exploratory = [row for row in records if row.extra.get("exploratory_ready") == "true"]
    return {
        "datasets": len(records),
        "research_ready": len(ready),
        "pit_verified": len(ready),
        "exploratory_ready": len(exploratory),
        "note": (
            "Research-ready datasets may be queried with available_time <= as_of."
            if ready
            else "PIT queries filter available_time <= as_of. "
            "A file on disk is not research-ready until the gate passes."
        ),
    }


def fabric_quality_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in fabric_catalog_rows(runtime):
        rows.append(
            {
                "dataset": f"{record['dataset_id']}@{record['version']}",
                "kind": record["data_kind"],
                "state": record["state"],
                "checksum": record["checksum"],
                "completeness": "not_tested",
                "note": (
                    "Production quality is NOT_TESTED until a quality report is attached. "
                    "Raw records are never silently repaired."
                ),
            }
        )
    if not rows:
        rows.append(
            {
                "dataset": "(none)",
                "kind": "unspecified",
                "state": "not_tested",
                "checksum": "",
                "completeness": "not_tested",
                "note": "No catalogued dataset. Official NSE history is not fabricated.",
            }
        )
    return rows


def fabric_security_master_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    return [
        {
            "security_id": "(none loaded)",
            "symbol_at_T": "historical",
            "note": (
                "Tickers are labels, not identity. symbol_at(security_id, T) is the PIT contract. "
                "Current ticker maps must not rewrite history."
            ),
        }
    ]


def fabric_corporate_action_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    return [
        {
            "type": "(none loaded)",
            "announcement": "not_tested",
            "effective": "not_tested",
            "available": "not_tested",
            "note": (
                "Corporate actions are not invented. "
                "Missing announcement timestamps stay NOT_TESTED."
            ),
        }
    ]


def fabric_calendar_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in fabric_catalog_rows(runtime):
        rows.append(
            {
                "dataset": f"{record['dataset_id']}@{record['version']}",
                "calendar": record.get("calendar") or "unspecified",
                "source": record["source"],
                "note": (
                    "Official NSE holiday calendar is NOT_TESTED unless a sourced calendar "
                    "is loaded. WeekdayCalendar is a diagnostic, not an exchange calendar."
                ),
            }
        )
    if not rows:
        rows.append(
            {
                "dataset": "(none)",
                "calendar": "not_tested",
                "source": "unspecified",
                "note": "Official NSE holiday calendar is not fabricated.",
            }
        )
    return rows


def fabric_universe_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    return [
        {
            "universe_id": "(none loaded)",
            "as_of": "PointInTimeUniverse.as_of",
            "note": (
                "Universe membership is historical. Current constituents must not rewrite T. "
                "Official index membership is NOT_TESTED unless sourced."
            ),
        }
    ]


def fabric_lineage_rows(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in fabric_catalog_rows(runtime):
        rows.append(
            {
                "dataset": f"{record['dataset_id']}@{record['version']}",
                "source": record["source"],
                "checksum": record["checksum"],
                "ca_policy": record.get("ca_policy") or "unspecified",
                "note": "Lineage is catalog provenance. Changing bytes creates a new version.",
            }
        )
    if not rows:
        rows.append(
            {
                "dataset": "(none)",
                "source": "unspecified",
                "checksum": "",
                "ca_policy": "unspecified",
                "note": "No snapshot lineage until a dataset is catalogued.",
            }
        )
    return rows


def is_validation_run(run: ExperimentRun) -> bool:
    """A job completion or NOT_TESTED gate is not a validation artifact.

    Older validation runs predate research_type, but contain the actual protocol
    output (including OOS window count). Preserve these without selecting an
    arbitrary backtest whose gate happens to be non-empty.
    """
    return run.research_type.lower() == "validation" or (
        bool(run.validation) and "oos_windows" in run.validation
    )


def selected_research_summary(runtime: ApplicationRuntime) -> dict[str, Any]:
    """Project only explicitly selected, published artifacts from this exact input bundle.

    Archived fixtures, unrelated latest runs and results whose publication failed
    cannot create a Home milestone. Computation remains distinct from validation.
    """
    from quantlab.agents.repository import AgentRepository
    from quantlab.app.market_backtest import FrozenMarketHistory
    from quantlab.app.research_workbench import load_research_run

    prefs = runtime.ui_settings.current
    histories = tuple(prefs.research_history_hashes)
    engines: dict[str, dict[str, Any]] = {}
    unavailable: dict[str, str] = {}
    if histories:
        try:
            if len(set(histories)) != len(histories):
                unavailable["inputs"] = "Selected source history missing, corrupt or duplicated"
            else:
                repository = AgentRepository(runtime.artifact_repository_path)
                try:
                    for history_hash in histories:
                        source = repository.get(history_hash, FrozenMarketHistory).verified()
                        if source.content_hash != history_hash:
                            raise ValueError("Selected source history identity mismatch")
                finally:
                    repository.close()
        except Exception:
            unavailable["inputs"] = "Selected source history missing, corrupt or unavailable"
    for engine, result_hash in prefs.research_result_hashes.items():
        if not histories or not result_hash or "inputs" in unavailable:
            continue
        try:
            result = load_research_run(runtime.artifact_repository_path, result_hash)
            if result.engine != engine or set(result.context.history_hashes) != set(histories):
                unavailable[engine] = "Selected result does not match this input bundle"
                continue
        except Exception:
            unavailable[engine] = "Selected result missing, corrupt or unpublished"
            continue
        report = json.loads(result.report_json)
        engines[engine] = {
            "run_id": result.run_id,
            "result_hash": result.content_hash,
            "specification": result.specification,
            "data_kind": "REAL",
            "input_tier": "EXPLORATORY",
            "validation_state": "NOT_TESTED",
            "gate_outcome": "NOT_TESTED",
            "metrics": report.get("metrics", {}),
            "metric_units": report.get("metric_units", {}),
            "context": result.context.model_dump(mode="json"),
        }
    return {
        "history_hashes": histories,
        "engines": engines,
        "unavailable": unavailable,
        "selected_run_ids": tuple(row["run_id"] for row in engines.values()),
        "status": "EXPLORATORY_COMPUTED" if engines else "NOT_COMPUTED",
        "validation_state": "NOT_TESTED",
        "execution_authority": False,
    }


def last_validation_row(
    runtime: ApplicationRuntime,
    *,
    parent_run_id: str | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any] | None:
    runs = runtime.ledger.list_runs()
    gated = [run for run in runs if is_validation_run(run)]
    if not fixtures_enabled():
        gated = [run for run in gated if run.data_kind.lower() == "real"]
    if parent_run_id is not None:
        gated = [run for run in gated if run.parent_experiment_id == parent_run_id]
    if candidate_id is not None:
        gated = [run for run in gated if candidate_id in {run.genome_id, run.hypothesis_id}]
    run = gated[-1] if gated else None
    if run is None:
        return None
    try:
        oos_sharpe = float(run.validation.get("oos_sharpe", ""))
    except (TypeError, ValueError):
        oos_sharpe = None
    if oos_sharpe is not None and not math.isfinite(oos_sharpe):
        oos_sharpe = None
    return {
        "id": run.id,
        "name": run.name,
        "status": run.status.value,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "config_hash": run.config_hash,
        "validation": run.validation,
        "gate_reasons": run.gate_reasons,
        "sharpe": oos_sharpe,
        "full_sample_sharpe": run.metrics.get("sharpe"),
        "oos_windows": run.validation.get("oos_windows", ""),
        "parent_experiment_id": run.parent_experiment_id,
        "validation_protocol": run.validation_protocol,
    }


def feature_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.features.registry import list_features

    rows: list[dict[str, Any]] = []
    for item in list_features():
        rows.append(
            {
                "feature_id": item.feature_id,
                "version": item.version,
                "family": item.family.value,
                "lookback": str(item.lookback),
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
                "definition": item.mathematical_definition,
            }
        )
    return rows


def alpha_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.alpha.definition import list_alphas

    rows: list[dict[str, Any]] = []
    for item in list_alphas():
        rows.append(
            {
                "alpha_id": item.alpha_id,
                "version": item.version,
                "inputs": ",".join(item.input_features),
                "transformation": item.transformation,
                "horizon": str(item.horizon),
                "lifecycle": item.lifecycle.value,
                "definition": item.mathematical_definition,
            }
        )
    return rows


def last_portfolio_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.portfolio_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "portfolio_version": run.portfolio_version,
        "ensemble_id": run.ensemble_id,
        "optimizer": run.optimizer,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "sharpe": run.metrics.get("sharpe"),
        "gross": run.metrics.get("gross"),
        "net": run.metrics.get("net"),
        "turnover": run.metrics.get("turnover"),
        "spearman_ic": run.metrics.get("spearman_ic"),
    }


def portfolio_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.portfolio.spec import list_portfolio_models

    rows: list[dict[str, Any]] = []
    for item in list_portfolio_models():
        rows.append(
            {
                "portfolio_id": item.portfolio_id,
                "version": item.version,
                "ensemble_id": item.ensemble_id,
                "constructor": item.constructor.value,
                "rebalance": item.rebalance.value,
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_feature_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.feature_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "feature_id": run.feature_id,
        "feature_version": run.feature_version,
        "identity": run.feature_identity_hash,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "spearman_ic": run.metrics.get("spearman_ic"),
        "ic_n": run.metrics.get("ic_n"),
        "label": run.label_definition,
    }


def factor_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.factors.registry import list_factors

    rows: list[dict[str, Any]] = []
    for item in list_factors():
        rows.append(
            {
                "factor_id": item.factor_id,
                "version": item.version,
                "category": item.category.value,
                "source": item.source.value,
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
                "definition": item.mathematical_definition,
            }
        )
    return rows


def risk_model_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.risk.model import list_risk_models

    rows: list[dict[str, Any]] = []
    for item in list_risk_models():
        rows.append(
            {
                "risk_model_id": item.risk_model_id,
                "version": item.version,
                "estimator": item.covariance_estimator,
                "lookback": str(item.covariance_lookback),
                "factors": ",".join(item.factor_ids),
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_factor_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.factor_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "factor_id": run.factor_id,
        "factor_set": run.factor_set,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "spearman_ic": run.metrics.get("spearman_ic"),
        "identity": run.feature_identity_hash,
    }


def last_risk_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.risk_model_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "risk_model_id": run.risk_model_id,
        "risk_model_version": run.risk_model_version,
        "factor_set": run.factor_set,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "estimated_volatility": run.metrics.get("estimated_volatility"),
        "condition_number": run.metrics.get("condition_number"),
        "beta_mean": run.metrics.get("beta_mean"),
        "identity": run.feature_identity_hash,
    }


def regime_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.regimes.registry import list_regime_models

    rows: list[dict[str, Any]] = []
    for item in list_regime_models():
        rows.append(
            {
                "regime_model_id": item.regime_model_id,
                "version": item.version,
                "detector": item.detector.value,
                "n_regimes": str(item.n_regimes),
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_cross_section_state_row() -> dict[str, Any] | None:
    from quantlab.features.engine import session_calendar
    from quantlab.regimes.snapshot import compute_snapshot

    bars = ResearchBarProvider(n_days=80).all_bars()
    dates = session_calendar(bars)
    if not dates:
        return None
    last = compute_snapshot(bars, dates[-1])
    return {
        "as_of": last.as_of.isoformat(),
        "n_names": str(last.n_names),
        "ew_return": last.market_ew_return,
        "realized_vol_20": last.realized_vol_20,
        "dispersion_cs": last.dispersion_cs,
        "breadth_sign": last.breadth_sign,
        "avg_pairwise_corr": last.avg_pairwise_corr,
        "ew_drawdown": last.ew_drawdown,
        "missing": ",".join(last.missing),
        "note": last.note,
    }


def last_regime_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.regime_model_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "regime_model_id": run.regime_model_id,
        "regime_model_version": run.regime_model_version,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "n_labelled": run.metrics.get("n_labelled"),
        "identity": run.feature_identity_hash,
    }


def adaptive_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.adaptive.registry import list_adaptive_models

    rows: list[dict[str, Any]] = []
    for item in list_adaptive_models():
        rows.append(
            {
                "adaptive_model_id": item.adaptive_model_id,
                "version": item.version,
                "policy": item.policy.value,
                "learner": item.learner.value,
                "alphas": ",".join(item.alpha_ids),
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_adaptive_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.adaptive_model_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "adaptive_model_id": run.adaptive_model_id,
        "policy": run.adaptation_policy,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "prequential_ic": run.metrics.get("prequential_ic"),
        "identity": run.feature_identity_hash,
    }


def learning_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.learning.registry import list_models

    rows: list[dict[str, Any]] = []
    for item in list_models():
        rows.append(
            {
                "model_id": item.model_id,
                "version": item.version,
                "algorithm": item.algorithm.value,
                "features": ",".join(item.features),
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_learning_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.statistical_model_id]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "model_id": run.statistical_model_id,
        "algorithm": run.algorithm,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "oos_ic": run.metrics.get("oos_ic"),
        "identity": run.feature_identity_hash,
    }


def ensemble_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.ensemble.registry import list_ensembles

    rows: list[dict[str, Any]] = []
    for item in list_ensembles():
        rows.append(
            {
                "ensemble_id": item.ensemble_id,
                "version": item.version,
                "weighting_policy": item.weighting_policy.value,
                "combination_method": item.combination_method.value,
                "components": ",".join(item.component_ids()),
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def last_ensemble_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [
        run
        for run in runtime.ledger.list_runs()
        if run.selection_stage == "meta_ensemble" or run.weighting_policy
    ]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "ensemble_id": run.ensemble_id,
        "weighting_policy": run.weighting_policy,
        "combination_method": run.combination_method,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "oos_ic": run.metrics.get("oos_ic"),
        "identity": run.feature_identity_hash,
    }


def execution_catalog_rows() -> list[dict[str, Any]]:
    from quantlab.app.execution import list_execution_model_rows

    return list_execution_model_rows()


def last_execution_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = [
        run for run in runtime.ledger.list_runs() if run.selection_stage == "execution_research"
    ]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "execution_model_id": run.execution_model_id,
        "scenario_id": run.scenario_id,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "net_return": run.metrics.get("net_return"),
        "identity": run.feature_identity_hash,
    }


def last_orchestration_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    from quantlab.app.orchestration import last_orchestration_experiment_row as _last

    return _last(runtime)


def last_discovery_experiment_row(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    from quantlab.app.discovery import last_discovery_experiment_row as _last

    return _last(runtime)
