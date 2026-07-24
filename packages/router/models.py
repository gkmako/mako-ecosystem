# packages/router/models.py
from sqlalchemy import Column, Integer, String, Boolean, JSON, Text, Float, DateTime
from sqlalchemy.sql import func
from .base import Base

class AgentDB(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, comment="Системное имя (например, python_developer)")
    display_name = Column(String, nullable=False, comment="Отображаемое имя для UI")
    instructions = Column(Text, nullable=False, comment="Системный промпт")
    model_name = Column(String, nullable=False, comment="Модель LLM (например, qwen/qwen3-coder)")
    
    allowed_tools = Column(JSON, default=list, comment="Список имен доступных серверных инструментов")
    rag_dataset_ids = Column(JSON, default=list, comment="Список ID датасетов RAGFlow для поиска")
    
    llm_parameters = Column(JSON, nullable=True)
    reviewer_parameters = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, comment="Включен ли агент")
    
    # Архитектура и схемы
    category = Column(String, nullable=True, comment="Контур (management, development, research и т.д.)")
    schema_type = Column(String, nullable=True, comment="Схема (Одноагентная, Двухагентная, Сервисный)")
    
    # Поля для ревьюера (используются, если schema_type == "Двухагентная")
    reviewer_model_name = Column(String, nullable=True, comment="Модель LLM для ревьюера")
    reviewer_instructions = Column(Text, nullable=True, comment="Системный промпт для ревьюера")

class LLMModelDB(Base):
    """Таблица моделей из RouterAI"""
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    context_length = Column(Integer, nullable=True)
    prompt_price = Column(Float, nullable=True)  # USD за 1M токенов
    completion_price = Column(Float, nullable=True)  # USD за 1M токенов
    supported_parameters = Column(JSON, nullable=True)
    provider = Column(String, nullable=True)      # Alibaba, Google, OpenAI...
    modalities = Column(JSON, nullable=True)      # ["text", "image", "audio", ...]
    hide_from_select = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ModelDefaultsDB(Base):
    """Дефолтные параметры моделей (наши настройки)"""
    __tablename__ = "model_defaults"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, unique=True, nullable=False, index=True)
    llm_parameters = Column(JSON, nullable=True)  # {temperature: {default, work}, top_p: ..., ...}
    reviewer_parameters = Column(JSON, nullable=True)  # аналогично
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromptDB(Base):
    """Системные промты (system.*, reviewer.*, chat.*)"""
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_key = Column(String, unique=True, nullable=False, index=True)
    prompt_type = Column(String, nullable=False)  # system, reviewer, chat
    content = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # True = нельзя удалить
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromptVersionDB(Base):
    """История версий промтов"""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_key = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    change_note = Column(String, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())    