import sqlite3
import logging
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deduplicate_articles(articles: List[Dict], db_path: str) -> List[Dict]:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создание таблицы, если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,
                summary TEXT,
                published TEXT
            )
        ''')
        conn.commit()
        
        unique_articles = []
        for article in articles:
            try:
                cursor.execute('''
                    INSERT INTO articles (title, link, summary, published)
                    VALUES (?, ?, ?, ?)
                ''', (article['title'], article['link'], article['summary'], article['published']))
                conn.commit()
                unique_articles.append(article)
            except sqlite3.IntegrityError:
                # Дубликат по URL, пропускаем
                pass
                
        conn.close()
        logger.info(f"Уникальных статей после дедупликации: {len(unique_articles)}")
        return unique_articles
    except Exception as e:
        logger.error(f"Ошибка при дедупликации: {e}")
        return []