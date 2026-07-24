from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from datetime import datetime


class NewsItem(BaseModel):
    title: str
    url: str
    published_at: datetime
    snippet: str
    source: str


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self) -> List[NewsItem]:
        pass