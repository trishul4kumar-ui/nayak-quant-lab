"""Risk research experiments on existing covariance + factor exposures."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import CheckResult, DataLineage
from quantlab.factors.engine import compute_factor_panel
from quantlab.factors.exposure import (
    ExposureMatrix,
    PortfolioFactorExposure,
    as_attribution,
    exposure_matrix,
    portfolio_exposures,
)
from quantlab.factors.market import rolling_betas
from quantlab.factors.registry import get_factor
from quantlab.features.engine import session_calendar
from quantlab.models.registry import ExperimentLedger
from quantlab.portfolio.baselines import equal_weight_names, targets_to_map
from quantlab.portfolio.covariance import CovarianceReport, estimate_covariance
from quantlab.portfolio.risk_model import RiskDiagnostics, risk_contributions
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity
from quantlab.risk.decomposition import FactorRiskReport, decompose_portfolio_variance
from quantlab.risk.model import RiskModelSpec, get_risk_model
from quantlab.risk.stress import StressResult, run_stress, seed_scenarios


class RiskExperimentReport(BaseModel):
    schema_version: str = "1"
    risk_model_id: str
    identity_hash: str
    n_names: int = 0
    estimated_volatility: float | None = None
    condition_number: float | None = None
    psd: bool = False
    exposures: dict[str, float] = Field(default_factory=dict)
    missing_exposures: list[str] = Field(default_factory=list)
    beta_mean: float | None = None
    stress: list[StressResult] = Field(default_factory=list)
    covariance: CovarianceReport | None = None
    diagnostics: RiskDiagnostics | None = None
    decomposition: FactorRiskReport | None = None
    exposure_matrix: ExposureMatrix | None = None
    portfolio_factor_exposure: PortfolioFactorExposure | None = None
    last_weights: dict[str, float] = Field(default_factory=dict)
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    note: str = (
        "A risk estimate is not a forecast and not alpha. Synthetic results cannot be promoted."
    )


def run_risk_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    spec: RiskModelSpec,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    weights: dict[str, float] | None = None,
    portfolio_id: str = "",
) -> tuple[RiskExperimentReport, ExperimentRun]:
    dates = session_calendar(bars)
    as_of = dates[-1]
    names = [str(i.id) for i in instruments]
    scores = {name: 1.0 for name in names}
    held = weights if weights is not None else targets_to_map(equal_weight_names(scores))
    cov = estimate_covariance(
        bars,
        as_of,
        names,
        spec.covariance_lookback,
        estimator=spec.covariance_estimator,
        repair=spec.covariance_repair,
        ewma_lambda=spec.ewma_lambda,
        shrinkage=spec.shrinkage,
    )
    risk = risk_contributions(held, cov)
    panels = {}
    versions: dict[str, str] = {}
    for fid in spec.factor_ids:
        definition = get_factor(fid)
        versions[fid] = definition.version
        panel, obs = compute_factor_panel(definition, bars, dates)
        if obs.status is not CheckResult.NOT_TESTED and panel:
            panels[fid] = panel
    matrix = exposure_matrix(panels, as_of) if panels else None
    exp = portfolio_exposures(held, matrix) if matrix is not None else None
    beta = rolling_betas(bars, as_of, lookback=spec.covariance_lookback)
    stress = [run_stress(held, cov, scenario) for scenario in seed_scenarios()]
    decomposition = decompose_portfolio_variance(held, cov)
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=False,
        data_kind=data_kind,
        pit_query_verified=True,
        future_covariance=False,
        future_factor=False,
        future_beta=False,
        feature_available_time_ok=True,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind=data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=CheckResult.NOT_TESTED,
        n_hypotheses=family_size,
        test_used_for_selection=False,
    )
    report = RiskExperimentReport(
        risk_model_id=spec.risk_model_id,
        identity_hash=spec.identity_hash(),
        n_names=len(cov.names),
        estimated_volatility=risk.volatility,
        condition_number=cov.condition_number,
        psd=cov.psd,
        exposures={} if exp is None else exp.exposures,
        missing_exposures=[] if exp is None else exp.missing,
        beta_mean=beta.mean,
        stress=stress,
        covariance=cov,
        diagnostics=risk,
        decomposition=decomposition,
        exposure_matrix=matrix,
        portfolio_factor_exposure=exp,
        last_weights=held,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
    )
    run = _ledger_row(
        spec,
        report,
        instruments,
        dataset_id,
        dataset_version,
        snapshot_id,
        checksum,
        versions,
        portfolio_id,
        family_size,
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, spec)
    return report, run


def run_named_risk_experiment(
    risk_model_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
    portfolio_id: str = "",
) -> tuple[RiskExperimentReport, ExperimentRun]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_risk_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        spec=get_risk_model(risk_model_id),
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
        portfolio_id=portfolio_id,
    )


def _ledger_row(
    spec: RiskModelSpec,
    report: RiskExperimentReport,
    instruments: list[Instrument],
    dataset_id: str,
    dataset_version: str,
    snapshot_id: str,
    checksum: str,
    factor_versions: dict[str, str],
    portfolio_id: str,
    family_size: int,
) -> ExperimentRun:
    env = environment()
    status = (
        ExperimentStatus.FAILED
        if report.gate.outcome is GateOutcome.REJECT
        else ExperimentStatus.PASSED
    )
    lineage = DataLineage(
        provider="risk_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["covariance", "factor_exposure", "stress"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt08",
    )
    metrics: dict[str, float] = {}
    if report.estimated_volatility is not None:
        metrics["estimated_volatility"] = report.estimated_volatility
    if report.condition_number is not None:
        metrics["condition_number"] = report.condition_number
    if report.beta_mean is not None:
        metrics["beta_mean"] = report.beta_mean
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"risk_{spec.risk_model_id}",
        hypothesis="risk model describes variance, not expected return",
        status=status,
        git_commit=git_commit(),
        dataset_version=dataset_version or "unspecified",
        universe=[str(i.id) for i in instruments],
        transaction_cost_bps=10.0,
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.integrity,
        application_version=__version__,
        conclusion=report.note,
        config_hash=config_hash({"risk": spec.identity_hash()}),
        research_family_id="risk_models",
        n_hypotheses_in_family=family_size,
        selection_stage="risk_model",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "risk", "prompt05_suite": "not_run"},
        risk_model_id=spec.risk_model_id,
        risk_model_version=spec.version,
        factor_set=",".join(spec.factor_ids),
        factor_versions=factor_versions,
        feature_identity_hash=spec.identity_hash(),
        portfolio_id=portfolio_id,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: RiskExperimentReport,
    spec: RiskModelSpec,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    attribution = (
        None
        if report.portfolio_factor_exposure is None
        else as_attribution(report.portfolio_factor_exposure).model_dump(mode="json")
    )
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "risk_model_id": spec.risk_model_id,
            "identity_hash": spec.identity_hash(),
            "data_kind": report.data_kind,
        },
        "covariance": None
        if report.covariance is None
        else report.covariance.model_dump(mode="json"),
        "risk": None if report.diagnostics is None else report.diagnostics.model_dump(mode="json"),
        "exposure": {
            "weights": report.last_weights,
            "exposures": report.exposures,
            "missing": report.missing_exposures,
        },
        "attribution": attribution,
        "stress": [item.model_dump(mode="json") for item in report.stress],
        "decomposition": None
        if report.decomposition is None
        else report.decomposition.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
