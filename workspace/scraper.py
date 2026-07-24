import feedparser
import json
import logging

# Настройка логирования
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Список RSS-лент
RSS_FEEDS = [
    'https://www.autostat.ru/news/rss/',
    'https://www.zr.ru/rss/news/',
    'https://motor.ru/rss/news.xml',
    'https://www.drom.ru/rss/news.xml'
]

# Ключевые слова для фильтрации
KEYWORDS = ['электромобиль', 'электрокар', 'EV', 'зарядная станция', 'ЭЗС', 'электротранспорт', 'батарея']

# Функция для проверки наличия ключевых слов
def contains_keywords(text, keywords):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

# Функция для извлечения новостей
def fetch_news():
    all_news = []
    for feed_url in RSS_FEEDS:
        try:
            logging.info(f'Парсинг ленты: {feed_url}')
            feed = feedparser.parse(feed_url)
            
            # Проверка на ошибки парсинга
            if feed.bozo:
                logging.warning(f'Bozo ошибка при парсинге {feed_url}: {feed.bozo_exception}')
                continue

            source = feed.feed.title if 'title' in feed.feed else feed_url

            for entry in feed.entries:
                title = entry.title
                summary = entry.summary if 'summary' in entry else ''
                if contains_keywords(title, KEYWORDS) or contains_keywords(summary, KEYWORDS):
                    news_item = {
                        'title': title,
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': source,
                        'summary': summary
                    }
                    all_news.append(news_item)
        except Exception as e:
            logging.error(f'Ошибка при парсинге {feed_url}: {e}')
    return all_news

# Сохранение новостей в JSON
def save_news(news):
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)
    logging.info(f'Сохранено {len(news)} новостей в news.json')

# Основная функция
def main():
    logging.info('Начало сбора новостей')
    news = fetch_news()
    save_news(news)
    logging.info('Завершение сбора новостей')

if __name__ == '__main__':
    main()