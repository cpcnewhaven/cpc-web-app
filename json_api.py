#!/usr/bin/env python3
"""
JSON-based API endpoints
Serves podcast data directly from JSON files for immediate use.
"""

from flask import Blueprint, jsonify
import json
import os
from typing import Dict, List, Optional

json_api = Blueprint('json_api', __name__)

def load_json_data(filename: str) -> Dict:
    """Load data from JSON file."""
    try:
        filepath = os.path.join('data', filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

@json_api.route('/api/json/sermons')
def json_sermons():
    """Serve sermons from JSON file."""
    sermons_data = load_json_data('sermons.json')
    
    if not sermons_data:
        return jsonify({
            'title': 'Sunday Sermons',
            'description': 'Weekly sermons from our Sunday worship services',
            'episodes': []
        })
    
    # Convert to the format expected by the frontend
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
            'podcast-thumbnail_url': sermon.get('podcast_thumbnail_url', ''),
            'series': sermon.get('series', 'Sunday Sermons'),
            'sermon_type': sermon.get('sermon_type', 'sermon'),
            'tags': sermon.get('tags', []),
            'search_keywords': sermon.get('search_keywords', ''),
            'duration_minutes': sermon.get('duration_minutes'),
            'guest_speaker': sermon.get('guest_speaker', ''),
            'source': sermon.get('source', 'anchor')
        }
        episodes.append(episode)
    
    return jsonify({
        'title': sermons_data.get('title', 'Sunday Sermons'),
        'description': sermons_data.get('description', 'Weekly sermons from our Sunday worship services'),
        'episodes': episodes
    })

@json_api.route('/api/json/podcasts')
def json_podcasts():
    """Serve podcast series from JSON files."""
    # Load podcast series
    series_data = load_json_data('podcast_series.json')
    episodes_data = load_json_data('podcast_episodes.json')
    
    # Group episodes by series
    series_episodes = {}
    for episode in episodes_data:
        series_id = episode.get('series_id', 'series_001')
        if series_id not in series_episodes:
            series_episodes[series_id] = []
        series_episodes[series_id].append(episode)
    
    # Create series with episodes
    series_list = []
    for series in series_data:
        series_id = series.get('id', 'series_001')
        series_info = {
            'id': series_id,
            'title': series.get('title', ''),
            'description': series.get('description', ''),
            'episodes': series_episodes.get(series_id, [])
        }
        series_list.append(series_info)
    
    return jsonify(series_list)

@json_api.route('/api/json/podcasts/beyond-podcast')
def json_beyond_podcast():
    """Serve Beyond the Sunday Sermon podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for Beyond the Sunday Sermon episodes
    beyond_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'Beyond the Sunday Sermon' in sermon.get('series', '') or 'Beyond the Sunday Sermon' in sermon.get('title', ''):
            episode = {
                'number': len(beyond_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            beyond_episodes.append(episode)
    
    return jsonify({
        'title': 'Beyond the Sunday Sermon',
        'description': 'Extended conversations and deeper dives into biblical topics with our pastoral staff and special guests.',
        'episodes': beyond_episodes
    })

@json_api.route('/api/json/podcasts/confessional-theology')
def json_confessional_theology():
    """Serve Confessional Theology podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for Confessional Theology episodes
    theology_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'Confessional Theology' in sermon.get('series', '') or 'Confessional Theology' in sermon.get('title', ''):
            episode = {
                'number': len(theology_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            theology_episodes.append(episode)
    
    return jsonify({
        'title': 'Confessional Theology',
        'description': 'Exploring Reformed theology and doctrine through systematic study of our confessional standards.',
        'episodes': theology_episodes
    })

@json_api.route('/api/json/podcasts/biblical-interpretation')
def json_biblical_interpretation():
    """Serve Biblical Interpretation podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for Biblical Interpretation episodes
    interpretation_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'Biblical Interpretation' in sermon.get('series', '') or 'Biblical Interpretation' in sermon.get('title', ''):
            episode = {
                'number': len(interpretation_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            interpretation_episodes.append(episode)
    
    return jsonify({
        'title': 'Biblical Interpretation',
        'description': 'Teaching series on how to read and understand Scripture in its historical and theological context.',
        'episodes': interpretation_episodes
    })

@json_api.route('/api/json/podcasts/membership-seminar')
def json_membership_seminar():
    """Serve Membership Seminar podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for Membership Seminar episodes
    membership_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'Membership Seminar' in sermon.get('series', '') or 'Membership Seminar' in sermon.get('title', '') or 'School of Discipleship' in sermon.get('series', ''):
            episode = {
                'number': len(membership_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            membership_episodes.append(episode)
    
    return jsonify({
        'title': 'Membership Seminar',
        'description': 'Understanding church membership and the Christian life through our comprehensive membership course.',
        'episodes': membership_episodes
    })

@json_api.route('/api/json/podcasts/what-we-believe')
def json_what_we_believe():
    """Serve What We Believe podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for What We Believe episodes
    belief_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'What We Believe' in sermon.get('series', '') or 'What We Believe' in sermon.get('title', ''):
            episode = {
                'number': len(belief_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            belief_episodes.append(episode)
    
    return jsonify({
        'title': 'What We Believe',
        'description': 'Teaching series on Reformed theology and doctrine.',
        'episodes': belief_episodes
    })

@json_api.route('/api/json/podcasts/walking-with-jesus')
def json_walking_with_jesus():
    """Serve Walking with Jesus Through Sinai podcast from JSON."""
    sermons_data = load_json_data('sermons.json')
    
    # Filter for Walking with Jesus episodes
    walking_episodes = []
    for sermon in sermons_data.get('sermons', []):
        if 'Walking with Jesus' in sermon.get('series', '') or 'Walking with Jesus' in sermon.get('title', ''):
            episode = {
                'number': len(walking_episodes) + 1,
                'title': sermon.get('title', ''),
                'link': sermon.get('link', ''),
                'listen_url': sermon.get('spotify_url', ''),
                'guest': sermon.get('guest_speaker', ''),
                'date_added': sermon.get('date', ''),
                'season': 1,
                'scripture': sermon.get('scripture', ''),
                'podcast_thumbnail_url': sermon.get('podcast_thumbnail_url', '')
            }
            walking_episodes.append(episode)
    
    return jsonify({
        'title': 'Walking with Jesus Through Sinai',
        'description': 'Study of the Ten Commandments and moral clarity.',
        'episodes': walking_episodes
    })
