import hashlib
from typing import List, Dict
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_article_fingerprint(article: Dict) -> str:
    """
    Generate a unique fingerprint for an article based on its content.
    
    Args:
        article (Dict): Article dictionary
        
    Returns:
        str: MD5 hash fingerprint of the article
    """
    # Create fingerprint based on title and description
    content = f"{article.get('title', '')} {article.get('description', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def deduplicate_articles(articles: List[Dict], time_window_hours: int = 24) -> List[Dict]:
    """
    Remove duplicate articles based on content and time window.
    
    Args:
        articles (List[Dict]): List of articles to deduplicate
        time_window_hours (int): Time window in hours to consider duplicates
        
    Returns:
        List[Dict]: List of unique articles
    """
    if not articles:
        return []
    
    # Sort articles by published date (newest first)
    articles_sorted = sorted(articles, key=lambda x: x['published'], reverse=True)
    
    unique_articles = []
    fingerprints = set()
    cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
    
    for article in articles_sorted:
        # Check if article is within the time window
        if article['published'] < cutoff_time:
            # Outside time window, add without deduplication
            unique_articles.append(article)
            continue
        
        # Generate fingerprint for the article
        fingerprint = generate_article_fingerprint(article)
        
        # Check if we've seen this fingerprint recently
        if fingerprint not in fingerprints:
            unique_articles.append(article)
            fingerprints.add(fingerprint)
        else:
            logger.debug(f"Duplicate article found and removed: {article['title']}")
    
    logger.info(f"Deduplicated articles: {len(articles)} -> {len(unique_articles)}")
    return unique_articles

def remove_exact_duplicates(articles: List[Dict]) -> List[Dict]:
    """
    Remove exact duplicates based on link or GUID.
    
    Args:
        articles (List[Dict]): List of articles
        
    Returns:
        List[Dict]: List of articles with exact duplicates removed
    """
    if not articles:
        return []
    
    unique_articles = []
    seen_links = set()
    seen_guids = set()
    
    for article in articles:
        link = article.get('link', '')
        guid = article.get('guid', '')
        
        # Check if we've seen this link or GUID
        if link not in seen_links and guid not in seen_guids:
            unique_articles.append(article)
            if link:
                seen_links.add(link)
            if guid:
                seen_guids.add(guid)
        else:
            logger.debug(f"Exact duplicate article found and removed: {article['title']}")
    
    logger.info(f"Removed exact duplicates: {len(articles)} -> {len(unique_articles)}")
    return unique_articles