"""
Discord integration for sending alerts and notifications.
"""

import aiohttp
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.helpers import format_discord_message


class DiscordNotifier:
    """Handles Discord webhook operations."""
    
    def __init__(self, webhook_url: str, max_retries: int = 3, retry_delay: float = 1200.0):
        """
        Initialize Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds (default: 1200 seconds)
        """
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
    
    async def send_alert(self, tweet_data: Dict[str, Any], summary: str) -> bool:
        """
        Send a single alert to Discord.
        
        Args:
            tweet_data: Tweet information dictionary
            summary: AI-generated summary
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = format_discord_message(tweet_data, summary)
        
        for attempt in range(self.max_retries):
            try:
                success = await self._send_message(message)
                if success:
                    self.logger.info(f"Sent alert for tweet {tweet_data.get('id', 'unknown')}")
                    return True
                else:
                    self.logger.warning(f"Failed to send alert (attempt {attempt + 1}/{self.max_retries})")
                    
            except Exception as e:
                self.logger.error(f"Error sending alert (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        self.logger.error(f"Failed to send alert after {self.max_retries} attempts")
        return False
    
    async def send_alerts_batch(self, alerts: List[Dict[str, Any]]) -> List[bool]:
        """
        Send multiple alerts in batch.
        
        Args:
            alerts: List of alert dictionaries with tweet_data and summary
            
        Returns:
            List of success status for each alert
        """
        results = []
        
        for alert in alerts:
            try:
                success = await self.send_alert(alert['tweet_data'], alert['summary'])
                results.append(success)
            except Exception as e:
                self.logger.error(f"Error sending alert: {e}")
                results.append(False)
        
        successful = sum(results)
        total = len(results)
        self.logger.info(f"Sent {successful}/{total} alerts successfully")
        
        return results
    
    async def _send_message(self, message: str) -> bool:
        """
        Send a message to Discord webhook.
        
        Args:
            message: Message content
            
        Returns:
            True if sent successfully, False otherwise
        """
        payload = {
            "content": message,
            "username": "X-Notifier Bot",
            "avatar_url": "https://cdn.discordapp.com/emojis/1234567890.png"  # Optional: custom avatar
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Discord webhook error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Discord message: {e}")
            return False
    
    async def send_status_message(self, message: str) -> bool:
        """
        Send a status/notification message to Discord.
        
        Args:
            message: Status message
            
        Returns:
            True if sent successfully, False otherwise
        """
        payload = {
            "content": f"ℹ️ **Bot Status:** {message}",
            "username": "X-Notifier Bot"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Status message webhook error {response.status}: {error_text}")
                        return False
        except Exception as e:
            self.logger.error(f"Error sending status message: {e}")
            return False
    
    async def test_webhook(self) -> bool:
        """
        Test Discord webhook connection.
        
        Returns:
            True if webhook is working, False otherwise
        """
        test_message = "🧪 **Test Message**\n\nThis is a test message from the X-Discord Bot to verify the webhook is working correctly."
        
        return await self._send_message(test_message) 