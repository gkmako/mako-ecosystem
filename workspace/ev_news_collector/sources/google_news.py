# sources/google_news.py - Сбор новостей через Google News RSS

import feedparser
import logging
from config import GOOGLE_NEWS_URL, KEYWORDS

def fetch_google_news():
    """
    Собирает новости из Google News по теме электромобилей.
    Возвращает список словарей с новостями.
    """
    news_list = []
    try:
        feed = feedparser.parse(GOOGLE_NEWS_URL)
        for entry in feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            # Проверяем наличие ключевых слов
            if any(keyword.lower() in (title + summary).lower() for keyword in KEYWORDS):
                # Извлекаем реальную ссылку из Google News
                real_link = entry.get('link', '')
                if 'google.com' in real_link:
                    # Google News иногда прячет реальную ссылку
                    # В этом случае можно использовать guid или ссылку на источник
                    real_link = entry.get('source', {}).get('href', real_link)
                news_item = {
                    'title': title,
                    'link': real_link,
                    'summary': summary,
                    'source': 'Google News'
                }
                news_list.append(news_item)
    except Exception as e:
        logging.error(f'Ошибка при парсинге Google News: {e}')
    return news_list