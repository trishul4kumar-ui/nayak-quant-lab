"""Append-only SQLite evidence storage with explicit migrations and WAL safety."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any


class ControlPlaneStoreError(RuntimeError):
    """A persistence failure that must block rather than silently fall back to memory."""


class ControlPlaneSqlite:
    """A small append-only evidence ledger shared by typed control-plane repositories.

    It stores canonical JSON payloads and hashes only; callers are responsible for
    keeping credentials out of the payload. ``append`` is atomic and idempotent for
    the same namespace, identity, and payload hash. A different payload for an
    immutable identity is rejected rather than overwritten.
    """

    schema_version = 2

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._closed = False
        self._connection = sqlite3.connect(
            str(path), check_same_thread=False, isolation_level=None, timeout=10.0
        )
        self._connection.row_factory = sqlite3.Row
        try:
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=FULL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._migrate()
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def append(
        self,
        *,
        namespace: str,
        identity: str,
        payload: dict[str, Any],
        payload_hash: str,
        immutable: bool = True,
        event: str,
    ) -> bool:
        """Persist one record and audit event; return False only for an exact replay."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as connection:
            existing = connection.execute(
                """
                SELECT payload_hash FROM control_plane_records
                WHERE namespace = ? AND identity = ?
                ORDER BY revision DESC LIMIT 1
                """,
                (namespace, identity),
            ).fetchone()
            if existing is not None:
                if str(existing["payload_hash"]) == payload_hash:
                    return False
                if immutable:
                    raise ControlPlaneStoreError(
                        f"immutable control-plane identity collision: {namespace}/{identity}"
                    )
            revision = connection.execute(
                """
                SELECT COALESCE(MAX(revision), 0) + 1 AS revision
                FROM control_plane_records WHERE namespace = ? AND identity = ?
                """,
                (namespace, identity),
            ).fetchone()["revision"]
            connection.execute(
                """
                INSERT INTO control_plane_records
                (namespace, identity, revision, payload_hash, payload_json, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (namespace, identity, revision, payload_hash, canonical, now),
            )
            connection.execute(
                """
                INSERT INTO control_plane_audit
                (namespace, identity, revision, event, payload_hash, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (namespace, identity, revision, event, payload_hash, now),
            )
        return True

    def get(self, namespace: str, identity: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT payload_json FROM control_plane_records
                WHERE namespace = ? AND identity = ?
                ORDER BY revision DESC LIMIT 1
                """,
                (namespace, identity),
            ).fetchone()
        return json.loads(str(row["payload_json"])) if row is not None else None

    def list_latest(self, namespace: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT current.payload_json FROM control_plane_records AS current
                JOIN (
                    SELECT identity, MAX(revision) AS revision
                    FROM control_plane_records
                    WHERE namespace = ? GROUP BY identity
                ) AS latest
                ON current.identity = latest.identity AND current.revision = latest.revision
                WHERE current.namespace = ? ORDER BY current.recorded_at, current.identity
                """,
                (namespace, namespace),
            ).fetchall()
        return [json.loads(str(row["payload_json"])) for row in rows]

    def audit(self, namespace: str | None = None) -> list[dict[str, str]]:
        query = (
            "SELECT namespace, identity, revision, event, payload_hash, recorded_at "
            "FROM control_plane_audit"
        )
        params: tuple[str, ...] = ()
        if namespace is not None:
            query += " WHERE namespace = ?"
            params = (namespace,)
        query += " ORDER BY audit_id"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            if self._closed:
                raise ControlPlaneStoreError("control-plane store is closed")
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                yield self._connection
                self._connection.execute("COMMIT")
            except sqlite3.Error as exc:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise ControlPlaneStoreError(f"control-plane SQLite failure: {exc}") from exc
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def _migrate(self) -> None:
        with self._transaction() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS control_plane_schema (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            current = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM control_plane_schema"
            ).fetchone()["version"]
            if current > self.schema_version:
                raise ControlPlaneStoreError(
                    f"database schema {current} is newer than supported {self.schema_version}"
                )
            if current == 0:
                connection.execute(
                    """
                    CREATE TABLE control_plane_records (
                        namespace TEXT NOT NULL,
                        identity TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        payload_hash TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        PRIMARY KEY (namespace, identity, revision)
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE control_plane_audit (
                        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        namespace TEXT NOT NULL,
                        identity TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        event TEXT NOT NULL,
                        payload_hash TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "INSERT INTO control_plane_schema (version, applied_at) VALUES (?, ?)",
                    (self.schema_version, datetime.now(tz=UTC).isoformat()),
                )
            elif current == 1:
                connection.execute(
                    """
                    CREATE TABLE control_plane_records_v2 (
                        namespace TEXT NOT NULL,
                        identity TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        payload_hash TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        PRIMARY KEY (namespace, identity, revision)
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO control_plane_records_v2
                    SELECT namespace, identity, revision, payload_hash, payload_json, recorded_at
                    FROM control_plane_records
                    """
                )
                connection.execute("DROP TABLE control_plane_records")
                connection.execute(
                    "ALTER TABLE control_plane_records_v2 RENAME TO control_plane_records"
                )
                connection.execute(
                    "INSERT INTO control_plane_schema (version, applied_at) VALUES (?, ?)",
                    (self.schema_version, datetime.now(tz=UTC).isoformat()),
                )
