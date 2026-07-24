#!/bin/bash

# Скрипт для запуска агрегатора новостей по тематике электромобилей в РФ

echo "Запуск агрегатора новостей..."

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Установка зависимостей..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Запуск агрегатора
python -m src.main "$@"

echo "Агрегатор завершил работу."