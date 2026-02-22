#!/usr/bin/env python3
from app import app
from models import PodcastSeries, PodcastEpisode

with app.app_context():
    series = PodcastSeries.query.all()
    print(f"Total series: {len(series)}")
    for s in series:
        ep_count = PodcastEpisode.query.filter_by(series_id=s.id).count()
        print(f" - {s.title} (ID: {s.id}): {ep_count} episodes")
