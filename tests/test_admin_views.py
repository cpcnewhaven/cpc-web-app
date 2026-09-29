import os
import tempfile
import unittest
from datetime import datetime

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["SECRET_KEY"] = "admin-test-key"

from app import app, db  # noqa: E402
from models import SiteFeedback, User  # noqa: E402


class AdminViewsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        if os.path.exists(_db_file.name):
            os.unlink(_db_file.name)

    def setUp(self):
        with app.app_context():
            db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.query(SiteFeedback).delete()
            db.session.commit()

    def test_admin_endpoints_require_auth(self):
        endpoints = [
            '/admin/sermon/',
            '/admin/podcastepisode/',
            '/admin/teachingseries/',
            '/admin/beta-features/',
            '/admin/feedback_review/',
        ]
        for path in endpoints:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 302, f"Expected 302 redirect for unauthenticated {path}")

    def test_admin_endpoints_render_successfully(self):
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'admin'

        endpoints = [
            '/admin/sermon/',
            '/admin/podcastepisode/',
            '/admin/teachingseries/',
            '/admin/beta-features/',
            '/admin/feedback_review/',
        ]
        for path in endpoints:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed to load {path}: {res.status_code}")

    def test_commit_1571679_alex_gonzalez_styling(self):
        # When logged in as Alex Gonzalez, custom transparency CSS should be present
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'alex gonzalez'

        res = self.client.get('/admin/sermon/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'table-responsive { background:transparent !important;', res.data)

        # When logged in as another user, it should not be present
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'regular_admin'

        res = self.client.get('/admin/sermon/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'table-responsive { background:transparent !important;', res.data)

    def test_feedback_review_with_items_date_formatting(self):
        with app.app_context():
            fb = SiteFeedback(
                kind='love',
                message='Test feedback message',
                name='Reviewer',
                email='reviewer@example.com',
                page_url='/about',
                page_title='About',
                status='new',
                created_at=datetime(2026, 9, 29, 9, 5, 0),
            )
            db.session.add(fb)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'admin'

        res = self.client.get('/admin/feedback_review/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test feedback message', res.data)
        self.assertIn(b'Sep 29, 2026', res.data)


if __name__ == '__main__':
    unittest.main()
