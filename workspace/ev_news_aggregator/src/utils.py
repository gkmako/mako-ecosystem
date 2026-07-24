import re
from typing import List
from loguru import logger
from datetime import datetime


def filter_by_keywords(text: str, keywords: List[str]) -> bool:
    """
    Фильтрует текст по ключевым словам.
    
    Args:
        text (str): Текст для фильтрации
        keywords (List[str]): Список ключевых слов
        
    Returns:
        bool: True, если текст содержит хотя бы одно ключевое слово
    """
    if not text:
        return False
        
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def clean_text(text: str) -> str:
    """
    Очищает текст от лишних пробелов и специальных символов.
    
    Args:
        text (str): Исходный текст
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
        
    # Удаление лишних пробелов и переносов строк
    text = re.sub(r'\s+', ' ', text)
    # Удаление специальных символов в начале и конце
    text = text.strip()
    
    return text


def setup_logger(log_file_path: str):
    """
    Настраивает логгер.
    
    Args:
        log_file_path (str): Путь к файлу логов
    """
    logger.remove()  # Удалить стандартный handler
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        compression="zip"
    )
    logger.add(
        "logs/latest.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )


def get_current_time() -> str:
    """
    Возвращает текущее время в формате строки.
    
    Returns:
        str: Текущее время
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")