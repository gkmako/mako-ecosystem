from .base import BaseScraper, NewsItem
from typing import List
from httpx import AsyncClient
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime


class AutostatScraper(BaseScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.source = "autostat.ru"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape(self) -> List[NewsItem]:
        articles = []
        try:
            async with AsyncClient() as client:
                response = await client.get(f"{self.base_url}/news/")
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Пример парсинга (необходимо адаптировать под реальную структуру сайта)
                for item in soup.find_all('div', class_='news-item')[:10]:  # Ограничим 10 новостями
                    title_tag = item.find('a', class_='news-title')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href')
                    if not url.startswith('http'):
                        url = f"{self.base_url}{url}"
                    
                    snippet_tag = item.find('div', class_='news-snippet')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    
                    # Дата публикации (пример, адаптировать под реальную разметку)
                    date_tag = item.find('span', class_='news-date')
                    published_at_str = date_tag.get_text(strip=True) if date_tag else ""
                    try:
                        published_at = datetime.strptime(published_at_str, "%d.%m.%Y")
                    except ValueError:
                        published_at = datetime.utcnow()
                    
                    articles.append(NewsItem(
                        title=title,
                        url=url,
                        published_at=published_at,
                        snippet=snippet,
                        source=self.source
                    ))
                    
            logger.info(f"Autostat: собрано {len(articles)} новостей")
        except Exception as e:
            logger.error(f"Ошибка при сборе новостей с Autostat: {e}")
            
        return articles