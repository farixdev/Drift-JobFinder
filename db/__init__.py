import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "jobs.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                url TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                source TEXT,
                scraped_at TEXT
            )
            """
        )


def dedupe_by_url(jobs: list) -> list:
    """Remove duplicate URLs within one scan — does not block rescans."""
    seen: set[str] = set()
    fresh: list = []
    for job in jobs:
        key = (job.url or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        fresh.append(job)
    return fresh


def mark_jobs_seen(jobs: list) -> None:
    """Optional: call after a successful results view if you want cross-scan dedup."""
    with _connect() as conn:
        for job in jobs:
            if not job.url:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO seen_jobs (url, title, company, source, scraped_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (job.url, job.title, job.company, job.source),
            )
