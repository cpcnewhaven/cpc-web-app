"""
Events ingester for Google Calendar ICS feeds
"""
from typing import Dict, List, Any
from .base import BaseIngester


class EventsIngester(BaseIngester):
    """Ingester for Google Calendar ICS feeds"""
    
    def fetch_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch events data from ICS feed"""
        url = config.get("EVENTS_ICS_URL")
        if not url or url.startswith("<PASTE_"):
            return {"error": "EVENTS_ICS_URL not configured"}
        
        try:
            response = self.make_request(url)
            response.raise_for_status()
            
            # Parse ICS content
            from ics import Calendar
            calendar = Calendar(response.text)
            events = []
            
            for event in sorted(calendar.events, key=lambda x: x.begin)[:50]:
                events.append({
                    "title": event.name,
                    "start": str(event.begin),
                    "end": str(event.end),
                    "location": event.location,
                    "description": event.description
                })
            
            return {"events": events}
            
        except Exception as e:
            return {"error": f"Failed to fetch events: {str(e)}"}
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize events data to standard format"""
        if "error" in raw_data:
            return raw_data
        
        return {
            "type": "events",
            "count": len(raw_data.get("events", [])),
            "events": raw_data.get("events", []),
            "last_updated": raw_data.get("last_updated")
        }
