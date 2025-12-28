#!/usr/bin/env python3
"""
Script to ingest historical sermon archive data into the master JSON file.
This script parses CSV/tab-separated sermon data and converts it to the proper JSON format
for the Sunday Sermon archive.

Usage:
    python ingest_sermon_archive.py <input_file> [--append] [--output <file>]
"""

import json
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional
import argparse

def parse_date(date_str: str) -> Optional[str]:
    """
    Parse date from various formats (M/D/YYYY, MM/DD/YYYY) to YYYY-MM-DD
    """
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # Try M/D/YYYY or MM/DD/YYYY format
    try:
        # Handle formats like "1/1/2002" or "01/01/2002"
        date_parts = date_str.split('/')
        if len(date_parts) == 3:
            month = int(date_parts[0])
            day = int(date_parts[1])
            year = int(date_parts[2])
            date_obj = datetime(year, month, day)
            return date_obj.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        pass
    
    # Try YYYY-MM-DD format (already correct)
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        pass
    
    return None

def generate_sermon_id(date_str: str, title: str, index: int = 0) -> str:
    """
    Generate a unique sermon ID in format YY-MM-DD or YY-MM-DD-N if duplicates
    """
    if not date_str:
        return f"archive-{index:04d}"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        base_id = date_obj.strftime('%y-%m-%d')
        
        # If index > 0, append it to handle multiple sermons on same date
        if index > 0:
            return f"{base_id}-{index}"
        return base_id
    except ValueError:
        return f"archive-{index:04d}"

def parse_sermon_row(row: List[str], headers: List[str]) -> Optional[Dict]:
    """
    Parse a single row of sermon data into a sermon dictionary
    """
    if len(row) < len(headers):
        return None
    
    # Map headers to values
    data = dict(zip(headers, row))
    
    # Extract fields
    podcast = data.get('Podcast', '').strip()
    show = data.get('Show', '').strip()
    series = data.get('Series', '').strip()
    episode = data.get('Episode', '').strip()
    episode_absolute = data.get('Episode_Absolute', '').strip()
    title = data.get('Title', '').strip()
    speaker = data.get('Speaker', '').strip()
    date_str = data.get('Date', '').strip()
    scripture = data.get('Scripture', '').strip()
    
    # Skip empty rows - need at least a title
    if not title:
        return None
    
    # Parse date
    date = parse_date(date_str)
    if not date:
        # If no valid date, skip this entry
        print(f"Warning: Skipping entry with invalid date: {date_str} (Title: {title})")
        return None
    
    # Use default speaker if missing
    if not speaker:
        speaker = "Unknown Speaker"
    
    # Determine series name
    series_name = series if series else "The Sunday Sermon"
    
    # Generate ID (we'll handle duplicates later)
    sermon_id = generate_sermon_id(date, title)
    
    # Build sermon object matching the existing format
    sermon = {
        "id": sermon_id,
        "title": title,
        "author": speaker,
        "scripture": scripture if scripture else "",
        "date": date,
        "apple_podcasts_url": "",
        "spotify_url": "",
        "youtube_url": "",
        "link": "",
        "podcast_thumbnail_url": "",
        "source": "archive",
        "series": series_name,
        "episode_title": title,
        "sermon_type": "sermon",
        "tags": [],
        "search_keywords": f"{title} {speaker} {scripture} {series_name}".lower()
    }
    
    # Add episode number if available
    if episode:
        try:
            sermon["episode_number"] = int(episode)
        except ValueError:
            pass
    
    # Add episode_absolute if available
    if episode_absolute:
        try:
            sermon["episode_absolute"] = int(episode_absolute)
        except ValueError:
            pass
    
    # Generate tags from series and scripture
    if series:
        sermon["tags"].append(series)
    if scripture:
        # Extract book name from scripture reference
        book_match = re.match(r'^([A-Za-z]+)', scripture)
        if book_match:
            book_name = book_match.group(1)
            if book_name not in sermon["tags"]:
                sermon["tags"].append(book_name)
    
    return sermon

def parse_tsv_data(data_text: str) -> List[Dict]:
    """
    Parse tab-separated or space-separated sermon data
    Handles both tab-separated and multi-space-separated formats
    """
    lines = data_text.strip().split('\n')
    if not lines:
        return []
    
    # First line is headers - try tab first, then multiple spaces
    headers_line = lines[0]
    if '\t' in headers_line:
        # Tab-separated
        headers = [h.strip() for h in headers_line.split('\t') if h.strip()]
        is_tab_separated = True
    else:
        # Space-separated (multiple spaces)
        headers = [h.strip() for h in re.split(r'\s{2,}', headers_line) if h.strip()]
        is_tab_separated = False
    
    if not headers:
        raise ValueError("Could not parse headers from first line")
    
    sermons = []
    seen_ids = {}  # Track IDs to handle duplicates
    
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        
        # Split based on detected format
        if is_tab_separated:
            row = [cell.strip() for cell in line.split('\t')]
        else:
            # For space-separated, split on 2+ spaces to handle spaces in titles
            row = [cell.strip() for cell in re.split(r'\s{2,}', line)]
        
        # Pad row if needed
        while len(row) < len(headers):
            row.append('')
        
        sermon = parse_sermon_row(row, headers)
        if sermon:
            # Handle duplicate IDs
            original_id = sermon["id"]
            if original_id in seen_ids:
                seen_ids[original_id] += 1
                sermon["id"] = generate_sermon_id(sermon["date"], sermon["title"], seen_ids[original_id])
            else:
                seen_ids[original_id] = 0
            
            sermons.append(sermon)
    
    return sermons

def load_existing_sermons(filepath: str) -> Dict:
    """
    Load existing sermons.json file
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "title": "Sunday Sermons",
            "description": "Weekly sermons from our Sunday worship services",
            "sermons": []
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing existing JSON: {e}")
        return {
            "title": "Sunday Sermons",
            "description": "Weekly sermons from our Sunday worship services",
            "sermons": []
        }

def merge_sermons(existing: List[Dict], new: List[Dict], append: bool = True) -> List[Dict]:
    """
    Merge new sermons with existing ones, avoiding duplicates
    """
    if append:
        # Create a set of existing IDs for quick lookup
        existing_ids = {s["id"] for s in existing}
        
        # Add new sermons that don't already exist
        for sermon in new:
            if sermon["id"] not in existing_ids:
                existing.append(sermon)
                existing_ids.add(sermon["id"])
        
        return existing
    else:
        # Replace existing with new
        return new

def main():
    parser = argparse.ArgumentParser(description='Ingest sermon archive data into JSON format')
    parser.add_argument('input', nargs='?', help='Input file (or read from stdin)')
    parser.add_argument('--append', action='store_true', help='Append to existing sermons.json instead of replacing')
    parser.add_argument('--output', default='data/sermons.json', help='Output JSON file path')
    parser.add_argument('--archive', action='store_true', help='Create separate archive file instead of merging')
    
    args = parser.parse_args()
    
    # Read input data
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data_text = f.read()
    else:
        # Read from stdin
        data_text = sys.stdin.read()
    
    # Parse the data
    print("Parsing sermon data...")
    new_sermons = parse_tsv_data(data_text)
    print(f"Parsed {len(new_sermons)} sermons")
    
    if args.archive:
        # Create separate archive file
        archive_data = {
            "title": "Sunday Sermon Archive",
            "description": "Historical archive of Sunday sermons",
            "sermons": new_sermons
        }
        archive_file = args.output.replace('.json', '_archive.json')
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        print(f"Created archive file: {archive_file}")
    else:
        # Merge with existing sermons
        existing_data = load_existing_sermons(args.output)
        existing_sermons = existing_data.get('sermons', [])
        
        print(f"Existing sermons: {len(existing_sermons)}")
        
        merged_sermons = merge_sermons(existing_sermons, new_sermons, append=args.append)
        
        existing_data['sermons'] = merged_sermons
        
        # Sort by date (newest first)
        existing_data['sermons'].sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Write back
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"Total sermons: {len(merged_sermons)}")
        print(f"Updated file: {args.output}")

if __name__ == '__main__':
    main()

