"""
Тестовый скрипт для проверки установки зависимостей.
"""
import sys
import importlib.util

def check_import(package_name):
    """Проверяет, можно ли импортировать пакет."""
    try:
        importlib.util.find_spec(package_name)
        print(f"✓ {package_name} - OK")
        return True
    except ImportError:
        print(f"✗ {package_name} - ОТСУТСТВУЕТ")
        return False

def main():
    print("Проверка установленных зависимостей...")
    
    required_packages = [
        "feedparser",
        "requests",
        "beautifulsoup4",
        "lxml",
        "httpx",
        "tenacity",
        "pydantic",
        "pydantic_settings",
        "loguru",
        "apscheduler",
        "pandas",
        "sqlite3"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if not check_import(package):
            missing_packages.append(package)
    
    print("\n" + "="*50)
    if missing_packages:
        print(f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их с помощью команды:")
        print("pip install -r requirements.txt")
        return 1
    else:
        print("Все зависимости установлены корректно!")
        return 0

if __name__ == "__main__":
    sys.exit(main())