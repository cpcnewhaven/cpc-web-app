import warnings
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping
    collections.Iterable = collections.abc.Iterable
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Sequence = collections.abc.Sequence

import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response, session, has_app_context, has_request_context
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView as _AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_caching import Cache
from datetime import datetime, date, timedelta
import os
import uuid
import requests
from werkzeug.utils import secure_filename
import feedparser
import json
import re
from ics import Calendar, Event
from dateutil import tz
import pytz
from dotenv import load_dotenv
import zipfile
import io

# Optional integration with Google Cloud Storage for media
try:
    from google.cloud import storage
    GCS_ENABLED = True
except ImportError:
    GCS_ENABLED = False

# ---------------------------------------------------------------------------
# Global monkeypatch for Flask-Admin 1.6.x compatibility.
# This must happen before model views are instantiated.
# ---------------------------------------------------------------------------
try:
    from markupsafe import Markup

    # Patch widgets to return Markup (prevents raw HTML escaping)
    from flask_admin.model.widgets import RenderTemplateWidget, InlineFieldListWidget
    
    def wrap_markup(original_func):
        def patched_func(self, *args, **kwargs):
            res = original_func(self, *args, **kwargs)
            return Markup(res) if res is not None else res
        return patched_func

    RenderTemplateWidget.__call__ = wrap_markup(RenderTemplateWidget.__call__)
    InlineFieldListWidget.__call__ = wrap_markup(InlineFieldListWidget.__call__)

    # Also patch InlineModelFormField if it exists
    try:
        from flask_admin.contrib.sqla.fields import InlineModelFormField
        InlineModelFormField.__call__ = wrap_markup(InlineModelFormField.__call__)
    except (ImportError, AttributeError):
        pass

    # Global WTForms widget patch for safety
    try:
        import wtforms.widgets.core
        if hasattr(wtforms.widgets.core, 'HTMLString'):
            # Ensure WTForms' HTMLString is treated as Markup by Jinja
            class PatchedHTMLString(Markup):
                def __new__(cls, value='', **kwargs):
                    return super(PatchedHTMLString, cls).__new__(cls, value)
            wtforms.widgets.core.HTMLString = PatchedHTMLString
    except Exception:
        pass

except Exception as e:
    import logging
    logging.getLogger("cpc").warning("Failed to apply robust WTForms 3.0 monkeypatch: %s", e)

from json_api import json_api
from port_finder import find_available_port
from google_drive_routes import google_drive_bp

load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup (so gunicorn workers inherit this)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("cpc")

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')


# Configuration
app.config.from_object('config')
cache = Cache(app)

app.register_blueprint(json_api)
app.register_blueprint(google_drive_bp)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Session cookie security — enforce HTTPS-only cookies in production
if os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER'):
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ---------------------------------------------------------------------------
# Database URL — require DATABASE_URL in production, allow SQLite for local dev
# ---------------------------------------------------------------------------
_is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER')
database_url = os.getenv('DATABASE_URL', '')

if not database_url:
    if _is_production:
        raise RuntimeError(
            "FATAL: DATABASE_URL environment variable is not set. "
            "The app cannot start without a database in production."
        )
    # Local development only — fallback to SQLite
    database_url = 'sqlite:///cpc_newhaven.db'
    log.info("DATABASE_URL not set — using local SQLite for development")

# Render provides postgres:// but SQLAlchemy 1.4+ requires postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connection-pool tuning — keep always connected to Postgres when DATABASE_URL is set.
# pool_pre_ping: test each connection before use (auto-reconnect if dropped).
# pool_recycle: refresh connections before server idle timeout (e.g. Render ~5 min).
_engine_opts = {
    'pool_size': 5,
    'max_overflow': 3,
    'pool_recycle': 240,
    'pool_pre_ping': True,
}
if database_url.startswith('postgresql'):
    _engine_opts['connect_args'] = {'connect_timeout': 10}
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = _engine_opts

# Log DB type + host (NEVER log the full URL — it contains credentials)
try:
    from urllib.parse import urlparse
    _parsed = urlparse(database_url)
    _db_kind = _parsed.scheme.split('+')[0]       # "postgresql" or "sqlite"
    _db_host = _parsed.hostname or 'localhost'
    _db_name = _parsed.path.lstrip('/')
    if _db_kind == 'postgresql':
        log.info("DB init: PostgreSQL host=%s db=%s (always connected: pool_pre_ping + pool_recycle)", _db_host, _db_name)
    else:
        log.info("DB init: engine=%s host=%s dbname=%s", _db_kind, _db_host, _db_name)
except Exception:
    log.info("DB init: engine=unknown (URL parsing failed)")

# Initialize extensions
from database import db
from flask_migrate import Migrate

migrate = Migrate()

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)

# Import models after db initialization
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent, Paper, User, GlobalIDCounter, next_global_id, AuditLog, TeachingSeries, TeachingSeriesSession, BibleBook, BibleChapter, SermonSeries, SiteContent, LifeGroup

def ensure_db_columns():
    """Add any missing columns to existing tables (SQLite and PostgreSQL).

    Call this AFTER ``db.create_all()`` inside an app context so that
    tables already exist.  ``db.create_all()`` creates tables that are
    missing but never adds new columns to tables that already exist.
    This function fills that gap for both SQLite and PostgreSQL.
    """
    # Map of table -> list of (column_name, sqlite_type, pg_type)
    # Every column that was ever added AFTER an initial deploy must appear here
    # so that existing PostgreSQL/SQLite tables get the column via ALTER TABLE.
    MIGRATIONS = {
        'announcements': [
            ('show_in_banner', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
            ('banner_sort_order', 'INTEGER DEFAULT 0', 'INTEGER DEFAULT 0'),
            ('featured_image', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('image_display_type', 'VARCHAR(50)', 'VARCHAR(50)'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
            ('speaker', 'VARCHAR(200)', 'VARCHAR(200)'),
            ('expires_at', 'DATE', 'DATE'),
            ('event_date', 'DATE', 'DATE'),
            ('event_start_time', 'VARCHAR(100)', 'VARCHAR(100)'),
            ('event_end_time', 'VARCHAR(100)', 'VARCHAR(100)'),
            ('revision', 'INTEGER DEFAULT 1', 'INTEGER DEFAULT 1'),
            ('updated_at', 'DATETIME', 'TIMESTAMP'),
            ('updated_by', 'VARCHAR(80)', 'VARCHAR(80)'),
        ],
        'ongoing_events': [
            ('sort_order', 'INTEGER DEFAULT 0', 'INTEGER DEFAULT 0'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
            ('expires_at', 'DATE', 'DATE'),
        ],
        'sermons': [
            ('active', 'BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
            ('expires_at', 'DATE', 'DATE'),
            ('series_id', 'INTEGER', 'INTEGER'),
            ('episode_number', 'INTEGER', 'INTEGER'),
            ('bible_book_id', 'INTEGER', 'INTEGER'),
            ('chapter_start', 'INTEGER', 'INTEGER'),
            ('verse_start', 'INTEGER', 'INTEGER'),
            ('chapter_end', 'INTEGER', 'INTEGER'),
            ('verse_end', 'INTEGER', 'INTEGER'),
            ('audio_file_url', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('video_file_url', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('beyond_episode_id', 'INTEGER', 'INTEGER'),
            ('speaker', 'VARCHAR(200)', 'VARCHAR(200)'),
            ('speaker_id', 'INTEGER', 'INTEGER'),
            ('featured', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
        ],
        'podcast_episodes': [
            ('expires_at', 'DATE', 'DATE'),
        ],
        'teaching_series_sessions': [
            ('session_date', 'DATE', 'DATE'),
        ],
        'gallery_images': [
            ('expires_at', 'DATE', 'DATE'),
            ('description', 'TEXT', 'TEXT'),
            ('location', 'VARCHAR(200)', 'VARCHAR(200)'),
            ('photographer', 'VARCHAR(100)', 'VARCHAR(100)'),
            ('sort_order', 'INTEGER DEFAULT 0', 'INTEGER DEFAULT 0'),
        ],
        'users': [
            ('last_login_at', 'DATETIME', 'TIMESTAMP'),
        ],
        'papers': [
            ('speaker', 'VARCHAR(200)', 'VARCHAR(200)'),
        ],
        'sermon_series': [
            ('slug', 'VARCHAR(100)', 'VARCHAR(100)'),
            ('external_url', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('sort_order', 'INTEGER DEFAULT 0', 'INTEGER DEFAULT 0'),
        ],
    }

    if database_url.startswith('sqlite:///'):
        _ensure_columns_sqlite(MIGRATIONS)
    elif 'postgresql' in database_url or 'postgres' in database_url:
        _ensure_columns_pg(MIGRATIONS)


def _ensure_columns_sqlite(migrations):
    import sqlite3
    db_path = database_url.replace('sqlite:///', '', 1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(__file__), db_path)
    if not os.path.exists(db_path):
        alt = os.path.join(os.path.dirname(__file__), 'instance', 'cpc_newhaven.db')
        if os.path.exists(alt):
            db_path = alt
        else:
            return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for table, columns_to_add in migrations.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cursor.fetchall()}
            if not existing:
                continue  # table doesn't exist yet
            for col_name, sqlite_type, _pg_type in columns_to_add:
                if col_name not in existing:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {sqlite_type}")
        conn.commit()
        conn.close()
    except Exception as exc:
        app.logger.warning("SQLite column migration skipped: %s", exc)


def _ensure_columns_pg(migrations):
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            for table, columns_to_add in migrations.items():
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = :tbl"
                ), {'tbl': table})
                existing = {row[0] for row in result}
                if not existing:
                    continue  # table doesn't exist yet
                for col_name, _sqlite_type, pg_type in columns_to_add:
                    if col_name not in existing:
                        conn.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN {col_name} {pg_type}"
                        ))
            conn.commit()
    except Exception as exc:
        app.logger.warning("PostgreSQL column migration skipped: %s", exc)

# ---------------------------------------------------------------------------
# Health check — lightweight DB liveness probe for Render
# ---------------------------------------------------------------------------
@app.route('/healthz')
def healthz():
    """Return 200 only if the database connection is alive."""
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as exc:
        log.error("Health check FAILED: %s", exc)
        return jsonify({"status": "error", "database": str(exc)}), 503

# ---------------------------------------------------------------------------
# Log 500 errors with full traceback (so Render logs show the real cause)
# ---------------------------------------------------------------------------
@app.errorhandler(500)
def internal_error(exc):
    import traceback
    log.error("500 Internal Server Error: %s\n%s", exc, traceback.format_exc())
    # Return HTML so admin/browser still get a page; real cause is in logs (e.g. Render dashboard)
    return (
        "<!DOCTYPE html><html><head><title>Error</title></head><body>"
        "<h1>Internal Server Error</h1><p>Check server logs for details.</p></body></html>"
    ), 500, {"Content-Type": "text/html; charset=utf-8"}

# ---------------------------------------------------------------------------
# Admin status: last content change — uses audit log so it matches Activity History
# ---------------------------------------------------------------------------
@app.route('/api/admin/last-change')
def api_admin_last_change():
    """Return the single most-recent content change (for the admin status bar).
    Uses AuditLog so the navbar matches Activity History."""
    try:
        latest = AuditLog.query.order_by(AuditLog.timestamp.desc()).first()
        if latest and latest.timestamp:
            return jsonify({
                'type': latest.entity_type or 'Content',
                'title': (latest.entity_title or '—')[:80],
                'when': latest.timestamp.strftime('%b %d, %Y %I:%M %p') if latest.timestamp else None,
            })
    except Exception:
        pass
    # Fallback when audit log is empty (e.g. fresh install)
    candidates = []
    try:
        a = Announcement.query.order_by(Announcement.date_entered.desc()).first()
        if a:
            candidates.append(('Announcement', a.title, a.date_entered))
        s = Sermon.query.order_by(Sermon.date.desc()).first()
        if s:
            candidates.append(('Sermon', s.title, datetime.combine(s.date, datetime.min.time()) if s.date else None))
        e = OngoingEvent.query.order_by(OngoingEvent.date_entered.desc()).first()
        if e:
            candidates.append(('Event', e.title, e.date_entered))
        g = GalleryImage.query.order_by(GalleryImage.created.desc()).first()
        if g:
            candidates.append(('Gallery', g.name or 'image', g.created))
    except Exception:
        pass
    candidates = [(t, n, d) for t, n, d in candidates if d]
    if not candidates:
        return jsonify({'type': None, 'title': None, 'when': None})
    candidates.sort(key=lambda x: x[2], reverse=True)
    typ, title, when = candidates[0]
    return jsonify({
        'type': typ,
        'title': title[:80] if title else '',
        'when': when.strftime('%b %d, %Y %I:%M %p') if when else None,
    })

# Redirect /admin to dashboard so "Admin" link lands on dashboard
@app.before_request
def redirect_admin_to_dashboard():
    if request.path in ('/admin', '/admin/'):
        return redirect('/admin/dashboard/')

# Routes
@app.route('/')
def index():
    """Homepage with highlights"""
    # Get active superfeatured announcements first, then regular ones (exclude expired)
    superfeatured = Announcement.query.filter_by(active=True, superfeatured=True)\
        .filter(_not_expired(Announcement))\
        .order_by(Announcement.date_entered.desc()).limit(3).all()
    regular = Announcement.query.filter_by(active=True, superfeatured=False)\
        .filter(_not_expired(Announcement))\
        .order_by(Announcement.date_entered.desc()).limit(7).all()
    
    highlights = superfeatured + regular
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('index.html', highlights=highlights, site_content=site_content)

@app.route('/about')
def about():
    # Load editable content from the DB; fall back gracefully if row doesn't exist
    rows = SiteContent.query.all()
    about_content = {r.key: r.value for r in rows}
    return render_template('about.html', about_content=about_content)

SUBPAGE_CONFIGS = {
    'about': {
        'title': 'About Page',
        'url': '/about',
        'icon': 'fas fa-file-alt',
        'color': '#7c3aed',
        'keys': [
            ('hero_description', 'Hero Description', 'We are a community of believers in New Haven, Connecticut, committed to growing in the truth and grace of Jesus Christ, acting as faithful witnesses in our community and world, and trusting in the grace and power of the Holy Spirit.'),
            ('mission_text', 'Our Mission (paragraph)', 'We are a church that is ambitious for the glory of God by <span class="highlight-word">GROWING</span> in the truth and grace of Jesus Christ, <span class="highlight-word">ACTING</span> as a faithful witness in the greater New Haven community and world, <span class="highlight-word">TRUSTING</span> in the grace and power of the Holy Spirit.'),
            ('total_christ_text', 'Total Christ (paragraph)', 'We want this to be all about Christ—his work, not ours, as the basis of our relationship to God and one another, and his glory, not ours or any popular leader, as the object of our ultimate affection and respect. It is our desire to experience total Christ, not just one or another brand of Christ.'),
            ('augustine_quote', 'Augustine Quote', '"The Word was made flesh, and dwelled among us; to that flesh is joined the church, and there is made total Christ, both head and body."'),
            ('staff_json', 'Staff Members (JSON)', '[{"initials":"CL","name":"Craig Luekens","title":"Senior Pastor"},{"initials":"JO","name":"Jerry Ornelas","title":"Assistant Pastor"},{"initials":"AV","name":"Alexis Vano","title":"Administrative Coordinator"},{"initials":"AG","name":"Alex Gonzalez","title":"AV Director"},{"initials":"CB","name":"Christopher Battista","title":"Audio and IT Specialist"},{"initials":"PW","name":"Paul Wildey","title":"Sexton"},{"initials":"JC","name":"Jennifer Cheng","title":"Music Coordinator"}]'),
            ('story_milestones_json', 'Story Milestones (JSON)', '[{"year":"1991","title":"The Beginning","text":"It all began in the summer of 1991 when three young families and a graduate student at Yale scheduled a ferry ride from Bridgeport, CT to Port Jefferson, NY."},{"year":"1991-1992","title":"The Vision Takes Shape","text":"Recent Gordon Conwell Seminary graduate Preston Graham was scheduled to visit New Haven to locate housing for his family while studying American Religious History at Yale."},{"year":"1992","title":"First Worship Service","text":"On October 11, 1992 at 9:30 am, the mission stage of church planting was initiated with a first worship service held at the Amity Regional Junior High in Orange, CT."},{"year":"2017","title":"Mission Anabaino","text":"As of the Spring of 2017, Mission Anabaino is inspiring a multiplying momentum for both an engagement in theological collaboration in missional ecclesiology and church planting."}]'),
        ]
    },
    'bulletin': {
        'title': 'Weekly Bulletin',
        'url': '/sundays',
        'icon': 'fas fa-newspaper',
        'color': '#d97706',
        'keys': [
            ('bulletin_title', 'Bulletin Heading', 'This Week at CPC'),
            ('bulletin_date', 'Bulletin Date (e.g. March 19, 2026)', ''),
            ('bulletin_text', 'Bulletin Content', ''),
        ]
    },
    'service_times': {
        'title': 'Service Times',
        'url': '/sundays',
        'icon': 'fas fa-clock',
        'color': '#0071e3',
        'keys': [
            ('service_prayer_time', 'Prayer Time', '8:30am'),
            ('service_school_time', 'Sunday School Time', '9:30am'),
            ('service_worship_time', 'Worship Service Time', '10:30am'),
            ('service_fellowship_time', 'Fellowship Lunch Time', '12:00pm'),
        ]
    },
    'contact': {
        'title': 'Contact Info',
        'url': '/contact',
        'icon': 'fas fa-address-card',
        'color': '#059669',
        'keys': [
            ('contact_address', 'Address', '135 Whitney Ave, New Haven, CT 06510'),
            ('contact_phone', 'Phone', '(203) 555-0123'),
            ('contact_email', 'General Email', 'admin@cpcnewhaven.org'),
        ]
    },
    'church-directory': {
        'title': 'Church Directory Page',
        'url': '/church-directory',
        'icon': 'fas fa-users',
        'color': '#00a0a0',
        'keys': [
            ('community_hero_subtitle', 'Hero Subtitle', 'Join our vibrant community of believers and seekers'),
            ('community_groups_intro', 'Groups Section Intro', 'Connect with others through our various community groups and ministries.'),
            ('community_groups_json', 'Community Groups Cards (JSON)', '[{"icon":"fas fa-users","title":"Small Groups","text":"Join a small group for Bible study, prayer, and fellowship in a more intimate setting.","bullets":["Westville Group - Thursdays at 7:00pm","Orange Group - Wednesdays at 7:00pm","Guilford Group - Fridays at 7:00pm"]},{"icon":"fas fa-child","title":"Children\'s Ministry","text":"Nurturing the faith of our youngest members through age-appropriate programs.","bullets":["Sunday School (ages 3-12)","Children\'s Church during worship","Vacation Bible School","Special events and activities"]},{"icon":"fas fa-graduation-cap","title":"Youth Ministry","text":"Engaging middle and high school students in their faith journey.","bullets":["Youth Group - Fridays at 7:00pm","Summer mission trips","Retreats and conferences","Service projects"]},{"icon":"fas fa-male","title":"Men\'s Ministry","text":"Building strong Christian men through fellowship and study.","bullets":["Men\'s Fellowship - Saturdays at 8:00am","Men\'s Bible Study","Service projects","Annual retreat"]},{"icon":"fas fa-female","title":"Women\'s Ministry","text":"Encouraging women in their walk with Christ and relationships with each other.","bullets":["Women\'s Bible Study","Women\'s Retreat","Mentoring program","Service opportunities"]},{"icon":"fas fa-music","title":"Music Ministry","text":"Using musical gifts to glorify God and lead in worship.","bullets":["Choir participation","Instrumental ensembles","Special music opportunities","Music education programs"]}]'),
            ('community_service_intro', 'Service Section Intro', 'Get involved in serving our church and community.'),
            ('community_service_json', 'Service Opportunities (JSON)', '[{"title":"Welcome Team","text":"Help welcome visitors and new members to our church family.","tag":"Hospitality"},{"title":"Children\'s Ministry","text":"Teach, assist, or help with children\'s programs and activities.","tag":"Teaching"},{"title":"Audio/Visual","text":"Support our worship services with technical assistance.","tag":"Technical"},{"title":"Facilities","text":"Help maintain and improve our church building and grounds.","tag":"Maintenance"},{"title":"Community Outreach","text":"Participate in local service projects and community events.","tag":"Outreach"},{"title":"Prayer Ministry","text":"Join our prayer team and intercede for our church and community.","tag":"Prayer"}]'),
            ('community_new_member_getting_connected', 'New Member: Getting Connected (text)', 'We\'re excited that you\'re interested in joining our community! Here\'s how you can get started:'),
            ('community_new_member_steps_json', 'New Member Steps (JSON)', '[{"bold":"Visit us on Sunday","text":"Join us for worship at 10:30am"},{"bold":"Stay for fellowship","text":"Meet people at our fellowship lunch after service"},{"bold":"Join a small group","text":"Connect with others in a more intimate setting"},{"bold":"Get involved","text":"Find a service opportunity that matches your gifts"},{"bold":"Consider membership","text":"Learn about becoming a member of CPC"}]'),
            ('community_new_member_questions', 'New Member: Questions? (text)', 'If you have questions about getting involved or becoming a member, we\'d love to help!'),
            ('community_stories_json', 'Community Stories (JSON)', '[{"title":"Finding Family at CPC","text":"When I moved to New Haven for graduate school, I was looking for a church that would feel like home. CPC welcomed me with open arms and helped me find my place in the community.","author":"Sarah, Graduate Student"},{"title":"Growing in Faith Together","text":"Through our small group, I\'ve been able to grow deeper in my faith while building meaningful relationships with other believers. It\'s been a blessing to journey together.","author":"Michael, Small Group Member"},{"title":"Serving Our Community","text":"I love how CPC encourages us to serve not just within the church, but in our broader community. It\'s been amazing to see God at work through our outreach efforts.","author":"Jennifer, Community Outreach Volunteer"}]'),
        ]
    },
    'lifegroups': {
        'title': 'LifeGroups Page',
        'url': '/lifegroups',
        'icon': 'fas fa-circle-nodes',
        'color': '#2563eb',
        'keys': [
            ('lifegroups_tagline', 'Hero Tagline', 'Church in the Small — Prayer, Teaching, Fellowship & Care'),
            ('lifegroups_vision_heading', 'Vision Section Heading', 'Our Vision for LifeGroups'),
            ('lifegroups_vision_p1', 'Vision Paragraph 1', '<strong>God\'s people are the hands and feet of Christ.</strong> We cannot experience God and grow spiritually in a truly gospel-centered and biblical way if we are living in isolation. Neither can we say we are flourishing if our brother or sister in Christ is suffering.'),
            ('lifegroups_vision_p2', 'Vision Paragraph 2', 'Bound together with covenant communion, God brings us into new relationships where sacrifice is freedom and giving to others is where we find life. <strong>LifeGroups are our way of doing church in the small</strong> with all sorts of people engaged in prayer, teaching, fellowship and care.'),
            ('lifegroups_vision_p3', 'Vision Paragraph 3', 'They are the vehicle that we use to help participants continue to experience Christ outside of our worship gatherings and to impart the pastoral care that Christ provides through the love of His people. Thus, the worship, teaching, fellowship, and care for one another supply a more intimate and hands-on encounter with the living Christ.'),
            ('lifegroups_groups_heading', 'Groups Section Heading', 'Current LifeGroups'),
            ('lifegroups_groups_intro', 'Groups Section Intro', 'Join a LifeGroup near you. All groups meet regularly for Bible study, prayer, and fellowship. Whether you\'re new to faith or have been walking with Jesus for years, there\'s a place for you.'),
            ('lifegroups_cta_heading', 'CTA Heading', 'Ready to Join?'),
            ('lifegroups_cta_text', 'CTA Body Text', 'Whether you\'re looking to deepen your faith, build genuine community, or experience Christ in a more intimate setting, there\'s a LifeGroup for you. Don\'t hesitate to reach out—our leaders are excited to welcome you.'),
            ('lifegroups_cta_email', 'CTA Email Address', 'admin@cpcnewhaven.org'),
            ('lifegroups_cta_phone', 'CTA Phone Number', '203-777-6960'),
            ('lifegroups_cta_phone_tel', 'CTA Phone (tel: link, digits only)', '+12037776960'),
        ]
    },
    'pastors_book': {
        'title': "Pastor's Book Pick",
        'url': '/pastors-book',
        'icon': 'fas fa-book-open',
        'color': '#007aff',
        'keys': [
            ('pastors_book_active', 'Show Book Pick (True/False)', 'True'),
            ('pastors_book_label', 'Label', "Pastor's Book Pick"),
            ('pastors_book_title', 'Book Title', 'Life Together'),
            ('pastors_book_author', 'Author', 'Dietrich Bonhoeffer'),
            ('pastors_book_description', 'Recommendation Text', "A modern classic, we're treading into deep waters with this one! Written by pastor-theologian and martyr, Life Together is Bonhoeffer's vision for the Christian life, both individually and communally. Copies in the foyer — suggested donation of $15."),
            ('pastors_book_image_url', 'Book Cover URL', 'https://m.media-amazon.com/images/I/41VLz4wzqrL._SY445_SX342_FMwebp_.jpg'),
            ('pastors_book_cta_text', 'CTA Text', 'Suggested donation of $15'),
            ('pastors_book_cta_link', 'External Purchase Link (optional)', ''),
        ]
    }
}

@app.route('/admin/subpage-edit/', methods=['GET', 'POST'])
def admin_subpage_edit():
    """Unified admin page to edit various subpage contents."""
    if not is_authenticated():
        return redirect(url_for('admin_login'))

    # Load active page
    active_page = request.args.get('page', 'about')
    if active_page not in SUBPAGE_CONFIGS:
        active_page = 'about'

    config = SUBPAGE_CONFIGS[active_page]
    saved = False

    if request.method == 'POST':
        for key, _label, _default in config['keys']:
            val = request.form.get(key, '')
            row = SiteContent.query.filter_by(key=key).first()
            if row:
                row.value = val
                row.updated_at = datetime.utcnow()
            else:
                db.session.add(SiteContent(key=key, value=val))
        db.session.commit()
        try:
            _log_audit('edited', SiteContent(key=config['title']), config['title'])
        except:
            pass
        flash(f"{config['title']} content saved successfully!", 'success')
        saved = True

    # Load current values
    rows = {r.key: r.value for r in SiteContent.query.all()}
    fields = []
    for key, label, default in config['keys']:
        fields.append({
            'key': key,
            'label': label,
            'value': rows.get(key, default) or default,
            'is_json': key.endswith('_json'),
        })

    return render_template('admin/subpage_edit.html',
                           fields=fields,
                           saved=saved,
                           active_page=active_page,
                           subpages=SUBPAGE_CONFIGS,
                           config=config)

@app.route('/about/what-we-believe')
def what_we_believe():
    return render_template('what_we_believe.html')

@app.route('/sermons')
def sermons():
    return render_template('sermons.html')

@app.route('/podcasts')
def podcasts():
    series = PodcastSeries.query.all()
    return render_template('podcasts.html', series=series)

@app.route('/events')
def events():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('events.html', site_content=site_content)

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/highlights')
def highlights():
    return render_template('highlights.html')

@app.route('/announcement/<int:announcement_id>')
def announcement_detail(announcement_id):
    """Detail page for a single announcement or event highlight."""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    # If it's not active or expired (and user isn't admin), maybe we shouldn't show it?
    # For now, let's just show it if it exists.
    
    return render_template('announcement_detail.html', announcement=announcement)

@app.route('/church-directory')
def church_directory():
    # Load editable content from the DB; fall back gracefully if row doesn't exist
    rows = SiteContent.query.all()
    community_content = {r.key: r.value for r in rows}
    return render_template('community.html', community_content=community_content)

@app.route('/lifegroups')
def lifegroups():
    groups = LifeGroup.query.filter_by(active=True).order_by(LifeGroup.sort_order).all()
    rows = SiteContent.query.all()
    lifegroup_content = {r.key: r.value for r in rows}
    return render_template('lifegroups.html', groups=groups, lifegroup_content=lifegroup_content)

@app.route('/sundays')
def sundays():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('sundays.html', site_content=site_content)

@app.route('/plan-a-visit')
def plan_a_visit():
    return render_template('plan-a-visit.html')

@app.route('/give')
def give():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('give.html', site_content=site_content)

# Liquid glass demo moved to possiblyDELETE folder
# @app.route('/liquid-glass-demo')
# def liquid_glass_demo():
#     return render_template('liquid_glass_demo.html')

@app.route('/live')
def live():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('live.html', site_content=site_content)

@app.route('/resources')
def resources():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('resources.html', site_content=site_content)

@app.route('/pastors-book')
def pastors_book():
    site_content = {r.key: r.value for r in SiteContent.query.all()}
    return render_template('pastors_book.html', site_content=site_content)

@app.route('/media')
def media():
    return render_template('media.html')

@app.route('/gallery')
def gallery():
    return redirect(url_for('media', view='gallery'))

@app.route('/yearbook')
def yearbook():
    return redirect(url_for('media', view='yearbook'))


@app.route('/newsletter')
def newsletter():
    return render_template('newsletter.html')

@app.route('/mailchimp-newsletter')
def mailchimp_newsletter():
    return render_template('mailchimp_newsletter.html')

@app.route('/cpc-newsletter')
def cpc_newsletter():
    return render_template('cpc_newsletter.html')

@app.route('/data-dashboard')
def data_dashboard():
    """Comprehensive data dashboard showing all external data sources"""
    return render_template('data_dashboard.html')

@app.route('/search')
def search():
    """Unified search page"""
    return render_template('search.html')

@app.route('/archive')
def archive():
    """Site archive page showing older content"""
    return render_template('archive.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/suggest-event', methods=['GET', 'POST'])
def suggest_event():
    """Public form for suggesting community events."""
    # Public-facing type options (subset of admin choices — no internal alert types)
    public_type_choices = [
        ('event', 'One-Time Event'),
        ('ongoing', 'Ongoing / Recurring'),
        ('announcement', 'Announcement'),
        ('highlight', 'Highlight'),
    ]
    public_category_choices = [
        ('general', 'General'),
        ('worship', 'Worship'),
        ('education', 'Education'),
        ('fellowship', 'Fellowship'),
        ('missions', 'Missions'),
        ('youth', 'Youth'),
        ('children', 'Children'),
    ]

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        event_date_str = request.form.get('event_date', '').strip()
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        event_start = request.form.get('event_start_time', '').strip() or None
        event_end = request.form.get('event_end_time', '').strip() or None
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        ann_type = request.form.get('type', 'event')
        category = request.form.get('category', 'general')
        tag = request.form.get('tag', '').strip() or None

        # Validate type/category against allowed values
        allowed_types = [v for v, _ in public_type_choices]
        allowed_cats = [v for v, _ in public_category_choices]
        if ann_type not in allowed_types:
            ann_type = 'event'
        if category not in allowed_cats:
            category = 'general'

        if not title or not description:
            flash('Event name and description are required.', 'error')
            return render_template('suggest_event.html',
                                   type_choices=public_type_choices,
                                   category_choices=public_category_choices,
                                   form_data=request.form)

        # Honeypot bot protection
        if request.form.get('website'):
            return redirect(url_for('index'))

        # Embed submitter info in description so admins can see who sent it
        submitter_line = f"\n\n— Suggested by: {name} ({email})" if name else ""
        full_desc = description + submitter_line

        ann = Announcement(
            id=next_global_id(),
            title=title,
            description=full_desc,
            event_date=event_date,
            event_start_time=event_start,
            event_end_time=event_end,
            type=ann_type,
            category=category,
            tag=tag,
            speaker=name or None,   # store submitter name in speaker field so it shows in admin list
            active=False,
            archived=False,
            date_entered=datetime.utcnow(),
            revision=1,
        )
        db.session.add(ann)
        db.session.commit()

        flash('Thank you! Your event suggestion has been submitted for review.', 'success')
        return redirect(url_for('suggest_event'))

    return render_template('suggest_event.html',
                           type_choices=public_type_choices,
                           category_choices=public_category_choices,
                           form_data={})

@app.route('/teaching-series')
def teaching_series():
    """Teaching series page showing sermon series and Sunday school series"""
    return render_template('teaching-series.html')


@app.route('/pastor-teaching')
def pastor_teaching():
    """Public page for pastor-led teaching series (e.g. Total Christ) with PDFs."""
    return render_template('pastor-teaching.html')


@app.route('/api/pastor-teaching-series')
def api_pastor_teaching_series():
    """List active teaching series (pastor-uploaded, with optional sessions count)."""
    series_list = TeachingSeries.query.filter_by(active=True)\
        .filter(_not_expired(TeachingSeries))\
        .order_by(TeachingSeries.sort_order.asc(), TeachingSeries.date_entered.desc()).all()
    return jsonify({
        'series': [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description or '',
                'image_url': s.image_url,
                'start_date': s.start_date.isoformat() if s.start_date else None,
                'end_date': s.end_date.isoformat() if s.end_date else None,
                'event_info': s.event_info or '',
                'session_count': len(s.sessions) if s.sessions else 0,
            }
            for s in series_list
        ]
    })


@app.route('/api/pastor-teaching-series/<int:series_id>')
def api_pastor_teaching_series_detail(series_id):
    """One teaching series with sessions in order (1, 2, 3...) and PDF links."""
    s = TeachingSeries.query.filter_by(id=series_id, active=True)\
        .filter(_not_expired(TeachingSeries)).first()
    if not s:
        return jsonify({'error': 'Not found'}), 404
    sessions = sorted(s.sessions, key=lambda x: x.number or 999) if s.sessions else []
    return jsonify({
        'id': s.id,
        'title': s.title,
        'description': s.description or '',
        'image_url': s.image_url,
        'start_date': s.start_date.isoformat() if s.start_date else None,
        'end_date': s.end_date.isoformat() if s.end_date else None,
        'event_info': s.event_info or '',
        'sessions': [
            {
                'id': sess.id,
                'number': sess.number,
                'title': sess.title,
                'description': sess.description or '',
                'session_date': sess.session_date.isoformat() if sess.session_date else None,
                'pdf_url': sess.pdf_url,
            }
            for sess in sessions
        ]
    })


@app.route('/api/teaching-series')
def api_teaching_series():
    """API endpoint for teaching series - sermon series and Sunday school series with enhanced metadata.
    Purely database driven - all data comes from Render PostgreSQL.
    """
    try:
        from sermon_data_helper import get_sermon_helper
        helper = get_sermon_helper()
        sermons = helper.get_all_sermons() # Now comes from DB
    except Exception as e:
        log.error(f"Error getting sermons for teaching series: {e}")
        sermons = []
    
    # Extract unique sermon series (excluding "The Sunday Sermon" as it's the default)
    sermon_series_buckets = {}
    sunday_school_series_buckets = {}
    all_speakers = set()
    all_scriptures = set()
    all_tags = set()
    date_range = {'min': None, 'max': None}
    
    for sermon in sermons:
        series_name = sermon.get('series') or ''
        title = sermon.get('title') or ''
        speaker = sermon.get('speaker', '') or sermon.get('author', '')
        scripture = sermon.get('scripture', '')
        date_str = sermon.get('date', '')
        tags = sermon.get('tags', [])
        
        # Collect metadata
        if speaker:
            all_speakers.add(speaker)
        if scripture:
            all_scriptures.add(scripture)
        if tags:
            all_tags.update(tags if isinstance(tags, list) else [str(tags)])
        
        # Track date range
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_range['min'] is None or date_obj < date_range['min']:
                    date_range['min'] = date_obj
                if date_range['max'] is None or date_obj > date_range['max']:
                    date_range['max'] = date_obj
            except:
                pass
        
        sermon_data = {
            'id': sermon.get('id'),
            'title': sermon.get('title'),
            'speaker': speaker,
            'date': date_str,
            'scripture': scripture,
            'link': sermon.get('link'),
            'spotify_url': sermon.get('spotify_url'),
            'youtube_url': sermon.get('youtube_url'),
            'apple_podcasts_url': sermon.get('apple_podcasts_url'),
            'tags': tags if isinstance(tags, list) else [tags] if tags else [],
            'sermon_type': sermon.get('sermon_type', 'sermon')
        }
        
        # Determine which bucket it goes into
        is_sunday_school = 'Sunday School' in series_name or 'Sunday School' in title or 'The Sunday School' in title
        target_buckets = sunday_school_series_buckets if is_sunday_school else sermon_series_buckets
        
        if series_name and series_name != 'The Sunday Sermon':
            if series_name not in target_buckets:
                target_buckets[series_name] = {
                    'name': series_name,
                    'count': 0,
                    'sermons': [],
                    'speakers': set(),
                    'date_range': {'min': None, 'max': None},
                    'scriptures': set()
                }
            
            bucket = target_buckets[series_name]
            bucket['count'] += 1
            bucket['sermons'].append(sermon_data)
            if speaker:
                bucket['speakers'].add(speaker)
            if scripture:
                bucket['scriptures'].add(scripture)
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if bucket['date_range']['min'] is None or date_obj < bucket['date_range']['min']:
                        bucket['date_range']['min'] = date_obj
                    if bucket['date_range']['max'] is None or date_obj > bucket['date_range']['max']:
                        bucket['date_range']['max'] = date_obj
                except:
                    pass

    # Convert buckets to lists and enhance with SermonSeries metadata from DB
    def finalize_series(buckets):
        final_list = []
        # Get metadata for all series from the database
        db_series = {s.title: s for s in SermonSeries.query.all()}
        
        for name, data in buckets.items():
            ds = db_series.get(name)
            series_item = {
                'name': name,
                'count': data['count'],
                'sermons': sorted(data['sermons'], key=lambda x: x.get('date', ''), reverse=True),
                'speakers': sorted(list(data['speakers'])),
                'scriptures': sorted(list(data['scriptures']))[:10],
                'date_range': {
                    'min': data['date_range']['min'].strftime('%Y-%m-%d') if data['date_range']['min'] else None,
                    'max': data['date_range']['max'].strftime('%Y-%m-%d') if data['date_range']['max'] else None
                },
                'description': ds.description if ds else '',
                'slug': ds.slug if ds and ds.slug else '',
                'external_url': ds.external_url if ds and ds.external_url else '',
                'sort_order': ds.sort_order if ds else 999,
                'image_url': ds.image_url if ds else None
            }
            final_list.append(series_item)
            
        # Add series from DB that don't have sermons yet (e.g. curated links)
        for title, ds in db_series.items():
            if title not in buckets and ds.active:
                 final_list.append({
                    'name': title,
                    'count': 0,
                    'sermons': [],
                    'speakers': [],
                    'scriptures': [],
                    'date_range': {'min': None, 'max': None},
                    'description': ds.description or '',
                    'slug': ds.slug or '',
                    'external_url': ds.external_url or '',
                    'sort_order': ds.sort_order or 999,
                    'image_url': ds.image_url
                })
        
        return sorted(final_list, key=lambda x: (x['sort_order'], x['name']))

    sermon_series_list = finalize_series(sermon_series_buckets)
    sunday_school_series_list = finalize_series(sunday_school_series_buckets)
    
    date_range_response = {
        'min': date_range['min'].strftime('%Y-%m-%d') if date_range['min'] else None,
        'max': date_range['max'].strftime('%Y-%m-%d') if date_range['max'] else None
    }
    
    return jsonify({
        'sermon_series': sermon_series_list,
        'sunday_school_series': sunday_school_series_list,
        'metadata': {
            'total_series': len(sermon_series_list) + len(sunday_school_series_list),
            'total_sermon_series': len(sermon_series_list),
            'total_sunday_school_series': len(sunday_school_series_list),
            'all_speakers': sorted(list(all_speakers)),
            'all_scriptures': sorted(list(all_scriptures))[:50],  # Top 50 for filter
            'all_tags': sorted(list(all_tags)),
            'date_range': date_range_response
        }
    })

# API Routes
def _not_expired(model_klass):
    """SQLAlchemy filter: show only content that has no expiration or expires_at > today."""
    from sqlalchemy import text
    col = getattr(model_klass, 'expires_at', None)
    if col is None:
        return text('1 = 1')  # no expires_at column
    return db.or_(col.is_(None), col > date.today())


@app.route('/api/announcements')
@cache.cached(timeout=60)
def api_announcements():
    """API endpoint matching your highlights.json structure"""
    announcements = Announcement.query.filter_by(active=True)\
        .filter(_not_expired(Announcement))\
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
                'showInBanner': getattr(a, 'show_in_banner', False),
                'featuredImage': a.featured_image,
                'imageDisplayType': a.image_display_type,
                'eventStartTime': getattr(a, 'event_start_time', None),
                'eventEndTime': getattr(a, 'event_end_time', None),
            } for a in announcements
        ]
    })


@app.route('/api/banner-announcements')
@cache.cached(timeout=60)
def api_banner_announcements():
    """Active announcements marked to show in the top yellow bar (weather, parking, etc.)"""
    announcements = Announcement.query.filter_by(active=True, show_in_banner=True)\
        .filter(_not_expired(Announcement))\
        .order_by(Announcement.banner_sort_order.asc(), Announcement.date_entered.desc()).all()
    return jsonify({
        'announcements': [
            {
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'type': a.type or 'announcement',
                'eventStartTime': getattr(a, 'event_start_time', None),
                'eventEndTime': getattr(a, 'event_end_time', None),
            } for a in announcements
        ]
    })

@app.route('/api/highlights')
@cache.cached(timeout=60)
def api_highlights():
    """API endpoint for highlights data - pulls from database"""
    # Get all announcements from database (not just active ones, for filtering on highlights page)
    # Limit to last 50 to avoid loading thousands of announcements
    announcements = Announcement.query.filter(_not_expired(Announcement))\
        .order_by(Announcement.date_entered.desc()).limit(50).all()
    
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
                'featuredImage': a.featured_image,
                'imageDisplayType': a.image_display_type,
                'eventStartTime': getattr(a, 'event_start_time', None),
                'eventEndTime': getattr(a, 'event_end_time', None),
            } for a in announcements
        ]
    })

@app.route('/api/ongoing-events')
@cache.cached(timeout=60)
def api_ongoing_events():
    """API endpoint for ongoing events (ordered by sort_order, then date)"""
    events = OngoingEvent.query.filter_by(active=True)\
        .filter(_not_expired(OngoingEvent))\
        .order_by(OngoingEvent.sort_order.asc(), OngoingEvent.date_entered.desc()).all()
    
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

@app.route('/api/papers/latest')
@cache.cached(timeout=120)
def api_papers_latest():
    """Latest paper (e.g. bulletin) for homepage. Prefer category 'bulletin'."""
    bulletin = Paper.query.filter_by(active=True).filter(
        Paper.category.in_(['bulletin', 'Bulletin'])
    ).order_by(Paper.date_entered.desc()).first()
    if bulletin:
        return jsonify({
            'id': bulletin.id,
            'title': bulletin.title,
            'speaker': bulletin.speaker,
            'file_url': bulletin.file_url,
            'date_published': bulletin.date_published.isoformat() if bulletin.date_published else None,
            'date_entered': bulletin.date_entered.strftime('%Y-%m-%d') if bulletin.date_entered else None,
        })
    # Fallback: any latest paper
    latest = Paper.query.filter_by(active=True).order_by(Paper.date_entered.desc()).first()
    if latest:
        return jsonify({
            'id': latest.id,
            'title': latest.title,
            'speaker': latest.speaker,
            'file_url': latest.file_url,
            'date_published': latest.date_published.isoformat() if latest.date_published else None,
            'date_entered': latest.date_entered.strftime('%Y-%m-%d') if latest.date_entered else None,
        })
    return jsonify({})

@app.route('/api/sermons')
@cache.cached(timeout=120)
def api_sermons():
    """Sunday Sermons API: Sourced from database only."""
    episodes = []
    try:
        db_sermons = Sermon.query.filter(
            Sermon.active == True,
            Sermon.archived == False,
        ).filter(_not_expired(Sermon)).order_by(Sermon.date.desc()).all()
        for s in db_sermons:
            sermon_data = {
                'id': s.id,
                'title': s.title or '',
                'speaker': (s.speaker_user.username if s.speaker_user else s.speaker) or '',
                'scripture': s.scripture or '',
                'date': s.date.strftime('%Y-%m-%d') if s.date else '',
                'spotify_url': s.spotify_url or '',
                'youtube_url': s.youtube_url or '',
                'apple_podcasts_url': s.apple_podcasts_url or '',
                'link': s.spotify_url or s.youtube_url or s.apple_podcasts_url or '',
                'podcast-thumbnail_url': s.podcast_thumbnail_url or '',
                'episode': s.episode_number,
                'audio_file': s.audio_file_url,
                'video_file': s.video_file_url,
            }
            if s.series:
                sermon_data['series'] = {
                    'id': s.series.id,
                    'title': s.series.title,
                    'image_url': s.series.image_url
                }
            if s.beyond_episode:
                sermon_data['beyond_link'] = s.beyond_episode.link or s.beyond_episode.listen_url
            
            episodes.append(sermon_data)
    except Exception as e:
        print(f"Error loading DB sermons: {e}")
        
    return jsonify({
        'title': 'Sunday Sermons',
        'description': 'Weekly sermons from our Sunday worship services',
        'episodes': episodes,
        'total': len(episodes),
        'source': 'database'
    })

def _get_podcast_episodes(series_title):
    """Helper to fetch podcast episodes from DB by series title."""
    series = PodcastSeries.query.filter(PodcastSeries.title.ilike(f'%{series_title}%')).first()
    if not series:
        return []
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id)\
        .order_by(PodcastEpisode.date_added.desc()).all()
    
    return [
        {
            'number': ep.number,
            'title': ep.title,
            'link': ep.link,
            'listen_url': ep.listen_url,
            'guest': ep.guest,
            'date_added': ep.date_added.strftime('%Y-%m-%d') if ep.date_added else None,
            'season': ep.season,
            'scripture': ep.scripture,
            'podcast_thumbnail_url': ep.podcast_thumbnail_url
        } for ep in episodes
    ]

@app.route('/api/podcasts/beyond-podcast')
def api_beyond_podcast():
    """API endpoint for Beyond the Sunday Sermon podcast sourced from database."""
    episodes = _get_podcast_episodes('Beyond the Sunday Sermon')
    return jsonify({
        'title': 'Beyond the Sunday Sermon',
        'description': 'Extended conversations and deeper dives into biblical topics.',
        'episodes': episodes
    })

@app.route('/api/podcasts/biblical-interpretation')
def api_biblical_interpretation():
    """API endpoint for Biblical Interpretation series sourced from database."""
    episodes = _get_podcast_episodes('Biblical Interpretation')
    return jsonify({
        'title': 'Biblical Interpretation',
        'description': 'Teaching series on how to read and understand Scripture.',
        'episodes': episodes
    })

@app.route('/api/podcasts/confessional-theology')
def api_confessional_theology():
    """API endpoint for Confessional Theology series sourced from database."""
    episodes = _get_podcast_episodes('Confessional Theology')
    return jsonify({
        'title': 'Confessional Theology',
        'description': 'Exploring Reformed theology and doctrine.',
        'episodes': episodes
    })

@app.route('/api/podcasts/membership-seminar')
def api_membership_seminar():
    """API endpoint for Membership Seminar series sourced from database."""
    episodes = _get_podcast_episodes('Membership Seminar')
    return jsonify({
        'title': 'Membership Seminar',
        'description': 'Understanding church membership and the Christian life.',
        'episodes': episodes
    })

@app.route('/api/gallery')
@cache.cached(timeout=300)
def api_gallery():
    """API endpoint for image gallery sourced from database"""
    try:
        images = GalleryImage.query.filter(_not_expired(GalleryImage))\
            .order_by(GalleryImage.created.desc()).all()
        
        return jsonify({
            'images': [
                {
                    'id': img.id,
                    'name': img.name or 'Untitled',
                    'url': img.url,
                    'size': img.size or 'Unknown',
                    'type': img.type or 'image/jpeg',
                    'created': img.created.strftime('%Y-%m-%d') if img.created else None,
                    'created_timestamp': img.created.isoformat() if img.created else None,
                    'tags': img.tags if isinstance(img.tags, list) else [],
                    'event': img.event,
                    'description': img.description or '',
                    'location': img.location or '',
                    'photographer': img.photographer or ''
                } for img in images
            ],
            'total': len(images),
            'source': 'database'
        })
    except Exception as e:
        print(f"Error loading gallery: {e}")
        return jsonify({'images': [], 'total': 0, 'error': str(e)})

def _fetch_podcast(feed_url: str) -> dict:
    r = requests.get(
        feed_url,
        timeout=10,
        headers={"User-Agent": "CPC-Web-App (+https://cpcnewhaven.org)"}
    )
    r.raise_for_status()
    parsed = feedparser.parse(r.content)

    channel = {
        "title": parsed.feed.get("title"),
        "link": parsed.feed.get("link"),
        "description": parsed.feed.get("subtitle") or parsed.feed.get("description"),
        "image": getattr(parsed.feed, "image", {}).get("href")
                 or parsed.feed.get("itunes_image", {}).get("href"),
    }

    episodes = []
    for e in parsed.entries[:50]:
        audio = None
        for enc in e.get("enclosures", []):
            if (enc.get("type") or "").startswith("audio"):
                audio = {"url": enc.get("href"), "type": enc.get("type")}
                break
        episodes.append({
            "title": e.get("title"),
            "link": e.get("link"),
            "published": e.get("published"),
            "summary": e.get("summary"),
            "audio": audio,
            "duration": e.get("itunes_duration"),
            "image": (e.get("itunes_image", {}) or {}).get("href"),
            "guid": e.get("id") or e.get("guid")
        })
    return {"channel": channel, "episodes": episodes}

@app.route("/api/podcast/<series_key>")
@cache.cached(timeout=900)
def api_podcast(series_key):
    feed_url = app.config["PODCAST_FEEDS"].get(series_key)
    if not feed_url:
        return {"error": f"Unknown podcast key: {series_key}"}, 404
    try:
        data = _fetch_podcast(feed_url)
        return data, 200
    except requests.RequestException as ex:
        return {"error": "Failed to fetch RSS", "details": str(ex)}, 502

@app.route("/api/newsletter")
@cache.cached(timeout=900)  # 15 min cache
def api_newsletter():
    """Fetch latest newsletter content from RSS feed"""
    url = app.config.get("NEWSLETTER_FEED_URL")
    if not url or url == "<PASTE_YOUR_NEWSLETTER_RSS_URL>":
        return {"error": "NEWSLETTER_FEED_URL not configured"}, 500
    
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "CPC-Web-App"})
        r.raise_for_status()
        parsed = feedparser.parse(r.content)

        items = []
        for e in parsed.entries[:20]:
            # Extract image from media_thumbnail or other sources
            image = None
            if e.get("media_thumbnail"):
                image = e.get("media_thumbnail", [{}])[0].get("url")
            elif e.get("enclosures"):
                for enc in e.get("enclosures", []):
                    if enc.get("type", "").startswith("image"):
                        image = enc.get("href")
                        break
            
            items.append({
                "title": e.get("title"),
                "url": e.get("link"),
                "published": e.get("published"),
                "summary": e.get("summary"),
                "image": image
            })
        
        return {
            "source": parsed.feed.get("title", "Newsletter"),
            "items": items
        }
    except requests.RequestException as ex:
        return {"error": "Failed to fetch newsletter", "details": str(ex)}, 502

@app.route("/api/events")
@cache.cached(timeout=900)
def api_events():
    """Fetch events from Google Calendar ICS feed with enhanced categorization"""
    try:
        data = _fetch_events_json()
        return jsonify(data), 200
    except Exception as ex:
        return jsonify({"error": "failed to load events", "details": str(ex)}), 502

@app.route("/api/youtube")
@cache.cached(timeout=900)
def api_youtube():
    """Fetch latest YouTube videos from channel RSS"""
    channel_id = app.config.get("YOUTUBE_CHANNEL_ID")
    if not channel_id or channel_id == "<PASTE_YOUR_YOUTUBE_CHANNEL_ID>":
        return {"error": "YOUTUBE_CHANNEL_ID not configured"}, 500
    
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(feed_url, timeout=10, headers={"User-Agent": "CPC-Web-App"})
        r.raise_for_status()
        parsed = feedparser.parse(r.content)

        videos = []
        for e in parsed.entries[:20]:
            # Extract video ID from link
            video_id = None
            if e.get("link"):
                import re
                match = re.search(r'v=([^&]+)', e.get("link", ""))
                if match:
                    video_id = match.group(1)
            
            videos.append({
                "title": e.get("title"),
                "url": e.get("link"),
                "published": e.get("published"),
                "description": e.get("summary"),
                "video_id": video_id,
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None
            })
        
        return {
            "channel": parsed.feed.get("title", "YouTube Channel"),
            "videos": videos
        }
    except requests.RequestException as ex:
        return {"error": "Failed to fetch YouTube videos", "details": str(ex)}, 502

@app.route("/api/bible-verse")
@cache.cached(timeout=3600)  # 1 hour cache
def api_bible_verse():
    """Fetch verse of the day from Bible API"""
    api_key = app.config.get("BIBLE_API_KEY")
    if not api_key or api_key == "<PASTE_YOUR_BIBLE_API_KEY>":
        return {"error": "BIBLE_API_KEY not configured"}, 500
    
    try:
        # Using Bible API (bible-api.com) - free, no key required
        r = requests.get("https://bible-api.com/john+3:16", timeout=10)
        r.raise_for_status()
        data = r.json()
        
        return {
            "reference": data.get("reference"),
            "text": data.get("text"),
            "translation": data.get("translation_name", "KJV")
        }
    except Exception as ex:
        return {"error": "Failed to fetch Bible verse", "details": str(ex)}, 502

@app.route("/api/mailchimp")
@cache.cached(timeout=900)
def api_mailchimp():
    """Fetch Mailchimp newsletter content"""
    from ingest.mailchimp import MailchimpIngester
    ingester = MailchimpIngester(cache)
    data = ingester.fetch_data(app.config)
    return ingester.normalize_data(data)

@app.route("/webhooks/mailchimp", methods=["POST"])
def mailchimp_webhook():
    """Handle Mailchimp webhook for campaign sent events"""
    try:
        # Parse webhook payload
        payload = request.form or request.json or {}
        campaign_id = payload.get("data[id]") or payload.get("data", {}).get("id")
        
        if not campaign_id:
            return {"error": "Missing campaign ID"}, 400
        
        # Get campaign content and cache it
        api_key = app.config.get("MAILCHIMP_API_KEY")
        server_prefix = app.config.get("MAILCHIMP_SERVER_PREFIX")
        
        if not api_key or not server_prefix:
            return {"error": "Mailchimp API not configured"}, 500
        
        # Fetch campaign content
        content_url = f"https://{server_prefix}.api.mailchimp.com/3.0/campaigns/{campaign_id}/content"
        response = requests.get(
            content_url, 
            auth=("anystring", api_key), 
            timeout=10,
            headers={"User-Agent": "CPC-Web-App"}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch campaign: {response.text}"}, 502
        
        campaign_data = response.json()
        
        # Process and cache the content
        from ingest.mailchimp import MailchimpIngester
        ingester = MailchimpIngester(cache)
        processed_data = {
            "title": campaign_data.get("settings", {}).get("subject_line", "Newsletter"),
            "html_content": campaign_data.get("html", ""),
            "text_content": campaign_data.get("plain_text", ""),
            "campaign_id": campaign_id,
            "webhook_received": datetime.utcnow().isoformat()
        }
        
        # Cache the latest newsletter
        cache.set("latest_mailchimp_newsletter", processed_data, timeout=60*60*24*7)  # 7 days
        
        return {"status": "success", "campaign_id": campaign_id}, 200
        
    except Exception as e:
        return {"error": f"Webhook processing failed: {str(e)}"}, 500

@app.route("/api/mailchimp/latest")
def mailchimp_latest():
    """Get the latest newsletter from webhook cache"""
    latest = cache.get("latest_mailchimp_newsletter")
    if not latest:
        return {"error": "No newsletter available"}, 404
    
    return latest

@app.route("/api/cpc-newsletter-sample")
def cpc_newsletter_sample():
    """Get sample CPC newsletter data for testing"""
    try:
        import json
        with open('data/cpc_newsletter_sample.json', 'r') as f:
            sample_data = json.load(f)
        return sample_data
    except Exception as e:
        return {"error": f"Failed to load sample data: {str(e)}"}, 500

# ---------- Events ingest & normalization ----------
def _categorize(title, description, rules):
    text = f"{title} {description}".lower()
    for cat, keywords in rules.items():
        for k in keywords:
            if k in text:
                return cat
    return "General"

def _normalize_events(ics_text, site_tz, rules):
    cal = Calendar(ics_text)
    local = pytz.timezone(site_tz)
    items = []
    for ev in cal.events:
        # Handle all-day vs timed
        all_day = (ev.all_day is True) or (ev.begin and ev.begin.time() == datetime.min.time() and ev.duration and ev.duration.days >= 1)
        # Normalize datetimes
        start = ev.begin.datetime if ev.begin else None
        end   = ev.end.datetime if ev.end else None
        if start and start.tzinfo is None:
            start = pytz.utc.localize(start)
        if end and end.tzinfo is None:
            end = pytz.utc.localize(end)
        if start:
            start = start.astimezone(local)
        if end:
            end = end.astimezone(local)
        # Stable id
        eid = (getattr(ev, "uid", None) or f"{ev.name}-{start}").replace(" ", "_")
        items.append({
            "id": eid,
            "title": ev.name or "Untitled Event",
            "start": start.isoformat() if start else None,
            "end":   end.isoformat() if end else None,
            "all_day": bool(all_day),
            "location": ev.location,
            "description": ev.description,
            "url": getattr(ev, "url", None),
            "category": _categorize(ev.name or "", ev.description or "", rules),
        })
    # Sort by start
    items.sort(key=lambda x: x["start"] or "")
    return items

@cache.cached(timeout=900, key_prefix="events_json")
def _fetch_events_json():
    ics_url = app.config.get("EVENTS_ICS_URL")
    if not ics_url:
        # Fallback: if a public Google Calendar is configured (or implied), build its public ICS URL.
        # This keeps the site working even if EVENTS_ICS_URL isn't explicitly set.
        try:
            site_content = {r.key: r.value for r in SiteContent.query.all()}
        except Exception:
            site_content = {}

        gcal_id = (site_content.get("google_calendar_id") or "").strip() or "baf2h147ghi7nu8ifijjrt994k@group.calendar.google.com"
        gcal_tz = (site_content.get("google_calendar_tz") or "").strip() or app.config.get("SITE_TIMEZONE", "America/New_York")

        # Public/basic ICS endpoint
        ics_url = (
            "https://calendar.google.com/calendar/ical/"
            + requests.utils.quote(gcal_id, safe="")
            + "/public/basic.ics"
        )
        # Ensure the rest of the pipeline uses the requested tz (if provided via SiteContent)
        app.config["SITE_TIMEZONE"] = gcal_tz

    r = requests.get(ics_url, timeout=10, headers={"User-Agent":"CPC-Web-App"})
    r.raise_for_status()
    items = _normalize_events(
        r.text,
        app.config.get("SITE_TIMEZONE", "America/New_York"),
        app.config.get("EVENT_CATEGORY_RULES", {})
    )
    # window filter
    lookahead = int(app.config.get("EVENTS_LOOKAHEAD_DAYS", 120))
    now = datetime.now(pytz.timezone(app.config.get("SITE_TIMEZONE", "America/New_York")))
    until = now + timedelta(days=lookahead)
    upcoming = [e for e in items if e["start"] and now.isoformat() <= e["start"] <= until.isoformat()]
    return {"events": upcoming}

@app.route("/api/events/<eid>.ics")
def api_event_ics(eid):
    # Build a single .ics download from cached list
    data = _fetch_events_json()
    ev = next((e for e in data.get("events", []) if e["id"] == eid), None)
    if not ev:
        return Response("Not found", status=404)
    cal = Calendar()
    evt = Event()
    evt.name = ev["title"]
    tzname = app.config.get("SITE_TIMEZONE", "America/New_York")
    local = pytz.timezone(tzname)
    if ev["start"]:
        evt.begin = datetime.fromisoformat(ev["start"]).astimezone(local)
    if ev["end"]:
        evt.end = datetime.fromisoformat(ev["end"]).astimezone(local)
    evt.description = ev.get("description") or ""
    evt.location = ev.get("location") or ""
    cal.events.add(evt)
    return Response(str(cal), mimetype="text/calendar",
                    headers={"Content-Disposition": f"attachment; filename={eid}.ics"})

@app.route("/api/external-data")
@cache.cached(timeout=900)
def api_external_data():
    """Comprehensive external data endpoint using ingester architecture"""
    data = {}
    
    # Initialize ingesters (lazy imports to keep startup fast)
    from ingest.newsletter import NewsletterIngester
    from ingest.events import EventsIngester
    from ingest.youtube import YouTubeIngester
    from ingest.mailchimp import MailchimpIngester
    newsletter_ingester = NewsletterIngester(cache)
    events_ingester = EventsIngester(cache)
    youtube_ingester = YouTubeIngester(cache)
    mailchimp_ingester = MailchimpIngester(cache)
    
    # Fetch newsletter data
    try:
        newsletter_data = newsletter_ingester.fetch_data(app.config)
        data["newsletter"] = newsletter_ingester.normalize_data(newsletter_data)
    except Exception as e:
        data["newsletter"] = {"error": f"Newsletter fetch failed: {str(e)}"}
    
    # Fetch Mailchimp data
    try:
        mailchimp_data = mailchimp_ingester.fetch_data(app.config)
        data["mailchimp"] = mailchimp_ingester.normalize_data(mailchimp_data)
    except Exception as e:
        data["mailchimp"] = {"error": f"Mailchimp fetch failed: {str(e)}"}
    
    # Fetch events data
    try:
        events_data = events_ingester.fetch_data(app.config)
        data["events"] = events_ingester.normalize_data(events_data)
    except Exception as e:
        data["events"] = {"error": f"Events fetch failed: {str(e)}"}
    
    # Fetch YouTube data
    try:
        youtube_data = youtube_ingester.fetch_data(app.config)
        data["youtube"] = youtube_ingester.normalize_data(youtube_data)
    except Exception as e:
        data["youtube"] = {"error": f"YouTube fetch failed: {str(e)}"}
    
    # Add metadata
    data["metadata"] = {
        "last_updated": datetime.utcnow().isoformat(),
        "sources": list(data.keys()),
        "status": "success" if all("error" not in v for v in data.values() if isinstance(v, dict)) else "partial"
    }
    
    return data

@app.route("/api/search")
def api_search():
    """Unified search endpoint that searches across all content types with optional filters"""
    from sqlalchemy import or_, and_
    from datetime import datetime

    query = request.args.get('q', '').strip().lower()
    content_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Optional filters per content type
    sermon_filters = {
        'speaker': request.args.get('speaker', '').strip(),
        'series_id': request.args.get('series_id', '').strip(),
        'year': request.args.get('year', '').strip(),
        'scripture_book': request.args.get('scripture_book', '').strip(),
    }

    podcast_filters = {
        'series_id': request.args.get('series_id', '').strip(),
        'guest': request.args.get('guest', '').strip(),
        'season': request.args.get('season', '').strip(),
    }

    event_filters = {
        'category': request.args.get('category', '').strip(),
    }

    gallery_filters = {
        'tags': request.args.get('tags', '').strip(),  # comma-separated
        'year': request.args.get('year', '').strip(),
    }

    results = {
        'query': query,
        'type': content_type,
        'results': [],
        'total': 0,
        'page': page,
        'per_page': per_page,
        'pages': 0
    }

    try:
        # Search sermons — DB only
        if content_type in ['all', 'sermons']:
            q = Sermon.query.filter(Sermon.active == True).filter(_not_expired(Sermon))

            # Text search (only on text fields, not integer speaker)
            if query:
                q = q.filter(or_(
                    Sermon.title.ilike(f'%{query}%'),
                    Sermon.scripture.ilike(f'%{query}%'),
                ))

            # Filter by speaker (match by speaker_id if numeric, otherwise skip)
            if sermon_filters['speaker']:
                try:
                    speaker_id = int(sermon_filters['speaker'])
                    q = q.filter(Sermon.speaker_id == speaker_id)
                except ValueError:
                    pass  # Skip if not a numeric ID

            # Filter by series
            if sermon_filters['series_id']:
                try:
                    series_id = int(sermon_filters['series_id'])
                    q = q.filter(Sermon.series_id == series_id)
                except ValueError:
                    pass

            # Filter by year
            if sermon_filters['year']:
                try:
                    year = int(sermon_filters['year'])
                    q = q.filter(Sermon.date >= datetime(year, 1, 1), Sermon.date < datetime(year + 1, 1, 1))
                except (ValueError, TypeError):
                    pass

            # Filter by scripture book
            if sermon_filters['scripture_book']:
                q = q.filter(Sermon.scripture.ilike(f'%{sermon_filters["scripture_book"]}%'))

            sermon_hits = q.order_by(Sermon.date.desc()).limit(100).all()

            for s in sermon_hits:
                series_title = s.series.title if s.series else ''
                results['results'].append({
                    'type': 'sermon',
                    'title': s.title,
                    'description': s.scripture or series_title,
                    'speaker': s.speaker or '',
                    'date': s.date.strftime('%Y-%m-%d') if s.date else None,
                    'series': series_title,
                    'url': s.spotify_url or s.youtube_url or s.apple_podcasts_url or '',
                    'thumbnail': s.podcast_thumbnail_url or ''
                })

        # Search announcements
        if content_type in ['all', 'announcements']:
            q = Announcement.query.filter(_not_expired(Announcement))

            if query:
                q = q.filter(db.or_(
                    Announcement.title.ilike(f'%{query}%'),
                    Announcement.description.ilike(f'%{query}%'),
                    Announcement.category.ilike(f'%{query}%'),
                    Announcement.tag.ilike(f'%{query}%')
                ))

            announcements = q.all()
            for a in announcements:
                results['results'].append({
                    'type': 'announcement',
                    'title': a.title,
                    'description': a.description[:200] if a.description else '',
                    'date': a.date_entered.strftime('%Y-%m-%d') if a.date_entered else None,
                    'category': a.category,
                    'tag': a.tag,
                    'url': url_for('announcements'),
                    'eventStartTime': getattr(a, 'event_start_time', None),
                    'eventEndTime': getattr(a, 'event_end_time', None),
                })

        # Search podcasts
        if content_type in ['all', 'podcasts']:
            q = PodcastEpisode.query.filter(_not_expired(PodcastEpisode))

            # Text search
            if query:
                conditions = [PodcastEpisode.title.ilike(f'%{query}%')]
                try:
                    conditions.append(or_(
                        PodcastEpisode.guest.ilike(f'%{query}%'),
                        PodcastEpisode.scripture.ilike(f'%{query}%')
                    ))
                except:
                    pass
                q = q.filter(or_(*conditions))

            # Filter by series
            if podcast_filters['series_id']:
                try:
                    series_id = int(podcast_filters['series_id'])
                    q = q.filter(PodcastEpisode.series_id == series_id)
                except ValueError:
                    pass

            # Filter by guest
            if podcast_filters['guest']:
                try:
                    q = q.filter(PodcastEpisode.guest.ilike(f'%{podcast_filters["guest"]}%'))
                except:
                    pass

            # Filter by season
            if podcast_filters['season']:
                try:
                    season = int(podcast_filters['season'])
                    q = q.filter(PodcastEpisode.season == season)
                except (ValueError, AttributeError):
                    pass

            episodes = q.all()
            for ep in episodes:
                results['results'].append({
                    'type': 'podcast',
                    'title': ep.title,
                    'description': getattr(ep, 'scripture', None) or '',
                    'guest': getattr(ep, 'guest', None),
                    'date': ep.date_added.strftime('%Y-%m-%d') if ep.date_added else None,
                    'url': ep.link or getattr(ep, 'listen_url', None)
                })

        # Search events
        if content_type in ['all', 'events']:
            q = OngoingEvent.query.filter(_not_expired(OngoingEvent))

            # Text search
            if query:
                q = q.filter(db.or_(
                    OngoingEvent.title.ilike(f'%{query}%'),
                    OngoingEvent.description.ilike(f'%{query}%')
                ))

            # Filter by category
            if event_filters['category']:
                q = q.filter(OngoingEvent.category.ilike(f'%{event_filters["category"]}%'))

            events = q.all()
            for e in events:
                results['results'].append({
                    'type': 'event',
                    'title': e.title,
                    'description': e.description[:200] if e.description else '',
                    'date': e.date_entered.strftime('%Y-%m-%d') if e.date_entered else None,
                    'category': e.category,
                    'url': url_for('events')
                })

        # Search gallery
        if content_type in ['all', 'gallery']:
            q = GalleryImage.query.filter(_not_expired(GalleryImage))

            # Text search by name
            if query:
                q = q.filter(GalleryImage.name.ilike(f'%{query}%'))

            # Filter by tags
            if gallery_filters['tags']:
                tag_list = [t.strip() for t in gallery_filters['tags'].split(',')]
                # Match images that have any of these tags
                for tag in tag_list:
                    q = q.filter(GalleryImage.tags.contains([tag]))

            # Filter by year
            if gallery_filters['year']:
                try:
                    year = int(gallery_filters['year'])
                    q = q.filter(GalleryImage.created >= datetime(year, 1, 1),
                                GalleryImage.created < datetime(year + 1, 1, 1))
                except (ValueError, TypeError):
                    pass

            images = q.all()
            for img in images:
                results['results'].append({
                    'type': 'gallery',
                    'id': img.id,
                    'name': img.name or 'Untitled',
                    'title': img.name or 'Untitled',
                    'description': img.description or '',
                    'tags': img.tags if isinstance(img.tags, list) else [],
                    'event': img.event,
                    'location': img.location or '',
                    'photographer': img.photographer or '',
                    'date': img.created.strftime('%Y-%m-%d') if img.created else None,
                    'created': img.created.isoformat() if img.created else None,
                    'url': img.url,
                    'thumbnail': img.url
                })

        # Search papers
        if content_type in ['all', 'papers']:
            q = Paper.query

            if query:
                q = q.filter(db.or_(
                    Paper.title.ilike(f'%{query}%'),
                    Paper.speaker.ilike(f'%{query}%'),
                    Paper.description.ilike(f'%{query}%')
                ))

            papers = q.all()
            for p in papers:
                results['results'].append({
                    'type': 'paper',
                    'title': p.title,
                    'speaker': p.speaker,
                    'description': p.description[:200] if p.description else '',
                    'date': p.date_published.strftime('%Y-%m-%d') if p.date_published else (p.date_entered.strftime('%Y-%m-%d') if p.date_entered else None),
                    'category': p.category,
                    'url': p.file_url
                })

        # Search series (SermonSeries & TeachingSeries)
        if content_type in ['all', 'teaching_series', 'sermon_series']:
            # Sermon Series
            q = SermonSeries.query.filter(SermonSeries.active == True)

            if query:
                q = q.filter(db.or_(
                    SermonSeries.title.ilike(f'%{query}%'),
                    SermonSeries.description.ilike(f'%{query}%'),
                    SermonSeries.slug.ilike(f'%{query}%')
                ))

            series_hits = q.all()
            for ss in series_hits:
                results['results'].append({
                    'type': 'sermon_series',
                    'title': ss.title,
                    'description': ss.description[:200] if ss.description else '',
                    'date': ss.start_date.strftime('%Y-%m-%d') if ss.start_date else None,
                    'url': url_for('sermons') + f"?series={ss.id}"
                })

            # Teaching Series (including sessions)
            q = TeachingSeries.query.filter(TeachingSeries.active == True)

            if query:
                q = q.filter(db.or_(
                    TeachingSeries.title.ilike(f'%{query}%'),
                    TeachingSeries.description.ilike(f'%{query}%')
                ))

            teaching_hits = q.all()

            # Find teaching series by matching sessions too
            if query:
                session_matches = TeachingSeriesSession.query.filter(
                    TeachingSeriesSession.title.ilike(f'%{query}%')
                ).all()

                seen_ts_ids = {ts.id for ts in teaching_hits}
                for sess in session_matches:
                    ts = sess.series
                    if ts and ts.active and ts.id not in seen_ts_ids:
                        teaching_hits.append(ts)
                        seen_ts_ids.add(ts.id)

            for ts in teaching_hits:
                results['results'].append({
                    'type': 'teaching_series',
                    'title': ts.title,
                    'description': ts.description[:200] if ts.description else '',
                    'date': ts.date_entered.strftime('%Y-%m-%d') if ts.date_entered else None,
                    'url': url_for('teaching_series') + f"?q={ts.title}"
                })

        # Sort by date descending
        results['results'].sort(key=lambda x: x.get('date', '') or '', reverse=True)
        results['total'] = len(results['results'])

        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        results['results'] = results['results'][start:end]
        results['page'] = page
        results['per_page'] = per_page
        results['pages'] = (results['total'] + per_page - 1) // per_page

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    return jsonify(results)

@app.route("/api/search/meta")
def api_search_meta():
    """Get available filter options for a given content type (for dropdown population)"""
    from datetime import datetime
    from sqlalchemy import func

    content_type = request.args.get('type', 'sermons')
    meta = {}

    try:
        if content_type in ['all', 'sermons']:
            # Get available speakers
            speakers = db.session.query(Sermon.speaker).filter(
                Sermon.active == True,
                Sermon.speaker.isnot(None)
            ).filter(_not_expired(Sermon)).distinct().order_by(Sermon.speaker).all()
            meta['speakers'] = []
            for s in speakers:
                if s[0]:
                    speaker_str = str(s[0]).strip() if not isinstance(s[0], str) else s[0].strip()
                    if speaker_str:
                        meta['speakers'].append(speaker_str)

            # Get available series - Show all series for the archive
            series_list = db.session.query(SermonSeries.id, SermonSeries.title).order_by(SermonSeries.title).all()
            meta['series'] = [{'id': s[0], 'title': s[1]} for s in series_list]

            # Get available years - Cross-DB compatible (PostgreSQL uses func.extract, SQLite uses strftime)
            year_field = func.extract('year', Sermon.date).label('year')
            if database_url.startswith('sqlite:///'):
                year_field = func.strftime('%Y', Sermon.date).label('year')

            years = db.session.query(year_field).filter(
                Sermon.active == True,
                Sermon.date.isnot(None)
            ).filter(_not_expired(Sermon)).distinct().order_by(year_field.desc()).all()
            meta['years'] = [int(y[0]) for y in years if y[0]]

            # Get scripture books (from titles of sermons that mention scripture)
            scripture_refs = db.session.query(Sermon.scripture).filter(
                Sermon.active == True,
                Sermon.scripture.isnot(None)
            ).filter(_not_expired(Sermon)).all()
            books = set()
            for (scripture,) in scripture_refs:
                if not scripture or not scripture.strip():
                    continue
                # Extract book names (simple heuristic: first word or two before a number)
                parts = scripture.split()
                for i, part in enumerate(parts):
                    if any(c.isdigit() for c in part):
                        if i > 0:
                            book = ' '.join(parts[:i]).strip()
                            if book and len(book) > 0:
                                books.add(book)
                        break
            meta['scripture_books'] = sorted(list(books))

        if content_type in ['all', 'podcasts']:
            # Get available series
            series_list = db.session.query(PodcastSeries.id, PodcastSeries.title).order_by(PodcastSeries.title).all()
            meta['podcast_series'] = [{'id': s[0], 'title': s[1]} for s in series_list]

            # Get available guests
            guests = db.session.query(PodcastEpisode.guest).filter(
                PodcastEpisode.guest.isnot(None)
            ).filter(_not_expired(PodcastEpisode)).distinct().order_by(PodcastEpisode.guest).all()
            meta['guests'] = []
            for g in guests:
                if g[0]:
                    guest_str = str(g[0]).strip() if not isinstance(g[0], str) else g[0].strip()
                    if guest_str:
                        meta['guests'].append(guest_str)

            # Get available seasons
            seasons = db.session.query(PodcastEpisode.season).filter(
                PodcastEpisode.season.isnot(None)
            ).filter(_not_expired(PodcastEpisode)).distinct().order_by(PodcastEpisode.season).all()
            meta['seasons'] = sorted([s[0] for s in seasons if s[0]])

        if content_type in ['all', 'events']:
            # Get available categories
            categories = db.session.query(OngoingEvent.category).filter(
                OngoingEvent.category.isnot(None)
            ).filter(_not_expired(OngoingEvent)).distinct().order_by(OngoingEvent.category).all()
            meta['categories'] = []
            for c in categories:
                if c[0]:
                    cat_str = str(c[0]).strip() if not isinstance(c[0], str) else c[0].strip()
                    if cat_str:
                        meta['categories'].append(cat_str)

        if content_type in ['all', 'gallery']:
            # Get available tags
            images = GalleryImage.query.filter(_not_expired(GalleryImage)).all()
            all_tags = set()
            for img in images:
                if img.tags:
                    all_tags.update(img.tags if isinstance(img.tags, list) else [img.tags])
            meta['tags'] = sorted(list(all_tags))

            # Get available years
            year_field = func.extract('year', GalleryImage.created).label('year')
            if database_url.startswith('sqlite:///'):
                year_field = func.strftime('%Y', GalleryImage.created).label('year')

            years = db.session.query(year_field).filter(
                GalleryImage.created.isnot(None)
            ).filter(_not_expired(GalleryImage)).distinct().order_by(year_field.desc()).all()
            meta['years'] = [int(y[0]) for y in years if y[0]]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'success': True,
        'type': content_type,
        'meta': meta
    })

@app.route("/api/archive")
def api_archive():
    """Archive endpoint showing older content from all sources"""
    content_type = request.args.get('type', 'all')  # all, sermons, podcasts, announcements, events, gallery
    year = request.args.get('year', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    results = {
        'type': content_type,
        'items': [],
        'total': 0,
        'page': page,
        'per_page': per_page,
        'pages': 0
    }
    
    try:
        # Get old sermons — DB only
        if content_type in ['all', 'sermons']:
            cutoff_date = (datetime.now() - timedelta(days=90)).date()
            query_builder = Sermon.query.filter(Sermon.active == True)
            if year:
                from sqlalchemy import extract
                query_builder = query_builder.filter(extract('year', Sermon.date) == int(year))
            else:
                query_builder = query_builder.filter(Sermon.date <= cutoff_date)
            archive_sermons = query_builder.order_by(Sermon.date.desc()).all()
            for s in archive_sermons:
                series_title = s.series.title if s.series else ''
                sermon_date = s.date.strftime('%Y-%m-%d') if s.date else None
                results['items'].append({
                    'type': 'sermon',
                    'title': s.title,
                    'speaker': s.speaker or '',
                    'date': sermon_date,
                    'url': s.spotify_url or s.youtube_url or s.apple_podcasts_url or '',
                    'scripture': s.scripture or '',
                    'series': series_title,
                    'description': f"{s.scripture or ''} - {series_title}".strip(' - ')
                })
        
        # Get old announcements
        if content_type in ['all', 'announcements']:
            cutoff_date = datetime.now() - timedelta(days=60)
            announcements = Announcement.query.filter(
                Announcement.date_entered < cutoff_date
            ).order_by(Announcement.date_entered.desc()).limit(50).all()
            
            for a in announcements:
                results['items'].append({
                    'type': 'announcement',
                    'title': a.title,
                    'date': a.date_entered.strftime('%Y-%m-%d'),
                    'category': a.category,
                    'url': url_for('highlights', _external=False),
                    'eventStartTime': getattr(a, 'event_start_time', None),
                    'eventEndTime': getattr(a, 'event_end_time', None),
                })
        
        # Get old podcast episodes
        if content_type in ['all', 'podcasts']:
            cutoff_date = datetime.now() - timedelta(days=90)
            episodes = PodcastEpisode.query.filter(
                PodcastEpisode.date_added < cutoff_date
            ).order_by(PodcastEpisode.date_added.desc()).limit(50).all()
            
            for ep in episodes:
                results['items'].append({
                    'type': 'podcast',
                    'title': ep.title,
                    'guest': ep.guest,
                    'date': ep.date_added.strftime('%Y-%m-%d') if ep.date_added else None,
                    'url': ep.link
                })
        
        # Get old papers
        if content_type in ['all', 'papers']:
            cutoff_date = datetime.now() - timedelta(days=180)
            papers = Paper.query.filter(
                db.or_(
                    Paper.date_entered < cutoff_date,
                    Paper.date_published < cutoff_date if Paper.date_published else False
                )
            ).order_by(Paper.date_entered.desc()).limit(50).all()
            
            for p in papers:
                results['items'].append({
                    'type': 'paper',
                    'title': p.title,
                    'speaker': p.speaker,
                    'description': p.description[:150] if p.description else '',
                    'date': p.date_published.strftime('%Y-%m-%d') if p.date_published else (p.date_entered.strftime('%Y-%m-%d') if p.date_entered else None),
                    'category': p.category,
                    'url': p.file_url
                })
        
        # Sort by date
        results['items'].sort(key=lambda x: x.get('date', ''), reverse=True)
        results['total'] = len(results['items'])
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        results['items'] = results['items'][start:end]
        results['pages'] = (results['total'] + per_page - 1) // per_page
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify(results)

# Authentication Routes
def init_admin_users():
    """Initialize the 5 admin accounts"""
    admin_accounts = [
        {'username': 'alex', 'password': 'totalchrist135'},
        {'username': 'chris', 'password': 'chrisROCKS!@#'},
        {'username': 'jerry', 'password': 'jerryOR123'},
        {'username': 'craig', 'password': 'mrCRAIG'},
        {'username': 'alexis', 'password': 'adminADMIN'}
    ]
    
    for account in admin_accounts:
        user = User.query.filter_by(username=account['username']).first()
        if not user:
            user = User(username=account['username'])
            user.set_password(account['password'])
            db.session.add(user)
    
    db.session.commit()


def _seed_pastor_teaching_sample():
    """Create sample teaching series 'Total Christ' with 5 sessions (no PDFs; pastor can add)."""
    series = TeachingSeries(
        title='Total Christ',
        description='A multi-week series on the person and work of Christ. Join us for teaching and discussion.',
        event_info='Sundays 9:00 AM — 6–8 weeks. Check bulletin for room.',
        active=True,
        sort_order=0,
    )
    db.session.add(series)
    db.session.flush()  # get series.id
    for i, title in enumerate([
        'Session 1: Introduction to Total Christ',
        'Session 2: The Deity of Christ',
        'Session 3: The Humanity of Christ',
        'Session 4: The Work of Christ',
        'Session 5: Living in Light of Christ',
    ], start=1):
        sess = TeachingSeriesSession(
            series_id=series.id,
            number=i,
            title=title,
            description='',
        )
        db.session.add(sess)
    db.session.commit()


def is_authenticated():
    """Check if user is authenticated"""
    return session.get('authenticated', False)


def get_authenticated_user():
    """Return the currently authenticated admin user or None."""
    if not is_authenticated():
        return None
    username = session.get('username')
    if not username:
        return None
    return User.query.filter_by(username=username).first()


@app.context_processor
def inject_current_user_metadata():
    """Expose authenticated-user metadata to templates."""
    user = get_authenticated_user()
    return {
        'current_user_last_login': user.last_login_at if user else None
    }

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                user.last_login_at = datetime.utcnow()
                db.session.commit()
                session['authenticated'] = True
                session['username'] = username
                flash('Login successful!', 'success')
                next_url = request.args.get('next', '/admin/dashboard/')
                return redirect(next_url)
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Please enter both username and password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('authenticated', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Admin Management Routes (all require authentication)
@app.route('/admin/debug/announcements')
@require_auth
def admin_debug_announcements():
    """Raw DB dump for debugging — returns every announcement row."""
    rows = Announcement.query.order_by(Announcement.id.desc()).all()
    return jsonify({
        'count': len(rows),
        'announcements': [
            {
                'id': a.id,
                'title': a.title,
                'active': a.active,
                'archived': getattr(a, 'archived', None),
                'type': a.type,
                'date_entered': str(a.date_entered) if a.date_entered else None,
                'description_len': len(a.description or ''),
            }
            for a in rows
        ]
    })

@app.route('/admin/export/announcements')
@require_auth
def admin_export_announcements():
    """Export announcements to CSV"""
    from admin_utils import export_announcements_csv
    return export_announcements_csv()

@app.route('/admin/export/sermons')
@require_auth
def admin_export_sermons():
    """Export sermons to CSV"""
    from admin_utils import export_sermons_csv
    return export_sermons_csv()

@app.route('/admin/stats')
@require_auth
def admin_stats():
    """Get detailed content statistics"""
    from admin_utils import get_content_stats
    return jsonify(get_content_stats())

@app.route('/admin/setup/podcast-series')
@require_auth
def admin_setup_podcast_series():
    """Create default podcast series"""
    from admin_utils import create_sample_podcast_series
    return jsonify({'message': f'Created {create_sample_podcast_series()} podcast series'})

@app.route('/admin/bulk/announcements', methods=['POST'])
@require_auth
def admin_bulk_announcements():
    """Bulk operations on announcements"""
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    field = data.get('field')
    value = data.get('value')
    
    if action == 'update' and field and value is not None:
        from admin_utils import bulk_update_announcements
        return jsonify({'success': bulk_update_announcements(ids, field, value)})
    elif action == 'delete':
        from admin_utils import bulk_delete_content
        return jsonify({'success': bulk_delete_content(Announcement, ids)})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/admin/events/reorder', methods=['POST'])
@require_auth
def admin_events_reorder():
    """Save drag-and-drop order of events. Body: JSON { \"order\": [\"id1\", \"id2\", ...] }"""
    try:
        data = request.get_json() or {}
        order = data.get('order', [])
        if not order:
            return jsonify({'success': False, 'error': 'Missing order'}), 400
        for i, eid in enumerate(order):
            event = OngoingEvent.query.get(int(eid))
            if event:
                event.sort_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/teaching-series/reorder-sessions', methods=['POST'])
@require_auth
def admin_sessions_reorder():
    """Save drag-and-drop order of sessions in a series. Body: JSON { \"order\": [\"id1\", \"id2\", ...] }"""
    try:
        data = request.get_json() or {}
        order = data.get('order', [])
        if not order:
            return jsonify({'success': False, 'error': 'Missing order'}), 400
        for i, sid in enumerate(order):
            session_obj = TeachingSeriesSession.query.get(int(sid))
            if session_obj:
                session_obj.number = i + 1  # Sessions are 1-indexed
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/bulk/sermons', methods=['POST'])
@require_auth
def admin_bulk_sermons():
    """Bulk operations on sermons"""
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    
    if action == 'delete':
        from admin_utils import bulk_delete_content
        return jsonify({'success': bulk_delete_content(Sermon, ids)})
    elif action in ('publish', 'archive', 'draft'):
        from admin_utils import bulk_update_sermons
        return jsonify({'success': bulk_update_sermons(ids, action)})
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/admin/banner-alert/new')
@require_auth
def admin_banner_alert_new():
    return redirect(url_for('announcement.create_view', banner=1))


@app.route('/admin/banners/reorder', methods=['POST'])
@require_auth
def admin_banners_reorder():
    """Save banner order (announcements with show_in_banner=True)."""
    try:
        data = request.get_json() or {}
        order = data.get('order', [])
        if not order:
            return jsonify({'success': False, 'error': 'Missing order'}), 400
        for i, aid in enumerate(order):
            ann = Announcement.query.get(int(aid))
            if ann and getattr(ann, 'show_in_banner', False):
                ann.banner_sort_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/banners/<int:aid>/expiration', methods=['POST'])
@require_auth
def admin_banner_update_expiration(aid):
    """Update expiration date for a banner announcement."""
    try:
        data = request.get_json() or {}
        ann = Announcement.query.get(aid)
        if not ann or not getattr(ann, 'show_in_banner', False):
            return jsonify({'success': False, 'error': 'Not found'}), 404
        val = data.get('expires_at')
        if val is None:
            ann.expires_at = None
        else:
            from datetime import datetime as dt
            ann.expires_at = dt.strptime(str(val)[:10], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({'success': True, 'expires_at': ann.expires_at.isoformat() if ann.expires_at else None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin image upload (for announcement featured image, etc.)
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/admin/upload-image', methods=['POST'])
@require_auth
def admin_upload_image():
    """Accept an image file; save to static/uploads; return the public URL to store in DB."""
    if 'file' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
    f = request.files.get('file') or request.files.get('image')
    if not f or f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not _allowed_image(f.filename):
        return jsonify({'error': 'Invalid file type. Use PNG, JPG, GIF, or WebP.'}), 400
    base = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    os.makedirs(base, exist_ok=True)
    ext = (f.filename.rsplit('.', 1)[1].lower() or 'jpg')
    safe_name = secure_filename(f.filename)
    if not safe_name:
        safe_name = 'image'
    unique = str(uuid.uuid4())[:8] + '_' + (safe_name[:50] if len(safe_name) > 50 else safe_name)
    unique = secure_filename(unique)
    if not unique.endswith('.' + ext):
        unique = unique + '.' + ext
    path = os.path.join(base, unique)
    try:
        f.save(path)
    except Exception as e:
        return jsonify({'error': 'Failed to save file: ' + str(e)}), 500
    # URL that works on this host (relative so it works behind a reverse proxy)
    url = url_for('static', filename='uploads/' + unique)
    return jsonify({'url': url})

@app.route('/admin/upload-gallery-image', methods=['POST'])
@require_auth
def admin_upload_gallery_image():
    """Accept an image file; upload directly to Google Cloud Storage bucket if configured, else fallback to local."""
    if 'file' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
        
    f = request.files.get('file') or request.files.get('image')
    if not f or f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not _allowed_image(f.filename):
        return jsonify({'error': 'Invalid file type. Use PNG, JPG, GIF, or WebP.'}), 400
        
    ext = (f.filename.rsplit('.', 1)[1].lower() or 'jpg')
    safe_name = secure_filename(f.filename)
    if not safe_name:
        safe_name = 'image'
        
    # Create unique filename
    unique = str(uuid.uuid4())[:8] + '_' + (safe_name[:50] if len(safe_name) > 50 else safe_name)
    unique = secure_filename(unique)
    if not unique.endswith('.' + ext):
        unique = unique + '.' + ext

    # If GCS is enabled, attempt upload to GCS first
    if GCS_ENABLED:
        try:
            client = storage.Client() 
            # Note: storage.Client() relies on Google Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS
            
            # Use public bucket shown in screenshot
            bucket_name = 'cpc-public-website' 
            bucket = client.bucket(bucket_name)
            
            # Destination inside bucket
            destination_blob_name = f"cpc-web-app-gallery/{unique}"
            blob = bucket.blob(destination_blob_name)
            
            # Upload from stream
            f.stream.seek(0)
            blob.upload_from_file(f.stream, content_type=f.content_type)
            
            # The bucket is public as per screenshot. We can form the URL easily.
            # E.g. https://storage.googleapis.com/cpc-public-website/cpc-web-app-gallery/...
            public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
            
            return jsonify({'url': public_url})
            
        except Exception as e:
            # If GCS upload fails (e.g., credentials missing), fallback to local storage
            import logging
            logging.error(f"Failed to upload to GCS: {str(e)}")
            # rewind file stream
            f.stream.seek(0)
            pass # Continue to local upload below

    # Fallback to local uploads directory
    base = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'gallery')
    os.makedirs(base, exist_ok=True)
    
    path = os.path.join(base, unique)
    try:
        f.save(path)
    except Exception as e:
        return jsonify({'error': 'Failed to save file: ' + str(e)}), 500
        
    url = url_for('static', filename='uploads/gallery/' + unique)
    return jsonify({'url': url})


@app.route('/admin/upload-podcast-thumbnail', methods=['POST'])
@require_auth
def admin_upload_podcast_thumbnail():
    """Accept an image file; upload to GCS bucket (podcast-thumbnails prefix) or local fallback; return public URL."""
    if 'file' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
    f = request.files.get('file') or request.files.get('image')
    if not f or f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not _allowed_image(f.filename):
        return jsonify({'error': 'Invalid file type. Use PNG, JPG, GIF, or WebP.'}), 400
    ext = (f.filename.rsplit('.', 1)[1].lower() or 'jpg')
    safe_name = secure_filename(f.filename)
    if not safe_name:
        safe_name = 'thumbnail'
    unique = str(uuid.uuid4())[:8] + '_' + (safe_name[:50] if len(safe_name) > 50 else safe_name)
    unique = secure_filename(unique)
    if not unique.endswith('.' + ext):
        unique = unique + '.' + ext

    if GCS_ENABLED:
        try:
            client = storage.Client()
            bucket_name = 'cpc-public-website'
            bucket = client.bucket(bucket_name)
            destination_blob_name = f"cpc-web-app-podcast-thumbnails/{unique}"
            blob = bucket.blob(destination_blob_name)
            f.stream.seek(0)
            blob.upload_from_file(f.stream, content_type=f.content_type)
            public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
            return jsonify({'url': public_url})
        except Exception as e:
            import logging
            logging.error(f"Failed to upload podcast thumbnail to GCS: {str(e)}")
            f.stream.seek(0)

    base = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'podcast-thumbnails')
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, unique)
    try:
        f.save(path)
    except Exception as e:
        return jsonify({'error': 'Failed to save file: ' + str(e)}), 500
    url = url_for('static', filename='uploads/podcast-thumbnails/' + unique)
    return jsonify({'url': url})


# PDF upload for teaching series (pastor uploads)
ALLOWED_PDF_EXTENSIONS = {'pdf'}

def _allowed_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS

@app.route('/admin/upload-pdf', methods=['POST'])
@require_auth
def admin_upload_pdf():
    """Accept a PDF file; save to static/uploads/teaching; return the public URL."""
    if 'file' not in request.files and 'pdf' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
    f = request.files.get('file') or request.files.get('pdf')
    if not f or f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not _allowed_pdf(f.filename):
        return jsonify({'error': 'Invalid file type. Only PDF is allowed.'}), 400
    base = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'teaching')
    os.makedirs(base, exist_ok=True)
    ext = (f.filename.rsplit('.', 1)[1].lower() or 'pdf')
    safe_name = secure_filename(f.filename)
    if not safe_name:
        safe_name = 'handout'
    unique = str(uuid.uuid4())[:8] + '_' + (safe_name[:50] if len(safe_name) > 50 else safe_name)
    unique = secure_filename(unique)
    if not unique.endswith('.' + ext):
        unique = unique + '.' + ext
    path = os.path.join(base, unique)
    try:
        f.save(path)
    except Exception as e:
        return jsonify({'error': 'Failed to save file: ' + str(e)}), 500
    url = url_for('static', filename='uploads/teaching/' + unique)
    return jsonify({'url': url})

# Enhanced Admin Interface
from flask_admin import BaseView, expose
from flask_admin.actions import action
from wtforms import TextAreaField, SelectField, BooleanField, StringField, DateField, URLField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, URL, Length, Optional
import re
from wtforms.widgets import TextArea, Select, Input
from datetime import datetime

# ---------------------------------------------------------------------------
# Global date/datetime picker widgets (calendar) for admin forms
# ---------------------------------------------------------------------------
class DatePickerWidget(Input):
    """Renders <input type="date"> for calendar picker."""
    input_type = 'date'
    validation_attrs = ('required', 'max', 'min', 'maxlength', 'minlength', 'pattern', 'step')

    def __call__(self, field, **kwargs):
        if field.data and hasattr(field.data, 'strftime'):
            kwargs.setdefault('value', field.data.strftime('%Y-%m-%d'))
        return super().__call__(field, **kwargs)


class DateTimePickerWidget(Input):
    """Renders <input type="datetime-local"> for calendar picker."""
    input_type = 'datetime-local'
    validation_attrs = ('required', 'max', 'min', 'maxlength', 'minlength', 'pattern', 'step')

    def __call__(self, field, **kwargs):
        if field.data:
            d = field.data
            if hasattr(d, 'strftime'):
                # datetime-local wants YYYY-MM-DDTHH:MM (no seconds for better browser support)
                kwargs.setdefault('value', d.strftime('%Y-%m-%dT%H:%M'))
            else:
                kwargs.setdefault('value', d)
        return super().__call__(field, **kwargs)


# ---------------------------------------------------------------------------
# Datalist widget — text input with <datalist> suggestions (no forced dropdown)
# ---------------------------------------------------------------------------
from wtforms.widgets import html_params

class DatalistWidget:
    """Renders <input type="text" list="..."> + <datalist> for browser autocomplete."""
    def __call__(self, field, **kwargs):
        dl_id = f'dl-{field.id}'
        kwargs.setdefault('id', field.id)
        kwargs['list'] = dl_id
        kwargs['autocomplete'] = 'off'
        value = field._value() if field.data is not None else ''
        from markupsafe import escape
        input_tag = f'<input type="text" name="{field.name}" value="{escape(value)}" {html_params(**kwargs)}>'
        choices = field.datalist_choices() if callable(getattr(field, 'datalist_choices', None)) else []
        opts = ''.join(f'<option value="{escape(c)}">' for c in choices)
        return Markup(f'{input_tag}<datalist id="{dl_id}">{opts}</datalist>')


class DatalistField(StringField):
    """StringField that renders with a <datalist> for suggestions."""
    widget = DatalistWidget()

    def __init__(self, label='', choices_func=None, **kwargs):
        super().__init__(label, **kwargs)
        self._choices_func = choices_func or (lambda: [])
        self.widget = DatalistWidget()

    def datalist_choices(self):
        try:
            return self._choices_func()
        except Exception:
            return []


# Expiration preset choices for "when to stop showing" in all content wizards
EXPIRATION_PRESET_CHOICES = [
    ('never', 'Never'),
    ('1_week', '1 week'),
    ('2_weeks', '2 weeks'),
    ('3_weeks', '3 weeks'),
    ('4_weeks', '4 weeks'),
    ('specific', 'Pick a date…'),
]


def _admin_speaker_choices():
    """Choices for speaker dropdown: all admin users (logged-in admins)."""
    try:
        if not has_app_context():
            return []
        return [(u.username, u.username) for u in User.query.order_by(User.username).all()]
    except RuntimeError:
        return []


def _compute_expires_at(preset_value, specific_date_value, base_date):
    """Return a date or None for model.expires_at from form preset + optional specific date.
    base_date is the content's "created" date (date_entered, date, date_added, or created).
    """
    if not preset_value or preset_value == 'never':
        return None
    if preset_value == 'specific':
        if specific_date_value and hasattr(specific_date_value, 'date'):
            return specific_date_value.date() if hasattr(specific_date_value, 'date') else specific_date_value
        return specific_date_value
    base = base_date.date() if hasattr(base_date, 'date') else (base_date if isinstance(base_date, date) else date.today())
    weeks = {'1_week': 1, '2_weeks': 2, '3_weeks': 3, '4_weeks': 4}.get(preset_value)
    if weeks:
        return base + timedelta(weeks=weeks)
    return None


class DatePickerField(DateField):
    """DateField that uses HTML5 date input (calendar widget)."""
    widget = DatePickerWidget()


class DateTimePickerField(DateTimeField):
    """DateTimeField that uses HTML5 datetime-local input (calendar widget)."""
    widget = DateTimePickerWidget()

    def process_formdata(self, valuelist):
        if not valuelist or not valuelist[0]:
            self.data = None
            return
        val = valuelist[0]
        try:
            from dateutil.parser import parse
            self.data = parse(val)
        except Exception:
            # Fallback to standard formats
            from datetime import datetime
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M', '%m/%d/%Y, %I:%M %p', '%m/%d/%Y %I:%M %p'):
                try:
                    self.data = datetime.strptime(val, fmt)
                    return
                except ValueError:
                    pass
            # If all else fails, don't throw a validation error
            self.data = None

# ---------------------------------------------------------------------------
# Audit-log helper
# ---------------------------------------------------------------------------
def _log_audit(action, model, entity_type=None):
    """Write one row to the audit_log table.

    ``model`` is the SQLAlchemy instance being created/edited/deleted.
    ``action`` is one of 'created', 'edited', 'deleted', 'published', 'archived', 'draft'.
    """
    if model is None:
        return
    try:
        username = session.get('username') or 'unknown'
        etype = entity_type or (getattr(model, '__class__', None) and model.__class__.__name__) or 'Content'
        eid = getattr(model, 'id', None)
        if eid is not None and not isinstance(eid, int):
            try:
                eid = int(eid)
            except (TypeError, ValueError):
                eid = None
        etitle = (getattr(model, 'title', None)
                  or getattr(model, 'name', None)
                  or (str(eid) if eid is not None else None))
        entity_title = (str(etitle)[:300]) if etitle else None
        entry = AuditLog(
            user=username,
            action=str(action)[:20],
            entity_type=etype[:50] if etype else 'Content',
            entity_id=eid,
            entity_title=entity_title,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        log.warning("Audit log write failed: %s", exc)
        try:
            db.session.rollback()
        except Exception:
            pass


# Authenticated ModelView
class AuthenticatedModelView(ModelView):
    """ModelView that requires authentication"""
    def is_accessible(self):
        return is_authenticated()
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    # --- audit hooks ---
    def after_model_change(self, form, model, is_created):
        _log_audit('created' if is_created else 'edited', model)

    def after_model_delete(self, model):
        _log_audit('deleted', model)


class UserView(AuthenticatedModelView):
    """Admin CRUD for login users (admin panel accounts)."""
    column_list = ('id', 'username', 'created_at', 'last_login_at')
    column_searchable_list = ('username',)
    form_excluded_columns = ('password_hash',)
    form_extra_fields = {
        'password': PasswordField('Password (required for new user; leave blank to keep current)', validators=[Optional()]),
    }
    form_columns = ('username', 'password')

    def on_model_change(self, form, model, is_created):
        pw = getattr(form, 'password', None)
        if pw and pw.data:
            from werkzeug.security import generate_password_hash
            model.password_hash = generate_password_hash(pw.data)
        elif is_created:
            import os
            from werkzeug.security import generate_password_hash
            model.password_hash = generate_password_hash(os.urandom(24).hex())
            flash('User created with a random password. Edit the user and set a real password.', 'warning')


# Choices for announcement type/category
# wtforms SelectField (4-tuple iter_choices), not Flask-Admin Select2Field (3-tuple, breaks widget)
ANNOUNCEMENT_TYPE_CHOICES = [
    ('announcement', 'Announcement'),
    ('event', 'Event'),
    ('ongoing', 'Ongoing'),
    ('highlight', 'Highlight'),
    ('weather', 'Weather Alert'),
    ('parking', 'Parking Update'),
    ('alert', 'General Alert'),
    ('info', 'Info'),
]
ANNOUNCEMENT_CATEGORY_CHOICES = [
    ('general', 'General'),
    ('worship', 'Worship'),
    ('education', 'Education'),
    ('fellowship', 'Fellowship'),
    ('missions', 'Missions'),
    ('youth', 'Youth'),
    ('children', 'Children'),
]


def _format_announcement_status(view, context, model, name):
    from flask import url_for
    base = url_for('announcement.set_status')
    publish_url = base + '?id=' + str(model.id) + '&status=publish'
    draft_url = base + '?id=' + str(model.id) + '&status=draft'
    archive_url = base + '?id=' + str(model.id) + '&status=archive'
    active = getattr(model, 'active', True)
    archived = getattr(model, 'archived', False)
    if archived:
        status_tag = '<span class="admin-status-tag admin-status-archived">Archived</span>'
    elif active:
        status_tag = '<span class="admin-status-tag admin-status-published">Published</span>'
    else:
        status_tag = '<span class="admin-status-tag admin-status-draft">Draft</span>'
    dropdown = (
        '<select class="admin-status-select" onchange="var u=this.value; if(u) window.location=u;">'
        '<option value="">Change status…</option>'
        '<option value="' + publish_url + '">Publish</option>'
        '<option value="' + draft_url + '">Revert to draft</option>'
        '<option value="' + archive_url + '">Archive</option>'
        '</select>'
    )
    tags = [status_tag, dropdown]
    if getattr(model, 'superfeatured', False):
        tags.insert(1, '<span class="admin-status-tag admin-status-featured">Featured</span>')
    if getattr(model, 'show_in_banner', False):
        tags.insert(1, '<span class="admin-status-tag admin-status-banner">Banner</span>')
    return Markup('<span class="admin-status-wrap announcement-status-wrap">' + ' '.join(tags) + '</span>')


from flask_admin.form import rules

class AnnouncementView(AuthenticatedModelView):
    create_template = 'admin/model/create_bento.html'
    edit_template = 'admin/model/edit_bento.html'
    column_list = ('id', 'title', 'speaker', 'type', 'category', 'active', 'show_in_banner', 'superfeatured', 'revision', 'date_entered', 'updated_at', 'updated_by', 'event_date', 'event_start_time', 'event_end_time', 'expires_at')
    column_searchable_list = ('title', 'description', 'tag', 'speaker')
    column_filters = ('type', 'active', 'tag', 'superfeatured', 'show_in_banner', 'category', 'speaker')
    column_sortable_list = ('title', 'type', 'active', 'superfeatured', 'date_entered', 'speaker')
    column_default_sort = ('date_entered', True)
    page_size = 50
    can_set_page_size = True
    page_size_choices = (20, 50, 100, 500, 1000)
    form_excluded_columns = ['id']
    create_template = 'admin/announcement_create.html'
    edit_template = 'admin/announcement_create.html'

    form_rules = [
        rules.FieldSet(('type',), 'What kind of announcement?'),
        rules.FieldSet(('title', 'description', 'category', 'tag', 'speaker'), 'Content'),
        rules.FieldSet(('event_date', 'event_start_time', 'event_end_time'), 'Event Details (if applicable)'),
        rules.FieldSet(('active', 'show_in_banner', 'banner_type', 'superfeatured', 'featured_image', 'image_display_type'), 'Styling and Placement'),
        rules.FieldSet(('expiration_preset', 'expiration_date'), 'Expiration'),
        rules.FieldSet(('date_entered',), 'System (Auto-managed)')
    ]
    form_columns = ('type', 'title', 'description', 'category', 'tag', 'speaker', 'event_date', 'event_start_time', 'event_end_time', 'active', 'show_in_banner', 'banner_type', 'superfeatured', 'featured_image', 'image_display_type', 'expiration_preset', 'expiration_date', 'date_entered')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Optional(), Length(max=2000)]),
        'banner_type': SelectField(
            'Top bar banner',
            choices=[
                ('', 'No banner'),
                ('weather', 'Weather'),
                ('parking', 'Parking'),
                ('alert', 'Alert'),
                ('info', 'Info')
            ]
        ),
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
    }
    form_overrides = {
        'type': SelectField,
        'category': SelectField,
        'date_entered': DateTimePickerField,
        'event_date': DateField,
        'speaker': SelectField,
    }

    form_args = {
        'type': {'choices': ANNOUNCEMENT_TYPE_CHOICES},
        'category': {'choices': ANNOUNCEMENT_CATEGORY_CHOICES},
        'speaker': {'choices': []},  # set in get_form from admin users
    }
    
    form_widget_args = {
        'description': {'rows': 10, 'style': 'width: 100%'},
        'featured_image': {'placeholder': 'https://example.com/image.jpg'},
        'image_display_type': {'placeholder': 'poster or leave empty'},
        'event_date': {'placeholder': 'Date of event'},
        'event_start_time': {'placeholder': 'e.g. 9:00 AM or Sunday 10:30'},
        'event_end_time': {'placeholder': 'e.g. 11:00 AM or leave empty'},
    }

    column_labels = {
        'date_entered': 'Date Created',
        'revision': 'Rev',
        'updated_at': 'Last Updated',
        'updated_by': 'Updated By',
        'expires_at': 'Expires',
        'expiration_preset': 'Expiration',
        'expiration_date': 'Expiration date',
        'superfeatured': 'Super Featured',
        'show_in_banner': 'Featured in top bar',
        'featured_image': 'Featured Image URL',
        'image_display_type': 'Image Display Type',
        'active': 'Status',
        'speaker': 'Speaker',
        'event_date': 'Add an event date',
        'event_start_time': 'Event start time',
        'event_end_time': 'Event end time',
    }

    column_formatters = {
        'active': _format_announcement_status
    }

    def get_form(self):
        form = super().get_form()
        if form and hasattr(form, 'speaker') and has_app_context():
            form.speaker.choices = _admin_speaker_choices()
            if not form.speaker.choices:
                form.speaker.choices = [('', '— No admins —')]
            if has_request_context():
                current = session.get('username')
                if current and (not form.speaker.data or not str(form.speaker.data).strip()):
                    form.speaker.data = current
        return form

    def on_form_prefill(self, form, id):
        announcement = self.get_one(id)
        if not announcement:
            return
        if hasattr(form, 'banner_type'):
            if getattr(announcement, 'show_in_banner', False):
                current_type = (announcement.type or '').strip().lower()
                if current_type not in {'weather', 'parking', 'alert', 'info'}:
                    current_type = 'alert'
                form.banner_type.data = current_type
            else:
                form.banner_type.data = ''
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(announcement, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(announcement, 'expires_at', None):
            form.expiration_date.data = announcement.expires_at

    def on_model_change(self, form, model, is_created):
        app.logger.info(
            "ANNC on_model_change: is_created=%s title=%r form_keys=%s",
            is_created, getattr(model, 'title', None),
            list(request.form.keys())
        )
        if request.form.get('_save_and_publish'):
            model.active = True
            model.archived = False
        # "Featured in top bar": banner_type selection (e.g. Weather) turns it on; otherwise use checkbox
        banner_field = getattr(form, 'banner_type', None)
        raw = getattr(banner_field, 'data', None) if banner_field else None
        banner_choice = (str(raw).strip().lower() if raw is not None and raw != '' else '')
        if banner_choice:
            model.show_in_banner = True
            model.type = banner_choice
        else:
            show_in_banner_field = getattr(form, 'show_in_banner', None)
            if show_in_banner_field is not None and hasattr(show_in_banner_field, 'data'):
                model.show_in_banner = bool(show_in_banner_field.data)
            else:
                model.show_in_banner = False
        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.date_entered or datetime.utcnow()
        model.expires_at = _compute_expires_at(preset, specific, base)
        if is_created:
            if not model.date_entered:
                model.date_entered = datetime.utcnow()
            model.id = next_global_id()
        else:
            # Versioning: so editors know what is what
            model.updated_at = datetime.utcnow()
            model.updated_by = session.get('username') or None
            model.revision = (getattr(model, 'revision', None) or 1) + 1

    def after_model_change(self, form, model, is_created):
        _log_audit('created' if is_created else 'edited', model)
        try:
            cache.clear()
        except Exception:
            pass

    def after_model_delete(self, model):
        _log_audit('deleted', model)
        try:
            cache.clear()
        except Exception:
            pass

    @expose('/create/', methods=['GET', 'POST'])
    def create_view(self):
        if not is_authenticated():
            return redirect(url_for('admin_login'))
        speakers = _admin_speaker_choices() or [('', '— No admins —')]
        errors = []
        form_data = {}
        if request.method == 'POST':
            form_data = request.form.to_dict()
            title = form_data.get('title', '').strip()
            description = form_data.get('description', '').strip()
            if not title:
                errors.append('Title is required.')
            if not description:
                errors.append('Description is required.')
            if not errors:
                ann = Announcement(
                    id=next_global_id(),
                    title=title,
                    description=description,
                    type=form_data.get('type', 'announcement'),
                    category=form_data.get('category', 'general'),
                    tag=form_data.get('tag', '') or None,
                    speaker=form_data.get('speaker', '') or None,
                    event_start_time=form_data.get('event_start_time', '') or None,
                    event_end_time=form_data.get('event_end_time', '') or None,
                    active='_publish' in request.form,
                    superfeatured=bool(form_data.get('superfeatured')),
                    show_in_banner=bool(form_data.get('show_in_banner')),
                    archived=False,
                    date_entered=datetime.utcnow(),
                )
                db.session.add(ann)
                db.session.commit()
                _log_audit('created', ann)
                try:
                    cache.clear()
                except Exception:
                    pass
                flash(f'"{title}" {"published" if ann.active else "saved as draft"}.', 'success')
                return redirect(url_for('announcement.index_view'))
        return self.render('admin/announcement_direct_create.html',
                           form_data=form_data,
                           errors=errors,
                           type_choices=ANNOUNCEMENT_TYPE_CHOICES,
                           category_choices=ANNOUNCEMENT_CATEGORY_CHOICES,
                           speakers=speakers)

    @expose('set-status/', methods=['GET'])
    def set_status(self):
        if not is_authenticated():
            return redirect(url_for('admin_login'))
        id_val = request.args.get('id', type=int)
        status = request.args.get('status')
        if not id_val or status not in ('publish', 'draft', 'archive'):
            flash('Invalid request.', 'error')
            return redirect(url_for('announcement.index_view'))
        ann = Announcement.query.get(id_val)
        if not ann:
            flash('Not found.', 'error')
            return redirect(url_for('announcement.index_view'))
        if status == 'publish':
            ann.active = True
            ann.archived = False
        elif status == 'draft':
            ann.active = False
            ann.archived = False
        else:
            ann.active = False
            ann.archived = True
        ann.updated_at = datetime.utcnow()
        ann.updated_by = session.get('username') or None
        ann.revision = (getattr(ann, 'revision', None) or 1) + 1
        db.session.commit()
        try:
            _log_audit(status, ann)
        except:
            pass
        try:
            cache.clear()
        except Exception:
            pass
        flash('Status updated.', 'success')
        return redirect(url_for('announcement.index_view'))

    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected items?')
    def toggle_active(self, ids):
        try:
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    announcement.active = not announcement.active
            db.session.commit()
            try:
                for id in ids:
                    ann = Announcement.query.get(id)
                    if ann:
                        _log_audit('edited', ann)
            except:
                pass
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
            try:
                for id in ids:
                    ann = Announcement.query.get(id)
                    if ann:
                        _log_audit('edited', ann)
            except:
                pass
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
                try:
                    for id in ids:
                        ann = Announcement.query.get(id)
                        if ann:
                            _log_audit('edited', ann)
                except:
                    pass
                flash(f'Successfully updated category for {len(ids)} announcements', 'success')
                return True
            except Exception as e:
                flash(f'Error updating category: {str(e)}', 'error')
                return False
        return False

    @action('bulk_publish', 'Publish Selected', 'Are you sure you want to publish the selected announcements?')
    def bulk_publish(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    announcement.active = True
                    announcement.archived = False
                    count += 1
            db.session.commit()
            
            for id in ids:
                ann = Announcement.query.get(id)
                if ann:
                    try:
                        _log_audit('published', ann)
                    except:
                        pass
            
            flash(f'Successfully published {count} announcements', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Announcement bulk_publish: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error publishing announcements: {str(e)}', 'error')
            return False

    @action('bulk_archive', 'Archive Selected', 'Are you sure you want to archive the selected announcements?')
    def bulk_archive(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    announcement.active = False
                    announcement.archived = True
                    count += 1
            db.session.commit()
            
            for id in ids:
                ann = Announcement.query.get(id)
                if ann:
                    try:
                        _log_audit('archived', ann)
                    except:
                        pass
            
            flash(f'Successfully archived {count} announcements', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Announcement bulk_archive: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error archiving announcements: {str(e)}', 'error')
            return False

    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected announcements? This cannot be undone.')
    def bulk_delete(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                announcement = Announcement.query.get(id)
                if announcement:
                    try:
                        _log_audit('deleted', announcement)
                    except:
                        pass
                    db.session.delete(announcement)
                    count += 1
            db.session.commit()
            flash(f'Successfully deleted {count} announcements', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Announcement bulk_delete: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error deleting announcements: {str(e)}', 'error')
            return False

# Gospel books for sermon wizard (series -> chapter -> verse)
SERMON_BOOK_CHOICES = [('', '— Select book —'), ('Matthew', 'Matthew'), ('Mark', 'Mark'), ('Luke', 'Luke'), ('John', 'John')]
SERMON_CHAPTER_CHOICES = [('', '—')] + [(str(i), str(i)) for i in range(1, 29)]
SERMON_VERSE_CHOICES = [('0', 'Whole chapter')] + [(str(i), str(i)) for i in range(1, 51)]


def _format_sermon_status(view, context, model, name):
    from flask import url_for
    base = url_for('sermon.set_status')
    publish_url = base + '?id=' + str(model.id) + '&status=publish'
    draft_url = base + '?id=' + str(model.id) + '&status=draft'
    archive_url = base + '?id=' + str(model.id) + '&status=archive'
    active = getattr(model, 'active', True)
    archived = getattr(model, 'archived', False)
    if archived:
        status_tag = '<span class="admin-status-tag admin-status-archived">Archived</span>'
    elif active:
        status_tag = '<span class="admin-status-tag admin-status-published">Published</span>'
    else:
        status_tag = '<span class="admin-status-tag admin-status-draft">Draft</span>'
    dropdown = (
        '<select class="admin-status-select" onchange="var u=this.value; if(u) window.location=u;">'
        '<option value="">Change status…</option>'
        '<option value="' + publish_url + '">Publish</option>'
        '<option value="' + draft_url + '">Revert to draft</option>'
        '<option value="' + archive_url + '">Archive</option>'
        '</select>'
    )
    return Markup('<span class="admin-status-wrap">' + status_tag + ' ' + dropdown + '</span>')


class PaperView(AuthenticatedModelView):
    column_list = ('title', 'speaker', 'category', 'date_published', 'active')
    column_searchable_list = ('title', 'speaker', 'description')
    column_filters = ('category', 'active', 'speaker')
    column_sortable_list = ('date_published', 'title', 'speaker')
    column_default_sort = ('date_published', True)
    form_columns = ('title', 'speaker', 'description', 'content', 'category', 'date_published', 'file_url', 'thumbnail_url', 'active')
    column_labels = {
        'speaker': 'Speaker/Author',
        'date_published': 'Published Date',
        'file_url': 'File URL',
        'thumbnail_url': 'Thumbnail URL',
    }
    form_overrides = {
        'speaker': StringField,
        'date_published': DatePickerField,
    }

    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected papers?')
    def toggle_active(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                paper = Paper.query.get(id)
                if paper:
                    paper.active = not paper.active
                    count += 1
            db.session.commit()
            flash(f'Successfully toggled active status for {count} papers', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Paper toggle_active: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error toggling active status: {str(e)}', 'error')
            return False

    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected papers? This cannot be undone.')
    def bulk_delete(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                paper = Paper.query.get(id)
                if paper:
                    db.session.delete(paper)
                    count += 1
            db.session.commit()
            flash(f'Successfully deleted {count} papers', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Paper bulk_delete: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error deleting papers: {str(e)}', 'error')
            return False
    
class SermonView(AuthenticatedModelView):
    create_template = 'admin/model/create_bento.html'
    edit_template = 'admin/model/edit_bento.html'
    column_list = ('id', 'title', 'series', 'episode_number', 'speaker_user', 'date', 'scripture', 'featured', 'active', 'expires_at')
    column_searchable_list = ('title', 'scripture')
    column_filters = ('series', 'speaker_user.full_name', 'date', 'active')
    column_sortable_list = ('date', 'title', 'episode_number')
    column_default_sort = ('date', True)
    form_excluded_columns = ['id', 'speaker']  # Exclude legacy speaker field from form

    form_fieldsets = (
        ('Basic Details', {'fields': ('title', 'speaker_name', 'date', 'series_name', 'episode_number', 'active')}),
        ('Scripture Reference', {'fields': ('book_name', 'chapter_start', 'verse_start', 'chapter_end', 'verse_end')}),
        ('Media Links & Files', {'fields': ('audio_file_url', 'video_file_url', 'youtube_url', 'spotify_url', 'apple_podcasts_url', 'podcast_thumbnail_url')}),
        ('Related Content', {'fields': ('beyond_episode_name',)}),
        ('Visibility & Expiration', {'fields': ('featured', 'archived', 'expiration_preset', 'expiration_date')}),
    )
    
    form_columns = (
        'series_name', 'episode_number',
        'book_name', 'chapter_start', 'verse_start', 'chapter_end', 'verse_end',
        'title', 'speaker_name', 'date',
        'audio_file_url', 'video_file_url',
        'beyond_episode_name',
        'spotify_url', 'youtube_url', 'apple_podcasts_url', 'podcast_thumbnail_url',
        'expiration_preset', 'expiration_date', 'featured', 'active', 'archived'
    )
    
    column_labels = {
        'series': 'Series',
        'series_name': 'Series',
        'episode_number': 'Ep #',
        'book': 'Bible Book',
        'book_name': 'Bible Book',
        'beyond_episode': 'Beyond Link',
        'beyond_episode_name': 'Beyond Link',
        'audio_file_url': 'Audio File',
        'video_file_url': 'Video File',
        'spotify_url': 'Spotify',
        'youtube_url': 'YouTube',
        'apple_podcasts_url': 'Apple Podcasts',
        'podcast_thumbnail_url': 'Thumbnail',
        'featured': 'Featured',
        'active': 'Status',
        'expires_at': 'Expires',
        'speaker_user': 'Speaker',
        'speaker_name': 'Speaker',
    }
    
    column_formatters = {
        'active': _format_sermon_status,
        'speaker_user': lambda view, context, model, name: (
            model.speaker_user.full_name if model.speaker_user and model.speaker_user.full_name
            else (model.speaker_user.username if model.speaker_user else (model.speaker if model.speaker else '—'))
        )
    }

    form_extra_fields = {
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
        'series_name': DatalistField('Series',
            choices_func=lambda: [s.title for s in SermonSeries.query.order_by(SermonSeries.start_date.desc()).all()]),
        'book_name': DatalistField('Bible Book',
            choices_func=lambda: [b.name for b in BibleBook.query.order_by(BibleBook.sort_order).all()]),
        'speaker_name': DatalistField('Speaker',
            choices_func=lambda: [u.full_name for u in User.query.filter(User.full_name != None).order_by(User.full_name).all()]),
        'beyond_episode_name': DatalistField('Beyond Link',
            choices_func=lambda: [e.title for e in PodcastEpisode.query.order_by(PodcastEpisode.date_added.desc()).all()]),
    }

    form_overrides = {
        'date': DatePickerField,
    }

    form_args = {}

    form_widget_args = {
        'spotify_url': {'placeholder': 'https://open.spotify.com/episode/...'},
        'youtube_url': {'placeholder': 'https://youtube.com/watch?v=...'},
        'apple_podcasts_url': {'placeholder': 'https://podcasts.apple.com/podcast/...'},
        'podcast_thumbnail_url': {'placeholder': 'https://example.com/thumbnail.jpg'},
        'audio_file_url': {'placeholder': 'https://storage.googleapis.com/.../sermon.mp3'},
        'video_file_url': {'placeholder': 'https://storage.googleapis.com/.../video.mp4'}
    }

    def on_form_prefill(self, form, id):
        sermon = self.get_one(id)
        if not sermon:
            return
        if hasattr(form, 'series_name'):
            form.series_name.data = sermon.series.title if sermon.series else ''
        if hasattr(form, 'book_name'):
            form.book_name.data = sermon.book.name if sermon.book else ''
        if hasattr(form, 'speaker_name'):
            form.speaker_name.data = sermon.speaker_user.full_name if sermon.speaker_user else ''
        if hasattr(form, 'beyond_episode_name'):
            form.beyond_episode_name.data = sermon.beyond_episode.title if sermon.beyond_episode else ''
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(sermon, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(sermon, 'expires_at', None):
            form.expiration_date.data = sermon.expires_at

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()

        # Resolve text datalist fields → FK relationships
        series_name = (getattr(form, 'series_name', None) and form.series_name.data or '').strip()
        model.series = SermonSeries.query.filter_by(title=series_name).first() if series_name else None

        book_name = (getattr(form, 'book_name', None) and form.book_name.data or '').strip()
        book_obj = BibleBook.query.filter(BibleBook.name.ilike(book_name)).first() if book_name else None
        model.book = book_obj

        speaker_name = (getattr(form, 'speaker_name', None) and form.speaker_name.data or '').strip()
        model.speaker_user = User.query.filter_by(full_name=speaker_name).first() if speaker_name else None

        beyond_name = (getattr(form, 'beyond_episode_name', None) and form.beyond_episode_name.data or '').strip()
        model.beyond_episode = PodcastEpisode.query.filter_by(title=beyond_name).first() if beyond_name else None

        # Auto-generate scripture string from book/chapter/verse
        ch_start = getattr(form, 'chapter_start', None) and getattr(form.chapter_start, 'data', None)
        v_start = getattr(form, 'verse_start', None) and getattr(form.verse_start, 'data', None)
        ch_end = getattr(form, 'chapter_end', None) and getattr(form.chapter_end, 'data', None)
        v_end = getattr(form, 'verse_end', None) and getattr(form.verse_end, 'data', None)

        if book_obj:
            ref = book_obj.name
            if ch_start:
                ref += f" {ch_start}"
                if v_start:
                    ref += f":{v_start}"
                
                if ch_end or v_end:
                    ref += "-"
                    if ch_end and ch_end != ch_start:
                         ref += f"{ch_end}:"
                    if v_end:
                        ref += f"{v_end}"
            
            model.scripture = ref
            # If title is empty, use scripture
            if not (model.title and model.title.strip()):
                model.title = ref

        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.date or date.today()
        model.expires_at = _compute_expires_at(preset, specific, base)

    @expose('set-status/', methods=['GET'])
    def set_status(self):
        if not is_authenticated():
            return redirect(url_for('admin_login'))
        id_val = request.args.get('id', type=int)
        status = request.args.get('status')
        if not id_val or status not in ('publish', 'draft', 'archive'):
            flash('Invalid request.', 'error')
            return redirect(url_for('sermon.index_view'))
        s = Sermon.query.get(id_val)
        if not s:
            flash('Not found.', 'error')
            return redirect(url_for('sermon.index_view'))
        if status == 'publish':
            s.active = True
            s.archived = False
        elif status == 'draft':
            s.active = False
            s.archived = False
        else:
            s.active = False
            s.archived = True
        db.session.commit()
        try:
            _log_audit(status, s)
        except:
            pass
        flash('Status updated.', 'success')
        return redirect(url_for('sermon.index_view'))
    
    @action('bulk_publish', 'Publish Selected', 'Are you sure you want to publish the selected sermons?')
    def bulk_publish(self, ids):
        try:
            count = 0
            # Cast all IDs to int upfront to avoid surprises
            ids = [int(i) for i in ids]
            for id in ids:
                sermon = Sermon.query.get(id)
                if sermon:
                    sermon.active = True
                    sermon.archived = False
                    count += 1
            db.session.commit()
            
            # Log audit after main commit
            for id in ids:
                s = Sermon.query.get(id)
                if s:
                    try:
                        _log_audit('published', s)
                    except Exception as e:
                        log.warning(f"Failed to log audit for sermon {id}: {e}")
            
            flash(f'Successfully published {count} sermons', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Sermon bulk_publish: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error publishing sermons: {str(e)}', 'error')
            return False
    
    @action('bulk_archive', 'Archive Selected', 'Are you sure you want to archive the selected sermons?')
    def bulk_archive(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                sermon = Sermon.query.get(id)
                if sermon:
                    sermon.active = False
                    sermon.archived = True
                    count += 1
            db.session.commit()
            
            for id in ids:
                s = Sermon.query.get(id)
                if s:
                    try:
                        _log_audit('archived', s)
                    except Exception as e:
                        log.warning(f"Failed to log audit for sermon {id}: {e}")
            
            flash(f'Successfully archived {count} sermons', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Sermon bulk_archive: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error archiving sermons: {str(e)}', 'error')
            return False
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected sermons?')
    def bulk_delete(self, ids):
        try:
            ids = [int(i) for i in ids]
            for id in ids:
                sermon = Sermon.query.get(id)
                if sermon:
                    try:
                        _log_audit('deleted', sermon)
                    except:
                        pass
                    db.session.delete(sermon)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} sermons', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in Sermon bulk_delete: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error deleting sermons: {str(e)}', 'error')
            return False

class PodcastEpisodeView(AuthenticatedModelView):
    create_template = 'admin/model/create_bento.html'
    edit_template = 'admin/model/edit_bento.html'
    column_list = ('number', 'title', 'series', 'guest', 'date_added', 'source', 'expires_at', 'scripture')
    column_searchable_list = ('title', 'guest', 'scripture')
    column_filters = ('series', 'guest', 'season', 'source')
    column_sortable_list = ('number', 'title', 'date_added')
    column_default_sort = ('number', True)
    form_excluded_columns = ['id', 'source', 'original_id']

    form_fieldsets = (
        ('Episode Information', {'fields': ('title', 'series', 'number', 'season', 'date_added')}),
        ('Content & Guests', {'fields': ('guest', 'scripture', 'podcast_thumbnail_url')}),
        ('Media Links & Resources', {'fields': ('link', 'listen_url', 'handout_url')}),
        ('Visibility & Expiration', {'fields': ('expiration_preset', 'expiration_date')})
    )
    form_columns = ('series', 'number', 'title', 'link', 'listen_url', 'handout_url', 'guest', 'date_added', 'season', 'scripture', 'podcast_thumbnail_url', 'expiration_preset', 'expiration_date')
    form_extra_fields = {
        'scripture': TextAreaField('Scripture', widget=TextArea()),
        'link': URLField('Episode Link', validators=[Optional(), URL()]),
        'listen_url': URLField('Listen URL', validators=[Optional(), URL()]),
        'handout_url': URLField('Handout URL', validators=[Optional(), URL()]),
        'podcast_thumbnail_url': URLField('Thumbnail URL', validators=[Optional(), URL()]),
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
    }
    form_overrides = {'date_added': DatePickerField}

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
        'podcast_thumbnail_url': 'Thumbnail',
        'source': 'Added By',
        'expires_at': 'Expires',
    }

    def on_form_prefill(self, form, id):
        episode = self.get_one(id)
        if not episode:
            return
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(episode, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(episode, 'expires_at', None):
            form.expiration_date.data = episode.expires_at

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
            if not getattr(model, 'source', None):
                model.source = 'manual'
        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.date_added or date.today()
        model.expires_at = _compute_expires_at(preset, specific, base)
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected podcast episodes?')
    def bulk_delete(self, ids):
        try:
            ids = [int(i) for i in ids]
            for id in ids:
                episode = PodcastEpisode.query.get(id)
                if episode:
                    try:
                        _log_audit('deleted', episode)
                    except:
                        pass
                    db.session.delete(episode)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} podcast episodes', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in PodcastEpisode bulk_delete: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error deleting podcast episodes: {str(e)}', 'error')
            return False

class GalleryImageView(AuthenticatedModelView):
    create_template = 'admin/model/create_bento.html'
    edit_template = 'admin/model/edit_bento.html'
    list_template = 'admin/gallery_list.html'
    column_list = ('id', 'name', 'event', 'photographer', 'created', 'expires_at', 'tags_display')
    column_searchable_list = ('name', 'description', 'location', 'photographer')
    column_filters = ('event', 'photographer')
    column_sortable_list = ('name', 'created', 'photographer', 'sort_order')
    column_default_sort = [('sort_order', False), ('created', True)]
    form_excluded_columns = ['id']

    form_columns = ('name', 'url', 'description', 'location', 'photographer', 'size', 'type', 'tags', 'event', 'created', 'expiration_preset', 'expiration_date')
    
    form_args = {
        'url': {
            'validators': [Optional()]
        }
    }
    form_extra_fields = {
        'url': URLField('Image URL', validators=[Optional(), URL()]),
        'tags': TextAreaField('Tags (comma-separated)', widget=TextArea()),
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
    }
    form_overrides = {'created': DateTimePickerField}

    form_widget_args = {
        'tags': {'rows': 3, 'style': 'width: 100%', 'placeholder': 'worship, fellowship, youth, etc.'},
        'url': {'placeholder': 'https://example.com/image.jpg'}
    }

    column_labels = {
        'event': 'Is Event Photo',
        'created': 'Date Added',
        'expires_at': 'Expires',
    }

    def tags_display(self, context, model, name):
        if model.tags:
            return ', '.join(model.tags) if isinstance(model.tags, list) else str(model.tags)
        return ''

    tags_display.column_type = 'string'

    def on_form_prefill(self, form, id):
        image = self.get_one(id)
        if not image:
            return
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(image, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(image, 'expires_at', None):
            form.expiration_date.data = image.expires_at

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.created or datetime.utcnow()
        model.expires_at = _compute_expires_at(preset, specific, base)
        if form.tags.data:
            # Convert comma-separated string to list
            tags = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
            model.tags = tags
    
    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected gallery images?')
    def bulk_delete(self, ids):
        try:
            ids = [int(i) for i in ids]
            for id in ids:
                image = GalleryImage.query.get(id)
                if image:
                    try:
                        _log_audit('deleted', image)
                    except:
                        pass
                    db.session.delete(image)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} gallery images', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in GalleryImage bulk_delete: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error deleting gallery images: {str(e)}', 'error')
            return False
    
    @action('toggle_event', 'Toggle Event Status', 'Are you sure you want to toggle the event status of selected images?')
    def toggle_event(self, ids):
        try:
            ids = [int(i) for i in ids]
            for id in ids:
                image = GalleryImage.query.get(id)
                if image:
                    image.event = not image.event
            db.session.commit()
            try:
                for id in ids:
                    image = GalleryImage.query.get(id)
                    if image:
                        _log_audit('edited', image)
            except:
                pass
            flash(f'Successfully toggled event status for {len(ids)} images', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in GalleryImage toggle_event: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error toggling event status: {str(e)}', 'error')
            return False

@app.route('/api/admin/reorder-gallery', methods=['POST'])
def api_admin_reorder_gallery():
    """Admin only: Save changes to gallery image display order."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    if not data or 'order' not in data:
        return jsonify({'error': 'Bad request'}), 400
        
    try:
        new_order = data['order']  # list of dicts: [{'id': id, 'sort_order': num}, ...]
        for item in new_order:
            img = GalleryImage.query.get(item.get('id'))
            if img:
                img.sort_order = item.get('sort_order', 0)
                
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        log.error("Error reordering gallery images: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/podcast-episode/<int:episode_id>/thumbnail', methods=['POST'])
def api_admin_set_podcast_episode_thumbnail(episode_id):
    """Admin only: Set podcast_thumbnail_url for a podcast episode."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    episode = PodcastEpisode.query.get(episode_id)
    if not episode:
        return jsonify({'error': 'Episode not found'}), 404
    try:
        episode.podcast_thumbnail_url = url
        db.session.commit()
        try:
            _log_audit('edited', episode)
        except:
            pass
        return jsonify({'status': 'success', 'url': url})
    except Exception as e:
        db.session.rollback()
        log.error("Error setting podcast episode thumbnail: %s", e)
        return jsonify({'error': str(e)}), 500


def _format_event_status(view, context, model, name):
    from flask import url_for
    base = url_for('event.set_status')
    publish_url = base + '?id=' + str(model.id) + '&status=publish'
    draft_url = base + '?id=' + str(model.id) + '&status=draft'
    archive_url = base + '?id=' + str(model.id) + '&status=archive'
    active = getattr(model, 'active', True)
    archived = getattr(model, 'archived', False)
    if archived:
        status_tag = '<span class="admin-status-tag admin-status-archived">Archived</span>'
    elif active:
        status_tag = '<span class="admin-status-tag admin-status-published">Published</span>'
    else:
        status_tag = '<span class="admin-status-tag admin-status-draft">Draft</span>'
    dropdown = (
        '<select class="admin-status-select" onchange="var u=this.value; if(u) window.location=u;">'
        '<option value="">Change status…</option>'
        '<option value="' + publish_url + '">Publish</option>'
        '<option value="' + draft_url + '">Revert to draft</option>'
        '<option value="' + archive_url + '">Archive</option>'
        '</select>'
    )
    return Markup('<span class="admin-status-wrap">' + status_tag + ' ' + dropdown + '</span>')


class OngoingEventView(AuthenticatedModelView):
    create_template = 'admin/model/create_bento.html'
    edit_template = 'admin/model/edit_bento.html'
    column_list = ('id', 'title', 'type', 'category', 'active', 'sort_order', 'date_entered', 'expires_at')
    column_searchable_list = ('title', 'description')
    column_filters = ('type', 'active', 'category')
    column_sortable_list = ('title', 'type', 'active', 'sort_order', 'date_entered')
    column_default_sort = ('sort_order', False)
    form_excluded_columns = ['id']
    create_template = 'admin/event_create.html'

    form_rules = [
        rules.FieldSet(('title', 'description', 'type', 'category', 'active'), 'Event Basics'),
        rules.FieldSet(('date_entered', 'expiration_preset', 'expiration_date'), 'Dates & Expiration')
    ]
    form_columns = ('date_entered', 'expiration_preset', 'expiration_date', 'title', 'description', 'type', 'category', 'active')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Optional(), Length(max=2000)]),
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
    }
    form_overrides = {
        'date_entered': DateTimePickerField,
        'type': SelectField,
        'category': SelectField,
    }
    form_widget_args = {
        'description': {'rows': 8, 'style': 'width: 100%'}
    }

    ONGOING_EVENT_TYPE_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('recurring', 'Recurring'),
        ('special', 'Special Event'),
    ]
    ONGOING_EVENT_CATEGORY_CHOICES = [
        ('worship', 'Worship'),
        ('education', 'Education'),
        ('fellowship', 'Fellowship'),
        ('missions', 'Missions'),
        ('youth', 'Youth'),
        ('children', 'Children'),
        ('prayer', 'Prayer'),
    ]
    form_args = {
        'type': {'choices': ONGOING_EVENT_TYPE_CHOICES},
        'category': {'choices': ONGOING_EVENT_CATEGORY_CHOICES},
    }

    column_labels = {
        'date_entered': 'Event date',
        'expires_at': 'Expires',
        'active': 'Status'
    }
    column_formatters = {'active': _format_event_status}

    def on_form_prefill(self, form, id):
        evt = self.get_one(id)
        if not evt:
            return
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(evt, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(evt, 'expires_at', None):
            form.expiration_date.data = evt.expires_at

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
        if request.form.get('_save_and_publish'):
            model.active = True
            model.archived = False
        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.date_entered or datetime.utcnow()
        model.expires_at = _compute_expires_at(preset, specific, base)

    @expose('set-status/', methods=['GET'])
    def set_status(self):
        if not is_authenticated():
            return redirect(url_for('admin_login'))
        id_val = request.args.get('id', type=int)
        status = request.args.get('status')
        if not id_val or status not in ('publish', 'draft', 'archive'):
            flash('Invalid request.', 'error')
            return redirect(url_for('event.index_view'))
        event = OngoingEvent.query.get(id_val)
        if not event:
            flash('Not found.', 'error')
            return redirect(url_for('event.index_view'))
        if status == 'publish':
            event.active = True
            event.archived = False
        elif status == 'draft':
            event.active = False
            event.archived = False
        else:
            event.active = False
            event.archived = True
        db.session.commit()
        try:
            _log_audit(status, event)
        except:
            pass
        flash('Status updated.', 'success')
        return redirect(url_for('event.index_view'))

    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected items?')
    def toggle_active(self, ids):
        try:
            ids = [int(i) for i in ids]
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    event.active = not event.active
            db.session.commit()
            try:
                for id in ids:
                    evt = OngoingEvent.query.get(id)
                    if evt:
                        _log_audit('edited', evt)
            except:
                pass
            flash(f'Successfully toggled active status for {len(ids)} events', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in OngoingEvent toggle_active: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error toggling active status: {str(e)}', 'error')
            return False
    
    @action('bulk_publish', 'Publish Selected', 'Are you sure you want to publish the selected events?')
    def bulk_publish(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    event.active = True
                    event.archived = False
                    count += 1
            db.session.commit()
            try:
                for id in ids:
                    evt = OngoingEvent.query.get(id)
                    if evt:
                        _log_audit('published', evt)
            except:
                pass
            flash(f'Successfully published {count} events', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in OngoingEvent bulk_publish: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error publishing events: {str(e)}', 'error')
            return False

    @action('bulk_archive', 'Archive Selected', 'Are you sure you want to archive the selected events?')
    def bulk_archive(self, ids):
        try:
            count = 0
            ids = [int(i) for i in ids]
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    event.active = False
                    event.archived = True
                    count += 1
            db.session.commit()
            try:
                for id in ids:
                    evt = OngoingEvent.query.get(id)
                    if evt:
                        _log_audit('archived', evt)
            except:
                pass
            flash(f'Successfully archived {count} events', 'success')
            return True
        except Exception as e:
            import traceback
            log.error(f"Error in OngoingEvent bulk_archive: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error archiving events: {str(e)}', 'error')
            return False

    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected events?')
    def bulk_delete(self, ids):
        try:
            for id in ids:
                event = OngoingEvent.query.get(id)
                if event:
                    try:
                        _log_audit('deleted', event)
                    except:
                        pass
                    db.session.delete(event)
            db.session.commit()
            flash(f'Successfully deleted {len(ids)} events', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting events: {str(e)}', 'error')
            return False


class TeachingSeriesOverviewView(BaseView):
    """Subpage listing all teaching series — no dropdown; single landing page with all series."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        series_list = TeachingSeries.query.order_by(
            TeachingSeries.sort_order.asc(),
            TeachingSeries.date_entered.desc()
        ).all()
        return self.render(
            'admin/teaching_series_overview.html',
            series_list=series_list,
        )


class TeachingSeriesView(AuthenticatedModelView):
    """Admin for pastor teaching series (e.g. Total Christ). Hidden from menu; use Overview page."""
    create_template = 'admin/teaching_series_create.html'
    edit_template = 'admin/teaching_series_edit.html'
    inline_models = [(TeachingSeriesSession, {
        'form_overrides': {
            'session_date': DatePickerField,
            'date_entered': DateTimePickerField
        }
    })]
    column_list = ('id', 'title', 'active', 'sort_order', 'start_date', 'end_date', 'date_entered', 'session_count')
    column_searchable_list = ('title', 'description', 'event_info')
    column_filters = ('active',)
    column_sortable_list = ('title', 'sort_order', 'start_date', 'end_date', 'date_entered')
    column_default_sort = ('sort_order', False)
    form_fieldsets = (
        ('Series Information', {'fields': ('title', 'description', 'image_url')}),
        ('Schedule & Location', {'fields': ('start_date', 'end_date', 'event_info')}),
        ('Status & Ordering', {'fields': ('active', 'sort_order', 'date_entered')}),
        ('Visibility & Expiration', {'fields': ('expiration_preset', 'expiration_date')})
    )
    form_columns = (
        'title', 'description', 'image_url', 'start_date', 'end_date', 'event_info',
        'active', 'sort_order', 'date_entered', 'expiration_preset', 'expiration_date'
    )
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Length(max=2000)]),
        'event_info': TextAreaField('Event info (when/where)', widget=TextArea(), validators=[Length(max=500)]),
        'expiration_preset': SelectField('Expiration', choices=EXPIRATION_PRESET_CHOICES, default='never'),
        'expiration_date': DatePickerField('Expiration date (when "Pick a date…" is selected)', default=None),
    }
    form_overrides = {
        'start_date': DatePickerField,
        'end_date': DatePickerField,
        'date_entered': DateTimePickerField,
    }
    form_widget_args = {
        'description': {'rows': 5, 'style': 'width: 100%'},
        'event_info': {'rows': 2, 'style': 'width: 100%', 'placeholder': 'e.g. Sundays 9am, Room 101'},
        'image_url': {'placeholder': 'https://example.com/series-image.jpg'},
    }
    column_labels = {
        'date_entered': 'Date Created',
        'event_info': 'When / Where',
        'expires_at': 'Expires',
    }

    def session_count(self, context, model, name):
        return len(model.sessions) if model.sessions else 0
    session_count.column_type = 'integer'

    def on_form_prefill(self, form, id):
        series = self.get_one(id)
        if not series:
            return
        if hasattr(form, 'expiration_preset'):
            form.expiration_preset.data = 'specific' if getattr(series, 'expires_at', None) else 'never'
        if hasattr(form, 'expiration_date') and getattr(series, 'expires_at', None):
            form.expiration_date.data = series.expires_at

    def on_model_change(self, form, model, is_created):
        preset = getattr(getattr(form, 'expiration_preset', None), 'data', None)
        specific = getattr(getattr(form, 'expiration_date', None), 'data', None)
        base = model.date_entered or datetime.utcnow()
        model.expires_at = _compute_expires_at(preset, specific, base)

    @action('toggle_active', 'Toggle Active Status', 'Are you sure you want to toggle the active status of selected teaching series?')
    def toggle_active(self, ids):
        try:
            count = 0
            for id in ids:
                series = TeachingSeries.query.get(id)
                if series:
                    series.active = not series.active
                    count += 1
            db.session.commit()
            try:
                for id in ids:
                    ser = TeachingSeries.query.get(id)
                    if ser:
                        _log_audit('edited', ser)
            except:
                pass
            flash(f'Successfully toggled active status for {count} teaching series', 'success')
            return True
        except Exception as e:
            flash(f'Error toggling active status: {str(e)}', 'error')
            return False

    @action('bulk_delete', 'Delete Selected', 'Are you sure you want to delete the selected teaching series? This will also delete all sessions within them.')
    def bulk_delete(self, ids):
        try:
            count = 0
            for id in ids:
                series = TeachingSeries.query.get(id)
                if series:
                    try:
                        _log_audit('deleted', series)
                    except:
                        pass
                    # Delete sessions first (maybe log these too? probably enough to log the series)
                    for sess in series.sessions:
                        db.session.delete(sess)
                    db.session.delete(series)
                    count += 1
            db.session.commit()
            flash(f'Successfully deleted {count} teaching series and their sessions', 'success')
            return True
        except Exception as e:
            flash(f'Error deleting teaching series: {str(e)}', 'error')
            return False

class TeachingSeriesSessionView(AuthenticatedModelView):
    """Admin for sessions (1, 2, 3...) within a teaching series; PDF upload per session."""
    column_list = ('number', 'title', 'series', 'session_date', 'pdf_url', 'date_entered')
    column_searchable_list = ('title', 'description')
    column_filters = ('series', 'session_date')
    column_sortable_list = ('number', 'title', 'session_date', 'date_entered')
    column_default_sort = ('number', True)
    form_excluded_columns = ('number',)
    form_columns = ('series', 'title', 'description', 'session_date', 'pdf_url', 'date_entered')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Length(max=2000)]),
    }
    form_overrides = {
        'date_entered': DateTimePickerField,
        'session_date': DatePickerField,
    }
    form_widget_args = {
        'description': {'rows': 4, 'style': 'width: 100%'},
        'pdf_url': {'placeholder': 'Upload PDF below or paste URL'},
    }
    column_labels = {
        'date_entered': 'Date Added',
        'pdf_url': 'PDF handout',
    }

    def on_model_change(self, form, model, is_created):
        pass  # no special handling needed, model event listener handles auto-numbering


class LifeGroupView(AuthenticatedModelView):
    """Admin CRUD for LifeGroups — small groups for prayer, teaching, fellowship, care."""
    column_list = ['name', 'leaders', 'location', 'meeting_time', 'active', 'sort_order']
    column_sortable_list = ['name', 'sort_order', 'active']
    column_default_sort = ('sort_order', False)
    column_labels = {
        'name': 'Group Name',
        'leaders': 'Leader(s)',
        'meeting_time': 'Meeting Time',
        'sort_order': 'Order',
    }
    form_columns = ['name', 'leaders', 'location', 'meeting_time', 'description', 'active', 'sort_order']
    form_widget_args = {
        'description': {'rows': 3},
        'leaders': {'placeholder': 'e.g. Craig Luekens, Allison Luekels'},
        'meeting_time': {'placeholder': 'e.g. Thursday evenings'},
        'location': {'placeholder': 'e.g. Downtown New Haven'},
    }


class PageEditorsView(BaseView):
    """Central hub for managing all editable page content — lists all pages and links to their editors."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        # Build list of pages from SUBPAGE_CONFIGS with metadata
        pages = []
        for page_key, config in SUBPAGE_CONFIGS.items():
            pages.append({
                'key': page_key,
                'title': config.get('title', ''),
                'url': config.get('url', ''),
                'icon': config.get('icon', 'edit_document'),
                'color': config.get('color', '#0052a3'),
                'num_fields': len(config.get('keys', [])),
            })

        return self.render('admin/page_editors.html', pages=pages)


class QuickAddSessionsView(BaseView):
    """Admin view for quick adding bulk sessions to a teaching series."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        import calendar
        series_id = request.args.get('series_id', type=int)
        if not series_id:
            flash('No series specified.', 'error')
            return redirect(url_for('teaching_series_overview.index'))
            
        series = TeachingSeries.query.get_or_404(series_id)
        
        if request.method == 'POST':
            num_sessions = request.form.get('num_sessions', type=int, default=5)
            start_date_str = request.form.get('start_date')
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                start_date = date.today()

            def get_last_friday(year, month):
                last_day = calendar.monthrange(year, month)[1]
                last_date = date(year, month, last_day)
                offset = (last_date.weekday() - 4) % 7
                return last_date - timedelta(days=offset)

            current_year = start_date.year
            current_month = start_date.month
            
            existing_count = len(series.sessions) if series.sessions else 0
            
            for i in range(1, num_sessions + 1):
                session_date = get_last_friday(current_year, current_month)
                sess_num = existing_count + i
                
                sess = TeachingSeriesSession(
                    series_id=series.id,
                    number=sess_num,
                    title=f'Session {sess_num}',
                    session_date=session_date
                )
                db.session.add(sess)
                
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
                    
            db.session.commit()
            try:
                _log_audit('edited', series, 'Teaching Series (Quick Sessions Add)')
            except:
                pass
            flash(f'Successfully added {num_sessions} sessions starting from {start_date.strftime("%b %Y")}.', 'success')
            return redirect(url_for('teachingseriessession.index_view', flt0_0=series.id))
            
        return self.render('admin/quick_add_sessions.html', series=series, today=date.today())


# Custom Admin Dashboard
class DashboardView(BaseView):
    def is_accessible(self):
        return is_authenticated()
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))
    
    @expose('/')
    def index(self):
        from datetime import datetime
        
        # Gamification: Calculate User XP based on AuditLog entries
        username = session.get('username')
        user_xp = 0
        if username:
            user_xp = AuditLog.query.filter_by(user=username).count()
        
        # Calculate level and next milestone
        admin_level = 1
        xp_next = 10
        if user_xp >= 500:
            admin_level = 5
            xp_next = 1000
        elif user_xp >= 100:
            admin_level = 4
            xp_next = 500
        elif user_xp >= 30:
            admin_level = 3
            xp_next = 100
        elif user_xp >= 10:
            admin_level = 2
            xp_next = 30
            
        progress_pct = min(100, int((user_xp / xp_next) * 100)) if xp_next > 0 else 100
        
        from datetime import date, timedelta
        today_d = date.today()
        stats = {
            'announcements': Announcement.query.count(),
            'active_announcements': Announcement.query.filter_by(active=True).filter_by(archived=False).count(),
            'draft_announcements': Announcement.query.filter_by(active=False).filter_by(archived=False).count(),
            'expiring_soon': Announcement.query.filter(
                Announcement.expires_at.isnot(None),
                Announcement.expires_at >= today_d,
                Announcement.expires_at <= today_d + timedelta(days=7),
            ).count(),
            'sermons': Sermon.query.count(),
            'podcast_series': PodcastSeries.query.count(),
            'podcast_episodes': PodcastEpisode.query.count(),
            'gallery_images': GalleryImage.query.count(),
            'ongoing_events': OngoingEvent.query.count(),
            'active_events': OngoingEvent.query.filter_by(active=True).count()
        }
        
        recent_announcements = Announcement.query.order_by(Announcement.date_entered.desc()).limit(5).all()
        recent_sermons = Sermon.query.order_by(Sermon.date.desc()).limit(5).all()
        today = datetime.now()
        
        # Get latest Luke chapter information
        latest_luke = None
        try:
            from sermon_data_helper import get_sermon_helper
            helper = get_sermon_helper()
            latest_luke = helper.get_latest_luke_chapter()
        except Exception as e:
            print(f"Error getting latest Luke chapter: {e}")
        
        return self.render('admin/dashboard.html', 
                         stats=stats, 
                         recent_announcements=recent_announcements,
                         recent_sermons=recent_sermons,
                         today=today,
                         latest_luke=latest_luke,
                         user_xp=user_xp,
                         admin_level=admin_level,
                         xp_next=xp_next,
                         progress_pct=progress_pct)


class ReorderSessionsView(BaseView):
    """Drag-and-drop reorder sessions for a specific series."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/', methods=['GET'])
    def index(self):
        series_id = request.args.get('series_id', type=int)
        if not series_id:
            return redirect(url_for('teaching_series_overview.index'))
        series = TeachingSeries.query.get_or_404(series_id)
        sessions = TeachingSeriesSession.query.filter_by(series_id=series_id).order_by(TeachingSeriesSession.number.asc()).all()
        return self.render('admin/reorder_sessions.html', series=series, sessions=sessions)


class ReorderEventsView(BaseView):
    """Drag-and-drop reorder events."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        events = OngoingEvent.query.order_by(OngoingEvent.sort_order.asc(), OngoingEvent.date_entered.desc()).all()
        return self.render('admin/reorder_events.html', events=events)


class BannerAlertView(BaseView):
    """Manage top-bar banner alerts: list, reorder, edit expiration; link to create new."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        banners = Announcement.query.filter_by(show_in_banner=True)\
            .order_by(Announcement.banner_sort_order.asc(), Announcement.date_entered.desc()).all()
        return self.render('admin/banner_manage.html', banners=banners, now=date.today())


class PodcastThumbnailsView(BaseView):
    """Upload and manage podcast thumbnails — list all podcasts (series + episodes) with gallery-style upload to GCS."""
    def is_accessible(self):
        return 'username' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        series_list = PodcastSeries.query.order_by(PodcastSeries.title.asc()).all()
        # Load episodes per series (ordered by date_added desc)
        for s in series_list:
            s._episodes = (
                PodcastEpisode.query.filter_by(series_id=s.id)
                .order_by(PodcastEpisode.date_added.desc(), PodcastEpisode.number.desc())
                .all()
            )
        return self.render('admin/podcast_thumbnails.html', series_list=series_list)


class BackupGalleryView(BaseView):
    """Download all gallery images as a ZIP file."""
    def is_accessible(self):
        return 'username' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        images = GalleryImage.query.all()
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img in images:
                if img.url:
                    try:
                        # Fetch the image content
                        response = requests.get(img.url, timeout=10)
                        if response.status_code == 200:
                            # Generate a safe filename
                            filename = img.name or f"image_{img.id}"
                            ext = img.url.split('.')[-1]
                            if len(ext) > 4 or '/' in ext:
                                ext = 'jpg'
                            if not filename.endswith(f".{ext}"):
                                filename = f"{filename}.{ext}"
                                
                            # Safe filename string
                            safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in [' ', '.', '_']]).rstrip()
                            if not safe_name:
                                safe_name = f"image_{img.id}.{ext}"
                                
                            zf.writestr(safe_name, response.content)
                    except Exception as e:
                        log.error(f"Failed to backup image {img.id} ({img.url}): {e}")
                        
        memory_file.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return Response(
            memory_file.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": f"attachment;filename=cpc_gallery_backup_{timestamp}.zip"}
        )

class HistoryView(BaseView):
    """Admin audit-log / history view — see who added, edited, or deleted content."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        page = request.args.get('page', 1, type=int)
        per_page = 50
        action_filter = request.args.get('action', '')
        type_filter = request.args.get('type', '')
        user_filter = request.args.get('user', '')

        logs = []
        pagination = None
        all_actions = []
        all_types = []
        all_users = []
        history_error = None

        try:
            query = AuditLog.query.order_by(AuditLog.timestamp.desc())

            if action_filter:
                query = query.filter(AuditLog.action == action_filter)
            if type_filter:
                query = query.filter(AuditLog.entity_type == type_filter)
            if user_filter:
                query = query.filter(AuditLog.user == user_filter)

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            logs = pagination.items

            all_actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all() if r[0]]
            all_types = [r[0] for r in db.session.query(AuditLog.entity_type).distinct().all() if r[0]]
            all_users = [r[0] for r in db.session.query(AuditLog.user).distinct().all() if r[0]]
        except Exception as e:
            history_error = str(e)
            log.warning("Activity history query failed: %s", e)
            try:
                db.session.rollback()
            except Exception:
                pass

        return self.render(
            'admin/history.html',
            logs=logs,
            pagination=pagination,
            action_filter=action_filter,
            type_filter=type_filter,
            user_filter=user_filter,
            all_actions=sorted(all_actions),
            all_types=sorted(all_types),
            all_users=sorted(all_users),
            history_error=history_error,
        )


# ---------------------------------------------------------------------------
# Unified content list — events, announcements, banners in one list by month
# ---------------------------------------------------------------------------
class ContentFeedView(BaseView):
    """Single list of all content (events, announcements, banners) grouped by month."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        type_filter = request.args.get('type', '')  # '' | 'announcement' | 'event' | 'banner'
        items = []

        for ann in Announcement.query.order_by(Announcement.date_entered.desc()).all():
            dt = ann.date_entered or datetime.utcnow()
            content_type = 'Banner' if getattr(ann, 'show_in_banner', False) else 'Announcement'
            items.append({
                'date': dt,
                'title': ann.title or '—',
                'content_type': content_type,
                'active': getattr(ann, 'active', True),
                'archived': getattr(ann, 'archived', False),
                'edit_url': url_for('announcement.edit_view', id=ann.id),
                'id': ann.id,
            })

        for ev in OngoingEvent.query.order_by(OngoingEvent.date_entered.desc()).all():
            dt = ev.date_entered or datetime.utcnow()
            items.append({
                'date': dt,
                'title': ev.title or '—',
                'content_type': 'Event',
                'active': getattr(ev, 'active', True),
                'archived': getattr(ev, 'archived', False),
                'edit_url': url_for('event.edit_view', id=ev.id),
                'id': ev.id,
            })

        if type_filter:
            type_map = {'announcement': 'Announcement', 'event': 'Event', 'banner': 'Banner'}
            want = type_map.get(type_filter.lower())
            if want:
                items = [i for i in items if i['content_type'] == want]

        # Robust sort in case some dates are strings or Naive vs Aware
        def safe_sort_key(x):
            d = x['date']
            if not d:
                return datetime.min
            if isinstance(d, str):
                try:
                    from dateutil.parser import parse
                    d = parse(d)
                except Exception:
                    return datetime.min
            # ensure naive so we can sort without offset timezone crash
            return d.replace(tzinfo=None)

        items.sort(key=safe_sort_key, reverse=True)

        # Group by (year, month), label e.g. "March 2025"
        months = []
        current_key = None
        current_list = None
        for i in items:
            dt = i['date']
            if isinstance(dt, str):
                try:
                    from dateutil.parser import parse
                    dt = parse(dt)
                except Exception:
                    dt = datetime.utcnow()
            elif not hasattr(dt, 'year'):
                dt = datetime.utcnow()
                
            i['date'] = dt
            key = (dt.year, dt.month)
            if key != current_key:
                current_key = key
                month_label = dt.strftime('%B %Y')
                current_list = []
                months.append({'label': month_label, 'items': current_list})
            current_list.append(i)

        return self.render(
            'admin/content_feed.html',
            months=months,
            type_filter=type_filter,
        )


# ---------------------------------------------------------------------------
# Live content snapshot — what is in the DB right now (e.g. on Render)
# ---------------------------------------------------------------------------
class LiveContentView(BaseView):
    """Show what is presently live in the database: counts and full announcements list with versioning."""
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        counts = {
            'announcements': Announcement.query.count(),
            'announcements_active': Announcement.query.filter_by(active=True).filter_by(archived=False).count(),
            'announcements_banner': Announcement.query.filter_by(show_in_banner=True).count(),
            'events': OngoingEvent.query.count(),
            'events_active': OngoingEvent.query.filter_by(active=True).count(),
            'sermons': Sermon.query.count(),
            'podcast_series': PodcastSeries.query.count(),
            'podcast_episodes': PodcastEpisode.query.count(),
            'gallery_images': GalleryImage.query.count(),
            'teaching_series': TeachingSeries.query.count(),
        }
        announcements = Announcement.query.order_by(Announcement.date_entered.desc()).all()
        return self.render(
            'admin/live_content.html',
            counts=counts,
            announcements=announcements,
        )


# Protected index view — redirect /admin/ to login or dashboard
class ProtectedAdminIndexView(_AdminIndexView):
    def is_accessible(self):
        return is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    @expose('/')
    def index(self):
        return redirect(url_for('dashboard.index'))

# Setup admin with enhanced organization
admin = Admin(app, name='CPC Admin', template_mode='bootstrap3',
              index_view=ProtectedAdminIndexView())

# ---------------------------------------------------------------------------
# Initialize database, verify connection, run migrations, seed admin users
# ---------------------------------------------------------------------------
with app.app_context():
    from sqlalchemy import text

    # 1. Verify the database is reachable
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("DB connection verified — SELECT 1 OK")
    except Exception as exc:
        log.critical("DB connection FAILED: %s", exc)
        raise RuntimeError(
            f"Cannot connect to database. Check DATABASE_URL. Error: {exc}"
        ) from exc

    # 2. Create any missing tables
    db.create_all()
    log.info("DB schema ready — db.create_all() complete")

    # 3. Add any columns that were added after the table was first created
    ensure_db_columns()
    log.info("DB column migrations complete")

    # 3b. Stamp Alembic version if not yet tracked (one-time baseline)
    from alembic.migration import MigrationContext
    alembic_ctx = MigrationContext.configure(db.engine.connect())
    if alembic_ctx.get_current_revision() is None:
        from flask_migrate import stamp
        stamp(revision='head')
        log.info("Alembic baseline stamped (first run)")

    # 4. Ensure the global ID counter row exists
    if not GlobalIDCounter.query.first():
        db.session.add(GlobalIDCounter(id=1, next_id=1))
        db.session.commit()

    # 5. Seed admin users
    init_admin_users()
    # 6. Sample pastor teaching series (Total Christ) if none exist
    if TeachingSeries.query.count() == 0:
        _seed_pastor_teaching_sample()
        log.info("Sample teaching series 'Total Christ' created")
    log.info("DB init complete — app is ready to serve")

    # 7. Register admin views (inside app context so get_form() can use DB)
    admin.add_view(DashboardView(name='Dashboard', endpoint='dashboard'))
    admin.add_view(AnnouncementView(Announcement, db.session, name='Announcements', endpoint='announcement'))
    admin.add_view(OngoingEventView(OngoingEvent, db.session, name='Events', endpoint='event'))
    admin.add_view(SermonView(Sermon, db.session, name='Sunday Sermons', endpoint='sermon'))
    admin.add_view(PodcastEpisodeView(PodcastEpisode, db.session, name='Podcasts', endpoint='podcastepisode'))
    admin.add_view(PaperView(Paper, db.session, name='Papers & Bulletins', endpoint='paper', category='More'))
    admin.add_view(GalleryImageView(GalleryImage, db.session, name='Gallery', endpoint='galleryimage', category='More'))
    admin.add_view(BannerAlertView(name='Banner Alerts', endpoint='banner_alerts', category='More'))
    admin.add_view(HistoryView(name='Activity History', endpoint='history', category='More'))
    admin.add_view(BackupGalleryView(name='Backup all media', endpoint='backup_gallery', category='More'))
    admin.add_view(PodcastThumbnailsView(name='Podcast Thumbnails', endpoint='podcast_thumbnails', category='More'))
    admin.add_view(UserView(User, db.session, name='Users', endpoint='user', category='More'))
    admin.add_view(TeachingSeriesView(TeachingSeries, db.session, name='Teaching Series', endpoint='teachingseries', category='More'))
    admin.add_view(TeachingSeriesSessionView(TeachingSeriesSession, db.session, name='Teaching Sessions', endpoint='teachingsession', category='More'))
    admin.add_view(LifeGroupView(LifeGroup, db.session, name='Life Groups', endpoint='lifegroups_admin', category='More'))
    admin.add_view(PageEditorsView(name='Page Editors', endpoint='page_editors'))

if __name__ == '__main__':
    # Use one port for both main and reloader (so URL doesn't change after restart)
    try:
        port = os.environ.get('FLASK_APP_PORT')
        if port is not None:
            port = int(port)
        else:
            port = find_available_port()
            os.environ['FLASK_APP_PORT'] = str(port)
        print(f"Starting Flask app on port {port}")
        print(f"Main site: http://localhost:{port}")
        print(f"Admin panel: http://localhost:{port}/admin")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, port=port, host='0.0.0.0')
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please free up a port or try running the app again.")
        exit(1)
