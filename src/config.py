"""
Configuration management for X to Discord posting pipeline.
Loads environment variables and provides configuration settings.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Configuration class that loads environment variables and provides settings."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        self._load_env()
        self._validate_config()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        try:
            # Load .env file if it exists
            load_dotenv()
            logger.info("Environment variables loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load .env file: {e}")
    
    def _validate_config(self):
        """Validate that required environment variables are set."""
        required_vars = [
            'GOOGLE_CREDENTIALS_PATH',
            'GOOGLE_SHEET_ID',
            'DISCORD_TOKEN',
            'DISCORD_WEBHOOK_URL',
            'DISCORD_GUILD_ID',
            'DISCORD_CHANNEL_ID',
            'OPENAI_API_KEY',
            'OPENAI_MODEL',
            'APIFY_TOKEN',
            'APIFY_ACTOR_ID',
            'X_BEARER_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load and return configuration dictionary."""
        return {
            'scraping_delay': self.scraping_delay,
            'notification_times': self.discord_notification_times,
            'tweets_per_account': self.posts_per_account,
            'database_path': self.database_path
        }
    
    # Environment variable getters
    @property
    def google_credentials_path(self) -> str:
        return os.getenv('GOOGLE_CREDENTIALS_PATH')
    
    @property
    def google_sheet_id(self) -> str:
        return os.getenv('GOOGLE_SHEET_ID')
    
    @property
    def discord_token(self) -> str:
        return os.getenv('DISCORD_TOKEN')
    
    @property
    def discord_webhook_url(self) -> str:
        return os.getenv('DISCORD_WEBHOOK_URL')
    
    @property
    def discord_guild_id(self) -> str:
        return os.getenv('DISCORD_GUILD_ID')
    
    @property
    def discord_channel_id(self) -> str:
        return os.getenv('DISCORD_CHANNEL_ID')
    
    @property
    def openai_api_key(self) -> str:
        return os.getenv('OPENAI_API_KEY')
    
    @property
    def openai_model(self) -> str:
        return os.getenv('OPENAI_MODEL')
    
    @property
    def apify_api_token(self) -> str:
        return os.getenv('APIFY_TOKEN')
    
    @property
    def apify_actor_id(self) -> str:
        return os.getenv('APIFY_ACTOR_ID')
    
    @property
    def x_bearer_token(self) -> str:
        return os.getenv('X_BEARER_TOKEN')
    
    # Configuration getters (with environment variable defaults)
    @property
    def scraping_delay(self) -> int:
        return int(os.getenv('SCRAPING_DELAY', 30))  # every N seconds
    
    @property
    def discord_notification_times(self) -> List[str]:
        return os.getenv('NOTIFICATION_TIMES', '10:00,16:00').split(',')  # 24h format, EST time
    
    @property
    def posts_per_account(self) -> int:
        return int(os.getenv('POSTS_PER_ACCOUNT', 10))  # number of tweets to fetch per account
    
    @property
    def database_path(self) -> str:
        return os.getenv('DATABASE_PATH', 'data/database.db')



