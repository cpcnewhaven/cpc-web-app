#!/usr/bin/env python
"""
Add May bulletin content to Render database via CRUD models.
Run: python add_may_bulletin.py
"""

from app import app, db
from models import Announcement, OngoingEvent, next_global_id
from datetime import datetime, date

def add_announcements():
    """Add announcement-type bulletin items."""

    announcements = [
        {
            'title': 'Large Print Bulletin',
            'description': 'Large Print Bulletin available for this Sunday.',
            'type': 'announcement',
            'category': 'bulletin',
            'active': True,
            'event_date': date(2026, 5, 3),  # This Sunday, May 3
        },
        {
            'title': 'Children\'s Participation in Worship This Sunday',
            'description': '''This Sunday, during the Passing of the Peace, all children are invited to come to the front by the worship team. Mrs. Patty will have shakers available for the children to use during the Song of Thanksgiving. We are grateful for our covenant children, and it is both our joy and privilege to help train them in the Worship of God.''',
            'type': 'announcement',
            'category': 'worship',
            'active': True,
            'event_date': date(2026, 5, 3),
        },
        {
            'title': 'Congregational Meeting | This Sunday During Lunch',
            'description': '''Our bi-annual congregational meeting takes place this Sunday, May 3rd after the worship service in the Fellowship Hall. We will hear a recap of all that God has done this year, and discuss plans for the future. All are welcome to attend, and members are highly encouraged, though there will be no official voting.''',
            'type': 'event',
            'category': 'meeting',
            'active': True,
            'event_date': date(2026, 5, 3),
            'event_start_time': 'After Worship (approx. 12:00 PM)',
            'event_end_time': None,
        },
        {
            'title': 'Lost and Found',
            'description': '''This is the 3rd and final week for the lost items on the tables in the foyer to find a home! Anyone who can use them may take them home. All leftover items will be donated.''',
            'type': 'announcement',
            'category': 'notice',
            'active': True,
            'event_date': date(2026, 5, 3),
        },
        {
            'title': 'I Heart New Haven Day! | Saturday, June 6',
            'description': '''Mark your calendars for June 6 for Bridges of Hope's annual I Heart New Haven Day! This is an exciting day joining with other churches around the city to love the greater New Haven area with projects such as clean up, gardening, painting, and repair.''',
            'type': 'event',
            'category': 'community',
            'active': True,
            'event_date': date(2026, 6, 6),
            'event_start_time': 'Saturday, June 6',
        },
        {
            'title': 'CPC College Internship Program | Application deadline THIS Sunday, May 3rd',
            'description': '''An opportunity for undergraduate students who desire to grow deeper in theology, godliness, and participation in ministry. Students will engage in theological training, personal formation, and missional opportunities in New Haven. The goal is to ground participants in sound doctrine, cultivate personal godliness, and, where applicable, help discern a call to ministry. The program offers two tracks: a Ministry Track for those exploring vocational ministry and a Formation Track for those seeking deeper theological and spiritual growth. Open to all undergraduate students. For more information or to apply, contact Pastor Jerry at jerry.ornelas@cpcnewhaven.org.''',
            'type': 'announcement',
            'category': 'ministry',
            'active': True,
            'event_date': date(2026, 5, 3),
            'expires_at': date(2026, 5, 3),  # Deadline is May 3
        },
    ]

    added_count = 0
    for ann_data in announcements:
        # Check if already exists (by title)
        existing = Announcement.query.filter_by(title=ann_data['title']).first()
        if existing:
            print(f"  ⊘ Skipped (already exists): {ann_data['title']}")
            continue

        # Get next global ID
        new_id = next_global_id()

        # Create announcement
        announcement = Announcement(
            id=new_id,
            title=ann_data['title'],
            description=ann_data['description'],
            type=ann_data.get('type', 'announcement'),
            category=ann_data.get('category'),
            active=ann_data.get('active', True),
            event_date=ann_data.get('event_date'),
            event_start_time=ann_data.get('event_start_time'),
            event_end_time=ann_data.get('event_end_time'),
            expires_at=ann_data.get('expires_at'),
            date_entered=datetime.utcnow(),
        )

        db.session.add(announcement)
        print(f"  ✓ Added announcement: {ann_data['title']} (ID: {new_id})")
        added_count += 1

    db.session.commit()
    return added_count

def add_ongoing_events():
    """Add OngoingEvent items (recurring/permanent items)."""

    ongoing_events = [
        {
            'title': 'Regular Sunday Schedule',
            'description': '''8:30am | Prayer in the Parlor
9:30am | Children's Sunday School
9:30am | Adult Sunday Studies
10:30am | Worship Service
12:00pm | Fellowship Lunch''',
            'category': 'worship',
            'sort_order': 10,
        },
        {
            'title': 'Friday Pastor Drop-In Office Hours',
            'description': '''Craig | Fridays 7:30-10:30am
Other hours available upon request.

If you have a more private or formal need, you're always welcome to set up a separate time with Pastor Craig (craig.luekens@cpcnewhaven.org) or Pastor Jerry (jerry.ornelas@cpcnewhaven.org), but this is meant to be a space where anyone can drop in.''',
            'category': 'pastoral',
            'sort_order': 20,
        },
    ]

    added_count = 0
    for event_data in ongoing_events:
        # Check if already exists
        existing = OngoingEvent.query.filter_by(title=event_data['title']).first()
        if existing:
            print(f"  ⊘ Skipped (already exists): {event_data['title']}")
            continue

        # Get next global ID
        new_id = next_global_id()

        # Create ongoing event
        event = OngoingEvent(
            id=new_id,
            title=event_data['title'],
            description=event_data['description'],
            category=event_data.get('category'),
            sort_order=event_data.get('sort_order', 0),
            active=True,
            date_entered=datetime.utcnow(),
        )

        db.session.add(event)
        print(f"  ✓ Added ongoing event: {event_data['title']} (ID: {new_id})")
        added_count += 1

    db.session.commit()
    return added_count

def main():
    with app.app_context():
        print("\n📋 Adding May bulletin content to Render database...\n")

        print("Adding Announcements:")
        ann_count = add_announcements()

        print(f"\nAdding OngoingEvents:")
        event_count = add_ongoing_events()

        total = ann_count + event_count
        print(f"\n✅ Done! Added {total} items total ({ann_count} announcements, {event_count} ongoing events)")
        print("\nNext steps:")
        print("  1. Log into the admin panel: http://localhost:PORT/admin")
        print("  2. Visit the Announcement and OngoingEvent CRUD pages to view/edit")
        print("  3. Mark items as featured/superfeatured as needed")
        print("  4. Update sort order if desired")

if __name__ == '__main__':
    main()
