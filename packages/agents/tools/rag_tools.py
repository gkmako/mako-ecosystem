# packages/agents/tools/rag_tools.py
import httpx
import json
from pydantic import BaseModel, Field
from packages.shared.config import settings
from packages.shared.llm import llm_client

class SearchKnowledgeBaseSchema(BaseModel):
    query: str = Field(description="Поисковый запрос для базы знаний")
    # dataset_ids не передаются агентом, они инжектятся из БД на уровне factory.py

async def rerank_chunks(query: str, chunks: list[dict]) -> list[str]:
    """Использует быструю LLM для оценки релевантности чанков и отбора лучших (LLM-as-a-Judge)."""
    if not chunks:
        return []
        
    texts = [chunk.get("content", "") for chunk in chunks]
    
    system_prompt = f"""Ты — эксперт по оценке релевантности. 
Тебе дан запрос пользователя и список фрагментов текста.
Оцени каждый фрагмент по шкале от 0 до 10 по степени полезности для ответа на запрос.
Верни ТОЛЬКО JSON объект с ключом "scores" и массивом чисел для каждого фрагмента в том же порядке.
Пример: {{"scores": [8, 2, 9, 0, 5]}}

Запрос: {query}"""

    user_prompt = "Фрагменты:\n" + "\n---\n".join([f"[{i}] {text}" for i, text in enumerate(texts)])

    try:
        response = await llm_client.chat.completions.create(
            model=settings.ROUTERAI_FAST_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        scores = data.get("scores", [])
        
        scored_chunks = []
        for i, chunk in enumerate(chunks):
            score = scores[i] if i < len(scores) else 0
            scored_chunks.append((score, chunk.get("content", "")))
        
        # Сортируем по убыванию скора и берем топ-3, отсеивая мусор (скор < 7)
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in scored_chunks[:3] if c[0] >= 7]
        
    except Exception:
        # Фолбэк: если LLM не справилась, возвращаем первые 3
        return [chunk.get("content", "") for chunk in chunks[:3]]

async def search_knowledge_base(query: str, dataset_ids: list[str] = None) -> str:
    """Ищет релевантную информацию в RAGFlow с последующим LLM-ре-ранжированием."""
    if not dataset_ids:
        return "База знаний для этого агента не настроена (пустой список dataset_ids)."

    headers = {
        "Authorization": f"Bearer {settings.RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "dataset_ids": dataset_ids,
        "question": query,
        "top_k": 10, # Запрашиваем больше для последующего ре-ранжирования
        "similarity_threshold": 0.2,
        "vector_similarity_weight": 0.3,
        "keyword_similarity_weight": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.RAGFLOW_API_BASE}/retrieval", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            chunks = data.get("data", {}).get("chunks", [])
            if not chunks:
                return "По запросу ничего не найдено в базе знаний."
                
            # LLM Re-ranking для повышения точности
            relevant_contents = await rerank_chunks(query, chunks)
            
            if not relevant_contents:
                return "Найдены фрагменты, но ни один не прошел проверку релевантности (LLM Re-ranker)."
                
            result_text = "Найденные и проверенные фрагменты из базы знаний:\n\n"
            for i, content in enumerate(relevant_contents, 1):
                result_text += f"--- Фрагмент {i} ---\n{content}\n\n"
            return result_text
            
    except Exception as e:
        return f"Ошибка при обращении к RAGFlow: {str(e)}"
