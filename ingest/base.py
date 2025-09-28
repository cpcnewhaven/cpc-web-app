"""
Base ingester class for external data sources
"""
import requests
import feedparser
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from flask_caching import Cache


class BaseIngester(ABC):
    """Base class for all data ingesters"""
    
    def __init__(self, cache: Cache, timeout: int = 10):
        self.cache = cache
        self.timeout = timeout
        self.headers = {"User-Agent": "CPC-Web-App (+https://cpcnewhaven.org)"}
    
    @abstractmethod
    def fetch_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from external source"""
        pass
    
    def make_request(self, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with common settings"""
        return requests.get(
            url, 
            timeout=self.timeout, 
            headers=self.headers,
            **kwargs
        )
    
    def parse_rss(self, content: bytes) -> feedparser.FeedParserDict:
        """Parse RSS/Atom content"""
        return feedparser.parse(content)
    
    def cache_key(self, source: str) -> str:
        """Generate cache key for source"""
        return f"ingest_{source}"
    
    def get_cached(self, source: str) -> Any:
        """Get cached data"""
        return self.cache.get(self.cache_key(source))
    
    def set_cache(self, source: str, data: Any, timeout: int = 900):
        """Set cached data"""
        self.cache.set(self.cache_key(source), data, timeout=timeout)
