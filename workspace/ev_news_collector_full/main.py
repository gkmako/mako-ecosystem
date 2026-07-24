"""
Точка входа в приложение. Оркестратор сбора новостей.
"""

import logging
from typing import List
from sources.rss_sources import fetch_rss_articles
from sources.web_scrapers import fetch_web_articles
from sources.google_news import fetch_google_news_articles
from utils.dedup import deduplicate_articles
from storage.database import init_db, save_articles, get_all_articles
from utils.exporter import export_to_csv
from storage.models import NewsArticle
from config import DB_PATH, CSV_EXPORT_PATH
import schedule
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_all_articles() -> List[NewsArticle]:
    """
    Собирает новости со всех источников.
    
    Returns:
        List[NewsArticle]: Список уникальных статей.
    """
    # Сбор статей
    rss_articles = fetch_rss_articles()
    web_articles = fetch_web_articles()
    google_news_articles = fetch_google_news_articles()
    
    # Объединение всех статей
    all_articles = rss_articles + web_articles + google_news_articles
    
    # Дедупликация
    unique_articles = deduplicate_articles(all_articles, DB_PATH)
    
    return unique_articles

def main():
    """
    Основная функция оркестратора.
    """
    # Инициализация базы данных
    init_db(DB_PATH)
    
    # Сбор статей
    articles = collect_all_articles()
    
    # Сохранение в базу данных
    save_articles(articles, DB_PATH)
    
    # Получение всех статей из базы для экспорта
    all_articles = get_all_articles(DB_PATH)
    
    # Экспорт в CSV
    export_to_csv(all_articles, CSV_EXPORT_PATH)
    
    logger.info("Процесс сбора новостей завершен.")

def scheduled_run():
    """
    Функция для запуска по расписанию.
    """
    logger.info("Запуск запланированного сбора новостей...")
    main()

if __name__ == "__main__":
    # Для однократного запуска
    # main()
    
    # Для запуска по расписанию (раз в час)
    schedule.every().hour.do(scheduled_run)
    
    logger.info("Сборщик новостей запущен. Ожидание запланированных задач...")
    
    while True:
        schedule.run_pending()
        time.sleep(1)