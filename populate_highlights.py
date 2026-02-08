#!/usr/bin/env python3
"""
Script to populate the database with highlights from highlights.json
"""

import json
from datetime import datetime
from app import app
from database import db
from models import Announcement, next_global_id

def parse_date(date_string):
    """Parse date string to datetime object"""
    if not date_string:
        return datetime.utcnow()
    
    try:
        # Try parsing as YYYY-MM-DD
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing as ISO format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
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
    """Main function to populate database with highlights"""
    
    with app.app_context():
        print("🚀 Starting database population...")
        
        # Read highlights.json
        try:
            with open('data/highlights.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("❌ Error: data/highlights.json not found!")
            return
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return
        
        announcements_data = data.get('announcements', [])
        print(f"📋 Found {len(announcements_data)} highlights to import")
        
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for item in announcements_data:
            try:
                title = item.get('title', '').strip()
                if not title:
                    print(f"⚠️  Skipping item without title")
                    skipped_count += 1
                    continue
                
                # Check if announcement already exists (match by title)
                existing = Announcement.query.filter_by(title=title).first()
                
                if existing:
                    # Update existing announcement
                    existing.description = item.get('description', existing.description)
                    existing.date_entered = parse_date(item.get('dateEntered'))
                    existing.active = parse_active(item.get('active', True))
                    existing.type = item.get('type')
                    existing.category = item.get('category')
                    existing.tag = item.get('tag')
                    existing.superfeatured = item.get('superfeatured', False)
                    existing.featured_image = item.get('featuredImage')
                    existing.image_display_type = item.get('imageDisplayType')
                    existing.show_in_banner = parse_active(item.get('showInBanner', False))
                    
                    updated_count += 1
                    print(f"♻️  Updated: #{existing.id} - {title[:50]}")
                else:
                    # Create new announcement with universal ID
                    announcement = Announcement(
                        id=next_global_id(),
                        title=title,
                        description=item.get('description', ''),
                        date_entered=parse_date(item.get('dateEntered')),
                        active=parse_active(item.get('active', True)),
                        type=item.get('type'),
                        category=item.get('category'),
                        tag=item.get('tag'),
                        superfeatured=item.get('superfeatured', False),
                        featured_image=item.get('featuredImage'),
                        image_display_type=item.get('imageDisplayType'),
                        show_in_banner=parse_active(item.get('showInBanner', False)),
                    )
                    
                    db.session.add(announcement)
                    added_count += 1
                    print(f"✅ Added: #{announcement.id} - {title[:50]}")
                
            except Exception as e:
                print(f"❌ Error processing {item.get('title', 'unknown')}: {e}")
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

if __name__ == '__main__':
    populate_database()

