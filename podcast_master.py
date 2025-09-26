#!/usr/bin/env python3
"""
Podcast Master Control Script
Orchestrates all podcast system operations.
"""

import argparse
import logging
import sys
from datetime import datetime
import json

# Import all our modules
from podcast_fetcher import PodcastFetcher
from sermon_enhancer import SermonEnhancer
from podcast_analytics import PodcastAnalytics
from database_sync import DatabaseSync
from advanced_search import AdvancedSearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_master.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PodcastMaster:
    def __init__(self, config_file: str = "podcast_config.json"):
        """Initialize the master control system."""
        self.config_file = config_file
        self.fetcher = PodcastFetcher(config_file)
        self.enhancer = SermonEnhancer()
        self.analytics = PodcastAnalytics()
        self.database_sync = DatabaseSync()
        self.search = AdvancedSearch()
        
    def fetch_and_update(self):
        """Fetch new episodes and update data."""
        logger.info("Starting fetch and update process...")
        
        try:
            # Step 1: Fetch new episodes
            logger.info("Step 1: Fetching new episodes...")
            self.fetcher.fetch_all_podcasts()
            
            # Step 2: Enhance data with AI features
            logger.info("Step 2: Enhancing sermon data...")
            self.enhancer.enhance_all_sermons()
            
            # Step 3: Sync to database
            logger.info("Step 3: Syncing to database...")
            self.database_sync.full_sync()
            
            logger.info("Fetch and update process completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Fetch and update failed: {e}")
            return False
    
    def run_analytics(self):
        """Run analytics and generate reports."""
        logger.info("Running analytics...")
        
        try:
            # Generate analytics
            stats = self.analytics.get_basic_stats()
            insights = self.analytics.generate_insights()
            
            # Generate report
            report = self.analytics.generate_report()
            
            # Save report
            with open("podcast_analytics_report.md", "w") as f:
                f.write(report)
            
            # Create visualizations
            self.analytics.create_visualizations()
            
            logger.info("Analytics completed successfully!")
            logger.info(f"Total sermons: {stats.get('total_sermons', 0)}")
            logger.info(f"Key insights: {len(insights)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return False
    
    def search_sermons(self, query: str, **kwargs):
        """Search sermons with advanced features."""
        logger.info(f"Searching sermons for: {query}")
        
        try:
            results = self.search.advanced_search(query=query, **kwargs)
            logger.info(f"Found {len(results)} sermons")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_system_status(self):
        """Get overall system status."""
        try:
            # Check data files
            sermon_count = len(self.search.sermons)
            
            # Check last update
            last_update = "Unknown"
            try:
                with open("podcast_master.log", "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "Fetch and update process completed successfully" in line:
                            last_update = line.split(" - ")[0]
                            break
            except:
                pass
            
            # Check system health
            health_status = "healthy"
            if sermon_count == 0:
                health_status = "warning - no sermons found"
            
            return {
                'status': health_status,
                'sermon_count': sermon_count,
                'last_update': last_update,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def backup_data(self):
        """Create backup of all data."""
        logger.info("Creating data backup...")
        
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/backup_{timestamp}"
            
            # Create backup directory
            import os
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup data files
            data_files = [
                "data/sermons.json",
                "data/podcast_episodes.json",
                "data/podcast_series.json",
                "podcast_config.json"
            ]
            
            for file_path in data_files:
                try:
                    shutil.copy2(file_path, backup_dir)
                    logger.info(f"Backed up {file_path}")
                except FileNotFoundError:
                    logger.warning(f"File not found: {file_path}")
            
            # Backup logs
            try:
                shutil.copy2("podcast_master.log", backup_dir)
            except FileNotFoundError:
                pass
            
            logger.info(f"Backup created: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def restore_data(self, backup_dir: str):
        """Restore data from backup."""
        logger.info(f"Restoring data from: {backup_dir}")
        
        try:
            import shutil
            
            # Restore data files
            data_files = [
                "data/sermons.json",
                "data/podcast_episodes.json", 
                "data/podcast_series.json",
                "podcast_config.json"
            ]
            
            for file_path in data_files:
                backup_file = f"{backup_dir}/{file_path.split('/')[-1]}"
                try:
                    shutil.copy2(backup_file, file_path)
                    logger.info(f"Restored {file_path}")
                except FileNotFoundError:
                    logger.warning(f"Backup file not found: {backup_file}")
            
            logger.info("Data restore completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def list_backups(self):
        """List available backups."""
        try:
            import os
            backup_dir = "backups"
            
            if not os.path.exists(backup_dir):
                return []
            
            backups = []
            for item in os.listdir(backup_dir):
                if item.startswith("backup_"):
                    backup_path = os.path.join(backup_dir, item)
                    if os.path.isdir(backup_path):
                        backups.append({
                            'name': item,
                            'path': backup_path,
                            'created': os.path.getctime(backup_path)
                        })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"List backups failed: {e}")
            return []

def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description='Podcast Master Control System')
    parser.add_argument('command', choices=[
        'fetch', 'enhance', 'analytics', 'sync', 'search', 'status', 
        'backup', 'restore', 'list-backups', 'full-update'
    ], help='Command to execute')
    
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--author', help='Filter by author')
    parser.add_argument('--series', help='Filter by series')
    parser.add_argument('--limit', type=int, help='Limit results')
    parser.add_argument('--backup-dir', help='Backup directory for restore')
    parser.add_argument('--config', default='podcast_config.json', help='Config file')
    
    args = parser.parse_args()
    
    # Initialize master control
    master = PodcastMaster(args.config)
    
    try:
        if args.command == 'fetch':
            master.fetcher.fetch_all_podcasts()
            
        elif args.command == 'enhance':
            master.enhancer.enhance_all_sermons()
            
        elif args.command == 'analytics':
            master.run_analytics()
            
        elif args.command == 'sync':
            master.database_sync.full_sync()
            
        elif args.command == 'search':
            if not args.query:
                print("Error: --query is required for search")
                sys.exit(1)
            
            search_kwargs = {}
            if args.author:
                search_kwargs['author'] = args.author
            if args.series:
                search_kwargs['series'] = args.series
            if args.limit:
                search_kwargs['limit'] = args.limit
            
            results = master.search_sermons(args.query, **search_kwargs)
            
            print(f"Found {len(results)} sermons:")
            for sermon in results:
                print(f"- {sermon.get('title', 'Unknown')} ({sermon.get('date', 'No date')})")
                
        elif args.command == 'status':
            status = master.get_system_status()
            print(json.dumps(status, indent=2))
            
        elif args.command == 'backup':
            backup_dir = master.backup_data()
            if backup_dir:
                print(f"Backup created: {backup_dir}")
            else:
                print("Backup failed")
                sys.exit(1)
                
        elif args.command == 'restore':
            if not args.backup_dir:
                print("Error: --backup-dir is required for restore")
                sys.exit(1)
            
            if master.restore_data(args.backup_dir):
                print("Data restored successfully")
            else:
                print("Restore failed")
                sys.exit(1)
                
        elif args.command == 'list-backups':
            backups = master.list_backups()
            if backups:
                print("Available backups:")
                for backup in backups:
                    print(f"- {backup['name']} ({backup['path']})")
            else:
                print("No backups found")
                
        elif args.command == 'full-update':
            success = master.fetch_and_update()
            if success:
                print("Full update completed successfully")
            else:
                print("Full update failed")
                sys.exit(1)
        
        print("Command completed successfully!")
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
