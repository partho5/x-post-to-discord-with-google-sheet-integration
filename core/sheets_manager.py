"""
Google Sheets integration for the X-Discord-Google-Sheet Bot.
"""

import gspread
import logging
from google.oauth2.service_account import Credentials
from typing import List, Optional
from pathlib import Path

from utils.helpers import parse_username


class SheetsManager:
    """Manages Google Sheets operations."""
    
    def __init__(self, credentials_path: Path, sheet_id: str):
        """
        Initialize sheets manager.
        
        Args:
            credentials_path: Path to Google service account credentials
            sheet_id: Google Sheet ID
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.logger = logging.getLogger(__name__)
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
                
                # Load credentials
                credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=scope
                )
                
                # Create client
                self._client = gspread.authorize(credentials)
                self.logger.info("Google Sheets client initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Sheets client: {e}")
                raise
        
        return self._client
    
    def get_monitored_accounts(self) -> List[str]:
        """
        Get list of monitored Twitter accounts from Google Sheet.
        
        Returns:
            List of clean usernames
            
        Raises:
            Exception: If sheet access fails
        """
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.sheet_id)
            
            # Get the first worksheet
            worksheet = sheet.get_worksheet(0)
            if not worksheet:
                raise Exception("No worksheets found in the Google Sheet")
            
            # Get all values from column A (first column)
            all_values = worksheet.col_values(1)
            
            # Filter out empty values and header row
            accounts = []
            for value in all_values[1:]:  # Skip header row
                if value and value.strip():
                    try:
                        clean_username = parse_username(value.strip())
                        if clean_username:
                            accounts.append(clean_username)
                        else:
                            self.logger.warning(f"Could not parse username from: {value}")
                    except Exception as e:
                        self.logger.warning(f"Error parsing username '{value}': {e}")
            
            self.logger.info(f"Retrieved {len(accounts)} monitored accounts from Google Sheet")
            return accounts
            
        except Exception as e:
            self.logger.error(f"Failed to get monitored accounts: {e}")
            raise
    
    def get_sheet_info(self) -> dict:
        """
        Get basic information about the Google Sheet.
        
        Returns:
            Dictionary with sheet information
        """
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.sheet_id)
            
            return {
                'title': sheet.title,
                'url': sheet.url,
                'worksheets': [ws.title for ws in sheet.worksheets()],
                'last_updated': sheet.updated
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sheet info: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to Google Sheets.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self._get_client()
            sheet = client.open_by_key(self.sheet_id)
            # Try to access the sheet title to verify connection
            _ = sheet.title
            self.logger.info("Google Sheets connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Google Sheets connection test failed: {e}")
            return False 