from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from packages.shared.config import settings
from .base import Base

# URL для БД router
_base_url = f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.ROUTER_DB}"

# Асинхронный движок (для работы API и агентов)
router_engine = create_async_engine(f"postgresql+asyncpg://{_base_url}", echo=False)
router_async_session = async_sessionmaker(router_engine, expire_on_commit=False)

# Синхронный движок (требуется для SQLAdmin)
sync_engine = create_engine(f"postgresql+psycopg2://{_base_url}")
