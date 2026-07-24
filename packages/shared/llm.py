# packages/shared/llm.py
from openai import AsyncOpenAI
from packages.shared.config import settings

# Глобальный асинхронный клиент для внутренних нужд (memory, router core)
llm_client = AsyncOpenAI(
    base_url=settings.LLM_API_BASE,
    api_key=settings.LLM_API_KEY,
)
