"""
OpenAI integration for processing tweets and generating decisions.
"""

import aiohttp
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.helpers import clean_json_response, RateLimiter


class PromptProcessor:
    """Handles OpenAI API operations for tweet analysis."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", rate_limit_delay: float = 1.0):
        """
        Initialize prompt processor.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            rate_limit_delay: Delay between API calls in seconds
        """
        self.api_key = api_key
        self.model = model
        self.rate_limiter = RateLimiter(1.0 / rate_limit_delay)
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self._prompt_template = None
    
    def load_prompt_template(self, prompt_file: Path) -> str:
        """
        Load prompt template from file.
        
        Args:
            prompt_file: Path to prompt template file
            
        Returns:
            Prompt template content
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self._prompt_template = f.read().strip()
            self.logger.info(f"Loaded prompt template from {prompt_file}")
            return self._prompt_template
        except Exception as e:
            self.logger.error(f"Failed to load prompt template: {e}")
            raise
    
    def _get_prompt_template(self) -> str:
        """Get the current prompt template."""
        if self._prompt_template is None:
            raise ValueError("Prompt template not loaded. Call load_prompt_template() first.")
        return self._prompt_template
    
    async def analyze_tweet(self, tweet_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a tweet using OpenAI.
        
        Args:
            tweet_data: Tweet information dictionary
            
        Returns:
            Analysis result with decision and summary, or None if failed
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            # Get the base prompt template
            base_prompt = self._get_prompt_template()
            tweet_text = tweet_data.get('text', '')
            username = tweet_data.get('username', 'Unknown')
            
            # Replace the placeholder with actual tweet content
            prompt = base_prompt.replace('<TWEET_CONTENT_HERE>', tweet_text)
            
            # Append JSON format requirement to the prompt
            json_instruction = """

Please respond with a JSON object in the following format:
{
    "decision": "TRUE" or "FALSE",
    "reasoning": "Brief explanation of your decision"
}

Respond only with the JSON object, no additional text."""
            
            final_prompt = prompt + json_instruction
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a tweet classifier. Analyze tweets and respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 300
            }
            
            # Make the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Parse the JSON response
                        try:
                            result = clean_json_response(content)
                            
                            # Validate the response structure
                            if 'decision' not in result:
                                self.logger.warning(f"Invalid response structure: {result}")
                                return None
                            
                            # Add tweet metadata to result
                            result['tweet_id'] = tweet_data.get('id')
                            result['username'] = username
                            result['tweet_text'] = tweet_text
                            
                            self.logger.debug(f"Analyzed tweet {tweet_data.get('id')}: {result['decision']}")
                            return result
                            
                        except ValueError as e:
                            self.logger.error(f"Failed to parse OpenAI response: {e}")
                            self.logger.error(f"Raw response content: {content}")
                            return None
                            
                    elif response.status == 429:
                        # Parse retry-after header for precise wait time
                        retry_after = response.headers.get('retry-after')
                        if retry_after:
                            wait_time = int(retry_after)
                            self.logger.warning(f"OpenAI rate limit exceeded, waiting {wait_time} seconds based on API headers...")
                            await asyncio.sleep(wait_time)
                        else:
                            self.logger.warning("OpenAI rate limit exceeded, waiting 60 seconds...")
                            await asyncio.sleep(60)  # Default 1 minute for OpenAI
                        return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error analyzing tweet: {e}")
            return None
    
    async def analyze_tweets_batch(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple tweets in batch.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            List of analysis results
        """
        results = []
        
        for tweet in tweets:
            try:
                result = await self.analyze_tweet(tweet)
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Error analyzing tweet {tweet.get('id', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Analyzed {len(results)} out of {len(tweets)} tweets")
        return results
    
    async def test_connection(self) -> bool:
        """
        Test OpenAI API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message."
                    }
                ],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"OpenAI API connection test failed: {e}")
            return False 