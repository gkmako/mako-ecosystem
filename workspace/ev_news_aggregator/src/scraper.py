import asyncio
import httpx
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
import hashlib
from .config import settings
from .utils import filter_by_keywords, clean_text, get_current_time


class NewsScraper:
    def __init__(self):
        self.keywords = settings.KEYWORDS
        self.request_timeout = settings.REQUEST_TIMEOUT
        self.request_delay = settings.REQUEST_DELAY
        self.seen_hashes = set()  # Для дедупликации
        
    def _generate_hash(self, title: str, url: str) -> str:
        """Генерирует хеш для дедупликации новостей."""
        combined = f"{title.lower().strip()}|{url}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
        
    def is_duplicate(self, title: str, url: str) -> bool:
        """Проверяет, является ли новость дубликатом."""
        hash_value = self._generate_hash(title, url)
        if hash_value in self.seen_hashes:
            return True
        self.seen_hashes.add(hash_value)
        return False
        
    def extract_summary(self, content: str, max_length: int = 300) -> str:
        """Извлекает краткое содержание из текста."""
        if not content:
            return ""
            
        # Очистка от HTML тегов
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        text = clean_text(text)
        
        # Обрезка до максимальной длины
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
        
    async def fetch_web_content(self, url: str, source_name: str) -> List[Dict]:
        """
        Асинхронно получает содержимое веб-страницы.
        
        Args:
            url (str): URL страницы
            source_name (str): Название источника
            
        Returns:
            List[Dict]: Список новостей
        """
        news_list = []
        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Поиск заголовков (адаптировать селекторы под конкретные сайты)
                headlines = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                
                for headline in headlines:
                    title = clean_text(headline.get_text())
                    link = headline.find_parent('a')
                    link_url = link.get('href') if link else ''
                    
                    # Преобразование относительных ссылок в абсолютные
                    if link_url and not link_url.startswith('http'):
                        link_url = urljoin(url, link_url)
                    
                    # Фильтрация по ключевым словам и дедупликация
                    if filter_by_keywords(title, self.keywords) and not self.is_duplicate(title, link_url):
                        # Извлечение краткого содержания
                        summary = ""
                        parent = headline.parent
                        if parent:
                            summary = self.extract_summary(str(parent), 200)
                        
                        news_list.append({
                            "date": get_current_time(),
                            "source": source_name,
                            "title": title,
                            "link": link_url,
                            "summary": summary
                        })
                        
                logger.info(f"С сайта {source_name} получено {len(news_list)} новостей")
        except Exception as e:
            logger.error(f"Ошибка при получении данных с {source_name}: {e}")
            
        # Задержка между запросами
        await asyncio.sleep(self.request_delay)
        return news_list
        
    def fetch_rss_content(self, url: str, source_name: str) -> List[Dict]:
        """
        Получает содержимое RSS-ленты.
        
        Args:
            url (str): URL RSS-ленты
            source_name (str): Название источника
            
        Returns:
            List[Dict]: Список новостей
        """
        news_list = []
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                title = clean_text(entry.title)
                link = entry.link
                published = entry.get('published', '')
                summary = entry.get('summary', '')
                
                # Преобразование даты
                try:
                    pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pub_date = get_current_time()
                
                # Фильтрация по ключевым словам и дедупликация
                if filter_by_keywords(title, self.keywords) and not self.is_duplicate(title, link):
                    # Извлечение краткого содержания
                    clean_summary = self.extract_summary(summary, 200)
                    
                    news_list.append({
                        "date": pub_date,
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "summary": clean_summary
                    })
                    
            logger.info(f"Из RSS {source_name} получено {len(news_list)} новостей")
        except Exception as e:
            logger.error(f"Ошибка при получении данных из RSS {source_name}: {e}")
            
        return news_list
        
    def fetch_google_news(self, query: str, source_name: str = "Google News") -> List[Dict]:
        """
        Получает новости через Google News RSS.
        
        Args:
            query (str): Поисковый запрос
            source_name (str): Название источника
            
        Returns:
            List[Dict]: Список новостей
        """
        news_list = []
        try:
            # Кодирование запроса для URL
            encoded_query = quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ru&gl=RU&ceid=RU:ru"
            
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                title = clean_text(entry.title)
                link = entry.link
                published = entry.get('published', '')
                summary = entry.get('summary', '')
                
                # Преобразование даты
                try:
                    pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pub_date = get_current_time()
                
                # Фильтрация по ключевым словам и дедупликация
                if filter_by_keywords(title, self.keywords) and not self.is_duplicate(title, link):
                    # Извлечение краткого содержания
                    clean_summary = self.extract_summary(summary, 200)
                    
                    news_list.append({
                        "date": pub_date,
                        "source": f"{source_name} ({query})",
                        "title": title,
                        "link": link,
                        "summary": clean_summary
                    })
                    
            logger.info(f"Из Google News по запросу '{query}' получено {len(news_list)} новостей")
        except Exception as e:
            logger.error(f"Ошибка при получении данных из Google News по запросу '{query}': {e}")
            
        return news_list
        
    async def scrape_all_sources(self) -> List[Dict]:
        """
        Собирает новости со всех источников.
        
        Returns:
            List[Dict]: Список всех новостей
        """
        all_news = []
        tasks = []
        
        # Сбор из RSS-лент
        for source in settings.NEWS_SOURCES:
            if not source.get('enabled', True):
                continue
                
            source_type = source.get('type', 'web')
            source_name = source.get('name', 'Unknown')
            source_url = source.get('url', '')
            
            if not source_url:
                logger.warning(f"Пропущен источник {source_name} - отсутствует URL")
                continue
                
            if source_type == 'web':
                task = self.fetch_web_content(source_url, source_name)
                tasks.append(task)
            elif source_type == 'rss':
                # RSS обрабатывается синхронно
                rss_news = self.fetch_rss_content(source_url, source_name)
                all_news.extend(rss_news)
                
        # Сбор из Google News по ключевым запросам
        google_queries = [
            "электромобили Россия",
            "рынок электромобилей РФ",
            "зарядные станции Россия",
            "электрокар"
        ]
        
        for query in google_queries:
            google_news = self.fetch_google_news(query)
            all_news.extend(google_news)
                
        # Асинхронное выполнение веб-запросов
        if tasks:
            web_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in web_results:
                if isinstance(result, Exception):
                    logger.error(f"Ошибка при асинхронном запросе: {result}")
                else:
                    all_news.extend(result)
                    
        logger.info(f"Всего собрано {len(all_news)} новостей")
        return all_news