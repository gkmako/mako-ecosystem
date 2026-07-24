import time
import uuid
import json
import logging
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi import HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response
from contextlib import asynccontextmanager
from sqladmin import Admin
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy import text, inspect, select, func
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List

from packages.memory.database import memory_engine
from packages.memory.models import Base as MemoryBase
from packages.router.database import router_engine, sync_engine, router_async_session
from packages.router.models import Base, AgentDB, LLMModelDB, ModelDefaultsDB, PromptDB, PromptVersionDB
from packages.router.admin import AgentAdmin
from packages.router.chat_view import ChatView
from packages.router.openai_schemas import ChatCompletionRequest
from packages.router.seed import seed_agents, seed_model_defaults, seed_prompts
from packages.router.auth import require_admin
from packages.agents.tools_registry import TOOLS_REGISTRY
from packages.langgraph_app.graph import get_compiled_graph
from packages.shared.config import settings

from packages.router.base import Base
from packages.router.seed import DEFAULT_MODELS

# === RouterAI provider mapping ===
PROVIDER_MAP = {
    "qwen": "Alibaba",
    "deepseek": "DeepSeek",
    "google": "Google",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "x-ai": "xAI",
    "moonshotai": "Moonshot AI",
    "meta-llama": "Meta",
    "mistralai": "Mistral",
    "nvidia": "NVIDIA",
    "cohere": "Cohere",
    "perplexity": "Perplexity",
    "agentica": "Agentica",
    "ai21": "AI21",
    "aion-labs": "Aion Labs",
    "alfredpros": "AlfredPros",
    "allenai": "Allen AI",
    "alpindale": "Alpindale",
    "arcee-ai": "Arcee AI",
    "cognitivecomputations": "Cognitive",
    "elevenlabs": "ElevenLabs",
    "openrouter": "OpenRouter",
    "sao10k": "SAO10K",
    "thudm": "THUDM",
    "01-ai": "01.AI",
}

MODALITY_MAP = {
    ("text", "text"): "text",
    ("image", "text"): "image",
    ("text", "image"): "image",
    ("audio", "text"): "stt",
    ("text", "audio"): "tts",
    ("video", "text"): "video",
    ("text", "embedding"): "embedding",
    ("text", "rerank"): "rerank",
}

def detect_provider(model_id: str) -> str:
    prefix = model_id.split("/")[0] if "/" in model_id else ""
    return PROVIDER_MAP.get(prefix.lower(), prefix.capitalize() or "Other")

def detect_modalities(model: dict) -> list:
    """Возвращает список всех типов модели (для мультимодальных)"""
    arch = model.get("architecture", {})
    input_mods = arch.get("input_modalities", ["text"])
    output_mods = arch.get("output_modalities", ["text"])
    
    modalities = set()
    
    # Special cases
    if "embedding" in output_mods:
        modalities.add("embedding")
    if "rerank" in output_mods or "rerank" in model.get("name", "").lower():
        modalities.add("rerank")
    if "audio" in output_mods and "text" in input_mods:
        modalities.add("tts")
    if "text" in output_mods and "audio" in input_mods:
        modalities.add("stt")
    
    # Standard modalities
    for mod in input_mods:
        if mod in ["text", "image", "audio", "video"]:
            modalities.add(mod)
    for mod in output_mods:
        if mod in ["text", "image", "audio", "video"]:
            modalities.add(mod)
    
    # If nothing detected, default to text
    if not modalities:
        modalities.add("text")
    
    return sorted(list(modalities))

logger = logging.getLogger(__name__)


def convert_dict_to_message(msg_dict: dict) -> BaseMessage:
    role = msg_dict.get("role")
    content = msg_dict.get("content", "")
    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "system":
        return SystemMessage(content=content)
    else:
        return HumanMessage(content=content)


async def safe_migrate_and_seed():
    async with router_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def check_and_add_columns(connection):
            inspector = inspect(connection)
            # === Миграция llm_models ===
            if "llm_models" not in inspector.get_table_names():
                # Таблица создастся автоматически через Base.metadata.create_all
                pass
            
            # === Миграция model_defaults ===
            if "model_defaults" not in inspector.get_table_names():
                # Таблица создастся автоматически через Base.metadata.create_all
                pass
            if "agents" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("agents")]
                if "category" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN category VARCHAR"))
                if "schema_type" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN schema_type VARCHAR"))
                if "reviewer_model_name" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN reviewer_model_name VARCHAR"))
                if "reviewer_instructions" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN reviewer_instructions TEXT"))
                if "rag_dataset_ids" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN rag_dataset_ids JSON DEFAULT '[]'"))
                if "llm_parameters" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN llm_parameters JSON DEFAULT '{}'"))
                if "reviewer_parameters" not in columns:
                    connection.execute(text("ALTER TABLE agents ADD COLUMN reviewer_parameters JSON DEFAULT '{}'"))    
                # === Миграция prompts ===
                if "prompts" not in inspector.get_table_names():
                    pass  # создастся через Base.metadata.create_all
                if "prompt_versions" not in inspector.get_table_names():
                    pass  # создастся через Base.metadata.create_all

        await conn.run_sync(check_and_add_columns)

    async with router_async_session() as session:
        result = await session.execute(select(AgentDB.id).limit(1))
        if not result.first():
            logger.info("Таблица agents пуста. Запуск сидирования 36 агентов...")
            await seed_agents(session)
        await seed_model_defaults(session)
        await seed_prompts(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await safe_migrate_and_seed()
    async with memory_engine.begin() as conn:
        await conn.run_sync(MemoryBase.metadata.create_all)
    yield
    await memory_engine.dispose()
    await router_engine.dispose()


app = FastAPI(title="Makotools Router Service", version="1.0.0 (LangGraph)", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Статика для сгенерированных изображений
import os as _os
_generated_dir = "/app/workspace/generated"
if _os.path.exists(_generated_dir):
    app.mount("/static/generated", StaticFiles(directory=_generated_dir), name="generated")
    print(f"[Static] ✅ Mounted /static/generated → {_generated_dir}")


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

admin = Admin(app, sync_engine)
admin.add_view(AgentAdmin)
admin.add_view(ChatView)

langgraph_app = get_compiled_graph()


# === Health ===

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# === Models ===

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "makotools-router",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "makotools"
        }]
    }


# === Chat ===

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    last_user_msg = ""
    for m in reversed(request.messages):
        if m.role == "user":
            last_user_msg = m.content if isinstance(m.content, str) else " ".join(
                [b.get("text", "") for b in m.content if isinstance(b, dict)]
            )
            break

    if not last_user_msg:
        raise HTTPException(400, "No user message found")

    session_id = request.user or "default_session"
    raw_messages = [convert_dict_to_message(m.model_dump(exclude_none=True)) for m in request.messages]

    config = {
        "configurable": {"thread_id": session_id},
        "metadata": {"client_tools": request.tools},
        "recursion_limit": 50
    }

    chat_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())

    if request.stream:
        async def event_generator():
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': {'session_id': session_id}})}\n\n"
            yield f"data: {json.dumps({'id': chat_id, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': ''}, 'finish_reason': None}]})}\n\n"

            async for event in langgraph_app.astream_events({"messages": raw_messages}, config=config, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "stream_to_client" in tags:
                        content = event["data"]["chunk"].content
                        if content:
                            yield f"data: {json.dumps({'id': chat_id, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {'content': content}, 'finish_reason': None}]})}\n\n"
                elif event["event"] == "on_custom_event" and event.get("name") == "status_update":
                    status_text = event.get("data", {}).get("status", "")
                    if status_text:
                        yield f"data: {json.dumps({'type': 'status', 'status': status_text})}\n\n"

            yield f"data: {json.dumps({'id': chat_id, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        final_state = await langgraph_app.ainvoke({"messages": raw_messages}, config=config)
        last_msg = final_state["messages"][-1]
        return {
            "id": chat_id,
            "object": "chat.completion",
            "created": created,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": last_msg.content},
                "finish_reason": "stop"
            }]
        }


# === Dashboard API ===

SERVICES_TO_CHECK = [
    {"name": "PostgreSQL (pgvector)", "url": None, "type": "db"},
    {"name": "RAGFlow", "url": f"{settings.RAGFLOW_API_BASE}/datasets", "type": "http", "headers": {"Authorization": f"Bearer {settings.RAGFLOW_API_KEY}"}},
    {"name": "Qdrant", "url": "http://qdrant:6333/healthz", "type": "http"},
    {"name": "Keycloak", "url": "http://keycloak:8080/health/ready", "type": "http"},
    {"name": "Forgejo", "url": "http://forgejo:3000/api/v1/version", "type": "http"},
]


@app.get("/v1/dashboard/status")
async def dashboard_status():
    result = {}

    try:
        async with router_async_session() as session:
            agents_res = await session.execute(
                select(
                    AgentDB.name, AgentDB.display_name, AgentDB.category,
                    AgentDB.model_name, AgentDB.schema_type, AgentDB.is_active
                ).order_by(AgentDB.category, AgentDB.name)
            )
            agents = [dict(row._mapping) for row in agents_res]
            result["agents"] = agents
            result["agents_total"] = len(agents)
            result["agents_active"] = sum(1 for a in agents if a["is_active"])

            models_res = await session.execute(
                select(AgentDB.model_name, func.count(AgentDB.id))
                .where(AgentDB.is_active == True)
                .group_by(AgentDB.model_name)
            )
            result["models"] = [{"model": row[0], "count": row[1]} for row in models_res]

            # Reviewer модели (per-agent)
            reviewer_res = await session.execute(
                select(AgentDB.reviewer_model_name, func.count(AgentDB.id))
                .where(AgentDB.is_active == True, AgentDB.reviewer_model_name != None, AgentDB.reviewer_model_name != "")
                .group_by(AgentDB.reviewer_model_name)
            )
            result["reviewer_models"] = [{"model": row[0], "count": row[1]} for row in reviewer_res]

        result["database"] = {"status": "up"}
    except Exception as e:
        logger.error(f"Dashboard DB error: {e}")
        result["agents"] = []
        result["agents_total"] = 0
        result["agents_active"] = 0
        result["models"] = []
        result["categories"] = []
        result["database"] = {"status": "down"}

    services = []
    async with httpx.AsyncClient(timeout=5) as client:
        for svc in SERVICES_TO_CHECK:
            if svc["type"] == "db":
                services.append({"name": svc["name"], "status": result["database"]["status"]})
                continue
            try:
                headers = svc.get("headers", {})
                resp = await client.get(svc["url"], headers=headers)
                status = "up" if resp.status_code < 500 else "down"
            except Exception:
                status = "down"
            services.append({"name": svc["name"], "status": status})

    result["services"] = services
    result["llm"] = {"provider": "routerai.ru", "base_url": settings.LLM_API_BASE}
    result["memory"] = {"status": "not_connected", "note": "pgvector инициализирован, не подключен"}
    result["monitoring"] = {"status": "not_configured", "note": "LangSmith / Prometheus не настроены"}

    # Reviewer модели (per-agent)
    try:
        async with router_async_session() as session:
            reviewer_res = await session.execute(
                select(AgentDB.reviewer_model_name, func.count(AgentDB.id))
                .where(AgentDB.is_active == True, AgentDB.reviewer_model_name != None, AgentDB.reviewer_model_name != "")
                .group_by(AgentDB.reviewer_model_name)
            )
            result["reviewer_models"] = [{"model": row[0], "count": row[1]} for row in reviewer_res]
    except Exception as e:
        logger.warning(f"Dashboard reviewer_models error: {e}")
        result["reviewer_models"] = []

    # Системные (глобальные) модели
    result["system_models"] = [
        {"role": "ROUTER", "model": settings.ROUTERAI_ROUTER_MODEL, "description": "Классификация контура"},
        {"role": "FAST", "model": settings.ROUTERAI_FAST_MODEL, "description": "Выбор агента в контуре"},
        {"role": "SMART", "model": settings.ROUTERAI_SMART_MODEL, "description": "Сложные рассуждения"},
        {"role": "CODER", "model": settings.ROUTERAI_CODER_MODEL, "description": "Написание кода"},
        {"role": "REVIEWER", "model": getattr(settings, 'ROUTERAI_REVIEWER_MODEL', 'NONE'), "description": "Fallback ревьюера"},
        {"role": "EMBEDDING", "model": settings.ROUTERAI_EMBEDDING_MODEL, "description": "Векторизация / RAG"},
        {"role": "TTS", "model": getattr(settings, 'TTS_MODEL', 'NONE'), "description": "Озвучка текста"},
        {"role": "STT", "model": getattr(settings, 'STT_MODEL', 'NONE'), "description": "Распознавание речи"},
    ]
    return result


# === Audio: TTS ===

@app.post("/v1/audio/speech")
async def text_to_speech(request: dict):
    tts_model = settings.TTS_MODEL
    if tts_model == "NONE":
        raise HTTPException(501, "TTS model not configured")

    payload = {
        "model": tts_model,
        "input": request.get("input", ""),
        "voice": request.get("voice", "eve"),
        "response_format": request.get("response_format", "mp3"),
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.LLM_API_BASE}/audio/speech",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"TTS error: {resp.text[:200]}")
        return Response(content=resp.content, media_type="audio/mpeg")


# === Audio: STT ===

@app.post("/v1/audio/transcriptions")
async def speech_to_text(file: UploadFile = File(...)):
    stt_model = settings.STT_MODEL
    if stt_model == "NONE":
        raise HTTPException(501, "STT model not configured")

    audio_data = await file.read()

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.LLM_API_BASE}/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            files={"file": (file.filename or "audio.webm", audio_data, file.content_type or "audio/webm")},
            data={"model": stt_model},
        )
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"STT error: {resp.text[:200]}")
        return resp.json()


# === Admin Auth & CRUD ===

class AgentCreate(BaseModel):
    name: str
    display_name: str
    instructions: str
    model_name: str
    category: Optional[str] = None
    schema_type: Optional[str] = None
    allowed_tools: Optional[List[str]] = []
    rag_dataset_ids: Optional[List[str]] = []
    reviewer_model_name: Optional[str] = None
    reviewer_instructions: Optional[str] = None
    llm_parameters: Optional[dict] = {}  # ← добавить
    reviewer_parameters: Optional[dict] = {}  # ← добавить
    is_active: bool = True


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    instructions: Optional[str] = None
    model_name: Optional[str] = None
    category: Optional[str] = None
    schema_type: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    rag_dataset_ids: Optional[List[str]] = None
    reviewer_model_name: Optional[str] = None
    reviewer_instructions: Optional[str] = None
    llm_parameters: Optional[dict] = None  # ← добавить
    reviewer_parameters: Optional[dict] = None  # ← добавить
    is_active: Optional[bool] = None


@app.get("/v1/admin/tools")
async def admin_list_tools(_: dict = Depends(require_admin)):
    return {"tools": list(TOOLS_REGISTRY.keys())}


@app.get("/v1/admin/agents")
async def admin_list_agents(_: dict = Depends(require_admin)):
    async with router_async_session() as session:
        result = await session.execute(select(AgentDB).order_by(AgentDB.category, AgentDB.name))
        agents = result.scalars().all()
        return {
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "display_name": a.display_name,
                    "instructions": a.instructions,
                    "model_name": a.model_name,
                    "category": a.category,
                    "schema_type": a.schema_type,
                    "allowed_tools": a.allowed_tools or [],
                    "rag_dataset_ids": a.rag_dataset_ids or [],
                    "reviewer_model_name": a.reviewer_model_name,
                    "reviewer_instructions": a.reviewer_instructions,
                    "llm_parameters": a.llm_parameters or {},
                    "reviewer_parameters": a.reviewer_parameters or {},
                    "is_active": a.is_active,
                }
                for a in agents
            ]
        }


@app.post("/v1/admin/agents", status_code=201)
async def admin_create_agent(body: AgentCreate, _: dict = Depends(require_admin)):
    async with router_async_session() as session:
        existing = await session.execute(select(AgentDB).where(AgentDB.name == body.name))
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"Agent '{body.name}' already exists")
        agent = AgentDB(
            name=body.name,
            display_name=body.display_name,
            instructions=body.instructions,
            model_name=body.model_name,
            category=body.category,
            schema_type=body.schema_type,
            allowed_tools=body.allowed_tools,
            rag_dataset_ids=body.rag_dataset_ids,
            reviewer_model_name=body.reviewer_model_name,
            reviewer_instructions=body.reviewer_instructions,
            llm_parameters=body.llm_parameters,
            reviewer_parameters=body.reviewer_parameters,
            is_active=body.is_active,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        return {"id": agent.id, "name": agent.name}


@app.put("/v1/admin/agents/{agent_id}")
async def admin_update_agent(agent_id: int, body: AgentUpdate, _: dict = Depends(require_admin)):
    async with router_async_session() as session:
        result = await session.execute(select(AgentDB).where(AgentDB.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(404, "Agent not found")
        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        await session.commit()
        return {"id": agent.id, "name": agent.name, "updated": True}


@app.delete("/v1/admin/agents/{agent_id}")
async def admin_delete_agent(agent_id: int, _: dict = Depends(require_admin)):
    async with router_async_session() as session:
        result = await session.execute(select(AgentDB).where(AgentDB.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(404, "Agent not found")
        await session.delete(agent)
        await session.commit()
        return {"deleted": True, "name": agent.name}


@app.post("/v1/admin/reload")
async def admin_reload(_: dict = Depends(require_admin)):
    """Перечитать агентов из БД (без пересборки графа)."""
    logger.info("[Admin] Agent cache reload requested")
    return {"reloaded": True}

# === Admin: Models ===

@app.post("/v1/admin/models/sync")
async def admin_sync_models(_: dict = Depends(require_admin)):
    """Синхронизация моделей из RouterAI API"""
    from packages.router.models import LLMModelDB
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{settings.LLM_API_BASE}/models",
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            )
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, f"RouterAI API error: {resp.text[:200]}")
            data = resp.json()
    except Exception as e:
        raise HTTPException(502, f"Cannot fetch models from RouterAI: {e}")

    models_data = data.get("data", [])
    synced = 0
    new_count = 0
    updated_count = 0

    async with router_async_session() as session:
        for model in models_data:
            model_id = model.get("id")
            if not model_id:
                continue

            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", 0) * 1_000_000  # за 1M токенов
            completion_price = pricing.get("completion", 0) * 1_000_000

            result = await session.execute(
                select(LLMModelDB).where(LLMModelDB.model_id == model_id)
            )
            existing = result.scalar_one_or_none()

            provider = detect_provider(model_id)
            modalities = detect_modalities(model)

            if existing:
                existing.name = model.get("name")
                existing.description = model.get("description")
                existing.context_length = model.get("context_length")
                existing.prompt_price = prompt_price
                existing.completion_price = completion_price
                existing.supported_parameters = model.get("supported_parameters", [])
                existing.provider = provider
                existing.modalities = modalities
                updated_count += 1
            else:
                new_model = LLMModelDB(
                    model_id=model_id,
                    name=model.get("name"),
                    description=model.get("description"),
                    context_length=model.get("context_length"),
                    prompt_price=prompt_price,
                    completion_price=completion_price,
                    supported_parameters=model.get("supported_parameters", []),
                    hide_from_select=(model_id not in DEFAULT_MODELS),
                    provider=provider,
                    modalities=modalities,
                )
                session.add(new_model)
                new_count += 1

            if existing:
                existing.name = model.get("name")
                existing.description = model.get("description")
                existing.context_length = model.get("context_length")
                existing.prompt_price = prompt_price
                existing.completion_price = completion_price
                existing.supported_parameters = model.get("supported_parameters", [])
                updated_count += 1
            else:
                new_model = LLMModelDB(
                    model_id=model_id,
                    name=model.get("name"),
                    description=model.get("description"),
                    context_length=model.get("context_length"),
                    prompt_price=prompt_price,
                    completion_price=completion_price,
                    supported_parameters=model.get("supported_parameters", []),
                    hide_from_select=True,
                )
                session.add(new_model)
                new_count += 1
            synced += 1

        await session.commit()

    return {"synced": synced, "new": new_count, "updated": updated_count}


@app.get("/v1/admin/models")
async def admin_list_models(
    search: Optional[str] = None,
    hide_filter: Optional[str] = "all",  # all, visible, hidden
    _: dict = Depends(require_admin)
):
    """Список моделей с фильтрами"""
    from packages.router.models import LLMModelDB
    
    async with router_async_session() as session:
        query = select(LLMModelDB).order_by(LLMModelDB.name)
        
        if search:
            query = query.where(
                LLMModelDB.name.ilike(f"%{search}%") |
                LLMModelDB.model_id.ilike(f"%{search}%")
            )
        
        if hide_filter == "visible":
            query = query.where(LLMModelDB.hide_from_select == False)
        elif hide_filter == "hidden":
            query = query.where(LLMModelDB.hide_from_select == True)

        result = await session.execute(query)
        models = result.scalars().all()

        return {
            "models": [
                {
                    "id": m.id,
                    "model_id": m.model_id,
                    "name": m.name,
                    "description": m.description,
                    "context_length": m.context_length,
                    "prompt_price": m.prompt_price,
                    "completion_price": m.completion_price,
                    "supported_parameters": m.supported_parameters or [],
                    "hide_from_select": m.hide_from_select,
                    "provider": m.provider,
                    "modalities": m.modalities or ["text"],
                }
                for m in models
            ]
        }


@app.patch("/v1/admin/models/{model_id}")
async def admin_toggle_model_hide(model_id: int, _: dict = Depends(require_admin)):
    """Toggle hide_from_select для модели"""
    from packages.router.models import LLMModelDB
    
    async with router_async_session() as session:
        result = await session.execute(
            select(LLMModelDB).where(LLMModelDB.id == model_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(404, "Model not found")
        
        model.hide_from_select = not model.hide_from_select
        await session.commit()
        return {"id": model.id, "hide_from_select": model.hide_from_select}


@app.get("/v1/admin/models/select")
async def admin_models_for_select(_: dict = Depends(require_admin)):
    """Список моделей для select в форме агента (только видимые)"""
    from packages.router.models import LLMModelDB
    
    async with router_async_session() as session:
        result = await session.execute(
            select(LLMModelDB)
            .where(LLMModelDB.hide_from_select == False)
            .order_by(LLMModelDB.name)
        )
        models = result.scalars().all()

        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "name": m.name,
                    "prompt_price": m.prompt_price,
                    "completion_price": m.completion_price,
                    "supported_parameters": m.supported_parameters or [],
                }
                for m in models
            ]
        }


@app.get("/v1/admin/models/{model_id}/defaults")
async def admin_get_model_defaults(model_id: str, _: dict = Depends(require_admin)):
    """Получить дефолтные параметры модели"""
    from packages.router.models import ModelDefaultsDB
    
    async with router_async_session() as session:
        result = await session.execute(
            select(ModelDefaultsDB).where(ModelDefaultsDB.model_id == model_id)
        )
        defaults = result.scalar_one_or_none()
        
        if not defaults:
            # создать с дефолтами
            defaults = ModelDefaultsDB(
                model_id=model_id,
                llm_parameters={
                    "temperature": {"default": 0.1, "work": 0.1},
                    "top_p": {"default": None, "work": None},
                    "top_k": {"default": None, "work": None},
                    "max_tokens": {"default": None, "work": None},
                    "frequency_penalty": {"default": None, "work": None},
                    "presence_penalty": {"default": None, "work": None},
                },
                reviewer_parameters={
                    "temperature": {"default": 0.0, "work": 0.0},
                    "top_p": {"default": None, "work": None},
                    "top_k": {"default": None, "work": None},
                    "max_tokens": {"default": None, "work": None},
                    "frequency_penalty": {"default": None, "work": None},
                    "presence_penalty": {"default": None, "work": None},
                },
            )
            session.add(defaults)
            await session.commit()
            await session.refresh(defaults)

        return {
            "model_id": defaults.model_id,
            "llm_parameters": defaults.llm_parameters,
            "reviewer_parameters": defaults.reviewer_parameters,
        }


@app.put("/v1/admin/models/{model_id}/defaults")
async def admin_update_model_defaults(model_id: str, body: dict, _: dict = Depends(require_admin)):
    """Обновить дефолтные параметры модели"""
    from packages.router.models import ModelDefaultsDB
    
    async with router_async_session() as session:
        result = await session.execute(
            select(ModelDefaultsDB).where(ModelDefaultsDB.model_id == model_id)
        )
        defaults = result.scalar_one_or_none()
        
        if not defaults:
            defaults = ModelDefaultsDB(model_id=model_id)
            session.add(defaults)
        
        defaults.llm_parameters = body.get("llm_parameters", {})
        defaults.reviewer_parameters = body.get("reviewer_parameters", {})
        await session.commit()
        
        return {"updated": True}    

# === Admin: Prompts ===

@app.get("/v1/admin/prompts")
async def admin_list_prompts(
    prompt_type: Optional[str] = None,
    _: dict = Depends(require_admin)
):
    """Список промтов с фильтрами"""
    async with router_async_session() as session:
        query = select(PromptDB).order_by(PromptDB.prompt_type, PromptDB.prompt_key)
        if prompt_type:
            query = query.where(PromptDB.prompt_type == prompt_type)
        result = await session.execute(query)
        prompts = result.scalars().all()
        return {
            "prompts": [
                {
                    "id": p.id,
                    "prompt_key": p.prompt_key,
                    "prompt_type": p.prompt_type,
                    "content": p.content,
                    "description": p.description,
                    "version": p.version,
                    "is_active": p.is_active,
                    "is_system": p.is_system,
                }
                for p in prompts
            ]
        }


@app.get("/v1/admin/prompts/{prompt_key}")
async def admin_get_prompt(prompt_key: str, _: dict = Depends(require_admin)):
    """Получить промт по ключу"""
    async with router_async_session() as session:
        result = await session.execute(
            select(PromptDB).where(PromptDB.prompt_key == prompt_key)
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise HTTPException(404, "Prompt not found")
        return {
            "id": prompt.id,
            "prompt_key": prompt.prompt_key,
            "prompt_type": prompt.prompt_type,
            "content": prompt.content,
            "description": prompt.description,
            "version": prompt.version,
            "is_active": prompt.is_active,
            "is_system": prompt.is_system,
        }


@app.get("/v1/admin/prompts/{prompt_key}/versions")
async def admin_get_prompt_versions(prompt_key: str, _: dict = Depends(require_admin)):
    """История версий промта"""
    async with router_async_session() as session:
        result = await session.execute(
            select(PromptVersionDB)
            .where(PromptVersionDB.prompt_key == prompt_key)
            .order_by(PromptVersionDB.version.desc())
        )
        versions = result.scalars().all()
        return {
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "content": v.content,
                    "change_note": v.change_note,
                    "changed_at": v.changed_at.isoformat() if v.changed_at else None,
                }
                for v in versions
            ]
        }


@app.post("/v1/admin/prompts", status_code=201)
async def admin_create_prompt(body: dict, _: dict = Depends(require_admin)):
    """Создать новый промт"""
    prompt_key = body.get("prompt_key", "").strip()
    if not prompt_key:
        raise HTTPException(400, "prompt_key is required")

    async with router_async_session() as session:
        existing = await session.execute(
            select(PromptDB).where(PromptDB.prompt_key == prompt_key)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"Prompt '{prompt_key}' already exists")

        prompt = PromptDB(
            prompt_key=prompt_key,
            prompt_type=body.get("prompt_type", "system"),
            content=body.get("content", ""),
            description=body.get("description", ""),
            is_system=False,
            version=1,
            is_active=True,
        )
        session.add(prompt)
        await session.commit()
        await session.refresh(prompt)

        # Reload cache
        _reload_prompt_cache()

        return {"id": prompt.id, "prompt_key": prompt.prompt_key}


@app.put("/v1/admin/prompts/{prompt_key}")
async def admin_update_prompt(prompt_key: str, body: dict, _: dict = Depends(require_admin)):
    """Обновить промт (с сохранением версии)"""
    async with router_async_session() as session:
        result = await session.execute(
            select(PromptDB).where(PromptDB.prompt_key == prompt_key)
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise HTTPException(404, "Prompt not found")

        new_content = body.get("content", prompt.content)
        change_note = body.get("change_note", "")

        # Сохранить старую версию
        if new_content != prompt.content:
            old_version = PromptVersionDB(
                prompt_key=prompt_key,
                version=prompt.version,
                content=prompt.content,
                change_note=change_note or f"Auto-saved before v{prompt.version + 1}",
            )
            session.add(old_version)
            prompt.version += 1

        prompt.content = new_content
        if "description" in body:
            prompt.description = body["description"]
        if "is_active" in body:
            prompt.is_active = body["is_active"]

        await session.commit()

        # Удалить старые версии (оставить 50)
        await session.execute(
            text(f"""
                DELETE FROM prompt_versions 
                WHERE prompt_key = :key AND id NOT IN (
                    SELECT id FROM prompt_versions 
                    WHERE prompt_key = :key 
                    ORDER BY version DESC LIMIT 50
                )
            """),
            {"key": prompt_key}
        )
        await session.commit()

        # Reload cache
        _reload_prompt_cache()

        return {"prompt_key": prompt_key, "version": prompt.version, "updated": True}


@app.delete("/v1/admin/prompts/{prompt_key}")
async def admin_delete_prompt(prompt_key: str, _: dict = Depends(require_admin)):
    """Удалить промт (только пользовательские)"""
    async with router_async_session() as session:
        result = await session.execute(
            select(PromptDB).where(PromptDB.prompt_key == prompt_key)
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise HTTPException(404, "Prompt not found")
        if prompt.is_system:
            raise HTTPException(403, "Cannot delete system prompts")

        await session.delete(prompt)
        await session.execute(
            text("DELETE FROM prompt_versions WHERE prompt_key = :key"),
            {"key": prompt_key}
        )
        await session.commit()

        _reload_prompt_cache()

        return {"deleted": True, "prompt_key": prompt_key}


@app.post("/v1/admin/prompts/{prompt_key}/rollback")
async def admin_rollback_prompt(prompt_key: str, body: dict, _: dict = Depends(require_admin)):
    """Откатить промт к указанной версии"""
    target_version = body.get("version")
    if not target_version:
        raise HTTPException(400, "version is required")

    async with router_async_session() as session:
        # Найти версию
        result = await session.execute(
            select(PromptVersionDB)
            .where(PromptVersionDB.prompt_key == prompt_key, PromptVersionDB.version == target_version)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(404, f"Version {target_version} not found")

        # Обновить текущий промт
        prompt_result = await session.execute(
            select(PromptDB).where(PromptDB.prompt_key == prompt_key)
        )
        prompt = prompt_result.scalar_one_or_none()
        if not prompt:
            raise HTTPException(404, "Prompt not found")

        # Сохранить текущую версию
        old_version = PromptVersionDB(
            prompt_key=prompt_key,
            version=prompt.version,
            content=prompt.content,
            change_note=f"Before rollback to v{target_version}",
        )
        session.add(old_version)

        prompt.content = version.content
        prompt.version += 1
        await session.commit()

        _reload_prompt_cache()

        return {"prompt_key": prompt_key, "version": prompt.version, "rolled_back_to": target_version}


@app.post("/v1/admin/prompts/reload")
async def admin_reload_prompts(_: dict = Depends(require_admin)):
    """Перезагрузить кэш промтов"""
    _reload_prompt_cache()
    return {"reloaded": True}


def _reload_prompt_cache():
    """Перезагрузить кэш промтов в PromptBuilder"""
    try:
        from packages.langgraph_app.prompt_builder import PromptBuilder
        PromptBuilder.reload_cache()
        logger.info("[Admin] Prompt cache reloaded")
    except Exception as e:
        logger.warning(f"[Admin] Failed to reload prompt cache: {e}")        


# === Frontend (должен быть последним) ===

app.mount("/", StaticFiles(directory="/app/frontend/dist", html=True), name="frontend")

@app.get("/api/download/{filename}")
async def download_generated_file(filename: str):
    """Скачивание сгенерированного файла."""
    import os
    filepath = f"/app/workspace/generated/{filename}"
    if not os.path.exists(filepath):
        return {"error": "File not found"}
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )
