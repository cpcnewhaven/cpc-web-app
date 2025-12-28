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

# Global instance for easy access
_sermon_helper = None

def get_sermon_helper() -> SermonDataHelper:
    """Get or create global sermon helper instance"""
    global _sermon_helper
    if _sermon_helper is None:
        _sermon_helper = SermonDataHelper()
    return _sermon_helper

