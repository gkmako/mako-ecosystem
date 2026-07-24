#!/usr/bin/env python3
"""
Финальный тест для проверки работоспособности парсера новостей
"""

import subprocess
import sys
import os

def test_file_exists(filename):
    """Проверяет существование файла"""
    if os.path.exists(filename):
        print(f"✓ Файл {filename} существует")
        return True
    else:
        print(f"✗ Файл {filename} не найден")
        return False

def test_parser_execution():
    """Тестовый запуск парсера новостей"""
    try:
        print("Запуск парсера новостей с тестовыми параметрами...")
        # Тестовый запуск с минимальными параметрами
        result = subprocess.run([
            'python', 'ev_news_parser_enhanced.py', 
            '--pages', '1', 
            '--delay', '1'
        ], capture_output=True, text=True, timeout=60)
        
        print("Результаты теста:")
        print(f"Код возврата: {result.returncode}")
        if result.stdout:
            print("Вывод stdout:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)  # Ограничим вывод
        if result.stderr:
            print("Ошибки stderr:")
            print(result.stderr)
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Тест прерван по таймауту")
        return False
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        return False

def main():
    print("Финальная проверка компонентов проекта")
    print("=" * 40)
    
    # Проверка наличия всех необходимых файлов
    required_files = [
        "ev_news_parser_enhanced.py",
        "ev_market_analysis_2025.md",
        "README.md"
    ]
    
    all_files_exist = True
    for file in required_files:
        if not test_file_exists(file):
            all_files_exist = False
    
    if not all_files_exist:
        print("\nНекоторые файлы отсутствуют!")
        return False
    
    print("\nВсе файлы присутствуют.")
    
    # Проверка запуска парсера
    print("\nПроверка запуска парсера...")
    parser_works = test_parser_execution()
    
    if parser_works:
        print("\n✓ Парсер работает корректно")
    else:
        print("\n✗ Парсер не работает корректно")
    
    return parser_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)