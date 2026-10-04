"""Freeze and verify the complete evidence boundary, including legacy shallow models."""

from __future__ import annotations

from datetime import datetime, timedelta
from math import isfinite
from typing import Self
from uuid import uuid4

from pydantic import model_validator

from quantlab.agents.contracts import (
    AgentIdentity,
    AgentMandate,
    AgentModelIdentity,
    AgentRunContext,
    AgentVersion,
    DataKind,
    ResearchMode,
    VersionReference,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.hashing import Artifact, digest
from quantlab.agents.repository import AgentRepository
from quantlab.domain.models import OHLCVBar
from quantlab.realtime_data.models import QualityStatus, RealTimeSnapshot


class FrozenSnapshot(Artifact):
    snapshot_hash: str
    # A string copy prevents mutation through legacy snapshot.extras/observations.
    canonical_snapshot_json: str

    def snapshot(self) -> RealTimeSnapshot:
        value = RealTimeSnapshot.model_validate_json(self.canonical_snapshot_json)
        if value.snapshot_hash != self.snapshot_hash:
            raise AgentContextError("SNAPSHOT_HASH_MISMATCH")
        return value

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        self.snapshot()
        return self


class FrozenHistory(Artifact):
    snapshot_hash: str
    bars_json: tuple[str, ...]
    price_basis: str
    data_kind: DataKind

    def bars(self) -> tuple[OHLCVBar, ...]:
        return tuple(OHLCVBar.model_validate_json(row) for row in self.bars_json)


def create_context(
    repository: AgentRepository,
    snapshot: RealTimeSnapshot,
    *,
    mandate: AgentMandate,
    model: AgentModelIdentity,
    now: datetime,
    mode: ResearchMode = ResearchMode.RESEARCH,
    ttl_seconds: int = 300,
    history: FrozenHistory | None = None,
    agent_version: AgentVersion | None = None,
) -> AgentRunContext:
    if now.tzinfo is None or snapshot.as_of.tzinfo is None:
        raise AgentContextError("TIMEZONE_REQUIRED")
    if ttl_seconds < 1 or ttl_seconds > 86400:
        raise AgentContextError("INVALID_TTL")
    if snapshot.as_of > now:
        raise AgentContextError("FUTURE_SNAPSHOT")
    if mode is not ResearchMode.REPLAY and (now - snapshot.as_of).total_seconds() > ttl_seconds:
        raise AgentContextError("STALE_SNAPSHOT")
    if snapshot.quality is not QualityStatus.VALID or not snapshot.observations:
        raise AgentContextError("UNHEALTHY_SNAPSHOT")
    for row in snapshot.observations:
        if row.quality is not QualityStatus.VALID or any(
            value is not None and not isfinite(value)
            for value in (row.price, row.bid, row.ask, row.quantity, row.volume)
        ):
            raise AgentContextError("UNHEALTHY_OBSERVATION")
        if max(row.event_time, row.receive_time, row.processing_time) > snapshot.as_of:
            raise AgentContextError("FUTURE_AVAILABLE_OBSERVATION")
    names = tuple(sorted({row.security_id for row in snapshot.observations}))
    manifest = str(snapshot.extras.get("source_manifest", "")).lower()
    synthetic_prefixes = ("mock", "synthetic")
    synthetic_rows = all(
        row.source.lower().startswith(synthetic_prefixes)
        and row.provenance.lower().startswith(synthetic_prefixes)
        for row in snapshot.observations
    )
    if manifest.startswith(synthetic_prefixes) and synthetic_rows:
        kind = DataKind.SYNTHETIC
    elif manifest.startswith("production-observe-only:") and all(
        row.source.lower() in manifest.split(":", 1)[1].split("|")
        and row.provenance
        and not row.provenance.lower().startswith(synthetic_prefixes)
        and not row.source.lower().startswith(synthetic_prefixes)
        for row in snapshot.observations
    ):
        kind = DataKind.REAL
    else:
        raise AgentContextError("UNVERIFIED_DATA_PROVENANCE")
    if history is not None:
        if history.snapshot_hash != snapshot.snapshot_hash or history.data_kind is not kind:
            raise AgentContextError("HISTORY_BOUNDARY_MISMATCH")
        if any(
            max(
                row.pit.available_time,
                row.pit.event_time,
                row.pit.effective_time,
                row.pit.ingestion_time,
            )
            > snapshot.as_of
            or str(row.instrument) not in names
            or row.price_kind != history.price_basis
            or row.data_kind.upper() != kind.value
            for row in history.bars()
        ):
            raise AgentContextError("INVALID_HISTORY_BOUNDARY")
        repository.put(history)
    snapshot_copy = repository.put(
        FrozenSnapshot(
            created_at=now,
            snapshot_hash=snapshot.snapshot_hash,
            canonical_snapshot_json=snapshot.model_dump_json(),
        )
    )
    prompt_hash = digest({"role": mandate.role, "mandate": mandate.mandate, "version": "39-v1"})
    context = repository.put(
        AgentRunContext(
            created_at=now,
            run_id=uuid4().hex,
            as_of=snapshot.as_of,
            expires_at=now + timedelta(seconds=ttl_seconds),
            snapshot_id=snapshot.snapshot_id,
            snapshot_hash=snapshot.snapshot_hash,
            snapshot_artifact_hash=snapshot_copy.content_hash,
            universe_id="frozen-observed-scope",
            universe_version="1",
            universe_hash=digest(names),
            security_scope=names,
            data_kind=kind,
            market_session=snapshot.session.value,
            source_versions=(
                VersionReference(
                    created_at=now,
                    name="market-source",
                    version=snapshot.schema_version,
                    source_hash=snapshot.source_manifest_hash,
                ),
            ),
            agent=AgentIdentity(
                created_at=now,
                agent_id=mandate.role.value,
                role=mandate.role,
                version=agent_version
                or AgentVersion(created_at=now, version="1", prompt_hash=prompt_hash),
            ),
            model=model,
            tool_policy_hash=mandate.content_hash,
            mode=mode,
            history_hash=history.content_hash if history else None,
        )
    )
    repository.audit(
        "RUN_CREATED", run_id=context.run_id, now=now, artifact_hash=context.content_hash
    )
    return context


def validate_context(repository: AgentRepository, context: AgentRunContext, now: datetime) -> None:
    context.verified()
    if now.tzinfo is None or now < context.created_at or now >= context.expires_at:
        raise AgentContextError("STALE_OR_INVALID_CLOCK")
    stored = repository.get(context.content_hash, AgentRunContext)
    frozen = repository.get(stored.snapshot_artifact_hash, FrozenSnapshot)
    if frozen.snapshot_hash != context.snapshot_hash or frozen.snapshot().as_of != context.as_of:
        raise AgentContextError("CONTEXT_SNAPSHOT_MISMATCH")
