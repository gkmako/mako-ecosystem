from sqlalchemy import select
from packages.router.database import router_async_session
from packages.router.models import AgentDB

async def get_agents_by_category(category: str) -> list[AgentDB]:
    """Возвращает список активных агентов конкретного Контура."""
    async with router_async_session() as session:
        result = await session.execute(
            select(AgentDB).where(
                AgentDB.category == category, 
                AgentDB.is_active == True
            )
        )
        return list(result.scalars().all())
