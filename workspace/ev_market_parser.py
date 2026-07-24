import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

def parse_news(query, pages=5):
    """
    Парсит новости по заданному запросу.
    
    :param query: Поисковый запрос
    :param pages: Количество страниц для парсинга
    """
    base_url = "https://news.yandex.ru/search/"
    params = {
        "query": query,
        "page": 0
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    news_data = []
    
    for page in range(pages):
        params["page"] = page
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('div', class_='story')
            
            for item in news_items:
                title = item.find('h2', class_='story__title').text.strip() if item.find('h2', class_='story__title') else "N/A"
                link = item.find('a', class_='link link_theme_normal')['href'] if item.find('a', class_='link link_theme_normal') else "N/A"
                date = item.find('div', class_='story__date').text.strip() if item.find('div', class_='story__date') else "N/A"
                
                news_data.append({
                    "title": title,
                    "link": link,
                    "date": date
                })
        else:
            print(f"Ошибка при запросе страницы {page}: {response.status_code}")
    
    return news_data

def save_to_csv(data, filename):
    """
    Сохраняет данные в CSV файл.
    
    :param data: Список словарей с данными новостей
    :param filename: Имя файла для сохранения
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'link', 'date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def main():
    # Поисковый запрос по теме электромобилей в РФ в 2025 году
    query = "электромобили Россия 2025"
    
    print(f"Парсинг новостей по запросу: {query}")
    news_data = parse_news(query)
    
    # Формирование имени файла с текущей датой
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"ev_news_{current_date}.csv"
    
    save_to_csv(news_data, filename)
    print(f"Данные сохранены в файл: {filename}")
    print(f"Всего найдено новостей: {len(news_data)}")

if __name__ == "__main__":
    main()