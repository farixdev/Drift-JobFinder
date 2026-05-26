import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from core.scraper.base import BaseScraper, RawJob


class ZipRecruiterScraper(BaseScraper):
    """Best-effort ZipRecruiter scraper.

    ZipRecruiter is highly dynamic and may change frequently. This scraper aims
    to extract job cards/links from the first few result pages using requests.
    """

    SEARCH_URL = "https://www.ziprecruiter.com/jobs"

    def _make_url(self, keywords: list[str], location: str, start: int) -> str:
        # ZipRecruiter commonly supports `search` and `location` query params.
        # We'll do best-effort construction.
        query = quote_plus(" ".join(keywords[:3]))
        loc = quote_plus(location or "")
        # `start` shifts paging.
        return f"{self.SEARCH_URL}?search={query}&location={loc}&start={start}"

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()

        # Collect in a small paging loop; worker will also stop at its target.
        # Keep this modest to avoid being blocked.
        max_pages = 3
        start = 0
        page_size_guess = 10

        query_words = [k for k in keywords[:5] if k]
        if not query_words:
            return []

        for _ in range(max_pages):
            url = self._make_url(query_words, location, start)
            try:
                resp = requests.get(
                    url,
                    headers={
                        "User-Agent": "drift.jobs/1.0",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
            except Exception:
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # Job cards can vary; try multiple selectors.
            candidates = []
            candidates.extend(soup.select("a.job-card-container"))
            candidates.extend(soup.select("a[data-testid='job-title']"))
            candidates.extend(soup.select("a[href*='/job/']"))

            for a in candidates:
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                if href.startswith("/"):
                    href = "https://www.ziprecruiter.com" + href
                if "/job/" not in href:
                    continue

                key = href.lower().rstrip("/")
                if key in seen:
                    continue

                title = a.get_text(strip=True)
                # Sometimes title is inside a child element; fallback.
                if not title:
                    title_el = a.select_one("[data-testid='job-title']") or a.select_one("h2")
                    title = title_el.get_text(strip=True) if title_el else ""

                if not title or len(title) < 3:
                    continue

                # Company sometimes appears near link.
                company = ""
                company_el = a.find_parent() and a.find_parent().select_one(
                    "[data-testid='company-name'], .company-name"
                )
                if company_el:
                    company = company_el.get_text(strip=True)

                jobs.append(
                    RawJob(
                        title=title[:120],
                        company=company[:120] if company else "",
                        location=location or "",
                        description=title,
                        url=href,
                        source="ziprecruiter",
                        job_type="",
                    )
                )
                seen.add(key)

                if len(jobs) >= 30:
                    return jobs

            start += page_size_guess
            time.sleep(1)

        return jobs[:50]

