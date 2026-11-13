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

    def append_with_prior_records(
        self,
        *,
        namespace: str,
        identity: str,
        payload: dict[str, Any],
        payload_hash: str,
        event: str,
    ) -> list[dict[str, Any]]:
        """Atomically append one immutable record and return its prior namespace records.

        The returned rows include their matching audit fields so the caller can
        verify domain-specific hashes and reject malformed history. The snapshot
        and insert share the same SQLite write transaction across processes.
        """
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as connection:
            orphan = connection.execute(
                """
                SELECT 1 FROM control_plane_audit AS a
                LEFT JOIN control_plane_records AS r
                  ON r.namespace = a.namespace AND r.identity = a.identity
                 AND r.revision = a.revision
                WHERE a.namespace = ? AND r.identity IS NULL LIMIT 1
                """,
                (namespace,),
            ).fetchone()
            if orphan is not None:
                raise ControlPlaneStoreError("control-plane audit has missing record")
            rows = connection.execute(
                """
                SELECT r.identity, r.payload_json, r.payload_hash,
                       a.event AS audit_event, a.payload_hash AS audit_hash
                FROM control_plane_records AS r
                LEFT JOIN control_plane_audit AS a
                  ON r.namespace = a.namespace AND r.identity = a.identity
                 AND r.revision = a.revision
                WHERE r.namespace = ?
                ORDER BY r.recorded_at, r.identity
                """,
                (namespace,),
            ).fetchall()
            if any(str(row["identity"]) == identity for row in rows):
                raise ControlPlaneStoreError("immutable control-plane identity collision")
            connection.execute(
                """
                INSERT INTO control_plane_records
                (namespace, identity, revision, payload_hash, payload_json, recorded_at)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (namespace, identity, payload_hash, canonical, now),
            )
            connection.execute(
                """
                INSERT INTO control_plane_audit
                (namespace, identity, revision, event, payload_hash, recorded_at)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (namespace, identity, event, payload_hash, now),
            )
        return [dict(row) for row in rows]

    def record_and_prior_records(
        self, namespace: str, identity: str
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Read a record and the namespace records preceding its audit sequence."""
        with self._transaction() as connection:
            target = connection.execute(
                """
                SELECT r.identity, r.payload_json, r.payload_hash,
                       a.audit_id, a.event AS audit_event, a.payload_hash AS audit_hash
                FROM control_plane_records AS r
                LEFT JOIN control_plane_audit AS a
                  ON r.namespace = a.namespace AND r.identity = a.identity
                 AND r.revision = a.revision
                WHERE r.namespace = ? AND r.identity = ?
                """,
                (namespace, identity),
            ).fetchall()
            if not target:
                orphan = connection.execute(
                    "SELECT 1 FROM control_plane_audit WHERE namespace = ? AND identity = ?",
                    (namespace, identity),
                ).fetchone()
                if orphan is not None:
                    raise ControlPlaneStoreError("control-plane audit has missing record")
                return None, []
            if len(target) != 1 or target[0]["audit_id"] is None:
                raise ControlPlaneStoreError("control-plane record audit is ambiguous")
            audit_id = target[0]["audit_id"]
            orphan = connection.execute(
                """
                SELECT 1 FROM control_plane_audit AS a
                LEFT JOIN control_plane_records AS r
                  ON r.namespace = a.namespace AND r.identity = a.identity
                 AND r.revision = a.revision
                WHERE a.namespace = ? AND a.audit_id < ? AND r.identity IS NULL LIMIT 1
                """,
                (namespace, audit_id),
            ).fetchone()
            if orphan is not None:
                raise ControlPlaneStoreError("control-plane audit has missing prior record")
            prior = connection.execute(
                """
                SELECT r.identity, r.payload_json, r.payload_hash,
                       a.event AS audit_event, a.payload_hash AS audit_hash
                FROM control_plane_records AS r
                LEFT JOIN control_plane_audit AS a
                  ON r.namespace = a.namespace AND r.identity = a.identity
                 AND r.revision = a.revision
                WHERE r.namespace = ? AND (a.audit_id < ? OR a.audit_id IS NULL)
                ORDER BY a.audit_id
                """,
                (namespace, audit_id),
            ).fetchall()
        return dict(target[0]), [dict(row) for row in prior]

    def list_latest(
        self, namespace: str, *, payload_type: str | None = None
    ) -> list[dict[str, Any]]:
        type_filter = (
            " AND json_extract(current.payload_json, '$.type') = ?" if payload_type else ""
        )
        parameters = (
            (namespace, namespace, payload_type) if payload_type else (namespace, namespace)
        )
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
                WHERE current.namespace = ?
                """
                + type_filter
                + " ORDER BY current.recorded_at, current.identity",
                parameters,
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
