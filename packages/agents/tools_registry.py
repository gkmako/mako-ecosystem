# packages/agents/tools_registry.py
from pydantic import BaseModel
from packages.agents.tools.memory_tools import save_to_memory, SaveMemorySchema, search_memory, SearchMemorySchema
from packages.agents.tools.web_search import web_search, WebSearchSchema
from packages.agents.developer import get_project_structure, get_project_structure_schema
from packages.agents.sales import get_company_rate, get_company_rate_schema
from packages.agents.architect import check_tech_compatibility, check_tech_compatibility_schema
from packages.agents.tools.rag_tools import search_knowledge_base, SearchKnowledgeBaseSchema
from packages.agents.tools.file_tools import write_file, WriteFileSchema, read_file, ReadFileSchema

def pydantic_to_openai_schema(model, name: str, description: str) -> dict:
    """Универсальный конвертер: принимает Pydantic модель или готовый dict."""
    
    # 1. Если это уже готовый словарь (старый формат)
    if isinstance(model, dict):
        if "type" in model and "function" in model:
            return model  # Уже полностью готовая OpenAI схема
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": model
            }
        }
        
    # 2. Если это Pydantic v2 модель
    if hasattr(model, "model_json_schema"):
        schema = model.model_json_schema()
        schema.pop("title", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": schema
            }
        }
        
    raise ValueError(f"Неподдерживаемый тип схемы для {name}: {type(model)}")

# Глобальный реестр: name -> (callable, openai_schema_dict)
TOOLS_REGISTRY = {
    "save_to_memory": (save_to_memory, pydantic_to_openai_schema(SaveMemorySchema, "save_to_memory", "Сохранить важный факт в долговременную память")),
    "search_memory": (search_memory, pydantic_to_openai_schema(SearchMemorySchema, "search_memory", "Найти факты в долговременной памяти")),
    "web_search": (web_search, pydantic_to_openai_schema(WebSearchSchema, "web_search", "Найти актуальную информацию в интернете")),
    "get_project_structure": (get_project_structure, get_project_structure_schema),
    "get_company_rate": (get_company_rate, get_company_rate_schema),
    "check_tech_compatibility": (check_tech_compatibility, check_tech_compatibility_schema),
    "search_knowledge_base": (search_knowledge_base, pydantic_to_openai_schema(SearchKnowledgeBaseSchema, "search_knowledge_base", "Поиск по внутренней базе знаний компании (RAG)")),
    "write_file": (write_file, pydantic_to_openai_schema(WriteFileSchema, "write_file", "Создать или перезаписать файл на сервере")),
    "read_file": (read_file, pydantic_to_openai_schema(ReadFileSchema, "read_file", "Прочитать содержимое файла с сервера")),
}
