"""Application boundary for reconciliation reports. Qt only receives immutable payloads."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from quantlab.agents.hashing import Artifact
from quantlab.agents.repository import AgentRepository
from quantlab.broker_gateway.service import last_snapshot, matching_internal_books, snapshot
from quantlab.core.errors import DataIntegrityError
from quantlab.data.policy import fixtures_enabled
from quantlab.reconciliation.models import InternalAccountSnapshot
from quantlab.reconciliation.repository import audit, exceptions, last
from quantlab.reconciliation.service import internal_from_books, reconcile

_LAST: dict[str, Any] | None = None


class IndependentInternalBooks(Artifact):
    snapshot: InternalAccountSnapshot
    origin: Literal["internal_event_ledger", "operator_internal_book"]
    source_document_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    independently_maintained: Literal[True]
    execution_authority: Literal[False] = False


def import_internal_books(path: Path, *, repository_path: Path | None = None) -> dict[str, Any]:
    """Import an independently authored internal book, never derive it from Kite."""
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise DataIntegrityError(
            "INTERNAL_BOOK_FILE_REQUIRED: select an independent JSON book under 1 MB"
        )
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("independently_maintained") is not True:
        raise DataIntegrityError(
            "INDEPENDENT_INTERNAL_BOOK_REQUIRED: broker or paper copies cannot establish agreement"
        )
    item = IndependentInternalBooks.model_validate(
        {
            "created_at": datetime.now(UTC),
            "snapshot": data.get("snapshot"),
            "origin": data.get("origin"),
            "source_document_hash": hashlib.sha256(raw).hexdigest(),
            "independently_maintained": True,
        }
    )
    if item.snapshot.observed_at.tzinfo is None:
        raise DataIntegrityError("INTERNAL_BOOK_TIMEZONE_REQUIRED")
    repository = AgentRepository(repository_path)
    try:
        repository.put(item)
    finally:
        repository.close()
    return {
        "internal_snapshot_hash": item.content_hash,
        "internal_snapshot_id": item.snapshot.snapshot_id,
        "observed_at": item.snapshot.observed_at.isoformat(),
        "origin": item.origin,
        "live_trading": False,
    }


def internal_book_choices(repository_path: Path | None = None) -> list[dict[str, Any]]:
    repository = AgentRepository(repository_path)
    try:
        return [
            {
                "internal_snapshot_hash": item.content_hash,
                "internal_snapshot_id": item.snapshot.snapshot_id,
                "observed_at": item.snapshot.observed_at.isoformat(),
                "origin": item.origin,
            }
            for item in repository.list(IndependentInternalBooks)
        ]
    finally:
        repository.close()


def run_payload(
    *,
    internal_snapshot_hash: str = "",
    repository_path: Path | None = None,
    broker_snapshot_id: str = "",
) -> dict[str, Any]:
    from quantlab.broker_gateway.repository import get_bundle

    broker = get_bundle(broker_snapshot_id) if broker_snapshot_id else last_snapshot()
    internal = None
    if internal_snapshot_hash:
        repository = AgentRepository(repository_path)
        try:
            internal = repository.get(internal_snapshot_hash, IndependentInternalBooks).snapshot
        except KeyError:
            raise DataIntegrityError(
                "INTERNAL_STATE_UNAVAILABLE: select the imported independent book"
            ) from None
        finally:
            repository.close()
    elif fixtures_enabled():
        broker = broker or snapshot()
        internal = internal_from_books(
            matching_internal_books(), observed_at=broker.provenance.source_timestamp
        )
    # Fixture comparisons stay reproducible at their recorded timestamp; real
    # imported snapshots are evaluated against the actual comparison time.
    observed_at = None if fixtures_enabled() else datetime.now(UTC)
    report = reconcile(broker, internal, observed_at=observed_at)
    payload = report.model_dump(mode="json")
    global _LAST
    _LAST = payload
    return payload


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def status_payload() -> dict[str, Any]:
    report = last()
    return {
        "status": report.status.value if report else "UNKNOWN",
        "exception_count": len(report.exceptions) if report else 0,
        "live_trading": False,
        "write_enabled": False,
    }


def exceptions_payload() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in exceptions()]


def audit_payload() -> list[dict[str, str]]:
    return audit()
