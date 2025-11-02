#!/usr/bin/env python3
"""
Fix podcast endpoints to use JSON data
"""

import re

def fix_podcast_endpoints():
    """Update podcast endpoints to redirect to JSON API."""
    
    # Read the app.py file
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Define the podcast endpoints to fix
    endpoints = [
        'biblical-interpretation',
        'confessional-theology', 
        'membership-seminar'
    ]
    
    # Pattern to match the old function structure
    pattern = r'@app\.route\(\'/api/podcasts/([^\']+)\'\)\ndef api_[^\(]+\(\):\s*"""[^"]*"""\s*series = PodcastSeries\.query\.filter_by\(title=[^)]+\)\.first\(\)\s*if not series:\s*return jsonify\(\{\'episodes\': \[\]\}\)\s*episodes = PodcastEpisode\.query\.filter_by\(series_id=series\.id\)\\\s*\.order_by\(PodcastEpisode\.date_added\.desc\(\)\)\.all\(\)\s*return jsonify\(\{\s*\'title\': series\.title,\s*\'description\': series\.description,\s*\'episodes\': \[\s*\{\s*\'number\': ep\.number,\s*\'title\': ep\.title,\s*\'link\': ep\.link,\s*\'guest\': ep\.guest,\s*\'date_added\': ep\.date_added\.strftime\(\'%Y-%m-%d\'\) if ep\.date_added else None,\s*\'season\': ep\.season,\s*\'scripture\': ep\.scripture,\s*\'podcast-thumbnail_url\': ep\.podcast_thumbnail_url\s*\} for ep in episodes\s*\]\s*\}\)'
    
    # Replace with simple redirect
    def replace_endpoint(match):
        endpoint_name = match.group(1)
        return f'''@app.route('/api/podcasts/{endpoint_name}')
def api_{endpoint_name.replace('-', '_')}():
    """API endpoint for {endpoint_name.replace('-', ' ').title()} series"""
    # Redirect to JSON API
    from flask import redirect
    return redirect('/api/json/podcasts/{endpoint_name}')'''
    
    # Apply the replacement
    new_content = re.sub(pattern, replace_endpoint, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated content
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Podcast endpoints updated to use JSON data")

if __name__ == "__main__":
    fix_podcast_endpoints()
