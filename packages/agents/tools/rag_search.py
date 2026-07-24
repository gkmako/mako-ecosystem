import os
import httpx

RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://ragflow:9380/api/v1")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")

async def search_knowledge_base(query: str, dataset_id: str = "") -> str:
    """Поиск информации в базе знаний RAGFlow (kb.makotools.ru)."""
    if not RAGFLOW_API_KEY:
        return "Ошибка: RAGFLOW_API_KEY не настроен."

    url = f"{RAGFLOW_API_URL}/retrieval"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Если dataset_id не передан, RAGFlow ищет по всем доступным датасетам
    payload = {
        "question": query,
        "dataset_ids": [dataset_id] if dataset_id else []
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            chunks = data.get("data", {}).get("chunks", [])
            if not chunks:
                return "Информация не найдена."
            
            # Берем топ-3 результата для контекста
            results = [chunk.get("content", "") for chunk in chunks[:3]]
            return "\n\n---\n\n".join(results)
            
    except httpx.HTTPStatusError as e:
        return f"Ошибка RAGFlow API (HTTP {e.response.status_code}): {e.response.text}"
    except Exception as e:
        return f"Ошибка при поиске в RAGFlow: {str(e)}"

SearchKnowledgeBaseSchema = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "Поиск информации в локальной базе знаний (kb.makotools.ru).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос к базе знаний"
                },
                "dataset_id": {
                    "type": "string",
                    "description": "ID конкретного датасета в RAGFlow. Если не указан, поиск идет по всем доступным базам."
                }
            },
            "required": ["query"]
        }
    }
}
