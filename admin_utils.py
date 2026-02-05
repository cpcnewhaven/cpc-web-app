"""
Admin utility functions for bulk operations and data management
"""
import json
import csv
from io import StringIO
from flask import Response, flash
from database import db
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent

def export_announcements_csv():
    """Export announcements to CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Title', 'Description', 'Type', 'Category', 'Tag', 'Active', 'Show in Top Bar', 'Super Featured', 'Date Entered', 'Featured Image'])
    
    # Write data
    announcements = Announcement.query.all()
    for announcement in announcements:
        writer.writerow([
            announcement.id,
            announcement.title,
            announcement.description,
            announcement.type or '',
            announcement.category or '',
            announcement.tag or '',
            announcement.active,
            getattr(announcement, 'show_in_banner', False),
            announcement.superfeatured,
            announcement.date_entered.strftime('%Y-%m-%d %H:%M:%S') if announcement.date_entered else '',
            announcement.featured_image or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=announcements.csv'}
    )

def export_sermons_csv():
    """Export sermons to CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Title', 'Author', 'Scripture', 'Date', 'Spotify URL', 'YouTube URL', 'Apple Podcasts URL', 'Thumbnail URL'])
    
    # Write data
    sermons = Sermon.query.all()
    for sermon in sermons:
        writer.writerow([
            sermon.id,
            sermon.title,
            sermon.author,
            sermon.scripture or '',
            sermon.date.strftime('%Y-%m-%d') if sermon.date else '',
            sermon.spotify_url or '',
            sermon.youtube_url or '',
            sermon.apple_podcasts_url or '',
            sermon.podcast_thumbnail_url or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=sermons.csv'}
    )

def bulk_update_announcements(ids, field, value):
    """Bulk update announcements"""
    try:
        count = 0
        for id in ids:
            announcement = Announcement.query.get(id)
            if announcement:
                setattr(announcement, field, value)
                count += 1
        
        db.session.commit()
        flash(f'Successfully updated {count} announcements', 'success')
        return True
    except Exception as e:
        flash(f'Error updating announcements: {str(e)}', 'error')
        return False

def bulk_delete_content(model_class, ids):
    """Bulk delete content"""
    try:
        count = 0
        for id in ids:
            item = model_class.query.get(id)
            if item:
                db.session.delete(item)
                count += 1
        
        db.session.commit()
        flash(f'Successfully deleted {count} items', 'success')
        return True
    except Exception as e:
        flash(f'Error deleting items: {str(e)}', 'error')
        return False

def get_content_stats():
    """Get comprehensive content statistics"""
    return {
        'announcements': {
            'total': Announcement.query.count(),
            'active': Announcement.query.filter_by(active=True).count(),
            'superfeatured': Announcement.query.filter_by(superfeatured=True).count(),
            'by_type': db.session.query(Announcement.type, db.func.count(Announcement.id))
                .group_by(Announcement.type).all(),
            'by_category': db.session.query(Announcement.category, db.func.count(Announcement.id))
                .group_by(Announcement.category).all()
        },
        'sermons': {
            'total': Sermon.query.count(),
            'by_author': db.session.query(Sermon.author, db.func.count(Sermon.id))
                .group_by(Sermon.author).all(),
            'recent_month': Sermon.query.filter(
                Sermon.date >= db.func.date('now', '-1 month')
            ).count()
        },
        'podcasts': {
            'series': PodcastSeries.query.count(),
            'episodes': PodcastEpisode.query.count(),
            'by_series': db.session.query(PodcastSeries.title, db.func.count(PodcastEpisode.id))
                .join(PodcastEpisode).group_by(PodcastSeries.title).all()
        },
        'gallery': {
            'total': GalleryImage.query.count(),
            'event_photos': GalleryImage.query.filter_by(event=True).count()
        },
        'events': {
            'total': OngoingEvent.query.count(),
            'active': OngoingEvent.query.filter_by(active=True).count()
        }
    }

def create_sample_podcast_series():
    """Create sample podcast series if they don't exist"""
    series_data = [
        {
            'title': 'Beyond the Sunday Sermon',
            'description': 'Extended conversations and deeper dives into biblical topics with our pastoral staff and special guests.'
        },
        {
            'title': 'Biblical Interpretation',
            'description': 'Teaching series on how to read and understand Scripture in its historical and theological context.'
        },
        {
            'title': 'Confessional Theology',
            'description': 'Exploring Reformed theology and doctrine through systematic study of our confessional standards.'
        },
        {
            'title': 'Membership Seminar',
            'description': 'Understanding church membership and the Christian life through our comprehensive membership course.'
        }
    ]
    
    created_count = 0
    for series_info in series_data:
        existing = PodcastSeries.query.filter_by(title=series_info['title']).first()
        if not existing:
            series = PodcastSeries(
                title=series_info['title'],
                description=series_info['description']
            )
            db.session.add(series)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        flash(f'Created {created_count} new podcast series', 'success')
    
    return created_count
