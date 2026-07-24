import sqlite3
import logging
import csv
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db_path: str) -> None:
    """
    Initialize the SQLite database and create the articles table if it doesn't exist.
    
    :param db_path: Path to the SQLite database file.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source TEXT,
                published_date TEXT,
                summary TEXT,
                content_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        raise

def insert_article(conn: sqlite3.Connection, article_dict: Dict[str, Any]) -> bool:
    """
    Insert a new article into the articles table.
    
    :param conn: SQLite connection object.
    :param article_dict: Dictionary containing article data.
    :return: True if inserted, False if duplicate.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO articles (title, url, source, published_date, summary, content_hash)
            VALUES (:title, :url, :source, :published_date, :summary, :content_hash)
        ''', article_dict)
        conn.commit()
        logger.info(f"Article inserted: {article_dict['title']}")
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"Duplicate article skipped: {article_dict['url']} or content hash {article_dict.get('content_hash')}. Error: {e}")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error inserting article: {e}")
        conn.rollback()
        raise

def get_articles(conn: sqlite3.Connection, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve articles from the database with pagination.
    
    :param conn: SQLite connection object.
    :param limit: Number of articles to retrieve.
    :param offset: Offset for pagination.
    :return: List of article dictionaries.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, source, published_date, summary, content_hash, created_at
            FROM articles
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        articles = [dict(zip(columns, row)) for row in rows]
        logger.info(f"Retrieved {len(articles)} articles.")
        return articles
    except sqlite3.Error as e:
        logger.error(f"Error retrieving articles: {e}")
        raise

def export_to_csv(conn: sqlite3.Connection, filepath: str) -> None:
    """
    Export all articles from the database to a CSV file.
    
    :param conn: SQLite connection object.
    :param filepath: Path to the output CSV file.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, source, published_date, summary, content_hash, created_at
            FROM articles
            ORDER BY created_at DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Write header
            writer.writerows(rows)   # Write data
        
        logger.info(f"Exported {len(rows)} articles to CSV: {filepath}")
    except sqlite3.Error as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise
    except IOError as e:
        logger.error(f"File I/O error during CSV export: {e}")
        raise

def export_to_json(conn: sqlite3.Connection, filepath: str) -> None:
    """
    Export all articles from the database to a JSON file.
    
    :param conn: SQLite connection object.
    :param filepath: Path to the output JSON file.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, source, published_date, summary, content_hash, created_at
            FROM articles
            ORDER BY created_at DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        articles = [dict(zip(columns, row)) for row in rows]
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(articles, jsonfile, ensure_ascii=False, indent=4)
        
        logger.info(f"Exported {len(articles)} articles to JSON: {filepath}")
    except sqlite3.Error as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise
    except IOError as e:
        logger.error(f"File I/O error during JSON export: {e}")
        raise