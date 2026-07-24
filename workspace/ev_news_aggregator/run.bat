@echo off
REM Скрипт для запуска агрегатора новостей по тематике электромобилей в РФ (Windows)

echo Запуск агрегатора новостей...

REM Проверка наличия виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
    call venv\Scripts\activate
    echo Установка зависимостей...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Запуск агрегатора
python -m src.main %*

echo Агрегатор завершил работу.