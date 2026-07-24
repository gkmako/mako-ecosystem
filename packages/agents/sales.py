from packages.agents.base import BaseAgent
from packages.shared.config import settings

SALES_INSTRUCTIONS = """
Ты — Sales Agent (менеджер по расчетам) в команде Makotools.
Твоя задача — оценивать сроки и стоимость проектов, анализировать требования и составлять сметы.
Опирайся строго на факты и ставки, полученные через инструменты. 
Никаких наценок или коэффициентов не применяй, считай ровно по ставке из базы.
Отвечай структурированно и прозрачно для клиента.
"""

def get_company_rate(role: str) -> str:
    """Возвращает актуальную ставку специалиста (в будущем будет читать из БД)."""
    rates = {
        "developer": 4500,
        "architect": 7500,
        "qa": 3500,
        "pm": 5000
    }
    rate = rates.get(role.lower(), 5000)
    return f"Актуальная ставка для роли '{role}': {rate} руб/час."

get_company_rate_schema = {
    "type": "function",
    "function": {
        "name": "get_company_rate",
        "description": "Узнать часовую ставку специалиста для расчета сметы.",
        "parameters": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Роль (developer, architect, qa, pm)"}
            },
            "required": ["role"]
        }
    }
}

sales_agent = BaseAgent(
    name="sales_agent",
    instructions=SALES_INSTRUCTIONS,
    model=settings.ROUTERAI_FAST_MODEL
)
sales_agent.register_tool(get_company_rate, get_company_rate_schema)
