"""
JSON-based data management for CPC New Haven
Simple, file-based data storage without database complexity
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class JSONDataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_json(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
    
    def save_json(self, filename: str, data: List[Dict[str, Any]]):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_announcements(self) -> List[Dict[str, Any]]:
        """Get all announcements"""
        return self.load_json('announcements.json')
    
    def get_sermons(self) -> List[Dict[str, Any]]:
        """Get all sermons"""
        return self.load_json('sermons.json')
    
    def get_podcast_series(self) -> List[Dict[str, Any]]:
        """Get all podcast series"""
        return self.load_json('podcast_series.json')
    
    def get_podcast_episodes(self) -> List[Dict[str, Any]]:
        """Get all podcast episodes"""
        return self.load_json('podcast_episodes.json')
    
    def get_gallery_images(self) -> List[Dict[str, Any]]:
        """Get all gallery images"""
        return self.load_json('gallery.json')
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events"""
        return self.load_json('events.json')
    
    def get_active_announcements(self) -> List[Dict[str, Any]]:
        """Get only active announcements"""
        announcements = self.get_announcements()
        return [ann for ann in announcements if ann.get('active', False)]
    
    def get_superfeatured_announcements(self) -> List[Dict[str, Any]]:
        """Get super featured announcements"""
        announcements = self.get_announcements()
        return [ann for ann in announcements if ann.get('superfeatured', False)]
    
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get only active events"""
        events = self.get_events()
        return [event for event in events if event.get('active', False)]
    
    def get_episodes_by_series(self, series_id: str) -> List[Dict[str, Any]]:
        """Get episodes for a specific series"""
        episodes = self.get_podcast_episodes()
        return [ep for ep in episodes if ep.get('series_id') == series_id]
    
    def get_event_images(self) -> List[Dict[str, Any]]:
        """Get only event photos from gallery"""
        images = self.get_gallery_images()
        return [img for img in images if img.get('event', False)]
    
    def add_announcement(self, announcement: Dict[str, Any]) -> bool:
        """Add a new announcement"""
        try:
            announcements = self.get_announcements()
            announcement['date_entered'] = datetime.now().isoformat()
            announcements.append(announcement)
            self.save_json('announcements.json', announcements)
            return True
        except Exception:
            return False
    
    def add_sermon(self, sermon: Dict[str, Any]) -> bool:
        """Add a new sermon"""
        try:
            sermons = self.get_sermons()
            sermons.append(sermon)
            self.save_json('sermons.json', sermons)
            return True
        except Exception:
            return False
    
    def add_event(self, event: Dict[str, Any]) -> bool:
        """Add a new event"""
        try:
            events = self.get_events()
            event['date_entered'] = datetime.now().isoformat()
            events.append(event)
            self.save_json('events.json', events)
            return True
        except Exception:
            return False
    
    def add_gallery_image(self, image: Dict[str, Any]) -> bool:
        """Add a new gallery image"""
        try:
            images = self.get_gallery_images()
            image['created'] = datetime.now().strftime('%Y-%m-%d')
            images.append(image)
            self.save_json('gallery.json', images)
            return True
        except Exception:
            return False
    
    def update_announcement(self, announcement_id: str, updates: Dict[str, Any]) -> bool:
        """Update an announcement"""
        try:
            announcements = self.get_announcements()
            for i, ann in enumerate(announcements):
                if ann.get('id') == announcement_id:
                    announcements[i].update(updates)
                    self.save_json('announcements.json', announcements)
                    return True
            return False
        except Exception:
            return False
    
    def delete_announcement(self, announcement_id: str) -> bool:
        """Delete an announcement"""
        try:
            announcements = self.get_announcements()
            announcements = [ann for ann in announcements if ann.get('id') != announcement_id]
            self.save_json('announcements.json', announcements)
            return True
        except Exception:
            return False

# Global instance
data_manager = JSONDataManager()
