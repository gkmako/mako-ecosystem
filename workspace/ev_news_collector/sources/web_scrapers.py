# sources/web_scrapers.py - Веб-скрапинг новостных сайтов

import requests
from bs4 import BeautifulSoup
import logging
from config import WEB_SOURCES, KEYWORDS

# Заголовки для обхода блокировок
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_rbc_news():
    """
    Скрапит новости с сайта auto.rbc.ru.
    Возвращает список словарей с новостями.
    """
    news_list = []
    try:
        response = requests.get('https://auto.rbc.ru/', headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Ищем статьи по классам или тегам, специфичным для RBC
        articles = soup.find_all('div', class_='item')
        for article in articles:
            title_tag = article.find('a', class_='item__title')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href', '')
            summary_tag = article.find('div', class_='item__text')
            summary = summary_tag.get_text(strip=True) if summary_tag else ''
            # Проверяем наличие ключевых слов
            if any(keyword.lower() in (title + summary).lower() for keyword in KEYWORDS):
                news_item = {
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'source': 'RBC Авто'
                }
                news_list.append(news_item)
    except Exception as e:
        logging.error(f'Ошибка при скрапинге RBC: {e}')
    return news_list

def fetch_kommersant_news():
    """
    Скрапит новости с сайта kommersant.ru/auto.
    Возвращает список словарей с новостями.
    """
    news_list = []
    try:
        response = requests.get('https://www.kommersant.ru/auto', headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Ищем статьи по классам или тегам, специфичным для Коммерсантъ
        articles = soup.find_all('article', class_='uho')
        for article in articles:
            title_tag = article.find('a', class_='uho__link')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = 'https://www.kommersant.ru' + title_tag.get('href', '')
            summary_tag = article.find('p', class_='uho__text')
            summary = summary_tag.get_text(strip=True) if summary_tag else ''
            # Проверяем наличие ключевых слов
            if any(keyword.lower() in (title + summary).lower() for keyword in KEYWORDS):
                news_item = {
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'source': 'Коммерсантъ Авто'
                }
                news_list.append(news_item)
    except Exception as e:
        logging.error(f'Ошибка при скрапинге Коммерсантъ: {e}')
    return news_list

def fetch_web_news():
    """
    Собирает новости со всех веб-источников.
    """
    all_news = []
    all_news.extend(fetch_rbc_news())
    all_news.extend(fetch_kommersant_news())
    return all_news