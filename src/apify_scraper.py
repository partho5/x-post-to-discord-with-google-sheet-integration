import time
import logging
from typing import Optional, List, Dict
from apify_client import ApifyClient
from .google_sheet_handler import GoogleSheetHandler
from .config import Config

logger = logging.getLogger(__name__)


class ApifyScraper:
    def __init__(self):
        self.config = Config()
        self.sheet_handler = GoogleSheetHandler(self.config)

    def scrape_all_accounts(self):
        """Process all accounts with delay between each"""
        try:
            accounts = self.sheet_handler.load_x_accounts()
            print(f"Loaded {len(accounts)} accounts")

            for i, account in enumerate(accounts, 1):
                print(f"Processing account {i}/{len(accounts)}: {account}")
                time.sleep(self.config.scraping_delay)

        except Exception as e:
            print(f"Error processing accounts: {e}")

    def scrape_x_account_using_twitter_scraper_ppr(self, username: str, max_posts: int = 10) -> Optional[List[Dict]]:
        """
        Scrape X account using Twitter Scraper PPR Actor
        
        Args:
            username: X username to scrape
            max_posts: Maximum number of posts to fetch (default: 10)
            
        Returns:
            List of tweet data as dictionaries on success, None on failure
        """
        try:
            # Validate inputs
            if not username or not username.strip():
                logger.error("Username is empty or invalid")
                return None
                
            if not isinstance(max_posts, int) or max_posts <= 0:
                logger.error(f"Invalid max_posts value: {max_posts}")
                return None
            
            # Get Apify credentials from config
            apify_token = self.config.apify_api_token
            actor_id = self.config.apify_actor_id
            
            if not apify_token or not apify_token.strip():
                logger.error("Apify API token is not configured")
                return None
                
            if not actor_id or not actor_id.strip():
                logger.error("Apify Actor ID is not configured")
                return None
            
            # Create Apify client
            client = ApifyClient(apify_token)
            
            # Build run input
            run_input = {
                "username": username.strip(),
                "max_posts": max_posts
            }
            
            logger.info(f"Running Actor {actor_id} for @{username} with max_posts={max_posts}")
            
            # Call the actor
            run = client.actor(actor_id).call(run_input=run_input)
            
            if not run or "defaultDatasetId" not in run:
                logger.error(f"Actor run failed or returned invalid response: {run}")
                return None
            
            dataset_id = run["defaultDatasetId"]
            
            if not dataset_id:
                logger.error("No dataset ID returned from actor run")
                return None
            
            # Extract dataset items
            logger.info(f"Extracting data from dataset {dataset_id}")
            items = list(client.dataset(dataset_id).iterate_items())
            
            if not items:
                logger.warning(f"No tweets found for @{username}")
                return []
            
            logger.info(f"Successfully scraped {len(items)} tweets for @{username}")
            return items
            
        except Exception as e:
            logger.error(f"Error scraping @{username}: {str(e)}")
            return None
