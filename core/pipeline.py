"""
Main pipeline for the X-Discord-Google-Sheet Bot.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from utils.config import Config
from utils.helpers import parse_username
from core.state_manager import StateManager
from core.sheets_manager import SheetsManager
from core.tweet_fetcher import TweetFetcher
from core.prompt_processor import PromptProcessor
from core.discord_notifier import DiscordNotifier


class Pipeline:
    """Main pipeline for monitoring Twitter accounts and processing tweets."""
    
    ENABLE_INTERNAL_CYCLING = False  # Control internal cycling behavior
    
    def __init__(self, config: Config):
        """
        Initialize the pipeline.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.state_manager = StateManager(config.db_path)
        self.sheets_manager = SheetsManager(
            config.get_google_credentials_path(),
            config.google_sheet_id
        )
        self.tweet_fetcher = TweetFetcher(
            config.twitter_bearer_token,
            config.rate_limit_delay
        )
        self.prompt_processor = PromptProcessor(
            config.openai_api_key,
            config.openai_model,
            config.rate_limit_delay
        )
        self.discord_notifier = DiscordNotifier(config.discord_webhook_url)
        
        # Load prompt template
        self.prompt_processor.load_prompt_template(config.prompt_file)
    
    async def run(self) -> None:
        """Run the complete pipeline."""
        start_time = datetime.now()
        self.logger.info("Starting pipeline execution")
        print(f"\n[START] Starting pipeline execution at {start_time.strftime('%H:%M:%S')}")
        
        try:
            # Step 1: Load monitored accounts
            accounts = await self._load_monitored_accounts()
            if not accounts:
                self.logger.warning("No accounts to monitor")
                print("[WARNING] No accounts to monitor")
                return
            
            # Step 2: Fetch new tweets for each account
            all_new_tweets = await self._fetch_new_tweets(accounts)
            if not all_new_tweets:
                self.logger.info("No new tweets found")
                print("[INFO] No new tweets found")
                return
            
            # Print all fetched tweets before processing
            # print(f"\n[FETCHED_TWEETS] Total tweets fetched: {len(all_new_tweets)}")
            # print("=" * 80)
            # for i, tweet in enumerate(all_new_tweets):
            #     print(f"[TWEET_{i+1}] ID: {tweet.get('id', 'N/A')}")
            #     print(f"         Username: @{tweet.get('username', 'N/A')}")
            #     print(f"         Content: {tweet.get('text', 'N/A')}")
            #     print(f"         Created: {tweet.get('created_at', 'N/A')}")
            #     print("-" * 80)
            
            # Step 3: Process tweets with OpenAI and save for later posting
            analysis_results = await self._process_tweets(all_new_tweets)
            if not analysis_results:
                self.logger.info("No tweets processed successfully")
                print("[INFO] No tweets processed successfully")
                return
            
            # Print all analysis results after processing
            # print(f"\n[ANALYSIS_RESULTS] Total analysis results: {len(analysis_results)}")
            # print("=" * 80)
            # for i, result in enumerate(analysis_results):
            #     print(f"[RESULT_{i+1}] Tweet ID: {result.get('tweet_id', 'N/A')}")
            #     print(f"           Username: @{result.get('username', 'N/A')}")
            #     print(f"           Decision: {result.get('decision', 'N/A')}")
            #     print(f"           Reasoning: {result.get('reasoning', 'N/A')}")
            #     print(f"           Content: {result.get('tweet_text', 'N/A')}")
            #     print("-" * 80)
            
            # Step 4: Save positive decisions for later posting (don't post immediately)
            await self._save_processed_content(all_new_tweets)
            
            # Step 5: Update state
            await self._update_state(all_new_tweets)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Pipeline completed successfully in {execution_time:.2f} seconds")
            print(f"\n[SUCCESS] Pipeline completed successfully in {execution_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            print(f"\n[ERROR] Pipeline execution failed: {e}")
            self.state_manager.log_error("pipeline_error", str(e))
            raise
    
    async def _load_monitored_accounts(self) -> List[str]:
        """Load monitored accounts from Google Sheet."""
        try:
            accounts = self.sheets_manager.get_monitored_accounts()
            self.logger.info(f"Loaded {len(accounts)} monitored accounts")
            return accounts
        except Exception as e:
            self.logger.error(f"Failed to load monitored accounts: {e}")
            self.state_manager.log_error("sheets_error", str(e))
            return []
    
    async def _fetch_new_tweets(self, accounts: List[str]) -> List[Dict[str, Any]]:
        """Fetch new tweets for all accounts."""
        all_tweets = []
        any_processed = False  # Track if any accounts were processed
        
        # Get the last processed account index
        last_processed_index = self.state_manager.get_last_processed_account_index()
        start_index = (last_processed_index + 1) % len(accounts)  # Start from next account
        
        self.logger.info(f"Starting from account index {start_index} (account: {accounts[start_index]})")
        print(f"\n[FETCH] Starting from account index {start_index} (account: {accounts[start_index]})")
        
        # Process accounts starting from the last processed index
        for i in range(len(accounts)):
            current_index = (start_index + i) % len(accounts)
            username_raw = accounts[current_index]
            
            # Parse username properly
            username = parse_username(username_raw)
            self.logger.info(f"Processing account {current_index + 1}/{len(accounts)}: {username_raw} -> {username}")
            print(f"\n[ACCOUNT] Processing account {current_index + 1}/{len(accounts)}: {username_raw} -> {username}")
            
            try:
                # Get last tweet ID for this account
                last_tweet_id = self.state_manager.get_last_tweet_id(username)
                
                # Fetch new tweets
                new_tweets = await self.tweet_fetcher.fetch_new_tweets(
                    username,
                    last_tweet_id,
                    self.config.max_tweets_per_account
                )
                
                if new_tweets is None:
                    # Rate limit hit, wait and resume from same account
                    self.logger.warning(f"Rate limit hit while processing @{username}, waiting 20 minutes and resuming from same account")
                    print(f"[RATE_LIMIT] Rate limit hit while processing @{username}, waiting 20 minutes and resuming from same account")
                    
                    # Save any processed content that was already analyzed
                    if all_tweets:
                        self.logger.info("Saving processed content for later posting...")
                        print("[SAVE] Saving processed content for later posting...")
                        await self._save_processed_content(all_tweets)
                    
                    # Wait 20 minutes for rate limit to reset
                    print(f"[WAIT] Waiting 20 minutes for rate limit to reset...")
                    await asyncio.sleep(1200)  # 20 minutes
                    
                    # Retry the same account instead of continuing to next
                    print(f"[RETRY] Retrying @{username} after rate limit reset...")
                    continue  # Retry the same account
                elif new_tweets:
                    self.logger.info(f"Found {len(new_tweets)} new tweets for @{username}")
                    print(f"[FOUND] Found {len(new_tweets)} new tweets for @{username}")
                    
                    # Log each fetched tweet
                    # for i, tweet in enumerate(new_tweets):
                    #     tweet_text = tweet.get('text', 'N/A')
                    #     tweet_id = tweet.get('id', 'N/A')
                    #     self.logger.info(f"  Fetched Tweet {i+1}: ID={tweet_id}, Content='{tweet_text[:100]}{'...' if len(tweet_text) > 100 else ''}'")
                    #     print(f"  [TWEET] Tweet {i+1}: ID={tweet_id}")
                    #     print(f"     Content: {tweet_text}")
                    #     print(f"     Username: @{username}")
                    #     print(f"     Created: {tweet.get('created_at', 'Unknown')}")
                    #     print()
                    
                    all_tweets.extend(new_tweets)
                else:
                    self.logger.debug(f"No new tweets for @{username}")
                    print(f"[INFO] No new tweets for @{username}")
                
                # Update the last processed account index (only on successful processing)
                self.state_manager.set_last_processed_account_index(current_index)
                any_processed = True  # Mark that an account was processed
                
                # Add delay between accounts to avoid rate limits (only if internal cycling is enabled)
                if self.ENABLE_INTERNAL_CYCLING and i < len(accounts) - 1:  # Don't sleep after the last account
                    print(f"[DELAY] Waiting 15 minutes before processing next account...")
                    await asyncio.sleep(900)  # 15 minute delay between accounts
                    
            except Exception as e:
                self.logger.error(f"Error fetching tweets for @{username}: {e}")
                self.state_manager.log_error("tweet_fetch_error", str(e), username)
                # Update the last processed account index even on error
                self.state_manager.set_last_processed_account_index(current_index)
                continue
        
        # Print summary of all fetched tweets
        self.logger.info(f"Total new tweets fetched: {len(all_tweets)}")
        print(f"\n[FETCH_SUMMARY] Total new tweets fetched from all accounts: {len(all_tweets)}")
        
        # Check if we've processed all accounts and reset for continuous monitoring
        if self.ENABLE_INTERNAL_CYCLING and (len(all_tweets) > 0 or any_processed):
            # If we processed any accounts, check if we should reset the index for continuous cycling
            last_processed = self.state_manager.get_last_processed_account_index()
            if last_processed >= len(accounts) - 1:
                # Reset to start of account list for continuous monitoring
                self.state_manager.set_last_processed_account_index(-1)  # Will start from index 0 next time
                print(f"[CYCLE] Completed all {len(accounts)} accounts, resetting to start for continuous monitoring")
        
        return all_tweets
    
    async def _post_pending_content(self) -> None:
        """Post the latest pending content that was saved due to rate limits."""
        # This method is deprecated - posting is now handled by PostingManager
        self.logger.warning("_post_pending_content is deprecated - use PostingManager instead")
        pass
    
    async def _save_processed_content(self, tweets: List[Dict[str, Any]]) -> None:
        """Save processed tweets for later posting when rate limits occur."""
        try:
            # Process the tweets with AI analysis
            analysis_results = await self._process_tweets(tweets)
            if not analysis_results:
                self.logger.info("No tweets to save for later posting")
                return
            
            # Save each positive result
            saved_count = 0
            for result in analysis_results:
                if result.get('decision', '').upper() == 'TRUE':
                    tweet_data = {
                        'id': result['tweet_id'],
                        'text': result['tweet_text'],
                        'username': result['username'],
                        'created_at': result.get('created_at', 'Unknown')
                    }
                    
                    # self.logger.info(f"[SAVE_DB] SAVING TO DATABASE: Tweet {result['tweet_id']} from @{result['username']} (TRUE decision)")
                    # print(f"[SAVE_DB] SAVING TO DATABASE: Tweet {result['tweet_id']} from @{result['username']} (TRUE decision)")
                    if self.state_manager.save_pending_post(tweet_data, result):
                        saved_count += 1
                        # self.logger.info(f"[SUCCESS] SUCCESSFULLY SAVED: Tweet {result['tweet_id']} to database")
                        # print(f"[SUCCESS] SUCCESSFULLY SAVED: Tweet {result['tweet_id']} to database")
                        pass
                    else:
                        # self.logger.warning(f"[FAIL] FAILED TO SAVE: Tweet {result['tweet_id']} to database (may already exist)")
                        # print(f"[FAIL] FAILED TO SAVE: Tweet {result['tweet_id']} to database (may already exist)")
                        pass
                else:
                    # self.logger.info(f"[SKIP_DB] NOT SAVING: Tweet {result.get('tweet_id', 'unknown')} (decision: {result.get('decision', 'unknown')})")
                    # print(f"[SKIP_DB] NOT SAVING: Tweet {result.get('tweet_id', 'unknown')} (decision: {result.get('decision', 'unknown')})")
                    pass
            
            if saved_count > 0:
                self.logger.info(f"Saved {saved_count} new positive tweets for later posting")
                print(f"[FINAL] Saved {saved_count} new positive tweets for later posting")
            else:
                self.logger.info("No new tweets to save (all were already saved)")
                print("[FINAL] No new tweets to save (all were already saved)")
            
        except Exception as e:
            self.logger.error(f"Error saving processed content: {e}")
            self.state_manager.log_error("save_content_error", str(e))
    
    async def _process_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process tweets with OpenAI analysis."""
        try:
            self.logger.info(f"Starting to process {len(tweets)} tweets with prompt analysis...")
            print(f"\n[ANALYZE] Starting to process {len(tweets)} tweets with prompt analysis...")
            
            results = await self.prompt_processor.analyze_tweets_batch(tweets)
            
            # Log each tweet and its analysis result
            for i, tweet in enumerate(tweets):
                tweet_text = tweet.get('text', 'N/A')
                tweet_id = tweet.get('id', 'N/A')
                username = tweet.get('username', 'N/A')
                
                # self.logger.info(f"Tweet {i+1}/{len(tweets)}:")
                # self.logger.info(f"  ID: {tweet_id}")
                # self.logger.info(f"  Username: @{username}")
                # self.logger.info(f"  Raw Content: {tweet_text}")
                
                # print(f"\n[ANALYZE] ANALYZING Tweet {i+1}/{len(tweets)}:")
                # print(f"  ID: {tweet_id}")
                # print(f"  Username: @{username}")
                # print(f"  Raw Content: {tweet_text}")
                
                # Find corresponding analysis result
                analysis_result = next((r for r in results if r.get('tweet_id') == tweet_id), None)
                
                if analysis_result:
                    decision = analysis_result.get('decision', 'UNKNOWN')
                    reasoning = analysis_result.get('reasoning', 'No reasoning provided')
                    
                    # self.logger.info(f"  Prompt Decision: {decision}")
                    # self.logger.info(f"  Reasoning: {reasoning}")
                    
                    # print(f"  [AI] AI Decision: {decision}")
                    # print(f"  [REASON] AI Reasoning: {reasoning}")
                    
                    # Simple summary format
                    print(f"Tweet {i+1} from @{username}: prompt satisfied {decision}")
                    
                    if decision.upper() == 'TRUE':
                        # self.logger.info(f"  [SAVE] SAVED: Tweet will be saved to database (TRUE decision)")
                        # print(f"  [SAVE] SAVED: Tweet will be saved to database (TRUE decision)")
                        pass
                    else:
                        # self.logger.info(f"  [SKIP] NOT SAVED: Tweet will NOT be saved to database (FALSE decision)")
                        # print(f"  [SKIP] NOT SAVED: Tweet will NOT be saved to database (FALSE decision)")
                        pass
                else:
                    # self.logger.warning(f"  [ERROR] NO ANALYSIS: No analysis result found for this tweet")
                    # print(f"  [ERROR] NO ANALYSIS: No analysis result found for this tweet")
                    print(f"Tweet {i+1} from @{username}: NO ANALYSIS RESULT")
            
            # Filter for positive decisions (TRUE responses)
            positive_results = [
                result for result in results 
                if result.get('decision', '').upper() == 'TRUE'
            ]
            
            self.logger.info(f"[SUMMARY] SUMMARY: Processed {len(results)} tweets, {len(positive_results)} positive decisions (TRUE)")
            self.logger.info(f"[DATABASE] DATABASE: {len(positive_results)} tweets will be saved to database")
            print(f"\n[SUMMARY] SUMMARY: Processed {len(results)} tweets, {len(positive_results)} positive decisions (TRUE)")
            print(f"[DATABASE] DATABASE: {len(positive_results)} tweets will be saved to database")
            
            return positive_results
            
        except Exception as e:
            self.logger.error(f"Error processing tweets: {e}")
            self.state_manager.log_error("processing_error", str(e))
            return []
    
    async def _send_alerts(self, analysis_results: List[Dict[str, Any]]) -> None:
        """Send Discord alerts for positive analysis results."""
        if not analysis_results:
            return
        
        alerts = []
        for result in analysis_results:
            tweet_data = {
                'id': result['tweet_id'],
                'text': result['tweet_text'],
                'username': result['username'],
                'created_at': result.get('created_at', 'Unknown')
            }
            
            summary = result.get('summary', 'No summary provided')
            alerts.append({
                'tweet_data': tweet_data,
                'summary': summary
            })
        
        try:
            success_results = await self.discord_notifier.send_alerts_batch(alerts)
            successful_count = sum(success_results)
            self.logger.info(f"Sent {successful_count} alerts successfully")
        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")
            self.state_manager.log_error("alert_error", str(e))
    
    async def _update_state(self, tweets: List[Dict[str, Any]]) -> None:
        """Update state with latest tweet IDs."""
        try:
            # Group tweets by username
            tweets_by_username = {}
            for tweet in tweets:
                username = tweet['username']
                if username not in tweets_by_username:
                    tweets_by_username[username] = []
                tweets_by_username[username].append(tweet)
            
            # Update last tweet ID for each account
            for username, user_tweets in tweets_by_username.items():
                # Sort by tweet ID (assuming numeric IDs) and get the latest
                latest_tweet = max(user_tweets, key=lambda t: int(t['id']))
                self.state_manager.update_last_tweet_id(username, latest_tweet['id'])
            
            self.logger.info(f"Updated state for {len(tweets_by_username)} accounts")
            
        except Exception as e:
            self.logger.error(f"Error updating state: {e}")
            self.state_manager.log_error("state_update_error", str(e))
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test all external connections."""
        results = {}
        
        # Test Google Sheets
        try:
            results['google_sheets'] = self.sheets_manager.test_connection()
        except Exception as e:
            self.logger.error(f"Google Sheets test failed: {e}")
            results['google_sheets'] = False
        
        # Test Twitter API
        try:
            results['twitter'] = await self.tweet_fetcher.test_connection()
        except Exception as e:
            self.logger.error(f"Twitter API test failed: {e}")
            results['twitter'] = False
        
        # Test OpenAI
        try:
            results['openai'] = await self.prompt_processor.test_connection()
        except Exception as e:
            self.logger.error(f"OpenAI test failed: {e}")
            results['openai'] = False
        
        # Test Discord webhook
        try:
            results['discord'] = await self.discord_notifier.test_webhook()
        except Exception as e:
            self.logger.error(f"Discord webhook test failed: {e}")
            results['discord'] = False
        
        return results 