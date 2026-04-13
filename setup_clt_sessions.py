#!/usr/bin/env python
"""
Helper script to set up CLT (Christian Leadership Training) sessions.
Run this to add placeholder sessions for the 2025-26 year.

python setup_clt_sessions.py
"""

import os
from app import app, db
from models import TeachingSeries, TeachingSeriesSession
from datetime import datetime, date

def setup_clt_sessions():
    with app.app_context():
        # Get the CLT series
        clt = db.session.query(TeachingSeries).filter_by(
            title='Christian Leadership Training'
        ).first()

        if not clt:
            print("❌ CLT series not found. Run add_clt_series.py first.")
            return

        print(f"\n✓ Found CLT series (ID: {clt.id})")
        print(f"  Current sessions: {len(clt.sessions) if clt.sessions else 0}")

        # List of months for 2025-26 year (last Friday of each month at 6:30pm)
        sessions_to_add = [
            ('October 2025', '2025-10-31'),
            ('November 2025', '2025-11-28'),
            ('December 2025', '2025-12-26'),
            ('January 2026', '2026-01-30'),
            ('February 2026', '2026-02-27'),
            ('March 2026', '2026-03-27'),
            ('April 2026', '2026-04-24'),
            ('May 2026', '2026-05-29'),
            ('June 2026', '2026-06-26'),
        ]

        added = 0
        for title, date_str in sessions_to_add:
            # Check if session already exists
            existing = db.session.query(TeachingSeriesSession).filter_by(
                series_id=clt.id,
                title=title
            ).first()

            if existing:
                print(f"  ⊘ {title} already exists (ID: {existing.id})")
                continue

            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            session = TeachingSeriesSession(
                series_id=clt.id,
                title=title,
                description=f'CLT session for {title}',
                session_date=session_date,
                pdf_url=None  # Users can add PDFs in the admin panel
            )
            db.session.add(session)
            added += 1
            print(f"  ✓ Added: {title} ({date_str})")

        if added > 0:
            db.session.commit()
            print(f"\n✓ Successfully added {added} session(s)")
        else:
            print("\n✓ All sessions already exist")

        print("\n📝 NEXT STEPS:")
        print("  1. Go to /admin/teachingseries")
        print("  2. Click 'Christian Leadership Training' to edit")
        print("  3. Edit individual sessions to:")
        print("     - Set session_date if needed")
        print("     - Add pdf_url for readings/handouts (link to Google Doc or PDF)")
        print("     - Add description/title customization")
        print("\n💡 TIP: Link to the CLT Readings List Google Doc in session PDFs")

if __name__ == '__main__':
    setup_clt_sessions()
