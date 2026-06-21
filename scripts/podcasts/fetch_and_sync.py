#!/usr/bin/env python3
"""
Fetch latest podcast episodes from Anchor/Spotify and sync into the database.
This is the script called by the Render cron service.
"""

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        from podcast_fetcher import PodcastFetcher
        from populate_podcasts import populate_podcasts

        logger.info("Starting podcast fetch and sync...")

        # 1. Fetch latest episodes from Anchor RSS and Spotify
        logger.info("Fetching episodes from configured sources...")
        fetcher = PodcastFetcher()
        fetcher.fetch_all_podcasts()

        # 2. Sync fetched episodes into the database
        logger.info("Syncing episodes into database...")
        populate_podcasts()

        logger.info("Podcast fetch and sync completed successfully!")

    except Exception as e:
        logger.error(f"Podcast sync failed: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
