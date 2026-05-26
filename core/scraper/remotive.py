import requests

from core.scraper.base import BaseScraper, RawJob


class RemotiveScraper(BaseScraper):
    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        query = " ".join(keywords[:2])
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query, "limit": 50},
            timeout=30,
        )
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
        return [
            RawJob(
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location="Remote",
                description=j.get("description", ""),
                url=j.get("url", ""),
                source="remotive",
                job_type=j.get("job_type", "Remote") or "Remote",
            )
            for j in jobs
            if j.get("title")
        ]
