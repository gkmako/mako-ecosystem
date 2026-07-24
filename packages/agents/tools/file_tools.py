# packages/agents/tools/file_tools.py
import os
import aiofiles
from pydantic import BaseModel, Field

# Базовая директория для безопасности (чтобы агент не читал /etc/passwd)
BASE_WORKSPACE = os.getenv("WORKSPACE_DIR", "/app/workspace")

class WriteFileSchema(BaseModel):
    path: str = Field(description="Относительный путь к файлу (например, 'src/main.py')")
    content: str = Field(description="Полное содержимое для записи в файл")

class ReadFileSchema(BaseModel):
    path: str = Field(description="Относительный путь к файлу для чтения")

async def write_file(path: str, content: str) -> str:
    """Сохраняет текст в файл на сервере."""
    full_path = os.path.realpath(os.path.join(BASE_WORKSPACE, path))
    base_dir = os.path.realpath(BASE_WORKSPACE)
    
    # Защита от Path Traversal
    if not full_path.startswith(base_dir):
        return "Ошибка безопасности: Попытка выхода за пределы рабочей директории."
        
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
        await f.write(content)
    return f"Файл успешно сохранен: {path}"

async def read_file(path: str) -> str:
    """Читает содержимое файла с сервера."""
    full_path = os.path.realpath(os.path.join(BASE_WORKSPACE, path))
    base_dir = os.path.realpath(BASE_WORKSPACE)
    
    # Защита от Path Traversal
    if not full_path.startswith(base_dir):
        return "Ошибка безопасности: Попытка выхода за пределы рабочей директории."
        
    if not os.path.exists(full_path):
        return f"Ошибка: Файл {path} не найден."
    
    async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
        content = await f.read()
    return content
