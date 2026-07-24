from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

def create_two_agent_graph(
    main_model: BaseChatModel,
    reviewer_model: BaseChatModel,
    reviewer_system_prompt: str = "Ты ревьюер. Оцени ответ. Если всё хорошо, напиши 'APPROVED'. Если есть ошибки, опиши их.",
    max_iterations: int = 2
) -> object:
    """Создает и компилирует граф двухагентной схемы (Main + Reviewer)."""
    
    workflow = StateGraph(MessagesState)

    # Узел основного агента
    def main_node(state: MessagesState):
        response = main_model.invoke(state["messages"])
        return {"messages": [response]}

    # Узел ревьюера
    def reviewer_node(state: MessagesState):
        # Формируем контекст для ревьюера (последнее сообщение от основного агента)
        last_message = state["messages"][-1].content
        messages = [
            SystemMessage(content=reviewer_system_prompt),
            HumanMessage(content=f"Оцени следующий ответ:\n\n{last_message}")
        ]
        response = reviewer_model.invoke(messages)
        return {"messages": [response]}

    # Маршрутизация после ревьюера
    def route_after_reviewer(state: MessagesState) -> Literal["main", "end"]:
        last_message = state["messages"][-1].content.lower()
        
        # Простая логика: если ревьюер написал APPROVED или мы достигли лимита итераций
        # В реальности здесь лучше использовать парсинг JSON или четкие ключевые слова
        if "approved" in last_message or len(state["messages"]) > (max_iterations * 2 + 2):
            return "end"
        return "main"

    # Сборка графа
        # Сборка графа
    workflow.add_node("main", main_node)
    workflow.add_node("reviewer", reviewer_node)

    workflow.set_entry_point("main")
    workflow.add_edge("main", "reviewer")

    workflow.add_conditional_edges(
        "reviewer", 
        route_after_reviewer,
        {
            "main": "main",
            "end": END
        }
    )

    return workflow.compile()
