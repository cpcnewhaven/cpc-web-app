#!/usr/bin/env python3
"""
Sermon Data Enhancer
Uses AI and smart parsing to enhance sermon data automatically.
"""

import json
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SermonEnhancer:
    def __init__(self, sermons_file: str = "data/sermons.json"):
        self.sermons_file = sermons_file
        self.sermons_data = self.load_sermons()
        
    def load_sermons(self) -> Dict:
        """Load sermons data from JSON file."""
        try:
            with open(self.sermons_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sermons file {self.sermons_file} not found")
            return {"sermons": []}
    
    def save_sermons(self):
        """Save enhanced sermons data back to file."""
        with open(self.sermons_file, 'w') as f:
            json.dump(self.sermons_data, f, indent=2)
        logger.info(f"Enhanced sermons saved to {self.sermons_file}")
    
    def extract_scripture_references(self, title: str, description: str = "") -> str:
        """Extract scripture references from title and description."""
        text = f"{title} {description}".lower()
        
        # Common patterns for scripture references
        patterns = [
            r'(?:luke|matthew|mark|john|acts|romans|corinthians|galatians|ephesians|philippians|colossians|thessalonians|timothy|titus|philemon|hebrews|james|peter|jude|revelation)\s+\d+:\d+(?:-\d+)?',
            r'(?:psalm|psalms|proverbs|ecclesiastes|song of solomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi)\s+\d+:\d+(?:-\d+)?',
            r'(?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|samuel|kings|chronicles|ezra|nehemiah|esther|job)\s+\d+:\d+(?:-\d+)?',
            r'\d+\s+(?:corinthians|thessalonians|timothy|peter|john)\s+\d+:\d+(?:-\d+)?',
            r'(?:ps|psa|prov|eccl|song|isa|jer|lam|ezek|dan|hos|joel|amos|obad|jonah|mic|nah|hab|zeph|hag|zech|mal)\s+\d+:\d+(?:-\d+)?'
        ]
        
        found_scriptures = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_scriptures.extend(matches)
        
        # Clean up and format
        if found_scriptures:
            # Remove duplicates and sort
            unique_scriptures = list(set(found_scriptures))
            return ", ".join(unique_scriptures)
        
        return ""
    
    def extract_series_info(self, title: str) -> Tuple[str, str]:
        """Extract series name and episode info from title."""
        # Common series patterns
        series_patterns = [
            r'(.+?)\s*\|\s*(?:The Sunday Sermon|Beyond the Sunday Sermon)',
            r'(.+?)\s*\|\s*(?:Episode|Ep)\s*\d+',
            r'(.+?)\s*\|\s*Part\s*\d+',
            r'(.+?)\s*\|\s*Lesson\s*\d+',
            r'(.+?)\s*\|\s*With Guest',
            r'(.+?)\s*\|\s*\d+\.\d+\.\d+',
        ]
        
        for pattern in series_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                series_name = match.group(1).strip()
                # Clean up series name
                series_name = re.sub(r'\s*\|\s*$', '', series_name)
                return series_name, title
        
        # If no series pattern found, try to extract from common prefixes
        if 'Beyond the Sunday Sermon' in title:
            return 'Beyond the Sunday Sermon', title
        elif 'The Sunday Sermon' in title:
            return 'Sunday Sermons', title
        elif 'What We Believe' in title:
            return 'What We Believe', title
        elif 'Confessional Theology' in title:
            return 'Confessional Theology', title
        elif 'School of Discipleship' in title:
            return 'School of Discipleship', title
        elif 'Walking with Jesus' in title:
            return 'Walking with Jesus Through Sinai', title
        
        return 'Sunday Sermons', title
    
    def extract_guest_speaker(self, title: str, description: str = "") -> str:
        """Extract guest speaker information."""
        text = f"{title} {description}"
        
        # Look for guest patterns
        guest_patterns = [
            r'With Guest\s+([^|]+)',
            r'Guest\s+([^|]+)',
            r'Rev\.\s+([^|]+)',
            r'Pastor\s+([^|]+)',
        ]
        
        for pattern in guest_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                guest = match.group(1).strip()
                # Clean up guest name
                guest = re.sub(r'\s*\|\s*.*$', '', guest)
                return guest
        
        return ""
    
    def categorize_sermon_type(self, title: str) -> str:
        """Categorize sermon by type."""
        title_lower = title.lower()
        
        if 'beyond the sunday sermon' in title_lower:
            return 'discussion'
        elif 'what we believe' in title_lower:
            return 'theology'
        elif 'confessional theology' in title_lower:
            return 'doctrine'
        elif 'school of discipleship' in title_lower:
            return 'education'
        elif 'walking with jesus' in title_lower:
            return 'bible_study'
        elif 'membership seminar' in title_lower:
            return 'membership'
        elif 'compline' in title_lower:
            return 'worship'
        else:
            return 'sermon'
    
    def extract_duration_from_title(self, title: str) -> Optional[int]:
        """Extract duration in minutes from title if present."""
        # Look for duration patterns like "40:30" or "1:23:45"
        duration_pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?'
        match = re.search(duration_pattern, title)
        
        if match:
            hours = int(match.group(1)) if len(match.group(1)) > 2 else 0
            minutes = int(match.group(2))
            seconds = int(match.group(3)) if match.group(3) else 0
            
            total_minutes = hours * 60 + minutes + (seconds / 60)
            return int(total_minutes)
        
        return None
    
    def enhance_sermon(self, sermon: Dict) -> Dict:
        """Enhance a single sermon with additional metadata."""
        enhanced = sermon.copy()
        
        # Extract scripture references
        if not enhanced.get('scripture'):
            enhanced['scripture'] = self.extract_scripture_references(
                enhanced.get('title', ''),
                enhanced.get('description', '')
            )
        
        # Extract series information
        series_name, episode_title = self.extract_series_info(enhanced.get('title', ''))
        enhanced['series'] = series_name
        enhanced['episode_title'] = episode_title
        
        # Extract guest speaker
        guest = self.extract_guest_speaker(
            enhanced.get('title', ''),
            enhanced.get('description', '')
        )
        if guest:
            enhanced['guest_speaker'] = guest
        
        # Categorize sermon type
        enhanced['sermon_type'] = self.categorize_sermon_type(enhanced.get('title', ''))
        
        # Extract duration
        duration = self.extract_duration_from_title(enhanced.get('title', ''))
        if duration:
            enhanced['duration_minutes'] = duration
        
        # Add tags based on content
        enhanced['tags'] = self.generate_tags(enhanced)
        
        # Add search keywords
        enhanced['search_keywords'] = self.generate_search_keywords(enhanced)
        
        return enhanced
    
    def generate_tags(self, sermon: Dict) -> List[str]:
        """Generate relevant tags for the sermon."""
        tags = []
        title = sermon.get('title', '').lower()
        scripture = sermon.get('scripture', '').lower()
        
        # Scripture-based tags
        if 'luke' in scripture:
            tags.append('Luke')
        if 'john' in scripture:
            tags.append('John')
        if 'acts' in scripture:
            tags.append('Acts')
        if 'romans' in scripture:
            tags.append('Romans')
        if 'ephesians' in scripture:
            tags.append('Ephesians')
        if 'psalm' in scripture:
            tags.append('Psalms')
        if 'exodus' in scripture:
            tags.append('Exodus')
        
        # Topic-based tags
        if 'grace' in title:
            tags.append('Grace')
        if 'love' in title:
            tags.append('Love')
        if 'faith' in title:
            tags.append('Faith')
        if 'hope' in title:
            tags.append('Hope')
        if 'church' in title:
            tags.append('Church')
        if 'jesus' in title:
            tags.append('Jesus')
        if 'god' in title:
            tags.append('God')
        if 'christ' in title:
            tags.append('Christ')
        
        # Series-based tags
        sermon_type = sermon.get('sermon_type', '')
        if sermon_type == 'discussion':
            tags.append('Discussion')
        elif sermon_type == 'theology':
            tags.append('Theology')
        elif sermon_type == 'doctrine':
            tags.append('Doctrine')
        elif sermon_type == 'education':
            tags.append('Education')
        
        return list(set(tags))  # Remove duplicates
    
    def generate_search_keywords(self, sermon: Dict) -> str:
        """Generate search keywords for better discoverability."""
        keywords = []
        
        # Add title words
        title_words = re.findall(r'\b\w+\b', sermon.get('title', '').lower())
        keywords.extend(title_words)
        
        # Add scripture references
        if sermon.get('scripture'):
            keywords.append(sermon['scripture'].lower())
        
        # Add author
        if sermon.get('author'):
            keywords.append(sermon['author'].lower())
        
        # Add series
        if sermon.get('series'):
            keywords.append(sermon['series'].lower())
        
        # Add tags
        keywords.extend(sermon.get('tags', []))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in keywords if word not in stop_words and len(word) > 2]
        
        return ' '.join(set(keywords))  # Remove duplicates
    
    def enhance_all_sermons(self):
        """Enhance all sermons in the dataset."""
        logger.info(f"Enhancing {len(self.sermons_data.get('sermons', []))} sermons...")
        
        enhanced_sermons = []
        for sermon in self.sermons_data.get('sermons', []):
            enhanced = self.enhance_sermon(sermon)
            enhanced_sermons.append(enhanced)
        
        self.sermons_data['sermons'] = enhanced_sermons
        self.save_sermons()
        
        logger.info("Sermon enhancement completed!")
        return enhanced_sermons

def main():
    """Main function to run sermon enhancement."""
    enhancer = SermonEnhancer()
    enhancer.enhance_all_sermons()

if __name__ == "__main__":
    main()
