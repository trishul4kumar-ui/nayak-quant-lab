from pathlib import Path
from threading import Barrier, Event, Thread

import pytest

from quantlab.app.jobs import Job, JobCancelledError, JobService, JobStatus


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


def test_cancel_before_publication_prevents_output(tmp_path: Path) -> None:
    service = JobService(tmp_path / "app.sqlite")
    computed, publish = Event(), Event()
    outputs: list[str] = []

    def work(job: Job) -> dict[str, str]:
        computed.set()
        assert publish.wait(2.0)
        job.begin_publication()
        outputs.append("artifact")
        return {"result_hash": "published"}

    try:
        job = service.submit("demo", work)
        assert computed.wait(2.0)
        assert service.cancel(job.job_id) is job
        publish.set()
        done = _wait(service, job.job_id)
        assert done.status is JobStatus.CANCELLED
        assert done.publication_started is False
        assert done.result == {}
        assert outputs == []
    finally:
        publish.set()
        service.shutdown()


@pytest.mark.parametrize("raw_signal", [False, True])
def test_cancel_after_publication_cannot_discard_completed_result(
    tmp_path: Path, raw_signal: bool
) -> None:
    service = JobService(tmp_path / "app.sqlite")
    publishing, finish = Event(), Event()
    events: list[dict[str, object]] = []
    service.set_event_sink(events.append)

    def work(job: Job) -> dict[str, str]:
        job.begin_publication()
        job.begin_publication()  # Multiple linked writes share one publication phase.
        publishing.set()
        assert finish.wait(2.0)
        return {"result_hash": "published"}

    try:
        job = service.submit("demo", work)
        assert publishing.wait(2.0)
        assert service.cancel(job.job_id) is False
        service.cancel_all()
        assert not job.cancel_event.is_set()
        assert job.status is JobStatus.RUNNING
        if raw_signal:
            # Legacy code may signal the raw Event without request_cancel(). Its
            # late signal cannot erase a guarded published result either.
            job.cancel_event.set()
        finish.set()
        done = _wait(service, job.job_id)
        assert done.status is JobStatus.COMPLETED
        assert done.result == {"result_hash": "published"}
        assert service.cancel(job.job_id) is False
    finally:
        finish.set()
        service.shutdown()
    assert "cancelling" not in {event["state"] for event in events}
    assert "cancelled" not in {event["state"] for event in events}
    assert events[-1]["state"] == "completed"


def test_publication_failure_stays_failed_despite_late_cancel(tmp_path: Path) -> None:
    service = JobService(tmp_path / "app.sqlite")
    publishing, finish = Event(), Event()

    def work(job: Job) -> dict[str, str]:
        job.begin_publication()
        publishing.set()
        assert finish.wait(2.0)
        job.cancel_event.set()
        raise RuntimeError("fixture publication failed")

    try:
        job = service.submit("demo", work)
        assert publishing.wait(2.0)
        assert service.cancel(job.job_id) is False
        finish.set()
        done = _wait(service, job.job_id)
        assert done.status is JobStatus.FAILED
        assert done.error == "fixture publication failed"
        assert done.result == {}
    finally:
        finish.set()
        service.shutdown()


def test_publication_and_cancellation_have_one_atomic_winner() -> None:
    def race_once() -> None:
        job = Job("race", "demo", JobStatus.RUNNING, "now")
        race = Barrier(2)
        outcomes: dict[str, bool] = {}

        def publish() -> None:
            race.wait(timeout=2.0)
            try:
                job.begin_publication()
                outcomes["publication"] = True
            except JobCancelledError:
                outcomes["publication"] = False

        def cancel() -> None:
            race.wait(timeout=2.0)
            outcomes["cancel"] = job.request_cancel()

        workers = [Thread(target=publish), Thread(target=cancel)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=2.0)
            assert not worker.is_alive()
        assert outcomes["publication"] is not outcomes["cancel"]
        assert job.publication_started is outcomes["publication"]
        assert job.cancel_event.is_set() is outcomes["cancel"]

    for _attempt in range(40):
        race_once()
