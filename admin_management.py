#!/usr/bin/env python3
"""
Admin management script for CPC New Haven
Provides command-line tools for content management
"""
import sys
import os
from datetime import datetime, date
from app import app, db
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent
from admin_utils import get_content_stats, create_sample_podcast_series

def show_stats():
    """Display content statistics"""
    with app.app_context():
        stats = get_content_stats()
        
        print("=== CPC New Haven Content Statistics ===")
        print()
        
        print("📢 ANNOUNCEMENTS")
        print(f"  Total: {stats['announcements']['total']}")
        print(f"  Active: {stats['announcements']['active']}")
        print(f"  Super Featured: {stats['announcements']['superfeatured']}")
        print()
        
        print("📖 SERMONS")
        print(f"  Total: {stats['sermons']['total']}")
        print(f"  Recent (last month): {stats['sermons']['recent_month']}")
        print()
        
        print("🎧 PODCASTS")
        print(f"  Series: {stats['podcasts']['series']}")
        print(f"  Episodes: {stats['podcasts']['episodes']}")
        print()
        
        print("🖼️  GALLERY")
        print(f"  Total Images: {stats['gallery']['total']}")
        print(f"  Event Photos: {stats['gallery']['event_photos']}")
        print()
        
        print("📅 EVENTS")
        print(f"  Total: {stats['events']['total']}")
        print(f"  Active: {stats['events']['active']}")
        print()

def create_sample_data():
    """Create comprehensive sample data"""
    with app.app_context():
        print("Creating sample data...")
        
        # Create podcast series
        series_created = create_sample_podcast_series()
        print(f"✓ Created {series_created} podcast series")
        
        # Create sample announcements
        announcements = [
            {
                'id': 'ann_001',
                'title': 'Welcome to CPC New Haven',
                'description': 'We are excited to welcome you to our church community. Join us for worship every Sunday at 10:30am.',
                'type': 'announcement',
                'category': 'general',
                'superfeatured': True,
                'active': True
            },
            {
                'id': 'ann_002',
                'title': 'Sunday School Classes Resume',
                'description': 'Children\'s Sunday School and Adult Sunday Studies begin at 9:30am every Sunday.',
                'type': 'event',
                'category': 'education',
                'superfeatured': False,
                'active': True
            },
            {
                'id': 'ann_003',
                'title': 'Fellowship Lunch',
                'description': 'Join us for fellowship lunch every Sunday after worship service at 12:00pm.',
                'type': 'ongoing',
                'category': 'fellowship',
                'superfeatured': False,
                'active': True
            },
            {
                'id': 'ann_004',
                'title': 'Youth Group Meeting',
                'description': 'High school and middle school students meet every Friday at 7:00pm for fellowship and study.',
                'type': 'ongoing',
                'category': 'youth',
                'superfeatured': False,
                'active': True
            }
        ]
        
        for ann_data in announcements:
            existing = Announcement.query.get(ann_data['id'])
            if not existing:
                announcement = Announcement(**ann_data)
                db.session.add(announcement)
        
        # Create sample sermons
        sermons = [
            {
                'id': 'serm_001',
                'title': 'The Grace of God',
                'author': 'Pastor John Smith',
                'scripture': 'Ephesians 2:8-9',
                'date': date(2024, 1, 7),
                'spotify_url': 'https://open.spotify.com/episode/example1',
                'youtube_url': 'https://youtube.com/watch?v=example1',
                'apple_podcasts_url': 'https://podcasts.apple.com/podcast/example1'
            },
            {
                'id': 'serm_002',
                'title': 'Walking in Faith',
                'author': 'Pastor John Smith',
                'scripture': 'Hebrews 11:1-6',
                'date': date(2024, 1, 14),
                'spotify_url': 'https://open.spotify.com/episode/example2',
                'youtube_url': 'https://youtube.com/watch?v=example2'
            },
            {
                'id': 'serm_003',
                'title': 'The Love of Christ',
                'author': 'Pastor Jane Doe',
                'scripture': 'Romans 8:35-39',
                'date': date(2024, 1, 21),
                'spotify_url': 'https://open.spotify.com/episode/example3',
                'youtube_url': 'https://youtube.com/watch?v=example3'
            }
        ]
        
        for sermon_data in sermons:
            existing = Sermon.query.get(sermon_data['id'])
            if not existing:
                sermon = Sermon(**sermon_data)
                db.session.add(sermon)
        
        # Create sample podcast episodes
        beyond_series = PodcastSeries.query.filter_by(title='Beyond the Sunday Sermon').first()
        if beyond_series:
            episodes = [
                {
                    'series_id': beyond_series.id,
                    'number': 1,
                    'title': 'Understanding Grace',
                    'link': 'https://example.com/beyond1',
                    'guest': 'Dr. Jane Doe',
                    'date_added': date(2024, 1, 8),
                    'scripture': 'Romans 3:23-24'
                },
                {
                    'series_id': beyond_series.id,
                    'number': 2,
                    'title': 'The Role of Prayer',
                    'link': 'https://example.com/beyond2',
                    'guest': 'Pastor Mike Johnson',
                    'date_added': date(2024, 1, 15),
                    'scripture': 'Philippians 4:6-7'
                }
            ]
            
            for episode_data in episodes:
                existing = PodcastEpisode.query.filter_by(
                    series_id=beyond_series.id,
                    number=episode_data['number']
                ).first()
                if not existing:
                    episode = PodcastEpisode(**episode_data)
                    db.session.add(episode)
        
        # Create sample ongoing events
        events = [
            {
                'id': 'event_001',
                'title': 'Prayer in the Parlor',
                'description': 'Join us for prayer every Sunday at 8:30am in the parlor.',
                'type': 'ongoing',
                'category': 'prayer',
                'active': True
            },
            {
                'id': 'event_002',
                'title': 'Bible Study',
                'description': 'Weekly Bible study on Wednesdays at 7:00pm.',
                'type': 'ongoing',
                'category': 'education',
                'active': True
            },
            {
                'id': 'event_003',
                'title': 'Men\'s Fellowship',
                'description': 'Men\'s fellowship group meets every Saturday at 8:00am.',
                'type': 'ongoing',
                'category': 'fellowship',
                'active': True
            }
        ]
        
        for event_data in events:
            existing = OngoingEvent.query.get(event_data['id'])
            if not existing:
                event = OngoingEvent(**event_data)
                db.session.add(event)
        
        db.session.commit()
        print("✓ Sample data created successfully!")

def clear_all_data():
    """Clear all data from the database"""
    with app.app_context():
        print("Clearing all data...")
        
        # Delete in reverse order to avoid foreign key constraints
        PodcastEpisode.query.delete()
        PodcastSeries.query.delete()
        Sermon.query.delete()
        GalleryImage.query.delete()
        OngoingEvent.query.delete()
        Announcement.query.delete()
        
        db.session.commit()
        print("✓ All data cleared!")

def reset_database():
    """Reset the entire database"""
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        print("✓ Database reset!")

def main():
    """Main command-line interface"""
    if len(sys.argv) < 2:
        print("CPC New Haven Admin Management")
        print("Usage: python admin_management.py <command>")
        print()
        print("Commands:")
        print("  stats        - Show content statistics")
        print("  sample       - Create sample data")
        print("  clear        - Clear all data")
        print("  reset        - Reset entire database")
        print("  help         - Show this help message")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'stats':
        show_stats()
    elif command == 'sample':
        create_sample_data()
    elif command == 'clear':
        confirm = input("Are you sure you want to clear all data? (yes/no): ")
        if confirm.lower() == 'yes':
            clear_all_data()
        else:
            print("Operation cancelled.")
    elif command == 'reset':
        confirm = input("Are you sure you want to reset the entire database? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_database()
        else:
            print("Operation cancelled.")
    elif command == 'help':
        print("CPC New Haven Admin Management")
        print("Usage: python admin_management.py <command>")
        print()
        print("Commands:")
        print("  stats        - Show content statistics")
        print("  sample       - Create sample data")
        print("  clear        - Clear all data")
        print("  reset        - Reset entire database")
        print("  help         - Show this help message")
    else:
        print(f"Unknown command: {command}")
        print("Use 'python admin_management.py help' for available commands.")

if __name__ == '__main__':
    main()
