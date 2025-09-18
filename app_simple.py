"""
CPC New Haven - Simplified Flask App with JSON Data
Glass morphism design with easy JSON file management
"""
from flask import Flask, render_template, jsonify, request
import os
from json_data import data_manager

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cpc-new-haven-secret-key-2024')

# Routes
@app.route('/')
def index():
    """Homepage with highlights and recent content"""
    announcements = data_manager.get_active_announcements()
    superfeatured = data_manager.get_superfeatured_announcements()
    recent_sermons = data_manager.get_sermons()[:3]
    
    return render_template('index.html', 
                         announcements=announcements,
                         superfeatured=superfeatured,
                         recent_sermons=recent_sermons)

@app.route('/sundays')
def sundays():
    """Sundays page with service information"""
    return render_template('sundays.html')

@app.route('/about')
def about():
    """About page with church information"""
    return render_template('about.html')

@app.route('/podcasts')
def podcasts():
    """Podcasts page with series and episodes"""
    series = data_manager.get_podcast_series()
    episodes = data_manager.get_podcast_episodes()
    return render_template('podcasts.html', series=series, episodes=episodes)

@app.route('/events')
def events():
    """Events page with upcoming events"""
    events = data_manager.get_active_events()
    return render_template('events_glass.html', events=events)

@app.route('/community')
def community():
    """Community page with groups and ministries"""
    return render_template('community.html')

@app.route('/live')
def live():
    """Live streaming page"""
    return render_template('live.html')

@app.route('/resources')
def resources():
    """Resources page"""
    return render_template('resources.html')

@app.route('/give')
def give():
    """Give page"""
    return render_template('give.html')

# API Routes
@app.route('/api/announcements')
def api_announcements():
    """API endpoint for announcements"""
    announcements = data_manager.get_active_announcements()
    return jsonify({'announcements': announcements})

@app.route('/api/sermons')
def api_sermons():
    """API endpoint for sermons"""
    sermons = data_manager.get_sermons()
    return jsonify({'sermons': sermons})

@app.route('/api/podcast-series')
def api_podcast_series():
    """API endpoint for podcast series"""
    series = data_manager.get_podcast_series()
    return jsonify({'series': series})

@app.route('/api/podcast-episodes')
def api_podcast_episodes():
    """API endpoint for podcast episodes"""
    episodes = data_manager.get_podcast_episodes()
    return jsonify({'episodes': episodes})

@app.route('/api/podcast-episodes/<series_id>')
def api_podcast_episodes_by_series(series_id):
    """API endpoint for episodes by series"""
    episodes = data_manager.get_episodes_by_series(series_id)
    return jsonify({'episodes': episodes})

@app.route('/api/gallery')
def api_gallery():
    """API endpoint for gallery images"""
    images = data_manager.get_gallery_images()
    return jsonify({'images': images})

@app.route('/api/events')
def api_events():
    """API endpoint for events"""
    events = data_manager.get_active_events()
    return jsonify({'events': events})

# Admin Routes (Simple JSON-based admin)
@app.route('/admin')
def admin():
    """Simple admin interface"""
    announcements = data_manager.get_announcements()
    sermons = data_manager.get_sermons()
    events = data_manager.get_events()
    series = data_manager.get_podcast_series()
    episodes = data_manager.get_podcast_episodes()
    gallery = data_manager.get_gallery_images()
    
    return render_template('admin.html',
                         announcements=announcements,
                         sermons=sermons,
                         events=events,
                         series=series,
                         episodes=episodes,
                         gallery=gallery)

@app.route('/admin/add-announcement', methods=['POST'])
def admin_add_announcement():
    """Add new announcement"""
    data = request.get_json()
    success = data_manager.add_announcement(data)
    return jsonify({'success': success})

@app.route('/admin/add-sermon', methods=['POST'])
def admin_add_sermon():
    """Add new sermon"""
    data = request.get_json()
    success = data_manager.add_sermon(data)
    return jsonify({'success': success})

@app.route('/admin/add-event', methods=['POST'])
def admin_add_event():
    """Add new event"""
    data = request.get_json()
    success = data_manager.add_event(data)
    return jsonify({'success': success})

@app.route('/admin/add-gallery-image', methods=['POST'])
def admin_add_gallery_image():
    """Add new gallery image"""
    data = request.get_json()
    success = data_manager.add_gallery_image(data)
    return jsonify({'success': success})

@app.route('/admin/update-announcement/<announcement_id>', methods=['PUT'])
def admin_update_announcement(announcement_id):
    """Update announcement"""
    data = request.get_json()
    success = data_manager.update_announcement(announcement_id, data)
    return jsonify({'success': success})

@app.route('/admin/delete-announcement/<announcement_id>', methods=['DELETE'])
def admin_delete_announcement(announcement_id):
    """Delete announcement"""
    success = data_manager.delete_announcement(announcement_id)
    return jsonify({'success': success})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
