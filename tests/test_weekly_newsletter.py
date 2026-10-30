import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

_database = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_database.close()
os.environ['DATABASE_URL'] = 'sqlite:///' + _database.name
from app import app, db, cache, _not_expired, _snapshot_announcements
from models import Announcement, OngoingEvent, GlobalIDCounter
from scripts.content.apply_weekly_newsletter import apply_batch


class WeeklyNewsletterTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(GlobalIDCounter(id=1, next_id=1000))
            db.session.commit()
            cache.clear()

    def test_past_events_hidden_but_recurring_groups_retained(self):
        with app.app_context():
            yesterday = date.today() - timedelta(days=1)
            for identifier, kind in [(1, 'event'), (2, 'highlight'), (3, 'ongoing')]:
                db.session.add(Announcement(id=identifier, title=kind, description='Copy',
                    type=kind, event_date=yesterday, active=True))
            db.session.commit()
            self.assertEqual([a.id for a in Announcement.query.filter(_not_expired(Announcement))], [3])

    def test_reviewed_import_is_idempotent_and_dry_run_does_not_write(self):
        payload = json.loads(Path('data/newsletters/2026-10-30.json').read_text())
        with app.app_context():
            self.assertTrue(apply_batch(payload))
            self.assertEqual(Announcement.query.count(), 0)
            apply_batch(payload, commit=True)
            self.assertEqual(Announcement.query.count(), 12)
            self.assertEqual(OngoingEvent.query.count(), 4)
            self.assertEqual(apply_batch(payload, commit=True), [])
            hill = Announcement.query.filter(Announcement.title.like('Hill Christmas%')).one()
            self.assertEqual(hill.event_date, date(2026, 12, 6))
            self.assertEqual(hill.expires_at, date(2026, 12, 7))

    def test_snapshot_lists_calendar_and_details_agree(self):
        with patch.dict(os.environ, {'CPC_USE_ANNOUNCEMENT_SNAPSHOT': '1'}):
            client = app.test_client()
            highlights = client.get('/api/highlights').get_json()['announcements']
            titles = [r['title'] for r in highlights]
            self.assertIn('Hill Christmas Store | Donate by December 6', titles)
            self.assertIn("Women's Discipleship Group", titles)
            self.assertNotIn('CPC Worship Night', titles)
            events = client.get('/api/event-announcements').get_json()['announcements']
            self.assertEqual(len(events), 8)
            for row in highlights:
                self.assertEqual(client.get('/announcement/' + str(row['id'])).status_code, 200)
