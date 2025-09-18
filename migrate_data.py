#!/usr/bin/env python3
"""
Data migration script to populate the database with sample data
"""
import json
from app import app, db
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent
from datetime import datetime

def create_sample_data():
    """Create sample data for testing"""
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Sample announcements
        announcements = [
            Announcement(
                id='ann_001',
                title='Welcome to CPC New Haven',
                description='We are excited to welcome you to our church community. Join us for worship every Sunday at 10:30am.',
                date_entered=datetime.utcnow(),
                active=True,
                type='announcement',
                category='general',
                superfeatured=True
            ),
            Announcement(
                id='ann_002',
                title='Sunday School Classes Resume',
                description='Children\'s Sunday School and Adult Sunday Studies begin at 9:30am every Sunday.',
                date_entered=datetime.utcnow(),
                active=True,
                type='event',
                category='education',
                superfeatured=False
            ),
            Announcement(
                id='ann_003',
                title='Fellowship Lunch',
                description='Join us for fellowship lunch every Sunday after worship service at 12:00pm.',
                date_entered=datetime.utcnow(),
                active=True,
                type='ongoing',
                category='fellowship',
                superfeatured=False
            )
        ]
        
        for announcement in announcements:
            existing = Announcement.query.get(announcement.id)
            if not existing:
                db.session.add(announcement)
        
        # Sample sermons
        sermons = [
            Sermon(
                id='serm_001',
                title='The Grace of God',
                author='Pastor John Smith',
                scripture='Ephesians 2:8-9',
                date=datetime(2024, 1, 7).date(),
                spotify_url='https://open.spotify.com/episode/example1',
                youtube_url='https://youtube.com/watch?v=example1',
                apple_podcasts_url='https://podcasts.apple.com/podcast/example1',
                podcast_thumbnail_url='https://example.com/thumbnail1.jpg'
            ),
            Sermon(
                id='serm_002',
                title='Walking in Faith',
                author='Pastor John Smith',
                scripture='Hebrews 11:1-6',
                date=datetime(2024, 1, 14).date(),
                spotify_url='https://open.spotify.com/episode/example2',
                youtube_url='https://youtube.com/watch?v=example2',
                podcast_thumbnail_url='https://example.com/thumbnail2.jpg'
            )
        ]
        
        for sermon in sermons:
            existing = Sermon.query.get(sermon.id)
            if not existing:
                db.session.add(sermon)
        
        # Sample podcast series
        beyond_series = PodcastSeries(
            title='Beyond the Sunday Sermon',
            description='Extended conversations and deeper dives into biblical topics'
        )
        
        existing_series = PodcastSeries.query.filter_by(title='Beyond the Sunday Sermon').first()
        if not existing_series:
            db.session.add(beyond_series)
            db.session.flush()  # Get the ID
            series_id = beyond_series.id
        else:
            series_id = existing_series.id
        
        # Sample podcast episodes
        episodes = [
            PodcastEpisode(
                series_id=series_id,
                number=1,
                title='Understanding Grace',
                link='https://example.com/beyond1',
                guest='Dr. Jane Doe',
                date_added=datetime(2024, 1, 8).date(),
                scripture='Romans 3:23-24',
                podcast_thumbnail_url='https://example.com/beyond1.jpg'
            ),
            PodcastEpisode(
                series_id=series_id,
                number=2,
                title='The Role of Prayer',
                link='https://example.com/beyond2',
                guest='Pastor Mike Johnson',
                date_added=datetime(2024, 1, 15).date(),
                scripture='Philippians 4:6-7',
                podcast_thumbnail_url='https://example.com/beyond2.jpg'
            )
        ]
        
        for episode in episodes:
            existing = PodcastEpisode.query.filter_by(
                series_id=series_id,
                number=episode.number
            ).first()
            if not existing:
                db.session.add(episode)
        
        # Sample ongoing events
        ongoing_events = [
            OngoingEvent(
                id='event_001',
                title='Prayer in the Parlor',
                description='Join us for prayer every Sunday at 8:30am in the parlor.',
                date_entered=datetime.utcnow(),
                active=True,
                type='ongoing',
                category='prayer'
            ),
            OngoingEvent(
                id='event_002',
                title='Bible Study',
                description='Weekly Bible study on Wednesdays at 7:00pm.',
                date_entered=datetime.utcnow(),
                active=True,
                type='ongoing',
                category='education'
            )
        ]
        
        for event in ongoing_events:
            existing = OngoingEvent.query.get(event.id)
            if not existing:
                db.session.add(event)
        
        # Commit all changes
        db.session.commit()
        print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()
