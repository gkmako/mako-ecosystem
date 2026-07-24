import asyncio
import aiohttp
import feedparser
import logging
from typing import List, Dict
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_rss(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"Ошибка при получении RSS с {url}: {e}")
        return ""

async def parse_feed(feed_content: str, keywords: List[str]) -> List[Dict]:
    try:
        feed = feedparser.parse(feed_content)
        articles = []
        for entry in feed.entries:
            # Проверка на наличие ключевых слов
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            content = (title + ' ' + summary).lower()
            
            if any(keyword.lower() in content for keyword in keywords):
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                })
        return articles
    except Exception as e:
        logger.error(f"Ошибка при парсинге фида: {e}")
        return []

async def collect_news(config_path: str = 'config.yaml') -> List[Dict]:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sources = config.get('sources', [])
    keywords = config.get('keywords', [])
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rss(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
        
        articles = []
        for result in results:
            if result:
                parsed_articles = await parse_feed(result, keywords)
                articles.extend(parsed_articles)
                
    logger.info(f"Собрано {len(articles)} статей.")
    return articles