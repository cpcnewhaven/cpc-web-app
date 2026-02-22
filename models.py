from datetime import datetime, date
from sqlalchemy import Text, JSON, event, func
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


class BibleBook(db.Model):
    __tablename__ = 'bible_books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    testament = db.Column(db.String(2), nullable=False) # 'OT' or 'NT'
    sort_order = db.Column(db.Integer, nullable=False, unique=True)

    def __repr__(self):
        return f'<BibleBook {self.name}>'

class BibleChapter(db.Model):
    __tablename__ = 'bible_chapters'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('bible_books.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    verse_count = db.Column(db.Integer, nullable=False)
    
    book = db.relationship('BibleBook', backref=db.backref('chapters', lazy=True))

class SermonSeries(db.Model):
    __tablename__ = 'sermon_series'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    slug = db.Column(db.String(100))
    external_url = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SermonSeries {self.title}>'


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
    banner_sort_order = db.Column(db.Integer, default=0)  # order in top bar when show_in_banner; lower = first
    archived = db.Column(db.Boolean, default=False)  # Archive = not active, archived True
    featured_image = db.Column(db.String(500))
    image_display_type = db.Column(db.String(50))  # poster, cover, etc.
    speaker = db.Column(db.String(200))  # who created/wrote the announcement
    expires_at = db.Column(db.Date, nullable=True)  # when to stop showing; NULL = never

class Sermon(db.Model):
    __tablename__ = 'sermons'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200), nullable=False)
    speaker = db.Column(db.String(100), nullable=True)
    scripture = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, default=True)
    archived = db.Column(db.Boolean, default=False)
    spotify_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))
    apple_podcasts_url = db.Column(db.String(500))
    podcast_thumbnail_url = db.Column(db.String(500))
    expires_at = db.Column(db.Date, nullable=True)  # when to stop showing; NULL = never
    
    # New fields for enhanced schema
    series_id = db.Column(db.Integer, db.ForeignKey('sermon_series.id'), nullable=True)
    episode_number = db.Column(db.Integer, nullable=True)
    
    # Scripture Validation
    bible_book_id = db.Column(db.Integer, db.ForeignKey('bible_books.id'), nullable=True)
    chapter_start = db.Column(db.Integer, nullable=True)
    verse_start = db.Column(db.Integer, nullable=True)
    chapter_end = db.Column(db.Integer, nullable=True)
    verse_end = db.Column(db.Integer, nullable=True)
    
    # Media & Links
    audio_file_url = db.Column(db.String(500), nullable=True) # Direct link for simple hosting
    video_file_url = db.Column(db.String(500), nullable=True) # Direct link for simple hosting
    
    # Association
    beyond_episode_id = db.Column(db.Integer, db.ForeignKey('podcast_episodes.id'), nullable=True)
    
    # Relationships
    series = db.relationship('SermonSeries', backref='sermons')
    book = db.relationship('BibleBook')
    beyond_episode = db.relationship('PodcastEpisode', foreign_keys=[beyond_episode_id])

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
    expires_at = db.Column(db.Date, nullable=True)  # when to stop showing; NULL = never

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
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    photographer = db.Column(db.String(100))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.Date, nullable=True)  # when to stop showing; NULL = never

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
    expires_at = db.Column(db.Date, nullable=True)  # when to stop showing; NULL = never

class TeachingSeries(db.Model):
    """Pastor-led teaching series (e.g. Total Christ) — 6–8 weeks, with event info."""
    __tablename__ = 'teaching_series'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    event_info = db.Column(db.Text)  # when/where (e.g. "Sundays 9am, Room 101")
    active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.Date, nullable=True)

    sessions = db.relationship('TeachingSeriesSession', back_populates='series', order_by='TeachingSeriesSession.number')


class TeachingSeriesSession(db.Model):
    """Single session in a teaching series (1, 2, 3...) with optional PDF."""
    __tablename__ = 'teaching_series_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    series_id = db.Column(db.Integer, db.ForeignKey('teaching_series.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    pdf_url = db.Column(db.String(500))  # uploaded PDF or external link
    session_date = db.Column(db.Date) # Date of the session
    date_entered = db.Column(db.DateTime, default=datetime.utcnow)

    series = db.relationship('TeachingSeries', back_populates='sessions')


@event.listens_for(TeachingSeriesSession, 'before_insert')
def auto_assign_session_number(mapper, connection, target):
    """Automatically assign the next number for the series if not provided."""
    # Check if number is None or 0 (treating 0 as unassigned)
    if not target.number:
        try:
            from sqlalchemy import select, func
            table = TeachingSeriesSession.__table__
            # Be very explicit about getting the max number for this series
            query = select(func.max(table.c.number)).where(table.c.series_id == target.series_id)
            max_num = connection.scalar(query) or 0
            target.number = int(max_num) + 1
        except Exception as e:
            # Fallback to 1 if anything goes wrong, but log it
            import logging
            logging.getLogger("cpc").warning("Failed to auto-assign session number in event listener: %s", e)
            target.number = 1


class Paper(db.Model):
    __tablename__ = 'papers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200), nullable=False)
    speaker = db.Column(db.String(200))
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
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
