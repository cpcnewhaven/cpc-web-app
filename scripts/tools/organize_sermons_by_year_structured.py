#!/usr/bin/env python3
"""
Reorganize sermons.json with year-based structure for easy scrolling.
Creates both a year-organized structure and maintains flat array for API compatibility.
"""

import json
from collections import defaultdict

def organize_sermons_by_year_structured(input_file, output_file):
    """
    Reorganize sermons with year-based structure for easy viewing.
    Maintains both structured (by year) and flat (for API) formats.
    """
    # Load existing data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sermons = data.get('sermons', [])
    
    # Count sermons by year
    year_counts = defaultdict(int)
    sermons_by_year = defaultdict(list)
    
    for sermon in sermons:
        date = sermon.get('date', '')
        if date:
            year = date[:4]
            year_counts[year] += 1
            sermons_by_year[year].append(sermon)
        else:
            sermons_by_year['_no_date'].append(sermon)
    
    # Sort years (oldest first)
    sorted_years = sorted([y for y in year_counts.keys()])
    
    # Sort sermons within each year by date (newest first within year)
    for year in sermons_by_year:
        if year != '_no_date':
            sermons_by_year[year].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Create year_counts metadata
    year_counts_metadata = {}
    for year in sorted_years:
        count = year_counts[year]
        year_counts_metadata[year] = {
            "count": count,
            "note": f"{count} sermons from {year}"
        }
    
    # Build structured format with years as keys
    sermons_by_year_dict = {}
    for year in sorted_years:
        sermons_by_year_dict[year] = sermons_by_year[year]
    
    if '_no_date' in sermons_by_year:
        sermons_by_year_dict['_no_date'] = sermons_by_year['_no_date']
    
    # Rebuild flat array for API compatibility (oldest to newest overall)
    flat_sermons = []
    for year in sorted_years:
        flat_sermons.extend(sermons_by_year[year])
    if '_no_date' in sermons_by_year:
        flat_sermons.extend(sermons_by_year['_no_date'])
    
    # Build new structure
    new_data = {
        "title": data.get('title', 'Sunday Sermons'),
        "description": data.get('description', 'Weekly sermons from our Sunday worship services'),
        "_year_counts": year_counts_metadata,
        "_total_sermons": len(sermons),
        "_organized_by": "year (oldest to newest)",
        "sermons_by_year": sermons_by_year_dict,
        "sermons": flat_sermons  # Keep flat array for API compatibility
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
    print(f"\nStructure:")
    print(f"  - sermons_by_year: Organized by year (for easy scrolling)")
    print(f"  - sermons: Flat array (for API compatibility)")

if __name__ == '__main__':
    import sys
    
    input_file = 'data/sermons.json'
    output_file = 'data/sermons.json'
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    organize_sermons_by_year_structured(input_file, output_file)

