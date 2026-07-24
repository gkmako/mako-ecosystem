# packages/agents/tools/__init__.py
import inspect
from typing import Any
from langchain_core.tools import StructuredTool

from .file_tools import read_file, write_file, ReadFileSchema, WriteFileSchema
from .rag_tools import search_knowledge_base, SearchKnowledgeBaseSchema
from .delegate_tool import delegate_to_agent, DelegateToAgentSchema
from .web_search import web_search, WebSearchSchema
from .generate_image import generate_image, GenerateImageSchema
from .generate_photo import generate_photo, GeneratePhotoSchema
from .generate_vector import generate_vector, GenerateVectorSchema
from .generate_video import generate_video, GenerateVideoSchema
from .edit_image import edit_image, EditImageSchema

try:
    from .memory_tools import search_memory, save_to_memory, SearchMemorySchema, SaveMemorySchema
    _HAS_MEMORY = True
except ImportError:
    _HAS_MEMORY = False

try:
    from .project_tools import get_project_structure, ProjectStructureSchema
    _HAS_PROJECT = True
except ImportError:
    _HAS_PROJECT = False


def _build_tool(name: str, func: Any, schema: Any, desc: str) -> StructuredTool:
    """Умная фабрика: сама определяет, sync функция или async."""
    kwargs = {
        "name": name,
        "description": desc,
        "args_schema": schema,
    }
    if inspect.iscoroutinefunction(func):
        kwargs["coroutine"] = func
    else:
        kwargs["func"] = func
    return StructuredTool.from_function(**kwargs)


def get_tool_by_name(name: str) -> Any:
    registry = {
        "read_file": (read_file, ReadFileSchema, "Читает содержимое файла по пути."),
        "write_file": (write_file, WriteFileSchema, "Создаёт или перезаписывает файл."),
        "search_knowledge_base": (search_knowledge_base, SearchKnowledgeBaseSchema, "Ищет в корпоративной базе знаний (RAG)."),
        "delegate_to_agent": (delegate_to_agent, DelegateToAgentSchema, "Делегирует задачу другому агенту."),
        "web_search": (web_search, WebSearchSchema, "Поиск актуальной информации в интернете через Perplexity Sonar."),
        "web_search": (web_search, WebSearchSchema, "Поиск актуальной информации в интернете через Perplexity."),
        "generate_image": (generate_image, GenerateImageSchema, "Генерация изображений (Recraft). Для баннеров, иллюстраций, артов."),
        "generate_photo": (generate_photo, GeneratePhotoSchema, "Генерация фотореалистичных изображений (Flux)."),
        "generate_vector": (generate_vector, GenerateVectorSchema, "Генерация векторной графики SVG (Recraft vector). Для логотипов, иконок."),
        "generate_video": (generate_video, GenerateVideoSchema, "Генерация коротких видео (Kling). 5-10 секунд."),
        "edit_image": (edit_image, EditImageSchema, "Редактирование существующего изображения (inpainting, style transfer)."),
    }
    
    if _HAS_MEMORY:
        registry["search_memory"] = (search_memory, SearchMemorySchema, "Ищет в долговременной памяти проекта.")
        registry["save_to_memory"] = (save_to_memory, SaveMemorySchema, "Сохраняет факт в память проекта.")
        
    if _HAS_PROJECT:
        registry["get_project_structure"] = (get_project_structure, ProjectStructureSchema, "Возвращает дерево файлов рабочей директории.")

    if name not in registry:
        raise ValueError(f"Инструмент '{name}' не зарегистрирован.")

    func, schema, desc = registry[name]
    return _build_tool(name, func, schema, desc)
