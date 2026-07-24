import re

path = '/opt/makotools/code/makotools/packages/agents/tools_registry.py'
with open(path, 'r') as f:
    code = f.read()

if 'memory_tools' in code:
    print("Уже добавлено!")
else:
    # 1. Добавляем импорты в начало файла
    imports = "from packages.agents.tools.memory_tools import save_to_memory, SaveMemorySchema, search_memory, SearchMemorySchema\n"
    code = imports + code
    
    # 2. Добавляем инструменты в словарь TOOLS_REGISTRY
    code = re.sub(
        r'(TOOLS_REGISTRY\s*=\s*\{)', 
        r'\1\n    "save_to_memory": (save_to_memory, SaveMemorySchema),\n    "search_memory": (search_memory, SearchMemorySchema),', 
        code
    )
    
    with open(path, 'w') as f:
        f.write(code)
    print("✅ Реестр успешно обновлен!")
