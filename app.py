from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, date
import os
from dotenv import load_dotenv
from admin_utils import export_announcements_csv, export_sermons_csv, bulk_update_announcements, bulk_delete_content, get_content_stats, create_sample_podcast_series

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
# Database configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///cpc_newhaven.db')
# Handle PostgreSQL URL format for Render.com
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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

# Admin Management Routes
@app.route('/admin/export/announcements')
def admin_export_announcements():
    """Export announcements to CSV"""
    return export_announcements_csv()

@app.route('/admin/export/sermons')
def admin_export_sermons():
    """Export sermons to CSV"""
    return export_sermons_csv()

@app.route('/admin/stats')
def admin_stats():
    """Get detailed content statistics"""
    stats = get_content_stats()
    return jsonify(stats)

@app.route('/admin/setup/podcast-series')
def admin_setup_podcast_series():
    """Create default podcast series"""
    created_count = create_sample_podcast_series()
    return jsonify({'message': f'Created {created_count} podcast series', 'created': created_count})

@app.route('/admin/bulk/announcements', methods=['POST'])
def admin_bulk_announcements():
    """Bulk operations on announcements"""
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    field = data.get('field')
    value = data.get('value')
    
    if action == 'update' and field and value is not None:
        success = bulk_update_announcements(ids, field, value)
        return jsonify({'success': success})
    elif action == 'delete':
        success = bulk_delete_content(Announcement, ids)
        return jsonify({'success': success})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/admin/bulk/sermons', methods=['POST'])
def admin_bulk_sermons():
    """Bulk operations on sermons"""
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    
    if action == 'delete':
        success = bulk_delete_content(Sermon, ids)
        return jsonify({'success': success})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

# Enhanced Admin Interface
from flask_admin import BaseView, expose
from flask_admin.actions import action
from flask_admin.form import Select2Field
from wtforms import TextAreaField, SelectField, BooleanField, StringField, DateField, URLField
from wtforms.validators import DataRequired, URL, Length
from wtforms.widgets import TextArea
from datetime import datetime

class AnnouncementView(ModelView):
    column_list = ('id', 'title', 'type', 'category', 'active', 'superfeatured', 'date_entered')
    column_searchable_list = ('title', 'description', 'tag')
    column_filters = ('type', 'active', 'tag', 'superfeatured', 'category')
    column_sortable_list = ('title', 'type', 'active', 'superfeatured', 'date_entered')
    column_default_sort = ('date_entered', True)
    
    form_columns = ('id', 'title', 'description', 'type', 'category', 'tag', 'active', 'superfeatured', 'featured_image')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[DataRequired(), Length(max=2000)])
    }
    
    form_widget_args = {
        'description': {'rows': 10, 'style': 'width: 100%'},
        'featured_image': {'placeholder': 'https://example.com/image.jpg'}
    }
    
    column_labels = {
        'date_entered': 'Date Created',
        'superfeatured': 'Super Featured',
        'featured_image': 'Featured Image URL'
    }
    
    form_choices = {
        'type': [
            ('announcement', 'Announcement'),
            ('event', 'Event'),
            ('ongoing', 'Ongoing'),
            ('highlight', 'Highlight')
        ],
        'category': [
            ('general', 'General'),
            ('worship', 'Worship'),
            ('education', 'Education'),
            ('fellowship', 'Fellowship'),
            ('missions', 'Missions'),
            ('youth', 'Youth'),
            ('children', 'Children')
        ]
    }
    
    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected items?')
    def toggle_active(self, ids):
        try:
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    announcement.active = not announcement.active
            db.session.commit()
            flash(f'Successfully toggled active status for {len(ids)} announcements', 'success')
            return True
        except Exception as e:
            flash(f'Error toggling active status: {str(e)}', 'error')
            return False
    
    @action('toggle_superfeatured', 'Toggle Super Featured', 'Are you sure you want to toggle the super featured status of selected items?')
    def toggle_superfeatured(self, ids):
        try:
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    announcement.superfeatured = not announcement.superfeatured
            db.session.commit()
            flash(f'Successfully toggled super featured status for {len(ids)} announcements', 'success')
            return True
        except Exception as e:
            flash(f'Error toggling super featured status: {str(e)}', 'error')
            return False
    
    @action('set_category', 'Set Category', 'Are you sure you want to update the category of selected items?')
    def set_category(self, ids):
        # This would need a custom form, but for now we'll use a simple approach
        category = request.form.get('category')
        if category:
            try:
                for id in ids:
                    announcement = Announcement.query.get(id)
                    if announcement:
                        announcement.category = category
                db.session.commit()
                flash(f'Successfully updated category for {len(ids)} announcements', 'success')
                return True
            except Exception as e:
                flash(f'Error updating category: {str(e)}', 'error')
                return False
        return False

class SermonView(ModelView):
    column_list = ('id', 'title', 'author', 'date', 'scripture', 'spotify_url', 'youtube_url')
    column_searchable_list = ('title', 'author', 'scripture')
    column_filters = ('author', 'date')
    column_sortable_list = ('title', 'author', 'date')
    column_default_sort = ('date', True)
    
    form_columns = ('id', 'title', 'author', 'scripture', 'date', 'spotify_url', 'youtube_url', 'apple_podcasts_url', 'podcast_thumbnail_url')
    form_extra_fields = {
        'scripture': TextAreaField('Scripture', widget=TextArea()),
        'spotify_url': URLField('Spotify URL', validators=[URL()]),
        'youtube_url': URLField('YouTube URL', validators=[URL()]),
        'apple_podcasts_url': URLField('Apple Podcasts URL', validators=[URL()]),
        'podcast_thumbnail_url': URLField('Thumbnail URL', validators=[URL()])
    }
    
    form_widget_args = {
        'scripture': {'rows': 3, 'style': 'width: 100%'},
        'spotify_url': {'placeholder': 'https://open.spotify.com/episode/...'},
        'youtube_url': {'placeholder': 'https://youtube.com/watch?v=...'},
        'apple_podcasts_url': {'placeholder': 'https://podcasts.apple.com/podcast/...'},
        'podcast_thumbnail_url': {'placeholder': 'https://example.com/thumbnail.jpg'}
    }
    
    column_labels = {
        'spotify_url': 'Spotify',
        'youtube_url': 'YouTube',
        'apple_podcasts_url': 'Apple Podcasts',
        'podcast_thumbnail_url': 'Thumbnail'
    }
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected sermons?')
    def bulk_delete(self, ids):
        try:
            for id in ids:
                sermon = Sermon.query.get(id)
                if sermon:
                    db.session.delete(sermon)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} sermons', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting sermons: {str(e)}', 'error')
            return False

class PodcastSeriesView(ModelView):
    column_list = ('title', 'description', 'episode_count')
    column_searchable_list = ('title', 'description')
    column_sortable_list = ('title',)
    
    form_columns = ('title', 'description')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Length(max=1000)])
    }
    
    form_widget_args = {
        'description': {'rows': 5, 'style': 'width: 100%'}
    }
    
    def episode_count(self, context, model, name):
        return len(model.episodes) if model.episodes else 0
    
    episode_count.column_type = 'integer'

class PodcastEpisodeView(ModelView):
    column_list = ('number', 'title', 'series', 'guest', 'date_added', 'scripture')
    column_searchable_list = ('title', 'guest', 'scripture')
    column_filters = ('series', 'guest', 'season')
    column_sortable_list = ('number', 'title', 'date_added')
    column_default_sort = ('number', True)
    
    form_columns = ('series', 'number', 'title', 'link', 'listen_url', 'handout_url', 'guest', 'date_added', 'season', 'scripture', 'podcast_thumbnail_url')
    form_extra_fields = {
        'scripture': TextAreaField('Scripture', widget=TextArea()),
        'link': URLField('Episode Link', validators=[URL()]),
        'listen_url': URLField('Listen URL', validators=[URL()]),
        'handout_url': URLField('Handout URL', validators=[URL()]),
        'podcast_thumbnail_url': URLField('Thumbnail URL', validators=[URL()])
    }
    
    form_widget_args = {
        'scripture': {'rows': 3, 'style': 'width: 100%'},
        'link': {'placeholder': 'https://example.com/episode'},
        'listen_url': {'placeholder': 'https://example.com/listen'},
        'handout_url': {'placeholder': 'https://example.com/handout.pdf'},
        'podcast_thumbnail_url': {'placeholder': 'https://example.com/thumbnail.jpg'}
    }
    
    column_labels = {
        'listen_url': 'Listen URL',
        'handout_url': 'Handout URL',
        'podcast_thumbnail_url': 'Thumbnail'
    }
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected podcast episodes?')
    def bulk_delete(self, ids):
        try:
            for id in ids:
                episode = PodcastEpisode.query.get(id)
                if episode:
                    db.session.delete(episode)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} podcast episodes', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting podcast episodes: {str(e)}', 'error')
            return False

class GalleryImageView(ModelView):
    column_list = ('id', 'name', 'event', 'created', 'tags_display')
    column_searchable_list = ('name',)
    column_filters = ('event',)
    column_sortable_list = ('name', 'created')
    column_default_sort = ('created', True)
    
    form_columns = ('id', 'name', 'url', 'size', 'type', 'tags', 'event')
    form_extra_fields = {
        'url': URLField('Image URL', validators=[DataRequired(), URL()]),
        'tags': TextAreaField('Tags (comma-separated)', widget=TextArea())
    }
    
    form_widget_args = {
        'tags': {'rows': 3, 'style': 'width: 100%', 'placeholder': 'worship, fellowship, youth, etc.'},
        'url': {'placeholder': 'https://example.com/image.jpg'}
    }
    
    column_labels = {
        'event': 'Is Event Photo'
    }
    
    def tags_display(self, context, model, name):
        if model.tags:
            return ', '.join(model.tags) if isinstance(model.tags, list) else str(model.tags)
        return ''
    
    tags_display.column_type = 'string'
    
    def on_model_change(self, form, model, is_created):
        if form.tags.data:
            # Convert comma-separated string to list
            tags = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
            model.tags = tags
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected gallery images?')
    def bulk_delete(self, ids):
        try:
            for id in ids:
                image = GalleryImage.query.get(id)
                if image:
                    db.session.delete(image)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} gallery images', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting gallery images: {str(e)}', 'error')
            return False
    
    @action('toggle_event', 'Toggle Event Status', 'Are you sure you want to toggle the event status of selected images?')
    def toggle_event(self, ids):
        try:
            for id in ids:
                image = GalleryImage.query.get(id)
                if image:
                    image.event = not image.event
            db.session.commit()
            flash(f'Successfully toggled event status for {len(ids)} images', 'success')
            return True
        except Exception as e:
            flash(f'Error toggling event status: {str(e)}', 'error')
            return False

class OngoingEventView(ModelView):
    column_list = ('id', 'title', 'type', 'category', 'active', 'date_entered')
    column_searchable_list = ('title', 'description')
    column_filters = ('type', 'active', 'category')
    column_sortable_list = ('title', 'type', 'active', 'date_entered')
    column_default_sort = ('date_entered', True)
    
    form_columns = ('id', 'title', 'description', 'type', 'category', 'active')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[DataRequired(), Length(max=2000)])
    }
    
    form_widget_args = {
        'description': {'rows': 8, 'style': 'width: 100%'}
    }
    
    form_choices = {
        'type': [
            ('ongoing', 'Ongoing'),
            ('recurring', 'Recurring'),
            ('special', 'Special Event')
        ],
        'category': [
            ('worship', 'Worship'),
            ('education', 'Education'),
            ('fellowship', 'Fellowship'),
            ('missions', 'Missions'),
            ('youth', 'Youth'),
            ('children', 'Children'),
            ('prayer', 'Prayer')
        ]
    }
    
    column_labels = {
        'date_entered': 'Date Created'
    }
    
    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected items?')
    def toggle_active(self, ids):
        try:
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    event.active = not event.active
            db.session.commit()
            flash(f'Successfully toggled active status for {len(ids)} events', 'success')
            return True
        except Exception as e:
            flash(f'Error toggling active status: {str(e)}', 'error')
            return False
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected events?')
    def bulk_delete(self, ids):
        try:
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    db.session.delete(event)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} events', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting events: {str(e)}', 'error')
            return False

# Custom Admin Dashboard
class DashboardView(BaseView):
    @expose('/')
    def index(self):
        stats = {
            'announcements': Announcement.query.count(),
            'active_announcements': Announcement.query.filter_by(active=True).count(),
            'sermons': Sermon.query.count(),
            'podcast_series': PodcastSeries.query.count(),
            'podcast_episodes': PodcastEpisode.query.count(),
            'gallery_images': GalleryImage.query.count(),
            'ongoing_events': OngoingEvent.query.count(),
            'active_events': OngoingEvent.query.filter_by(active=True).count()
        }
        
        recent_announcements = Announcement.query.order_by(Announcement.date_entered.desc()).limit(5).all()
        recent_sermons = Sermon.query.order_by(Sermon.date.desc()).limit(5).all()
        
        return self.render('admin/dashboard.html', 
                         stats=stats, 
                         recent_announcements=recent_announcements,
                         recent_sermons=recent_sermons)

# Setup admin with enhanced organization
admin = Admin(app, name='CPC Admin', template_mode='bootstrap3')

# Add dashboard view
admin.add_view(DashboardView(name='Dashboard', endpoint='dashboard'))

# Add views with categories
admin.add_view(AnnouncementView(Announcement, db.session, name='Announcements', category='Content'))
admin.add_view(OngoingEventView(OngoingEvent, db.session, name='Events', category='Content'))
admin.add_view(SermonView(Sermon, db.session, name='Sermons', category='Media'))
admin.add_view(PodcastSeriesView(PodcastSeries, db.session, name='Podcast Series', category='Media'))
admin.add_view(PodcastEpisodeView(PodcastEpisode, db.session, name='Podcast Episodes', category='Media'))
admin.add_view(GalleryImageView(GalleryImage, db.session, name='Gallery', category='Media'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
