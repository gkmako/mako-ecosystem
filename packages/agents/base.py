# packages/agents/base.py
import json
import uuid
from typing import AsyncGenerator, Callable, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from packages.shared.config import settings
from packages.shared.llm_profiles import SMART_PROFILE

class BaseAgent:
    def __init__(self, name: str, instructions: str, model: str, rag_dataset_ids: list[str] = None, llm_profile: dict | None = None):
        self.name = name
        self.instructions = instructions
        self.rag_dataset_ids = rag_dataset_ids or []
        
        profile = llm_profile if llm_profile is not None else SMART_PROFILE
        
        self.llm = ChatOpenAI(
            model=model,
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
            streaming=True,
            **profile
        )
        
        self.tools: dict[str, tuple[Callable, dict]] = {}

    def register_tool(self, func: Callable, schema: dict):
        """Регистрирует серверный инструмент."""
        self.tools[schema["function"]["name"]] = (func, schema)

    def _get_bound_llm(self, client_tools: list[dict] | None = None):
        """Возвращает LLM с привязанными инструментами (серверными + клиентскими)."""
        all_schemas = [schema for _, schema in self.tools.values()]
        if client_tools:
            all_schemas.extend(client_tools)
            
        if all_schemas:
            return self.llm.bind_tools(all_schemas)
        return self.llm

    async def run(self, prompt: str) -> str:
        """Синхронный (обычный) запуск для внутренних нужд и тестов."""
        messages = [SystemMessage(content=self.instructions), HumanMessage(content=prompt)]
        full_response = ""
        async for event in self.run_stream(messages):
            if event["type"] == "content":
                full_response += event["data"]
        return full_response

    async def run_stream(self, messages: list, client_tools: list[dict] | None = None) -> AsyncGenerator[dict, None]:
        """Стриминговый запуск с поддержкой ReAct (инструментов)."""
        
        # Конвертируем сообщения в LangChain объекты (если они еще не объекты)
        lc_messages = []
        for m in messages:
            # Если это уже LangChain объект, просто добавляем
            if isinstance(m, BaseMessage):
                lc_messages.append(m)
            # Если это словарь, конвертируем
            elif isinstance(m, dict):
                if m.get("role") == "system":
                    lc_messages.append(SystemMessage(content=m.get("content", "")))
                elif m.get("role") == "user":
                    lc_messages.append(HumanMessage(content=m.get("content", "")))
                elif m.get("role") == "assistant":
                    lc_messages.append(AIMessage(content=m.get("content") or "", tool_calls=m.get("tool_calls")))
                elif m.get("role") == "tool":
                    lc_messages.append(ToolMessage(content=m.get("content", ""), tool_call_id=m.get("tool_call_id", "")))
            else:
                print(f"[BaseAgent] Unknown message type: {type(m)}")

        if not lc_messages or not isinstance(lc_messages[0], SystemMessage):
            lc_messages.insert(0, SystemMessage(content=self.instructions))

        bound_llm = self._get_bound_llm(client_tools)
        max_iterations = 5

        for _ in range(max_iterations):
            collected_content = ""
            collected_tool_calls = []
            
            # Стриминг ответа от LLM
            async for chunk in bound_llm.astream(lc_messages):
                if chunk.content:
                    collected_content += chunk.content
                    yield {"type": "content", "data": chunk.content}
                
                if chunk.tool_call_chunks:
                    for tc_chunk in chunk.tool_call_chunks:
                        # Инициализация или дополнение tool_call
                        if tc_chunk.index is not None:
                            while len(collected_tool_calls) <= tc_chunk.index:
                                collected_tool_calls.append({"id": "", "name": "", "args": ""})
                            
                            if tc_chunk.id:
                                collected_tool_calls[tc_chunk.index]["id"] = tc_chunk.id
                            if tc_chunk.name:
                                collected_tool_calls[tc_chunk.index]["name"] += tc_chunk.name
                            if tc_chunk.args:
                                collected_tool_calls[tc_chunk.index]["args"] += tc_chunk.args

            # Формируем AIMessage для истории
            ai_msg = AIMessage(content=collected_content)
            
            if collected_tool_calls:
                # Форматируем для OpenAI API (чтобы отдать клиенту)
                formatted_tool_calls = []
                for idx, tc in enumerate(collected_tool_calls):
                    try:
                        args_dict = json.loads(tc["args"]) if tc["args"] else {}
                    except json.JSONDecodeError:
                        args_dict = {}
                        
                    formatted_tc = {
                        "index": idx,
                        "id": tc["id"] or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(args_dict, ensure_ascii=False)
                        }
                    }
                    formatted_tool_calls.append(formatted_tc)
                    
                    # Отдаем tool_calls клиенту (в Zed или Web UI)
                    yield {"type": "tool_calls", "data": formatted_tool_calls}
                    
                    # Добавляем в историю LangChain
                    ai_msg.tool_calls = [
                        {"name": tc["name"], "args": json.loads(tc["args"]) if tc["args"] else {}, "id": tc["id"]} 
                        for tc in collected_tool_calls
                    ]
                    lc_messages.append(ai_msg)
                    
                    # Выполняем ТОЛЬКО серверные инструменты
                    for tc in collected_tool_calls:
                        tool_name = tc["name"]
                        tool_id = tc["id"]
                        
                        if tool_name in self.tools:
                            func, _ = self.tools[tool_name]
                            try:
                                args = json.loads(tc["args"]) if tc["args"] else {}
                                # Инжектим dataset_ids для RAG
                                if tool_name == "search_knowledge_base":
                                    args["dataset_ids"] = self.rag_dataset_ids
                                    
                                result = await func(**args)
                            except Exception as e:
                                result = f"Ошибка выполнения: {str(e)}"
                                
                            lc_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
                        else:
                            # Это client_tool. Прерываем цикл.
                            return 
                            
                # Продолжаем цикл ReAct
                continue
            
            # Если tool_calls не было, значит агент дал финальный ответ
            break
