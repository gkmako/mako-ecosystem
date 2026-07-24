# packages/router/core.py
from sqlalchemy import select
from packages.shared.llm import llm_client
from packages.shared.config import settings
from packages.router.schemas import RoutingDecision
from packages.router.database import router_async_session
from packages.router.models import AgentDB

async def get_active_agents_prompt() -> str:
    """Генерирует список агентов для системного промпта роутера прямо из БД."""
    async with router_async_session() as session:
        result = await session.execute(select(AgentDB).where(AgentDB.is_active == True))
        agents = result.scalars().all()

    if not agents:
        return "Агенты не настроены. Возвращай unknown."

    lines = []
    for ag in agents:
        lines.append(f'- name: "{ag.name}" | display: "{ag.display_name}"')
    return "\n".join(lines)

async def get_agent_names() -> list[str]:
    """Возвращает список реальных имен агентов из БД."""
    async with router_async_session() as session:
        result = await session.execute(select(AgentDB.name).where(AgentDB.is_active == True))
        return [row[0] for row in result.all()]

async def route_task(prompt: str) -> RoutingDecision:
    agents_list = await get_active_agents_prompt()
    valid_agent_names = await get_agent_names()

    system_prompt = f"""Ты — диспетчер (Competency Router) в AI-агентстве Makotools.
Проанализируй запрос пользователя и определи, какому агенту его передать.

ДОСТУПНЫЕ АГЕНТЫ (используй ТОЛЬКО эти имена в поле assigned_agent):
{agents_list}

ПРАВИЛА:
1. category может быть ТОЛЬКО: "development", "sales", "architecture" или "unknown"
2. assigned_agent должен быть ТОЧНО одним из имен выше (например, "developer", "architect")
3. Если запрос не подходит ни одному агенту, верни category="unknown" и assigned_agent="orchestrator"

Верни СТРОГО JSON:
{{"category": "...", "reasoning": "...", "assigned_agent": "..."}}"""

    response = await llm_client.chat.completions.create(
        model=settings.ROUTERAI_ROUTER_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    
    decision = RoutingDecision.model_validate_json(response.choices[0].message.content)
    
    # БЕЗОПАСНЫЙ ФОЛБЭК: если LLM выдумала имя агента, отправляем запрос универсальному оркестратору
    if decision.assigned_agent not in valid_agent_names:
        fallback_agent = "orchestrator" if "orchestrator" in valid_agent_names else (valid_agent_names[0] if valid_agent_names else "orchestrator")
        decision.assigned_agent = fallback_agent
        decision.category = "management"
        decision.reasoning += f" [FALLBACK: запрошенный агент не найден в БД, передано оркестратору]"
    
    return decision
