from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    POSTGRES_USER: str = "mako"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    ROUTER_DB: str = "router"
    MEMORY_DB: str = "memory"

    # LLM Proxy (routerai.ru)
    LLM_API_BASE: str = "https://routerai.ru/api/v1"
    LLM_API_KEY: str = ""

    # Models
    ROUTERAI_ROUTER_MODEL: str = "google/gemini-3.5-flash-lite"     # 817ms, классификация контура
    ROUTERAI_FAST_MODEL: str = "google/gemini-3.5-flash-lite"       # 804ms, выбор агента в контуре
    ROUTERAI_SMART_MODEL: str = "openai/gpt-5.6-luna-pro"           # 9.8s, reasoning (architect/orchestrator)
    ROUTERAI_CODER_MODEL: str = "qwen/qwen3-coder-next"             # 5.5s, написание кода
    ROUTERAI_REVIEWER_MODEL: str = "meta/muse-spark-1.1"            # 2.4s, fallback для reviewer
    ROUTERAI_EMBEDDING_MODEL: str = "openai/text-embedding-3-small" # без изменений

    # RAGFlow
    RAGFLOW_API_BASE: str = "http://ragflow:9380/api/v1"
    RAGFLOW_API_KEY: str = ""

    # Voice
    STT_MODEL: str = "qwen/qwen3-asr-flash-2026-02-10"
    TTS_MODEL: str = "x-ai/grok-voice-tts-1.0"

    # Tavily
    TAVILY_API_KEY: str = ""

    # --- Properties ---
    @property
    def memory_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.MEMORY_DB}"

    @property
    def router_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.ROUTER_DB}"

    @property
    def router_db_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.ROUTER_DB}"

    @property
    def database_url(self) -> str:
        return self.router_db_url

    @property
    def sync_database_url(self) -> str:
        return self.router_db_url_sync


settings = Settings()
