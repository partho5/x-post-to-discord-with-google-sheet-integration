#!/usr/bin/env python3
"""
Standalone Posting Script for X-Discord-Google-Sheet Bot

This script can be run independently to post the latest pending tweet to Discord.
It's designed to be triggered by cron jobs or system schedulers.

Usage:
    python post_latest.py

Environment Variables Required:
    - DISCORD_WEBHOOK_URL: Discord webhook URL for sending alerts
    - All other config variables (Twitter API, OpenAI, Google Sheets, etc.)

Features:
    - Gets the latest pending post from the database
    - Sends it to Discord if it exists
    - Removes the post from database after successful sending
    - Provides detailed logging for monitoring
    - Safe to run multiple times (won't duplicate posts)

Exit Codes:
    - 0: Success (posted or no posts to send)
    - 1: Error occurred

Example Cron Job (every hour at minute 0):
    0 * * * * cd /path/to/project && /path/to/venv/bin/python post_latest.py

Example System Scheduler (Windows):
    Create a scheduled task that runs:
    C:\path\to\venv\Scripts\python.exe C:\path\to\project\post_latest.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from core.discord_notifier import DiscordNotifier
from core.state_manager import StateManager
from utils.config import Config
from utils.logger import setup_logging


async def post_latest_pending():
    """
    Post the latest pending tweet to Discord.
    
    Returns:
        bool: True if successful (posted or no posts), False if error occurred
    """
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting standalone posting script")
        
        # Load configuration
        config = Config()
        
        # Initialize components
        state_manager = StateManager(config.db_path)
        discord_notifier = DiscordNotifier(config.discord_webhook_url)
        
        # Get latest pending post
        latest_post = state_manager.get_latest_pending_post()
        
        if not latest_post:
            logger.info("No pending posts found in database")
            return True
        
        logger.info(f"Found pending post: {latest_post['tweet_id']} from @{latest_post['username']}")
        
        # Prepare tweet data for Discord
        tweet_data = {
            'id': latest_post['tweet_id'],
            'text': latest_post['tweet_text'],
            'username': latest_post['username'],
            'created_at': latest_post['created_at']
        }
        
        summary = latest_post['ai_summary']
        
        # Send to Discord
        logger.info("Sending post to Discord...")
        success = await discord_notifier.send_alert(tweet_data, summary)
        
        if success:
            # Remove the posted content from database
            state_manager.delete_pending_post(latest_post['tweet_id'])
            logger.info(f"Successfully posted and removed tweet {latest_post['tweet_id']} from database")
            return True
        else:
            logger.error(f"Failed to post tweet {latest_post['tweet_id']} to Discord")
            return False
            
    except Exception as e:
        logger.error(f"Error in posting script: {e}", exc_info=True)
        return False


async def main():
    """
    Main entry point for the standalone posting script.
    
    Exit codes:
        - 0: Success (posted or no posts to send)
        - 1: Error occurred
    """
    try:
        success = await post_latest_pending()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 