from core.scraper.base import BaseScraper
from core.scraper.custom import CustomSiteScraper
from core.scraper.indeed import IndeedScraper
from core.scraper.internet_bing import BingInternetSearchScraper
from core.scraper.linkedin import LinkedInScraper
from core.scraper.remotive import RemotiveScraper
from core.scraper.wwr import WWRScraper
from core.scraper.ziprecruiter import ZipRecruiterScraper

SCRAPERS = {
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "remotive": RemotiveScraper,
    "wwr": WWRScraper,
    "ziprecruiter": ZipRecruiterScraper,
    "bing": BingInternetSearchScraper,
}



def get_custom_scraper(base_url: str) -> CustomSiteScraper:
    return CustomSiteScraper(base_url)


def get_scraper(source: str) -> BaseScraper:
    key = source.lower().replace(" ", "")
    aliases = {
        "weworkremotely": "wwr",
        "weworkremotely.com": "wwr",
    }
    key = aliases.get(key, key)
    if key not in SCRAPERS:
        raise ValueError(f"Unknown job source: {source}")
    return SCRAPERS[key]()
