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

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
