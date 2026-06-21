#!/usr/bin/env python3
"""
Script to add YouTube sermons to the archive based on video titles.
Parses YouTube video titles and adds them to sermons.json
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

# YouTube video data from the user
YOUTUBE_VIDEOS = [
    ("A Life of Readiness | Luke 12:35-59 | 1.25.26", "1:35:27", "38 watching", "6 days ago"),
    ("The Rich Fool and The Heart's Treasure | Luke 12:13-34 | 1.18.26", "1:35:27", "89 views", "Streamed 6 days ago"),
    ("What Do You Fear? Who Do You Love? | Luke 11:37-12:12 | 1.11.26", "1:49:25", "39 views", "Streamed 13 days ago"),
    ("But Something Greater Is Here | Luke 11:14-36 | 1.4.26", "1:36:21", "50 views", "Streamed 2 weeks ago"),
    ("Audacity, Assurance, & the Man Inside the House | Luke 10:41-11:13 | 12.28.25", "1:40:52", "47 views", "Streamed 3 weeks ago"),
    ("Love Redefined: Jesus, the Good Samaritan, and Uprooting Selfishness | Luke 10:25-42 | 12.21.25", "1:45:21", "55 views", "Streamed 1 month ago"),
    ("The Kingdom Has Come: The Grace, Acceptance, and Rejection of the Gospel | Luke 10:14-21 | 12.14.25", "1:44:43", "51 views", "Streamed 1 month ago"),
    ("The Covenant Promises of Christmas", "52:34", "85 views", "Streamed 1 month ago"),
    ("The Eden-Temple-Church Connection | Genesis 1:1-2, 26-28 | 12.07.25", None, "58 views", "Streamed 1 month ago"),
    ("A House Full of Condiments With No Real Food | Luke 9:43-62 | 11.30.25", "1:36:21", "41 views", "Streamed 1 month ago"),
    ("Listen to Him! The Glory of the Suffering Savior | Luke 9:28-45 | 11.23.25", "1:49:25", "50 views", "Streamed 2 months ago"),
    ("The Call to Die: Life, Death, and Following Jesus the Christ | Luke 9:18-27 | 11.16.25", "1:36:21", "60 views", "Streamed 2 months ago"),
    ("In Which Kingdom Do We Live? | Luke 9:1-17 | 11.9.25", "1:40:52", "59 views", "Streamed 2 months ago"),
    ("Wedding 2024", None, "6 views", "Streamed 2 months ago"),
    ("Who Then Is This? The Marvel of Jesus' Compassionate Power | Luke 8:22-56 | 11.2.25", "1:45:21", "54 views", "Streamed 2 months ago"),
    ("Fertile Ears | Luke 8:4-21 | 10.26.25", "1:44:43", "67 views", "Streamed 2 months ago"),
    ("Extravagant Love & Forgiveness in the Face of Calloused Hearts | Luke 7:36-8:3 | 10.19.25", "1:36:21", "47 views", "Streamed 3 months ago"),
    ("Living as the Family of God | Ephesians 4:1-6, 17-32 | 10.12.25", "1:49:25", "87 views", "Streamed 3 months ago"),
    ("Are You the One? | Luke 7:1-35 | 10.5.25", "1:40:52", "40 views", "Streamed 3 months ago"),
    ("The Fruit of the Church: Obedience | Luke 6:39-49 | 9.28.25", "1:36:21", "99 views", "Streamed 3 months ago"),
    ("The Character of the Church: Humility | Luke 6:37-42 | 9.21.25", "1:44:43", "47 views", "Streamed 4 months ago"),
    ("Congregational Meeting September 2025", None, "56 views", "Streamed 4 months ago"),
    ("The Ethic of the Church: Love | Luke 6:20-36 | 9.14.25", "1:45:21", "78 views", "Streamed 4 months ago"),
    ("The Identity of the Church: Poor | Luke 6:12-26 | 9.7.25", "1:40:52", "70 views", "Streamed 4 months ago"),
    ("Christ at the Center of It All | Revelation 1:1-20 | 8.31.25", "1:36:21", "49 views", "Streamed 4 months ago"),
    ("Who is the Lord of Your Life? | Luke 6:1-11 | 8.24.25", "1:49:25", "33 views", "Streamed 5 months ago"),
    ("The Doctor Is In | Luke 5:27-39 | 8.17.25", "1:44:43", "47 views", "Streamed 5 months ago"),
    ("Becoming a Christian, Part 2: Forgiven | Luke 5:17-26 | 8.10.25", "1:36:21", "47 views", "Streamed 5 months ago"),
]

def parse_video_title(title_str: str) -> Dict[str, Optional[str]]:
    """
    Parse YouTube video title to extract sermon title, scripture, and date.
    Format: "Title | Scripture | Date" or just "Title"
    """
    parts = [p.strip() for p in title_str.split('|')]
    
    title = parts[0] if parts else title_str
    scripture = None
    date_str = None
    
    if len(parts) >= 2:
        # Check if second part is scripture (contains colon or chapter:verse pattern)
        if ':' in parts[1] or re.search(r'\d+:\d+', parts[1]):
            scripture = parts[1]
            if len(parts) >= 3:
                date_str = parts[2]
        else:
            # Second part might be date
            date_str = parts[1]
    
    if len(parts) >= 3:
        date_str = parts[2]
    
    return {
        "title": title,
        "scripture": scripture,
        "date_str": date_str
    }

def parse_date(date_str: str, title: str = "") -> Optional[str]:
    """
    Parse date from format M.DD.YY or M.D.YY to YYYY-MM-DD
    Examples: "1.25.26" -> "2026-01-25", "12.28.25" -> "2025-12-28"
    Also handles special cases like "Wedding 2024" or "September 2025"
    """
    if not date_str:
        # Try to extract date from title for special cases
        if "Christmas" in title:
            # Assume Christmas sermon is around December 25
            return "2025-12-25"
        if "Wedding 2024" in title:
            return "2024-06-15"  # Default wedding date, can be updated
        if "September 2025" in title or "Congregational Meeting September 2025" in title:
            return "2025-09-15"  # Mid-September default
        return None
    
    # Remove any extra whitespace
    date_str = date_str.strip()
    
    # Try M.DD.YY or MM.DD.YY format
    try:
        parts = date_str.split('.')
        if len(parts) == 3:
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])
            
            # Assume 20XX for years < 100
            if year < 100:
                year = 2000 + year
            
            date_obj = datetime(year, month, day)
            return date_obj.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        pass
    
    return None

def determine_series(title: str, scripture: Optional[str]) -> str:
    """
    Determine the sermon series based on title and scripture
    """
    if not scripture:
        # Check title for special series
        if "Christmas" in title or "Covenant Promises" in title:
            return "Christmas"
        if "Wedding" in title:
            return "Special Events"
        if "Congregational Meeting" in title:
            return "Church Business"
        return "The Sunday Sermon"
    
    # Extract book name from scripture
    book_match = re.match(r'^([A-Za-z]+)', scripture)
    if book_match:
        book_name = book_match.group(1)
        
        # Check for series patterns in title
        if "Church" in title and ("Character" in title or "Ethic" in title or "Identity" in title or "Fruit" in title):
            return "The Character of the Church"
        if "Family of God" in title:
            return "Ephesians"
        
        # For Luke, use "Luke" as series name
        if book_name.lower() == "luke":
            # Check for specific Luke series
            if "Church" in title and ("Character" in title or "Ethic" in title or "Identity" in title or "Fruit" in title):
                return "The Character of the Church"
            return "Luke"
        
        # Default to book name as series
        return book_name
    
    return "The Sunday Sermon"

def generate_sermon_id(date_str: str, title: str, existing_ids: set) -> str:
    """
    Generate a unique sermon ID
    """
    if not date_str:
        return f"youtube-{len(existing_ids)}"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        base_id = date_obj.strftime('%y-%m-%d')
        
        if base_id not in existing_ids:
            return base_id
        
        # Handle duplicates
        counter = 1
        while f"{base_id}-{counter}" in existing_ids:
            counter += 1
        return f"{base_id}-{counter}"
    except ValueError:
        return f"youtube-{len(existing_ids)}"

def add_youtube_sermons(sermons_file: str = 'data/sermons.json'):
    """
    Add YouTube sermons to the sermons.json file
    """
    # Load existing sermons
    with open(sermons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get existing sermons and IDs
    sermons_by_year = data.get('sermons_by_year', {})
    all_sermons = []
    existing_ids = set()
    
    # Collect all existing sermons and IDs
    for year, sermons in sermons_by_year.items():
        if year.startswith('_'):
            continue
        for sermon in sermons:
            all_sermons.append(sermon)
            existing_ids.add(sermon.get('id', ''))
    
    # Also check the flat sermons array if it exists
    if 'sermons' in data:
        for sermon in data['sermons']:
            if sermon.get('id') not in existing_ids:
                all_sermons.append(sermon)
                existing_ids.add(sermon.get('id', ''))
    
    # Check for existing sermons by title and date to avoid duplicates
    existing_sermons_by_key = {}
    for sermon in all_sermons:
        key = (sermon.get('title', '').lower(), sermon.get('date', ''))
        existing_sermons_by_key[key] = sermon
    
    # Parse and add YouTube sermons
    new_sermons = []
    skipped = []
    for video_data in YOUTUBE_VIDEOS:
        title_str = video_data[0]
        parsed = parse_video_title(title_str)
        
        date = parse_date(parsed['date_str'], parsed['title'])
        if not date:
            print(f"Warning: Could not parse date for: {title_str}")
            continue
        
        # Check if sermon already exists
        key = (parsed['title'].lower(), date)
        if key in existing_sermons_by_key:
            existing = existing_sermons_by_key[key]
            # Update YouTube URL if missing
            if not existing.get('youtube_url') and existing.get('source') != 'youtube':
                existing['youtube_url'] = ""  # Will be filled when we have actual URLs
                skipped.append(f"Skipped (exists): {parsed['title']}")
            else:
                skipped.append(f"Skipped (duplicate): {parsed['title']}")
            continue
        
        sermon_id = generate_sermon_id(date, parsed['title'], existing_ids)
        existing_ids.add(sermon_id)
        
        series = determine_series(parsed['title'], parsed['scripture'])
        
        sermon = {
            "id": sermon_id,
            "title": parsed['title'],
            "author": "Rev. Craig Luekens",  # Default author, can be updated
            "scripture": parsed['scripture'] or "",
            "date": date,
            "apple_podcasts_url": "",
            "spotify_url": "",
            "youtube_url": "",  # Will be filled in when we have actual video URLs
            "link": "",
            "podcast_thumbnail_url": "",
            "source": "youtube",
            "series": series,
            "episode_title": parsed['title'],
            "sermon_type": "sermon",
            "tags": [series] if series != "The Sunday Sermon" else [],
            "search_keywords": f"{parsed['title']} {parsed['scripture'] or ''} {series}".lower()
        }
        
        new_sermons.append(sermon)
        all_sermons.append(sermon)
    
    # Reorganize by year
    year_counts = {}
    sermons_by_year_new = {}
    
    for sermon in all_sermons:
        date = sermon.get('date', '')
        if date:
            year = date[:4]
            if year not in sermons_by_year_new:
                sermons_by_year_new[year] = []
                year_counts[year] = 0
            sermons_by_year_new[year].append(sermon)
            year_counts[year] += 1
    
    # Sort years
    sorted_years = sorted(year_counts.keys())
    
    # Sort sermons within each year by date (newest first)
    for year in sermons_by_year_new:
        sermons_by_year_new[year].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Update year counts metadata
    year_counts_metadata = {}
    for year in sorted_years:
        count = year_counts[year]
        year_counts_metadata[year] = {
            "count": count,
            "note": f"{count} sermons from {year}"
        }
    
    # Rebuild flat array for API compatibility (oldest to newest)
    flat_sermons = []
    for year in sorted_years:
        flat_sermons.extend(sermons_by_year_new[year])
    
    # Update data structure
    data['sermons_by_year'] = sermons_by_year_new
    data['_year_counts'] = year_counts_metadata
    data['_total_sermons'] = len(all_sermons)
    data['sermons'] = flat_sermons
    
    # Save updated data
    with open(sermons_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Added {len(new_sermons)} new YouTube sermons to {sermons_file}")
    print(f"Total sermons: {len(all_sermons)}")
    for sermon in new_sermons:
        print(f"  - {sermon['date']}: {sermon['title']} ({sermon['series']})")

if __name__ == '__main__':
    add_youtube_sermons()

