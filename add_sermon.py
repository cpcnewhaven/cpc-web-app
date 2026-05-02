#!/usr/bin/env python
"""
Add sermon to Render database.
Run: python add_sermon.py
"""

from app import app, db
from models import Sermon, next_global_id
from datetime import datetime, date

def add_sermon():
    """Add a single sermon."""

    sermon_data = {
        'title': 'The Heart of Christ',
        'scripture': 'Luke 19:11-40',
        'speaker': 'Rev. Jerry Ornelas',
        'date': date(2026, 5, 3),
    }

    # Check if already exists
    existing = Sermon.query.filter_by(
        title=sermon_data['title'],
        date=sermon_data['date']
    ).first()

    if existing:
        print(f"⊘ Sermon already exists: {sermon_data['title']} ({sermon_data['date']})")
        return 0

    # Get next global ID
    new_id = next_global_id()

    # Create sermon
    sermon = Sermon(
        id=new_id,
        title=sermon_data['title'],
        scripture=sermon_data['scripture'],
        speaker=sermon_data['speaker'],
        date=sermon_data['date'],
        active=True,
    )

    db.session.add(sermon)
    db.session.commit()

    print(f"✓ Added sermon: {sermon_data['title']}")
    print(f"  Speaker: {sermon_data['speaker']}")
    print(f"  Scripture: {sermon_data['scripture']}")
    print(f"  Date: {sermon_data['date']}")
    print(f"  ID: {new_id}")

    return 1

def main():
    with app.app_context():
        print("\n🎙️  Adding sermon to Render database...\n")
        count = add_sermon()

        if count > 0:
            print(f"\n✅ Done! Added {count} sermon")
            print("\nNext steps:")
            print("  1. Log into admin: http://localhost:PORT/admin")
            print("  2. Visit Sermons CRUD to add media links (Spotify, YouTube, etc.)")
            print("  3. Associate with a sermon series if applicable")
            print("  4. Upload podcast thumbnail if available")

if __name__ == '__main__':
    main()
