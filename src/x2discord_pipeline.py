import time
import json
from .google_sheet_handler import GoogleSheetHandler
from .apify_scraper import ApifyScraper
from .tweet_processor import TweetProcessor
from .db_operations import DatabaseOperations
from .config import Config


class X2DiscordPipeline:
    def __init__(self):
        self.config = Config()
        self.sheet_handler = GoogleSheetHandler(self.config)
        self.apify_scraper = ApifyScraper()
        self.tweet_processor = TweetProcessor()
        self.db_ops = DatabaseOperations(self.config)

    def run_scraping_pipeline(self):
        """Run the complete scraping pipeline for all X accounts"""
        try:
            # Get all X usernames from Google Sheet
            all_x_accounts = self.sheet_handler.load_x_accounts()
            print(f"Loaded {len(all_x_accounts)} X accounts from sheet")
            
            # Get resume point from last processed account
            last_processed = self.db_ops.get_last_processed_account()
            start_index = 0
            if last_processed and last_processed in all_x_accounts:
                start_index = all_x_accounts.index(last_processed) + 1
                print(f"Resuming from account {start_index + 1}")
            
            # Process each account
            for i, username in enumerate(all_x_accounts[start_index:], start_index + 1):
                print(f"\n--- Processing account {i}/{len(all_x_accounts)}: @{username} ---")
                
                # Scrape the account using Apify
                scraped_data = self.apify_scraper.scrape_x_account_using_twitter_scraper_ppr(username)
                
                if scraped_data is not None:
                    print(f"Scraped data for @{username}:")
                    # print(json.dumps(scraped_data, indent=2, ensure_ascii=False))

                    # Extract tweet_id and text from scraped data
                    for tweet in scraped_data:
                        tweet_id = tweet.get('tweet_id')
                        text = tweet.get('text')
                        
                        # Process tweet with OpenAI to get TRUE/FALSE decision
                        result = self.tweet_processor.analyze_tweet(text)
                        
                        if result and result.get('decision') == 'TRUE':
                            # Save to database
                            post_data = {
                                'tweet_id': tweet_id,
                                'content': text,
                                'username': username,
                                'post_link': f"https://x.com/{username}/status/{tweet_id}",
                                'status': 'pending'
                            }
                            self.db_ops.save_post(post_data)

                else:
                    print(f"Failed to scrape @{username}")
                
                # Update last processed account after completing this username
                self.db_ops.update_last_processed_account(username)
                
                # Sleep before next account
                if i < len(all_x_accounts):  # Don't sleep after last account
                    print(f"Sleeping for {self.config.scraping_delay} seconds...")
                    time.sleep(self.config.scraping_delay)
                    
        except Exception as e:
            print(f"Error in scraping pipeline: {e}")

    def run(self):
        """Main execution method - runs the scraping pipeline"""
        print("Starting X to Discord scraping pipeline...")
        self.run_scraping_pipeline()
        print("Pipeline completed.")
