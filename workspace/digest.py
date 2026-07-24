from jinja2 import Template
from datetime import datetime


# HTML шаблон
HTML_TEMPLATE = \"\"\"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Дайджест рынка электромобилей РФ</title>
</head>
<body>
    <h1>Дайджест рынка электромобилей РФ</h1>
    <p><strong>Дата:</strong> {{ date }}</p>
    <ul>
    {% for article in articles %}
        <li>
            <h2><a href="{{ article.url }}">{{ article.title }}</a></h2>
            <p><strong>Дата:</strong> {{ article.date }} | <strong>Источник:</strong> {{ article.source }}</p>
            <p>{{ article.description }}</p>
        </li>
    {% endfor %}
    </ul>
</body>
</html>
\"\"\"


# Markdown шаблон
MARKDOWN_TEMPLATE = \"\"\"
# Дайджест рынка электромобилей РФ

**Дата:** {{ date }}

{% for article in articles %}
## [{{ article.title }}]({{ article.url }})

**Дата:** {{ article.date }} | **Источник:** {{ article.source }}

{{ article.description }}

{% endfor %}
\"\"\"


def generate_html_digest(articles):
    \"\"\"
    Генерирует HTML дайджест из списка статей.

    :param articles: Список словарей с ключами: title, url, date, source, description
    :return: Строка с HTML содержимым
    \"\"\"
    template = Template(HTML_TEMPLATE.strip())
    return template.render(articles=articles, date=datetime.now().strftime('%Y-%m-%d'))


def generate_markdown_digest(articles):
    \"\"\"
    Генерирует Markdown дайджест из списка статей.

    :param articles: Список словарей с ключами: title, url, date, source, description
    :return: Строка с Markdown содержимым
    \"\"\"
    template = Template(MARKDOWN_TEMPLATE.strip())
    return template.render(articles=articles, date=datetime.now().strftime('%Y-%m-%d'))


# Пример использования:
if __name__ == '__main__':
    sample_articles = [
        {
            'title': 'Новые электромобили от Tesla',
            'url': 'https://example.com/tesla',
            'date': '2023-10-01',
            'source': 'Tesla News',
            'description': 'Компания Tesla анонсировала новые модели электромобилей с увеличенным запасом хода.'
        },
        {
            'title': 'Рост продаж электромобилей в РФ',
            'url': 'https://example.com/sales',
            'date': '2023-09-28',
            'source': 'Auto Market',
            'description': 'Продажи электромобилей в России выросли на 25% по сравнению с прошлым годом.'
        }
    ]

    html_digest = generate_html_digest(sample_articles)
    markdown_digest = generate_markdown_digest(sample_articles)

    print(\"HTML Дайджест:\")
    print(html_digest)
    print(\"\\nMarkdown Дайджест:\")
    print(markdown_digest)
\"\"\"