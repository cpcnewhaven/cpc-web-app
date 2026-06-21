#!/usr/bin/env python3
"""
Reorganize sermons.json by year and add year count metadata.
This makes it easier to scroll through and verify counts.
"""

import json
from collections import defaultdict
from datetime import datetime

def organize_sermons_by_year(input_file, output_file):
    """
    Reorganize sermons by year and add metadata with counts.
    """
    # Load existing data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sermons = data.get('sermons', [])
    
    # Count sermons by year
    year_counts = defaultdict(int)
    for sermon in sermons:
        date = sermon.get('date', '')
        if date:
            year = date[:4]
            year_counts[year] += 1
    
    # Sort years (oldest first for easier scrolling)
    sorted_years = sorted(year_counts.keys())
    
    # Group sermons by year
    sermons_by_year = defaultdict(list)
    for sermon in sermons:
        date = sermon.get('date', '')
        if date:
            year = date[:4]
            sermons_by_year[year].append(sermon)
        else:
            # Handle sermons without dates - put them in a special category
            sermons_by_year['_no_date'].append(sermon)
    
    # Sort sermons within each year by date (newest first)
    for year in sermons_by_year:
        if year != '_no_date':
            sermons_by_year[year].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Rebuild sermons array organized by year
    organized_sermons = []
    
    # Add sermons year by year (oldest to newest)
    for year in sorted_years:
        organized_sermons.extend(sermons_by_year[year])
    
    # Add sermons without dates at the end
    if '_no_date' in sermons_by_year:
        organized_sermons.extend(sermons_by_year['_no_date'])
    
    # Create year_counts metadata with comments as strings
    year_counts_metadata = {}
    for year in sorted_years:
        count = year_counts[year]
        year_counts_metadata[year] = {
            "count": count,
            "note": f"{count} sermons from {year}"
        }
    
    # Build new structure with metadata
    new_data = {
        "title": data.get('title', 'Sunday Sermons'),
        "description": data.get('description', 'Weekly sermons from our Sunday worship services'),
        "_year_counts": year_counts_metadata,
        "_total_sermons": len(sermons),
        "_organized_by": "year (oldest to newest)",
        "sermons": organized_sermons
    }
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Reorganized {len(sermons)} sermons by year")
    print(f"\nYear counts:")
    for year in sorted_years:
        count = year_counts[year]
        print(f"  {year}: {count} sermons")
    
    if '_no_date' in sermons_by_year:
        print(f"  No date: {len(sermons_by_year['_no_date'])} sermons")
    
    print(f"\nTotal: {len(sermons)} sermons")
    print(f"Output written to: {output_file}")

if __name__ == '__main__':
    import sys
    
    input_file = 'data/sermons.json'
    output_file = 'data/sermons.json'
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    organize_sermons_by_year(input_file, output_file)

