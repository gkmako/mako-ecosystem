# main.py - Главный файл сборщика новостей

import logging
import schedule
import time
from sources.rss_sources import fetch_rss_news
from sources.google_news import fetch_google_news
from sources.web_scrapers import fetch_web_news
from storage.database import init_db, save_news_to_db
from utils.dedup import filter_duplicates
from utils.exporter import export_to_csv
from config import DATABASE_PATH, CSV_EXPORT_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_collector.log'),
        logging.StreamHandler()
    ]
)

def collect_all_news():
    """
    Собирает новости со всех источников.
    """
    logging.info('Начало сбора новостей...')
    all_news = []
    
    # Сбор через RSS
    rss_news = fetch_rss_news()
    all_news.extend(rss_news)
    logging.info(f'Собрано {len(rss_news)} новостей через RSS.')
    
    # Сбор через Google News
    google_news = fetch_google_news()
    all_news.extend(google_news)
    logging.info(f'Собрано {len(google_news)} новостей через Google News.')
    
    # Сбор через веб-скрапинг
    web_news = fetch_web_news()
    all_news.extend(web_news)
    logging.info(f'Собрано {len(web_news)} новостей через веб-скрапинг.')
    
    # Фильтрация дубликатов
    unique_news = filter_duplicates(all_news)
    logging.info(f'После фильтрации дубликатов осталось {len(unique_news)} новостей.')
    
    if unique_news:
        # Сохранение в БД
        save_news_to_db(unique_news)
        # Экспорт в CSV
        export_to_csv()
    else:
        logging.info('Нет новых уникальных новостей для сохранения.')
    
    logging.info('Сбор новостей завершен.')

def run_scheduler():
    """
    Запускает планировщик на выполнение задачи каждые 2 часа.
    """
    schedule.every(2).hours.do(collect_all_news)
    logging.info('Планировщик запущен. Сбор новостей будет выполняться каждые 2 часа.')
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == '__main__':
    # Инициализация БД
    init_db()
    # Первый запуск сбора новостей
    collect_all_news()
    # Запуск планировщика
    run_scheduler()