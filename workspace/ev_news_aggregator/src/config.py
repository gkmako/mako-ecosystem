from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import os


class Settings(BaseSettings):
    # Новостные источники
    NEWS_SOURCES: List[Dict[str, Any]] = [
        # RSS-ленты
        {"name": "Автостат", "url": "https://www.autostat.ru/rss/", "type": "rss", "enabled": True},
        {"name": "За рулем", "url": "https://www.zr.ru/rss/", "type": "rss", "enabled": True},
        {"name": "Авторевю", "url": "https://www.autoreview.ru/rss/", "type": "rss", "enabled": True},
        {"name": "Дром", "url": "https://feedpress.me/drom", "type": "rss", "enabled": True},
        {"name": "Motor.ru", "url": "https://motor.ru/rss/", "type": "rss", "enabled": True},
        {"name": "ТАСС", "url": "https://tass.ru/rss/v2.xml", "type": "rss", "enabled": True},
        {"name": "РБК Авто", "url": "https:// rssexport.rbc.ru/rbcnews/auto/20", "type": "rss", "enabled": True},
        {"name": "Коммерсантъ Авто", "url": "https://www.kommersant.ru/RSS/auto.xml", "type": "rss", "enabled": True},
        
        # Дополнительные источники
        # {"name": "Google News", "url": "https://news.google.com/rss/search?q=электромобили+Россия", "type": "rss", "enabled": False},
    ]
    
    # Ключевые слова для фильтрации
    KEYWORDS: List[str] = [
        "электромобиль", 
        "электрокар", 
        "EV", 
        "зарядная станция", 
        "ЭЗС", 
        "батарея", 
        "аккумулятор",
        "электротяга", 
        "Tesla Россия", 
        "Zeekr", 
        "Li Auto", 
        "Avatr", 
        "BYD Россия",
        "электромобили",
        "электромобиля",
        "электромобилем",
        "электромобилям",
        "электромобилями",
        "электромобилях",
        "зарядные станции",
        "инфраструктура",
        "электроавтомобиль"
    ]
    
    # Пути к файлам
    CSV_FILE_PATH: str = "data/news.csv"
    JSON_FILE_PATH: str = "data/news.json"
    SQLITE_DB_PATH: str = "data/news.db"
    LOG_FILE_PATH: str = "logs/news_aggregator.log"
    
    # Настройки HTTP-запросов
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 1.0  # Задержка между запросами в секундах
    
    # Настройки планировщика
    SCHEDULER_INTERVAL_HOURS: int = 24  # Ежедневно
    
    # Настройки Telegram (опционально)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()