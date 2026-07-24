# sources/rss_sources.py - Сбор новостей через RSS

import feedparser
import logging
from config import RSS_SOURCES, KEYWORDS

def fetch_rss_news():
    """
    Собирает новости из RSS-лент.
    Возвращает список словарей с новостями.
    """
    news_list = []
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '')
                # Проверяем наличие ключевых слов
                if any(keyword.lower() in (title + summary).lower() for keyword in KEYWORDS):
                    news_item = {
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'source': url
                    }
                    news_list.append(news_item)
        except Exception as e:
            logging.error(f'Ошибка при парсинге RSS {url}: {e}')
    return news_list