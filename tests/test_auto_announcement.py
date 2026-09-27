import os
import tempfile
import unittest
from datetime import datetime


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "auto-announcement-test"

from app import app, db  # noqa: E402
from models import Announcement, GlobalIDCounter  # noqa: E402


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
        with app.app_context():
            drafts = Announcement.query.filter(Announcement.title.in_(["Fall retreat", "Weekly groups"])).all()
            self.assertEqual(len(drafts), 2)
            self.assertTrue(all(not draft.active and not draft.archived for draft in drafts))
            self.assertEqual({draft.type for draft in drafts}, {"event", "ongoing"})

    def test_empty_bulk_save_returns_actionable_error(self):
        response = self.client.post("/admin/auto-announcement/", json={"announcements": []})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Add at least one announcement", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
