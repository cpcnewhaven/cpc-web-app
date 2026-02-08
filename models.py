from datetime import datetime
import uuid
from sqlalchemy import Text, JSON
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.String(60), primary_key=True, default=lambda: uuid.uuid4().hex)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(50))  # event, announcement, ongoing
    category = db.Column(db.String(50))
    tag = db.Column(db.String(50))
    superfeatured = db.Column(db.Boolean, default=False)
    show_in_banner = db.Column(db.Boolean, default=False)  # show in top yellow bar (weather, parking, etc.)
    featured_image = db.Column(db.String(500))
    image_display_type = db.Column(db.String(50))  # poster, cover, etc.

class Sermon(db.Model):
    __tablename__ = 'sermons'
    
    id = db.Column(db.String(60), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    scripture = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    spotify_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))
    apple_podcasts_url = db.Column(db.String(500))
    podcast_thumbnail_url = db.Column(db.String(500))

class PodcastEpisode(db.Model):
    __tablename__ = 'podcast_episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('podcast_series.id'))
    number = db.Column(db.Integer)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500))
    listen_url = db.Column(db.String(500))
    handout_url = db.Column(db.String(500))
    guest = db.Column(db.String(100))
    date_added = db.Column(db.Date)
    season = db.Column(db.Integer)
    scripture = db.Column(db.String(200))
    podcast_thumbnail_url = db.Column(db.String(500))
    
    series = db.relationship('PodcastSeries', back_populates='episodes')

class PodcastSeries(db.Model):
    __tablename__ = 'podcast_series'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    episodes = db.relationship('PodcastEpisode', back_populates='series')

class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'
    
    id = db.Column(db.String(60), primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(500), nullable=False)
    size = db.Column(db.String(50))
    type = db.Column(db.String(50))
    tags = db.Column(JSON)  # Store as JSON array
    event = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

class OngoingEvent(db.Model):
    __tablename__ = 'ongoing_events'
    
    id = db.Column(db.String(60), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(50))
    category = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)  # lower = first; drag to reorder

class Paper(db.Model):
    __tablename__ = 'papers'
    
    id = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    date_published = db.Column(db.Date)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))
    tags = db.Column(JSON)  # Store as JSON array
    file_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
