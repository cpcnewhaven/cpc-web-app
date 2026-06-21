#!/usr/bin/env python3
"""
Enhanced API Endpoints
Adds advanced API endpoints for the podcast system.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

# Import search functionality
from advanced_search import AdvancedSearch

logger = logging.getLogger(__name__)

# Create blueprint for enhanced API
enhanced_api = Blueprint('enhanced_api', __name__)

# Initialize search and analytics (lazy)
search_engine = AdvancedSearch()
analytics = None

def get_analytics():
    """Lazy-load analytics to avoid heavy imports at startup."""
    global analytics
    if analytics is None:
        try:
            from podcast_analytics import PodcastAnalytics
            analytics = PodcastAnalytics()
        except ImportError:
            analytics = None
    return analytics

@enhanced_api.route('/api/search/sermons')
def search_sermons():
    """Advanced search endpoint for sermons."""
    try:
        # Get search parameters
        query = request.args.get('q', '')
        scripture_book = request.args.get('scripture_book')
        scripture_chapter = request.args.get('scripture_chapter', type=int)
        scripture_verse = request.args.get('scripture_verse', type=int)
        speaker = request.args.get('speaker')
        series = request.args.get('series')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        tags = request.args.getlist('tags')
        sermon_type = request.args.get('sermon_type')
        min_duration = request.args.get('min_duration', type=int)
        max_duration = request.args.get('max_duration', type=int)
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')
        limit = request.args.get('limit', type=int)
        
        # Build search criteria
        search_criteria = {}
        
        if query:
            search_criteria['query'] = query
        
        if scripture_book:
            search_criteria['scripture'] = {
                'book': scripture_book,
                'chapter': scripture_chapter,
                'verse': scripture_verse
            }
        
        if speaker:
            search_criteria['speaker'] = speaker
        
        if series:
            search_criteria['series'] = series
        
        if start_date or end_date:
            search_criteria['date_range'] = {
                'start': start_date,
                'end': end_date
            }
        
        if tags:
            search_criteria['tags'] = tags
        
        if sermon_type:
            search_criteria['sermon_type'] = sermon_type
        
        if min_duration or max_duration:
            search_criteria['duration'] = {
                'min': min_duration,
                'max': max_duration
            }
        
        # Perform search
        results = search_engine.advanced_search(
            **search_criteria,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'criteria': search_criteria
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/search/suggestions')
def search_suggestions():
    """Get search suggestions based on partial query."""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'suggestions': []})
        
        suggestions = search_engine.get_search_suggestions(query)
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/search/filters')
def search_filters():
    """Get available search filters and options."""
    try:
        filters = search_engine.get_search_filters()
        return jsonify({
            'success': True,
            'filters': filters
        })
        
    except Exception as e:
        logger.error(f"Filters error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/analytics/overview')
def analytics_overview():
    """Get analytics overview."""
    try:
        analytics_instance = get_analytics()
        stats = analytics_instance.get_basic_stats()
        frequency = analytics_instance.get_publishing_frequency()
        content = analytics_instance.get_content_analysis()
        engagement = analytics_instance.get_engagement_metrics()
        insights = analytics_instance.generate_insights()
        
        return jsonify({
            'success': True,
            'overview': {
                'basic_stats': stats,
                'publishing_frequency': frequency,
                'content_analysis': content,
                'engagement_metrics': engagement,
                'insights': insights
            }
        })
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/analytics/trends')
def analytics_trends():
    """Get publishing trends and patterns."""
    try:
        analytics_instance = get_analytics()
        frequency = analytics_instance.get_publishing_frequency()
        content = analytics_instance.get_content_analysis()
        
        return jsonify({
            'success': True,
            'trends': {
                'publishing_frequency': frequency,
                'content_trends': content
            }
        })
        
    except Exception as e:
        logger.error(f"Trends error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/recent')
def recent_sermons():
    """Get recent sermons with enhanced data."""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent sermons
        results = search_engine.advanced_search(
            sort_by='date',
            sort_order='desc',
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Recent sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/popular')
def popular_sermons():
    """Get popular sermons based on various metrics."""
    try:
        limit = request.args.get('limit', 10, type=int)
        metric = request.args.get('metric', 'recent')  # recent, series, speaker
        
        if metric == 'recent':
            results = search_engine.advanced_search(
                sort_by='date',
                sort_order='desc',
                limit=limit
            )
        elif metric == 'series':
            # Get most popular series
            series_counts = {}
            for sermon in search_engine.sermons:
                series = sermon.get('series', 'Sunday Sermons')
                series_counts[series] = series_counts.get(series, 0) + 1
            
            # Get sermons from most popular series
            most_popular_series = max(series_counts.items(), key=lambda x: x[1])[0]
            results = search_engine.search_by_series(most_popular_series)[:limit]
        elif metric == 'speaker':
            # Get most prolific speaker
            speaker_counts = {}
            for sermon in search_engine.sermons:
                speaker = sermon.get('speaker', '')
                if speaker:
                    speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            most_prolific_speaker = max(speaker_counts.items(), key=lambda x: x[1])[0]
            results = search_engine.search_by_speaker(most_prolific_speaker)[:limit]
        else:
            results = []
        
        return jsonify({
            'success': True,
            'sermons': results,
            'total': len(results),
            'metric': metric
        })
        
    except Exception as e:
        logger.error(f"Popular sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/series/<series_name>')
def sermons_by_series(series_name):
    """Get sermons by specific series."""
    try:
        results = search_engine.search_by_series(series_name)
        
        return jsonify({
            'success': True,
            'series': series_name,
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Series sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/speaker/<speaker_name>')
def sermons_by_speaker(speaker_name):
    """Get sermons by specific speaker."""
    try:
        results = search_engine.search_by_speaker(speaker_name)
        
        return jsonify({
            'success': True,
            'speaker': speaker_name,
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Author sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/scripture')
def sermons_by_scripture():
    """Get sermons by scripture reference."""
    try:
        book = request.args.get('book')
        chapter = request.args.get('chapter', type=int)
        verse = request.args.get('verse', type=int)
        
        if not book:
            return jsonify({
                'success': False,
                'error': 'Book parameter is required'
            }), 400
        
        results = search_engine.search_by_scripture(book, chapter, verse)
        
        return jsonify({
            'success': True,
            'scripture': {
                'book': book,
                'chapter': chapter,
                'verse': verse
            },
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Scripture sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/tags')
def sermons_by_tags():
    """Get sermons by tags."""
    try:
        tags = request.args.getlist('tags')
        
        if not tags:
            return jsonify({
                'success': False,
                'error': 'At least one tag is required'
            }), 400
        
        results = search_engine.search_by_tags(tags)
        
        return jsonify({
            'success': True,
            'tags': tags,
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Tag sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/date-range')
def sermons_by_date_range():
    """Get sermons by date range."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date and not end_date:
            return jsonify({
                'success': False,
                'error': 'At least one date parameter is required'
            }), 400
        
        results = search_engine.search_by_date_range(start_date, end_date)
        
        return jsonify({
            'success': True,
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'sermons': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Date range sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/sermons/random')
def random_sermons():
    """Get random sermons."""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        import random
        all_sermons = search_engine.sermons
        random_sermons = random.sample(all_sermons, min(limit, len(all_sermons)))
        
        return jsonify({
            'success': True,
            'sermons': random_sermons,
            'total': len(random_sermons)
        })
        
    except Exception as e:
        logger.error(f"Random sermons error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_api.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        sermon_count = len(search_engine.sermons)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'sermon_count': sermon_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
