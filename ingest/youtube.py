"""
YouTube ingester for channel RSS feeds
"""
import re
from typing import Dict, List, Any
from .base import BaseIngester


class YouTubeIngester(BaseIngester):
    """Ingester for YouTube channel RSS feeds"""
    
    def fetch_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch YouTube videos from channel RSS"""
        channel_id = config.get("YOUTUBE_CHANNEL_ID")
        if not channel_id or channel_id.startswith("<PASTE_"):
            return {"error": "YOUTUBE_CHANNEL_ID not configured"}
        
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            response = self.make_request(feed_url)
            response.raise_for_status()
            parsed = self.parse_rss(response.content)
            
            videos = []
            for entry in parsed.entries[:20]:
                # Extract video ID from link
                video_id = None
                if entry.get("link"):
                    match = re.search(r'v=([^&]+)', entry.get("link", ""))
                    if match:
                        video_id = match.group(1)
                
                videos.append({
                    "title": entry.get("title"),
                    "url": entry.get("link"),
                    "published": entry.get("published"),
                    "description": entry.get("summary"),
                    "video_id": video_id,
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None
                })
            
            return {
                "channel": parsed.feed.get("title", "YouTube Channel"),
                "videos": videos
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch YouTube videos: {str(e)}"}
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize YouTube data to standard format"""
        if "error" in raw_data:
            return raw_data
        
        return {
            "type": "youtube",
            "channel": raw_data.get("channel", "YouTube Channel"),
            "count": len(raw_data.get("videos", [])),
            "videos": raw_data.get("videos", []),
            "last_updated": raw_data.get("last_updated")
        }
