"""
Tweet processor for analyzing tweets using OpenAI.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from .openai_handler import OpenAIHandler

logger = logging.getLogger(__name__)


class TweetProcessor:
    """Processes tweets using OpenAI for classification."""
    
    def __init__(self):
        """Initialize tweet processor with OpenAI handler."""
        self.openai_handler = OpenAIHandler()
        self._prompt_template = None
    
    def load_prompt_template(self, prompt_file: str = "prompts/tweet_deciding_prompt1.txt") -> str:
        """
        Load prompt template from file.
        
        Args:
            prompt_file: Path to prompt template file
            
        Returns:
            Prompt template content
        """
        try:
            prompt_path = Path(prompt_file)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self._prompt_template = f.read().strip()
            logger.info(f"Loaded prompt template from {prompt_file}")
            return self._prompt_template
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
            raise
    
    def _get_prompt_template(self) -> str:
        """Get the current prompt template."""
        if self._prompt_template is None:
            # Auto-load default prompt if not loaded
            self.load_prompt_template()
        return self._prompt_template
    
    def analyze_tweet(self, tweet_text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single tweet using OpenAI.
        
        Args:
            tweet_text: The tweet text to analyze
            
        Returns:
            Analysis result with decision, or None if failed
        """
        try:
            if not tweet_text or not tweet_text.strip():
                logger.error("Tweet text is empty")
                return None
            
            # Get the prompt template and replace placeholder
            base_prompt = self._get_prompt_template()
            prompt = base_prompt.replace('<TWEET_CONTENT_HERE>', tweet_text.strip())
            
            # Get response from OpenAI
            response = self.openai_handler.openai_response(
                prompt=prompt,
                system_message="You are a tweet classifier. Respond only with TRUE or FALSE."
            )
            
            # Check for errors in response
            if response.startswith("[Error]"):
                logger.error(f"OpenAI error: {response}")
                return None
            
            # Clean and validate response
            decision = response.strip().upper()
            if decision not in ["TRUE", "FALSE"]:
                logger.warning(f"Invalid decision response: {decision}")
                return None
            
            # Build result
            result = {
                "decision": decision,
                "tweet_text": tweet_text,
                "reasoning": f"Classified as {decision} based on TV appearance indicators"
            }
            
            logger.debug(f"Analyzed tweet: {decision}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing tweet: {e}")
            return None
    
    def analyze_tweets_batch(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple tweets in batch.
        
        Args:
            tweets: List of tweet dictionaries with 'text' field and optional 'tweet_id', 'username'
            
        Returns:
            List of analysis results
        """
        results = []
        
        for tweet in tweets:
            try:
                tweet_text = tweet.get('text', '')
                tweet_id = tweet.get('tweet_id')
                username = tweet.get('username') or tweet.get('screen_name')
                
                result = self.analyze_tweet(tweet_text, tweet_id, username)
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error analyzing tweet {tweet.get('tweet_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Analyzed {len(results)} out of {len(tweets)} tweets")
        return results
    
    def test_processing(self, test_tweet: str = "Excited to join Bloomberg TV this morning to talk markets.") -> Optional[Dict[str, Any]]:
        """
        Test the tweet processing functionality.
        
        Args:
            test_tweet: Test tweet text
            
        Returns:
            Test result
        """
        logger.info("Testing tweet processing...")
        return self.analyze_tweet(test_tweet, "test_123", "test_user")
