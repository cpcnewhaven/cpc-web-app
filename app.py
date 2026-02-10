import warnings
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response, session
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
from enhanced_api import enhanced_api
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

# Configuration
app.config.from_object('config')
cache = Cache(app)

app.register_blueprint(enhanced_api, url_prefix='/api')
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

# Connection-pool tuning (PostgreSQL) — recycle connections before the
# server-side 5-min idle timeout, and keep a small pool for the free tier.
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 3,
    'max_overflow': 2,
    'pool_recycle': 270,      # recycle before PG's idle timeout
    'pool_pre_ping': True,    # test connections before handing them out
}

# Log DB type + host (NEVER log the full URL — it contains credentials)
try:
    from urllib.parse import urlparse
    _parsed = urlparse(database_url)
    _db_kind = _parsed.scheme.split('+')[0]       # "postgresql" or "sqlite"
    _db_host = _parsed.hostname or 'localhost'
    _db_name = _parsed.path.lstrip('/')
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
from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent, Paper, User, GlobalIDCounter, next_global_id, AuditLog

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
            ('featured_image', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('image_display_type', 'VARCHAR(50)', 'VARCHAR(50)'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
            ('author', 'VARCHAR(200)', 'VARCHAR(200)'),
        ],
        'ongoing_events': [
            ('sort_order', 'INTEGER DEFAULT 0', 'INTEGER DEFAULT 0'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
        ],
        'sermons': [
            ('active', 'BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE'),
            ('archived', 'BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE'),
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
# Admin status: last content change across all tables
# ---------------------------------------------------------------------------
@app.route('/api/admin/last-change')
def api_admin_last_change():
    """Return the single most-recent content change (for the admin status bar)."""
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
    return render_template('events.html')

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/highlights')
def highlights():
    return render_template('highlights.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/sundays')
def sundays():
    return render_template('sundays.html')

@app.route('/plan-a-vist')
def plan_a_vist():
    return render_template('plan-a-vist.html')

@app.route('/give')
def give():
    return render_template('give.html')

# Liquid glass demo moved to possiblyDELETE folder
# @app.route('/liquid-glass-demo')
# def liquid_glass_demo():
#     return render_template('liquid_glass_demo.html')

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/media')
def media():
    return render_template('media.html')

@app.route('/gallery')
def gallery():
    return redirect(url_for('media'))

@app.route('/yearbook')
def yearbook():
    return redirect(url_for('media'))

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

@app.route('/teaching-series')
def teaching_series():
    """Teaching series page showing sermon series and Sunday school series"""
    return render_template('teaching-series.html')

@app.route('/api/teaching-series')
def api_teaching_series():
    """API endpoint for teaching series - sermon series and Sunday school series with enhanced metadata"""
    try:
        from sermon_data_helper import get_sermon_helper
        helper = get_sermon_helper()
        sermons = helper.get_all_sermons()
    except ImportError:
        # Fallback to old method
        import json
        with open('data/sermons.json', 'r') as f:
            sermons_data = json.load(f)
        sermons = sermons_data.get('sermons', [])
    
    # Extract unique sermon series (excluding "The Sunday Sermon" as it's the default)
    sermon_series = {}
    sunday_school_series = {}
    all_authors = set()
    all_scriptures = set()
    all_tags = set()
    date_range = {'min': None, 'max': None}
    
    for sermon in sermons:
        series_name = sermon.get('series', '')
        title = sermon.get('title', '')
        author = sermon.get('author', '')
        scripture = sermon.get('scripture', '')
        date = sermon.get('date', '')
        tags = sermon.get('tags', [])
        
        # Collect metadata
        if author:
            all_authors.add(author)
        if scripture:
            all_scriptures.add(scripture)
        if tags:
            if isinstance(tags, list):
                all_tags.update(tags)
            else:
                all_tags.add(str(tags))
        
        # Track date range
        if date:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                if date_range['min'] is None or date_obj < date_range['min']:
                    date_range['min'] = date_obj
                if date_range['max'] is None or date_obj > date_range['max']:
                    date_range['max'] = date_obj
            except:
                pass
        
        sermon_data = {
            'id': sermon.get('id'),
            'title': sermon.get('title'),
            'author': author,
            'date': date,
            'scripture': scripture,
            'link': sermon.get('link') or sermon.get('spotify_url') or sermon.get('youtube_url'),
            'spotify_url': sermon.get('spotify_url'),
            'youtube_url': sermon.get('youtube_url'),
            'apple_podcasts_url': sermon.get('apple_podcasts_url'),
            'tags': tags if isinstance(tags, list) else [tags] if tags else [],
            'sermon_type': sermon.get('sermon_type', 'sermon'),
            'search_keywords': sermon.get('search_keywords', '')
        }
        
        # Check if it's a Sunday School series
        if 'Sunday School' in series_name or 'Sunday School' in title or 'The Sunday School' in title:
            if series_name and series_name not in sunday_school_series:
                sunday_school_series[series_name] = {
                    'name': series_name,
                    'count': 0,
                    'sermons': [],
                    'authors': set(),
                    'date_range': {'min': None, 'max': None},
                    'scriptures': set()
                }
            if series_name in sunday_school_series:
                sunday_school_series[series_name]['count'] += 1
                sunday_school_series[series_name]['sermons'].append(sermon_data)
                if author:
                    sunday_school_series[series_name]['authors'].add(author)
                if scripture:
                    sunday_school_series[series_name]['scriptures'].add(scripture)
                if date:
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        s_range = sunday_school_series[series_name]['date_range']
                        if s_range['min'] is None or date_obj < s_range['min']:
                            s_range['min'] = date_obj
                        if s_range['max'] is None or date_obj > s_range['max']:
                            s_range['max'] = date_obj
                    except:
                        pass
        # Regular sermon series (exclude default "The Sunday Sermon")
        elif series_name and series_name != 'The Sunday Sermon' and series_name not in ['', None]:
            if series_name not in sermon_series:
                sermon_series[series_name] = {
                    'name': series_name,
                    'count': 0,
                    'sermons': [],
                    'authors': set(),
                    'date_range': {'min': None, 'max': None},
                    'scriptures': set()
                }
            sermon_series[series_name]['count'] += 1
            sermon_series[series_name]['sermons'].append(sermon_data)
            if author:
                sermon_series[series_name]['authors'].add(author)
            if scripture:
                sermon_series[series_name]['scriptures'].add(scripture)
            if date:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    s_range = sermon_series[series_name]['date_range']
                    if s_range['min'] is None or date_obj < s_range['min']:
                        s_range['min'] = date_obj
                    if s_range['max'] is None or date_obj > s_range['max']:
                        s_range['max'] = date_obj
                except:
                    pass
    
    # Convert sets to lists and format date ranges
    def format_series(series_dict):
        result = []
        for name, data in series_dict.items():
            series_item = {
                'name': name,
                'count': data['count'],
                'sermons': data['sermons'],
                'authors': sorted(list(data['authors'])),
                'scriptures': sorted(list(data['scriptures']))[:10],  # Limit to 10 for display
                'date_range': {
                    'min': data['date_range']['min'].strftime('%Y-%m-%d') if data['date_range']['min'] else None,
                    'max': data['date_range']['max'].strftime('%Y-%m-%d') if data['date_range']['max'] else None
                }
            }
            result.append(series_item)
        return result
    
    sermon_series_list = format_series(sermon_series)
    sunday_school_series_list = format_series(sunday_school_series)
    
    # Sort sermons within each series by date (newest first)
    for series in sermon_series_list:
        series['sermons'].sort(key=lambda x: x.get('date', ''), reverse=True)
    for series in sunday_school_series_list:
        series['sermons'].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Merge curated teaching series (e.g. "What We Believe") from config for long-term data use
    _curated_path = os.path.join(os.path.dirname(__file__), 'data', 'teaching_series_config.json')
    if os.path.exists(_curated_path):
        try:
            with open(_curated_path, 'r', encoding='utf-8') as f:
                curated_config = json.load(f)
            for curated in curated_config.get('curated_series', []):
                name = curated.get('name')
                if not name:
                    continue
                existing = next((s for s in sermon_series_list if s['name'] == name), None)
                if existing:
                    if curated.get('description') is not None:
                        existing['description'] = curated['description']
                    if curated.get('external_url') is not None:
                        existing['external_url'] = curated['external_url']
                    if curated.get('slug') is not None:
                        existing['slug'] = curated['slug']
                else:
                    sermon_series_list.append({
                        'name': name,
                        'count': 0,
                        'sermons': [],
                        'authors': [],
                        'scriptures': [],
                        'date_range': {'min': None, 'max': None},
                        'description': curated.get('description', ''),
                        'external_url': curated.get('external_url', ''),
                        'slug': curated.get('slug', ''),
                    })
            # Sort so curated series (with sort_order) appear first; preserve order otherwise
            def _series_sort_key(s):
                idx = next((i for i, c in enumerate(curated_config.get('curated_series', [])) if c.get('name') == s['name']), None)
                return (0, idx) if idx is not None else (1, 0)
            sermon_series_list.sort(key=_series_sort_key)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Convert date range for response
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
            'all_authors': sorted(list(all_authors)),
            'all_scriptures': sorted(list(all_scriptures))[:50],  # Top 50 for filter
            'all_tags': sorted(list(all_tags)),
            'date_range': date_range_response
        }
    })

# API Routes
@app.route('/api/announcements')
@cache.cached(timeout=60)
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
                'showInBanner': getattr(a, 'show_in_banner', False),
                'featuredImage': a.featured_image,
                'imageDisplayType': a.image_display_type
            } for a in announcements
        ]
    })


@app.route('/api/banner-announcements')
@cache.cached(timeout=60)
def api_banner_announcements():
    """Active announcements marked to show in the top yellow bar (weather, parking, etc.)"""
    announcements = Announcement.query.filter_by(active=True, show_in_banner=True)\
        .order_by(Announcement.date_entered.desc()).all()
    return jsonify({
        'announcements': [
            {
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'type': a.type or 'announcement',
            } for a in announcements
        ]
    })

@app.route('/api/highlights')
@cache.cached(timeout=60)
def api_highlights():
    """API endpoint for highlights data - pulls from database"""
    # Get all announcements from database (not just active ones, for filtering on highlights page)
    announcements = Announcement.query.order_by(Announcement.date_entered.desc()).all()
    
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
                'imageDisplayType': a.image_display_type
            } for a in announcements
        ]
    })

@app.route('/api/ongoing-events')
@cache.cached(timeout=60)
def api_ongoing_events():
    """API endpoint for ongoing events (ordered by sort_order, then date)"""
    events = OngoingEvent.query.filter_by(active=True)\
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
            'author': bulletin.author,
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
            'author': latest.author,
            'file_url': latest.file_url,
            'date_published': latest.date_published.isoformat() if latest.date_published else None,
            'date_entered': latest.date_entered.strftime('%Y-%m-%d') if latest.date_entered else None,
        })
    return jsonify({})

@app.route('/api/sermons')
@cache.cached(timeout=120)
def api_sermons():
    """Sunday Sermons API: DB sermons (published) first, then JSON fallback."""
    episodes = []
    # 1. Published sermons from admin (Sunday Sermons)
    try:
        db_sermons = Sermon.query.filter(
            Sermon.active == True,
            Sermon.archived == False
        ).order_by(Sermon.date.desc()).all()
        for s in db_sermons:
            episodes.append({
                'id': s.id,
                'title': s.title or '',
                'author': s.author or '',
                'scripture': s.scripture or '',
                'date': s.date.strftime('%Y-%m-%d') if s.date else '',
                'spotify_url': s.spotify_url or '',
                'youtube_url': s.youtube_url or '',
                'apple_podcasts_url': s.apple_podcasts_url or '',
                'link': s.spotify_url or s.youtube_url or s.apple_podcasts_url or '',
                'podcast-thumbnail_url': s.podcast_thumbnail_url or ''
            })
    except Exception as e:
        print(f"Error loading DB sermons: {e}")
    # 2. If no DB sermons, use JSON (sermon_data_helper)
    if not episodes:
        try:
            from sermon_data_helper import get_sermon_helper
            helper = get_sermon_helper()
            metadata = helper.get_metadata()
            sermons = helper.get_all_sermons()
            for sermon in sermons:
                episodes.append({
                    'id': sermon.get('id', ''),
                    'title': sermon.get('title', ''),
                    'author': sermon.get('author', ''),
                    'scripture': sermon.get('scripture', ''),
                    'date': sermon.get('date', ''),
                    'spotify_url': sermon.get('spotify_url', ''),
                    'youtube_url': sermon.get('youtube_url', ''),
                    'apple_podcasts_url': sermon.get('apple_podcasts_url', ''),
                    'link': sermon.get('link', ''),
                    'podcast-thumbnail_url': sermon.get('podcast_thumbnail_url', '')
                })
            return jsonify({
                'title': metadata.get('title', 'Sunday Sermons'),
                'description': metadata.get('description', 'Weekly sermons from our Sunday worship services'),
                'episodes': episodes
            })
        except Exception as e:
            print(f"Error loading sermons: {e}")
    return jsonify({
        'title': 'Sunday Sermons',
        'description': 'Weekly sermons from our Sunday worship services',
        'episodes': episodes
    })

@app.route('/api/podcasts/beyond-podcast')
def api_beyond_podcast():
    """API endpoint for Beyond the Sunday Sermon podcast"""
    # Redirect to JSON API
    from flask import redirect
    return redirect('/api/json/podcasts/beyond-podcast')

@app.route('/api/podcasts/biblical-interpretation')
def api_biblical_interpretation():
    """API endpoint for Biblical Interpretation series"""
    # Redirect to JSON API
    from flask import redirect
    return redirect('/api/json/podcasts/biblical-interpretation')

@app.route('/api/podcasts/confessional-theology')
def api_confessional_theology():
    """API endpoint for Confessional Theology series"""
    # Redirect to JSON API
    from flask import redirect
    return redirect('/api/json/podcasts/confessional-theology')

@app.route('/api/podcasts/membership-seminar')
def api_membership_seminar():
    """API endpoint for Membership Seminar series"""
    # Redirect to JSON API
    from flask import redirect
    return redirect('/api/json/podcasts/membership-seminar')

@app.route('/api/gallery')
def api_gallery():
    """API endpoint for image gallery with enhanced metadata"""
    # Try to load from JSON first (for existing data)
    try:
        import json
        with open('data/gallery.json', 'r') as f:
            json_data = json.load(f)
        
        # Enhance JSON data with better metadata
        enhanced_images = []
        for img in json_data:
            # Parse date from created field or use current date
            created_date = None
            if img.get('created') and img['created'] != 'Unknown':
                try:
                    created_date = datetime.strptime(img['created'], '%Y-%m-%d')
                except:
                    created_date = datetime.now()
            else:
                created_date = datetime.now()
            
            enhanced_img = {
                'id': img.get('id', ''),
                'name': img.get('name', 'Untitled'),
                'url': img.get('url', ''),
                'size': img.get('size', 'Unknown'),
                'type': img.get('type', 'image/jpeg'),
                'created': created_date.strftime('%Y-%m-%d'),
                'created_timestamp': created_date.isoformat(),
                'tags': img.get('tags', []),
                'event': img.get('event', False),
                'description': img.get('description', ''),
                'location': img.get('location', ''),
                'photographer': img.get('photographer', ''),
                'category': img.get('category', 'general')
            }
            enhanced_images.append(enhanced_img)
        
        return jsonify({
            'images': enhanced_images,
            'total': len(enhanced_images),
            'source': 'json'
        })
        
    except Exception as e:
        print(f"Error loading gallery from JSON: {e}")
        # Fallback to database
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
                    'created_timestamp': img.created.isoformat() if img.created else None,
                    'tags': img.tags,
                    'event': img.event,
                    'description': getattr(img, 'description', ''),
                    'location': getattr(img, 'location', ''),
                    'photographer': getattr(img, 'photographer', ''),
                    'category': getattr(img, 'category', 'general')
                } for img in images
            ],
            'total': len(images),
            'source': 'database'
        })

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
        return {"error": "EVENTS_ICS_URL not configured"}
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
    """Unified search endpoint that searches across all content types"""
    query = request.args.get('q', '').strip().lower()
    content_type = request.args.get('type', 'all')  # all, sermons, podcasts, announcements, events, gallery
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    results = {
        'query': query,
        'type': content_type,
        'results': [],
        'total': 0,
        'page': page,
        'per_page': per_page,
        'pages': 0
    }
    
    if not query:
        return jsonify(results)
    
    try:
        # Search sermons
        if content_type in ['all', 'sermons']:
            try:
                with open('data/sermons.json', 'r', encoding='utf-8') as f:
                    sermons_data = json.load(f)
                    for sermon in sermons_data.get('sermons', []):
                        # Search across multiple fields
                        search_fields = [
                            sermon.get('title', ''),
                            sermon.get('author', ''),
                            sermon.get('scripture', ''),
                            sermon.get('series', ''),
                            sermon.get('sermon_type', ''),
                            ', '.join(sermon.get('tags', [])) if isinstance(sermon.get('tags'), list) else ''
                        ]
                        search_text = ' '.join([str(f) for f in search_fields if f]).lower()
                        if query in search_text:
                            results['results'].append({
                                'type': 'sermon',
                                'title': sermon.get('title'),
                                'description': sermon.get('scripture', '') or sermon.get('series', ''),
                                'author': sermon.get('author'),
                                'date': sermon.get('date'),
                                'series': sermon.get('series', ''),
                                'url': sermon.get('link') or sermon.get('spotify_url') or sermon.get('youtube_url') or sermon.get('apple_podcasts_url'),
                                'thumbnail': sermon.get('podcast_thumbnail_url')
                            })
            except FileNotFoundError:
                pass  # Sermons file not found, skip
        
        # Search announcements
        if content_type in ['all', 'announcements']:
            announcements = Announcement.query.filter(
                db.or_(
                    Announcement.title.ilike(f'%{query}%'),
                    Announcement.description.ilike(f'%{query}%'),
                    Announcement.category.ilike(f'%{query}%'),
                    Announcement.tag.ilike(f'%{query}%')
                )
            ).all()
            for a in announcements:
                results['results'].append({
                    'type': 'announcement',
                    'title': a.title,
                    'description': a.description[:200] if a.description else '',
                    'date': a.date_entered.strftime('%Y-%m-%d') if a.date_entered else None,
                    'category': a.category,
                    'tag': a.tag,
                    'url': url_for('announcements')
                })
        
        # Search podcasts
        if content_type in ['all', 'podcasts']:
            from sqlalchemy import or_
            conditions = [PodcastEpisode.title.ilike(f'%{query}%')]
            # Only add guest/scripture conditions if those fields exist
            try:
                conditions.append(or_(
                    PodcastEpisode.guest.ilike(f'%{query}%'),
                    PodcastEpisode.scripture.ilike(f'%{query}%')
                ))
            except:
                pass  # Fields might not exist
            
            episodes = PodcastEpisode.query.filter(or_(*conditions)).all()
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
            events = OngoingEvent.query.filter(
                db.or_(
                    OngoingEvent.title.ilike(f'%{query}%'),
                    OngoingEvent.description.ilike(f'%{query}%')
                )
            ).all()
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
            images = GalleryImage.query.filter(
                GalleryImage.name.ilike(f'%{query}%')
            ).all()
            for img in images:
                results['results'].append({
                    'type': 'gallery',
                    'title': img.name,
                    'description': ', '.join(img.tags) if img.tags else '',
                    'date': img.created.strftime('%Y-%m-%d') if img.created else None,
                    'url': img.url,
                    'thumbnail': img.url
                })
        
        # Search papers
        if content_type in ['all', 'papers']:
            papers = Paper.query.filter(
                db.or_(
                    Paper.title.ilike(f'%{query}%'),
                    Paper.author.ilike(f'%{query}%') if Paper.author else False,
                    Paper.description.ilike(f'%{query}%') if Paper.description else False
                )
            ).all()
            for p in papers:
                results['results'].append({
                    'type': 'paper',
                    'title': p.title,
                    'author': p.author,
                    'description': p.description[:200] if p.description else '',
                    'date': p.date_published.strftime('%Y-%m-%d') if p.date_published else (p.date_entered.strftime('%Y-%m-%d') if p.date_entered else None),
                    'category': p.category,
                    'url': p.file_url
                })
        
        # Sort by date descending
        results['results'].sort(key=lambda x: x.get('date', ''), reverse=True)
        results['total'] = len(results['results'])
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        results['results'] = results['results'][start:end]
        results['page'] = page
        results['per_page'] = per_page
        results['pages'] = (results['total'] + per_page - 1) // per_page
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify(results)

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
        # Get old sermons
        if content_type in ['all', 'sermons']:
            try:
                from sermon_data_helper import get_sermon_helper
                helper = get_sermon_helper()
                archive_sermons = helper.get_archive_sermons(cutoff_days=90)
                
                for sermon in archive_sermons:
                    sermon_date = sermon.get('date')
                    if sermon_date:
                        # Filter by year if specified
                        if not year or sermon_date.startswith(str(year)):
                            results['items'].append({
                                'type': 'sermon',
                                'title': sermon.get('title'),
                                'author': sermon.get('author'),
                                'date': sermon_date,
                                'url': sermon.get('link') or sermon.get('spotify_url') or sermon.get('youtube_url') or sermon.get('apple_podcasts_url'),
                                'scripture': sermon.get('scripture', ''),
                                'series': sermon.get('series', ''),
                                'description': f"{sermon.get('scripture', '')} - {sermon.get('series', '')}".strip(' - ')
                            })
            except ImportError:
                # Fallback to old method
                with open('data/sermons.json', 'r') as f:
                    sermons_data = json.load(f)
                cutoff_date = datetime.now() - timedelta(days=90)
                
                for sermon in sermons_data.get('sermons', []):
                    sermon_date = sermon.get('date')
                    if sermon_date:
                        try:
                            serm_dt = datetime.strptime(sermon_date, '%Y-%m-%d')
                            is_archive = sermon.get('source') == 'archive'
                            if serm_dt < cutoff_date or is_archive:
                                if not year or sermon_date.startswith(str(year)):
                                    results['items'].append({
                                        'type': 'sermon',
                                        'title': sermon.get('title'),
                                        'author': sermon.get('author'),
                                        'date': sermon_date,
                                        'url': sermon.get('link') or sermon.get('spotify_url') or sermon.get('youtube_url') or sermon.get('apple_podcasts_url'),
                                        'scripture': sermon.get('scripture', ''),
                                        'series': sermon.get('series', ''),
                                        'description': f"{sermon.get('scripture', '')} - {sermon.get('series', '')}".strip(' - ')
                                    })
                        except:
                            pass
        
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
                    'author': p.author,
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

def is_authenticated():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

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
    
    return jsonify({'success': False, 'error': 'Invalid action'})

@app.route('/admin/banner-alert/new')
@require_auth
def admin_banner_alert_new():
    return redirect(url_for('announcement.create_view', banner=1))

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

# Enhanced Admin Interface
from flask_admin import BaseView, expose
from flask_admin.actions import action
from wtforms import TextAreaField, SelectField, BooleanField, StringField, DateField, URLField
from wtforms.validators import DataRequired, URL, Length, Optional
import re
from wtforms.widgets import TextArea, Select
from datetime import datetime

# ---------------------------------------------------------------------------
# Audit-log helper
# ---------------------------------------------------------------------------
def _log_audit(action, model, entity_type=None):
    """Write one row to the audit_log table.

    ``model`` is the SQLAlchemy instance being created/edited/deleted.
    ``action`` is one of 'created', 'edited', 'deleted'.
    """
    try:
        username = session.get('username', 'unknown')
        etype = entity_type or model.__class__.__name__
        eid = getattr(model, 'id', None)
        etitle = (getattr(model, 'title', None)
                  or getattr(model, 'name', None)
                  or str(eid))
        entry = AuditLog(
            user=username,
            action=action,
            entity_type=etype,
            entity_id=eid,
            entity_title=str(etitle)[:300] if etitle else None,
        )
        db.session.add(entry)
        # Don't commit here — the caller (Flask-Admin) manages the session.
    except Exception as exc:
        log.warning("Audit log write failed: %s", exc)


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

# Choices for announcement type/category — use form_args + form_overrides so we get
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
    return Markup('<span class="admin-status-wrap">' + ' '.join(tags) + '</span>')


class AnnouncementView(AuthenticatedModelView):
    column_list = ('id', 'title', 'author', 'type', 'category', 'active', 'show_in_banner', 'superfeatured', 'date_entered')
    column_searchable_list = ('title', 'description', 'tag', 'author')
    column_filters = ('type', 'active', 'tag', 'superfeatured', 'show_in_banner', 'category')
    column_sortable_list = ('title', 'type', 'active', 'superfeatured', 'date_entered', 'author')
    column_default_sort = ('date_entered', True)
    # Exclude id from create form so we set it in on_model_change (next_global_id)
    form_excluded_columns = ['id', 'date_entered']

    form_columns = ('title', 'description', 'type', 'category', 'tag', 'author', 'active', 'show_in_banner', 'banner_type', 'superfeatured', 'featured_image', 'image_display_type')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[DataRequired(), Length(max=2000)]),
        'banner_type': SelectField(
            'Top bar banner',
            choices=[
                ('', 'No banner'),
                ('weather', 'Weather'),
                ('parking', 'Parking'),
                ('alert', 'Alert'),
                ('info', 'Info')
            ]
        )
    }

    # Use wtforms SelectField (not Flask-Admin Select2Field) so iter_choices yields 4-tuples and the Select widget works
    form_overrides = {
        'type': SelectField,
        'category': SelectField,
    }
    form_args = {
        'type': {'choices': ANNOUNCEMENT_TYPE_CHOICES},
        'category': {'choices': ANNOUNCEMENT_CATEGORY_CHOICES},
    }
    
    form_widget_args = {
        'description': {'rows': 10, 'style': 'width: 100%'},
        'featured_image': {'placeholder': 'https://example.com/image.jpg'},
        'image_display_type': {'placeholder': 'poster or leave empty'}
    }

    column_labels = {
        'date_entered': 'Date Created',
        'superfeatured': 'Super Featured',
        'show_in_banner': 'Featured in top bar',
        'featured_image': 'Featured Image URL',
        'image_display_type': 'Image Display Type',
        'active': 'Status',
        'author': 'Author',
    }

    column_formatters = {
        'active': _format_announcement_status
    }

    def on_form_prefill(self, form, id):
        announcement = self.get_one(id)
        if not announcement or not hasattr(form, 'banner_type'):
            return
        if getattr(announcement, 'show_in_banner', False):
            current_type = (announcement.type or '').strip().lower()
            if current_type not in {'weather', 'parking', 'alert', 'info'}:
                current_type = 'alert'
            form.banner_type.data = current_type
        else:
            form.banner_type.data = ''

    def on_model_change(self, form, model, is_created):
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
        if is_created:
            model.id = next_global_id()

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
        db.session.commit()
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


class SermonView(AuthenticatedModelView):
    column_list = ('id', 'title', 'author', 'date', 'scripture', 'active', 'spotify_url', 'youtube_url')
    column_searchable_list = ('title', 'author', 'scripture')
    column_filters = ('author', 'date')
    column_sortable_list = ('title', 'author', 'date')
    column_default_sort = ('date', True)
    form_excluded_columns = ['id']
    column_labels = {
        'spotify_url': 'Spotify',
        'youtube_url': 'YouTube',
        'apple_podcasts_url': 'Apple Podcasts',
        'podcast_thumbnail_url': 'Thumbnail',
        'active': 'Status'
    }
    column_formatters = {'active': _format_sermon_status}

    form_columns = (
        'scripture_book', 'scripture_chapter', 'verse_start', 'verse_end',
        'title', 'author', 'scripture', 'date',
        'spotify_url', 'youtube_url', 'apple_podcasts_url', 'podcast_thumbnail_url'
    )
    form_extra_fields = {
        'scripture_book': SelectField('1. Series (Book)', choices=SERMON_BOOK_CHOICES),
        'scripture_chapter': SelectField('2. Chapter', choices=SERMON_CHAPTER_CHOICES),
        'verse_start': SelectField('3. Verse (start)', choices=SERMON_VERSE_CHOICES),
        'verse_end': SelectField('Verse (end, optional)', choices=SERMON_VERSE_CHOICES),
        'scripture': TextAreaField('Scripture (or type manually)', widget=TextArea()),
        'spotify_url': URLField('Spotify URL', validators=[Optional(), URL()]),
        'youtube_url': URLField('YouTube URL', validators=[Optional(), URL()]),
        'apple_podcasts_url': URLField('Apple Podcasts URL', validators=[Optional(), URL()]),
        'podcast_thumbnail_url': URLField('Thumbnail URL', validators=[Optional(), URL()])
    }
    form_widget_args = {
        'scripture': {'rows': 2, 'style': 'width: 100%', 'placeholder': 'e.g. Luke 12:35-59'},
        'spotify_url': {'placeholder': 'https://open.spotify.com/episode/...'},
        'youtube_url': {'placeholder': 'https://youtube.com/watch?v=...'},
        'apple_podcasts_url': {'placeholder': 'https://podcasts.apple.com/podcast/...'},
        'podcast_thumbnail_url': {'placeholder': 'https://example.com/thumbnail.jpg'}
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
        book = getattr(form, 'scripture_book', None) and getattr(form.scripture_book, 'data', None)
        ch = getattr(form, 'scripture_chapter', None) and getattr(form.scripture_chapter, 'data', None)
        v1 = getattr(form, 'verse_start', None) and getattr(form.verse_start, 'data', None)
        v2 = getattr(form, 'verse_end', None) and getattr(form.verse_end, 'data', None)
        if book and ch and str(ch).isdigit():
            try:
                vs = int(v1 or 0) if v1 else 0
                ve = int(v2 or 0) if v2 else 0
                if vs > 0:
                    ref = f"{book} {ch}:{vs}"
                    if ve > vs:
                        ref += f"-{ve}"
                else:
                    ref = f"{book} {ch}"
                model.scripture = ref
                if not (model.title and model.title.strip()):
                    model.title = ref
            except (TypeError, ValueError):
                pass

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
        flash('Status updated.', 'success')
        return redirect(url_for('sermon.index_view'))
    
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

class PodcastSeriesView(AuthenticatedModelView):
    column_list = ('title', 'description', 'episode_count')
    column_searchable_list = ('title', 'description')
    column_sortable_list = ('title',)
    form_excluded_columns = ['id']

    form_columns = ('title', 'description')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[Length(max=1000)])
    }
    
    form_widget_args = {
        'description': {'rows': 5, 'style': 'width: 100%'}
    }
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
    
    def episode_count(self, context, model, name):
        return len(model.episodes) if model.episodes else 0
    
    episode_count.column_type = 'integer'

class PodcastEpisodeView(AuthenticatedModelView):
    column_list = ('number', 'title', 'series', 'guest', 'date_added', 'scripture')
    column_searchable_list = ('title', 'guest', 'scripture')
    column_filters = ('series', 'guest', 'season')
    column_sortable_list = ('number', 'title', 'date_added')
    column_default_sort = ('number', True)
    form_excluded_columns = ['id']

    form_columns = ('series', 'number', 'title', 'link', 'listen_url', 'handout_url', 'guest', 'date_added', 'season', 'scripture', 'podcast_thumbnail_url')
    form_extra_fields = {
        'scripture': TextAreaField('Scripture', widget=TextArea()),
        'link': URLField('Episode Link', validators=[Optional(), URL()]),
        'listen_url': URLField('Listen URL', validators=[Optional(), URL()]),
        'handout_url': URLField('Handout URL', validators=[Optional(), URL()]),
        'podcast_thumbnail_url': URLField('Thumbnail URL', validators=[Optional(), URL()])
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
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()
    
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

class GalleryImageView(AuthenticatedModelView):
    column_list = ('id', 'name', 'event', 'created', 'tags_display')
    column_searchable_list = ('name',)
    column_filters = ('event',)
    column_sortable_list = ('name', 'created')
    column_default_sort = ('created', True)
    form_excluded_columns = ['id']

    form_columns = ('name', 'url', 'size', 'type', 'tags', 'event')
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
        if is_created:
            model.id = next_global_id()
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

def _format_event_status(view, context, model, name):
    from flask import url_for
    base = url_for('ongoingevent.set_status')
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
    column_list = ('id', 'title', 'type', 'category', 'active', 'sort_order', 'date_entered')
    column_searchable_list = ('title', 'description')
    column_filters = ('type', 'active', 'category')
    column_sortable_list = ('title', 'type', 'active', 'sort_order', 'date_entered')
    column_default_sort = ('sort_order', False)
    form_excluded_columns = ['id']

    form_columns = ('title', 'description', 'type', 'category', 'active')
    form_extra_fields = {
        'description': TextAreaField('Description', widget=TextArea(), validators=[DataRequired(), Length(max=2000)])
    }
    
    form_widget_args = {
        'description': {'rows': 8, 'style': 'width: 100%'}
    }
    form_widgets = {'type': Select(), 'category': Select()}

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
        'date_entered': 'Date Created',
        'active': 'Status'
    }
    column_formatters = {'active': _format_event_status}

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.id = next_global_id()

    @expose('set-status/', methods=['GET'])
    def set_status(self):
        if not is_authenticated():
            return redirect(url_for('admin_login'))
        id_val = request.args.get('id', type=int)
        status = request.args.get('status')
        if not id_val or status not in ('publish', 'draft', 'archive'):
            flash('Invalid request.', 'error')
            return redirect(url_for('ongoingevent.index_view'))
        event = OngoingEvent.query.get(id_val)
        if not event:
            flash('Not found.', 'error')
            return redirect(url_for('ongoingevent.index_view'))
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
        flash('Status updated.', 'success')
        return redirect(url_for('ongoingevent.index_view'))

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
    def is_accessible(self):
        return is_authenticated()
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))
    
    @expose('/')
    def index(self):
        from datetime import datetime
        
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
                         latest_luke=latest_luke)


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

        query = AuditLog.query.order_by(AuditLog.timestamp.desc())

        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        if type_filter:
            query = query.filter(AuditLog.entity_type == type_filter)
        if user_filter:
            query = query.filter(AuditLog.user == user_filter)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        logs = pagination.items

        # Gather distinct values for the filter dropdowns
        all_actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]
        all_types = [r[0] for r in db.session.query(AuditLog.entity_type).distinct().all()]
        all_users = [r[0] for r in db.session.query(AuditLog.user).distinct().all()]

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

# Add dashboard view
admin.add_view(DashboardView(name='Dashboard', endpoint='dashboard'))

# Add views with categories
admin.add_view(AnnouncementView(Announcement, db.session, name='Announcements', category='Content'))
admin.add_view(OngoingEventView(OngoingEvent, db.session, name='Events', category='Content'))
admin.add_view(ReorderEventsView(name='Reorder events', endpoint='reorder_events', category='Content'))
admin.add_view(SermonView(Sermon, db.session, name='Sunday Sermons', category='Media'))
admin.add_view(PodcastSeriesView(PodcastSeries, db.session, name='Podcast Series', category='Media'))
admin.add_view(PodcastEpisodeView(PodcastEpisode, db.session, name='Podcast Episodes', category='Media'))
admin.add_view(GalleryImageView(GalleryImage, db.session, name='Gallery', category='Media'))
admin.add_view(HistoryView(name='History', endpoint='history', category='Content'))

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

    # 4. Ensure the global ID counter row exists
    if not GlobalIDCounter.query.first():
        db.session.add(GlobalIDCounter(id=1, next_id=1))
        db.session.commit()

    # 5. Seed admin users
    init_admin_users()
    log.info("DB init complete — app is ready to serve")

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
        print(f"Enhanced search: http://localhost:{port}/sermons_enhanced")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, port=port, host='0.0.0.0')
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please free up a port or try running the app again.")
        exit(1)
