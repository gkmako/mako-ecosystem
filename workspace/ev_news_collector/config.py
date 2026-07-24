# config.py - Конфигурационный файл для сборщика новостей

# Список RSS-источников
RSS_SOURCES = [
    'https://auto.ru/rss/all/',
    'https://www.motor.ru/rss/all/',
    'https://www.zr.ru/rss/all/',
    'https://www.kolesa.ru/rss/news'
]

# URL для Google News по теме электромобилей в России
GOOGLE_NEWS_URL = 'https://news.google.com/rss/search?q=электромобиль+Россия&hl=ru&gl=RU&ceid=RU:ru'

# Список сайтов для веб-скрапинга
WEB_SOURCES = [
    'https://auto.rbc.ru/',
    'https://www.kommersant.ru/auto'
]

# Ключевые слова для фильтрации новостей
KEYWORDS = [
    'электромобиль', 'электрокар', 'EV', 'электроавтомобиль',
    'зарядная станция', 'электробус', 'Tesla', 'Zeekr', 'Avatr',
    'Voyah', 'Li Ideal', 'BYD', 'Evolute', 'Москвич', 'Атом', 'E-Neva'
]

# Путь к базе данных SQLite
DATABASE_PATH = 'news.db'

# Путь к файлу экспорта CSV
CSV_EXPORT_PATH = 'news_export.csv'