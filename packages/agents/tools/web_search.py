import os
import json
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from packages.shared.config import settings

# Модель Perplexity через RouterAI
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "perplexity/sonar")


class WebSearchSchema(BaseModel):
    """Поиск актуальной информации через Perplexity Sonar."""
    query: str = Field(description="Поисковый запрос (чёткий, конкретный)")
    max_results: int = Field(default=5, description="Игнорируется (для совместимости)")


async def web_search(query: str, max_results: int = 5) -> str:
    """Поиск через Perplexity Sonar (LLM + Web Search в одном)."""
    try:
        llm = ChatOpenAI(
            model=PERPLEXITY_MODEL,
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
            temperature=0.1,
            max_tokens=2000,
        )

        system_prompt = """Ты — эксперт по веб-поиску. Ответь на запрос пользователя используя актуальную информацию из интернета.

Правила:
- Цитируй источники со ссылками [1], [2] и т.д.
- В конце ответа дай список источников в формате:

### Источники
1. [Название или домен](URL)
2. ...

- Если информация противоречива — укажи разные точки зрения
- Отвечай на русском языке
- Если не нашёл релевантной информации — честно скажи об этом"""

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ])

        content = response.content or "Ничего не найдено"
        
        # Perplexity возвращает citations в metadata
        try:
            metadata = getattr(response, "response_metadata", {}) or {}
            citations = metadata.get("citations") or metadata.get("search_results", [])
            
            if citations and isinstance(citations, list) and "### Источники" not in content:
                content += "\n\n### Источники (из Perplexity)\n"
                for i, url in enumerate(citations[:10], 1):
                    if isinstance(url, str):
                        content += f"{i}. {url}\n"
                    elif isinstance(url, dict):
                        content += f"{i}. {url.get('url', url)}\n"
        except Exception:
            pass  # citations опциональны

        return content

    except Exception as e:
        return json.dumps({
            "error": f"Perplexity API error: {type(e).__name__}: {str(e)[:200]}"
        }, ensure_ascii=False)
