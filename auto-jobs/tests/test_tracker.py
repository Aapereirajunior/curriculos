import tempfile
from pathlib import Path

from auto_jobs.models import JobPosting
from auto_jobs.tracker import Tracker


def make_job(job_id="1"):
    return JobPosting(
        source="greenhouse",
        company="acme",
        job_id=job_id,
        title="Backend Engineer",
        location="Remote",
        url="https://example.com/job/" + job_id,
    )


def test_tracker_records_and_detects_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "applications.db")
        tracker = Tracker(db_path)
        job = make_job()

        assert not tracker.already_seen(job)
        tracker.record(job, status="found")
        assert tracker.already_seen(job)


def test_tracker_update_status():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "applications.db")
        tracker = Tracker(db_path)
        job = make_job()

        tracker.record(job, status="found")
        tracker.update_status(job, "applied")
        assert tracker.count_applied_today() == 1
