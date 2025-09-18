from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, date
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///cpc_newhaven.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from database import db
from flask_migrate import Migrate

migrate = Migrate()

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)

# Import models after db initialization
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent

# Routes
@app.route('/')
def index():
    """Homepage with highlights"""
    # Get active superfeatured announcements first, then regular ones
    superfeatured = Announcement.query.filter_by(active=True, superfeatured=True)\
        .order_by(Announcement.date_entered.desc()).limit(3).all()
    regular = Announcement.query.filter_by(active=True, superfeatured=False)\
        .order_by(Announcement.date_entered.desc()).limit(7).all()
    
    highlights = superfeatured + regular
    return render_template('index.html', highlights=highlights)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sermons')
def sermons():
    return render_template('sermons.html')

@app.route('/podcasts')
def podcasts():
    series = PodcastSeries.query.all()
    return render_template('podcasts.html', series=series)

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/give')
def give():
    return render_template('give.html')

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

# API Routes
@app.route('/api/announcements')
def api_announcements():
    """API endpoint matching your highlights.json structure"""
    announcements = Announcement.query.filter_by(active=True)\
        .order_by(Announcement.date_entered.desc()).all()
    
    return jsonify({
        'announcements': [
            {
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'dateEntered': a.date_entered.strftime('%Y-%m-%d') if a.date_entered else None,
                'active': 'true' if a.active else 'false',
                'type': a.type,
                'category': a.category,
                'tag': a.tag,
                'superfeatured': a.superfeatured,
                'featuredImage': a.featured_image
            } for a in announcements
        ]
    })

@app.route('/api/ongoing-events')
def api_ongoing_events():
    """API endpoint for ongoing events"""
    events = OngoingEvent.query.filter_by(active=True)\
        .order_by(OngoingEvent.date_entered.desc()).all()
    
    return jsonify({
        'ongoingEvents': [
            {
                'id': e.id,
                'title': e.title,
                'description': e.description,
                'dateEntered': e.date_entered.strftime('%Y-%m-%d') if e.date_entered else None,
                'active': 'true' if e.active else 'false',
                'type': e.type,
                'category': e.category
            } for e in events
        ]
    })

@app.route('/api/sermons')
def api_sermons():
    """API endpoint matching your sunday-sermons.json structure"""
    sermons = Sermon.query.order_by(Sermon.date.desc()).all()
    
    return jsonify({
        'title': 'Sunday Sermons',
        'description': 'Weekly sermons from our Sunday worship services',
        'episodes': [
            {
                'id': s.id,
                'title': s.title,
                'author': s.author,
                'scripture': s.scripture,
                'date': s.date.strftime('%Y-%m-%d') if s.date else None,
                'spotify_url': s.spotify_url,
                'youtube_url': s.youtube_url,
                'apple_podcasts_url': s.apple_podcasts_url,
                'link': s.spotify_url or s.youtube_url or s.apple_podcasts_url,
                'podcast-thumbnail_url': s.podcast_thumbnail_url
            } for s in sermons
        ]
    })

@app.route('/api/podcasts/beyond-podcast')
def api_beyond_podcast():
    """API endpoint for Beyond the Sunday Sermon podcast"""
    series = PodcastSeries.query.filter_by(title='Beyond the Sunday Sermon').first()
    if not series:
        return jsonify({'episodes': []})
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id)\
        .order_by(PodcastEpisode.date_added.desc()).all()
    
    return jsonify({
        'title': series.title,
        'description': series.description,
        'episodes': [
            {
                'number': ep.number,
                'title': ep.title,
                'link': ep.link,
                'guest': ep.guest,
                'date_added': ep.date_added.strftime('%Y-%m-%d') if ep.date_added else None,
                'season': ep.season,
                'scripture': ep.scripture,
                'podcast-thumbnail_url': ep.podcast_thumbnail_url
            } for ep in episodes
        ]
    })

@app.route('/api/podcasts/biblical-interpretation')
def api_biblical_interpretation():
    """API endpoint for Biblical Interpretation series"""
    series = PodcastSeries.query.filter_by(title='Biblical Interpretation').first()
    if not series:
        return jsonify({'episodes': []})
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id)\
        .order_by(PodcastEpisode.number).all()
    
    return jsonify({
        'title': series.title,
        'episodes': [
            {
                'number': ep.number,
                'title': ep.title,
                'link': ep.link
            } for ep in episodes
        ]
    })

@app.route('/api/podcasts/confessional-theology')
def api_confessional_theology():
    """API endpoint for Confessional Theology series"""
    series = PodcastSeries.query.filter_by(title='Confessional Theology').first()
    if not series:
        return jsonify({'episodes': []})
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id)\
        .order_by(PodcastEpisode.number.desc()).all()
    
    return jsonify({
        'title': series.title,
        'episodes': [
            {
                'number': ep.number,
                'title': ep.title,
                'listen': ep.listen_url,
                'handout': ep.handout_url
            } for ep in episodes
        ]
    })

@app.route('/api/podcasts/membership-seminar')
def api_membership_seminar():
    """API endpoint for Membership Seminar series"""
    series = PodcastSeries.query.filter_by(title='Membership Seminar').first()
    if not series:
        return jsonify({'episodes': []})
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id)\
        .order_by(PodcastEpisode.number).all()
    
    return jsonify({
        'title': series.title,
        'episodes': [
            {
                'number': ep.number,
                'title': ep.title,
                'link': ep.link
            } for ep in episodes
        ]
    })

@app.route('/api/gallery')
def api_gallery():
    """API endpoint for image gallery"""
    images = GalleryImage.query.order_by(GalleryImage.created.desc()).all()
    
    return jsonify({
        'images': [
            {
                'id': img.id,
                'name': img.name,
                'url': img.url,
                'size': img.size,
                'type': img.type,
                'created': img.created.strftime('%Y-%m-%d') if img.created else None,
                'tags': img.tags,
                'event': img.event
            } for img in images
        ]
    })

# Admin Interface
class AnnouncementView(ModelView):
    column_list = ('id', 'title', 'type', 'active', 'superfeatured', 'date_entered')
    column_searchable_list = ('title', 'description')
    column_filters = ('type', 'active', 'tag', 'superfeatured')
    form_excluded_columns = ('date_entered',)
    column_default_sort = ('date_entered', True)

class SermonView(ModelView):
    column_list = ('id', 'title', 'author', 'date', 'scripture')
    column_searchable_list = ('title', 'author', 'scripture')
    column_filters = ('author', 'date')
    column_default_sort = ('date', True)

class PodcastEpisodeView(ModelView):
    column_list = ('number', 'title', 'series', 'guest', 'date_added')
    column_searchable_list = ('title', 'guest')
    column_filters = ('series', 'guest')

class PodcastSeriesView(ModelView):
    column_list = ('title', 'description')
    column_searchable_list = ('title', 'description')

class GalleryImageView(ModelView):
    column_list = ('id', 'name', 'event', 'created')
    column_searchable_list = ('name',)
    column_filters = ('event',)

class OngoingEventView(ModelView):
    column_list = ('id', 'title', 'type', 'active', 'date_entered')
    column_searchable_list = ('title', 'description')
    column_filters = ('type', 'active')

# Setup admin
admin = Admin(app, name='CPC Admin', template_mode='bootstrap3')
admin.add_view(AnnouncementView(Announcement, db.session, name='Announcements'))
admin.add_view(OngoingEventView(OngoingEvent, db.session, name='Ongoing Events'))
admin.add_view(SermonView(Sermon, db.session, name='Sermons'))
admin.add_view(PodcastSeriesView(PodcastSeries, db.session, name='Podcast Series'))
admin.add_view(PodcastEpisodeView(PodcastEpisode, db.session, name='Podcast Episodes'))
admin.add_view(GalleryImageView(GalleryImage, db.session, name='Gallery Images'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
