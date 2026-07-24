from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from packages.agents.factory import build_agent_from_db

# Схема для структурированного вывода роутера
class RouterDecision(BaseModel):
    agent_name: str = Field(description="Имя агента для обработки запроса (строго из списка доступных)")

# Состояние графа
class OrchestratorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_name: str

def create_orchestrator_graph(llm: ChatOpenAI, available_agents: List[str]) -> object:
    
    # 1. Узел роутера
    def router_node(state: OrchestratorState):
        agents_str = ", ".join(available_agents)
        system_prompt = f"Ты диспетчер. Выбери ОДНОГО агента из списка: [{agents_str}]. Отвечай только валидным JSON."
        
        structured_llm = llm.with_structured_output(RouterDecision)
        last_msg = state["messages"][-1].content
        
        decision = structured_llm.invoke([("system", system_prompt), ("human", last_msg)])
        return {"agent_name": decision.agent_name}

    # 2. Узел выполнения агента
    async def agent_node(state: OrchestratorState):
        agent_name = state["agent_name"]
        
        # Загружаем агента из БД (твой factory.py)
        agent = await build_agent_from_db(agent_name)
        if not agent:
            return {"messages": [AIMessage(content=f"Агент {agent_name} не найден или неактивен.")]}

        # BaseAgent.run принимает строку и сам обрабатывает инструменты
        last_user_msg = state["messages"][-1].content
        response = await agent.run(last_user_msg)
        
        return {"messages": [AIMessage(content=response)]}

    # 3. Сборка графа
    workflow = StateGraph(OrchestratorState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("agent", agent_node)
    
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "agent")
    workflow.add_edge("agent", END)
    
    return workflow.compile()
