"""
Configuration management for the X-Discord-Google-Sheet Bot.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration management."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Project paths
        self.project_root = Path(__file__).parent.parent
        self.assets_dir = self.project_root / "assets"
        self.data_dir = self.project_root / "data"
        
        # Google Sheets configuration
        self.google_sheet_id = self._get_required_env("GOOGLE_SHEET_ID")
        self.google_credentials_file = self._get_required_env("GOOGLE_CREDENTIALS_FILE")
        
        # Discord configuration
        self.discord_webhook_url = self._get_required_env("DISCORD_WEBHOOK_URL")
        
        # OpenAI configuration
        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Twitter/X API configuration
        self.twitter_bearer_token = self._get_required_env("X_BEARER_TOKEN")
        
        # Application settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_tweets_per_account = int(os.getenv("MAX_TWEETS_PER_ACCOUNT", "10"))
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
        
        # Posting schedule, in EST time, (24-hour format)
        self.posting_hours = [10, 16]  # 10 AM and 4 PM
        self.posting_timezone = "US/Eastern"  # Default timezone
        
        # Database
        self.db_path = self.data_dir / "bot_state.db"
        
        # Prompt file
        self.prompt_file = self.assets_dir / "deciding_prompt_1.txt"
        
        # Ensure directories exist
        self.assets_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
    
    def _get_required_env(self, key: str) -> str:
        """Get a required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def get_google_credentials_path(self) -> Path:
        """Get the full path to Google credentials file."""
        return self.project_root / self.google_credentials_file
    
    def validate(self) -> bool:
        """Validate configuration."""
        # Check if credentials file exists
        if not self.get_google_credentials_path().exists():
            raise FileNotFoundError(f"Google credentials file not found: {self.google_credentials_file}")
        
        # Check if prompt file exists
        if not self.prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_file}")
        
        return True 