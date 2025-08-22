"""
Google Sheets integration handler for reading X accounts.
"""

import logging
import re
from typing import List
import gspread
from google.oauth2.service_account import Credentials
from .config import Config

logger = logging.getLogger(__name__)


class GoogleSheetHandler:
    """Handles Google Sheets operations for X accounts."""

    def __init__(self, config: Config):
        """Initialize with configuration."""
        self.config = config
        self._client = None

    def _get_client(self) -> gspread.Client:
        """Get or create Google Sheets client."""
        if self._client is None:
            try:
                # Define the scope
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]

                # Load credentials from service account file
                credentials = Credentials.from_service_account_file(
                    self.config.google_credentials_path,
                    scopes=scope
                )

                # Create client
                self._client = gspread.authorize(credentials)
                logger.info("Google Sheets client initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets client: {e}")
                raise

        return self._client

    def load_x_accounts(self) -> List[str]:
        """Load X accounts from Google Sheets. Returns list of usernames."""
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.config.google_sheet_id)

            # Get the first worksheet
            worksheet = sheet.get_worksheet(0)
            if not worksheet:
                raise Exception("No worksheets found in the Google Sheet")

            # Get all values from column A (first column)
            all_values = worksheet.col_values(1)

            # Filter out empty values and header row
            usernames = []
            failed_values = []
            for value in all_values[1:]:  # Skip header row
                if value and value.strip():
                    try:
                        clean_username = self.extract_x_username(value.strip())
                        if clean_username:
                            usernames.append(clean_username)
                        else:
                            failed_values.append(value)
                            # logger.warning(f"Could not extract username from: {value}")
                    except Exception as e:
                        failed_values.append(value)
                        logger.warning(f"Error parsing username '{value}': {e}")

            logger.info(f"Retrieved {len(usernames)} monitored accounts from Google Sheet")
            logger.info(f"Failed to parse {len(failed_values)} values")
            if failed_values:
                logger.info(f"Failed values (first 10): {failed_values[:10]}")
            
            return usernames

        except Exception as e:
            logger.error(f"Failed to get monitored accounts: {e}")
            raise

    def extract_x_username(self, url_or_username: str) -> str:
        """
        Extract clean username from various Twitter/X URL formats.
        
        Args:
            url_or_username: URL or username string
            
        Returns:
            Clean username without @ symbol, or None if extraction fails
            
        Examples:
            >>> extract_x_username("https://twitter.com/username")
            "username"
            >>> extract_x_username("x.com/username")
            "username"
            >>> extract_x_username("@username")
            "username"
            >>> extract_x_username("username")
            "username"
        """
        if not url_or_username or not isinstance(url_or_username, str):
            return None
            
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
        
        # If no pattern matches, return None to indicate failure
        return None

    def test_connection(self) -> bool:
        """Test connection to Google Sheets."""
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.config.google_sheet_id)
            # Try to access the sheet title to verify connection
            _ = sheet.title
            logger.info("Google Sheets connection test successful")
            return True
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False

    def get_sheet_info(self) -> dict:
        """Get basic information about the Google Sheet."""
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.config.google_sheet_id)

            return {
                'title': sheet.title,
                'url': sheet.url,
                'worksheets': [ws.title for ws in sheet.worksheets()],
                'last_updated': sheet.updated
            }

        except Exception as e:
            logger.error(f"Failed to get sheet info: {e}")
            raise
