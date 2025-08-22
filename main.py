#!/usr/bin/env python3
"""
Main entry point for X to Discord posting pipeline
"""

from src.x2discord_pipeline import X2DiscordPipeline


def main():
    """Main function to run the X to Discord pipeline"""
    pipeline = X2DiscordPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
