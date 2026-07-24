from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from packages.shared.config import settings

# Движок для БД memory (использует pgvector)
memory_engine = create_async_engine(settings.memory_db_url, echo=False)
memory_async_session = async_sessionmaker(memory_engine, expire_on_commit=False)
