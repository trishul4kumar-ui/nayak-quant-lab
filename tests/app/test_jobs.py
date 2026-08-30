from pathlib import Path
from threading import Event

from quantlab.app.jobs import Job, JobService, JobStatus


def _wait(service: JobService, job_id: str, timeout: float = 5.0) -> Job:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        job = service.get(job_id)
        assert job is not None
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return job
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_job_completes(tmp_path: Path) -> None:
    service = JobService(tmp_path / "app.sqlite")

    def work(job: Job) -> dict[str, str]:
        return {"ok": "yes"}

    job = service.submit("demo", work, {"a": 1})
    done = _wait(service, job.job_id)
    assert done.status is JobStatus.COMPLETED
    assert done.result["ok"] == "yes"
    service.shutdown()


def test_job_failure(tmp_path: Path) -> None:
    service = JobService(tmp_path / "app.sqlite")

    def boom(job: Job) -> dict[str, str]:
        raise RuntimeError("worker boom")

    job = service.submit("demo", boom)
    done = _wait(service, job.job_id)
    assert done.status is JobStatus.FAILED
    assert done.error is not None
    assert "boom" in done.error
    service.shutdown()


def test_job_cancel(tmp_path: Path) -> None:
    service = JobService(tmp_path / "app.sqlite")
    started = Event()

    def slow(job: Job) -> dict[str, str]:
        started.set()
        job.cancel_event.wait(5.0)
        return {}

    job = service.submit("demo", slow)
    assert started.wait(2.0)
    service.cancel(job.job_id)
    done = _wait(service, job.job_id)
    assert done.status is JobStatus.CANCELLED
    service.shutdown()
