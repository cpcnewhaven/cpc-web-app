import os
import tempfile
import unittest

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["SECRET_KEY"] = "security-test-key"

from app import app, db
from models import Announcement, User
from werkzeug.security import generate_password_hash


class SecurityFixesTestCase(unittest.TestCase):
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
            if not User.query.filter_by(username="secadmin").first():
                user = User(username="secadmin", password_hash=generate_password_hash("testpass123"))
                db.session.add(user)
                db.session.commit()
        self.client = app.test_client()

    def test_security_headers_present(self):
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_google_drive_routes_require_authentication(self):
        response = self.client.get('/admin/google-drive/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.headers.get('Location', ''))

    def test_google_drive_routes_accessible_when_authenticated(self):
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'secadmin'
        response = self.client.get('/admin/google-drive/')
        self.assertIn(response.status_code, [200, 302])

    def test_admin_login_open_redirect_mitigated(self):
        # Open redirect attempt to external domain
        response = self.client.post('/admin/login?next=https://evil.com', data={
            'username': 'secadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/admin/dashboard/')

        # Protocol-relative open redirect attempt
        response = self.client.post('/admin/login?next=//evil.com/phish', data={
            'username': 'secadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/admin/dashboard/')

        # Legitimate internal relative redirect
        response = self.client.post('/admin/login?next=/admin/sermon/', data={
            'username': 'secadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/admin/sermon/')

    def test_suggest_event_sanitizes_html_payload(self):
        response = self.client.post('/suggest-event', data={
            'title': '<script>alert(1)</script>Safe Title',
            'description': '<img src=x onerror=alert("xss")>Fun community meetup',
            'type': 'event',
            'category': 'fellowship',
            'name': 'Hacker <script>',
            'email': 'test@example.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with app.app_context():
            ann = Announcement.query.filter(Announcement.title.like('%Safe Title%')).first()
            self.assertIsNotNone(ann)
            self.assertNotIn('<script>', ann.title)
            self.assertIn('&lt;script&gt;', ann.title)
            self.assertNotIn('<img src=x', ann.description)
            self.assertIn('&lt;img', ann.description)

    def test_feedback_honeypot_blocks_bot_submission(self):
        # Bot fills the honeypot field 'website'
        from models import SiteFeedback
        response = self.client.post('/api/feedback', json={
            'kind': 'idea',
            'message': 'Spam message buy watches',
            'name': 'Spambot',
            'website': 'https://spamsite.example'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json().get('id'), 0)
        with app.app_context():
            entry = SiteFeedback.query.filter_by(message='Spam message buy watches').first()
            self.assertIsNone(entry)

        # Legitimate submission with empty website
        response = self.client.post('/api/feedback', json={
            'kind': 'idea',
            'message': 'Real human message',
            'name': 'Visitor',
            'website': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.get_json().get('id'), 0)
        with app.app_context():
            entry = SiteFeedback.query.filter_by(message='Real human message').first()
            self.assertIsNotNone(entry)

    def test_admin_csrf_blocks_cross_origin_requests(self):
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'secadmin'

        # Cross-origin request attempt from evil.com
        response = self.client.post('/admin/bulk/announcements', json={
            'action': 'delete',
            'ids': [9999]
        }, headers={'Origin': 'https://evil.com'})
        self.assertEqual(response.status_code, 403)
        self.assertIn('blocked', response.get_json().get('error', ''))

        # Same-origin request attempt
        response = self.client.post('/admin/bulk/announcements', json={
            'action': 'delete',
            'ids': [9999]
        }, headers={'Origin': 'http://localhost'})
        self.assertEqual(response.status_code, 200)

    def test_api_admin_last_change_requires_authentication(self):
        # Unauthenticated request redirects to login
        response = self.client.get('/api/admin/last-change')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.headers.get('Location', ''))

        # Authenticated request succeeds
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['username'] = 'secadmin'
        response = self.client.get('/api/admin/last-change')
        self.assertEqual(response.status_code, 200)

    def test_mailchimp_webhook_secret_enforced_when_configured(self):
        import os
        os.environ['MAILCHIMP_WEBHOOK_SECRET'] = 'webhooksecret123'
        try:
            # Request without secret returns 401
            response = self.client.post('/webhooks/mailchimp', json={'data[id]': 'c123'})
            self.assertEqual(response.status_code, 401)

            # Request with wrong secret returns 401
            response = self.client.post('/webhooks/mailchimp?secret=wrong', json={'data[id]': 'c123'})
            self.assertEqual(response.status_code, 401)

            # Request with correct secret is accepted (proceeds to payload processing)
            response = self.client.post('/webhooks/mailchimp?secret=webhooksecret123', json={})
            # Missing campaign ID will return 400, meaning it passed secret authentication!
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json().get('error'), 'Missing campaign ID')
        finally:
            os.environ.pop('MAILCHIMP_WEBHOOK_SECRET', None)


if __name__ == '__main__':
    unittest.main()
