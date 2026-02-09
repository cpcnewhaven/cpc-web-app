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
    
    # ── Series classification helpers ──────────────────────────────────

    SERIES_PATTERNS = [
        # Order matters: check "Beyond" before generic "Sunday Sermon"
        ('Beyond the Sunday Sermon', re.compile(r'Beyond the Sunday Sermon', re.IGNORECASE)),
        ('The Sunday Sermon',        re.compile(r'(?:The )?Sunday Sermon', re.IGNORECASE)),
        ('Walking with Jesus Through Sinai', re.compile(r'Walking with Jesus', re.IGNORECASE)),
        ('What We Believe',          re.compile(r'What We Believe', re.IGNORECASE)),
        ('Confessional Theology',    re.compile(r'Confessional', re.IGNORECASE)),
        ('Biblical Interpretation',  re.compile(r'Biblical Interpretation', re.IGNORECASE)),
        ('Membership Seminar',       re.compile(r'Membership Seminar|School of Discipleship', re.IGNORECASE)),
        ('Smokin\' Theologians',     re.compile(r'Smokin', re.IGNORECASE)),
        ('The Gospel according to Luke', re.compile(r'Gospel.*Luke|Luke \d', re.IGNORECASE)),
        ('The Book of Exodus',       re.compile(r'Exodus', re.IGNORECASE)),
        ('Why Do We Worship?',       re.compile(r'Why Do We Worship', re.IGNORECASE)),
        ('The Narrow Road to New Life', re.compile(r'Narrow (Road|Door)', re.IGNORECASE)),
    ]

    def classify_episode(self, title: str) -> Dict[str, str]:
        """Classify an episode into a series based on its title.

        Returns a dict with:
          series       – canonical series name
          sermon_type  – 'sermon', 'discussion', or 'teaching'
          guest_speaker – extracted guest name (if any)
        """
        series = ''
        sermon_type = 'sermon'
        guest_speaker = ''

        for series_name, pattern in self.SERIES_PATTERNS:
            if pattern.search(title):
                series = series_name
                break

        # If the title has "|" delimiters but matched no pattern, use the
        # last pipe-segment as a rough series label.
        if not series and '|' in title:
            series = title.split('|')[-1].strip()

        # Beyond episodes are discussions by default
        if series == 'Beyond the Sunday Sermon':
            sermon_type = 'discussion'

        # Extract guest from "With Guest <Name>" or "with <Name>"
        guest_match = re.search(r'[Ww]ith (?:Guest )?([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', title)
        if guest_match:
            guest_speaker = guest_match.group(1)

        return {
            'series': series or 'Uncategorized',
            'sermon_type': sermon_type,
            'guest_speaker': guest_speaker,
        }

    def _build_search_keywords(self, sermon: Dict) -> str:
        """Build a lowercase search-keyword string for quick filtering."""
        parts = [
            sermon.get('title', ''),
            sermon.get('author', ''),
            sermon.get('scripture', ''),
            sermon.get('series', ''),
            sermon.get('guest_speaker', ''),
            ' '.join(sermon.get('tags', [])),
        ]
        text = ' '.join(parts).lower()
        # Deduplicate words while preserving rough order
        seen = set()
        words = []
        for w in text.split():
            if w not in seen:
                seen.add(w)
                words.append(w)
        return ' '.join(words)

    # ── Convert raw feed episodes to the sermon JSON format ──────────

    def convert_to_sermon_format(self, episodes: List[Dict], source: str) -> List[Dict]:
        """Convert fetched episodes to sermon format with series classification."""
        sermons = []
        id_counter: Dict[str, int] = {}  # track collisions on date-based IDs

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
                base_id = date_obj.strftime('%y-%m-%d')
            except Exception:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
                base_id = datetime.now().strftime('%y-%m-%d')

            # Handle same-date ID collisions (append -1, -2, …)
            if base_id in id_counter:
                id_counter[base_id] += 1
                sermon_id = f"{base_id}-{id_counter[base_id]}"
            else:
                id_counter[base_id] = 0
                sermon_id = base_id

            # Get thumbnail URL
            thumbnail_url = ""
            if source == 'spotify' and episode.get('images'):
                thumbnail_url = episode['images'][0]['url']
            elif source == 'anchor' and episode.get('enclosures'):
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
                description = episode.get('description', '')
                spotify_match = re.search(r'https://open\.spotify\.com/episode/[a-zA-Z0-9]+', description)
                if spotify_match:
                    spotify_url = spotify_match.group(0)

                apple_match = re.search(r'https://podcasts\.apple\.com/[^\s]+', description)
                if apple_match:
                    apple_url = apple_match.group(0)

            # Classify into series
            title = episode.get('title', '')
            classification = self.classify_episode(title)

            # Build tags from series
            tags = []
            if classification['sermon_type'] == 'discussion':
                tags.append('Discussion')
            if classification['guest_speaker']:
                tags.append(f"Guest: {classification['guest_speaker']}")
            if classification['series'] and classification['series'] != 'Uncategorized':
                tags.append(classification['series'])

            sermon = {
                'id': sermon_id,
                'title': title,
                'author': 'Rev. Craig Luekens',
                'scripture': '',
                'date': formatted_date,
                'apple_podcasts_url': apple_url,
                'spotify_url': spotify_url,
                'link': spotify_url or episode.get('link', ''),
                'podcast_thumbnail_url': thumbnail_url,
                'youtube_url': '',
                'source': source,
                'original_id': episode.get('id', ''),
                'series': classification['series'],
                'episode_title': title,
                'guest_speaker': classification['guest_speaker'],
                'sermon_type': classification['sermon_type'],
                'tags': tags,
            }
            sermon['search_keywords'] = self._build_search_keywords(sermon)

            sermons.append(sermon)

        return sermons
    
    def update_sermons_json(self, new_sermons: List[Dict], output_file: str = "data/sermons.json"):
        """Update the sermons JSON file with new data, preserving existing entries."""
        try:
            # Load existing data
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "title": "Sunday Sermons",
                    "description": "Weekly sermons from our Sunday worship services",
                    "sermons": []
                }

            # Build dedup index using original_id (most reliable), fall back to id
            existing_by_original_id = {}
            existing_by_id = {}
            for sermon in data.get('sermons', []):
                oid = sermon.get('original_id', '')
                if oid:
                    existing_by_original_id[oid] = sermon
                existing_by_id[sermon['id']] = sermon

            # Add new sermons, avoiding duplicates
            added = 0
            enriched = 0
            for sermon in new_sermons:
                oid = sermon.get('original_id', '')

                # Check if already exists by original_id first, then by id
                existing = existing_by_original_id.get(oid) or existing_by_id.get(sermon['id'])

                if existing is None:
                    data['sermons'].append(sermon)
                    if oid:
                        existing_by_original_id[oid] = sermon
                    existing_by_id[sermon['id']] = sermon
                    added += 1
                    logger.info(f"Added new episode: {sermon['title']}")
                else:
                    # Enrich existing entry with any new fields it lacks
                    changed = False
                    for key in ('series', 'episode_title', 'guest_speaker',
                                'sermon_type', 'tags', 'search_keywords',
                                'spotify_url', 'apple_podcasts_url', 'link',
                                'podcast_thumbnail_url', 'original_id'):
                        new_val = sermon.get(key)
                        old_val = existing.get(key)
                        if new_val and not old_val:
                            existing[key] = new_val
                            changed = True
                    if changed:
                        enriched += 1

            if added or enriched:
                # Sort sermons by date (newest first)
                data['sermons'].sort(key=lambda x: x.get('date', ''), reverse=True)

                # Rebuild sermons_by_year
                by_year: Dict[str, List] = {}
                for s in data['sermons']:
                    year = s.get('date', '')[:4]
                    if year:
                        by_year.setdefault(year, []).append(s)
                data['sermons_by_year'] = dict(sorted(by_year.items()))

                # Update metadata counts
                year_counts = {}
                for year, slist in by_year.items():
                    year_counts[year] = {
                        "count": len(slist),
                        "note": f"{len(slist)} sermons from {year}"
                    }
                data['_year_counts'] = year_counts
                data['_total_sermons'] = len(data['sermons'])

                # Save updated data
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                logger.info(f"Updated {output_file}: {added} added, {enriched} enriched, {len(data['sermons'])} total")
            else:
                logger.info("No new sermons to add")

            return added, enriched

        except Exception as e:
            logger.error(f"Failed to update sermons JSON: {e}")
            return 0, 0
    
    # ── Podcast-episodes.json helpers ───────────────────────────────────

    # Map series names → series IDs used in podcast_series.json / podcast_episodes.json
    SERIES_ID_MAP = {
        'Beyond the Sunday Sermon':      'series_001',
        'Biblical Interpretation':       'series_002',
        'Confessional Theology':         'series_003',
        'Membership Seminar':            'series_004',
        'The Gospel according to Luke':  'series_005',
        'Smokin\' Theologians':          'series_006',
        'What We Believe':               'series_007',
        'The Book of Exodus':            'series_008',
        'Why Do We Worship?':            'series_009',
        'The Narrow Road to New Life':   'series_010',
        'The Sunday Sermon':             'series_011',
        'Walking with Jesus Through Sinai': 'series_012',
    }

    def update_podcast_episodes_json(self, sermons: List[Dict],
                                      output_file: str = "data/podcast_episodes.json"):
        """Update podcast_episodes.json with episode entries for all series."""
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_episodes = json.load(f)
            else:
                existing_episodes = []

            existing_ids = {ep.get('original_id') or ep.get('id') for ep in existing_episodes}
            added = 0

            for sermon in sermons:
                series_name = sermon.get('series', '')
                series_id = self.SERIES_ID_MAP.get(series_name)
                if not series_id:
                    continue  # Skip uncategorized

                # Dedup by original_id
                oid = sermon.get('original_id', '')
                if oid and oid in existing_ids:
                    continue

                ep = {
                    'id': f"ep_{sermon.get('original_id', sermon['id'])}",
                    'series_id': series_id,
                    'number': None,  # will be set below
                    'title': sermon.get('title', ''),
                    'link': sermon.get('link', ''),
                    'listen_url': sermon.get('spotify_url', '') or sermon.get('link', ''),
                    'handout_url': '',
                    'guest': sermon.get('guest_speaker', ''),
                    'date_added': sermon.get('date', ''),
                    'season': 1,
                    'scripture': sermon.get('scripture', ''),
                    'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', ''),
                    'original_id': oid,
                }
                existing_episodes.append(ep)
                if oid:
                    existing_ids.add(oid)
                added += 1

            if added:
                # Sort by date descending
                existing_episodes.sort(
                    key=lambda x: x.get('date_added', ''), reverse=True)

                # Re-number episodes per series (newest = highest number)
                from collections import defaultdict
                series_counters = defaultdict(int)
                # Count per series first (oldest → newest for numbering)
                episodes_by_series = defaultdict(list)
                for ep in existing_episodes:
                    episodes_by_series[ep['series_id']].append(ep)
                for sid, eps in episodes_by_series.items():
                    eps.sort(key=lambda x: x.get('date_added', ''))
                    for i, ep in enumerate(eps, 1):
                        ep['number'] = i

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_episodes, f, indent=2, ensure_ascii=False)

                logger.info(f"Updated {output_file}: {added} episodes added, {len(existing_episodes)} total")
            else:
                logger.info("No new podcast episodes to add")

            return added

        except Exception as e:
            logger.error(f"Failed to update podcast_episodes.json: {e}")
            return 0

    # ── Main orchestration ───────────────────────────────────────────

    def fetch_all_podcasts(self):
        """Fetch all configured podcasts and update JSON files."""
        if not self.config:
            logger.error("No configuration loaded")
            return

        all_sermons: List[Dict] = []

        # Fetch from Spotify API
        spotify_config = self.config.get('spotify', {})
        if spotify_config.get('enabled', False):
            show_ids = spotify_config.get('show_ids', [])
            for show_id in show_ids:
                logger.info(f"Fetching Spotify show: {show_id}")
                episodes = self.fetch_spotify_episodes(show_id)
                sermons = self.convert_to_sermon_format(episodes, 'spotify')
                all_sermons.extend(sermons)

        # Fetch from Anchor.fm RSS
        anchor_config = self.config.get('anchor', {})
        if anchor_config.get('enabled', False):
            rss_urls = anchor_config.get('rss_urls', [])
            for rss_url in rss_urls:
                logger.info(f"Fetching Anchor RSS: {rss_url}")
                episodes = self.fetch_anchor_rss(rss_url)
                sermons = self.convert_to_sermon_format(episodes, 'anchor')
                all_sermons.extend(sermons)

        if all_sermons:
            # 1. Update sermons.json (master data store)
            added, enriched = self.update_sermons_json(all_sermons)

            # 2. Update podcast_episodes.json (used by /api/json/podcasts)
            ep_added = self.update_podcast_episodes_json(all_sermons)

            # Summary
            sunday = sum(1 for s in all_sermons if s.get('series') == 'The Sunday Sermon')
            beyond = sum(1 for s in all_sermons if s.get('series') == 'Beyond the Sunday Sermon')
            other  = len(all_sermons) - sunday - beyond
            logger.info(f"Fetch complete — RSS episodes: {len(all_sermons)} "
                         f"(Sunday Sermons: {sunday}, Beyond: {beyond}, Other: {other})")
            logger.info(f"sermons.json: {added} added, {enriched} enriched")
            logger.info(f"podcast_episodes.json: {ep_added} added")
        else:
            logger.info("No episodes fetched from any source")

def main():
    """Main function to run the podcast fetcher."""
    fetcher = PodcastFetcher()
    fetcher.fetch_all_podcasts()

if __name__ == "__main__":
    main()
