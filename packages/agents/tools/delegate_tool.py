# packages/agents/tools/delegate_tool.py
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

_subgraph_factory = None

class DelegateToAgentSchema(BaseModel):
    agent_id: str = Field(..., description="ID агента, которому передается задача (ТОЧНО как в БД!)")
    task_description: str = Field(..., description="Подробное описание задачи для исполнителя")

def register_factory(factory):
    global _subgraph_factory
    _subgraph_factory = factory
    print(f"[DelegateTool] ✅ SubgraphFactory зарегистрирована")

async def delegate_to_agent(agent_id: str, task_description: str) -> str:
    """Делегирует выполнение задачи другому агенту и возвращает его финальный ответ."""
    if not _subgraph_factory:
        return f"Ошибка: Система делегирования не инициализирована."

    try:
        print(f"[DelegateTool] 🎯 Делегирование задачи агенту {agent_id}")

        graph = await _subgraph_factory.build_agent_graph(agent_id)
        print(f"[DelegateTool] ✅ Граф для {agent_id} собран")

        # 🛠 ФИКС: Увеличиваем recursion_limit до 50 шагов для сложных агентов
        final_state = await asyncio.wait_for(
            graph.ainvoke({
                "messages": [HumanMessage(content=task_description)],
                "is_approved": False,
                "iteration": 0,
            }, config={"recursion_limit": 50}),
            timeout=120.0
        )
        print(f"[DelegateTool] ✅ Агент {agent_id} завершил выполнение")

        messages = final_state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                if not msg.content.startswith("REVIEWER REJECT"):
                    result = f"--- Ответ от агента {agent_id} ---\n{msg.content}\n--- Конец ответа ---"
                    return result

        return f"Агент {agent_id} не сформировал финальный ответ."

    except asyncio.TimeoutError:
        return f"⏱ Таймаут (120с): Агент {agent_id} завис (вероятно, сетевой запрос)."
    except Exception as e:
        return f"Ошибка при выполнении задачи агентом {agent_id}: {type(e).__name__}: {str(e)[:200]}"