import subprocess
import sys

def test_parser():
    """
    Тестовый запуск парсера новостей
    """
    try:
        # Тестовый запуск с минимальными параметрами
        result = subprocess.run([
            'python', 'ev_news_parser_enhanced.py', 
            '--pages', '1', 
            '--delay', '1',
            '--days-back', '365'
        ], capture_output=True, text=True, timeout=30)
        
        print("Скрипт выполнен успешно!")
        print(f"Код возврата: {result.returncode}")
        print(f"Вывод: {result.stdout}")
        if result.stderr:
            print(f"Ошибки: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Тест прерван по таймауту")
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")

if __name__ == "__main__":
    test_parser()