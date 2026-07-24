import asyncio
from packages.memory.database import memory_engine
from packages.memory.models import Base as MemoryBase

async def main():
    try:
        async with memory_engine.begin() as conn:
            # Принудительно удаляем и создаем заново
            await conn.run_sync(MemoryBase.metadata.drop_all)
            await conn.run_sync(MemoryBase.metadata.create_all)
        print("✅ Таблицы успешно созданы!")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")

asyncio.run(main())
