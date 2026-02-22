#!/usr/bin/env python3
import json
import os
from app import app, db
from models import GalleryImage, next_global_id
from datetime import datetime

def migrate_gallery():
    with app.app_context():
        filepath = 'data/gallery.json'
        if not os.path.exists(filepath):
            print("No gallery.json found.")
            return

        with open(filepath, 'r') as f:
            images = json.load(f)

        count = 0
        for img in images:
            # Skip if already exists by URL
            existing = GalleryImage.query.filter_by(url=img.get('url')).first()
            if existing:
                continue

            created_date = datetime.utcnow()
            if img.get('created') and img['created'] != 'Unknown':
                try:
                    created_date = datetime.strptime(img['created'], '%Y-%m-%d')
                except:
                    pass

            new_img = GalleryImage(
                id=next_global_id(),
                name=img.get('name', 'Untitled'),
                url=img.get('url'),
                size=img.get('size'),
                type=img.get('type'),
                tags=img.get('tags', []),
                event=img.get('event', False),
                description=img.get('description', ''),
                location=img.get('location', ''),
                photographer=img.get('photographer', ''),
                created=created_date
            )
            db.session.add(new_img)
            count += 1

        db.session.commit()
        print(f"Migrated {count} images to database.")

if __name__ == "__main__":
    migrate_gallery()
