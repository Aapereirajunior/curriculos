import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from auto_jobs.models import JobPosting

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    company TEXT NOT NULL,
    job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'found',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Tracker:
    """Registra vagas encontradas/aplicadas em SQLite para evitar duplicatas."""

    def __init__(self, db_path: str = "data/applications.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def already_seen(self, job: JobPosting) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM applications WHERE key = ?", (job.key,)
            ).fetchone()
        return row is not None

    def record(self, job: JobPosting, status: str = "found") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO applications
                    (key, source, company, job_id, title, url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (job.key, job.source, job.company, job.job_id, job.title, job.url, status, now, now),
            )

    def update_status(self, job: JobPosting, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET status = ?, updated_at = ? WHERE key = ?",
                (status, now, job.key),
            )

    def count_applied_today(self) -> int:
        today = datetime.now(timezone.utc).date().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'applied' AND updated_at LIKE ?",
                (f"{today}%",),
            ).fetchone()
        return row[0] if row else 0
