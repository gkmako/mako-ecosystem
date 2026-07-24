import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import argparse
from urllib.parse import quote_plus
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User-Agent для имитации браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Ключевые слова для поиска
DEFAULT_KEYWORDS = ['электромобиль', 'электромобили', 'EV', 'электрокар', 'Tesla', 'Ниссан', 'Renault', 'LADA']

def fetch_news_with_search(site, keyword, delay=1):
    """Получение новостей с сайта по ключевому слову"""
    try:
        time.sleep(delay)  # Задержка между запросами
        
        # Формирование URL для поиска (разные сайты имеют разные форматы)
        search_urls = {
            'ria': f'https://ria.ru/search/?query={quote_plus(keyword)}',
            'tass': f'https://tass.ru/search?searchStr={quote_plus(keyword)}',
            'rbc': f'https://www.rbc.ru/search?query={quote_plus(keyword)}&type=story'
        }
        
        url = search_urls.get(site)
        if not url:
            logger.warning(f"Неизвестный сайт: {site}")
            return []
        
        logger.info(f"Парсинг новостей по запросу '{keyword}' с {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Более гибкий подход к поиску заголовков новостей
        headlines = []
        
        # Попытка найти заголовки новостей по различным селекторам
        selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.news-item', '.article-title', '.news__item',
            '[class*="title"]', '[class*="headline"]',
            '.js-news-item-title', '.news-feed__item'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 10:  # Фильтрация коротких строк
                        headlines.append(text)
            except Exception as e:
                logger.debug(f"Ошибка при поиске по селектору {selector}: {e}")
                continue
        
        logger.info(f"Найдено {len(headlines)} заголовков на {site}")
        return list(set(headlines))  # Удаление дубликатов
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при получении данных с {site} по запросу '{keyword}': {e}")
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении данных с {site} по запросу '{keyword}': {e}")
        return []

def collect_news(keywords, delay=1):
    """Сбор новостей по списку ключевых слов"""
    all_news = []
    sites = ['ria', 'tass', 'rbc']
    
    for keyword in keywords:
        logger.info(f"Поиск новостей по ключевому слову: {keyword}")
        for site in sites:
            news = fetch_news_with_search(site, keyword, delay)
            all_news.extend(news)
    
    # Удаление дубликатов
    unique_news = list(set(all_news))
    logger.info(f"Всего найдено {len(unique_news)} уникальных новостей")
    return unique_news

def save_to_csv(news_data, filename='news.csv'):
    """Сохранение новостей в CSV файл"""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Дата', 'Заголовок'])
            for item in news_data:
                writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item])
        logger.info(f"Успешно сохранено {len(news_data)} новостей в {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Парсер новостей об электромобилях в РФ')
    parser.add_argument('--keywords', nargs='+', default=DEFAULT_KEYWORDS, 
                        help='Ключевые слова для поиска')
    parser.add_argument('--output', default='news.csv', 
                        help='Имя выходного файла')
    parser.add_argument('--delay', type=int, default=1, 
                        help='Задержка между запросами в секундах')
    
    args = parser.parse_args()
    
    logger.info("Начало сбора новостей...")
    news = collect_news(args.keywords, args.delay)
    
    if news:
        save_to_csv(news, args.output)
        logger.info(f"Сбор завершен. Найдено {len(news)} уникальных новостей.")
    else:
        logger.warning("Не удалось найти новости по заданным ключевым словам.")

if __name__ == "__main__":
    main()