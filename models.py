from datetime import datetime
from sqlalchemy import Text, JSON
from database import db
from werkzeug.security import generate_password_hash, check_password_hash


class GlobalIDCounter(db.Model):
    """Single-row table that tracks the next universal content ID.
    Every piece of content (announcement, sermon, podcast, event, etc.)
    pulls its ID from this shared counter so IDs are unique across types
    and always go up: 1, 2, 3, … 543, 544, …
    """
    __tablename__ = 'global_id_counter'

    id = db.Column(db.Integer, primary_key=True)          # always 1
    next_id = db.Column(db.Integer, nullable=False, default=1)


def next_global_id():
    """Return the next universal content ID and bump the counter.

    Must be called inside an active ``db.session`` / app-context.

    Uses ``no_autoflush`` so that calling this from an
    ``on_model_change`` hook (where a new model with id=None is already
    in the session) does not trigger an early INSERT that would violate
    PostgreSQL's NOT-NULL primary-key constraint.
    """
    with db.session.no_autoflush:
        counter = GlobalIDCounter.query.first()
        if not counter:
            counter = GlobalIDCounter(id=1, next_id=1)
            db.session.add(counter)
        current_id = counter.next_id
        counter.next_id = current_id + 1
    return current_id


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.String(50))  # event, announcement, ongoing
    category = db.Column(db.String(50))
    tag = db.Column(db.String(50))
    superfeatured = db.Column(db.Boolean, default=False)
    show_in_banner = db.Column(db.Boolean, default=False)  # show in top yellow bar (weather, parking, etc.)
    archived = db.Column(db.Boolean, default=False)  # Archive = not active, archived True
    featured_image = db.Column(db.String(500))
    image_display_type = db.Column(db.String(50))  # poster, cover, etc.
    author = db.Column(db.String(200))  # who created/wrote the announcement

class Sermon(db.Model):
    __tablename__ = 'sermons'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    scripture = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, default=True)
    archived = db.Column(db.Boolean, default=False)
    spotify_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))
    apple_podcasts_url = db.Column(db.String(500))
    podcast_thumbnail_url = db.Column(db.String(500))

class PodcastEpisode(db.Model):
    __tablename__ = 'podcast_episodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
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

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    episodes = db.relationship('PodcastEpisode', back_populates='series')

class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.String(200))
    url = db.Column(db.String(500), nullable=False)
    size = db.Column(db.String(50))
    type = db.Column(db.String(50))
    tags = db.Column(JSON)  # Store as JSON array
    event = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

class OngoingEvent(db.Model):
    __tablename__ = 'ongoing_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    archived = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(50))
    category = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)  # lower = first; drag to reorder

class Paper(db.Model):
    __tablename__ = 'papers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
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

class AuditLog(db.Model):
    """Tracks who added, edited, or deleted content and when."""
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = db.Column(db.String(80), nullable=False)               # session username
    action = db.Column(db.String(20), nullable=False)              # 'created', 'edited', 'deleted'
    entity_type = db.Column(db.String(50), nullable=False)         # e.g. 'Announcement', 'Sermon'
    entity_id = db.Column(db.Integer)                              # id of the affected record
    entity_title = db.Column(db.String(300))                       # human-readable title/name
    details = db.Column(db.Text)                                   # optional extra info (changed fields, etc.)

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type} #{self.entity_id} by {self.user}>'


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
