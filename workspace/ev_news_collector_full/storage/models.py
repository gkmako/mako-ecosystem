"""
Модуль с моделями данных.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class NewsArticle:
    """
    Модель новости.
    """
    title: str
    link: str
    summary: str
    published: str
    source: str