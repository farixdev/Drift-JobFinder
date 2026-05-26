from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Job:
    title: str
    company: str
    location: str
    job_type: str
    url: str
    source: str
    matched_skills: List[str] = field(default_factory=list)
    score: int = 0
    summary: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
