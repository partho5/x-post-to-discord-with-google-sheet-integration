#!/usr/bin/env python3
"""
Test script for X-Discord-Google-Sheet Bot setup.
Use this to verify your configuration and test individual components.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.config import Config
from utils.logger import setup_logging
from core.pipeline import Pipeline


async def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        config = Config()
        config.validate()
        print("Configuration loaded successfully")
        return config
    except Exception as e:
        print(f" Configuration error: {e}")
        return None


async def test_connections(config):
    """Test all external connections."""
    print("\n Testing external connections...")
    
    try:
        pipeline = Pipeline(config)
        results = await pipeline.test_all_connections()
        
        for service, status in results.items():
            status_icon = "" if status else ""
            print(f"{status_icon} {service.replace('_', ' ').title()}: {'Connected' if status else 'Failed'}")
        
        return results
    except Exception as e:
        print(f" Connection test error: {e}")
        return {}


async def test_pipeline_run(config):
    """Test a single pipeline run."""
    print("\n Testing pipeline execution...")
    
    try:
        pipeline = Pipeline(config)
        await pipeline.run()
        print(" Pipeline executed successfully")
        return True
    except Exception as e:
        print(f" Pipeline execution error: {e}")
        return False


async def main():
    """Main test function."""
    print(" X-Discord-Google-Sheet Bot Setup Test")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Test configuration
    config = await test_configuration()
    if not config:
        print("\n Configuration test failed. Please check your .env file.")
        return
    
    # Test connections
    connection_results = await test_connections(config)
    
    # Summary
    print("\n Test Summary:")
    print("-" * 30)
    
    if connection_results:
        successful = sum(connection_results.values())
        total = len(connection_results)
        print(f"Connections: {successful}/{total} successful")
        
        if successful == total:
            print(" All tests passed! Your bot is ready to run.")
            print("\nTo start the bot, run: python main.py")
        else:
            print("Some connections failed. Please check your credentials and try again.")
    else:
        print(" Connection tests failed. Please check your setup.")


if __name__ == "__main__":
    asyncio.run(main()) 