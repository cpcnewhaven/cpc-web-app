import os
import tempfile
import unittest

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["SECRET_KEY"] = "feedback-test-key"

from app import app, db  # noqa: E402
from models import SiteFeedback  # noqa: E402


class FeedbackTestCase(unittest.TestCase):
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

    def test_feedback_launcher_visible_to_all_visitors_in_production(self):
        """Verify feedback launcher and panel are visible by default on Render / production."""
        os.environ['RENDER'] = 'true'
        try:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn('cpcFeedbackOpen', html)
            self.assertIn('cpcFeedbackPanel', html)
            self.assertIn('feedback.css', html)
            self.assertIn('feedback.js', html)
        finally:
            os.environ.pop('RENDER', None)

    def test_feedback_can_be_disabled_via_env(self):
        """Verify feedback can be explicitly disabled via FEEDBACK_ENABLED=0."""
        os.environ['FEEDBACK_ENABLED'] = '0'
        try:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertNotIn('cpcFeedbackOpen', html)
            self.assertNotIn('cpcFeedbackPanel', html)
        finally:
            os.environ.pop('FEEDBACK_ENABLED', None)

    def test_submit_feedback_and_tracking(self):
        """Submit feedback and verify tracking code lookup."""
        payload = {
            'kind': 'idea',
            'message': 'Love the new service times section.',
            'name': 'Visitor',
            'email': 'visitor@example.com',
            'page_url': 'https://cpc-web-app.onrender.com/about',
            'page_title': 'About Us',
        }
        res = self.client.post('/api/feedback', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('ok'))
        code = data.get('tracking_code')
        self.assertTrue(code.startswith('CPC-'))

        with app.app_context():
            item = db.session.get(SiteFeedback, data['id'])
            self.assertIsNotNone(item)
            self.assertEqual(item.name, 'Visitor')
            self.assertEqual(item.page_url, 'https://cpc-web-app.onrender.com/about')

        # Test tracking
        track_res = self.client.get(f'/api/feedback/{code}')
        self.assertEqual(track_res.status_code, 200)
        track_data = track_res.get_json()
        self.assertEqual(track_data.get('tracking_code'), code)
        self.assertEqual(track_data.get('status'), 'new')

    def test_submit_feedback_requires_name_and_message(self):
        """Feedback requires both name and message."""
        res = self.client.post('/api/feedback', json={'name': 'Anon', 'message': ''})
        self.assertEqual(res.status_code, 400)

        res = self.client.post('/api/feedback', json={'name': '', 'message': 'Some message'})
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main()
