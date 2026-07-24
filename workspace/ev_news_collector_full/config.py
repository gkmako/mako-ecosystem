"""
Модуль конфигурации сборщика новостей.
Содержит настройки источников, ключевых слов, путей к файлам и параметров планировщика.
"""

# RSS-источники
RSS_SOURCES = [
    "https://avtonews.ru/rss",
    "https://www.autoreview.ru/rss/",
    "https://motor.ru/rss/",
    "https://www.zr.ru/rss/",
    "https://kolesa.ru/rss",
    # Дополнительные источники можно добавить здесь
]

# Веб-сайты для парсинга
WEB_SOURCES = [
    "https://rbc.ru/auto/",
    "https://www.kommersant.ru/auto",
    "https://www.vedomosti.ru/auto",
    "https://tass.ru/avtomobilnyj-ryнok",
]

# Google News RSS по ключевым словам
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q=электромобили+Россия&hl=ru&gl=RU&ceid=RU:ru"

# Ключевые слова для фильтрации
KEYWORDS = [
    "электромобиль",
    "электрокар",
    "EV",
    "электроавтомобиль",
    "зарядная станция",
    "электрогрузовик",
    "электробус",
    "батарея",
    "аккумулятор",
    "Tesla",
    "Zeekr",
    "Avatr",
    "Voyah",
    "Li Ideal",
    "BYD",
    "Evolute",
    "Москвич",
    "Атом",
    "E-Neva"
]

# Пути к файлам
DB_PATH = "news.db"
CSV_EXPORT_PATH = "news_digest.csv"

# Параметры планировщика (в минутах)
SCHEDULE_INTERVAL = 60  # Раз в час