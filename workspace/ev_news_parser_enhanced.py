#!/usr/bin/env python3
"""
Парсер новостей по теме электромобилей в России 2025 года
Собирает новости с различных источников и проводит анализ
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
from datetime import datetime, timedelta
import time
import argparse
from urllib.parse import urljoin, urlparse
import sys

# Конфигурация источников новостей
NEWS_SOURCES = {
    "ria": {
        "base_url": "https://ria.ru/search/",
        "search_param": "q",
        "page_param": "page",
        "title_selector": "a.search-item__title",
        "date_selector": "span.search-item__date",
        "container_selector": "div.search-item"
    },
    "tass": {
        "base_url": "https://tass.ru/search",
        "search_param": "q",
        "page_param": "page",
        "title_selector": "a.search-item__title",
        "date_selector": "span.search-item__date",
        "container_selector": "div.search-item"
    }
}

# Ключевые слова для фильтрации новостей
KEYWORDS = [
    'электромобиль', 'электромобили', 'EV', 'электрокар', 'Tesla', 'Lada', 'Ниссан', 
    'Renault', 'зарядка', 'батарея', 'аккумулятор', 'зарядная станция', 'инфраструктура',
    'субсидии', 'госпрограмма', 'экология', 'zero emission', 'электротранспорт'
]

def validate_url(url):
    """Проверяет, является ли строка корректным URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def parse_date(date_string):
    """Пытается распарсить дату из строки"""
    try:
        # Попытка распознать различные форматы дат
        date_patterns = [
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for pattern in date_patterns:
            try:
                return datetime.strptime(date_string, pattern)
            except ValueError:
                continue
                
        return None
    except:
        return None

def fetch_news_from_source(source_name, query, pages=3, delay=1):
    """
    Парсит новости с указанного источника
    
    :param source_name: Название источника из NEWS_SOURCES
    :param query: Поисковый запрос
    :param pages: Количество страниц для парсинга
    :param delay: Задержка между запросами в секундах
    :return: Список новостей
    """
    if source_name not in NEWS_SOURCES:
        print(f"Источник {source_name} не найден в конфигурации")
        return []
    
    source_config = NEWS_SOURCES[source_name]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    news_data = []
    
    for page in range(pages):
        params = {
            source_config["search_param"]: query,
            source_config["page_param"]: page + 1
        }
        
        try:
            response = requests.get(
                source_config["base_url"], 
                params=params, 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('div', class_='search-item')
                
                for item in news_items:
                    # Извлечение заголовка
                    title_elem = item.find('a', class_='search-item__title')
                    title = title_elem.text.strip() if title_elem else "N/A"
                    link = title_elem['href'] if title_elem and title_elem.get('href') else "N/A"
                    
                    # Коррекция относительных ссылок
                    if link != "N/A" and not link.startswith('http'):
                        link = urljoin(source_config["base_url"], link)
                    
                    # Извлечение даты
                    date_elem = item.find('span', class_='search-item__date')
                    date = date_elem.text.strip() if date_elem else "N/A"
                    
                    # Фильтрация по ключевым словам
                    if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                        news_data.append({
                            "title": title,
                            "link": link,
                            "date": date,
                            "source": source_name.upper(),
                            "query": query
                        })
            else:
                print(f"Ошибка при запросе к {source_name}: {response.status_code}")
                
        except Exception as e:
            print(f"Ошибка при парсинге {source_name}: {e}")
            
        # Пауза между запросами
        time.sleep(delay)
    
    return news_data

def filter_news_by_date(news_data, days_back=365):
    """
    Фильтрует новости по дате (за последние days_back дней)
    
    :param news_data: Список новостей
    :param days_back: Количество дней назад для фильтрации
    :return: Отфильтрованный список новостей
    """
    if days_back <= 0:
        return news_data
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    filtered_news = []
    
    for item in news_data:
        # Попытка распарсить дату из строки
        item_date = parse_date(item.get('date', ''))
        if item_date and item_date >= cutoff_date:
            filtered_news.append(item)
        elif not item_date:  # Если дату не удалось распарсить, оставляем новость
            filtered_news.append(item)
    
    return filtered_news

def save_to_csv(data, filename):
    """
    Сохраняет данные в CSV файл
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'link', 'date', 'source', 'query']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def save_to_json(data, filename):
    """
    Сохраняет данные в JSON файл
    """
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=2)

def analyze_news_trends(news_data):
    """
    Проводит анализ собранных новостей
    """
    print("\n=== АНАЛИЗ НОВОСТЕЙ ПО ТЕМЕ ЭЛЕКТРОМОБИЛЕЙ В РФ ===")
    print(f"Всего найдено новостей: {len(news_data)}")
    
    if not news_data:
        print("Нет данных для анализа")
        return
    
    # Подсчет новостей по источникам
    source_count = {}
    for item in news_data:
        source = item.get('source', 'Unknown')
        source_count[source] = source_count.get(source, 0) + 1
    
    print("\nНовости по источникам:")
    for source, count in source_count.items():
        print(f"  {source}: {count}")
    
    # Анализ ключевых слов
    keyword_frequency = {}
    for item in news_data:
        title = item.get('title', '').lower()
        for keyword in KEYWORDS:
            if keyword.lower() in title:
                keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
    
    print("\nЧастота ключевых слов в заголовках:")
    # Сортировка по частоте упоминания
    sorted_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)
    for keyword, count in sorted_keywords[:10]:  # Показываем топ-10
        if count > 0:
            print(f"  {keyword}: {count}")
    
    # Анализ по датам (если возможно)
    dates = [item.get('date', '') for item in news_data if item.get('date') != 'N/A']
    if dates:
        print(f"\nДиапазон дат: {min(dates)} - {max(dates)}")

def main():
    parser = argparse.ArgumentParser(description='Парсер новостей по теме электромобилей в РФ')
    parser.add_argument('--query', type=str, default='электромобили Россия 2025', 
                        help='Поисковый запрос')
    parser.add_argument('--pages', type=int, default=3, 
                        help='Количество страниц для парсинга')
    parser.add_argument('--delay', type=int, default=1, 
                        help='Задержка между запросами в секундах')
    parser.add_argument('--days-back', type=int, default=365, 
                        help='Фильтрация новостей за последние N дней')
    parser.add_argument('--format', type=str, choices=['csv', 'json', 'both'], default='csv',
                        help='Формат выходного файла')
    
    args = parser.parse_args()
    
    print(f"Парсинг новостей по запросу: {args.query}")
    
    # Сбор новостей с разных источников
    all_news = []
    
    for source_name in NEWS_SOURCES.keys():
        print(f"\nПарсинг {source_name.upper()}...")
        news = fetch_news_from_source(source_name, args.query, args.pages, args.delay)
        all_news.extend(news)
    
    # Фильтрация по дате
    if args.days_back > 0:
        print(f"\nФильтрация новостей за последние {args.days_back} дней...")
        all_news = filter_news_by_date(all_news, args.days_back)
    
    # Анализ собранных данных
    analyze_news_trends(all_news)
    
    # Сохранение данных
    current_date = datetime.now().strftime("%Y-%m-%d")
    base_filename = f"ev_news_russia_2025_{current_date}"
    
    if args.format in ['csv', 'both']:
        csv_filename = f"{base_filename}.csv"
        save_to_csv(all_news, csv_filename)
        print(f"\nДанные в формате CSV сохранены в файл: {csv_filename}")
    
    if args.format in ['json', 'both']:
        json_filename = f"{base_filename}.json"
        save_to_json(all_news, json_filename)
        print(f"Данные в формате JSON сохранены в файл: {json_filename}")
    
    # Вывод первых 5 новостей
    print("\nПервые 5 новостей:")
    for i, news in enumerate(all_news[:5]):
        print(f"{i+1}. {news['title']} ({news['date']})")
        print(f"   Источник: {news['source']}")
        print(f"   Ссылка: {news['link']}")
        print()

if __name__ == "__main__":
    main()