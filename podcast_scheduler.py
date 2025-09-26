#!/usr/bin/env python3
"""
Podcast Scheduler
Automatically runs the podcast fetcher at regular intervals.
"""

import schedule
import time
import logging
import os
import sys
from datetime import datetime
from podcast_fetcher import PodcastFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PodcastScheduler:
    def __init__(self, config_file: str = "podcast_config.json"):
        """Initialize the scheduler."""
        self.fetcher = PodcastFetcher(config_file)
        self.config = self.fetcher.config
        self.update_interval = self.config.get('settings', {}).get('update_interval_hours', 6)
        
    def run_fetch(self):
        """Run the podcast fetch process."""
        logger.info("Starting scheduled podcast fetch...")
        try:
            self.fetcher.fetch_all_podcasts()
            logger.info("Podcast fetch completed successfully")
        except Exception as e:
            logger.error(f"Error during podcast fetch: {e}")
    
    def start_scheduler(self):
        """Start the scheduler."""
        logger.info(f"Starting podcast scheduler with {self.update_interval} hour intervals")
        
        # Schedule the job
        schedule.every(self.update_interval).hours.do(self.run_fetch)
        
        # Run immediately on start
        self.run_fetch()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_once(self):
        """Run the fetch process once and exit."""
        logger.info("Running podcast fetch once...")
        self.run_fetch()

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Podcast Scheduler')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit instead of scheduling')
    parser.add_argument('--config', default='podcast_config.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    scheduler = PodcastScheduler(args.config)
    
    if args.once:
        scheduler.run_once()
    else:
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()
