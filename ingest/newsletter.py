"""
Newsletter ingester for RSS feeds
"""
from typing import Dict, List, Any
from .base import BaseIngester


class NewsletterIngester(BaseIngester):
    """Ingester for newsletter RSS feeds"""
    
    def fetch_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch newsletter data from RSS feed"""
        url = config.get("NEWSLETTER_FEED_URL")
        if not url or url.startswith("<PASTE_"):
            return {"error": "NEWSLETTER_FEED_URL not configured"}
        
        try:
            response = self.make_request(url)
            response.raise_for_status()
            parsed = self.parse_rss(response.content)
            
            items = []
            for entry in parsed.entries[:20]:
                # Extract image from various sources
                image = None
                if entry.get("media_thumbnail"):
                    image = entry.get("media_thumbnail", [{}])[0].get("url")
                elif entry.get("enclosures"):
                    for enc in entry.get("enclosures", []):
                        if enc.get("type", "").startswith("image"):
                            image = enc.get("href")
                            break
                
                items.append({
                    "title": entry.get("title"),
                    "url": entry.get("link"),
                    "published": entry.get("published"),
                    "summary": entry.get("summary"),
                    "image": image
                })
            
            return {
                "source": parsed.feed.get("title", "Newsletter"),
                "items": items
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch newsletter: {str(e)}"}
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize newsletter data to standard format"""
        if "error" in raw_data:
            return raw_data
        
        return {
            "type": "newsletter",
            "source": raw_data.get("source", "Newsletter"),
            "count": len(raw_data.get("items", [])),
            "items": raw_data.get("items", []),
            "last_updated": raw_data.get("last_updated")
        }
