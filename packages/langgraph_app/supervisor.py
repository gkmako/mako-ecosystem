# packages/langgraph_app/supervisor.py
from typing import Literal, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

from packages.shared.config import settings
from packages.shared.llm_profiles import ROUTER_PROFILE
from packages.langgraph_app.subgraph_factory import build_contour_graph
from packages.langgraph_app.memory_node import memory_node
from packages.langgraph_app.rule_router import rule_based_route


class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    contour: Optional[str]
    agent_name: Optional[str]


class ContourDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    contour: Literal[
        "management",
        "research",
        "architecture",
        "development",
        "business",
        "content",
    "image",
    "marketing",
        "support",
        "ai_ops",
        "unknown",
    ] = Field(validation_alias=AliasChoices("contour", "category", "type", "name"))

    agent: Optional[str] = Field(
        default=None,
        description="Имя конкретного агента (например, python_developer). Оставь null, если не уверен."
    )


def create_supervisor_graph():
    workflow = StateGraph(SupervisorState)
    workflow.add_node("memory", memory_node)

    async def router_node(state: SupervisorState):
        last_msg = state["messages"][-1]
        content = last_msg.get("content",
    "image",
    "marketing", "") if isinstance(last_msg, dict) else last_msg.content

        print(f"\n{'='*60}")
        print(f"[Router] 🔍 Классифицирую запрос длиной {len(content)} симв.")
        print(f"{'='*60}")

        # Шаг 1: Rule-based роутинг (только приветствия и пинг)
        try:
            rule_result = rule_based_route(content)
            if rule_result:
                contour, agent_name = rule_result
                print(f"[Router] ✅ Rule-based: {contour}/{agent_name}")
                return {"contour": contour, "agent_name": agent_name}
        except Exception as e:
            print(f"[Router] ⚠️ Rule-based failed: {e}")

        # Шаг 2: LLM роутинг (умная маршрутизация)
        print("[Router] 🤖 Используем LLM для семантического роутинга")

        llm = ChatOpenAI(
            model=settings.ROUTERAI_ROUTER_MODEL,
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
            **ROUTER_PROFILE,
        ).with_structured_output(ContourDecision, include_raw=True)

        system_prompt = """Ты — умный маршрутизатор в мультиагентной системе МАКО.
Твоя задача — решить, КТО должен выполнить запрос пользователя.

🚨 ПРАВИЛО №1: ОРКЕСТРАТОР (management / orchestrator)
ВСЕГДА отправляй запрос Оркестратору, если:
- Задача требует НЕСКОЛЬКИХ ШАГОВ (например: "проанализируй рынок И напиши скрипт", "спроектируй И составь смету").
- Задача комплексная и требует координации разных специалистов.
- Запрос общий, философский или ты не уверен, кому его поручить.
Оркестратор сам разобьет задачу и заделегит её нужным агентам.

🚨 ПРАВИЛО №2: УЗКИЕ СПЕЦИАЛИСТЫ
Отправляй конкретному агенту ТОЛЬКО если задача ОДНОШАГОВАЯ и узкоспециализированная:
- development: "напиши ОДНУ функцию", "исправь ОДИН баг в этом коде".
- architecture: "спроектируй ТОЛЬКО базу данных".
- business: "составь ТОЛЬКО КП по этим вводным".
- content: "напиши ОДИН пост".

КОНТУРЫ:
- management (orchestrator) - сложные, составные и общие задачи
- research - глубокий поиск информации
- architecture - проектирование систем
- development - программирование
- business - бизнес-аналитика, продажи
- content - тексты, UI/UX, медиа
- support - техподдержка, инциденты
- ai_ops - работа с LLM, промптами
image - генерация изображений, видео, логотипов, бренд-дизайн
marketing - маркетинговые стратегии, продвижение, аналитика рынка

Верни СТРОГО JSON с полями "contour" и "agent" (agent = null, если пусть выбирает система)."""

        try:
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=content),
            ])

            if response.get("parsing_error"):
                print(f"[Router] ⚠️ Parsing error: {response['parsing_error']}")

            decision = response.get("parsed")
            if decision:
                print(f"[Router] ✅ LLM Parsed: {decision.contour}/{decision.agent or 'auto'}")
                return {"contour": decision.contour, "agent_name": decision.agent}

            print("[Router] ⚠️ LLM returned None -> management/orchestrator")
            return {"contour": "management", "agent_name": "orchestrator"}

        except Exception as e:
            print(f"[Router] ❌ Exception: {type(e).__name__}: {str(e)[:200]}")
            return {"contour": "management", "agent_name": "orchestrator"}

    workflow.add_node("router", router_node)

    contours = [
        "management", "research", "architecture", "development",
        "business", "content",
    "image",
    "marketing", "support", "ai_ops",
    ]

    def create_subgraph_node(contour_name: str):
        async def subgraph_node(state: SupervisorState):
            agent_name = state.get("agent_name")
            print(f"\n[Subgraph:{contour_name}] 🚀 Запуск | агент: {agent_name or 'auto'}")

            try:
                graph = await build_contour_graph(contour_name, agent_name)
                print(f"[Subgraph:{contour_name}] ✅ Граф собран")

                total_msg_chars = sum(len(m.content) if hasattr(m, 'content') and isinstance(m.content, str) else len(str(m)) for m in state["messages"])
                print(f"[Subgraph:{contour_name}] 📊 STATE SIZE: {len(state['messages'])} messages, {total_msg_chars} chars (~{total_msg_chars//4} tokens)")

                final_sub_state = await graph.ainvoke(
                    {"messages": state["messages"]}, 
                    config={"recursion_limit": 50}
                )
                print(f"[Subgraph:{contour_name}] ✅ Выполнение завершено")
                return {"messages": final_sub_state["messages"]}

            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                print(f"[Subgraph:{contour_name}] ❌ ОШИБКА: {error_type}: {error_msg[:300]}")

                if "Insufficient balance" in error_msg or "402" in error_msg:
                    return {"messages": [AIMessage(content="⚠️ Недостаточно средств на балансе LLM.")]
                            }
                elif "Model" in error_msg and "not found" in error_msg:
                    return {"messages": [AIMessage(content="⚠️ Модель не найдена у провайдера.")]
                            }
                elif "API" in error_type:
                    return {"messages": [AIMessage(content=f"⚠️ Ошибка LLM ({error_type}).")]
                            }
                else:
                    return {"messages": [AIMessage(content=f"⚠️ Внутренняя ошибка: {error_type}. Попробуйте переформулировать.")]
                            }

        return subgraph_node

    for contour in contours:
        workflow.add_node(contour, create_subgraph_node(contour))

    async def fallback_node(state: SupervisorState):
        return {"messages": [AIMessage(content="Я не понял запрос. Уточните задачу.")]}

    workflow.add_node("unknown", fallback_node)

    workflow.add_edge(START, "memory")
    workflow.add_edge("memory", "router")
    workflow.add_conditional_edges(
        "router",
        lambda state: (state.get("contour") or "unknown").strip(),
    )
    for contour in contours + ["unknown"]:
        workflow.add_edge(contour, END)

    compiled = workflow.compile()
    print(f"\n[Supervisor] ✅ Граф скомпилирован. Активных контуров: {len(contours)}")
    return compiled