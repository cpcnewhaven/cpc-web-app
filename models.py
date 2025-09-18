from datetime import datetime
from sqlalchemy import Text, JSON
from database import db

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(50))  # event, announcement, ongoing
    category = db.Column(db.String(50))
    tag = db.Column(db.String(50))
    superfeatured = db.Column(db.Boolean, default=False)
    featured_image = db.Column(db.String(500))

class Sermon(db.Model):
    __tablename__ = 'sermons'
    
    id = db.Column(db.String(20), primary_key=True)
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
    
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(500), nullable=False)
    size = db.Column(db.String(50))
    type = db.Column(db.String(50))
    tags = db.Column(JSON)  # Store as JSON array
    event = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

class OngoingEvent(db.Model):
    __tablename__ = 'ongoing_events'
    
    id = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(50))
    category = db.Column(db.String(50))
