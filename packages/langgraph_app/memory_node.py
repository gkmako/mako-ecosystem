# packages/langgraph_app/memory_node.py
from langchain_core.messages import SystemMessage
from packages.agents.tools.memory_tools import search_memory

async def memory_node(state: dict) -> dict:
    """Context Agent: Обогащает запрос контекстом из памяти."""
    messages = state.get("messages", [])
    if not messages:
        return state
        
    last_msg = messages[-1]
    query = last_msg.get("content", "") if isinstance(last_msg, dict) else last_msg.content
        
    if not query:
        return state
        
    memory_context = await search_memory(query=query)
    
    if memory_context and "Ничего не найдено" not in memory_context:
        context_msg = SystemMessage(content=f"[Контекст из памяти агентства]:\n{memory_context}")
        # Вставляем контекст перед последним сообщением пользователя
        new_messages = messages[:-1] + [context_msg] + [messages[-1]]
        return {"messages": new_messages}
        
    return state
