"""
Utility functions for the X-Discord-Google-Sheet Bot.
"""

import asyncio
import re
import time
from typing import Optional, Dict, Any
import json


def parse_username(url_or_username: str) -> str:
    """
    Extract clean username from various Twitter/X URL formats.
    
    Args:
        url_or_username: URL or username string
        
    Returns:
        Clean username without @ symbol
        
    Examples:
        >>> parse_username("https://twitter.com/username")
        "username"
        >>> parse_username("x.com/username")
        "username"
        >>> parse_username("@username")
        "username"
        >>> parse_username("username")
        "username"
    """
    # Clean the input - remove whitespace and convert to lowercase
    cleaned_input = url_or_username.strip().lower()
    
    # Extract username from URLs - try URL patterns first
    url_patterns = [
        r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})',
        r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([^/?]+)'
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, cleaned_input)
        if match:
            username = match.group(1)
            # Remove any trailing slashes or query parameters
            username = username.rstrip('/').split('?')[0]
            return username
    
    # Remove @ symbol if present (for direct usernames)
    cleaned_input = cleaned_input.lstrip('@')
    
    # If it looks like a valid Twitter username (1-15 chars, alphanumeric + underscore)
    if re.match(r'^[a-zA-Z0-9_]{1,15}$', cleaned_input):
        return cleaned_input
    
    # If no pattern matches, return as-is but log a warning
    print(f"Warning: Could not parse username from: {url_or_username}")
    return cleaned_input


def clean_json_response(response: str) -> Dict[str, Any]:
    """
    Clean and parse JSON response from OpenAI, removing markdown formatting.
    
    Args:
        response: Raw response string from OpenAI
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If response cannot be parsed as JSON
    """
    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*$', '', response)
    response = re.sub(r'^```\s*', '', response)
    
    # Remove other markdown formatting
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Bold
    response = re.sub(r'\*(.*?)\*', r'\1', response)      # Italic
    response = re.sub(r'`(.*?)`', r'\1', response)        # Inline code
    
    # Strip whitespace
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}. Response: {response}")


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
    
    async def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            wait_time = self.min_interval - time_since_last_call
            await asyncio.sleep(wait_time)
        
        self.last_call_time = time.time()


def format_discord_message(tweet_data: Dict[str, Any], summary: str) -> str:
    """
    Format tweet data for Discord message.
    
    Args:
        tweet_data: Tweet information dictionary
        summary: AI-generated summary
        
    Returns:
        Formatted Discord message
    """
    username = tweet_data.get('username', 'Unknown')
    tweet_id = tweet_data.get('id', '')
    tweet_text = tweet_data.get('text', '')
    created_at = tweet_data.get('created_at', '')
    
    # Create tweet URL
    tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
    
    # Format message
    message = f"🚨 **New Alert from @{username}**\n\n"
    message += f"**Tweet:** {tweet_text[:200]}{'...' if len(tweet_text) > 200 else ''}\n\n"
    message += f"**AI Summary:** {summary}\n\n"
    message += f"**Link:** {tweet_url}\n"
    
    # Only show Posted field if it has a valid value
    if created_at and created_at.lower() not in ['unknown', 'none', '']:
        message += f"**Posted:** {created_at}"
    
    return message


def validate_tweet_data(tweet_data: Dict[str, Any]) -> bool:
    """
    Validate tweet data structure.
    
    Args:
        tweet_data: Tweet data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['id', 'text', 'username', 'created_at']
    return all(field in tweet_data for field in required_fields) 