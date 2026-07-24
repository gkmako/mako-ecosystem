"""
SubgraphFactory - динамическая сборка графов агентов.
"""
import json
import logging
import warnings
from typing import TypedDict, Annotated, List, Optional, Tuple

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    HumanMessage, SystemMessage, AIMessage, BaseMessage,
)
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from sqlalchemy import select

from packages.shared.config import settings
from packages.shared.llm_profiles import ROUTER_PROFILE
from packages.langgraph_app.prompt_builder import PromptBuilder
from packages.agents.tools import get_tool_by_name
from packages.agents.tools.delegate_tool import register_factory
from packages.router.database import router_async_session
from packages.router.models import AgentDB

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]
    is_approved: bool
    iteration: int
    reviewer_feedback: Optional[str]


class SubgraphFactory:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        register_factory(self)

    async def _get_active_agents_list(self) -> Tuple[str, List[str]]:
        """Возвращает текст для промпта и список валидных ID."""
        try:
            async with router_async_session() as session:
                result = await session.execute(
                    select(AgentDB.name, AgentDB.display_name, AgentDB.category)
                    .where(AgentDB.is_active == True, AgentDB.name != "orchestrator")
                )
                agents = result.all()
                if not agents:
                    return "Список агентов пуст.", []
                lines = []
                ids = []
                for name, display_name, category in agents:
                    lines.append(f"- `{name}` ({display_name}, контур: {category})")
                    ids.append(name)
                return "\n".join(lines), ids
        except Exception as e:
            logger.warning(f"[Orchestrator] Ошибка загрузки списка агентов: {e}")
            return "Ошибка загрузки списка.", []

    def _get_llm(
        self,
        model_name: str,
        tools: list,
        temperature: float = 0.1,
        top_p: float = None,
        top_k: int = None,
        max_tokens: int = None,
        frequency_penalty: float = None,
        presence_penalty: float = None,
    ) -> ChatOpenAI:
        profile_kwargs = {**ROUTER_PROFILE, "temperature": temperature}
        if top_p is not None:
            profile_kwargs["top_p"] = top_p
        if top_k is not None:
            profile_kwargs["top_k"] = top_k
        if max_tokens is not None:
            profile_kwargs["max_tokens"] = max_tokens
        if frequency_penalty is not None:
            profile_kwargs["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            profile_kwargs["presence_penalty"] = presence_penalty

        llm = ChatOpenAI(
            model=model_name,
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
            **profile_kwargs,
        )
        if tools:
            return llm.bind_tools(tools)
        return llm

    def _normalize_tool_calls(self, response: BaseMessage) -> BaseMessage:
        has_tcs = getattr(response, "tool_calls", None)
        has_invalid = getattr(response, "invalid_tool_calls", None)
        if not has_tcs and not has_invalid:
            return response

        normalized_tcs = []
        all_calls = list(has_tcs or []) + list(has_invalid or [])
        for tc in all_calls:
            tc_dict = dict(tc)
            args = tc_dict.get("args")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw_args": args}
            elif not isinstance(args, dict):
                args = {}
            normalized_tcs.append({
                "name": tc_dict.get("name"),
                "args": args,
                "id": tc_dict.get("id"),
                "type": "tool_call"
            })

        return AIMessage(
            content=response.content,
            tool_calls=normalized_tcs,
            invalid_tool_calls=[],
            id=getattr(response, "id", None),
            additional_kwargs=getattr(response, "additional_kwargs", {}),
            response_metadata=getattr(response, "response_metadata", {})
        )

    async def _select_agent_from_contour(self, contour: str, task: str, suggested_agent: Optional[str]) -> str:
        if suggested_agent and suggested_agent.lower() not in ("auto", "none", ""):
            try:
                self.prompt_builder.load_profile(suggested_agent)
                return suggested_agent
            except FileNotFoundError:
                try:
                    async with router_async_session() as session:
                        result = await session.execute(
                            select(AgentDB).where(AgentDB.name == suggested_agent, AgentDB.is_active == True)
                        )
                        if result.scalar_one_or_none():
                            return suggested_agent
                except Exception:
                    pass

        try:
            async with router_async_session() as session:
                result = await session.execute(select(AgentDB).where(AgentDB.is_active == True))
                all_agents = result.scalars().all()
        except Exception:
            return "python_developer"

        contour_agents = [ag for ag in all_agents if getattr(ag, "category", None) == contour]
        if not contour_agents:
            contour_agents = list(all_agents)
        if not contour_agents:
            return "python_developer"

        if len(contour_agents) == 1:
            return contour_agents[0].name

        agents_list = "\n".join([f'- name: "{ag.name}" | display: "{ag.display_name}"' for ag in contour_agents])
        system_prompt = f"Ты — диспетчер. Выбери агента для контура {contour}.\nАГЕНТЫ:\n{agents_list}\nВерни ТОЛЬКО name."

        try:
            llm = self._get_llm(settings.ROUTERAI_FAST_MODEL, [], temperature=0.0)
            response = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=task or "default")])
            selected = response.content.strip().strip('"').strip("'")
            if selected in [ag.name for ag in contour_agents]:
                return selected
            logger.warning(f"[Router] LLM вернул '{selected}', не найден в контуре '{contour}'. Fallback: {contour_agents[0].name}")
            return contour_agents[0].name
        except Exception:
            return contour_agents[0].name

    async def build_agent_graph(self, agent_id: str):
        try:
            profile = self.prompt_builder.load_profile(agent_id)
        except FileNotFoundError:
            return await self._build_dynamic_or_fallback_graph(agent_id)

        execution_cfg = profile.get("execution")
        capabilities = profile.get("capabilities", {})
        if not execution_cfg:
            execution_cfg = {
                "schema": "one_agent",
                "model": settings.ROUTERAI_FAST_MODEL,
                "temperature": 0.1,
                "max_retries": 2
            }
            profile["execution"] = execution_cfg

        try:
            async with router_async_session() as session:
                result = await session.execute(select(AgentDB).where(AgentDB.name == agent_id))
                db_agent = result.scalar_one_or_none()
                if db_agent:
                    if getattr(db_agent, "model_name", None):
                        execution_cfg["model"] = db_agent.model_name
                    if getattr(db_agent, "reviewer_model_name", None) and "reviewer" in execution_cfg:
                        execution_cfg["reviewer"]["model"] = db_agent.reviewer_model_name

                    if getattr(db_agent, "llm_parameters", None):
                        llm_params = db_agent.llm_parameters
                        for param_name in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", "presence_penalty"]:
                            param_data = llm_params.get(param_name, {})
                            value = param_data.get("work")
                            if value is not None:
                                execution_cfg[param_name] = value
                            elif param_data.get("default") is not None:
                                execution_cfg[param_name] = param_data["default"]

                    if getattr(db_agent, "reviewer_parameters", None) and "reviewer" in execution_cfg:
                        rev_params = db_agent.reviewer_parameters
                        for param_name in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", "presence_penalty"]:
                            param_data = rev_params.get(param_name, {})
                            value = param_data.get("work")
                            if value is not None:
                                execution_cfg["reviewer"][param_name] = value
                            elif param_data.get("default") is not None:
                                execution_cfg["reviewer"][param_name] = param_data["default"]
        except Exception:
            pass

        max_retries = execution_cfg.get("max_retries", 2)
        tools = []
        for tool_name in capabilities.get("tools", []):
            try:
                tools.append(get_tool_by_name(tool_name))
            except Exception:
                pass

        is_two_agent = execution_cfg.get("schema") == "two_agent"
        stream_tags = [] if is_two_agent else ["stream_to_client"]

        agent_llm = self._get_llm(
            execution_cfg["model"],
            tools,
            execution_cfg.get("temperature", 0.1),
            top_p=execution_cfg.get("top_p"),
            top_k=execution_cfg.get("top_k"),
            max_tokens=execution_cfg.get("max_tokens"),
            frequency_penalty=execution_cfg.get("frequency_penalty"),
            presence_penalty=execution_cfg.get("presence_penalty"),
        ).with_config({"tags": stream_tags})

        reviewer_llm = None
        if is_two_agent:
            reviewer_cfg = execution_cfg.get("reviewer", {})
            reviewer_llm = self._get_llm(
                reviewer_cfg.get("model", settings.ROUTERAI_REVIEWER_MODEL),
                [],
                reviewer_cfg.get("temperature", 0.0),
                top_p=reviewer_cfg.get("top_p"),
                top_k=reviewer_cfg.get("top_k"),
                max_tokens=reviewer_cfg.get("max_tokens"),
                frequency_penalty=reviewer_cfg.get("frequency_penalty"),
                presence_penalty=reviewer_cfg.get("presence_penalty"),
            )

        async def agent_node(state: AgentState, config: RunnableConfig):
            iteration = state.get("iteration", 0)
            sys_prompt = self.prompt_builder.build_agent_prompt(agent_id)

            await adispatch_custom_event(
                "status_update",
                {"status": f"🤖 {agent_id} думает..."},
                config=config
            )

            if agent_id == "orchestrator":
                agents_text, valid_ids = await self._get_active_agents_list()
                valid_ids_str = ", ".join([f'"{id}"' for id in valid_ids])
                sys_prompt += f"""

🚨 КРИТИЧЕСКИ ВАЖНО: ИНСТРУМЕНТ `delegate_to_agent` 🚨
В параметре `agent_id` ты ИМЕЕШЬ ПРАВО использовать ТОЛЬКО одно из этих точных значений (буква в букву):
[{valid_ids_str}]

❌ ЗАПРЕЩЕНО выдумывать имена (например, researcher, coder, knowledge_agent, context_agent, analyst).
❌ ЗАПРЕЩЕНО использовать синонимы или переводить названия.
✅ Если нужного специалиста нет в списке выше — ВЫПОЛНИ ЗАДАЧУ САМ своими силами, не вызывая `delegate_to_agent`.

📋 СПИСОК ДОСТУПНЫХ АГЕНТОВ (ID -> Роль):
{agents_text}

Правила работы:
1. Разбей сложный запрос пользователя на подзадачи.
2. Делегируй подзадачи ТОЛЬКО агентам из списка выше.
3. Собери ответы от агентов и сформируй финальный отчет для пользователя.
4. Если агент вернул ошибку (таймаут), попробуй другого агента из списка или реши задачу сам.
"""

            messages = [SystemMessage(content=sys_prompt)] + state["messages"]
            feedback = state.get("reviewer_feedback")
            if feedback:
                messages.append(HumanMessage(content=f"Критика от ревьюера (учти её):\n{feedback}"))

            try:
                await adispatch_custom_event(
                    "status_update",
                    {"status": f"🧠 {agent_id} генерирует ответ..."},
                    config=config
                )
                response = await agent_llm.ainvoke(messages)
                response = self._normalize_tool_calls(response)

                has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
                if has_tool_calls:
                    tool_names = [tc["name"] for tc in response.tool_calls]
                    await adispatch_custom_event(
                        "status_update",
                        {"status": f"🔧 {agent_id} → {', '.join(tool_names)}"},
                        config=config
                    )

                update_dict = {"messages": [response]}
                if not has_tool_calls:
                    update_dict["iteration"] = iteration + 1
                    update_dict["reviewer_feedback"] = None
                return update_dict

            except Exception as e:
                logger.error(f"[{agent_id}] LLM error: {e}")
                raise

        async def reviewer_node(state: AgentState, config: RunnableConfig):
            await adispatch_custom_event(
                "status_update",
                {"status": "✅ Reviewer проверяет ответ..."},
                config=config
            )

            last_message = state["messages"][-1]
            domain = execution_cfg.get("reviewer", {}).get("domain", "general")
            checks = execution_cfg.get("reviewer", {}).get("checks", [])
            sys_prompt = self.prompt_builder.build_reviewer_prompt(domain, checks)

            messages = [SystemMessage(content=sys_prompt), HumanMessage(content=f"Проверь:\n{last_message.content}")]

            try:
                response = await reviewer_llm.ainvoke(messages)
                content = response.content.strip().strip("`").replace("json", "").strip()
                data = json.loads(content)

                is_approved = data.get("is_approved", False)
                feedback = data.get("feedback", "")

                if is_approved:
                    return {"is_approved": True}
                else:
                    return {
                        "is_approved": False,
                        "reviewer_feedback": f"REVIEWER REJECT: {feedback}. Исправь ошибки."
                    }
            except Exception as e:
                logger.warning(f"[Reviewer] Parse/LLM error: {e}")
                return {
                    "is_approved": False,
                    "reviewer_feedback": "Ошибка проверки формата. Повтори ответ в корректном JSON-формате."
                }

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")

        if tools:
            workflow.add_node("tools", ToolNode(tools))
            workflow.add_edge("tools", "agent")

            def should_continue(state: AgentState):
                last_message = state["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    return "tools"
                return "reviewer" if is_two_agent else END

            workflow.add_conditional_edges("agent", should_continue)
        else:
            workflow.add_edge("agent", "reviewer" if is_two_agent else END)

        if is_two_agent:
            workflow.add_node("reviewer", reviewer_node)

            def route_reviewer(state: AgentState):
                if state.get("is_approved"):
                    return END
                iteration = state.get("iteration", 0)
                if iteration >= max_retries:
                    return END
                return "agent"

            workflow.add_conditional_edges("reviewer", route_reviewer)

        return workflow.compile()

    async def _build_dynamic_or_fallback_graph(self, agent_id: str):
        try:
            async with router_async_session() as session:
                result = await session.execute(select(AgentDB).where(AgentDB.name == agent_id))
                db_agent = result.scalar_one_or_none()
                if db_agent and db_agent.is_active:
                    return await self._build_dynamic_graph(db_agent)
        except Exception:
            pass

        try:
            self.prompt_builder.load_profile("python_developer")
            return await self.build_agent_graph("python_developer")
        except FileNotFoundError:
            pass

        workflow = StateGraph(AgentState)

        async def fallback_node(state: AgentState):
            return {"messages": [AIMessage(content=f"⚠️ Агент '{agent_id}' не найден.")]}

        workflow.add_node("fallback", fallback_node)
        workflow.set_entry_point("fallback")
        workflow.add_edge("fallback", END)
        return workflow.compile()

    async def _build_dynamic_graph(self, db_agent):
        agent_id = db_agent.name
        display_name = getattr(db_agent, "display_name", agent_id)
        description = f"Специализированный агент: {display_name}"
        model_name = getattr(db_agent, "model_name", None) or settings.ROUTERAI_FAST_MODEL

        sys_prompt = f"Ты — {display_name}.\n\n## Описание:\n{description}\n\nОтвечай на русском."

        tools = []
        dev_keywords = ["developer", "engineer", "devops", "architect", "database", "ai_engineer", "frontend", "backend"]
        if any(kw in agent_id.lower() for kw in dev_keywords):
            for tool_name in ["get_project_structure", "read_file", "write_file", "search_memory", "save_to_memory"]:
                try:
                    tools.append(get_tool_by_name(tool_name))
                except Exception:
                    pass

        llm_kwargs = {
            "temperature": 0.2,
            "top_p": None,
            "top_k": None,
            "max_tokens": None,
            "frequency_penalty": None,
            "presence_penalty": None
        }
        if getattr(db_agent, "llm_parameters", None):
            for param_name in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", "presence_penalty"]:
                param_data = db_agent.llm_parameters.get(param_name, {})
                value = param_data.get("work")
                if value is not None:
                    llm_kwargs[param_name] = value
                elif param_data.get("default") is not None:
                    llm_kwargs[param_name] = param_data["default"]

        is_two_agent = getattr(db_agent, "schema_type", None) == "Двухагентная"
        stream_tags = [] if is_two_agent else ["stream_to_client"]

        agent_llm = self._get_llm(
            model_name,
            tools,
            llm_kwargs["temperature"],
            top_p=llm_kwargs["top_p"],
            top_k=llm_kwargs["top_k"],
            max_tokens=llm_kwargs["max_tokens"],
            frequency_penalty=llm_kwargs["frequency_penalty"],
            presence_penalty=llm_kwargs["presence_penalty"],
        ).with_config({"tags": stream_tags})

        reviewer_llm = None
        max_retries = 2
        if is_two_agent:
            reviewer_model = getattr(db_agent, "reviewer_model_name", None) or settings.ROUTERAI_REVIEWER_MODEL
            reviewer_kwargs = {
                "temperature": 0.0,
                "top_p": None,
                "top_k": None,
                "max_tokens": None,
                "frequency_penalty": None,
                "presence_penalty": None
            }
            if getattr(db_agent, "reviewer_parameters", None):
                for param_name in ["temperature", "top_p", "top_k", "max_tokens", "frequency_penalty", "presence_penalty"]:
                    param_data = db_agent.reviewer_parameters.get(param_name, {})
                    value = param_data.get("work")
                    if value is not None:
                        reviewer_kwargs[param_name] = value
                    elif param_data.get("default") is not None:
                        reviewer_kwargs[param_name] = param_data["default"]

            reviewer_llm = self._get_llm(
                reviewer_model,
                [],
                reviewer_kwargs["temperature"],
                top_p=reviewer_kwargs["top_p"],
                top_k=reviewer_kwargs["top_k"],
                max_tokens=reviewer_kwargs["max_tokens"],
                frequency_penalty=reviewer_kwargs["frequency_penalty"],
                presence_penalty=reviewer_kwargs["presence_penalty"],
            )

        async def agent_node(state: AgentState, config: RunnableConfig):
            iteration = state.get("iteration", 0)

            await adispatch_custom_event(
                "status_update",
                {"status": f"🤖 {display_name} думает..."},
                config=config
            )

            messages = [SystemMessage(content=sys_prompt)] + state["messages"]

            await adispatch_custom_event(
                "status_update",
                {"status": f"🧠 {display_name} генерирует ответ..."},
                config=config
            )

            response = await agent_llm.ainvoke(messages)
            response = self._normalize_tool_calls(response)

            has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
            if has_tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                await adispatch_custom_event(
                    "status_update",
                    {"status": f"🔧 {display_name} → {', '.join(tool_names)}"},
                    config=config
                )

            update_dict = {"messages": [response]}
            if not has_tool_calls:
                update_dict["iteration"] = iteration + 1
                update_dict["reviewer_feedback"] = None
            return update_dict

        async def reviewer_node(state: AgentState, config: RunnableConfig):
            await adispatch_custom_event(
                "status_update",
                {"status": f"✅ Reviewer проверяет ответ {display_name}..."},
                config=config
            )

            last_message = state["messages"][-1]
            sys_prompt = (
                "Ты — строгий ревьюер. Проверь ответ на корректность, полноту и качество.\n"
                "Верни СТРОГО JSON: {\"is_approved\": true/false, \"feedback\": \"комментарий\"}"
            )

            messages = [SystemMessage(content=sys_prompt), HumanMessage(content=f"Проверь:\n{last_message.content}")]

            try:
                response = await reviewer_llm.ainvoke(messages)
                content = response.content.strip().strip("`").replace("json", "").strip()
                data = json.loads(content)

                is_approved = data.get("is_approved", False)
                feedback = data.get("feedback", "")

                if is_approved:
                    return {"is_approved": True}
                else:
                    return {
                        "is_approved": False,
                        "reviewer_feedback": f"REVIEWER REJECT: {feedback}. Исправь ошибки."
                    }
            except Exception as e:
                logger.warning(f"[Reviewer-dynamic] Parse/LLM error: {e}")
                return {
                    "is_approved": False,
                    "reviewer_feedback": "Ошибка проверки формата. Повтори ответ в корректном JSON-формате."
                }

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")

        if tools:
            workflow.add_node("tools", ToolNode(tools))
            workflow.add_edge("tools", "agent")

            def should_continue(state: AgentState):
                last_message = state["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    return "tools"
                return "reviewer" if is_two_agent else END

            workflow.add_conditional_edges("agent", should_continue)
        else:
            workflow.add_edge("agent", "reviewer" if is_two_agent else END)

        if is_two_agent:
            workflow.add_node("reviewer", reviewer_node)

            def route_reviewer(state: AgentState):
                if state.get("is_approved"):
                    return END
                iteration = state.get("iteration", 0)
                if iteration >= max_retries:
                    return END
                return "agent"

            workflow.add_conditional_edges("reviewer", route_reviewer)

        return workflow.compile()


_factory_instance = SubgraphFactory()


async def build_contour_graph(contour_name: str, agent_name: Optional[str] = None):
    selected_agent = await _factory_instance._select_agent_from_contour(
        contour=contour_name,
        task="",
        suggested_agent=agent_name
    )
    return await _factory_instance.build_agent_graph(selected_agent)
