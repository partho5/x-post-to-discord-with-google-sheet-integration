"""
Discord integration for sending X post notifications.
Handles database queries and Discord webhook communication.
"""

import requests
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

# Handle both direct execution and module import
if __name__ == "__main__":
    # Add the parent directory to sys.path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import Config
    from src.db_operations import DatabaseOperations
else:
    # Use relative imports when imported as a module
    from .config import Config
    from .db_operations import DatabaseOperations

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handles Discord webhook operations for X post notifications."""
    
    def __init__(self, config: Config = None):
        """
        Initialize Discord notifier.
        
        Args:
            config: Configuration object containing Discord settings
        """
        self.config = config or Config()
        self.db_ops = DatabaseOperations(self.config)
        self.webhook_url = self.config.discord_webhook_url
        self.max_retries = 3
        self.retry_delay = 5.0  # seconds
        
        if not self.webhook_url:
            raise ValueError("Discord webhook URL is required")
    
    def get_latest_post(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest pending post from the database.
        
        Returns:
            Dictionary containing post data or None if no pending posts
        """
        try:
            pending_posts = self.db_ops.get_posts_by_status('pending')
            
            if not pending_posts:
                logger.info("No pending posts found in database")
                return None
            
            # Get the latest post (first in the list since ordered by created_at DESC)
            latest_post = pending_posts[0]
            logger.info(f"Found latest pending post: ID {latest_post['id']}, Tweet ID {latest_post['tweet_id']}")
            return latest_post
            
        except Exception as e:
            logger.error(f"Failed to retrieve latest post from database: {e}")
            return None
    
    def send_to_discord(self, post_content: str, post_link: str, username: str) -> bool:
        """
        Send post content to Discord with retry logic.
        
        Args:
            post_content: The tweet content
            post_link: Link to the original X post
            username: X username who posted the tweet
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_message(post_content, post_link, username)
        
        for attempt in range(self.max_retries):
            try:
                success = self._send_message(message)
                if success:
                    logger.info(f"Successfully sent notification for @{username} post to Discord")
                    return True
                else:
                    logger.warning(f"Failed to send Discord notification (attempt {attempt + 1}/{self.max_retries})")
                    
            except Exception as e:
                logger.error(f"Error sending Discord notification (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        logger.error(f"Failed to send Discord notification after {self.max_retries} attempts")
        return False
    
    def mark_as_processed(self, post_id: int) -> bool:
        """
        Mark a post as processed in the database.
        
        Args:
            post_id: ID of the post to mark as processed
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            self.db_ops.update_post_status(post_id, 'processed')
            logger.info(f"Marked post ID {post_id} as processed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark post ID {post_id} as processed: {e}")
            return False
    
    def run(self) -> bool:
        """
        Main execution method - gets latest post and sends to Discord.
        
        Returns:
            True if notification was sent successfully, False otherwise
        """
        logger.info("Starting Discord notification process")
        
        try:
            # Get latest pending post
            latest_post = self.get_latest_post()
            if not latest_post:
                logger.info("No pending posts to process")
                return True
            
            # Send to Discord
            success = self.send_to_discord(
                post_content=latest_post['content'],
                post_link=latest_post['post_link'],
                username=latest_post['username']
            )
            
            if success:
                # Mark as processed
                processed_success = self.mark_as_processed(latest_post['id'])
                if processed_success:
                    logger.info("Discord notification process completed successfully")
                    return True
                else:
                    logger.error("Failed to mark post as processed after successful Discord send")
                    return False
            else:
                logger.error("Failed to send Discord notification")
                return False
                
        except Exception as e:
            logger.error(f"Error in Discord notification process: {e}")
            return False
    
    def _format_message(self, post_content: str, post_link: str, username: str) -> str:
        """
        Format the Discord message content.
        
        Args:
            post_content: The tweet content
            post_link: Link to the original X post
            username: X username
            
        Returns:
            Formatted message string
        """
        message = f"**New X Post from @{username}**\n\n"
        message += f"{post_content}\n\n"
        message += f"**Link:** {post_link}"
        return message
    
    def _send_message(self, message: str) -> bool:
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
            "avatar_url": None  # Using default Discord avatar
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 204:
                return True
            else:
                logger.error(f"Discord webhook error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Discord message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord message: {e}")
            return False


def main():
    """Entry point when run as a script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        notifier = DiscordNotifier()
        success = notifier.run()
        
        if success:
            logger.info("Discord notification script completed successfully")
        else:
            logger.error("Discord notification script failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in Discord notification script: {e}")
        exit(1)


if __name__ == "__main__":
    main()
