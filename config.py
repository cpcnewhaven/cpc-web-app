import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///cpc_newhaven.db')
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
NEWSLETTER_FEED_URL = "<PASTE_YOUR_NEWSLETTER_RSS_URL>"
EVENTS_ICS_URL = "<PASTE_YOUR_GOOGLE_CALENDAR_ICS_URL>"
YOUTUBE_CHANNEL_ID = "<PASTE_YOUR_YOUTUBE_CHANNEL_ID>"
BIBLE_API_KEY = "<PASTE_YOUR_BIBLE_API_KEY>"

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
