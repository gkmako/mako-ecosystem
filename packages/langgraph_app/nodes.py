"""Узлы графа LangGraph."""

from packages.langgraph_app.graph import AgentState


async def orchestrator_node(state: AgentState) -> dict:
    """Узел оркестратора - маршрутизирует задачи."""
    # TODO: Реализовать маршрутизацию
    return {"next_agent": "unknown"}


async def agent_node(state: AgentState) -> dict:
    """Узел агента - выполняет задачу."""
    # TODO: Реализовать выполнение задачи агентом
    return {"final_response": "Ответ агента"}


def route_decision(state: AgentState) -> Literal["agent", "end"]:
    """Маршрутизация на основе решения оркестратора."""
    if state.get("next_agent") == "unknown":
        return "end"
    return "agent"
