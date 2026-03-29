#!/usr/bin/env python3
import os
from app import app, db
from models import GalleryImage, next_global_id
from datetime import datetime

def populate_cookout():
    images = [
        'https://storage.googleapis.com/cpc-public-website/web-assets/heros/%5BHERO%5D%5BComm%7D6.jpg',
        'https://storage.googleapis.com/cpc-public-website/web-assets/heros/%5BHERO%5D%5BComm%7D5.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/2.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/3.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/4.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/5.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/6.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/7.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/8.jpg',
        'https://storage.googleapis.com/cpc-public-website/events/Young%20Adults%20Cookout%20-%20September%202025/9.jpg'
    ]

    with app.app_context():
        count = 0
        for i, url in enumerate(images):
            # Skip if already exists
            existing = GalleryImage.query.filter_by(url=url).first()
            if existing:
                print(f"Skipping existing image: {url}")
                continue

            # Descriptive names
            if 'heros' in url:
                name = f"Community Hero {i+1}"
                tags = ["cookout", "fellowship", "hero"]
            else:
                name = f"Young Adults Cookout - Image {i-1}"
                tags = ["cookout", "fellowship", "young adults"]

            # Assume September 2025
            created_date = datetime(2025, 9, 15)

            new_img = GalleryImage(
                id=next_global_id(),
                name=name,
                url=url,
                size='Large',
                type='image/jpeg',
                tags=tags,
                event=True,
                description="CPC Young Adults Cookout - September 2025 event photos.",
                location="New Haven, CT",
                photographer="CPC Media Team",
                created=created_date
            )
            db.session.add(new_img)
            count += 1
        
        db.session.commit()
        print(f"Added {count} new images to the gallery.")

if __name__ == "__main__":
    populate_cookout()
