"""
Модуль для сбора новостей через Google News RSS.
"""

import feedparser
import logging
from typing import List, Dict
from config import GOOGLE_NEWS_RSS, KEYWORDS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_google_news_articles() -> List[Dict]:
    """
    Собирает новости из Google News RSS.
    
    Returns:
        List[Dict]: Список словарей с данными статей.
    """
    articles = []
    
    try:
        feed = feedparser.parse(GOOGLE_NEWS_RSS)
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
                    'source': 'google_news'
                })
    except Exception as e:
        logger.error(f"Ошибка при парсинге Google News RSS: {e}")
    
    logger.info(f"Собрано {len(articles)} статей из Google News.")
    return articles