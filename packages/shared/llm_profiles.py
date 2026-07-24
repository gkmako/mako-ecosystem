# packages/shared/llm_profiles.py
"""
Профили параметров сэмплирования для RouterAI.
Используются для распаковки в ChatOpenAI(**PROFILE).
"""

# Для роутеров и ревьюеров. Критичен детерминизм.
ROUTER_PROFILE = {
    "temperature": 0.0,
    "top_p": 0.1,
}

# Для написания кода. Минимальная вариативность.
CODER_PROFILE = {
    "temperature": 0.2,
    "top_p": 0.9,
}

# Для сложных рассуждений, архитектуры, анализа.
SMART_PROFILE = {
    "temperature": 0.4,
    "top_p": 0.9,
}

# Для быстрых ответов, small-talk и fallback.
FAST_PROFILE = {
    "temperature": 0.7,
    "top_p": 0.95,
}
