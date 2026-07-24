"""
Модуль для дедупликации новостей.
"""

import sqlite3
import logging
from typing import List, Dict
from storage.models import NewsArticle

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deduplicate_articles(articles: List[Dict], db_path: str) -> List[NewsArticle]:
    """
    Удаляет дубликаты новостей по URL и заголовку.
    
    Args:
        articles (List[Dict]): Список словарей с данными статей.
        db_path (str): Путь к файлу базы данных.
        
    Returns:
        List[NewsArticle]: Список уникальных статей.
    """
    try:
        # Подключение к базе данных для проверки существующих статей
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        unique_articles = []
        for article_dict in articles:
            # Создание объекта статьи
            article = NewsArticle(
                title=article_dict['title'],
                link=article_dict['link'],
                summary=article_dict['summary'],
                published=article_dict['published'],
                source=article_dict['source']
            )
            
            # Проверка на дубликаты в базе данных
            cursor.execute('SELECT 1 FROM articles WHERE link = ? OR title = ?', 
                          (article.link, article.title))
            if not cursor.fetchone():
                unique_articles.append(article)
                
        conn.close()
        logger.info(f"Уникальных статей после дедупликации: {len(unique_articles)}")
        return unique_articles
    except Exception as e:
        logger.error(f"Ошибка при дедупликации: {e}")
        return []