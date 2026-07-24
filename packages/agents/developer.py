from packages.agents.base import BaseAgent
from packages.shared.config import settings

DEV_INSTRUCTIONS = """
Ты — опытный Developer Agent в AI-агентстве Makotools.
Твоя задача — писать чистый, современный код, анализировать требования и предлагать решения.
Если тебе нужно узнать контекст или структуру проекта, обязательно используй доступные инструменты.
Отвечай кратко и по делу.
"""

# Заглушка инструмента (позже заменим на реальное чтение ФС или MCP)
def get_project_structure(path: str) -> str:
    return f"Структура директории {path}:\n- main.py\n- database.py\n- requirements.txt\n- .env"

get_project_structure_schema = {
    "type": "function",
    "function": {
        "name": "get_project_structure",
        "description": "Получить список файлов и папок в указанной директории проекта.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Путь к директории"}
            },
            "required": ["path"]
        }
    }
}

# Инициализация агента
developer_agent = BaseAgent(
    name="developer_agent",
    instructions=DEV_INSTRUCTIONS,
    model=settings.ROUTERAI_SMART_MODEL
)
developer_agent.register_tool(get_project_structure, get_project_structure_schema)
