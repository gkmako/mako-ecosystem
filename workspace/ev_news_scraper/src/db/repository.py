from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import List, Optional
from .models import Base, NewsArticle
from src.config import settings
from loguru import logger


class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{settings.database.path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def save_articles(self, articles: List[NewsArticle]) -> int:
        session = self.SessionLocal()
        saved_count = 0
        try:
            for article in articles:
                # Проверка на дубликаты по URL
                existing = session.query(NewsArticle).filter(NewsArticle.url == article.url).first()
                if not existing:
                    session.add(article)
                    saved_count += 1
            session.commit()
            logger.info(f"Сохранено {saved_count} новых статей")
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сохранении статей: {e}")
        finally:
            session.close()
        return saved_count

    def get_unexported_articles(self) -> List[NewsArticle]:
        session = self.SessionLocal()
        try:
            articles = session.query(NewsArticle).filter(NewsArticle.is_exported == False).all()
            return articles
        except Exception as e:
            logger.error(f"Ошибка при получении неэкспортированных статей: {e}")
            return []
        finally:
            session.close()

    def mark_as_exported(self, article_ids: List[int]):
        session = self.SessionLocal()
        try:
            session.query(NewsArticle).filter(NewsArticle.id.in_(article_ids)).update(
                {NewsArticle.is_exported: True}, synchronize_session=False
            )
            session.commit()
            logger.info(f"Помечено {len(article_ids)} статей как экспортированные")
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при пометке статей как экспортированные: {e}")
        finally:
            session.close()