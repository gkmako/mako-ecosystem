import asyncio
from packages.router.database import router_async_session
from packages.router.models import AgentDB
from sqlalchemy import select

async def list_agents():
    async with router_async_session() as s:
        r = await s.execute(select(AgentDB).order_by(AgentDB.contour, AgentDB.name))
        for a in r.scalars().all():
            print(f'{a.contour:15} | {a.name:25} | {a.display_name:30} | active={a.is_active}')

asyncio.run(list_agents())
