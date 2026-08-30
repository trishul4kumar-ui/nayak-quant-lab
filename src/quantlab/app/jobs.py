"""SQLite-backed background jobs. The UI must not run these on the GUI thread."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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

    def request_cancel(self) -> None:
        self.cancel_event.set()
        if self.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED}:
            self.status = JobStatus.CANCELLING


JobFn = Callable[["Job"], dict[str, Any]]


class JobService:
    def __init__(self, db_path: Path, max_workers: int = 2) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._jobs: dict[str, Job] = {}
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

    def cancel(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.request_cancel()
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
                if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                    job.request_cancel()
                    self._persist(job)

    def shutdown(self, wait: bool = True) -> None:
        self.cancel_all()
        self._pool.shutdown(wait=wait, cancel_futures=True)
        with self._lock:
            self._conn.close()

    def _run(self, job: Job, fn: JobFn) -> None:
        if job.cancel_event.is_set():
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(tz=UTC).isoformat()
            self._persist(job)
            return
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(tz=UTC).isoformat()
        job.progress = 0.05
        self._persist(job)
        try:
            result = fn(job)
            if job.cancel_event.is_set():
                job.status = JobStatus.CANCELLED
                job.error = "cancelled"
            else:
                job.status = JobStatus.COMPLETED
                job.result = result
                job.progress = 1.0
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
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
            except sqlite3.ProgrammingError:
                return
