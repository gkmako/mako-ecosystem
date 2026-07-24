"""
Модуль для работы с SQLite базой данных.
"""

import sqlite3
import logging
from typing import List, Dict
from storage.models import NewsArticle

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db_path: str):
    """
    Инициализирует базу данных, создавая таблицу статей если её нет.
    
    Args:
        db_path (str): Путь к файлу базы данных.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,
                summary TEXT,
                published TEXT,
                source TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")

def save_articles(articles: List[NewsArticle], db_path: str):
    """
    Сохраняет статьи в базу данных.
    
    Args:
        articles (List[NewsArticle]): Список статей для сохранения.
        db_path (str): Путь к файлу базы данных.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT INTO articles (title, link, summary, published, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (article.title, article.link, article.summary, article.published, article.source))
            except sqlite3.IntegrityError:
                # Пропуск дубликатов
                pass
                
        conn.commit()
        conn.close()
        logger.info(f"Сохранено {len(articles)} статей в базу данных.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении статей в базу данных: {e}")

def get_all_articles(db_path: str) -> List[Dict]:
    """
    Получает все статьи из базы данных.
    
    Args:
        db_path (str): Путь к файлу базы данных.
        
    Returns:
        List[Dict]: Список словарей с данными статей.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT title, link, summary, published, source FROM articles')
        rows = cursor.fetchall()
        
        conn.close()
        
        # Преобразование в список словарей
        articles = [
            {
                'title': row[0],
                'link': row[1],
                'summary': row[2],
                'published': row[3],
                'source': row[4]
            }
            for row in rows
        ]
        
        logger.info(f"Получено {len(articles)} статей из базы данных.")
        return articles
    except Exception as e:
        logger.error(f"Ошибка при получении статей из базы данных: {e}")
        return []