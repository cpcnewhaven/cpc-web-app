import os
import tempfile
import unittest


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "subpage-editor-test"

from app import SUBPAGE_CONFIGS, app, db  # noqa: E402
from models import SiteContent  # noqa: E402


class SubpageEditorTestCase(unittest.TestCase):
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
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["authenticated"] = True
            session["username"] = "tester"

    def test_about_editor_uses_shared_admin_shell_and_save_controls(self):
        response = self.client.get("/admin/subpage-edit/?page=about")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Page Editors", body)
        self.assertIn('id="admin-form"', body)
        self.assertIn("Save & Deploy", body)
        self.assertIn("Discard Changes", body)
        self.assertIn("Page Editors", body)
        self.assertNotIn("<body>\n\n    <!-- Simple nav bar -->", body)

    def test_page_editor_index_does_not_show_crud_publish_footer(self):
        response = self.client.get("/admin/page_editors/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Manage Site Content", body)
        self.assertNotIn("Publish Content", body)

    def test_post_still_saves_page_content(self):
        response = self.client.post(
            "/admin/subpage-edit/?page=about",
            data={"hero_description": "Updated hero copy"},
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            saved = SiteContent.query.filter_by(key="hero_description").one()
            self.assertEqual(saved.value, "Updated hero copy")

    def test_all_page_editors_render_inside_the_shared_shell(self):
        for page_key in SUBPAGE_CONFIGS:
            with self.subTest(page=page_key):
                response = self.client.get(f"/admin/subpage-edit/?page={page_key}")
                self.assertEqual(response.status_code, 200)
                self.assertIn('id="admin-form"', response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
