"""Typed, locally persisted real-capture research jobs for the desktop workbench.

No provider calls, implicit dataset selection, fixture paths, validation claims or
execution authority. This is retrospective exploratory research, not a PIT import.
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Literal
from urllib.parse import quote

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from quantlab import __version__
from quantlab.agents.hashing import Artifact, digest
from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job
from quantlab.core.errors import DataIntegrityError
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.realtime_data.service import _assert_safety
from quantlab.research.exploratory import ExploratoryFrame, load_exploratory_frame

ResearchEngine = Literal[
    "features",
    "alpha",
    "regime",
    "adaptive",
    "model",
    "ensemble",
    "portfolio",
    "risk",
    "econometrics",
    "discovery",
]

DEFAULT_SPECIFICATIONS: dict[str, str] = {
    "features": "momentum_20",
    "alpha": "rank_momentum_20",
    "regime": "vol_tercile",
    "adaptive": "expanding_ic_mom20",
    "model": "ridge_mom",
    "ensemble": "ew_mom_5_20",
    "portfolio": "mom_5_20_ew",
    "risk": "sample_cs",
    "econometrics": "stationarity_returns",
    "discovery": "GP-MOM-VOL-001",
}


class ResearchRunParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    engine: ResearchEngine
    history_hashes: tuple[str, ...] = Field(min_length=1, max_length=64)
    specification: str = Field(default="", max_length=100, pattern=r"^[A-Za-z0-9_.-]*$")
    lookback: int = Field(default=20, ge=2, le=252, strict=True)
    horizon: int = Field(default=1, ge=1, le=20, strict=True)
    training_window: int = Field(default=24, ge=12, le=252, strict=True)
    top_n: int = Field(default=2, ge=1, le=64, strict=True)
    cost_bps: float = Field(default=10.0, ge=0, le=100, strict=True)
    max_candidates: int = Field(default=12, ge=1, le=24, strict=True)
    parent_hashes: tuple[str, ...] = Field(default=(), max_length=16)
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None
    data_kind: Literal["REAL"] = "REAL"
    input_tier: Literal["EXPLORATORY"] = "EXPLORATORY"

    @model_validator(mode="after")
    def identities(self) -> ResearchRunParameters:
        for value in (*self.history_hashes, *self.parent_hashes):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("INVALID_RESEARCH_ARTIFACT_HASH")
        if len(set(self.history_hashes)) != len(self.history_hashes):
            raise ValueError("DUPLICATE_HISTORY_SELECTION")
        if self.start and self.end and self.start >= self.end:
            raise ValueError("INVALID_RESEARCH_RANGE")
        return self


class ResearchInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    history_hash: str
    dataset_id: str
    version: str
    instrument: str
    interval: str
    bars: int
    first_bar: AwareDatetime
    last_bar: AwareDatetime
    captured_at: AwareDatetime
    source: str
    missing_volume: int
    input_tier: Literal["EXPLORATORY"] = "EXPLORATORY"
    historical_availability_verified: Literal[False] = False


class ResearchRunContext(Artifact):
    run_id: str
    correlation_id: str
    parameters: ResearchRunParameters
    input_hash: str
    history_hashes: tuple[str, ...]
    universe: tuple[str, ...]
    interval: str
    aligned_bars: int
    analytical_start: AwareDatetime
    analytical_end: AwareDatetime
    captured_at: tuple[AwareDatetime, ...]
    dropped_bars: tuple[int, ...]
    data_kind: Literal["REAL"] = "REAL"
    input_tier: Literal["EXPLORATORY"] = "EXPLORATORY"
    historical_availability_verified: Literal[False] = False
    corporate_actions_verified: Literal[False] = False
    membership_verified: Literal[False] = False
    analytical_clock: Literal["INTERVAL_CLOSE_ASSUMED_NOT_HISTORICAL_AVAILABILITY"] = (
        "INTERVAL_CLOSE_ASSUMED_NOT_HISTORICAL_AVAILABILITY"
    )
    execution_authority: Literal[False] = False


class ResearchSeries(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    name: str
    unit: str
    timestamps: tuple[AwareDatetime, ...]
    values: tuple[float | None, ...]
    instrument: str = ""

    @model_validator(mode="after")
    def matched(self) -> ResearchSeries:
        if len(self.timestamps) != len(self.values):
            raise ValueError("RESEARCH_SERIES_LENGTH_MISMATCH")
        if any(b <= a for a, b in zip(self.timestamps, self.timestamps[1:], strict=False)):
            raise ValueError("RESEARCH_SERIES_CHRONOLOGY_INVALID")
        return self


class FrozenResearchResult(Artifact):
    run_id: str
    engine: ResearchEngine
    specification: str
    context: ResearchRunContext
    # A canonical JSON payload keeps nested engine reports immutable and permits
    # the existing non-Artifact engine models without mutable dicts in this model.
    report_json: str
    series: tuple[ResearchSeries, ...] = ()
    warnings: tuple[str, ...] = ()
    data_kind: Literal["REAL"] = "REAL"
    input_tier: Literal["EXPLORATORY"] = "EXPLORATORY"
    validation_state: Literal["NOT_TESTED"] = "NOT_TESTED"
    gate_outcome: Literal["NOT_TESTED"] = "NOT_TESTED"
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def bound_context(self) -> FrozenResearchResult:
        self.context.verified()
        if self.run_id != self.context.run_id or self.engine != self.context.parameters.engine:
            raise ValueError("RESEARCH_RESULT_CONTEXT_MISMATCH")
        if not isinstance(json.loads(self.report_json), dict):
            raise ValueError("RESEARCH_REPORT_OBJECT_REQUIRED")
        return self

    def envelope(self) -> dict[str, Any]:
        report = json.loads(self.report_json)
        return {
            **report,
            "run_id": self.run_id,
            "experiment_id": self.run_id,
            "engine": self.engine,
            "specification": self.specification,
            "context": self.context.model_dump(mode="json"),
            "context_hash": self.context.content_hash,
            "history_hashes": list(self.context.history_hashes),
            "input_hash": self.context.input_hash,
            "result_hash": self.content_hash,
            "evidence_hash": self.content_hash,
            "data_kind": "REAL",
            "input_tier": "EXPLORATORY",
            "source": "kite-historical-v3",
            "gate_outcome": "NOT_TESTED",
            "validation_state": "NOT_TESTED",
            "status": "completed",
            "series": [row.model_dump(mode="json") for row in self.series],
            "warnings": list(self.warnings),
            "execution_authority": False,
            "live_trading": False,
        }


_INPUT_INDEX_LOCK = RLock()
_INPUT_INDEX_CACHE: dict[Path, tuple[tuple[object, ...], tuple[ResearchInput, ...]]] = {}


def _input_store_signature(path: Path) -> tuple[object, ...]:
    signature: list[object] = []
    for name in (path, path.with_name(path.name + "-wal")):
        try:
            stat = name.stat()
            signature.extend((stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
        except FileNotFoundError:
            signature.append(None)
    return tuple(signature)


def list_research_inputs(repository_path: Path) -> tuple[ResearchInput, ...]:
    """Immutable metadata inventory, not an execution/provenance verification.

    Project only the required fields in SQLite. Repeated desktop pages share a
    bounded cache invalidated by database *and WAL* changes. Executing a job still
    loads and hash-verifies every complete FrozenMarketHistory independently.
    """
    path = repository_path.resolve()
    if not path.is_file():
        return ()
    with _INPUT_INDEX_LOCK:
        for _attempt in range(3):
            signature = _input_store_signature(path)
            previous = _INPUT_INDEX_CACHE.get(path)
            if previous is not None and previous[0] == signature:
                return previous[1]
            try:
                connection = sqlite3.connect("file:" + quote(str(path)) + "?mode=ro", uri=True)
                try:
                    rows = connection.execute(
                        """
                        SELECT identity,
                            json_extract(payload_json, '$.artifact.content_hash'),
                            json_extract(payload_json, '$.artifact.instrument'),
                            json_extract(payload_json, '$.artifact.interval'),
                            json_array_length(payload_json, '$.artifact.candles'),
                            json_extract(payload_json, '$.artifact.candles[0].time'),
                            json_extract(payload_json, '$.artifact.candles[#-1].time'),
                            json_extract(payload_json, '$.artifact.captured_at'),
                            json_extract(payload_json, '$.artifact.source'),
                            (SELECT count(*) FROM json_each(
                                json_extract(records.payload_json, '$.artifact.candles'))
                             WHERE json_extract(value, '$.volume') IS NULL)
                        FROM control_plane_records AS records
                        WHERE namespace = 'agent_artifacts'
                          AND json_extract(payload_json, '$.type') = 'FrozenMarketHistory'
                          AND json_extract(payload_json, '$.artifact.data_kind') = 'REAL'
                        """
                    ).fetchall()
                finally:
                    connection.close()
                items = []
                for (
                    key,
                    artifact_hash,
                    instrument,
                    interval,
                    bars,
                    first,
                    last,
                    captured,
                    source,
                    missing,
                ) in rows:
                    if key != artifact_hash or source != "kite-historical-v3":
                        raise ValueError("FROZEN_HISTORY_METADATA_BINDING_INVALID")
                    items.append(
                        ResearchInput(
                            history_hash=key,
                            dataset_id="kite-" + instrument.replace(":", "-") + "-" + interval,
                            version=key,
                            instrument=instrument,
                            interval=interval,
                            bars=bars,
                            first_bar=first,
                            last_bar=last,
                            captured_at=captured,
                            source=source,
                            missing_volume=missing,
                        )
                    )
                result = tuple(sorted(items, key=lambda row: row.captured_at, reverse=True))
            except (sqlite3.Error, ValueError, TypeError, AttributeError, OSError):
                _INPUT_INDEX_CACHE.pop(path, None)
                raise DataIntegrityError("RESEARCH_HISTORY_INDEX_UNAVAILABLE") from None
            if _input_store_signature(path) == signature:
                _INPUT_INDEX_CACHE[path] = (signature, result)
                if len(_INPUT_INDEX_CACHE) > 16:
                    _INPUT_INDEX_CACHE.pop(next(iter(_INPUT_INDEX_CACHE)))
                return result
        raise DataIntegrityError("RESEARCH_HISTORY_INDEX_BUSY: capture writes are still changing")


def list_research_results(
    repository_path: Path,
    engine: str | None = None,
    history_hashes: tuple[str, ...] | None = None,
) -> tuple[FrozenResearchResult, ...]:
    repository = AgentRepository(repository_path)
    try:
        rows = repository.list(FrozenResearchResult)
        published = {
            event.artifact_hash
            for event in repository.audit_events()
            if event.event == "RESEARCH_COMPLETED"
        }
    finally:
        repository.close()
    return tuple(
        sorted(
            (
                r
                for r in rows
                if r.content_hash in published
                and (engine is None or r.engine == engine)
                and (history_hashes is None or set(r.context.history_hashes) == set(history_hashes))
            ),
            key=lambda r: r.created_at,
            reverse=True,
        )
    )


def load_research_run(repository_path: Path, run_id: str) -> FrozenResearchResult:
    """Exact artifact hash or exact run identity; never an unrelated latest result."""
    repository = AgentRepository(repository_path)
    try:
        try:
            result = repository.get(run_id, FrozenResearchResult).verified()
        except KeyError:
            rows = [r for r in repository.list(FrozenResearchResult) if r.run_id == run_id]
            if len(rows) != 1:
                raise DataIntegrityError("RESEARCH_RUN_NOT_FOUND_OR_AMBIGUOUS") from None
            result = rows[0].verified()
        if not any(
            e.event == "RESEARCH_COMPLETED" and e.artifact_hash == result.content_hash
            for e in repository.audit_events(result.run_id)
        ):
            raise DataIntegrityError("RESEARCH_RUN_NOT_PUBLISHED: persistence did not complete")
        return result
    finally:
        repository.close()


def execute_research_workbench(
    job: Job,
    repository_path: Path,
    ledger_path: Path,
    fabric_root: Path | None = None,
) -> dict[str, Any]:
    """JobService callback. All I/O is local evidence; no market/order endpoints."""
    del fabric_root  # This adapter deliberately does not certify or mutate the PIT catalog.
    _assert_safety()
    parameters = ResearchRunParameters.model_validate(job.parameters)
    _cancelled(job)
    frame = load_exploratory_frame(
        repository_path,
        parameters.history_hashes,
        minimum_bars=_minimum_bars(parameters),
        start=parameters.start,
        end=parameters.end,
    )
    specification = parameters.specification or DEFAULT_SPECIFICATIONS[parameters.engine]
    parents = _validate_parents(repository_path, parameters, frame)
    job.progress = 0.15
    now = datetime.now(UTC)
    run_id = "research-" + job.job_id
    context = ResearchRunContext(
        created_at=now,
        run_id=run_id,
        correlation_id=job.job_id,
        parameters=parameters,
        input_hash=frame.input_hash,
        history_hashes=tuple(h.content_hash for h in frame.histories),
        universe=tuple(str(i.id) for i in frame.instruments),
        interval=frame.interval,
        aligned_bars=len(frame.dates),
        analytical_start=frame.dates[0],
        analytical_end=frame.dates[-1],
        captured_at=tuple(h.captured_at for h in frame.histories),
        dropped_bars=frame.dropped_bars,
    )
    from quantlab.app.research_workbench_engines import calculate_research

    report, series, warnings = calculate_research(
        frame, parameters, specification, cancelled=lambda: _cancelled(job), parents=parents
    )
    _cancelled(job)
    job.progress = 0.85
    result = FrozenResearchResult(
        created_at=now,
        run_id=run_id,
        engine=parameters.engine,
        specification=specification,
        context=context,
        report_json=json.dumps(_finite(report), sort_keys=True, allow_nan=False),
        series=tuple(series),
        warnings=tuple(
            [
                "Exploratory broker history: historical revisions/availability, "
                "corporate actions and membership are NOT_TESTED.",
                "Interval-close analytical timestamps are an assumption, "
                "not verified historical availability.",
                *(
                    [
                        "Timestamp intersection dropped unaligned bars; "
                        "no forward fill or interpolation."
                    ]
                    if any(frame.dropped_bars)
                    else []
                ),
                *warnings,
            ]
        ),
    )
    _assert_safety()
    job.begin_publication()
    repository = AgentRepository(repository_path)
    try:
        repository.put(context)
        repository.put(result)
        _append_ledger(ledger_path, result)
        repository.audit(
            "RESEARCH_COMPLETED", run_id=run_id, now=now, artifact_hash=result.content_hash
        )
    finally:
        repository.close()
    job.progress = 1.0
    return result.envelope()


def _minimum_bars(parameters: ResearchRunParameters) -> int:
    if parameters.engine in {"model", "adaptive", "ensemble"}:
        return max(45, parameters.lookback + parameters.training_window + parameters.horizon + 3)
    if parameters.engine == "discovery":
        return max(80, parameters.lookback + parameters.horizon + 30)
    return max(parameters.lookback + parameters.horizon + 3, 25)


def available_research_specifications(engine: str) -> tuple[str, ...]:
    from quantlab.app.research_workbench_engines import available_research_specifications as options

    return options(engine)


def _validate_parents(
    repository_path: Path, parameters: ResearchRunParameters, frame: ExploratoryFrame
) -> tuple[FrozenResearchResult, ...]:
    parents = []
    for value in parameters.parent_hashes:
        parent = load_research_run(repository_path, value)
        if parent.context.input_hash != frame.input_hash:
            raise DataIntegrityError(
                "INCOMPATIBLE_RESEARCH_PARENT: exact aligned input bundle required"
            )
        parents.append(parent)
    if parents and parameters.engine not in {"ensemble", "portfolio", "risk"}:
        raise DataIntegrityError(
            "PARENT_OVERRIDE_UNSUPPORTED: this engine recomputes its explicit versioned inputs; "
            "choose no parent, or use ensemble/portfolio/risk for linked consumption."
        )
    return tuple(parents)


def _cancelled(job: Job) -> None:
    if job.cancel_event.is_set():
        raise ValueError("cancelled")


def _finite(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): _finite(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_finite(v) for v in value]
    return value


def _append_ledger(path: Path, result: FrozenResearchResult) -> None:
    from quantlab.research.envinfo import environment, git_commit, git_dirty

    context, report = result.context, json.loads(result.report_json)
    metrics = {
        k: float(v)
        for k, v in report.get("metrics", {}).items()
        if isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v)
    }
    common: dict[str, Any] = dict(
        id=result.run_id,
        name=f"{result.engine}:{result.specification}",
        hypothesis="Explicit exploratory engine calculation on a frozen real-capture bundle; "
        "independent historical availability and validation remain unverified.",
        status=ExperimentStatus.COMPLETED,
        git_commit=git_commit(),
        git_dirty=git_dirty(),
        dataset_version=context.input_hash,
        dataset_id="frozen_capture_bundle",
        snapshot_id=context.input_hash,
        universe=list(context.universe),
        training_period=(
            f"{context.analytical_start.isoformat()} → {context.analytical_end.isoformat()}"
        ),
        data_kind="REAL",
        transaction_cost_bps=context.parameters.cost_bps,
        lineage={
            "source": "kite-historical-v3",
            "context_hash": context.content_hash,
            "result_hash": result.content_hash,
            "input_tier": "EXPLORATORY",
            "history_hashes": ",".join(context.history_hashes),
            "interval": context.interval,
        },
        metrics=metrics,
        integrity={"pit_query": "NOT_TESTED", "corporate_actions": "NOT_TESTED"},
        application_version=__version__,
        conclusion="Exploratory calculation completed; independent validation NOT_TESTED.",
        config_hash=digest(context.parameters.model_dump(mode="json")),
        research_type=result.engine,
        selection_stage="exploratory_" + result.engine,
        gate_outcome="NOT_TESTED",
        gate_reasons={"input_tier": "EXPLORATORY: no historical availability/PIT certification"},
        validation_protocol="exploratory_capture_diagnostic",
        price_adjustment_method="BROKER_PROVIDED_UNVERIFIED",
        corporate_action_policy="NOT_TESTED",
        python_version=environment()["python"],
    )
    identity_field = {
        "features": "feature_id",
        "alpha": "alpha_id",
        "regime": "regime_model_id",
        "adaptive": "adaptive_model_id",
        "model": "statistical_model_id",
        "ensemble": "ensemble_id",
        "portfolio": "portfolio_id",
        "risk": "risk_model_id",
    }.get(result.engine)
    if identity_field:
        common[identity_field] = result.specification
    ExperimentLedger(path).append(ExperimentRun(**common))
