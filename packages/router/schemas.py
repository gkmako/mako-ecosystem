from pydantic import BaseModel, field_validator
from typing import Optional

class RoutingDecision(BaseModel):
    category: str
    assigned_agent: str
    reasoning: Optional[str] = ""

    @field_validator('category', mode='before')
    @classmethod
    def validate_category(cls, v):
        """Приводим неизвестные категории к 'unknown'"""
        allowed = ['development', 'sales', 'architecture', 'research', 'unknown']
        return v if v in allowed else 'unknown'

class TaskSubmitRequest(BaseModel):
    prompt: str
