from sqlalchemy import select
from packages.router.database import router_async_session
from packages.router.models import AgentDB
from packages.agents.base import BaseAgent
from packages.agents.tools_registry import TOOLS_REGISTRY

async def build_agent_from_db(agent_name: str) -> BaseAgent | None:
    """Загружает конфигурацию агента из БД и инициализирует его с инструментами."""
    async with router_async_session() as session:
        result = await session.execute(
            select(AgentDB).where(AgentDB.name == agent_name, AgentDB.is_active == True)
        )
        agent_db = result.scalar_one_or_none()
        
    if not agent_db:
        return None
        
    agent = BaseAgent(
        name=agent_db.name,
        instructions=agent_db.instructions,
        model=agent_db.model_name
    )
    
    for tool_name in (agent_db.allowed_tools or []):
        if tool_name in TOOLS_REGISTRY:
            func, schema = TOOLS_REGISTRY[tool_name]
            agent.register_tool(func, schema)
            
    return agent
