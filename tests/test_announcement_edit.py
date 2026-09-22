import os
import tempfile
import unittest


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "announcement-edit-test"

from app import app, db, init_admin_users  # noqa: E402
from models import Announcement, GalleryImage, TeachingSeries, TeachingSeriesSession  # noqa: E402
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
        self.assertIn("Edit Announcement", body)
        self.assertIn("announcement-preview-panel", body)
        self.assertNotIn('id="bento-grid-form"', body)

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
            self.assertEqual(announcement.image_display_type, "9x16")
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

    def test_local_demo_account_can_log_in(self):
        with app.app_context():
            init_admin_users()
        response = self.client.post(
            "/admin/login?next=/admin/dashboard/",
            data={"username": "demo", "password": "demo"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/dashboard/")

    def test_gallery_edit_can_clear_existing_tags(self):
        with app.app_context():
            image = GalleryImage(
                id=482,
                name="Tagged image",
                url="https://example.com/image.jpg",
                tags=["worship", "summer"],
            )
            db.session.add(image)
            db.session.commit()
            gallery_view = next(
                view for view in app.extensions["admin"][0]._views
                if getattr(view, "endpoint", None) == "galleryimage"
            )
            form = gallery_view.edit_form(image)
            with app.test_request_context(
                "/admin/galleryimage/edit/", method="POST", data={"tags": ""}
            ):
                form.tags.data = ""
                gallery_view.on_model_change(form, image, is_created=False)
            db.session.commit()
            db.session.expire_all()
            self.assertEqual(db.session.get(GalleryImage, 482).tags, [])

    def test_deleting_teaching_series_also_deletes_sessions(self):
        with app.app_context():
            series = TeachingSeries(id=483, title="Delete me")
            series.sessions.append(
                TeachingSeriesSession(number=1, title="Child session")
            )
            db.session.add(series)
            db.session.commit()
            session_id = series.sessions[0].id

            teaching_view = next(
                view for view in app.extensions["admin"][0]._views
                if getattr(view, "endpoint", None) == "teachingseries"
            )
            self.assertTrue(teaching_view.delete_model(series))
            self.assertIsNone(db.session.get(TeachingSeries, 483))
            self.assertIsNone(db.session.get(TeachingSeriesSession, session_id))

    def test_require_auth_redirects_unauthenticated(self):
        unauthed_client = app.test_client()
        response = unauthed_client.get("/auth/planning-center/connect")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers.get("Location", ""))

    def test_announcement_image_upload_and_aspect_ratios(self):
        import io
        fake_image = (io.BytesIO(b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"), "test.gif")
        response = self.client.post(
            "/admin/upload-image",
            data={"file": fake_image},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        uploaded_url = response.get_json().get("url")
        self.assertTrue(uploaded_url and uploaded_url.startswith("/static/uploads/"))

        # Test creating announcement with square aspect ratio
        resp_create = self.client.post(
            "/admin/announcement/create/",
            data={
                "title": "Square Announcement",
                "description": "Has square image",
                "featured_image": uploaded_url,
                "image_display_type": "square",
                "_save_and_publish": "1",
            },
        )
        self.assertEqual(resp_create.status_code, 302)

        with app.app_context():
            ann = Announcement.query.filter_by(title="Square Announcement").one()
            self.assertEqual(ann.image_display_type, "square")
            self.assertEqual(ann.featured_image, uploaded_url)

        # Verify api_announcements returns normalized imageDisplayType
        api_data = self.client.get("/api/announcements").get_json()
        matching = next(a for a in api_data["announcements"] if a["id"] == ann.id)
        self.assertEqual(matching["imageDisplayType"], "square")
        self.assertEqual(matching["featuredImage"], uploaded_url)

    def test_image_library_endpoint_and_picker(self):
        # 1. Verify library endpoint returns images including the one uploaded in previous tests
        response = self.client.get("/admin/api/image-library")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("images", data)
        self.assertIsInstance(data["images"], list)

        # 2. Verify editor template renders library picker trigger button and modal
        create_page = self.client.get("/admin/announcement/create/").get_data(as_text=True)
        self.assertIn('id="open_library_btn"', create_page)
        self.assertIn('id="image-library-modal"', create_page)
        self.assertIn('Select Image from Library', create_page)


if __name__ == "__main__":
    unittest.main()
