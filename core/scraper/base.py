from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawJob:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    job_type: str = ""


class BaseScraper(ABC):
    @abstractmethod
    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        pass
