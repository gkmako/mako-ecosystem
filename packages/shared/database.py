from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from packages.shared.config import settings

# Создаем асинхронный движок для БД memory
engine = create_async_engine(settings.memory_db_url, echo=False, pool_pre_ping=True)

# Фабрика сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)
