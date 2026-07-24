import yaml
import logging
from datetime import datetime
from typing import Dict, Any

from collector import collect_news
from storage import NewsStorage
from dedup import deduplicate_articles, remove_exact_duplicates
from digest import NewsDigest, format_article_summary
from scheduler import NewsScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[Any, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        Dict[Any, Any]: Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def run_news_collection():
    """Main function to collect, process, and store news."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        storage = NewsStorage(config['database']['path'])
        digest_generator = NewsDigest()
        
        # Collect news from RSS feeds
        logger.info("Starting news collection...")
        articles = collect_news(config['rss_feeds'])
        
        if not articles:
            logger.warning("No articles collected")
            return
        
        # Remove exact duplicates
        if config['deduplication']['enabled']:
            articles = remove_exact_duplicates(articles)
        
        # Deduplicate articles based on content
        if config['deduplication']['enabled']:
            articles = deduplicate_articles(
                articles, 
                config['deduplication']['time_window_hours']
            )
        
        if not articles:
            logger.warning("No unique articles after deduplication")
            return
        
        # Save articles to database
        saved_count = storage.save_articles(articles)
        logger.info(f"Saved {saved_count} new articles")
        
        # Export to CSV and JSON if enabled
        if config['storage']['export_enabled']:
            all_articles = storage.get_all_articles()
            
            # Export to CSV
            storage.export_to_csv(
                config['storage']['csv_path'], 
                all_articles
            )
            
            # Export to JSON
            storage.export_to_json(
                config['storage']['json_path'], 
                all_articles
            )
        
        # Generate digest if we have articles
        if articles:
            formatted_articles = format_article_summary(articles)
            digest_generator.generate_digest(
                formatted_articles,
                config['digest']['output_path'],
                items_per_digest=config['digest']['items_per_digest']
            )
        
        logger.info("News collection completed successfully")
        
    except Exception as e:
        logger.error(f"Error in news collection: {str(e)}")
        raise

def main():
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Check if scheduler is enabled
        if 'scheduler' in config:
            scheduler_config = config['scheduler']
            
            # Initialize scheduler
            scheduler = NewsScheduler()
            
            # Schedule the job
            scheduler.schedule_job(
                run_news_collection,
                scheduler_config['interval_minutes'],
                scheduler_config['run_on_startup']
            )
            
            # Run scheduler
            logger.info("Starting scheduler...")
            scheduler.run_scheduler()
        else:
            # Run once
            run_news_collection()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()