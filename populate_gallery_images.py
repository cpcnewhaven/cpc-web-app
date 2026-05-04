"""
Populate gallery_images table with the full image URL list.
Run once: python populate_gallery_images.py
Safe to re-run — skips images whose URL already exists.
"""
from datetime import datetime
from app import app, db
from models import GalleryImage, GlobalIDCounter


def next_id():
    counter = GlobalIDCounter.query.filter_by(id=1).first()
    nid = counter.next_id
    counter.next_id += 1
    return nid


IMAGES = [
    # ── Women's Fall Brunch 2024 ────────────────────────────────────────────
    {
        'name': "Women's Fall Brunch 2024 — Photo 1",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/605c1ade-b21e-4713-ad4e-d9bb2d6709ad.JPG',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },
    {
        'name': "Women's Fall Brunch 2024 — Photo 2",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/89c3ea3b-e196-4318-bee8-08b5e66e728d.JPG',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },
    {
        'name': "Women's Fall Brunch 2024 — Photo 3",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/IMG_3661.jpg',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },
    {
        'name': "Women's Fall Brunch 2024 — Photo 4",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/IMG_3672.jpg',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },
    {
        'name': "Women's Fall Brunch 2024 — Photo 5",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/IMG_3673.jpg',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },
    {
        'name': "Women's Fall Brunch 2024 — Photo 6",
        'url': 'https://storage.googleapis.com/cpc-public-website/media-gallery/womans-fall-brunch-2024/ffa7bc41-31fb-49b5-aac6-f4ecd199a12a.JPG',
        'tags': ["women's ministry", 'brunch', 'fellowship', '2024'],
        'event': True,
        'location': 'New Haven, CT',
        'description': "Women's Fall Brunch 2024",
        'created': datetime(2024, 10, 15),
    },

    # ── CPC Retreat 2025 ────────────────────────────────────────────────────
    {
        'name': 'CPC Retreat 2025 — Group Photo',
        'url': 'https://storage.googleapis.com/cpc-public-website/retreat2025/CPC%20Retreat%202025%20All.jpg',
        'tags': ['retreat', 'fellowship', 'community', '2025'],
        'event': True,
        'description': 'Full congregation group photo from CPC Retreat 2025',
        'created': datetime(2025, 3, 1),
    },

    # ── Mission Trip 2025 ───────────────────────────────────────────────────
    {
        'name': 'Mission Trip 2025 — Atlantic City',
        'url': 'https://storage.googleapis.com/cpc-public-website/events/Mission%20Trip%202025/cpcMissionTrip_ATLANTIC%20CITY.jpg',
        'tags': ['mission trip', 'outreach', 'service', '2025', 'atlantic city'],
        'event': True,
        'location': 'Atlantic City, NJ',
        'description': 'CPC Mission Trip 2025 — Atlantic City outreach',
        'created': datetime(2025, 5, 1),
    },

    # ── LifeGroups ──────────────────────────────────────────────────────────
    {
        'name': 'LifeGroups 2025',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/CPC_Lifegroup_2025.jpg',
        'tags': ['lifegroups', 'small groups', 'fellowship', '2025'],
        'event': False,
        'description': 'CPC LifeGroups — small group community 2025',
        'created': datetime(2025, 1, 1),
    },
    {
        'name': 'LifeGroup Photo',
        'url': 'https://storage.googleapis.com/cpc-public-website/lifegroup-pics/cpc-lifegroup-2.jpeg',
        'tags': ['lifegroups', 'small groups', 'fellowship'],
        'event': False,
        'description': 'CPC LifeGroup community gathering',
        'created': datetime(2024, 9, 1),
    },

    # ── General Church Photos (53–69) ───────────────────────────────────────
    {
        'name': 'Church Photo 53',
        'url': 'https://storage.googleapis.com/cpc-public-website/53.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 54',
        'url': 'https://storage.googleapis.com/cpc-public-website/54.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 62',
        'url': 'https://storage.googleapis.com/cpc-public-website/62.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 63',
        'url': 'https://storage.googleapis.com/cpc-public-website/63.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 65',
        'url': 'https://storage.googleapis.com/cpc-public-website/65.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 67',
        'url': 'https://storage.googleapis.com/cpc-public-website/67.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },
    {
        'name': 'Church Photo 69',
        'url': 'https://storage.googleapis.com/cpc-public-website/69.jpg',
        'tags': ['congregation', 'church', 'worship'],
        'event': False,
        'description': 'CPC New Haven church photo',
        'created': datetime(2024, 1, 1),
    },

    # ── Featured / Hero Images ──────────────────────────────────────────────
    {
        'name': 'New Haven Skyline — Featured',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/homepage/Homepage%20-%20FEATURED%20IMG-NewHaven.jpg',
        'tags': ['new haven', 'featured', 'hero', 'city'],
        'event': False,
        'description': 'New Haven skyline — homepage featured image',
        'created': datetime(2024, 6, 1),
    },
    {
        'name': 'Sermon — Featured',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/homepage/Homepage%20-%20FEATURED%20IMG-Sermon.jpg',
        'tags': ['sermon', 'worship', 'featured', 'hero'],
        'event': False,
        'description': 'Sermon / worship service — homepage featured image',
        'created': datetime(2024, 6, 1),
    },
    {
        'name': 'Congregation — Featured',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/homepage/Homepage%20-%20FEATURED%20IMG-congregation.jpg',
        'tags': ['congregation', 'worship', 'featured', 'hero'],
        'event': False,
        'description': 'Congregation gathered for worship — homepage featured image',
        'created': datetime(2024, 6, 1),
    },
    {
        'name': 'Autumn Church Photo',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/homepage/CPC_AUTUMN_PHOTO.jpg',
        'tags': ['autumn', 'fall', 'church', 'exterior', 'featured'],
        'event': False,
        'description': 'CPC New Haven autumn exterior photo',
        'created': datetime(2024, 10, 1),
    },
    {
        'name': 'About Page — Drone Shot',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/%5BFEATURED%20IMAGE%5D%5BABOUT%20PAGE%5D%5BDrone%20Shot%5D-1.jpg',
        'tags': ['drone', 'aerial', 'exterior', 'about', 'featured'],
        'event': False,
        'description': 'Aerial drone shot of CPC New Haven — about page hero',
        'created': datetime(2024, 6, 1),
    },
    {
        'name': 'Live Page — Craig Luekens',
        'url': 'https://storage.googleapis.com/cpc-public-website/featuredIMGs/%5BFEATURED%20IMG%5D%5BLIVE%20PAGE%5D%5BCRAIG%5D-1.jpg',
        'tags': ['pastor', 'live', 'craig luekens', 'sermon', 'featured'],
        'event': False,
        'description': 'Pastor Craig Luekens — live page featured image',
        'created': datetime(2024, 6, 1),
    },

    # ── Partiful Event ──────────────────────────────────────────────────────
    {
        'name': 'Community Event Photo',
        'url': 'https://partiful.imgix.net/external/user/GpJGatjzQAZA6L6xI7wtwziXjl93/fRLKa-QyxLePlBM7thoEW?fit=clip&w=800&auto=format',
        'tags': ['community', 'event', 'fellowship'],
        'event': True,
        'description': 'Community event photo',
        'created': datetime(2025, 1, 1),
    },
]


def run():
    with app.app_context():
        existing_urls = {img.url for img in GalleryImage.query.with_entities(GalleryImage.url).all()}
        added = 0
        skipped = 0

        for data in IMAGES:
            if data['url'] in existing_urls:
                print(f"  SKIP (exists): {data['name']}")
                skipped += 1
                continue

            img = GalleryImage(
                id=next_id(),
                name=data['name'],
                url=data['url'],
                tags=data['tags'],
                event=data.get('event', False),
                description=data.get('description', ''),
                location=data.get('location', ''),
                photographer=data.get('photographer', ''),
                created=data.get('created', datetime.utcnow()),
                size='',
                type='image',
                sort_order=0,
            )
            db.session.add(img)
            existing_urls.add(data['url'])
            print(f"  ADD: {data['name']}")
            added += 1

        db.session.commit()
        print(f'\nDone — {added} added, {skipped} skipped.')


if __name__ == '__main__':
    run()
