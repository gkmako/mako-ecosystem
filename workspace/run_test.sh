#!/bin/bash
echo "Установка зависимостей..."
pip install requests beautifulsoup4 >/dev/null 2>&1

echo "Запуск теста парсера..."
python test_parser.py