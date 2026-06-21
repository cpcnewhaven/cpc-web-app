#!/usr/bin/env python3
"""
Setup script for podcast fetcher
Helps configure the podcast fetcher with your specific podcast information.
"""

import json
import os
import re
import requests
from urllib.parse import urlparse

def get_spotify_show_id_from_url(url):
    """Extract Spotify show ID from various URL formats."""
    patterns = [
        r'spotify\.com/show/([a-zA-Z0-9]+)',
        r'open\.spotify\.com/show/([a-zA-Z0-9]+)',
        r'spotify:show:([a-zA-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_anchor_rss_url_from_anchor_url(url):
    """Convert Anchor.fm URL to RSS URL."""
    # Extract podcast ID from various Anchor URL formats
    patterns = [
        r'anchor\.fm/s/([^/]+)',
        r'anchor\.fm/@([^/]+)',
        r'anchor\.fm/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            podcast_id = match.group(1)
            return f"https://anchor.fm/s/{podcast_id}/podcast/rss"
    
    return None

def test_spotify_credentials(client_id, client_secret):
    """Test Spotify credentials."""
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        return True, "Credentials are valid"
    except requests.exceptions.RequestException as e:
        return False, f"Invalid credentials: {e}"

def test_rss_url(rss_url):
    """Test RSS URL accessibility."""
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        return True, "RSS URL is accessible"
    except requests.exceptions.RequestException as e:
        return False, f"RSS URL not accessible: {e}"

def main():
    """Main setup function."""
    print("🎙️  Podcast Fetcher Setup")
    print("=" * 50)
    
    config = {
        "spotify": {
            "enabled": False,
            "client_id": "",
            "client_secret": "",
            "show_ids": []
        },
        "anchor": {
            "enabled": False,
            "rss_urls": []
        },
        "settings": {
            "update_interval_hours": 6,
            "backup_before_update": True,
            "log_level": "INFO"
        }
    }
    
    # Spotify setup
    print("\n📱 Spotify Configuration")
    print("-" * 30)
    
    use_spotify = input("Do you want to use Spotify API? (y/n): ").lower().strip() == 'y'
    
    if use_spotify:
        print("\nTo get Spotify credentials:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create a new app")
        print("3. Copy the Client ID and Client Secret")
        
        client_id = input("Enter your Spotify Client ID: ").strip()
        client_secret = input("Enter your Spotify Client Secret: ").strip()
        
        if client_id and client_secret:
            print("Testing credentials...")
            valid, message = test_spotify_credentials(client_id, client_secret)
            print(f"✓ {message}")
            
            if valid:
                config["spotify"]["enabled"] = True
                config["spotify"]["client_id"] = client_id
                config["spotify"]["client_secret"] = client_secret
                
                # Get show IDs
                print("\nEnter Spotify show URLs or IDs (one per line, empty to finish):")
                show_ids = []
                while True:
                    url_or_id = input("Spotify show URL/ID: ").strip()
                    if not url_or_id:
                        break
                    
                    show_id = get_spotify_show_id_from_url(url_or_id) or url_or_id
                    show_ids.append(show_id)
                    print(f"✓ Added show ID: {show_id}")
                
                config["spotify"]["show_ids"] = show_ids
    
    # Anchor.fm setup
    print("\n🎧 Anchor.fm Configuration")
    print("-" * 30)
    
    use_anchor = input("Do you want to use Anchor.fm RSS feeds? (y/n): ").lower().strip() == 'y'
    
    if use_anchor:
        print("\nEnter Anchor.fm podcast URLs (one per line, empty to finish):")
        rss_urls = []
        while True:
            anchor_url = input("Anchor.fm URL: ").strip()
            if not anchor_url:
                break
            
            rss_url = get_anchor_rss_url_from_anchor_url(anchor_url)
            if rss_url:
                print(f"Testing RSS URL: {rss_url}")
                valid, message = test_rss_url(rss_url)
                print(f"✓ {message}")
                
                if valid:
                    rss_urls.append(rss_url)
                    print(f"✓ Added RSS URL: {rss_url}")
                else:
                    print("❌ Skipping invalid RSS URL")
            else:
                print("❌ Could not convert URL to RSS format")
        
        if rss_urls:
            config["anchor"]["enabled"] = True
            config["anchor"]["rss_urls"] = rss_urls
    
    # Settings
    print("\n⚙️  Settings")
    print("-" * 30)
    
    try:
        interval = int(input("Update interval in hours (default 6): ") or "6")
        config["settings"]["update_interval_hours"] = interval
    except ValueError:
        print("Invalid input, using default 6 hours")
    
    backup = input("Create backup before updates? (y/n, default y): ").lower().strip()
    config["settings"]["backup_before_update"] = backup != 'n'
    
    # Save configuration
    config_file = "podcast_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to {config_file}")
    
    # Test the configuration
    print("\n🧪 Testing Configuration")
    print("-" * 30)
    
    try:
        from podcast_fetcher import PodcastFetcher
        fetcher = PodcastFetcher(config_file)
        fetcher.fetch_all_podcasts()
        print("✅ Configuration test successful!")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    print("\n📋 Next Steps:")
    print("1. Run 'python podcast_fetcher.py' to fetch podcasts once")
    print("2. Run 'python podcast_scheduler.py' to start automatic updates")
    print("3. Run 'python podcast_scheduler.py --once' to run once and exit")
    print("4. Check the generated data/sermons.json file")

if __name__ == "__main__":
    main()
