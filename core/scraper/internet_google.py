import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from core.scraper.base import BaseScraper, RawJob


class GoogleInternetSearchScraper(BaseScraper):
    """Best-effort internet search using Google HTML (no API key).

    WARNING:
    - Google frequently blocks automated scraping.
    - This scraper is designed to fail gracefully (return []) if blocked.
    - It extracts job-like URLs using heuristics from search-result anchors.

    The goal is to get *some* job links so the matcher can score them.
    """

    SEARCH_URL = "https://www.google.com/search"

    # Heuristics: job-like paths/pages.
    _job_url_re = re.compile(r"/(jobs|job|careers|career)/", re.I)

    def _build_query(self, keywords: list[str], location: str) -> str:
        # Use first few keywords as a proxy for "user skills".
        # Example: "software engineer skills" + "Lahore, Pakistan"
        kw = [k for k in keywords[:6] if k]
        base = " ".join(kw) if kw else "jobs"
        loc = (location or "").strip()
        if loc:
            return f"{base} in {loc}"
        return base

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        query = self._build_query(keywords, location)
        url = f"{self.SEARCH_URL}?q={quote_plus(query)}&hl=en&num=50"

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
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        results: list[RawJob] = []
        seen: set[str] = set()

        # Google results use many different structures; anchors are still present.
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue

            # Google often wraps outbound links in /url?q=...
            if href.startswith("/url?") and "q=" in href:
                m = re.search(r"[?&]q=([^&]+)", href)
                if m:
                    try:
                        from urllib.parse import unquote

                        href = unquote(m.group(1))
                    except Exception:
                        continue

            if not href.startswith("http"):
                continue

            if not self._job_url_re.search(href):
                continue

            key = href.lower().rstrip("/")
            if key in seen:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                # fallback: nearby headline-like element
                title_el = a.find_parent() and a.find_parent().select_one("h3")
                title = title_el.get_text(strip=True) if title_el else ""

            if not title:
                continue

            results.append(
                RawJob(
                    title=title[:120],
                    company="",
                    location=location or "",
                    description=title,
                    url=href,
                    source="google",
                    job_type="",
                )
            )
            seen.add(key)

            if len(results) >= 50:
                break

        return results

