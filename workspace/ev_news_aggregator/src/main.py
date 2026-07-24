import asyncio
import argparse
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from .config import settings
from .scraper import NewsScraper
from .storage import save_to_csv, save_to_json, save_to_sqlite
from .utils import setup_logger, get_current_time
from .telegram_notifier import TelegramNotifier


def setup_directories():
    """Создает необходимые директории."""
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)


async def run_aggregator(send_telegram: bool = False):
    """Основная функция запуска агрегатора."""
    logger.info("Запуск агрегатора новостей по тематике электромобилей в РФ")
    
    # Инициализация скрапера
    scraper = NewsScraper()
    
    # Асинхронный сбор новостей
    news_data = await scraper.scrape_all_sources()
    
    # Сохранение данных
    if news_data:
        save_to_csv(news_data, settings.CSV_FILE_PATH)
        save_to_json(news_data, settings.JSON_FILE_PATH)
        save_to_sqlite(news_data, settings.SQLITE_DB_PATH)
        logger.info(f"Собрано и сохранено {len(news_data)} новостей")
        
        # Отправка в Telegram, если настроено
        if send_telegram and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            telegram = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
            await telegram.send_news_digest(news_data[:5], "Новые новости по электромобилям в РФ")
    else:
        logger.info("Новых новостей не найдено")
        # Создать пустые файлы
        save_to_csv([], settings.CSV_FILE_PATH)
        save_to_json([], settings.JSON_FILE_PATH)
        save_to_sqlite([], settings.SQLITE_DB_PATH)


def main():
    """Точка входа в приложение."""
    # Настройка директорий
    setup_directories()
    
    # Настройка логгера
    setup_logger(settings.LOG_FILE_PATH)
    
    # Парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Агрегатор новостей по тематике электромобилей в РФ')
    parser.add_argument('--schedule', action='store_true', help='Запустить с планировщиком')
    parser.add_argument('--telegram', action='store_true', help='Отправить уведомление в Telegram')
    args = parser.parse_args()
    
    if args.schedule:
        # Запуск с планировщиком
        logger.info("Запуск с планировщиком задач")
        scheduler = BlockingScheduler()
        
        async def scheduled_run():
            await run_aggregator(args.telegram)
        
        scheduler.add_job(lambda: asyncio.run(scheduled_run()), 'interval', hours=settings.SCHEDULER_INTERVAL_HOURS)
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Планировщик остановлен пользователем")
    else:
        # Однократный запуск
        asyncio.run(run_aggregator(args.telegram))


if __name__ == "__main__":
    main()