import sqlite3
import csv
import json
import logging
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_to_sqlite(articles: List[Dict], db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,
                summary TEXT,
                published TEXT
            )
        ''')
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT INTO articles (title, link, summary, published)
                    VALUES (?, ?, ?, ?)
                ''', (article['title'], article['link'], article['summary'], article['published']))
            except sqlite3.IntegrityError:
                # Пропуск дубликатов
                pass
                
        conn.commit()
        conn.close()
        logger.info(f"Сохранено {len(articles)} статей в SQLite.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в SQLite: {e}")

def export_to_csv(articles: List[Dict], csv_path: str):
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'link', 'summary', 'published']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)
        logger.info(f"Экспортировано {len(articles)} статей в CSV.")
    except Exception as e:
        logger.error(f"Ошибка при экспорте в CSV: {e}")

def export_to_json(articles: List[Dict], json_path: str):
    try:
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(articles, jsonfile, ensure_ascii=False, indent=4)
        logger.info(f"Экспортировано {len(articles)} статей в JSON.")
    except Exception as e:
        logger.error(f"Ошибка при экспорте в JSON: {e}")