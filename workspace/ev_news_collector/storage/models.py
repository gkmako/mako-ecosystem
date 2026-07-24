# storage/models.py - Модель данных для новостей

class NewsItem:
    def __init__(self, title, link, summary, source):
        self.title = title
        self.link = link
        self.summary = summary
        self.source = source

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'summary': self.summary,
            'source': self.source
        }

    def __repr__(self):
        return f'NewsItem(title="{self.title}", source="{self.source}")'