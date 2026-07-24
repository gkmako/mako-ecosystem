import csv
import json
import sqlite3
from typing import List, Dict
from pathlib import Path
from loguru import logger
import pandas as pd


def save_to_csv(news_data: List[Dict], file_path: str):
    """
    Сохраняет данные в CSV файл.
    
    Args:
        news_data (List[Dict]): Список новостей
        file_path (str): Путь к файлу
    """
    try:
        # Создать директорию, если она не существует
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            if news_data:
                writer = csv.DictWriter(file, fieldnames=news_data[0].keys())
                writer.writeheader()
                writer.writerows(news_data)
            else:
                # Создать пустой файл с заголовками
                writer = csv.writer(file)
                writer.writerow(["date", "source", "title", "link", "summary"])
                
        logger.info(f"Данные успешно сохранены в {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в CSV: {e}")


def save_to_json(news_data: List[Dict], file_path: str):
    """
    Сохраняет данные в JSON файл.
    
    Args:
        news_data (List[Dict]): Список новостей
        file_path (str): Путь к файлу
    """
    try:
        # Создать директорию, если она не существует
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, mode='w', encoding='utf-8') as file:
            json.dump(news_data, file, ensure_ascii=False, indent=2)
            
        logger.info(f"Данные успешно сохранены в {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в JSON: {e}")


def save_to_sqlite(news_data: List[Dict], db_path: str):
    """
    Сохраняет данные в SQLite базу данных.
    
    Args:
        news_data (List[Dict]): Список новостей
        db_path (str): Путь к базе данных
    """
    try:
        # Создать директорию, если она не существует
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Подключение к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создание таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                source TEXT,
                title TEXT,
                link TEXT UNIQUE,
                summary TEXT
            )
        ''')
        
        # Вставка данных
        for item in news_data:
            cursor.execute('''
                INSERT OR IGNORE INTO news (date, source, title, link, summary)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item.get('date', ''),
                item.get('source', ''),
                item.get('title', ''),
                item.get('link', ''),
                item.get('summary', '')
            ))
        
        # Сохранение изменений
        conn.commit()
        conn.close()
        
        logger.info(f"Данные успешно сохранены в SQLite: {db_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в SQLite: {e}")


def export_to_csv_from_sqlite(db_path: str, csv_path: str):
    """
    Экспортирует данные из SQLite в CSV файл.
    
    Args:
        db_path (str): Путь к базе данных
        csv_path (str): Путь к CSV файлу
    """
    try:
        # Создать директорию, если она не существует
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Подключение к базе данных
        conn = sqlite3.connect(db_path)
        
        # Чтение данных в DataFrame
        df = pd.read_sql_query("SELECT * FROM news ORDER BY date DESC", conn)
        
        # Сохранение в CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        conn.close()
        
        logger.info(f"Данные успешно экспортированы в {csv_path}")
    except Exception as e:
        logger.error(f"Ошибка при экспорте из SQLite в CSV: {e}")


def get_news_history(db_path: str, limit: int = 100) -> List[Dict]:
    """
    Получает историю новостей из базы данных.
    
    Args:
        db_path (str): Путь к базе данных
        limit (int): Максимальное количество записей
        
    Returns:
        List[Dict]: Список новостей
    """
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получение данных
        cursor.execute('''
            SELECT date, source, title, link, summary
            FROM news
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Преобразование в список словарей
        news_list = []
        for row in rows:
            news_list.append({
                'date': row[0],
                'source': row[1],
                'title': row[2],
                'link': row[3],
                'summary': row[4]
            })
            
        return news_list
    except Exception as e:
        logger.error(f"Ошибка при получении истории новостей: {e}")
        return []