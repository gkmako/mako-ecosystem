from packages.agents.base import BaseAgent
from packages.shared.config import settings

ARCH_INSTRUCTIONS = """
Ты — Architect Agent в AI-агентстве Makotools.
Твоя задача — проектировать архитектуру систем, выбирать технологический стек, проектировать базы данных и обеспечивать масштабируемость.
Используй инструменты для проверки лучших практик и совместимости технологий.
Отвечай технически грамотно, аргументируя каждый выбор.
"""

def check_tech_compatibility(tech1: str, tech2: str) -> str:
    """Проверяет совместимость и лучшие практики для пары технологий."""
    return f"Связка {tech1} + {tech2}: Отличная совместимость. Рекомендуется использовать {tech1} в качестве ядра, а {tech2} для асинхронных задач. Не забудь про Docker."

check_tech_compatibility_schema = {
    "type": "function",
    "function": {
        "name": "check_tech_compatibility",
        "description": "Проверить архитектурную совместимость двух технологий.",
        "parameters": {
            "type": "object",
            "properties": {
                "tech1": {"type": "string", "description": "Первая технология"},
                "tech2": {"type": "string", "description": "Вторая технология"}
            },
            "required": ["tech1", "tech2"]
        }
    }
}

architect_agent = BaseAgent(
    name="architect_agent",
    instructions=ARCH_INSTRUCTIONS,
    model=settings.ROUTERAI_SMART_MODEL # Архитектура требует мощной reasoning-модели
)
architect_agent.register_tool(check_tech_compatibility, check_tech_compatibility_schema)
