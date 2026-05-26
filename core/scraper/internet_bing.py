import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from core.scraper.base import BaseScraper, RawJob


class BingInternetSearchScraper(BaseScraper):
    """Best-effort internet search using Bing HTML (no API key).

    This is intentionally conservative. It returns RawJob entries based on
    search-result snippets/links. Not guaranteed; Bing HTML changes.

    NOTE: This scraper scrapes a search results page and extracts links; it
    does NOT attempt to bypass CAPTCHAs.
    """

    SEARCH_URL = "https://www.bing.com/search"

    _job_url_re = re.compile(
        r"/(job|jobs|career|careers)/", re.I
    )

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        # Build a single query.
        query = " ".join([k for k in keywords[:5] if k])
        loc = (location or "").strip()
        if loc:
            query = f"{query} {loc}"

        url = f"{self.SEARCH_URL}?q={quote_plus(query)}"

        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "drift.jobs/1.0", "Accept-Language": "en-US,en;q=0.9"},
                timeout=30,
            )
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        results: list[RawJob] = []
        seen: set[str] = set()

        # Bing results usually contain anchors to real pages.
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            # Bing wraps outbound links with /ck/a?u=...
            if "bing.com/" in href and "ck/a" in href and "u=" in href:
                # Try to extract u param.
                m = re.search(r"[?&]u=([^&]+)", href)
                if m:
                    href = requests.utils.unquote(m.group(1))

            if not href or not href.startswith("http"):
                continue
            if not self._job_url_re.search(href):
                # Keep it safe: likely job pages only.
                continue

            key = href.lower().rstrip("/")
            if key in seen:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                # try title from nearby
                title_el = a.find_parent() and a.find_parent().select_one("h2")
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
                    source="bing",
                    job_type="",
                )
            )
            seen.add(key)

            if len(results) >= 50:
                break

        return results

