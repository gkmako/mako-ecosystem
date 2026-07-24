import asyncio
import logging
import feedparser
import aiohttp
from typing import List, Dict, Any
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RSS feed URLs for electric vehicles in Russia
RSS_FEEDS = [
    "https://example.com/rss/electric-vehicles",  # Placeholder URLs
    "https://example.com/rss/ev-news",
    "https://example.com/rss/tesla-russia"
]

async def fetch_feed(session: aiohttp.ClientSession, url: str, retries: int = 3) -> Dict[str, Any]:
    """
    Asynchronously fetch a single RSS feed with retry logic.
    
    Args:
        session: aiohttp client session
        url: RSS feed URL
        retries: Number of retry attempts (default: 3)
        
    Returns:
        Dictionary containing feed data or error information
    """
    for attempt in range(retries):
        try:
            logger.info(f"Fetching feed from {url} (attempt {attempt + 1}/{retries})")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    logger.info(f"Successfully fetched feed from {url}")
                    return {
                        "url": url,
                        "status": "success",
                        "feed": feed,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while fetching {url} (attempt {attempt + 1}/{retries})")
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)} (attempt {attempt + 1}/{retries})")
        
        if attempt < retries - 1:
            # Wait before retrying (exponential backoff)
            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time} seconds before retrying {url}")
            await asyncio.sleep(wait_time)
    
    logger.error(f"Failed to fetch feed from {url} after {retries} attempts")
    return {
        "url": url,
        "status": "error",
        "error": f"Failed after {retries} attempts",
        "timestamp": datetime.now().isoformat()
    }

def parse_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single RSS entry.
    
    Args:
        entry: RSS entry from feedparser
        
    Returns:
        Dictionary with parsed entry information
    """
    try:
        parsed_entry = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", ""),
            "author": entry.get("author", ""),
        }
        
        # Try to get published date from different possible fields
        if not parsed_entry["published"] and "published_parsed" in entry:
            try:
                parsed_entry["published"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", entry["published_parsed"]
                )
            except Exception:
                pass
                
        logger.debug(f"Parsed entry: {parsed_entry['title']}")
        return parsed_entry
    except Exception as e:
        logger.error(f"Error parsing entry: {str(e)}")
        return {
            "title": "",
            "link": "",
            "summary": "",
            "published": "",
            "author": "",
            "error": str(e)
        }

async def fetch_all_feeds(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Asynchronously fetch all RSS feeds.
    
    Args:
        urls: List of RSS feed URLs
        
    Returns:
        List of results from fetching feeds
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_feed(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception occurred while fetching {urls[i]}: {str(result)}")
                processed_results.append({
                    "url": urls[i],
                    "status": "error",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
                
        return processed_results

async def main():
    """Main function to run the RSS collector."""
    logger.info("Starting RSS feed collection for electric vehicles in Russia")
    
    # Fetch all feeds
    results = await fetch_all_feeds(RSS_FEEDS)
    
    # Process successful feeds
    all_entries = []
    successful_feeds = 0
    
    for result in results:
        if result["status"] == "success":
            successful_feeds += 1
            feed = result["feed"]
            logger.info(f"Feed from {result['url']} has {len(feed.entries)} entries")
            
            # Parse entries
            for entry in feed.entries:
                parsed_entry = parse_entry(entry)
                parsed_entry["source"] = result["url"]
                all_entries.append(parsed_entry)
        else:
            logger.error(f"Failed to fetch feed: {result['url']} - {result.get('error', 'Unknown error')}")
    
    logger.info(f"Collection complete. Successfully processed {successful_feeds}/{len(RSS_FEEDS)} feeds.")
    logger.info(f"Total entries collected: {len(all_entries)}")
    
    # Example of how to use the collected data
    if all_entries:
        logger.info("Latest 5 entries:")
        for entry in all_entries[:5]:
            logger.info(f"- {entry['title'][:50]}... ({entry['published']})")
    
    return all_entries

if __name__ == "__main__":
    # Run the collector
    try:
        entries = asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.error(f"Error running collector: {str(e)}")