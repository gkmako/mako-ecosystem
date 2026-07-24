import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

# Список URL новостных сайтов для парсинга
NEWS_SOURCES = [
    'https://ria.ru',
    'https://tass.ru',
    'https://rbc.ru'
]

# Ключевые слова для поиска
KEYWORDS = ['электромобиль', 'электромобили', 'EV', 'электрокар', 'Tesla', 'Ниссан', 'Renault', 'LADA']

def fetch_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = soup.find_all('h3')  # Пример, может потребоваться адаптация под конкретный сайт
        return [headline.get_text() for headline in headlines]
    except Exception as e:
        print(f"Ошибка при получении данных с {url}: {e}")
        return []

def save_to_csv(news_data, filename='news.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Дата', 'Заголовок'])
        for item in news_data:
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item])

def main():
    all_news = []
    for source in NEWS_SOURCES:
        print(f"Парсинг новостей с {source}")
        news = fetch_news(source)
        # Фильтрация по ключевым словам
        filtered_news = [item for item in news if any(keyword.lower() in item.lower() for keyword in KEYWORDS)]
        all_news.extend(filtered_news)
    
    save_to_csv(all_news)
    print("Новости успешно сохранены в news.csv")

if __name__ == "__main__":
    main()