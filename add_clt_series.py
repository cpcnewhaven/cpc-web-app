#!/usr/bin/env python
"""
Add the Christian Leadership Training (CLT) teaching series to the database.
Run this with:
  python add_clt_series.py
"""

import os
from app import app, db
from models import TeachingSeries
from datetime import datetime

def add_clt_series():
    """Add CLT teaching series to database."""

    with app.app_context():
        # Check if CLT already exists
        existing = db.session.query(TeachingSeries).filter_by(
            title='Christian Leadership Training'
        ).first()

        if existing:
            print("✓ Christian Leadership Training series already exists (ID: {})".format(existing.id))
            return existing

        # Create the new teaching series
        clt_series = TeachingSeries(
            title='Christian Leadership Training',
            description="""This class is for those interested in going deeper in their Christian faith, learning more about what it means to be a leader in the Church, and wanting to be challenged in their own life to follow Christ more radically.

**Prerequisites:** This class assumes participation in the Adult Sunday Studies "Total Christ" class. It is very important that you attend or listen to the recording and get the handouts. This class will be assuming that material and building on top of it. This class also assumes much of the "What We Believe" class, which is our core beliefs class.

**Resources:**
- CLT Readings List (Google Doc): Full monthly schedule, handouts, and readings

**Suggested Reading List:**
- Dietrich Bonhoeffer's Discipleship (sometimes published as "Cost of Discipleship")
- Tim Keller's Center Church
- Brian Devries' You Will be My Witnesses
- Jack Miller's A Praying Life
- Lesslie Newbigin's The Open Secret
- Michael Horton's The Christian Faith
- Michael Goheen's A Light to the Nations: The Missional Church and the Biblical Story and The Church and its Vocation
- Ken Golden's Presbytopia: What it means to be Presbyterian""",
            event_info='Last(-ish) Fridays of every month @6:30pm in the Fellowship Hall',
            start_date=None,  # Will be updated manually
            end_date=None,    # Will be updated manually
            active=True,
            sort_order=100,
            date_entered=datetime.utcnow()
        )

        # Add to session and commit
        db.session.add(clt_series)
        db.session.commit()

        print("✓ Christian Leadership Training series created successfully!")
        print(f"  ID: {clt_series.id}")
        print(f"  Title: {clt_series.title}")
        print(f"  Event Info: {clt_series.event_info}")
        print(f"  Status: Active")
        print("\nYou can now:")
        print("  1. Edit this series in the admin panel (/admin/teachingseries)")
        print("  2. Add monthly sessions with readings and handouts")
        print("  3. Link to the Google Doc for the full readings list")

        return clt_series

if __name__ == '__main__':
    add_clt_series()
