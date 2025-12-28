#!/usr/bin/env python3
"""
Reorganize sermons.json so sermons_by_year comes first for easy viewing.
"""

import json

def reorganize_file_structure(input_file, output_file):
    """
    Reorganize file so year-based structure is first, flat array is last.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Rebuild with sermons_by_year first (for easy viewing)
    new_data = {
        "title": data.get('title', 'Sunday Sermons'),
        "description": data.get('description', 'Weekly sermons from our Sunday worship services'),
        "_year_counts": data.get('_year_counts', {}),
        "_total_sermons": data.get('_total_sermons', 0),
        "_organized_by": data.get('_organized_by', 'year (oldest to newest)'),
        "_note": "Scroll through 'sermons_by_year' to see sermons organized by year. The 'sermons' array at the end is for API compatibility.",
        "sermons_by_year": data.get('sermons_by_year', {}),  # Year-organized (for viewing)
        "sermons": data.get('sermons', [])  # Flat array (for API)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"Reorganized file structure")
    print(f"  - sermons_by_year: First (organized by year for easy scrolling)")
    print(f"  - sermons: Last (flat array for API compatibility)")

if __name__ == '__main__':
    reorganize_file_structure('data/sermons.json', 'data/sermons.json')

