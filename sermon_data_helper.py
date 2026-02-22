#!/_usr_bin_env python3
"""
Sermon Data Helper - Database Powered
Sourced from the Render PostgreSQL database instead of JSON files.
Author: Antigravity
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from database import db
from models import Sermon, SermonSeries

logger = logging.getLogger(__name__)

class SermonDataHelper:
    """Helper class for database-driven sermon data access"""
    
    def __init__(self, sermons_file: str = None):
        # We ignore sermons_file now as we use the database
        pass
    
    def _sermon_to_dict(self, sermon: Sermon) -> Dict:
        """Convert a Sermon model instance to a dictionary for API compatibility."""
        series_name = sermon.series.title if sermon.series else "The Sunday Sermon"
        return {
            'id': sermon.id,
            'title': sermon.title,
            'speaker': sermon.speaker or '',
            'author': sermon.speaker or '', # Keep for backward compatibility
            'scripture': sermon.scripture or '',
            'date': sermon.date.isoformat() if sermon.date else '',
            'active': sermon.active,
            'archived': sermon.archived,
            'spotify_url': sermon.spotify_url,
            'youtube_url': sermon.youtube_url,
            'apple_podcasts_url': sermon.apple_podcasts_url,
            'podcast_thumbnail_url': sermon.podcast_thumbnail_url,
            'series': series_name,
            'episode_number': sermon.episode_number,
            'audio_file_url': sermon.audio_file_url,
            'video_file_url': sermon.video_file_url,
            'link': sermon.spotify_url or sermon.youtube_url or sermon.apple_podcasts_url,
            'tags': [], # Tags are not yet fully implemented in the model as a separate table
            'sermon_type': 'sermon'
        }
    
    def get_all_sermons(self) -> List[Dict]:
        """Get all active sermons from the database."""
        try:
            sermons = Sermon.query.filter_by(active=True, archived=False).order_by(Sermon.date.desc()).all()
            return [self._sermon_to_dict(s) for s in sermons]
        except Exception as e:
            logger.error(f"Error fetching sermons from database: {e}")
            return []
    
    def get_sermons_by_year(self, year: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Get sermons organized by year"""
        all_sermons = self.get_all_sermons()
        sermons_by_year = {}
        
        for sermon in all_sermons:
            s_year = sermon['date'][:4] if sermon['date'] else '_no_date'
            if s_year not in sermons_by_year:
                sermons_by_year[s_year] = []
            sermons_by_year[s_year].append(sermon)
            
        if year:
            return {year: sermons_by_year.get(year, [])}
        return sermons_by_year
    
    def get_year_counts(self) -> Dict:
        """Get year counts metadata"""
        sermons_by_year = self.get_sermons_by_year()
        return {year: len(sermons) for year, sermons in sermons_by_year.items()}
    
    def get_metadata(self) -> Dict:
        """Get metadata (title, description, etc.)"""
        all_sermons = self.get_all_sermons()
        return {
            'title': 'Sunday Sermons',
            'description': 'Weekly sermons from our Sunday worship services',
            'total_sermons': len(all_sermons),
            'year_counts': self.get_year_counts()
        }
    
    def search_sermons(self, query: str = None, year: str = None, 
                      speaker: str = None, series: str = None) -> List[Dict]:
        """Search sermons with optional filters using database queries."""
        q = Sermon.query.filter_by(active=True, archived=False)
        
        if year:
            # Simple year filter
            q = q.filter(db.extract('year', Sermon.date) == int(year))
            
        if speaker:
            q = q.filter(Sermon.speaker.ilike(f'%{speaker}%'))
            
        if series:
            q = q.join(Sermon.series).filter(SermonSeries.title.ilike(f'%{series}%'))
            
        if query:
            q = q.filter(db.or_(
                Sermon.title.ilike(f'%{query}%'),
                Sermon.scripture.ilike(f'%{query}%'),
                Sermon.speaker.ilike(f'%{query}%')
            ))
            
        results = q.order_by(Sermon.date.desc()).all()
        return [self._sermon_to_dict(s) for s in results]
    
    def get_archive_sermons(self, cutoff_days: int = 90) -> List[Dict]:
        """Get archived sermons."""
        try:
            sermons = Sermon.query.filter_by(archived=True).order_by(Sermon.date.desc()).all()
            return [self._sermon_to_dict(s) for s in sermons]
        except Exception as e:
            logger.error(f"Error fetching archived sermons: {e}")
            return []
    
    def get_latest_luke_chapter(self) -> Optional[Dict]:
        """Find the latest Luke chapter from all sermons."""
        import re
        all_sermons = self.get_all_sermons()
        luke_sermons = []
        luke_pattern = re.compile(r'luke\s+(\d+)[:\.]', re.IGNORECASE)
        
        for sermon in all_sermons:
            scripture = sermon.get('scripture', '').strip()
            if scripture:
                match = luke_pattern.search(scripture)
                if match:
                    chapter = int(match.group(1))
                    luke_sermons.append({
                        'chapter': chapter,
                        'reference': scripture,
                        'date': sermon['date'],
                        'title': sermon['title'],
                        'sermon': sermon
                    })
        
        if not luke_sermons:
            return None
            
        luke_sermons.sort(key=lambda x: (x['date'], -x['chapter']), reverse=True)
        latest = luke_sermons[0]
        max_chapter_sermon = max(luke_sermons, key=lambda x: x['chapter'])
        
        return {
            'latest_by_date': {
                'chapter': latest['chapter'],
                'reference': latest['reference'],
                'date': latest['date'],
                'title': latest['title']
            },
            'latest_by_chapter': {
                'chapter': max_chapter_sermon['chapter'],
                'reference': max_chapter_sermon['reference'],
                'date': max_chapter_sermon['date'],
                'title': max_chapter_sermon['title']
            },
            'total_luke_sermons': len(luke_sermons)
        }

# Global instance
_sermon_helper = None

def get_sermon_helper() -> SermonDataHelper:
    global _sermon_helper
    if _sermon_helper is None:
        _sermon_helper = SermonDataHelper()
    return _sermon_helper
