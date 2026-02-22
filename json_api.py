from flask import Blueprint, jsonify
import json
import os
from typing import Dict, List, Optional
from models import PodcastSeries, PodcastEpisode, Sermon

json_api = Blueprint('json_api', __name__)

def _get_db_episodes(series_name: str) -> List[Dict]:
    """Helper to fetch episodes from database by series name or partial match."""
    series = PodcastSeries.query.filter(PodcastSeries.title.ilike(f'%{series_name}%')).first()
    if not series:
        return []
    
    episodes = PodcastEpisode.query.filter_by(series_id=series.id).order_by(PodcastEpisode.date_added.desc()).all()
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

@json_api.route('/api/json/sermons')
def json_sermons():
    """Serve sermons from database."""
    try:
        from sermon_data_helper import get_sermon_helper
        helper = get_sermon_helper()
        metadata = helper.get_metadata()
        sermons = helper.get_all_sermons()
    except Exception as e:
        print(f"Error loading sermons for JSON API: {e}")
        return jsonify({'episodes': [], 'error': str(e)})
    
    episodes = []
    for sermon in sermons:
        episodes.append({
            'id': sermon.get('id', ''),
            'title': sermon.get('title', ''),
            'speaker': sermon.get('speaker', '') or sermon.get('author', ''),
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
            'guest_speaker': sermon.get('guest_speaker', ''),
            'source': sermon.get('source', 'database')
        })
    
    return jsonify({
        'title': metadata.get('title', 'Sunday Sermons'),
        'description': metadata.get('description', 'Weekly sermons from our Sunday worship services'),
        'episodes': episodes
    })

@json_api.route('/api/json/podcasts')
def json_podcasts():
    """Serve all podcast series from database."""
    series_list = PodcastSeries.query.all()
    results = []
    for s in series_list:
        episodes = PodcastEpisode.query.filter_by(series_id=s.id).order_by(PodcastEpisode.date_added.desc()).all()
        results.append({
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'episodes': [
                {
                    'title': ep.title,
                    'link': ep.link,
                    'listen_url': ep.listen_url,
                    'date_added': ep.date_added.strftime('%Y-%m-%d') if ep.date_added else None
                } for ep in episodes
            ]
        })
    return jsonify(results)

@json_api.route('/api/json/podcasts/beyond-podcast')
def json_beyond_podcast():
    """Serve Beyond the Sunday Sermon podcast from database."""
    return jsonify({
        'title': 'Beyond the Sunday Sermon',
        'description': 'Extended conversations and deeper dives into biblical topics.',
        'episodes': _get_db_episodes('Beyond the Sunday Sermon')
    })

@json_api.route('/api/json/podcasts/confessional-theology')
def json_confessional_theology():
    """Serve Confessional Theology podcast from database."""
    return jsonify({
        'title': 'Confessional Theology',
        'description': 'Exploring Reformed theology and doctrine.',
        'episodes': _get_db_episodes('Confessional Theology')
    })

@json_api.route('/api/json/podcasts/biblical-interpretation')
def json_biblical_interpretation():
    """Serve Biblical Interpretation podcast from database."""
    return jsonify({
        'title': 'Biblical Interpretation',
        'description': 'Teaching series on how to read and understand Scripture.',
        'episodes': _get_db_episodes('Biblical Interpretation')
    })

@json_api.route('/api/json/podcasts/membership-seminar')
def json_membership_seminar():
    """Serve Membership Seminar podcast from database."""
    return jsonify({
        'title': 'Membership Seminar',
        'description': 'Understanding church membership and the Christian life.',
        'episodes': _get_db_episodes('Membership Seminar')
    })

@json_api.route('/api/json/podcasts/what-we-believe')
def json_what_we_believe():
    """Serve What We Believe podcast from database."""
    return jsonify({
        'title': 'What We Believe',
        'description': 'Teaching series on Reformed theology and doctrine.',
        'episodes': _get_db_episodes('What We Believe')
    })

@json_api.route('/api/json/podcasts/walking-with-jesus')
def json_walking_with_jesus():
    """Serve Walking with Jesus Through Sinai podcast from database."""
    return jsonify({
        'title': 'Walking with Jesus Through Sinai',
        'description': 'Study of the Ten Commandments and moral clarity.',
        'episodes': _get_db_episodes('Walking with Jesus')
    })
