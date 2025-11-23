#!/usr/bin/env python3
"""
Script to populate the database with announcements from announcements.json
"""

import json
from datetime import datetime
from app import app
from database import db
from models import Announcement

def parse_date(date_string):
    """Parse date string to datetime object"""
    if not date_string:
        return datetime.utcnow()
    
    try:
        # Try parsing as ISO format (YYYY-MM-DDTHH:MM:SSZ)
        if 'T' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        # Try parsing as YYYY-MM-DD
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing as ISO format without timezone
            return datetime.fromisoformat(date_string)
        except:
            # Default to current time if parsing fails
            return datetime.utcnow()

def parse_active(active_value):
    """Parse active field to boolean"""
    if isinstance(active_value, bool):
        return active_value
    if isinstance(active_value, str):
        return active_value.lower() == 'true'
    return True

def populate_database():
    """Main function to populate database with announcements"""
    
    with app.app_context():
        print("🚀 Starting announcements database population...")
        
        # Read announcements.json
        try:
            with open('data/announcements.json', 'r', encoding='utf-8') as f:
                announcements_data = json.load(f)
        except FileNotFoundError:
            print("❌ Error: data/announcements.json not found!")
            return
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return
        
        # Handle both array format and object with 'announcements' key
        if isinstance(announcements_data, dict):
            announcements_data = announcements_data.get('announcements', [])
        
        if not isinstance(announcements_data, list):
            print("❌ Error: announcements.json must contain an array of announcements")
            return
        
        print(f"📋 Found {len(announcements_data)} announcements to import")
        
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for item in announcements_data:
            try:
                announcement_id = item.get('id')
                
                if not announcement_id:
                    print(f"⚠️  Skipping item without ID: {item.get('title', 'Unknown')[:50]}")
                    skipped_count += 1
                    continue
                
                # Check if announcement already exists
                existing = Announcement.query.filter_by(id=announcement_id).first()
                
                # Map JSON fields to database fields
                # JSON uses: date_entered, featured_image
                # Database uses: date_entered, featured_image
                date_entered = item.get('date_entered') or item.get('dateEntered')
                featured_image = item.get('featured_image') or item.get('featuredImage')
                
                if existing:
                    # Update existing announcement
                    existing.title = item.get('title', existing.title)
                    existing.description = item.get('description', existing.description)
                    if date_entered:
                        existing.date_entered = parse_date(date_entered)
                    existing.active = parse_active(item.get('active', True))
                    existing.type = item.get('type')
                    existing.category = item.get('category')
                    existing.tag = item.get('tag')
                    existing.superfeatured = item.get('superfeatured', False)
                    existing.featured_image = featured_image
                    existing.image_display_type = item.get('image_display_type') or item.get('imageDisplayType')
                    
                    updated_count += 1
                    print(f"♻️  Updated: {announcement_id} - {item.get('title', 'No title')[:50]}")
                else:
                    # Create new announcement
                    announcement = Announcement(
                        id=announcement_id,
                        title=item.get('title', 'Untitled'),
                        description=item.get('description', ''),
                        date_entered=parse_date(date_entered) if date_entered else datetime.utcnow(),
                        active=parse_active(item.get('active', True)),
                        type=item.get('type'),
                        category=item.get('category'),
                        tag=item.get('tag'),
                        superfeatured=item.get('superfeatured', False),
                        featured_image=featured_image,
                        image_display_type=item.get('image_display_type') or item.get('imageDisplayType')
                    )
                    
                    db.session.add(announcement)
                    added_count += 1
                    print(f"✅ Added: {announcement_id} - {item.get('title', 'No title')[:50]}")
                
            except Exception as e:
                print(f"❌ Error processing {item.get('id', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                skipped_count += 1
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "="*60)
            print("🎉 Database population complete!")
            print(f"✅ Added: {added_count}")
            print(f"♻️  Updated: {updated_count}")
            print(f"⚠️  Skipped: {skipped_count}")
            print(f"📊 Total processed: {added_count + updated_count + skipped_count}")
            print("="*60)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing to database: {e}")
            print("Changes have been rolled back.")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    populate_database()

