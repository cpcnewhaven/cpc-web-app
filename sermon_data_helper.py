#!/usr/bin/env python3
"""
Optimized Sermon Data Helper
Eliminates duplication by generating flat array on-demand from sermons_by_year.
Includes caching for performance.
"""

import json
import os
from functools import lru_cache
from typing import Dict, List, Optional
from datetime import datetime

class SermonDataHelper:
    """Helper class for optimized sermon data access"""
    
    def __init__(self, sermons_file: str = 'data/sermons.json'):
        self.sermons_file = sermons_file
        self._data_cache = None
        self._flat_cache = None
        self._cache_timestamp = None
    
    def _load_data(self) -> Dict:
        """Load sermons data with caching"""
        # Check if file was modified
        current_mtime = os.path.getmtime(self.sermons_file) if os.path.exists(self.sermons_file) else 0
        
        if (self._data_cache is None or 
            self._cache_timestamp is None or 
            current_mtime > self._cache_timestamp):
            try:
                with open(self.sermons_file, 'r', encoding='utf-8') as f:
                    self._data_cache = json.load(f)
                    self._cache_timestamp = current_mtime
                    # Clear flat cache when data changes
                    self._flat_cache = None
            except FileNotFoundError:
                return {}
            except json.JSONDecodeError as e:
                print(f"Error parsing sermons.json: {e}")
                return {}
        
        return self._data_cache
    
    def get_all_sermons(self) -> List[Dict]:
        """
        Get all sermons as a flat array.
        Generates from sermons_by_year if flat array doesn't exist.
        Cached for performance.
        """
        if self._flat_cache is not None:
            return self._flat_cache
        
        data = self._load_data()
        
        # Try to get from flat array first (backward compatibility)
        if 'sermons' in data and data['sermons']:
            self._flat_cache = data['sermons']
            return self._flat_cache
        
        # Generate from sermons_by_year
        sermons_by_year = data.get('sermons_by_year', {})
        flat_sermons = []
        
        # Get all years sorted
        years = sorted([y for y in sermons_by_year.keys() if y != '_no_date'])
        
        # Add sermons year by year (oldest to newest)
        for year in years:
            flat_sermons.extend(sermons_by_year[year])
        
        # Add sermons without dates at the end
        if '_no_date' in sermons_by_year:
            flat_sermons.extend(sermons_by_year['_no_date'])
        
        self._flat_cache = flat_sermons
        return flat_sermons
    
    def get_sermons_by_year(self, year: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Get sermons organized by year"""
        data = self._load_data()
        sermons_by_year = data.get('sermons_by_year', {})
        
        if year:
            return {year: sermons_by_year.get(year, [])}
        return sermons_by_year
    
    def get_year_counts(self) -> Dict:
        """Get year counts metadata"""
        data = self._load_data()
        return data.get('_year_counts', {})
    
    def get_metadata(self) -> Dict:
        """Get metadata (title, description, etc.)"""
        data = self._load_data()
        return {
            'title': data.get('title', 'Sunday Sermons'),
            'description': data.get('description', 'Weekly sermons from our Sunday worship services'),
            'total_sermons': data.get('_total_sermons', len(self.get_all_sermons())),
            'year_counts': data.get('_year_counts', {})
        }
    
    def search_sermons(self, query: str = None, year: str = None, 
                      author: str = None, series: str = None) -> List[Dict]:
        """Search sermons with optional filters"""
        sermons = self.get_all_sermons()
        
        if not any([query, year, author, series]):
            return sermons
        
        results = []
        query_lower = query.lower() if query else None
        
        for sermon in sermons:
            # Year filter
            if year and not sermon.get('date', '').startswith(str(year)):
                continue
            
            # Author filter
            if author and author.lower() not in sermon.get('author', '').lower():
                continue
            
            # Series filter
            if series and series.lower() not in sermon.get('series', '').lower():
                continue
            
            # Query search
            if query_lower:
                searchable_fields = [
                    sermon.get('title', ''),
                    sermon.get('author', ''),
                    sermon.get('scripture', ''),
                    sermon.get('series', ''),
                    sermon.get('search_keywords', '')
                ]
                if not any(query_lower in str(field).lower() for field in searchable_fields):
                    continue
            
            results.append(sermon)
        
        return results
    
    def get_archive_sermons(self, cutoff_days: int = 90) -> List[Dict]:
        """Get sermons older than cutoff_days or marked as archive"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=cutoff_days)
        
        sermons = self.get_all_sermons()
        archive_sermons = []
        
        for sermon in sermons:
            sermon_date = sermon.get('date')
            if sermon_date:
                try:
                    serm_dt = datetime.strptime(sermon_date, '%Y-%m-%d')
                    is_archive = sermon.get('source') == 'archive'
                    if serm_dt < cutoff_date or is_archive:
                        archive_sermons.append(sermon)
                except ValueError:
                    pass
        
        return archive_sermons
    
    def get_latest_luke_chapter(self) -> Optional[Dict]:
        """
        Find the latest Luke chapter from all sermons.
        Returns dict with chapter number, reference, date, and sermon title.
        """
        import re
        sermons = self.get_all_sermons()
        luke_sermons = []
        
        # Pattern to match Luke references: "luke 24:36-53", "Luke 23.26-43", etc.
        luke_pattern = re.compile(r'luke\s+(\d+)[:\.]', re.IGNORECASE)
        
        for sermon in sermons:
            scripture = sermon.get('scripture', '').strip()
            title = sermon.get('title', '')
            date = sermon.get('date', '')
            
            # Check scripture field first
            if scripture:
                match = luke_pattern.search(scripture)
                if match:
                    chapter = int(match.group(1))
                    luke_sermons.append({
                        'chapter': chapter,
                        'reference': scripture,
                        'date': date,
                        'title': sermon.get('title', ''),
                        'sermon': sermon
                    })
                    continue
            
            # Also check title if scripture field is empty
            if not scripture and title:
                match = luke_pattern.search(title)
                if match:
                    chapter = int(match.group(1))
                    # Try to extract full reference from title
                    ref_match = re.search(r'luke\s+(\d+)[:\.]?\d*[-\.]?\d*', title, re.IGNORECASE)
                    reference = ref_match.group(0) if ref_match else f"Luke {chapter}"
                    luke_sermons.append({
                        'chapter': chapter,
                        'reference': reference,
                        'date': date,
                        'title': title,
                        'sermon': sermon
                    })
        
        if not luke_sermons:
            return None
        
        # Sort by date (most recent first), then by chapter number
        luke_sermons.sort(key=lambda x: (
            x['date'] if x['date'] else '0000-00-00',
            -x['chapter']  # Negative for descending
        ), reverse=True)
        
        # Get the most recent sermon
        latest = luke_sermons[0]
        
        # Find the highest chapter number overall (in case we want the latest chapter regardless of date)
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

# Global instance for easy access
_sermon_helper = None

def get_sermon_helper() -> SermonDataHelper:
    """Get or create global sermon helper instance"""
    global _sermon_helper
    if _sermon_helper is None:
        _sermon_helper = SermonDataHelper()
    return _sermon_helper

