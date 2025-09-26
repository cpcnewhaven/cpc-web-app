#!/usr/bin/env python3
"""
Podcast Data Fetcher
Automatically pulls podcast data from Spotify API and Anchor.fm RSS feeds
and updates the JSON data files.
"""

import json
import requests
import feedparser
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import time
import re
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PodcastFetcher:
    def __init__(self, config_file: str = "podcast_config.json"):
        """Initialize the podcast fetcher with configuration."""
        self.config = self.load_config(config_file)
        self.spotify_token = None
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found. Please create it first.")
            return {}
    
    def get_spotify_token(self) -> Optional[str]:
        """Get Spotify access token using client credentials flow."""
        if not self.config.get('spotify'):
            logger.warning("Spotify configuration not found")
            return None
            
        spotify_config = self.config['spotify']
        client_id = spotify_config.get('client_id')
        client_secret = spotify_config.get('client_secret')
        
        if not client_id or not client_secret:
            logger.error("Spotify client_id and client_secret are required")
            return None
        
        # Spotify Client Credentials Flow
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            token_data = response.json()
            return token_data['access_token']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Spotify token: {e}")
            return None
    
    def fetch_spotify_episodes(self, show_id: str) -> List[Dict]:
        """Fetch episodes from Spotify show."""
        if not self.spotify_token:
            self.spotify_token = self.get_spotify_token()
            if not self.spotify_token:
                return []
        
        headers = {'Authorization': f'Bearer {self.spotify_token}'}
        episodes = []
        url = f'https://api.spotify.com/v1/shows/{show_id}/episodes'
        
        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                for episode in data.get('items', []):
                    episode_data = {
                        'id': episode['id'],
                        'title': episode['name'],
                        'description': episode.get('description', ''),
                        'release_date': episode['release_date'],
                        'duration_ms': episode.get('duration_ms', 0),
                        'external_urls': episode.get('external_urls', {}),
                        'images': episode.get('images', []),
                        'audio_preview_url': episode.get('audio_preview_url', ''),
                        'language': episode.get('language', 'en'),
                        'explicit': episode.get('explicit', False)
                    }
                    episodes.append(episode_data)
                
                url = data.get('next')  # Pagination
                if url:
                    time.sleep(0.1)  # Rate limiting
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch Spotify episodes: {e}")
                break
        
        return episodes
    
    def fetch_anchor_rss(self, rss_url: str) -> List[Dict]:
        """Fetch episodes from Anchor.fm RSS feed."""
        try:
            feed = feedparser.parse(rss_url)
            episodes = []
            
            for entry in feed.entries:
                # Extract episode ID from various possible sources
                episode_id = self.extract_episode_id(entry)
                
                episode_data = {
                    'id': episode_id,
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'enclosures': entry.get('enclosures', []),
                    'tags': [tag.term for tag in entry.get('tags', [])],
                    'summary': entry.get('summary', ''),
                    'author': entry.get('author', ''),
                    'duration': self.extract_duration(entry)
                }
                episodes.append(episode_data)
            
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to fetch Anchor RSS: {e}")
            return []
    
    def extract_episode_id(self, entry) -> str:
        """Extract episode ID from RSS entry."""
        # Try different methods to get episode ID
        if hasattr(entry, 'id'):
            return entry.id.split('/')[-1] if '/' in entry.id else entry.id
        
        if hasattr(entry, 'link'):
            # Extract ID from URL
            link = entry.link
            if 'spotify.com' in link:
                match = re.search(r'episode/([a-zA-Z0-9]+)', link)
                if match:
                    return match.group(1)
            elif 'anchor.fm' in link:
                return link.split('/')[-1]
        
        # Fallback to title hash
        import hashlib
        return hashlib.md5(entry.title.encode()).hexdigest()[:12]
    
    def extract_duration(self, entry) -> int:
        """Extract duration in seconds from RSS entry."""
        duration = 0
        
        # Check iTunes namespace
        if hasattr(entry, 'itunes_duration'):
            duration_str = entry.itunes_duration
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:  # MM:SS
                    duration = int(parts[0]) * 60 + int(parts[1])
            else:
                duration = int(duration_str)
        
        return duration
    
    def convert_to_sermon_format(self, episodes: List[Dict], source: str) -> List[Dict]:
        """Convert fetched episodes to sermon format."""
        sermons = []
        
        for episode in episodes:
            # Extract date
            if source == 'spotify':
                date_str = episode.get('release_date', '')
            else:  # anchor
                date_str = episode.get('published', '')
            
            # Parse and format date
            try:
                if source == 'spotify':
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    from email.utils import parsedate_to_datetime
                    date_obj = parsedate_to_datetime(date_str)
                
                formatted_date = date_obj.strftime('%Y-%m-%d')
                sermon_id = date_obj.strftime('%y-%m-%d')
            except:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
                sermon_id = datetime.now().strftime('%y-%m-%d')
            
            # Get thumbnail URL
            thumbnail_url = ""
            if source == 'spotify' and episode.get('images'):
                thumbnail_url = episode['images'][0]['url']
            elif source == 'anchor' and episode.get('enclosures'):
                # Try to find image in enclosures or use default
                for enc in episode['enclosures']:
                    if enc.get('type', '').startswith('image'):
                        thumbnail_url = enc['href']
                        break
            
            # Get external URLs
            spotify_url = ""
            apple_url = ""
            
            if source == 'spotify':
                spotify_url = episode.get('external_urls', {}).get('spotify', '')
            elif source == 'anchor':
                # Try to find Spotify URL in description or other fields
                description = episode.get('description', '')
                spotify_match = re.search(r'https://open\.spotify\.com/episode/[a-zA-Z0-9]+', description)
                if spotify_match:
                    spotify_url = spotify_match.group(0)
                
                apple_match = re.search(r'https://podcasts\.apple\.com/[^\s]+', description)
                if apple_match:
                    apple_url = apple_match.group(0)
            
            sermon = {
                'id': sermon_id,
                'title': episode.get('title', ''),
                'author': 'Rev. Craig Luekens',  # Default, can be customized
                'scripture': '',  # Would need to be extracted or added manually
                'date': formatted_date,
                'apple_podcasts_url': apple_url,
                'spotify_url': spotify_url,
                'link': spotify_url or episode.get('link', ''),
                'podcast_thumbnail_url': thumbnail_url,
                'youtube_url': '',  # Would need to be added manually
                'source': source,
                'original_id': episode.get('id', '')
            }
            
            sermons.append(sermon)
        
        return sermons
    
    def update_sermons_json(self, new_sermons: List[Dict], output_file: str = "data/sermons.json"):
        """Update the sermons JSON file with new data."""
        try:
            # Load existing data
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {
                    "title": "Sunday Sermons",
                    "description": "Weekly sermons from our Sunday worship services",
                    "sermons": []
                }
            
            existing_sermons = {sermon['id']: sermon for sermon in data.get('sermons', [])}
            
            # Add new sermons, avoiding duplicates
            updated = False
            for sermon in new_sermons:
                if sermon['id'] not in existing_sermons:
                    data['sermons'].append(sermon)
                    updated = True
                    logger.info(f"Added new sermon: {sermon['title']}")
                else:
                    # Update existing sermon if it has new data
                    existing = existing_sermons[sermon['id']]
                    if sermon.get('spotify_url') and not existing.get('spotify_url'):
                        existing.update(sermon)
                        updated = True
                        logger.info(f"Updated sermon: {sermon['title']}")
            
            if updated:
                # Sort sermons by date (newest first)
                data['sermons'].sort(key=lambda x: x['date'], reverse=True)
                
                # Save updated data
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Updated {output_file} with new sermon data")
            else:
                logger.info("No new sermons to add")
                
        except Exception as e:
            logger.error(f"Failed to update sermons JSON: {e}")
    
    def fetch_all_podcasts(self):
        """Fetch all configured podcasts and update JSON files."""
        if not self.config:
            logger.error("No configuration loaded")
            return
        
        # Fetch from Spotify
        spotify_config = self.config.get('spotify', {})
        if spotify_config.get('enabled', False):
            show_ids = spotify_config.get('show_ids', [])
            for show_id in show_ids:
                logger.info(f"Fetching Spotify show: {show_id}")
                episodes = self.fetch_spotify_episodes(show_id)
                sermons = self.convert_to_sermon_format(episodes, 'spotify')
                self.update_sermons_json(sermons)
        
        # Fetch from Anchor.fm
        anchor_config = self.config.get('anchor', {})
        if anchor_config.get('enabled', False):
            rss_urls = anchor_config.get('rss_urls', [])
            for rss_url in rss_urls:
                logger.info(f"Fetching Anchor RSS: {rss_url}")
                episodes = self.fetch_anchor_rss(rss_url)
                sermons = self.convert_to_sermon_format(episodes, 'anchor')
                self.update_sermons_json(sermons)

def main():
    """Main function to run the podcast fetcher."""
    fetcher = PodcastFetcher()
    fetcher.fetch_all_podcasts()

if __name__ == "__main__":
    main()
