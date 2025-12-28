#!/usr/bin/env python3
"""
Optimize sermons.json by removing duplicate flat array.
Keeps only sermons_by_year structure and generates flat array on-demand.
"""

import json
import shutil
from datetime import datetime

def optimize_sermons_json(input_file: str = 'data/sermons.json', 
                          backup: bool = True):
    """
    Remove the flat sermons array to eliminate duplication.
    The flat array will be generated on-demand by SermonDataHelper.
    """
    # Backup original file
    if backup:
        backup_file = f"{input_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(input_file, backup_file)
        print(f"Backup created: {backup_file}")
    
    # Load current data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Calculate original size
    original_size = len(json.dumps(data, ensure_ascii=False))
    
    # Remove flat sermons array (will be generated on-demand)
    if 'sermons' in data:
        del data['sermons']
        print("Removed duplicate 'sermons' array")
    
    # Add note about optimization
    data['_optimized'] = True
    data['_note'] = "Flat 'sermons' array is generated on-demand from 'sermons_by_year' to eliminate duplication"
    data['_optimized_date'] = datetime.now().isoformat()
    
    # Save optimized version
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Calculate new size
    new_size = len(json.dumps(data, ensure_ascii=False))
    savings = original_size - new_size
    savings_percent = (savings / original_size) * 100
    
    print(f"\nOptimization complete!")
    print(f"  Original size: {original_size / 1024:.2f} KB")
    print(f"  New size: {new_size / 1024:.2f} KB")
    print(f"  Savings: {savings / 1024:.2f} KB ({savings_percent:.1f}%)")
    print(f"\nNote: Flat array will be generated on-demand by SermonDataHelper")

if __name__ == '__main__':
    import sys
    backup = '--no-backup' not in sys.argv
    optimize_sermons_json(backup=backup)

