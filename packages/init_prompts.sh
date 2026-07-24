#!/bin/bash
BASE_DIR="/opt/makotools/code/makotools/packages/prompts"

echo "Создание структуры директорий..."
mkdir -p "$BASE_DIR/base"
mkdir -p "$BASE_DIR/agents"
mkdir -p "$BASE_DIR/reviewers/reviewer_checks"
mkdir -p "$BASE_DIR/profiles/development"
mkdir -p "$BASE_DIR/profiles/management"
mkdir -p "$BASE_DIR/profiles/business"

echo "Создание файлов-заглушек..."

# 1. Базовые шаблоны
touch "$BASE_DIR/base/base_developer.jinja2"
touch "$BASE_DIR/base/base_architect.jinja2"
touch "$BASE_DIR/base/base_business.jinja2"

# 2. Шаблоны агентов
touch "$BASE_DIR/agents/python_developer.jinja2"
touch "$BASE_DIR/agents/orchestrator.jinja2"
touch "$BASE_DIR/agents/architect.jinja2"
touch "$BASE_DIR/agents/sales_agent.jinja2"

# 3. Ревьюеры и чек-листы
touch "$BASE_DIR/reviewers/reviewer_generic.jinja2"
touch "$BASE_DIR/reviewers/reviewer_checks/code_quality.md"
touch "$BASE_DIR/reviewers/reviewer_checks/security.md"
touch "$BASE_DIR/reviewers/reviewer_checks/async_performance.md"
touch "$BASE_DIR/reviewers/reviewer_checks/architecture.md"
touch "$BASE_DIR/reviewers/reviewer_checks/pricing_accuracy.md"

# 4. YAML-профили
touch "$BASE_DIR/profiles/development/python_developer.yaml"
touch "$BASE_DIR/profiles/development/architect.yaml"
touch "$BASE_DIR/profiles/management/orchestrator.yaml"
touch "$BASE_DIR/profiles/business/sales_agent.yaml"

echo "✅ Готово! Структура создана в $BASE_DIR"
tree "$BASE_DIR" # Выведет дерево папок, если утилита tree установлена
