import asyncio
from packages.memory.service import save_memory, search_memory
from packages.memory.models import MemoryType

async def main():
    print("1. Сохраняем воспоминания...")
    await save_memory(
        content="Для проекта маркетплейса мы выбрали PostgreSQL и Redis.", 
        memory_type=MemoryType.SEMANTIC, 
        agent_name="architect_agent"
    )
    await save_memory(
        content="Клиент согласовал смету на 330 000 рублей за 60 часов работы.", 
        memory_type=MemoryType.EPISODIC, 
        agent_name="sales_agent"
    )
    print("Успешно сохранено!")

    print("\n2. Ищем контекст про базу данных...")
    results = await search_memory("Какую базу данных мы выбрали?")
    for r in results:
        print(f"- [{r['type']}] {r['content']}")

if __name__ == "__main__":
    asyncio.run(main())
