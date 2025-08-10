"""
Twitter/X API integration for fetching tweets.
"""

import aiohttp
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.helpers import RateLimiter


class TweetFetcher:
    """Handles Twitter/X API operations using API v2."""
    
    def __init__(self, bearer_token: str, rate_limit_delay: float = 1.0):
        """
        Initialize tweet fetcher.
        
        Args:
            bearer_token: Twitter API bearer token
            rate_limit_delay: Delay between API calls in seconds
        """
        self.bearer_token = bearer_token
        self.rate_limiter = RateLimiter(1.0 / rate_limit_delay)
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.twitter.com/2"
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
        # Cache for user IDs to avoid redundant API calls
        self._user_id_cache = {}
        
        # Global rate limit state
        self._rate_limit_until = 0.0
    
    def _check_global_rate_limit(self) -> bool:
        """
        Check if we're currently under a global rate limit.
        
        Returns:
            True if we should wait, False if we can proceed
        """
        import time
        current_time = time.time()
        if current_time < self._rate_limit_until:
            wait_time = self._rate_limit_until - current_time
            self.logger.warning(f"Global rate limit active, waiting {wait_time:.1f} seconds...")
            return True
        return False
    
    def _set_global_rate_limit(self, duration_seconds: float = 1200.0):
        """
        Set a global rate limit for the specified duration.
        
        Args:
            duration_seconds: Duration of the rate limit in seconds
        """
        import time
        self._rate_limit_until = time.time() + duration_seconds
        self.logger.warning(f"Global rate limit set for {duration_seconds} seconds")
    
    def _parse_rate_limit_headers(self, response) -> Optional[float]:
        """
        Parse rate limit headers from Twitter API response.
        
        Args:
            response: aiohttp response object
            
        Returns:
            Wait time in seconds or None if no rate limit info
        """
        try:
            # Get rate limit reset time from headers
            reset_time = response.headers.get('x-rate-limit-reset')
            if reset_time:
                import time
                reset_timestamp = int(reset_time)
                current_time = int(time.time())
                wait_time = max(0, reset_timestamp - current_time)
                return wait_time
            
            # Fallback: use retry-after header if available
            retry_after = response.headers.get('retry-after')
            if retry_after:
                return int(retry_after)
                
        except Exception as e:
            self.logger.error(f"Error parsing rate limit headers: {e}")
        
        return None
    
    async def get_user_id(self, username: str) -> Optional[str]:
        """
        Get user ID from username.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            User ID or None if not found
        """
        # Check cache first
        if username in self._user_id_cache:
            self.logger.debug(f"Using cached user ID for {username}: {self._user_id_cache[username]}")
            return self._user_id_cache[username]
        
        # Check global rate limit
        if self._check_global_rate_limit():
            await asyncio.sleep(1200)  # Wait 20 minutes
            return None
        
        await self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/users/by/username/{username}"
        
        try:
            self.logger.debug(f"Making request to: {url}")
            self.logger.debug(f"Headers: {self.headers}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    self.logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        user_id = data.get('data', {}).get('id')
                        if user_id:
                            # Cache the user ID
                            self._user_id_cache[username] = user_id
                            self.logger.debug(f"Successfully got and cached user ID: {user_id}")
                        return user_id
                    elif response.status == 404:
                        self.logger.warning(f"User not found: {username}")
                        return None
                    elif response.status == 429:
                        # Parse rate limit headers for precise wait time
                        wait_time = self._parse_rate_limit_headers(response)
                        if wait_time:
                            self.logger.warning(f"Rate limit hit in get_user_id, waiting {wait_time} seconds based on API headers...")
                            self._set_global_rate_limit(wait_time)
                        else:
                            self.logger.warning("Rate limit hit in get_user_id, setting default 15-minute wait...")
                            self._set_global_rate_limit(900.0)  # 15 minutes default
                        return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get user ID for {username}: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Error getting user ID for {username}: {e}")
            return None
    
    async def get_user_tweets(
        self, 
        username: str, 
        since_id: Optional[str] = None,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent tweets from a user.
        
        Args:
            username: Twitter username (without @)
            since_id: Tweet ID to start from (exclusive)
            max_results: Maximum number of tweets to fetch (default: 10)
            
        Returns:
            List of tweet dictionaries with id, created_at, and text
        """
        # Check global rate limit
        if self._check_global_rate_limit():
            await asyncio.sleep(1200)  # Wait 20 minutes
            return None
        
        await self.rate_limiter.wait_if_needed()
        
        try:
            user_id = await self.get_user_id(username)
            if not user_id:
                self.logger.error(f"Could not find user ID for username: {username}")
                return None

            url = f"{self.base_url}/users/{user_id}/tweets"
            
            # Twitter API requires max_results to be between 5-100
            if max_results < 5:
                max_results = 5
            elif max_results > 100:
                max_results = 100
                
            params = {
                "max_results": max_results,
                "tweet.fields": "created_at,text,referenced_tweets",
                "expansions": "referenced_tweets.id",
            }
            
            if since_id:
                params['since_id'] = since_id

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        # Parse rate limit headers for precise wait time
                        wait_time = self._parse_rate_limit_headers(response)
                        if wait_time:
                            self.logger.warning(f"Rate limit hit in get_user_tweets, waiting {wait_time} seconds based on API headers...")
                            self._set_global_rate_limit(wait_time)
                        else:
                            self.logger.warning("Rate limit hit in get_user_tweets, setting default 15-minute wait...")
                            self._set_global_rate_limit(900.0)  # 15 minutes default
                        return None
                    elif response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Error fetching tweets: {response.status} - {error_text}")
                        return None
                    else:
                        data = await response.json()

            original_tweet_lookup = {}
            
            # Build lookup for original tweets (for retweets/quotes)
            for tweet in data.get("includes", {}).get("tweets", []):
                original_tweet_lookup[tweet["id"]] = tweet

            # Process and enrich tweets
            enriched_tweets = []
            for tweet in data.get("data", []):
                full_text = tweet["text"]
                
                # If this is a retweet, get the original tweet text
                if "referenced_tweets" in tweet:
                    for ref in tweet["referenced_tweets"]:
                        if ref["type"] == "retweeted":
                            ref_id = ref["id"]
                            original_tweet = original_tweet_lookup.get(ref_id, {})
                            full_text = original_tweet.get("text", tweet["text"])
                
                enriched_tweets.append({
                    "id": tweet["id"],
                    "created_at": tweet["created_at"],
                    "text": full_text,
                    "username": username
                })

            self.logger.info(f"Fetched {len(enriched_tweets)} tweets for user {username}")
            return enriched_tweets
            
        except Exception as e:
            self.logger.error(f"Error in get_user_tweets: {e}")
            return None
    
    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tweet by ID.
        
        Args:
            tweet_id: Twitter tweet ID
            
        Returns:
            Tweet dictionary or None if not found
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.base_url}/tweets/{tweet_id}"
            params = {
                "tweet.fields": "created_at,text,author_id",
                "expansions": "author_id",
                "user.fields": "username"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweet = data["data"]
                        return {
                            "id": tweet["id"],
                            "created_at": tweet["created_at"],
                            "text": tweet["text"],
                            "author_id": tweet["author_id"]
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error fetching tweet: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error in get_tweet_by_id: {e}")
            return None
    
    async def fetch_new_tweets(
        self, 
        username: str, 
        since_id: Optional[str] = None,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch new tweets for a username.
        
        Args:
            username: Twitter username
            since_id: Last tweet ID seen
            max_results: Maximum number of tweets to fetch
            
        Returns:
            List of new tweet dictionaries, or None if rate limit hit
        """
        try:
            # Get tweets using the new method
            tweets = await self.get_user_tweets(username, since_id, max_results)
            
            if tweets is None:
                # Rate limit hit, return None to signal pipeline to stop
                return None
            
            # Format tweets for consistency with existing code
            formatted_tweets = []
            for tweet in tweets:
                formatted_tweet = {
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'username': tweet.get('username', username),
                    'created_at': tweet['created_at'],
                    'author_id': tweet.get('author_id', '')  # May not be available in all responses
                }
                formatted_tweets.append(formatted_tweet)
            
            return formatted_tweets
            
        except Exception as e:
            self.logger.error(f"Error fetching tweets for {username}: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """
        Test Twitter API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get a well-known user (using elonmusk instead of twitter since twitter is suspended)
            user_id = await self.get_user_id("elonmusk")
            return user_id is not None
        except Exception as e:
            self.logger.error(f"Twitter API connection test failed: {e}")
            return False 