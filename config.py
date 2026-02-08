import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    _db_url = os.getenv('DATABASE_URL', 'sqlite:///cpc_newhaven.db')
    # Render provides postgres:// but SQLAlchemy requires postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# --- Podcast + cache config ---
PODCAST_FEEDS = {
    "cpc": "<PASTE_YOUR_SPOTIFY_RSS_URL_HERE>"
}
CACHE_TYPE = "SimpleCache"
CACHE_DEFAULT_TIMEOUT = 900  # 15 minutes

# --- External data sources ---
# Using public feeds for testing - replace with your actual feeds later
NEWSLETTER_FEED_URL = "https://feeds.feedburner.com/desiringgod"  # Public feed for testing
EVENTS_ICS_URL = "https://calendar.google.com/calendar/ical/baf2h147ghi7nu8ifijjrt994k%40group.calendar.google.com/public/basic.ics"  # Your CPC calendar
YOUTUBE_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # TODO: Replace with actual CPC New Haven channel ID (handle: @CPCNewHaven)
BIBLE_API_KEY = "not_needed"  # Uses free public API

# === Events (Google Calendar ICS) ===
# How far ahead to show events (in days)
EVENTS_LOOKAHEAD_DAYS = 120

# Site timezone for display
SITE_TIMEZONE = "America/New_York"

# Keyword → category mapping (used for UI chips)
EVENT_CATEGORY_RULES = {
    "Weekly":      ["sunday", "service", "worship", "prayer", "midweek"],
    "Educational": ["class", "seminar", "course", "training"],
    "Fellowship":  ["fellowship", "potluck", "picnic", "gathering", "banquet"],
    "Service":     ["outreach", "volunteer", "serve", "service project"],
    "Youth":       ["youth", "teen", "students"],
    "Children":    ["children", "kids", "vbs", "sunday school", "nursery"]
}

# --- Mailchimp Integration ---
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX")  # e.g., "us21"
MAILCHIMP_LIST_ID = os.getenv("MAILCHIMP_LIST_ID")
MAILCHIMP_RSS_URL = "<PASTE_YOUR_MAILCHIMP_RSS_URL>"  # Alternative to API

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
