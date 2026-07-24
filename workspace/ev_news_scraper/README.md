# EV News Scraper

Автоматизированный сборщик новостей по тематике рынка электромобилей в РФ.

## Описание

Сбор новостей из различных источников с сохранением в SQLite и экспортом в JSON/CSV.

## Источники

- autostat.ru
- drom.ru
- auto.ru
- Минпромторг РФ
- RSS-ленты (включая зарубежные с фильтрацией по РФ)

## Требования

- Python 3.11+
- Зависимости из requirements.txt

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Создайте `.env` файл на основе `.env.example`.

## Запуск

```bash
python -m src.pipeline
```

## Docker

```bash
docker-compose up --build
```