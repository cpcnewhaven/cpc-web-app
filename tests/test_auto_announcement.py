import os
import tempfile
import unittest
from datetime import datetime


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "auto-announcement-test"

from app import app, db  # noqa: E402
from models import Announcement, GlobalIDCounter, AnnouncementImportBatch  # noqa: E402


class AutoAnnouncementTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        os.unlink(_database_file.name)

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(Announcement(
                id=10,
                title="Fall retreat registration",
                description="Registration closes October 1.",
                active=True,
                archived=False,
                date_entered=datetime(2026, 9, 20),
            ))
            db.session.add(Announcement(
                id=11,
                title="Old retreat announcement",
                description="This archived copy should not be shown as a possible repeat.",
                active=False,
                archived=True,
                date_entered=datetime(2026, 8, 20),
            ))
            db.session.add(GlobalIDCounter(id=1, next_id=12))
            db.session.commit()
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["authenticated"] = True
            session["username"] = "tester"

    def test_match_feed_returns_existing_announcement_copy(self):
        response = self.client.get("/admin/auto-announcement/?matches=1")

        self.assertEqual(response.status_code, 200)
        announcements = response.get_json()["announcements"]
        self.assertEqual(len(announcements), 1)
        self.assertEqual(announcements[0]["title"], "Fall retreat registration")
        self.assertEqual(announcements[0]["description"], "Registration closes October 1.")

    def test_editor_page_renders_inside_admin_shell(self):
        response = self.client.get("/admin/auto-announcement/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Paste the announcement copy", body)
        self.assertIn("Sort into drafts", body)
        self.assertIn("Possible repeats include a quick wording comparison", body)

    def test_bulk_save_creates_unpublished_drafts(self):
        response = self.client.post("/admin/auto-announcement/", json={
            "announcements": [
                {"title": "Fall retreat", "description": "Register by October 1.", "type": "event"},
                {"title": "Weekly groups", "description": "Groups meet this week.", "type": "ongoing"},
            ]
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 2)
        batch_id = response.get_json()["batch_id"]
        self.assertIn('batch=' + batch_id, response.get_json()["url"])
        with app.app_context():
            drafts = Announcement.query.filter(Announcement.title.in_(["Fall retreat", "Weekly groups"])).all()
            self.assertEqual(len(drafts), 2)
            self.assertTrue(all(not draft.active and not draft.archived for draft in drafts))
            self.assertEqual({draft.type for draft in drafts}, {"event", "ongoing"})
            self.assertEqual({draft.import_batch_id for draft in drafts}, {batch_id})

    def test_import_review_excludes_existing_content_and_other_batches(self):
        first = self.client.post("/admin/auto-announcement/", json={
            "announcements": [{"title": "First batch item", "description": "First copy"}]
        }).get_json()
        second = self.client.post("/admin/auto-announcement/", json={
            "announcements": [{"title": "Second batch item", "description": "Second copy"}]
        }).get_json()
        self.assertNotEqual(first['batch_id'], second['batch_id'])
        response = self.client.get(first['url'])
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('First batch item', body)
        self.assertNotIn('Second batch item', body)
        self.assertNotIn('Fall retreat registration', body)
        self.assertIn('1 announcement in this import', body)
        self.assertIn('Back to all announcements', body)
        self.assertIn('batch=' + first['batch_id'], body)
        with app.app_context():
            draft_id = Announcement.query.filter_by(import_batch_id=first['batch_id']).first().id
        changed = self.client.get('/admin/announcement/set-status/', query_string={
            'id': draft_id, 'status': 'publish', 'batch': first['batch_id']})
        self.assertIn('batch=' + first['batch_id'], changed.location)
        with app.app_context():
            published = db.session.get(Announcement, draft_id)
            self.assertTrue(published.active)
            self.assertEqual(published.import_batch_id, first['batch_id'])
        all_content = self.client.get('/admin/announcement/').get_data(as_text=True)
        self.assertIn('First batch item', all_content)
        self.assertIn('Second batch item', all_content)
        self.assertIn('Fall retreat registration', all_content)

    def test_batch_pagination_counts_only_its_own_records(self):
        batch = self.client.post('/admin/auto-announcement/', json={
            'announcements': [{'title': 'Batch item %02d' % i, 'description': 'Copy'} for i in range(21)]
        }).get_json()
        response = self.client.get(batch['url'] + '&page_size=20&page=1')
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertEqual(body.count('class="announcement-title-text"'), 1)
        self.assertNotIn('Fall retreat registration', body)
        self.assertIn('batch=' + batch['batch_id'], body)

    def test_empty_bulk_save_returns_actionable_error(self):
        response = self.client.post("/admin/auto-announcement/", json={"announcements": []})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Add at least one announcement", response.get_json()["error"])

    def test_named_batch_updates_copy_preserving_status_and_original_batch(self):
        with app.app_context():
            existing = db.session.get(Announcement, 10)
            existing.import_batch_id = 'earlier-import'
            existing.show_in_banner = True
            existing.created_by = 'original-author'
            db.session.commit()
        response = self.client.post('/admin/auto-announcement/', json={
            'batch_name': 'September 29 Weekly', 'announcements': [
                {'title': 'Fall retreat registration', 'description': 'Updated deadline October 5.',
                 'action': 'update', 'existing_id': 10, 'revision': 1},
                {'title': 'New group', 'description': 'Meet this week.', 'action': 'create'},
                {'title': 'Ignored footer', 'action': 'skip'},
            ]})
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual((result['created'], result['updated'], result['count']), (1, 1, 2))
        with app.app_context():
            existing = db.session.get(Announcement, 10)
            self.assertEqual(existing.description, 'Updated deadline October 5.')
            self.assertTrue(existing.active and existing.show_in_banner)
            self.assertEqual(existing.created_by, 'original-author')
            self.assertEqual(existing.import_batch_id, 'earlier-import')
            self.assertEqual(existing.revision, 2)
            self.assertEqual(db.session.get(AnnouncementImportBatch, result['batch_id']).name, 'September 29 Weekly')
            self.assertEqual(Announcement.query.count(), 3)
        body = self.client.get(result['url']).get_data(as_text=True)
        self.assertIn('Fall retreat registration', body)
        self.assertIn('New group', body)
        self.assertIn('September 29 Weekly', body)
        earlier = self.client.get('/admin/announcement/?batch=earlier-import').get_data(as_text=True)
        self.assertIn('Fall retreat registration', earlier)
        self.assertNotIn('New group', earlier)

    def test_stale_update_rejects_entire_batch(self):
        response = self.client.post('/admin/auto-announcement/', json={'announcements': [
            {'title': 'Must not create', 'description': 'Copy'},
            {'title': 'Retreat', 'description': 'Copy', 'action': 'update', 'existing_id': 10, 'revision': 0},
        ]})
        self.assertEqual(response.status_code, 409)
        with app.app_context():
            self.assertEqual(Announcement.query.count(), 2)
            self.assertEqual(AnnouncementImportBatch.query.count(), 0)
            self.assertEqual(db.session.get(Announcement, 10).description, 'Registration closes October 1.')

    def test_duplicate_update_and_invalid_target_rejected(self):
        update = {'title': 'Retreat', 'description': 'Copy', 'action': 'update', 'existing_id': 10, 'revision': 1}
        response = self.client.post('/admin/auto-announcement/', json={'announcements': [update, update]})
        self.assertEqual(response.status_code, 400)
        update['existing_id'] = 11
        self.assertEqual(self.client.post('/admin/auto-announcement/', json={'announcements': [update]}).status_code, 409)
        with app.app_context():
            self.assertEqual(AnnouncementImportBatch.query.count(), 0)

    def test_excluded_items_are_not_saved(self):
        response = self.client.post('/admin/auto-announcement/', json={'announcements': [
            {'title': 'Keep this', 'description': 'Copy'},
            {'title': 'Ignore this', 'included': False},
        ]})
        self.assertEqual(response.get_json()['count'], 1)
        with app.app_context():
            self.assertIsNone(Announcement.query.filter_by(title='Ignore this').first())


if __name__ == "__main__":
    unittest.main()
