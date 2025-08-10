#!/usr/bin/env python3
"""
X-Discord-Google-Sheet Bot
Main entry point for the automated Twitter monitoring and Discord alerting system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from core.pipeline import Pipeline
from utils.config import Config
from utils.logger import setup_logging


async def main():
    """Main entry point for the application."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting X-Discord-Google-Sheet Bot")
        
        # Load configuration
        config = Config()
        
        # Initialize pipeline
        pipeline = Pipeline(config)
        
        # Send startup notification (comment out this line to disable)
        # await pipeline.discord_notifier.send_status_message("Bot started successfully!")
        
        # Run the pipeline
        await run_pipeline(pipeline)
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def run_pipeline(pipeline: Pipeline):
    """Run the main monitoring pipeline."""
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            # Check if we're under a global rate limit
            if pipeline.tweet_fetcher._check_global_rate_limit():
                logger.info("Global rate limit active, waiting 20 minutes before retry...")
                await asyncio.sleep(1200)  # Wait 20 minutes
                continue

            # Then: Run the pipeline (scraping)
            await pipeline.run()
            
            # Wait 20 minutes before next pipeline run
            await asyncio.sleep(1200)  # 20 minutes
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            await asyncio.sleep(1200)  # Wait 20 minutes before retrying








if __name__ == "__main__":
    asyncio.run(main())
