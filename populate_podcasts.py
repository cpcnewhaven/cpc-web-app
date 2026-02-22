#!/usr/bin/env python3
import json
import os
from app import app, db
from models import PodcastSeries, PodcastEpisode, next_global_id

def populate_podcasts():
    with app.app_context():
        # Map of old_id string -> new_id integer
        series_map = {}
        
        # 1. Load Podcast Series
        series_file = 'data/podcast_series.json'
        if os.path.exists(series_file):
            with open(series_file, 'r') as f:
                series_data = json.load(f)
            
            for s in series_data:
                old_id = s['id']
                existing = PodcastSeries.query.filter_by(title=s['title']).first()
                if not existing:
                    new_id = next_global_id()
                    new_series = PodcastSeries(
                        id=new_id,
                        title=s['title'],
                        description=s.get('description', '')
                    )
                    db.session.add(new_series)
                    series_map[old_id] = new_id
                else:
                    series_map[old_id] = existing.id
            db.session.commit()
            print(f"Populated/Mapped {len(series_data)} podcast series.")

        # 2. Load Podcast Episodes
        episodes_file = 'data/podcast_episodes.json'
        if os.path.exists(episodes_file):
            with open(episodes_file, 'r') as f:
                episodes_data = json.load(f)
            
            count = 0
            for ep in episodes_data:
                old_series_id = ep['series_id']
                new_series_id = series_map.get(old_series_id)
                if not new_series_id:
                    continue
                
                # Check if episode with this title and series already exists
                existing = PodcastEpisode.query.filter_by(
                    series_id=new_series_id,
                    title=ep['title']
                ).first()
                
                if not existing:
                    new_id = next_global_id()
                    new_ep = PodcastEpisode(
                        id=new_id,
                        series_id=new_series_id,
                        number=ep.get('number'),
                        title=ep['title'],
                        link=ep.get('link'),
                        listen_url=ep.get('listen_url'),
                        handout_url=ep.get('handout_url'),
                        guest=ep.get('guest'),
                        date_added=datetime.strptime(ep['date_added'], '%Y-%m-%d').date() if ep.get('date_added') else None,
                        season=ep.get('season', 1),
                        scripture=ep.get('scripture'),
                        podcast_thumbnail_url=ep.get('podcast_thumbnail_url')
                    )
                    db.session.add(new_ep)
                    count += 1
            db.session.commit()
            print(f"Populated {count} podcast episodes.")

if __name__ == "__main__":
    from datetime import datetime
    populate_podcasts()
