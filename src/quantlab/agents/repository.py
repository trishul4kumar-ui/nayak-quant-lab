"""Durable hash-addressed research artifacts on the canonical control plane."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TypeVar
from uuid import uuid4

from pydantic import Field

from quantlab.agents.hashing import Artifact, digest
from quantlab.app.paths import RuntimePaths
from quantlab.control_plane.sqlite import ControlPlaneSqlite, ControlPlaneStoreError

T = TypeVar("T", bound=Artifact)


class AuditEvent(Artifact):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    event: str
    artifact_hash: str | None = None
    safe_code: str | None = None


class AgentRepository:
    def __init__(self, path: Path | None = None) -> None:
        with self._persistence():
            self.store = ControlPlaneSqlite(
                path or RuntimePaths.discover().database_dir / "agent_desk.sqlite"
            )

    @staticmethod
    @contextmanager
    def _persistence() -> Iterator[None]:
        try:
            yield
        except (sqlite3.Error, OSError, ControlPlaneStoreError):
            # Never expose filesystem paths, raw SQL, or a lower-level error to
            # a provider/presentation; and never silently substitute an in-memory DB.
            raise ControlPlaneStoreError("AGENT_PERSISTENCE_UNAVAILABLE") from None

    def put(self, artifact: T) -> T:
        verified = artifact.verified()
        with self._persistence():
            self.store.append(
                namespace="agent_artifacts",
                identity=verified.content_hash,
                payload={"type": type(verified).__name__, "artifact": verified.identity_payload()},
                payload_hash=verified.content_hash,
                event="ARTIFACT_FROZEN",
            )
        return verified

    def get(self, artifact_hash: str, contract: type[T]) -> T:
        with self._persistence():
            payload = self.store.get("agent_artifacts", artifact_hash)
        if payload is None or payload["type"] != contract.__name__:
            raise KeyError("artifact missing or wrong contract")
        return contract.model_validate(payload["artifact"])

    def list(self, contract: type[T]) -> tuple[T, ...]:
        with self._persistence():
            return tuple(
                contract.model_validate(row["artifact"])
                for row in self.store.list_latest("agent_artifacts")
                if row["type"] == contract.__name__
            )

    def audit(
        self,
        event: str,
        *,
        run_id: str,
        now: datetime,
        artifact_hash: str | None = None,
        safe_code: str | None = None,
    ) -> AuditEvent:
        item = AuditEvent(
            created_at=now,
            run_id=run_id,
            event=event,
            artifact_hash=artifact_hash,
            safe_code=safe_code,
        )
        with self._persistence():
            self.store.append(
                namespace="agent_audit",
                identity=item.event_id,
                payload=item.identity_payload(),
                payload_hash=item.content_hash,
                event=event,
            )
        return item

    def audit_events(self, run_id: str | None = None) -> tuple[AuditEvent, ...]:
        with self._persistence():
            rows = tuple(
                AuditEvent.model_validate(row) for row in self.store.list_latest("agent_audit")
            )
        return tuple(row for row in rows if run_id is None or row.run_id == run_id)

    def close(self) -> None:
        self.store.close()

    def claim_run(self, run_id: str, context_hash: str) -> bool:
        """Atomic, permanent claim: crashes cannot silently replay paid model calls."""
        payload = {"context_hash": context_hash}
        with self._persistence():
            return self.store.append(
                namespace="agent_run_claims",
                identity=run_id,
                payload=payload,
                payload_hash=digest(payload),
                event="RUN_CLAIMED",
            )
