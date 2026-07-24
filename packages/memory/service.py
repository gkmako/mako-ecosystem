from sqlalchemy import select
from packages.memory.database import memory_async_session
from packages.memory.models import Memory, MemoryType
from packages.shared.llm import llm_client
from packages.shared.config import settings

async def get_embedding(text: str) -> list[float]:
    """Получает векторное представление текста через API RouterAI."""
    response = await llm_client.embeddings.create(
        model=settings.ROUTERAI_EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

async def save_memory(content: str, memory_type: MemoryType, agent_name: str, metadata: dict = None) -> int:
    """Сохраняет новое воспоминание в базу."""
    embedding = await get_embedding(content)
    async with memory_async_session() as session:
        mem = Memory(
            content=content,
            memory_type=memory_type,
            embedding=embedding,
            agent_name=agent_name,
            metadata_=metadata or {}
        )
        session.add(mem)
        await session.commit()
        return mem.id

async def search_memory(query: str, memory_type: MemoryType = None, limit: int = 5) -> list[dict]:
    """Ищет самые релевантные воспоминания по косинусному расстоянию."""
    query_embedding = await get_embedding(query)
    
    async with memory_async_session() as session:
        # Используем встроенный метод Vector для расчета расстояния
        stmt = select(Memory).order_by(Memory.embedding.cosine_distance(query_embedding)).limit(limit)
        
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
            
        result = await session.execute(stmt)
        memories = result.scalars().all()
        
    return [
        {
            "id": m.id,
            "content": m.content,
            "type": m.memory_type.value,
            "agent": m.agent_name,
            "metadata": m.metadata_
        } 
        for m in memories
    ]

async def auto_save_episode(prompt: str, agent_name: str, response: str):
    """Автоматически создает краткое резюме выполненной задачи и сохраняет его как эпизод."""
    try:
        # 1. Просим LLM сделать краткую выжимку (чтобы экономить токены и место в БД)
        summary_prompt = (
            f"Кратко (в 1-2 предложениях) резюмируй суть задачи и итоговый результат на русском языке. "
            f"Не пиши код, только факты.\n"
            f"Задача: {prompt}\n"
            f"Результат: {response[:1000]}" # Обрезаем, чтобы не превысить лимиты
        )
        
        summary_response = await llm_client.chat.completions.create(
            model="openai/gpt-4o-mini", # Используем быструю и дешевую модель для саммари
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2
        )
        summary_text = summary_response.choices[0].message.content.strip()
        
        # 2. Сохраняем в эпизодическую память
        await save_memory(
            content=summary_text,
            memory_type=MemoryType.EPISODIC,
            agent_name=agent_name,
            metadata={"original_prompt": prompt[:200]}
        )
    except Exception as e:
        # Фоновая задача не должна ломать основной поток, просто логируем (в продакшене тут будет logger)
        print(f"[Memory Auto-Save Error] {e}")
