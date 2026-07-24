# storage/database.py - Работа с базой данных SQLite

import sqlite3
import logging
from config import DATABASE_PATH

def init_db():
    """
    Инициализирует базу данных и создает таблицу новостей, если она не существует.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                summary TEXT,
                source TEXT NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f'Ошибка при инициализации БД: {e}')

def save_news_to_db(news_list):
    """
    Сохраняет список новостей в базу данных.
    news_list: список словарей с новостями.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        inserted_count = 0
        for item in news_list:
            try:
                cursor.execute('''
                    INSERT INTO news (title, link, summary, source)
                    VALUES (?, ?, ?, ?)
                ''', (item['title'], item['link'], item['summary'], item['source']))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Пропускаем дубликаты по ссылке
                pass
        conn.commit()
        conn.close()
        logging.info(f'Успешно сохранено {inserted_count} новостей в БД.')
    except Exception as e:
        logging.error(f'Ошибка при сохранении новостей в БД: {e}')