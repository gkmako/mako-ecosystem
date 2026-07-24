# packages/router/admin.py
from sqladmin import ModelView
from wtforms import SelectField, SelectMultipleField, TextAreaField
from packages.router.models import AgentDB
from packages.agents.tools_registry import TOOLS_REGISTRY

class AgentAdmin(ModelView, model=AgentDB):
    column_list = [
        AgentDB.id, AgentDB.name, AgentDB.display_name, 
        AgentDB.category, AgentDB.schema_type, 
        AgentDB.model_name, AgentDB.is_active
    ]
    form_columns = [
        AgentDB.name, AgentDB.display_name, AgentDB.category, AgentDB.schema_type,
        AgentDB.instructions, AgentDB.model_name, 
        AgentDB.reviewer_model_name, AgentDB.reviewer_instructions,
        AgentDB.allowed_tools, AgentDB.rag_dataset_ids, AgentDB.is_active
    ]

    name = "Агент"
    name_plural = "Агенты"
    icon = "fa-solid fa-robot"

    form_overrides = {
        "category": SelectField,
        "schema_type": SelectField,
        "allowed_tools": SelectMultipleField,
        "rag_dataset_ids": TextAreaField,
        "instructions": TextAreaField,
        "reviewer_instructions": TextAreaField,
    }

    form_args = {
        "category": {
            "choices": [
                ("management", "Управление"), ("research", "Исследования"),
                ("architecture", "Архитектура"), ("development", "Разработка"),
                ("business", "Бизнес"), ("content", "Контент"),
                ("support", "Поддержка"), ("ai_ops", "AI Ops"),
            ]
        },
        "schema_type": {
            "choices": [
                ("Одноагентная", "Одноагентная"),
                ("Двухагентная", "Двухагентная"),
                ("Сервисный", "Сервисный"),
            ]
        },
        "allowed_tools": {
            "choices": [(k, k) for k in TOOLS_REGISTRY.keys()]
        },
        "rag_dataset_ids": {
            "description": "Список ID датасетов RAGFlow в формате JSON (например: ['id1', 'id2'])"
        }
    }

    form_widget_args = {
        "instructions": {"rows": 10},
        "reviewer_instructions": {"rows": 5},
        "rag_dataset_ids": {"rows": 3},
        "allowed_tools": {"class": "form-select", "data-role": "select2", "multiple": True},
    }
