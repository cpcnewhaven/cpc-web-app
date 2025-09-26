#!/usr/bin/env python3
"""
Database Synchronization
Syncs JSON data with the Flask database automatically.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Import your Flask app models
try:
    from app import app, db
    from models import Sermon, PodcastEpisode, PodcastSeries
except ImportError:
    print("Warning: Could not import Flask models. Make sure you're in the correct directory.")
    app = None
    db = None

logger = logging.getLogger(__name__)

class DatabaseSync:
    def __init__(self, sermons_file: str = "data/sermons.json"):
        self.sermons_file = sermons_file
        self.sermons_data = self.load_sermons()
        
    def load_sermons(self) -> Dict:
        """Load sermons data from JSON file."""
        try:
            with open(self.sermons_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sermons file {self.sermons_file} not found")
            return {"sermons": []}
    
    def sync_sermons_to_database(self):
        """Sync sermons from JSON to database."""
        if not app or not db:
            logger.error("Flask app or database not available")
            return
        
        with app.app_context():
            try:
                sermons = self.sermons_data.get('sermons', [])
                synced_count = 0
                updated_count = 0
                
                for sermon_data in sermons:
                    # Check if sermon already exists
                    existing_sermon = Sermon.query.filter_by(id=sermon_data.get('id')).first()
                    
                    if existing_sermon:
                        # Update existing sermon
                        self.update_sermon(existing_sermon, sermon_data)
                        updated_count += 1
                        logger.info(f"Updated sermon: {sermon_data.get('title', 'Unknown')}")
                    else:
                        # Create new sermon
                        new_sermon = self.create_sermon(sermon_data)
                        if new_sermon:
                            db.session.add(new_sermon)
                            synced_count += 1
                            logger.info(f"Added new sermon: {sermon_data.get('title', 'Unknown')}")
                
                db.session.commit()
                logger.info(f"Database sync completed: {synced_count} new, {updated_count} updated")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database sync failed: {e}")
                raise
    
    def create_sermon(self, sermon_data: Dict) -> Optional[Sermon]:
        """Create a new Sermon object from JSON data."""
        try:
            # Parse date
            date_str = sermon_data.get('date', '')
            sermon_date = None
            if date_str:
                try:
                    sermon_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
            
            return Sermon(
                id=sermon_data.get('id', ''),
                title=sermon_data.get('title', ''),
                author=sermon_data.get('author', ''),
                scripture=sermon_data.get('scripture', ''),
                date=sermon_date,
                spotify_url=sermon_data.get('spotify_url', ''),
                youtube_url=sermon_data.get('youtube_url', ''),
                apple_podcasts_url=sermon_data.get('apple_podcasts_url', ''),
                podcast_thumbnail_url=sermon_data.get('podcast_thumbnail_url', '')
            )
        except Exception as e:
            logger.error(f"Error creating sermon: {e}")
            return None
    
    def update_sermon(self, existing_sermon: Sermon, sermon_data: Dict):
        """Update existing sermon with new data."""
        try:
            # Update fields if they're not empty in the new data
            if sermon_data.get('title'):
                existing_sermon.title = sermon_data['title']
            if sermon_data.get('author'):
                existing_sermon.author = sermon_data['author']
            if sermon_data.get('scripture'):
                existing_sermon.scripture = sermon_data['scripture']
            
            # Update date
            date_str = sermon_data.get('date', '')
            if date_str:
                try:
                    sermon_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    existing_sermon.date = sermon_date
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
            
            # Update URLs
            if sermon_data.get('spotify_url'):
                existing_sermon.spotify_url = sermon_data['spotify_url']
            if sermon_data.get('youtube_url'):
                existing_sermon.youtube_url = sermon_data['youtube_url']
            if sermon_data.get('apple_podcasts_url'):
                existing_sermon.apple_podcasts_url = sermon_data['apple_podcasts_url']
            if sermon_data.get('podcast_thumbnail_url'):
                existing_sermon.podcast_thumbnail_url = sermon_data['podcast_thumbnail_url']
                
        except Exception as e:
            logger.error(f"Error updating sermon: {e}")
    
    def sync_podcast_series(self):
        """Sync podcast series data to database."""
        if not app or not db:
            return
        
        with app.app_context():
            try:
                # Get unique series from sermons
                series_data = {}
                for sermon in self.sermons_data.get('sermons', []):
                    series_name = sermon.get('series', 'Sunday Sermons')
                    if series_name not in series_data:
                        series_data[series_name] = {
                            'title': series_name,
                            'description': self.get_series_description(series_name),
                            'sermon_count': 0
                        }
                    series_data[series_name]['sermon_count'] += 1
                
                # Sync series to database
                for series_name, series_info in series_data.items():
                    existing_series = PodcastSeries.query.filter_by(title=series_name).first()
                    
                    if not existing_series:
                        new_series = PodcastSeries(
                            id=f"series_{series_name.lower().replace(' ', '_')}",
                            title=series_info['title'],
                            description=series_info['description']
                        )
                        db.session.add(new_series)
                        logger.info(f"Added new series: {series_name}")
                    else:
                        existing_series.description = series_info['description']
                        logger.info(f"Updated series: {series_name}")
                
                db.session.commit()
                logger.info("Podcast series sync completed")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Podcast series sync failed: {e}")
    
    def get_series_description(self, series_name: str) -> str:
        """Get description for a series based on its name."""
        descriptions = {
            'Sunday Sermons': 'Weekly messages from our Sunday worship services',
            'Beyond the Sunday Sermon': 'Extended conversations and deeper dives into biblical topics',
            'What We Believe': 'Teaching series on Reformed theology and doctrine',
            'Confessional Theology': 'Exploring Reformed theology through systematic study',
            'School of Discipleship': 'Comprehensive membership course and Christian formation',
            'Walking with Jesus Through Sinai': 'Study of the Ten Commandments and moral clarity'
        }
        return descriptions.get(series_name, f'Podcast series: {series_name}')
    
    def sync_podcast_episodes(self):
        """Sync individual podcast episodes to database."""
        if not app or not db:
            return
        
        with app.app_context():
            try:
                episodes = self.sermons_data.get('sermons', [])
                synced_count = 0
                
                for episode_data in episodes:
                    series_name = episode_data.get('series', 'Sunday Sermons')
                    series = PodcastSeries.query.filter_by(title=series_name).first()
                    
                    if not series:
                        logger.warning(f"Series not found: {series_name}")
                        continue
                    
                    # Check if episode already exists
                    existing_episode = PodcastEpisode.query.filter_by(
                        series_id=series.id,
                        title=episode_data.get('title', '')
                    ).first()
                    
                    if not existing_episode:
                        new_episode = PodcastEpisode(
                            id=episode_data.get('id', ''),
                            series_id=series.id,
                            number=len(PodcastEpisode.query.filter_by(series_id=series.id).all()) + 1,
                            title=episode_data.get('title', ''),
                            link=episode_data.get('link', ''),
                            listen_url=episode_data.get('spotify_url', ''),
                            guest=episode_data.get('guest_speaker', ''),
                            date_added=datetime.now().date(),
                            season=1,
                            scripture=episode_data.get('scripture', ''),
                            podcast_thumbnail_url=episode_data.get('podcast_thumbnail_url', '')
                        )
                        db.session.add(new_episode)
                        synced_count += 1
                        logger.info(f"Added new episode: {episode_data.get('title', 'Unknown')}")
                
                db.session.commit()
                logger.info(f"Podcast episodes sync completed: {synced_count} new episodes")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Podcast episodes sync failed: {e}")
    
    def full_sync(self):
        """Perform a full synchronization of all data."""
        logger.info("Starting full database synchronization...")
        
        # Sync in order: series first, then sermons, then episodes
        self.sync_podcast_series()
        self.sync_sermons_to_database()
        self.sync_podcast_episodes()
        
        logger.info("Full database synchronization completed!")

def main():
    """Main function to run database sync."""
    sync = DatabaseSync()
    sync.full_sync()

if __name__ == "__main__":
    main()
