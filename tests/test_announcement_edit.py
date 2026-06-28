import os
import tempfile
import unittest


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "announcement-edit-test"

from app import app, db  # noqa: E402
from models import Announcement  # noqa: E402
from wtforms.validators import Optional  # noqa: E402


class AnnouncementEditTestCase(unittest.TestCase):
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
            db.session.add(
                Announcement(
                    id=481,
                    title="Original title",
                    description="Original body",
                    type="event",
                    category="general",
                    active=True,
                )
            )
            db.session.commit()

        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["authenticated"] = True
            session["username"] = "tester"

    def test_edit_page_renders_record_and_optional_fields(self):
        response = self.client.get(
            "/admin/announcement/edit/?id=481&url=/admin/announcement/"
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="admin-form"', body)
        self.assertIn('value="Original title"', body)
        self.assertIn("Original body", body)
        self.assertIn('name="event_end_time"', body)
        self.assertIn('name="featured_image"', body)
        self.assertIn('name="_save_and_publish"', body)

    def test_edit_persists_with_no_expiration_date(self):
        response = self.client.post(
            "/admin/announcement/edit/?id=481&url=/admin/announcement/",
            data={
                "type": "event",
                "title": "Edited title",
                "description": "Edited body",
                "category": "worship",
                "tag": "",
                "speaker": "",
                "event_date": "2026-07-12",
                "event_start_time": "9:00 AM",
                "event_end_time": "10:30 AM",
                "active": "y",
                "banner_type": "",
                "featured_image": "https://example.com/announcement.jpg",
                "image_display_type": "",
                "expiration_preset": "never",
                "expiration_date": "",
                "date_entered": "2026-06-28T14:13",
            },
        )

        self.assertEqual(response.status_code, 302)
        with app.app_context():
            announcement = db.session.get(Announcement, 481)
            self.assertEqual(announcement.title, "Edited title")
            self.assertEqual(announcement.description, "Edited body")
            self.assertEqual(announcement.event_start_time, "9:00 AM")
            self.assertEqual(announcement.revision, 2)

        refresh_body = self.client.get(
            "/admin/announcement/edit/?id=481"
        ).get_data(as_text=True)
        self.assertIn('value="Edited title"', refresh_body)
        self.assertIn("Edited body", refresh_body)

        announcements = self.client.get("/api/announcements").get_json()["announcements"]
        self.assertTrue(
            any(item["id"] == 481 and item["title"] == "Edited title"
                for item in announcements)
        )

        public_body = self.client.get("/announcement/481").get_data(as_text=True)
        self.assertIn("Edited title", public_body)
        self.assertIn("Edited body", public_body)

    def test_save_and_deploy_publishes_a_draft(self):
        with app.app_context():
            announcement = db.session.get(Announcement, 481)
            announcement.active = False
            db.session.commit()

        response = self.client.post(
            "/admin/announcement/edit/?id=481&url=/admin/announcement/",
            data={
                "type": "event",
                "title": "Published title",
                "description": "Published body",
                "category": "general",
                "tag": "",
                "speaker": "",
                "event_date": "",
                "event_start_time": "",
                "event_end_time": "",
                "banner_type": "",
                "featured_image": "",
                "image_display_type": "",
                "expiration_preset": "never",
                "expiration_date": "",
                "date_entered": "2026-06-28T14:13",
                "_save_and_publish": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        with app.app_context():
            announcement = db.session.get(Announcement, 481)
            self.assertTrue(announcement.active)

    def test_create_supports_dates_image_and_expiration(self):
        create_page = self.client.get("/admin/announcement/create/")
        create_body = create_page.get_data(as_text=True)
        self.assertEqual(create_page.status_code, 200)
        self.assertIn('id="admin-form"', create_body)
        for field_name in (
            "event_date",
            "featured_image",
            "image_display_type",
            "expiration_preset",
            "expiration_date",
        ):
            self.assertIn(f'name="{field_name}"', create_body)

        response = self.client.post(
            "/admin/announcement/create/",
            data={
                "type": "event",
                "title": "Created with complete fields",
                "description": "Complete create workflow",
                "category": "worship",
                "tag": "summer",
                "speaker": "",
                "event_date": "2026-07-19",
                "event_start_time": "9:00 AM",
                "event_end_time": "10:30 AM",
                "featured_image": "https://example.com/created.jpg",
                "image_display_type": "poster",
                "expiration_preset": "specific",
                "expiration_date": "2026-07-20",
                "_save_and_publish": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        with app.app_context():
            announcement = Announcement.query.filter_by(
                title="Created with complete fields"
            ).one()
            self.assertTrue(announcement.active)
            self.assertEqual(str(announcement.event_date), "2026-07-19")
            self.assertEqual(
                announcement.featured_image,
                "https://example.com/created.jpg",
            )
            self.assertEqual(announcement.image_display_type, "poster")
            self.assertEqual(str(announcement.expires_at), "2026-07-20")

    def test_all_expiration_date_fields_accept_empty_values(self):
        endpoints = {
            "announcement",
            "event",
            "sermon",
            "podcastepisode",
            "galleryimage",
            "teachingseries",
        }
        views = {
            view.endpoint: view
            for view in app.extensions["admin"][0]._views
            if getattr(view, "endpoint", None) in endpoints
        }

        self.assertEqual(set(views), endpoints)
        with app.test_request_context("/admin/"):
            for endpoint, view in views.items():
                form = view.create_form()
                self.assertTrue(
                    any(
                        isinstance(validator, Optional)
                        for validator in form.expiration_date.validators
                    ),
                    endpoint,
                )

    def test_missing_record_shows_error_instead_of_edit_shell(self):
        response = self.client.get(
            "/admin/announcement/edit/?id=999999&url=/admin/announcement/",
            follow_redirects=True,
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Record does not exist.", body)
        self.assertNotIn("Editing Record", body)


if __name__ == "__main__":
    unittest.main()
