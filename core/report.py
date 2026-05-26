import csv
from datetime import datetime
from pathlib import Path

from models import Job


def export_csv(jobs: list[Job], threshold: int, output_path: str) -> str:
    path = Path(output_path)
    if path.suffix.lower() != ".csv":
        path = path.with_suffix(".csv")

    fieldnames = [
        "title",
        "company",
        "location",
        "job_type",
        "match_score",
        "matched_skills",
        "summary",
        "url",
        "source",
        "scraped_at",
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            writer.writerow(
                {
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "job_type": job.job_type,
                    "match_score": job.score,
                    "matched_skills": "; ".join(job.matched_skills),
                    "summary": job.summary,
                    "url": job.url,
                    "source": job.source,
                    "scraped_at": job.scraped_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

    return str(path.resolve())
