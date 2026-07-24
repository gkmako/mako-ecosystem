import schedule
import time
import logging
from typing import Callable

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_scheduler(job_func: Callable, interval_minutes: int):
    schedule.every(interval_minutes).minutes.do(job_func)
    logger.info(f"Планировщик запущен. Задача будет выполняться каждые {interval_minutes} минут.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)