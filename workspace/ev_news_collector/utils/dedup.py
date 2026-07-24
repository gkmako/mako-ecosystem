# utils/dedup.py - Функции для дедупликации новостей

import sqlite3
from config import DATABASE_PATH

def is_duplicate(link):
    """
    Проверяет, существует ли новость с такой ссылкой в БД.
    Возвращает True, если дубликат найден.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM news WHERE link = ?', (link,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        # В случае ошибки БД считаем, что это не дубликат
        return False

def filter_duplicates(news_list):
    """
    Фильтрует дубликаты из списка новостей.
    """
    unique_news = []
    for item in news_list:
        if not is_duplicate(item['link']):
            unique_news.append(item)
    return unique_news