from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum

Base = declarative_base()

class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"      # История диалогов, решенные задачи
    SEMANTIC = "semantic"      # База знаний, факты, документация (RAG)
    PROCEDURAL = "procedural"  # Паттерны кода, успешные решения

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(Enum(MemoryType), nullable=False, index=True)
    content = Column(Text, nullable=False, comment="Текстовое содержимое памяти")
    
    # text-embedding-3-small выдает 1536 измерений — идеально для HNSW
    embedding = Column(Vector(1536), nullable=False, comment="Векторное представление")
    
    metadata_ = Column("metadata", JSONB, default=dict, comment="Дополнительные данные")
    agent_name = Column(String, index=True, comment="Какой агент создал эту память")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        # HNSW индекс для быстрого similarity search
        Index(
            'ix_memories_embedding_hnsw', 
            embedding, 
            postgresql_using='hnsw', 
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )
