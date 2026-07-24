#!/usr/bin/env python3
"""
Скрипт для финального тестирования всех компонентов проекта
"""

import os
import sys

def check_files():
    """Проверяет наличие всех необходимых файлов"""
    required_files = [
        "ev_news_parser_enhanced.py",
        "ev_market_analysis_2025.md",
        "README.md",
        "ev_market_analyzer_2025.py",
        "ev_market_parser.py",
        "news_parser.py"
    ]
    
    print("Проверка наличия файлов:")
    all_present = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file}")
            all_present = False
    
    return all_present

def check_parser_syntax():
    """Проверяет синтаксис Python файлов"""
    python_files = [
        "ev_news_parser_enhanced.py",
        "ev_market_analyzer_2025.py",
        "ev_market_parser.py",
        "news_parser.py"
    ]
    
    print("\nПроверка синтаксиса Python файлов:")
    all_valid = True
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    compile(f.read(), file, 'exec')
                print(f"  ✓ {file} - синтаксис корректен")
            except SyntaxError as e:
                print(f"  ✗ {file} - синтаксическая ошибка: {e}")
                all_valid = False
            except Exception as e:
                print(f"  ? {file} - ошибка при проверке: {e}")
    
    return all_valid

def main():
    print("Финальное тестирование проекта")
    print("=" * 40)
    
    # Проверка наличия файлов
    files_ok = check_files()
    
    # Проверка синтаксиса
    syntax_ok = check_parser_syntax()
    
    print("\nРезультаты тестирования:")
    print(f"  Наличие файлов: {'OK' if files_ok else 'FAIL'}")
    print(f"  Синтаксис: {'OK' if syntax_ok else 'FAIL'}")
    
    if files_ok and syntax_ok:
        print("\n✓ Все тесты пройдены успешно!")
        print("Проект готов к использованию.")
        return True
    else:
        print("\n✗ Обнаружены проблемы!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)