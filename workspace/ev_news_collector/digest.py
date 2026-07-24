import os
import logging
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_digest(articles: List[Dict], template_dir: str, html_output: str, markdown_output: str):
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Создание директории для шаблонов, если её нет
        os.makedirs(template_dir, exist_ok=True)
        
        # HTML шаблон
        html_template_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Дайджест новостей по EV в РФ</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Дайджест новостей по EV в РФ</h1>
    <ul>
    {% for article in articles %}
        <li>
            <a href="{{ article.link }}">{{ article.title }}</a>
            <p>{{ article.summary }}</p>
            <small>{{ article.published }}</small>
        </li>
    {% endfor %}
    </ul>
</body>
</html>
'''
        with open(os.path.join(template_dir, 'digest.html.j2'), 'w', encoding='utf-8') as f:
            f.write(html_template_content)
            
        # Markdown шаблон
        md_template_content = '''
# Дайджест новостей по EV в РФ

{% for article in articles %}
## [{{ article.title }}]({{ article.link }})

{{ article.summary }}

_{{ article.published }}_
{% endfor %}
'''
        with open(os.path.join(template_dir, 'digest.md.j2'), 'w', encoding='utf-8') as f:
            f.write(md_template_content)
        
        # Генерация HTML
        html_template = env.get_template('digest.html.j2')
        html_content = html_template.render(articles=articles)
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Генерация Markdown
        md_template = env.get_template('digest.md.j2')
        md_content = md_template.render(articles=articles)
        with open(markdown_output, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        logger.info("Дайджест успешно сгенерирован.")
    except Exception as e:
        logger.error(f"Ошибка при генерации дайджеста: {e}")