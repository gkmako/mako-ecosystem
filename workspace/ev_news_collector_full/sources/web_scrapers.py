"""
Модуль для парсинга новостных сайтов.
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
from fake_useragent import UserAgent
from config import WEB_SOURCES, KEYWORDS
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация UserAgent
ua = UserAgent()

def fetch_web_articles() -> List[Dict]:
    """
    Парсит новости с веб-сайтов.
    
    Returns:
        List[Dict]: Список словарей с данными статей.
    """
    articles = []
    
    for url in WEB_SOURCES:
        try:
            # Используем случайный User-Agent для обхода блокировок
            headers = {'User-Agent': ua.random}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Поиск заголовков статей (пример, может потребоваться адаптация под каждый сайт)
            # Это упрощенный пример, в реальности может потребоваться более точная настройка
            headlines = soup.find_all(['h1', 'h2', 'h3'], limit=20)
            
            for headline in headlines:
                title = headline.get_text(strip=True)
                link = headline.find_parent('a')['href'] if headline.find_parent('a') else ''
                
                # Приведение ссылки к абсолютному виду
                if link and not link.startswith('http'):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)
                
                # Проверка на наличие ключевых слов
                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    articles.append({
                        'title': title,
                        'link': link,
                        'summary': '',  # Веб-скрапинг может не давать краткого содержания
                        'published': '',  # Дата может отсутствовать при парсинге
                        'source': 'web'
                    })
                    
            # Пауза между запросами
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге сайта {url}: {e}")
    
    logger.info(f"Собрано {len(articles)} статей с веб-сайтов.")
    return articles