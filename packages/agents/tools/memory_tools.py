# packages/agents/tools/memory_tools.py
from pydantic import BaseModel, Field

class SearchMemorySchema(BaseModel):
    query: str = Field(..., description="Поисковый запрос для поиска в долговременной памяти проекта")

class SaveMemorySchema(BaseModel):
    content: str = Field(..., description="Важный факт, архитектурное решение или контекст для сохранения")

async def search_memory(query: str) -> str:
    """Заглушка для поиска в памяти (позже подключим к pgvector)."""
    return f"Поиск в памяти по запросу '{query}': Релевантных исторических данных пока не найдено."

async def save_to_memory(content: str) -> str:
    """Заглушка для сохранения в память."""
    print(f"[Memory] Сохранено: {content[:100]}...")
    return "Информация успешно сохранена в долговременную память проекта."