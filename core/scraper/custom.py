import json
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.scraper.base import BaseScraper, RawJob

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_SKIP_HREF = re.compile(
    r"^(#|mailto:|tel:|javascript:)|/(login|signin|signup|register|privacy|terms)\b",
    re.I,
)
_NOISE_TITLES = re.compile(
    r"^(home|about|contact|login|sign in|sign up|privacy|terms|cookie|menu|more)$",
    re.I,
)


class CustomSiteScraper(BaseScraper):
    def __init__(self, jobs_url: str):
        self.jobs_url = jobs_url.rstrip("/")
        parsed = urlparse(self.jobs_url)
        self._host = parsed.netloc.lower()
        self._company = parsed.netloc.replace("www.", "").split(".")[0].title()

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        html = self._fetch(self.jobs_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        jobs: list[RawJob] = []
        seen: set[str] = set()

        for extractor in (
            self._from_json_ld,
            self._from_job_containers,
            self._from_list_items,
            self._from_links,
        ):
            for job in extractor(soup, self.jobs_url):
                key = job.url.lower().rstrip("/")
                if key not in seen and job.title:
                    seen.add(key)
                    jobs.append(job)
            if len(jobs) >= 10:
                break

        return jobs[:50]

    def _fetch(self, url: str) -> str:
        try:
            response = requests.get(url, headers=_HEADERS, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception:
            return ""

    def _from_json_ld(self, soup: BeautifulSoup, base_url: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                jobs.extend(self._parse_ld_item(item, base_url))
        return jobs

    def _parse_ld_item(self, item: dict, base_url: str) -> list[RawJob]:
        if not isinstance(item, dict):
            return []
        jobs: list[RawJob] = []
        typ = item.get("@type", "")
        types = typ if isinstance(typ, list) else [typ]
        if "JobPosting" in types:
            title = item.get("title") or item.get("name") or ""
            desc = item.get("description") or title
            url = item.get("url") or base_url
            if title:
                jobs.append(
                    RawJob(
                        title=str(title).strip(),
                        company=self._company,
                        location=self._ld_location(item),
                        description=self._clean_html(str(desc))[:2000],
                        url=urljoin(base_url, str(url)),
                        source="custom",
                    )
                )
        for child in item.get("@graph", []) if isinstance(item.get("@graph"), list) else []:
            jobs.extend(self._parse_ld_item(child, base_url))
        return jobs

    def _ld_location(self, item: dict) -> str:
        loc = item.get("jobLocation") or item.get("location")
        if isinstance(loc, dict):
            addr = loc.get("address", loc)
            if isinstance(addr, dict):
                parts = [
                    addr.get("addressLocality"),
                    addr.get("addressRegion"),
                    addr.get("addressCountry"),
                ]
                return ", ".join(p for p in parts if p)
            return str(loc)
        if isinstance(loc, list) and loc:
            return self._ld_location(loc[0])
        return str(loc) if loc else ""

    def _from_job_containers(self, soup: BeautifulSoup, base_url: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        selectors = [
            "[class*='job-listing']",
            "[class*='job-list']",
            "[class*='job-item']",
            "[class*='job-card']",
            "[class*='job-post']",
            "[class*='opening']",
            "[class*='vacancy']",
            "[data-job-id]",
            "article",
        ]
        for sel in selectors:
            for node in soup.select(sel):
                job = self._node_to_job(node, base_url)
                if job:
                    jobs.append(job)
        return jobs

    def _from_list_items(self, soup: BeautifulSoup, base_url: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for li in soup.find_all("li"):
            anchor = li.find("a", href=True)
            if not anchor:
                continue
            job = self._anchor_to_job(anchor, base_url, li.get_text(" ", strip=True))
            if job:
                jobs.append(job)
        return jobs

    def _from_links(self, soup: BeautifulSoup, base_url: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for anchor in soup.find_all("a", href=True):
            job = self._anchor_to_job(anchor, base_url)
            if job:
                jobs.append(job)
        return jobs

    def _node_to_job(self, node, base_url: str) -> RawJob | None:
        anchor = node.find("a", href=True)
        if anchor:
            return self._anchor_to_job(anchor, base_url, node.get_text(" ", strip=True))
        title_el = node.find(["h1", "h2", "h3", "h4", "strong"])
        title = title_el.get_text(strip=True) if title_el else node.get_text(" ", strip=True)
        if not self._valid_title(title):
            return None
        return RawJob(
            title=title[:120],
            company=self._company,
            location="",
            description=node.get_text(" ", strip=True)[:2000],
            url=base_url,
            source="custom",
        )

    def _anchor_to_job(
        self, anchor, base_url: str, context: str = ""
    ) -> RawJob | None:
        href = anchor.get("href", "").strip()
        if not href or _SKIP_HREF.search(href):
            return None
        title = anchor.get_text(" ", strip=True)
        if not self._valid_title(title):
            if context:
                title = context.split("\n")[0].strip()[:120]
            else:
                return None
        if not self._valid_title(title):
            return None

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc.lower() != self._host:
            return None

        description = context or title
        parent = anchor.find_parent(["li", "article", "div", "section", "tr"])
        if parent:
            block = parent.get_text(" ", strip=True)
            if len(block) > len(title):
                description = block[:2000]

        return RawJob(
            title=title[:120],
            company=self._company,
            location="",
            description=description,
            url=full_url,
            source="custom",
        )

    def _valid_title(self, title: str) -> bool:
        if not title or len(title) < 3 or len(title) > 150:
            return False
        if _NOISE_TITLES.match(title.strip()):
            return False
        return True

    def _clean_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text)
