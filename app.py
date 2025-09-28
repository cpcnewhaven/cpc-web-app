from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_caching import Cache
from datetime import datetime, date, timedelta
import os
import requests
import feedparser
import json
import re
from ics import Calendar, Event
from dateutil import tz
import pytz
from dotenv import load_dotenv
from admin_utils import export_announcements_csv, export_sermons_csv, bulk_update_announcements, bulk_delete_content, get_content_stats, create_sample_podcast_series
from enhanced_api import enhanced_api
from json_api import json_api
from port_finder import find_available_port
from ingest.newsletter import NewsletterIngester
from ingest.events import EventsIngester
from ingest.youtube import YouTubeIngester
from ingest.mailchimp import MailchimpIngester


load_dotenv()

app = Flask(__name__)

# Configuration
app.config.from_object('config')
cache = Cache(app)

app.register_blueprint(enhanced_api, url_prefix='/api')
app.register_blueprint(json_api)

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
    # Use JSON data instead of database
    try:
        import json
        with open('data/sermons.json', 'r') as f:
            sermons_data = json.load(f)
        
        episodes = []
        for sermon in sermons_data.get('sermons', []):
            episode = {
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
            }
            episodes.append(episode)
        
        return jsonify({
            'title': sermons_data.get('title', 'Sunday Sermons'),
            'description': sermons_data.get('description', 'Weekly sermons from our Sunday worship services'),
            'episodes': episodes
        })
    except Exception as e:
        print(f"Error loading sermons from JSON: {e}")
        return jsonify({
            'title': 'Sunday Sermons',
            'description': 'Weekly sermons from our Sunday worship services',
            'episodes': []
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
    
    # Initialize ingesters
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
    
    # Find an available port
    try:
        port = find_available_port()
        print(f"🚀 Starting Flask app on port {port}")
        print(f"🌐 Main site: http://localhost:{port}")
        print(f"⚙️  Admin panel: http://localhost:{port}/admin")
        print(f"🔍 Enhanced search: http://localhost:{port}/sermons_enhanced")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, port=port, host='0.0.0.0')
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("Please free up a port or try running the app again.")
        exit(1)
