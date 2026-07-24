"""
Rule-based роутер — мгновенная маршрутизация (< 1ms) по regex-паттернам.
Используется ДО LLM Router для экономии времени и денег.
"""
import re
from typing import Optional, Tuple

# Порядок важен: проверяется сверху вниз, первое совпадение побеждает.
# Для кириллицы НЕ используем \b (нестабильно).

RULES: list[tuple[str, tuple[str, Optional[str]]]] = [
    # === Image контур (ВЫСОКИЙ ПРИОРИТЕТ) ===
    (r'(логотип|брендбук|фирменн\w*\s*стиль|айдентик|векторн)',
     ('image', 'brand_designer')),
    (r'(нарисуй|сгенерируй|создай|сделай)\s*(изображение|картинку|фото|иллюстрац|арт|баннер|иконк|персонаж|аватар|героя|сцену|пейзаж)',
     ('image', 'image_generator')),
    (r'(фотореалистичн|фотографи|портрет|продуктов\w*\s*фото|реалистичн\w*\s*изображ)',
     ('image', 'photo_generator')),
    (r'(нарисуй|сгенерируй|создай|сделай)\s*(видео|ролик|анимацию|клип)',
     ('image', 'video_generator')),

    # === Marketing контур ===
    (r'(маркетингов\w*\s*стратег|стратег\w*\s*маркетинг|продвижени|рекламн\w*\s*кампани|таргет|воронк\w*\s*продаж|маркетинг директор|SMM|SEO продвиж)',
     ('marketing', 'marketing_director')),

    # === Приветствия ===
    (r'\b(привет|здравствуй|hello|hi|добрый день|хай|ку|здарова|hello there)\b',
     ('management', 'orchestrator')),
    (r'(что ты умеешь|помощь|help|возможности|функции|кто ты|что можешь)',
     ('management', 'orchestrator')),

    # === Разработка ===
    (r'(напиши (код|функцию|скрипт|программу|endpoint|api)|'
     r'исправь (баг|ошибку)|'
     r'python|javascript|typescript|fastapi|django|flask|react|vue|'
     r'\bкод\b|\bпрограмма\b|\bфункция\b|\bскрипт\b)',
     ('development', 'python_developer')),
    (r'(сверстай|frontend|вёрстка|css|html|\bui\b|\bux\b|интерфейс|компонент)',
     ('development', 'frontend_developer')),
    (r'(docker|kubernetes|k8s|ci/cd|pipeline|deploy|nginx|devops|инфраструктур)',
     ('development', 'devops_engineer')),

    # === Архитектура ===
    (r'(база данных|\bбд\b|sql|postgresql|mysql|mongodb|redis|таблица|запрос sql)',
     ('architecture', 'database_architect')),
    (r'(спроектируй|архитектура|\bсистема\b|микросервис|проектирование|'
     r'high.?level|design doc|диаграмм)',
     ('architecture', 'system_architect')),

    # === Исследования ===
    (r'(проанализируй|исследуй|найди информацию|\bанализ\b|исследование|'
     r'обзор|сравни|benchmark|статистик)',
     ('research', 'web_research')),

    # === Бизнес ===
    (r'(бизнес.?план|\bкп\b|коммерческое предложение|продажи|'
     r'анализ рынка|конкурент|целевая аудитория|custdev)',
     ('business', 'business_analyst')),

    # === Контент ===
    (r'(напиши (статью|пост|текст|копирайт|контент)|'
     r'статья|пост|\bтекст\b|\bкопирайт\b|\bконтент\b|seo тек)',
     ('content', 'copywriter_agent')),

    # === Поддержка ===
    (r'(\bошибка\b|баг|не работает|проблема|помоги разобраться|incident|'
     r'инцидент|техподдержка|ticket)',
     ('support', 'support_agent')),

    # === AI / Промпты ===
    (r'(промпт|prompt|\bllm\b|нейросет|fine.?tuning|\brag\b|embedding)',
     ('ai_ops', 'prompt_engineer')),
]

_COMPILED_RULES = [(re.compile(pattern, re.IGNORECASE), target)
                   for pattern, target in RULES]


def rule_based_route(content: str) -> Optional[Tuple[str, Optional[str]]]:
    if not content or len(content) < 2:
        return None
    for pattern, target in _COMPILED_RULES:
        if pattern.search(content):
            return target
    return None
