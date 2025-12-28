#!/usr/bin/env python3
"""
Advanced Search & Filtering System
Provides powerful search capabilities for sermon content.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AdvancedSearch:
    def __init__(self, sermons_file: str = "data/sermons.json"):
        self.sermons_file = sermons_file
        try:
            from sermon_data_helper import get_sermon_helper
            self.helper = get_sermon_helper()
            self.sermons = self.helper.get_all_sermons()
        except ImportError:
            # Fallback to old method
            self.helper = None
            self.sermons_data = self.load_sermons()
            self.sermons = self.sermons_data.get('sermons', [])
    
    def load_sermons(self) -> Dict:
        """Load sermons data from JSON file."""
        try:
            with open(self.sermons_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sermons file {self.sermons_file} not found")
            return {"sermons": []}
    
    def search_by_keywords(self, query: str, fields: List[str] = None) -> List[Dict]:
        """Search sermons by keywords in specified fields."""
        if not query.strip():
            return self.sermons
        
        if fields is None:
            fields = ['title', 'scripture', 'author', 'description', 'search_keywords']
        
        query_lower = query.lower()
        results = []
        
        for sermon in self.sermons:
            for field in fields:
                field_value = str(sermon.get(field, '')).lower()
                if query_lower in field_value:
                    results.append(sermon)
                    break  # Avoid duplicates
        
        return results
    
    def search_by_scripture(self, book: str = None, chapter: int = None, verse: int = None) -> List[Dict]:
        """Search sermons by scripture reference."""
        results = []
        
        for sermon in self.sermons:
            scripture = sermon.get('scripture', '').lower()
            if not scripture:
                continue
            
            # If only book is specified
            if book and not chapter and not verse:
                if book.lower() in scripture:
                    results.append(sermon)
            
            # If book and chapter are specified
            elif book and chapter and not verse:
                pattern = rf"{book.lower()}\s*{chapter}(?:\s*:\s*\d+)?"
                if re.search(pattern, scripture):
                    results.append(sermon)
            
            # If book, chapter, and verse are specified
            elif book and chapter and verse:
                pattern = rf"{book.lower()}\s*{chapter}\s*:\s*{verse}"
                if re.search(pattern, scripture):
                    results.append(sermon)
        
        return results
    
    def search_by_author(self, author: str) -> List[Dict]:
        """Search sermons by author."""
        author_lower = author.lower()
        return [sermon for sermon in self.sermons 
                if author_lower in sermon.get('author', '').lower()]
    
    def search_by_series(self, series: str) -> List[Dict]:
        """Search sermons by series."""
        series_lower = series.lower()
        return [sermon for sermon in self.sermons 
                if series_lower in sermon.get('series', '').lower()]
    
    def search_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Search sermons by date range."""
        results = []
        
        for sermon in self.sermons:
            sermon_date = sermon.get('date', '')
            if not sermon_date:
                continue
            
            try:
                sermon_dt = datetime.strptime(sermon_date, '%Y-%m-%d').date()
                
                if start_date:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                    if sermon_dt < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                    if sermon_dt > end_dt:
                        continue
                
                results.append(sermon)
                
            except ValueError:
                logger.warning(f"Could not parse date: {sermon_date}")
                continue
        
        return results
    
    def search_by_tags(self, tags: List[str]) -> List[Dict]:
        """Search sermons by tags."""
        results = []
        
        for sermon in self.sermons:
            sermon_tags = sermon.get('tags', [])
            if isinstance(sermon_tags, str):
                sermon_tags = [tag.strip() for tag in sermon_tags.split(',')]
            
            # Check if any of the search tags match
            for tag in tags:
                if any(tag.lower() in sermon_tag.lower() for sermon_tag in sermon_tags):
                    results.append(sermon)
                    break
        
        return results
    
    def search_by_sermon_type(self, sermon_type: str) -> List[Dict]:
        """Search sermons by type."""
        return [sermon for sermon in self.sermons 
                if sermon.get('sermon_type', '').lower() == sermon_type.lower()]
    
    def search_by_duration(self, min_minutes: int = None, max_minutes: int = None) -> List[Dict]:
        """Search sermons by duration."""
        results = []
        
        for sermon in self.sermons:
            duration = sermon.get('duration_minutes')
            if duration is None:
                continue
            
            if min_minutes and duration < min_minutes:
                continue
            
            if max_minutes and duration > max_minutes:
                continue
            
            results.append(sermon)
        
        return results
    
    def advanced_search(self, 
                       query: str = None,
                       scripture: Dict = None,
                       author: str = None,
                       series: str = None,
                       date_range: Dict = None,
                       tags: List[str] = None,
                       sermon_type: str = None,
                       duration: Dict = None,
                       sort_by: str = 'date',
                       sort_order: str = 'desc',
                       limit: int = None) -> List[Dict]:
        """Perform advanced search with multiple criteria."""
        
        # Start with all sermons
        results = self.sermons.copy()
        
        # Apply filters
        if query:
            results = self.search_by_keywords(query)
        
        if scripture:
            book = scripture.get('book')
            chapter = scripture.get('chapter')
            verse = scripture.get('verse')
            scripture_results = self.search_by_scripture(book, chapter, verse)
            results = [s for s in results if s in scripture_results]
        
        if author:
            author_results = self.search_by_author(author)
            results = [s for s in results if s in author_results]
        
        if series:
            series_results = self.search_by_series(series)
            results = [s for s in results if s in series_results]
        
        if date_range:
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            date_results = self.search_by_date_range(start_date, end_date)
            results = [s for s in results if s in date_results]
        
        if tags:
            tag_results = self.search_by_tags(tags)
            results = [s for s in results if s in tag_results]
        
        if sermon_type:
            type_results = self.search_by_sermon_type(sermon_type)
            results = [s for s in results if s in type_results]
        
        if duration:
            min_minutes = duration.get('min')
            max_minutes = duration.get('max')
            duration_results = self.search_by_duration(min_minutes, max_minutes)
            results = [s for s in results if s in duration_results]
        
        # Sort results
        results = self.sort_results(results, sort_by, sort_order)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    def sort_results(self, results: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
        """Sort search results."""
        reverse = sort_order.lower() == 'desc'
        
        if sort_by == 'date':
            return sorted(results, key=lambda x: x.get('date', ''), reverse=reverse)
        elif sort_by == 'title':
            return sorted(results, key=lambda x: x.get('title', '').lower(), reverse=reverse)
        elif sort_by == 'author':
            return sorted(results, key=lambda x: x.get('author', '').lower(), reverse=reverse)
        elif sort_by == 'duration':
            return sorted(results, key=lambda x: x.get('duration_minutes', 0), reverse=reverse)
        else:
            return results
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query."""
        suggestions = set()
        partial_lower = partial_query.lower()
        
        for sermon in self.sermons:
            # Add title words
            title_words = re.findall(r'\b\w+\b', sermon.get('title', '').lower())
            for word in title_words:
                if word.startswith(partial_lower) and len(word) > 3:
                    suggestions.add(word)
            
            # Add author names
            author = sermon.get('author', '').lower()
            if author.startswith(partial_lower):
                suggestions.add(author)
            
            # Add series names
            series = sermon.get('series', '').lower()
            if series.startswith(partial_lower):
                suggestions.add(series)
            
            # Add scripture references
            scripture = sermon.get('scripture', '').lower()
            scripture_words = re.findall(r'\b\w+\b', scripture)
            for word in scripture_words:
                if word.startswith(partial_lower) and len(word) > 2:
                    suggestions.add(word)
        
        return sorted(list(suggestions))[:10]
    
    def get_popular_searches(self) -> List[str]:
        """Get popular search terms based on content analysis."""
        word_counts = {}
        
        for sermon in self.sermons:
            # Count words in titles
            title_words = re.findall(r'\b\w+\b', sermon.get('title', '').lower())
            for word in title_words:
                if len(word) > 3:  # Only count meaningful words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Count scripture books
            scripture = sermon.get('scripture', '').lower()
            books = ['luke', 'john', 'acts', 'romans', 'ephesians', 'psalm', 'exodus', 'genesis']
            for book in books:
                if book in scripture:
                    word_counts[book] = word_counts.get(book, 0) + 1
        
        # Return top 10 most common words
        return [word for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    def get_search_filters(self) -> Dict:
        """Get available search filters and their options."""
        filters = {
            'authors': list(set(sermon.get('author', '') for sermon in self.sermons if sermon.get('author'))),
            'series': list(set(sermon.get('series', '') for sermon in self.sermons if sermon.get('series'))),
            'sermon_types': list(set(sermon.get('sermon_type', '') for sermon in self.sermons if sermon.get('sermon_type'))),
            'tags': []
        }
        
        # Collect all tags
        all_tags = set()
        for sermon in self.sermons:
            tags = sermon.get('tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                all_tags.update(tag.strip() for tag in tags.split(','))
        
        filters['tags'] = sorted(list(all_tags))
        
        return filters

def main():
    """Main function to test search functionality."""
    search = AdvancedSearch()
    
    # Test basic search
    print("Testing keyword search...")
    results = search.search_by_keywords("grace")
    print(f"Found {len(results)} sermons about 'grace'")
    
    # Test scripture search
    print("\nTesting scripture search...")
    results = search.search_by_scripture("luke", 6)
    print(f"Found {len(results)} sermons from Luke 6")
    
    # Test advanced search
    print("\nTesting advanced search...")
    results = search.advanced_search(
        query="church",
        author="Rev. Craig Luekens",
        sermon_type="sermon",
        limit=5
    )
    print(f"Found {len(results)} sermons matching criteria")
    
    # Test search suggestions
    print("\nTesting search suggestions...")
    suggestions = search.get_search_suggestions("gra")
    print(f"Suggestions for 'gra': {suggestions}")

if __name__ == "__main__":
    main()
