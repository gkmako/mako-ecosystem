from pydantic_settings import BaseSettings
from typing import List, Optional
import yaml
from pathlib import Path


class SourceConfig(BaseSettings):
    url: str
    enabled: bool = True


class RSSConfig(BaseSettings):
    urls: List[str]
    enabled: bool = True


class DatabaseConfig(BaseSettings):
    path: str = "news.db"


class SchedulerConfig(BaseSettings):
    interval_minutes: int = 60


class Settings(BaseSettings):
    autostat: SourceConfig
    drom: SourceConfig
    auto_ru: SourceConfig
    minpromtorg: SourceConfig
    rss: RSSConfig
    database: DatabaseConfig
    scheduler: SchedulerConfig

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    @classmethod
    def from_yaml(cls, path: str = "config.yaml"):
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return cls(**config)


settings = Settings.from_yaml()