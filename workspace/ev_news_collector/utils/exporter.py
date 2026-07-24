# utils/exporter.py - Экспорт новостей в CSV

import csv
import sqlite3
import logging
from config import DATABASE_PATH, CSV_EXPORT_PATH

def export_to_csv():
    """
    Экспортирует все новости из БД в CSV-файл.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT title, link, summary, source, date_added FROM news')
        rows = cursor.fetchall()
        conn.close()

        with open(CSV_EXPORT_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'link', 'summary', 'source', 'date_added']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    'title': row[0],
                    'link': row[1],
                    'summary': row[2],
                    'source': row[3],
                    'date_added': row[4]
                })
        logging.info(f'Новости успешно экспортированы в {CSV_EXPORT_PATH}')
    except Exception as e:
        logging.error(f'Ошибка при экспорте в CSV: {e}')