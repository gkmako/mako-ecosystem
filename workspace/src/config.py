from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import yaml
from pathlib import Path


class SourcesConfig(BaseSettings):
    urls: List[str] = Field(default_factory=list)
    rss_feeds: List[str] = Field(default_factory=list)
    user_agent: str = "ev-news-scraper/0.1.0"
    
    class Config:
        env_prefix = "SOURCES_"


class DatabaseConfig(BaseSettings):
    path: str = "news.db"
    
    class Config:
        env_prefix = "DB_"


class Settings(BaseSettings):
    sources: SourcesConfig = SourcesConfig()
    database: DatabaseConfig = DatabaseConfig()
    collection_interval_minutes: int = 60
    request_timeout: int = 30
    retry_attempts: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    @classmethod
    def from_yaml(cls, path: str = "config.yaml"):
        config_path = Path(path)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return cls(**config)
        return cls()


settings = Settings.from_yaml()