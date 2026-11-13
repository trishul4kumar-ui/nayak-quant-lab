"""SQLite-backed background jobs. The UI must not run these on the GUI thread."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCancelledError(RuntimeError):
    """Cancellation was accepted before publication; no output may be published."""


@dataclass
class Job:
    job_id: str
    type: str
    status: JobStatus
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    progress: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    _state_lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False, compare=False
    )
    _publication_started: bool = field(default=False, init=False, repr=False, compare=False)

    @property
    def publication_started(self) -> bool:
        with self._state_lock:
            return self._publication_started

    def begin_publication(self) -> None:
        """Atomically commit to publishing a result, or honor an accepted cancellation.

        Call immediately before the first result/artifact/ledger write. Once this
        method succeeds, cancellation is no longer accepted: success must retain
        its result and a publication exception must be reported as FAILED. This
        does not make several storage writes transactional; incomplete publication
        is still excluded by the artifact's completion audit.
        """
        with self._state_lock:
            if self._publication_started:
                return
            if self.cancel_event.is_set():
                raise JobCancelledError("cancelled before publication")
            self._publication_started = True

    def request_cancel(self) -> bool:
        """Return whether cancellation is accepted; publication/terminal jobs refuse it."""
        with self._state_lock:
            if self._publication_started or self.status not in {
                JobStatus.QUEUED,
                JobStatus.RUNNING,
                JobStatus.PAUSED,
                JobStatus.CANCELLING,
            }:
                return False
            self.cancel_event.set()
            self.status = JobStatus.CANCELLING
            return True


JobFn = Callable[["Job"], dict[str, Any]]


class JobService:
    def __init__(self, db_path: Path, max_workers: int = 2) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._jobs: dict[str, Job] = {}
        self._event_sink: Callable[[dict[str, Any]], None] | None = None
        self._event_states: dict[str, str] = {}
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                progress REAL NOT NULL,
                parameters TEXT NOT NULL,
                result TEXT NOT NULL,
                error TEXT
            )
            """
        )
        self._conn.commit()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="quantlab-job")

    def set_event_sink(self, sink: Callable[[dict[str, Any]], None]) -> None:
        """Attach the runtime log sink. Events expose IDs/states, never parameters/secrets."""
        self._event_sink = sink

    def _emit_transition(self, job: Job) -> None:
        if self._event_states.get(job.job_id) == job.status.value:
            return
        self._event_states[job.job_id] = job.status.value
        if self._event_sink is None:
            return
        from quantlab.agents.hashing import safe_text

        event: dict[str, Any] = {
            "event": "job_lifecycle",
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "component": "jobs",
            "job_id": job.job_id,
            "correlation_id": job.job_id,
            "job_type": job.type,
            "state": job.status.value,
            "level": "error" if job.status is JobStatus.FAILED else "info",
        }
        if job.error:
            event["error"] = safe_text(job.error)[:2000]
        if job.result.get("experiment_id"):
            event["experiment_id"] = str(job.result["experiment_id"])
        # Logging is not allowed to change a computation's result.
        with suppress(Exception):
            self._event_sink(event)

    def persisted_events(self, limit: int = 400) -> list[dict[str, Any]]:
        """Read retained job outcomes so failures remain visible after a restart."""
        from quantlab.agents.hashing import safe_text

        with self._lock:
            rows = self._conn.execute(
                "SELECT job_id, type, status, created_at, completed_at, error FROM jobs "
                "ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 2000)),),
            ).fetchall()
        return [
            {
                "event": "job_outcome",
                "job_id": job_id,
                "correlation_id": job_id,
                "job_type": job_type,
                "state": status,
                "timestamp": completed or created,
                "level": "error" if status == "failed" else "info",
                "error": safe_text(error)[:2000] if error else "",
            }
            for job_id, job_type, status, created, completed, error in reversed(rows)
        ]

    def submit(self, job_type: str, fn: JobFn, parameters: dict[str, Any] | None = None) -> Job:
        now = datetime.now(tz=UTC).isoformat()
        job = Job(
            job_id=uuid4().hex,
            type=job_type,
            status=JobStatus.QUEUED,
            created_at=now,
            parameters=dict(parameters or {}),
        )
        with self._lock:
            self._jobs[job.job_id] = job
            self._persist(job)
        self._pool.submit(self._run, job, fn)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def cancel(self, job_id: str) -> Job | Literal[False] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if not job.request_cancel():
                return False
            self._persist(job)
            return job

    def experiment_completed_at(self, experiment_id: str) -> str | None:
        """Best-effort timestamp from persisted job results."""
        if not experiment_id:
            return None
        with self._lock:
            try:
                rows = self._conn.execute(
                    """
                    SELECT completed_at, result FROM jobs
                    WHERE status = ? AND result LIKE ?
                    ORDER BY completed_at DESC LIMIT 1
                    """,
                    (JobStatus.COMPLETED.value, f"%{experiment_id}%"),
                ).fetchall()
            except sqlite3.Error:
                return None
        for completed_at, raw in rows:
            if not completed_at or not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if str(payload.get("experiment_id", "")) == experiment_id:
                return str(completed_at)
        return None

    def cancel_all(self) -> None:
        with self._lock:
            for job in self._jobs.values():
                if job.request_cancel():
                    self._persist(job)

    def shutdown(self, wait: bool = True) -> None:
        self.cancel_all()
        self._pool.shutdown(wait=wait, cancel_futures=True)
        with self._lock:
            self._conn.close()

    def _run(self, job: Job, fn: JobFn) -> None:
        with job._state_lock:
            cancelled_before_start = job.cancel_event.is_set() and not job._publication_started
            if cancelled_before_start:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(tz=UTC).isoformat()
            else:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(tz=UTC).isoformat()
                job.progress = 0.05
        self._persist(job)
        if cancelled_before_start:
            return
        try:
            result = fn(job)
            with job._state_lock:
                if job.cancel_event.is_set() and not job._publication_started:
                    job.status = JobStatus.CANCELLED
                    job.error = "cancelled"
                else:
                    job.status = JobStatus.COMPLETED
                    job.result = result
                    job.progress = 1.0
        except Exception as exc:
            from quantlab.agents.hashing import safe_text

            with job._state_lock:
                job.status = (
                    JobStatus.CANCELLED
                    if job.cancel_event.is_set() and not job._publication_started
                    else JobStatus.FAILED
                )
                job.error = safe_text(str(exc))[:4000]
        job.completed_at = datetime.now(tz=UTC).isoformat()
        self._persist(job)

    def _persist(self, job: Job) -> None:
        with self._lock:
            try:
                self._conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs
                    (job_id, type, status, created_at, started_at, completed_at,
                     progress, parameters, result, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id,
                        job.type,
                        job.status.value,
                        job.created_at,
                        job.started_at,
                        job.completed_at,
                        job.progress,
                        json.dumps(job.parameters),
                        json.dumps(job.result, default=str),
                        job.error,
                    ),
                )
                self._conn.commit()
                self._emit_transition(job)
            except sqlite3.ProgrammingError:
                return
