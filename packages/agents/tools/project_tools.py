# packages/agents/tools/project_tools.py
import os
from pydantic import BaseModel, Field

BASE_WORKSPACE = os.getenv("WORKSPACE_DIR", "/app/workspace")

class ProjectStructureSchema(BaseModel):
    max_depth: int = Field(..., description="Максимальная глубина обхода директорий (целое число, например 3)")

async def get_project_structure(max_depth: int = 3) -> str:
    """Возвращает текстовое дерево файлов и папок текущей рабочей директории."""
    base_dir = os.path.realpath(BASE_WORKSPACE)
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        return f"Рабочая директория {base_dir} была пустой и только что создана."

    tree_lines = [f"Структура проекта ({base_dir}):"]
    ignore_dirs = {".venv", "node_modules", "__pycache__", ".git", ".idea", ".vscode"}
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
        
        level = root.replace(base_dir, '').count(os.sep)
        if level > max_depth:
            dirs[:] = []
            continue
            
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        tree_lines.append(f"{indent}{os.path.basename(root)}/")
        
        for i, file in enumerate(files):
            if file.startswith('.'): continue
            prefix = '└── ' if i == len(files) - 1 else '├── '
            tree_lines.append(f"{'│   ' * level}{prefix}{file}")
            
    return "\n".join(tree_lines)