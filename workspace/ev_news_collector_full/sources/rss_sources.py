"""
Модуль для сбора новостей через RSS-ленты.
"""

import feedparser
import logging
from typing import List, Dict
from config import RSS_SOURCES, KEYWORDS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_rss_articles() -> List[Dict]:
    """
    Собирает новости из RSS-лент.
    
    Returns:
        List[Dict]: Список словарей с данными статей.
    """
    articles = []
    
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Проверка на наличие ключевых слов
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                content = (title + ' ' + summary).lower()
                
                if any(keyword.lower() in content for keyword in KEYWORDS):
                    articles.append({
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'source': 'rss'
                    })
        except Exception as e:
            logger.error(f"Ошибка при парсинге RSS {url}: {e}")
    
    logger.info(f"Собрано {len(articles)} статей из RSS.")
    return articles