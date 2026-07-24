"""
Модуль для экспорта новостей в CSV.
"""

import csv
import logging
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_to_csv(articles: List[Dict], csv_path: str):
    """
    Экспортирует статьи в CSV файл.
    
    Args:
        articles (List[Dict]): Список словарей с данными статей.
        csv_path (str): Путь к CSV файлу для экспорта.
    """
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'link', 'summary', 'published', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for article in articles:
                writer.writerow(article)
                
        logger.info(f"Экспортировано {len(articles)} статей в {csv_path}.")
    except Exception as e:
        logger.error(f"Ошибка при экспорте в CSV: {e}")