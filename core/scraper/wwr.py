import re

import requests
from bs4 import BeautifulSoup

from core.scraper.base import BaseScraper, RawJob


class WWRScraper(BaseScraper):
    BASE_URL = "https://weworkremotely.com/remote-jobs/search"

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        query = "-".join(k.lower().replace(" ", "-") for k in keywords[:2])
        url = f"{self.BASE_URL}?term={query}"
        response = requests.get(
            url,
            headers={"User-Agent": "drift.jobs/1.0"},
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[RawJob] = []
        for li in soup.select("li.feature")[:30]:
            link = li.select_one("a")
            title_el = li.select_one("span.title")
            company_el = li.select_one("span.company")
            region_el = li.select_one("span.region")
            if not link or not title_el:
                continue
            href = link.get("href", "")
            if href.startswith("/"):
                href = f"https://weworkremotely.com{href}"
            results.append(
                RawJob(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "",
                    location=region_el.get_text(strip=True) if region_el else "Remote",
                    description=title_el.get_text(strip=True),
                    url=href,
                    source="wwr",
                    job_type="Remote",
                )
            )
        if results:
            return results

        # Fallback: parse job links from listing page
        for a in soup.select("a[href*='/remote-jobs/']")[:30]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 4:
                continue
            if href.startswith("/"):
                href = f"https://weworkremotely.com{href}"
            if re.search(r"/remote-jobs/[^/]+$", href):
                results.append(
                    RawJob(
                        title=title,
                        company="",
                        location="Remote",
                        description=title,
                        url=href,
                        source="wwr",
                        job_type="Remote",
                    )
                )
        return results[:30]
