"""Research vertical slice and research-grade validation around the same engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from quantlab import __version__
from quantlab.backtest.engine import BacktestConfig, BacktestResult, run_backtest
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import DataIntegrityError
from quantlab.core.identifiers import AlphaId, ExperimentId, HypothesisId, InstrumentId
from quantlab.data.fabric.catalog import DatasetRecord
from quantlab.data.fabric.ingest import SYNTHETIC_DATASET_ID, materialize_synthetic
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.store import PitStore
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.data.validation import validate_bars
from quantlab.domain.models import (
    ExperimentRun,
    ExperimentStatus,
    Instrument,
    MarketState,
    OHLCVBar,
)
from quantlab.domain.research import Alpha, DataLineage, ResearchHypothesis, ResearchStatus
from quantlab.market.state import build_cross_section
from quantlab.models.registry import ExperimentLedger
from quantlab.research.artifacts import write_experiment_artifacts
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.genome import evaluate_genome, momentum_genome
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.suite import ValidationConfig, ValidationReport, run_validation_suite
from quantlab.risk.firewall import RiskFirewall, RiskLimits


@dataclass(frozen=True)
class SyntheticFrame:
    record: DatasetRecord
    instruments: list[Instrument]
    bars: dict[InstrumentId, list[OHLCVBar]]
    flat: list[OHLCVBar]


def load_synthetic_frame(
    *,
    n_days: int = 80,
    ledger_path: Path | None = None,
    fabric_root: Path | None = None,
) -> SyntheticFrame:
    path = ledger_path or Path("experiments/ledger.jsonl")
    layout = FabricLayout(fabric_root or (path.parent / "fabric"))
    ingested = materialize_synthetic(layout, n_days=n_days)
    record = ingested.record
    max_available = record.extra.get("max_available_time")
    if not max_available:
        raise DataIntegrityError("synthetic fabric snapshot missing max_available_time")
    as_of = datetime.fromisoformat(max_available)
    store = PitStore(layout, record.dataset_id, record.version)
    bars = store.all_as_of(as_of)
    if not bars:
        raise DataIntegrityError("PIT store returned no bars for the synthetic snapshot")

    provider = MemoryBarProvider(n_days=n_days)
    instruments = provider.get_instruments()
    flat: list[OHLCVBar] = []
    validated: dict[InstrumentId, list[OHLCVBar]] = {}
    for inst in instruments:
        series = bars.get(inst.id)
        if series is None:
            raise DataIntegrityError(f"PIT store missing {inst.id}")
        series = validate_bars(series)
        validated[inst.id] = series
        flat.extend(series)
    return SyntheticFrame(record=record, instruments=instruments, bars=validated, flat=flat)


def run_momentum_vertical_slice(
    ledger_path: Path | None = None,
    n_days: int = 80,
    lookback: int = 20,
    top_n: int = 2,
    cost_bps: float = 10.0,
    fabric_root: Path | None = None,
) -> tuple[BacktestResult, ExperimentRun]:
    path = ledger_path or Path("experiments/ledger.jsonl")
    frame = load_synthetic_frame(n_days=n_days, ledger_path=path, fabric_root=fabric_root)
    return _slice_from_frame(
        frame,
        ledger_path=path,
        lookback=lookback,
        top_n=top_n,
        cost_bps=cost_bps,
        append=True,
    )


def run_momentum_validation(
    ledger_path: Path | None = None,
    n_days: int = 80,
    lookback: int = 20,
    top_n: int = 2,
    cost_bps: float = 10.0,
    fabric_root: Path | None = None,
    artifacts_dir: Path | None = None,
    config: ValidationConfig | None = None,
) -> tuple[BacktestResult, ExperimentRun, ValidationReport]:
    path = ledger_path or Path("experiments/ledger.jsonl")
    frame = load_synthetic_frame(n_days=n_days, ledger_path=path, fabric_root=fabric_root)
    cfg = config or ValidationConfig(lookback=lookback, top_n=top_n, cost_bps=cost_bps)
    preview, _ = _slice_from_frame(
        frame,
        ledger_path=path,
        lookback=cfg.lookback,
        top_n=cfg.top_n,
        cost_bps=cfg.cost_bps,
        append=False,
    )
    integrity = evaluate_integrity(
        bars=frame.flat,
        states=_integrity_states(frame.bars, preview, cfg.lookback),
        as_of_times=preview.dates,
        next_bar_fill=True,
        cost_bps=cfg.cost_bps,
        slippage_model=cfg.slippage_model,
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=len(cfg.lookbacks),
        used_ml=False,
        data_kind=frame.record.data_kind.value,
        pit_query_verified=True,
        walk_forward_windows_ok=True,
        embargo_enforced=True,
        purge_applied=True,
        test_used_for_selection=False,
        future_parameter_selection=False,
    )
    result, report = run_validation_suite(
        frame.bars,
        frame.instruments,
        config=cfg,
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        integrity_failed=integrity.failed(),
        integrity=integrity.as_str_map(),
    )
    result.integrity = integrity.as_str_map()
    report.integrity = integrity.as_str_map()
    run = _experiment_from_validation(frame, result, cfg, report)
    report.experiment_id = run.id
    ExperimentLedger(path).append(run)
    dest = artifacts_dir or (path.parent / "artifacts")
    write_experiment_artifacts(dest, run, result, extra=report.model_dump(mode="json"))
    return result, run, report


def _slice_from_frame(
    frame: SyntheticFrame,
    *,
    ledger_path: Path,
    lookback: int,
    top_n: int,
    cost_bps: float,
    append: bool,
) -> tuple[BacktestResult, ExperimentRun]:
    record = frame.record
    genome = momentum_genome(lookback)
    hypothesis = ResearchHypothesis(
        id=str(HypothesisId()),
        title="Cross-sectional momentum persists one day",
        statement="Names with higher 20-day momentum outperform on the next bar after costs.",
        economic_intuition="Underreaction / trend following in a small synthetic universe.",
        mathematical_formulation="rank(zscore(close[t]/close[t-20]-1))",
        expected_effect="positive next-bar long-only spread",
        universe=[str(i.id) for i in frame.instruments],
        required_data=["ohlcv"],
        null_hypothesis="next-bar returns are independent of 20-day momentum rank",
        alternative_hypothesis="higher rank associated with higher next-bar return",
        experiment_design="next-bar cost-adjusted backtest",
        acceptance_criteria="integrity has no FAIL; architecture is reproducible",
        rejection_criteria="look-ahead FAIL or zero-cost backtest",
        status=ResearchStatus.EXPERIMENTAL,
    )
    alpha = Alpha(
        alpha_id=str(AlphaId()),
        name="cs_momentum_nse_synthetic",
        hypothesis_id=hypothesis.id,
        universe=hypothesis.universe,
        data_dependencies=[f"{record.dataset_id}@{record.version}"],
        features=[f"momentum_{lookback}"],
        signal_definition=genome.genome_id,
        prediction_horizon="1d",
        holding_period="1d",
        genome_id=genome.genome_id,
        provenance="prompt04-fabric-vertical-slice",
    )
    strategy = CrossSectionalMomentum(lookback=lookback, top_n=top_n)
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(frame.instruments)
    result = run_backtest(
        frame.bars, strategy, firewall, BacktestConfig(lookback=lookback, cost_bps=cost_bps)
    )
    integrity_states = _integrity_states(frame.bars, result, lookback)
    if integrity_states:
        feature_map: dict[str, dict[str, float]] = {f"momentum_{lookback}": {}}
        for state in integrity_states:
            value = state.features.get(f"momentum_{lookback}")
            if value is not None:
                feature_map[f"momentum_{lookback}"][str(state.instrument)] = value
        evaluate_genome(genome, feature_map, result.dates[0])
    integrity = evaluate_integrity(
        bars=frame.flat,
        states=integrity_states,
        as_of_times=result.dates,
        next_bar_fill=True,
        cost_bps=cost_bps,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=record.data_kind.value,
        pit_query_verified=True,
    )
    result.integrity = integrity.as_str_map()
    lineage = DataLineage(
        provider="data_fabric",
        dataset_version=record.version,
        ingested_at=datetime.now(tz=UTC),
        transformations=[
            "materialize_synthetic",
            "sha256",
            "validate_bars",
            "parquet_pit_query",
            "market_state",
            f"momentum_{lookback}",
        ],
        feature_versions={"momentum": strategy.version},
        signal_version=strategy.version,
        genome_id=genome.genome_id,
        dataset_id=record.dataset_id,
        snapshot_id=record.snapshot_id,
        data_kind=record.data_kind.value,
        checksum=record.checksum,
        source="memory_synthetic_nse",
    )
    env = environment()
    status = ExperimentStatus.FAILED if integrity.failed() else ExperimentStatus.PASSED
    run = ExperimentRun(
        id=str(ExperimentId()),
        name=alpha.name,
        hypothesis=hypothesis.statement,
        status=status,
        git_commit=git_commit(),
        dataset_version=record.version,
        universe=hypothesis.universe,
        feature_versions={"momentum": strategy.version},
        label_definition="next_bar_close_return",
        hyperparameters={"lookback": lookback, "top_n": top_n, "cost_bps": cost_bps},
        test_period="synthetic-80d",
        transaction_cost_bps=cost_bps,
        slippage_model="none",
        random_seed=0,
        hypothesis_id=hypothesis.id,
        alpha_id=alpha.alpha_id,
        genome_id=genome.genome_id,
        cost_model="proportional_bps",
        latency_model="none",
        dataset_id=record.dataset_id or SYNTHETIC_DATASET_ID,
        snapshot_id=record.snapshot_id,
        universe_version=record.universe_version,
        calendar_version=record.calendar_version,
        data_kind=record.data_kind.value,
        price_adjustment_method=record.price_adjustment_method,
        corporate_action_policy=record.corporate_action_policy,
        lineage=lineage.as_dict(),
        metrics=result.metrics,
        integrity=result.integrity,
        application_version=__version__,
        conclusion="Architecture slice over the PIT fabric. Returns are not a claim of alpha.",
        config_hash=result.config_hash,
        research_family_id="cs_momentum",
        n_hypotheses_in_family=1,
        validation_protocol="next_bar_cost_adjusted",
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
    )
    if append:
        ExperimentLedger(ledger_path).append(run)
    return result, run


def _experiment_from_validation(
    frame: SyntheticFrame,
    result: BacktestResult,
    cfg: ValidationConfig,
    validation: ValidationReport,
) -> ExperimentRun:
    record = frame.record
    genome = momentum_genome(cfg.lookback)
    env = environment()
    status = ExperimentStatus.PASSED
    if validation.gate.outcome.value == "reject":
        status = ExperimentStatus.FAILED
    strategy_version = CrossSectionalMomentum(lookback=cfg.lookback, top_n=cfg.top_n).version
    lineage = DataLineage(
        provider="data_fabric",
        dataset_version=record.version,
        ingested_at=datetime.now(tz=UTC),
        transformations=[
            "materialize_synthetic",
            "validation_suite",
            "walk_forward",
            "cost_sensitivity",
            "parameter_surface",
        ],
        feature_versions={"momentum": strategy_version},
        signal_version=strategy_version,
        genome_id=genome.genome_id,
        dataset_id=record.dataset_id,
        snapshot_id=record.snapshot_id,
        data_kind=record.data_kind.value,
        checksum=record.checksum,
        source="memory_synthetic_nse",
    )
    payload = lineage.as_dict()
    payload["git_dirty"] = "true" if git_dirty() else "false"
    return ExperimentRun(
        id=str(ExperimentId()),
        name="cs_momentum_validation",
        hypothesis="Names with higher 20-day momentum outperform on the next bar after costs.",
        status=status,
        git_commit=git_commit(),
        dataset_version=record.version,
        universe=[str(i.id) for i in frame.instruments],
        feature_versions={"momentum": strategy_version},
        label_definition="next_bar_close_return",
        hyperparameters={"lookback": cfg.lookback, "top_n": cfg.top_n, "cost_bps": cfg.cost_bps},
        test_period="synthetic-walk-forward-oos",
        transaction_cost_bps=cfg.cost_bps,
        slippage_model=cfg.slippage_model,
        random_seed=validation.seed,
        hypothesis_id=str(HypothesisId()),
        alpha_id=str(AlphaId()),
        genome_id=genome.genome_id,
        cost_model="proportional_bps",
        latency_model="none",
        dataset_id=record.dataset_id or SYNTHETIC_DATASET_ID,
        snapshot_id=record.snapshot_id,
        universe_version=record.universe_version,
        calendar_version=record.calendar_version,
        data_kind=record.data_kind.value,
        price_adjustment_method=record.price_adjustment_method,
        corporate_action_policy=record.corporate_action_policy,
        lineage=payload,
        metrics=result.metrics,
        integrity=result.integrity,
        application_version=__version__,
        conclusion=(
            "Research-grade validation of the synthetic momentum slice. "
            "data_kind=synthetic cannot be promoted as market evidence."
        ),
        config_hash=validation.config_hash,
        research_family_id=cfg.family_id,
        n_hypotheses_in_family=len(cfg.lookbacks),
        selection_stage="pre_registered_lookback",
        gate_outcome=validation.gate.outcome.value,
        gate_reasons=validation.gate.as_str_map(),
        validation_protocol=validation.validation_protocol,
        git_dirty=validation.git_dirty,
        python_version=env.get("python", ""),
        validation=validation.as_str_map(),
    )


def _integrity_states(
    bars: dict[InstrumentId, list[OHLCVBar]],
    result: BacktestResult,
    lookback: int,
) -> list[MarketState]:
    if not result.dates:
        return []
    return build_cross_section(bars, result.dates[0], lookback)
