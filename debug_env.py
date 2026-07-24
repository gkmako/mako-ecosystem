import asyncio
from packages.shared.config import settings
from packages.shared.llm import llm_client

async def main():
    print(f"1. Модель из конфига: {settings.ROUTERAI_EMBEDDING_MODEL}")
    
    response = await llm_client.embeddings.create(
        model=settings.ROUTERAI_EMBEDDING_MODEL,
        input="test"
    )
    dims = len(response.data[0].embedding)
    print(f"2. Реальная размерность от API: {dims}")

asyncio.run(main())
